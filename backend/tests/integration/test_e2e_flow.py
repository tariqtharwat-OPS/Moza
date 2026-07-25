"""Phase 2.8: Backend E2E Integration Test (Frontend Simulator).

Simulates exact frontend SSE-stream consumption behavior.
Validates: Event schema, tool execution, capability manager,
approval service, and EventRecorder persistence.
"""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from httpx import ASGITransport

from moza.agents.interfaces import AgentInterface
from moza.config.models import MOZAConfig, AgentConfig
from moza.core.event_recorder import EventRecorder, get_recorder
from moza.core.models import (
    Environment,
    Event,
    EventType,
    Session,
    Task,
    TaskStatus,
    ToolResultPayload,
)
from moza.orchestrator.orchestrator import get_orchestrator
from moza.tools.filesystem_tool import FilesystemTool
from moza.tools.terminal_tool import TerminalTool
from moza.tools.registry import get_tool_registry


# ---------------------------------------------------------------------------
# Test Agent for E2E flows
# ---------------------------------------------------------------------------

class _E2ETestAgent(AgentInterface):
    """Yields events instantly (no sleeps) for fast E2E testing."""

    def __init__(self, require_confirmation: bool = False):
        self.require_confirmation = require_confirmation

    async def execute(self, context):
        session = context.session
        task = session.tasks[-1]
        tid = task.id
        sid = session.id

        yield Event(
            session_id=sid, task_id=tid, type=EventType.AGENT_STARTED,
            source="e2e_agent", payload={"description": task.description},
        )

        yield Event(
            session_id=sid, task_id=tid, type=EventType.TOOL_CALL,
            source="e2e_agent",
            payload={
                "tool": "filesystem",
                "description": "Read current directory",
                "args": {"action": "read", "path": "."},
                "requires_confirmation": self.require_confirmation,
            },
        )

        yield Event(
            session_id=sid, task_id=tid, type=EventType.TOOL_RESULT,
            source="e2e_agent",
            payload={
                "tool": "filesystem",
                "success": True,
                "duration_ms": 1.0,
                "exit_code": 0,
                "stdout": "file contents from e2e test",
            },
        )

        yield Event(
            session_id=sid, task_id=tid, type=EventType.LLM_FINISHED,
            source="e2e_agent",
            payload={"content": "E2E task completed successfully."},
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def e2e_app(tmp_path):
    """FastAPI app configured for E2E testing with fresh singletons."""
    from fastapi import FastAPI
    from moza.api.routes.chat import router as chat_router

    app = FastAPI()

    from moza.config.models import ProviderConfig

    config = MOZAConfig(
        agent_type="mock",
        providers={
            "openrouter": ProviderConfig(model="openrouter/test", api_key="test-key"),
        },
        agents={
            "mock": AgentConfig(allowed_tools=[]),
            "openhands": AgentConfig(allowed_tools=[]),
        },
    )
    app.state.config = config
    app.state.llm = None

    import moza.core.event_recorder as er_module
    er_module._recorder = EventRecorder(base_path=str(tmp_path / "sessions"))

    registry = get_tool_registry()
    registry.register(FilesystemTool())
    registry.register(TerminalTool())

    app.include_router(chat_router)
    return app


# ---------------------------------------------------------------------------
# SSE Parsing Helpers
# ---------------------------------------------------------------------------

def _sse_events_from_lines(lines: list[str]) -> list[dict]:
    """Parse SSE lines into event dicts. Handles CRLF and double-newline boundaries."""
    events = []
    current = {}
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = line[6:]
        elif not line and "data" in current:
            events.append(json.loads(current["data"]))
            current = {}
    if "data" in current:
        events.append(json.loads(current["data"]))
    return events


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSSEStream:
    """Verify the SSE stream produces valid Event JSON objects."""

    async def test_sse_returns_valid_events(self, e2e_app):
        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/task/execute",
                json={"description": "E2E SSE test", "workspace_path": "."},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            lines = response.text.split("\n")
            events = _sse_events_from_lines(lines)

        assert len(events) >= 3, f"Expected at least 3 events, got {len(events)}"

        for ev_data in events:
            parsed = Event(**ev_data)
            assert parsed.id, f"Event missing id: {ev_data}"
            assert parsed.type in EventType._value2member_map_, f"Invalid event type: {parsed.type}"
            assert parsed.source, f"Event missing source: {ev_data}"
            assert parsed.task_id, f"Event missing task_id: {ev_data}"
            assert parsed.session_id, f"Event missing session_id: {ev_data}"

    async def test_sse_event_order(self, e2e_app):
        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/task/execute",
                json={"description": "E2E event order test"},
            )
            lines = response.text.split("\n")
            events = _sse_events_from_lines(lines)

        types = [e["type"] for e in events]
        assert types[0] == "agent_started", f"First event should be agent_started, got {types[0]}"
        assert "tool_call" in types or "tool_selected" in types
        assert "tool_result" in types
        end_idx = next((i for i, t in enumerate(types) if t == "task_completed"), -1)
        assert end_idx >= 0, "task_completed not found"
        assert end_idx == len(types) - 1, f"task_completed should be last, got position {end_idx} of {len(types)}"

    async def test_sse_no_broken_json(self, e2e_app):
        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/task/execute",
                json={"description": "JSON integrity test"},
            )
            lines = response.text.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("data: "):
                    raw = stripped[6:]
                    try:
                        json.loads(raw)
                    except json.JSONDecodeError as e:
                        pytest.fail(f"Broken JSON in SSE stream: {e}\nRaw: {raw}")


class TestToolExecutionAndCapabilities:
    """Verify tool execution and capability checking."""

    async def test_tool_registry_check_capability(self, tmp_path):
        from moza.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register(FilesystemTool())

        registry.set_agent_capabilities("E2EAgent", ["filesystem"])
        assert registry.check_capability("E2EAgent", "filesystem") is True

    async def test_capability_denies_unauthorized_tool(self, tmp_path):
        from moza.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register(TerminalTool())

        registry.set_agent_capabilities("E2EAgent", ["filesystem"])
        with pytest.raises(PermissionError, match="not allowed"):
            registry.check_capability("E2EAgent", "terminal")

    async def test_orchestrator_completes_with_mock_agent(self, fresh_orchestrator):
        orch = fresh_orchestrator
        orch.set_agent(_E2ETestAgent(require_confirmation=False))

        registry = get_tool_registry()
        registry.register(FilesystemTool())

        session_id = "e2e-tool-test"
        env = Environment()
        task = Task(session_id=session_id, description="Tool execution test")

        await orch.submit_task(session_id, task, env)
        await asyncio.sleep(0.5)

        assert task.status == TaskStatus.COMPLETED, f"Expected COMPLETED, got {task.status}"

        session = orch.get_session(session_id)
        assert session is not None
        types = [e.type for e in session.execution_history]
        assert EventType.AGENT_STARTED in types
        assert EventType.TOOL_CALL in types
        assert EventType.TOOL_RESULT in types


class TestApprovalServiceE2E:
    """Test the full approval flow end-to-end."""

    async def test_approve_flow_via_orchestrator(self, fresh_orchestrator):
        orch = fresh_orchestrator
        orch.set_agent(_E2ETestAgent(require_confirmation=True))

        registry = get_tool_registry()
        registry.register(FilesystemTool())

        session_id = "e2e-approve"
        env = Environment()
        task = Task(session_id=session_id, description="Approve me")

        await orch.submit_task(session_id, task, env)
        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.WAITING_USER

        ok = await orch.approve_task(task.id)
        assert ok is True

        await asyncio.sleep(0.3)
        assert task.status == TaskStatus.COMPLETED

    async def test_reject_flow_via_orchestrator(self, fresh_orchestrator):
        orch = fresh_orchestrator
        orch.set_agent(_E2ETestAgent(require_confirmation=True))

        registry = get_tool_registry()
        registry.register(FilesystemTool())

        session_id = "e2e-reject"
        env = Environment()
        task = Task(session_id=session_id, description="Reject me")

        await orch.submit_task(session_id, task, env)
        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.WAITING_USER

        ok = await orch.reject_task(task.id)
        assert ok is True

        await asyncio.sleep(0.3)
        assert task.status == TaskStatus.CANCELLED

    async def test_approve_nonexistent_task_returns_404(self, e2e_app):
        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/v1/task/bogus-id/approve")
            assert resp.status_code == 404

    async def test_reject_nonexistent_task_returns_404(self, e2e_app):
        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/v1/task/bogus-id/reject")
            assert resp.status_code == 404


class TestEventRecorder:
    """Verify EventRecorder persists all emitted events to JSONL."""

    async def test_events_recorded_to_jsonl(self, e2e_app):
        orch = get_orchestrator()
        orch.set_agent(_E2ETestAgent(require_confirmation=False))

        registry = get_tool_registry()
        registry.register(FilesystemTool())

        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/v1/task/execute",
                json={"description": "Recorder test"},
            )
        lines = resp.text.split("\n")
        events = _sse_events_from_lines(lines)
        assert len(events) >= 3

        recorder = get_recorder()
        assert recorder.session_exists(events[0]["session_id"])

        log_path = recorder.get_log_path(events[0]["session_id"], events[0]["task_id"])
        assert log_path.exists()

        recorded_lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(recorded_lines) >= 3

        last_recorded = json.loads(recorded_lines[-1])
        assert last_recorded["type"] in ("task_completed", "task_failed", "llm_finished")

    async def test_replay_matches_streamed_events(self, e2e_app):
        orch = get_orchestrator()
        orch.set_agent(_E2ETestAgent(require_confirmation=False))

        registry = get_tool_registry()
        registry.register(FilesystemTool())

        transport = ASGITransport(app=e2e_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/v1/task/execute",
                json={"description": "Replay test"},
            )

        lines = resp.text.split("\n")
        streamed = _sse_events_from_lines(lines)
        assert len(streamed) >= 3

        sid = streamed[0]["session_id"]
        tid = streamed[0]["task_id"]

        recorder = get_recorder()
        replayed = recorder.replay(sid, tid)
        assert len(replayed) >= 3

        streamed_types = [e["type"] for e in streamed]
        replayed_types = [e.type.value for e in replayed]
        assert streamed_types == replayed_types, (
            f"Event type order mismatch:\n"
            f"  streamed ({len(streamed_types)}): {streamed_types}\n"
            f"  replayed ({len(replayed_types)}): {replayed_types}"
        )

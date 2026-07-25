import asyncio

import pytest

from moza.agents.interfaces import AgentInterface
from moza.core.models import Environment, Event, EventType, Session, Task, TaskStatus
from moza.core.context import ExecutionContext
from moza.orchestrator.orchestrator import Orchestrator


class _ApprovalTestAgent(AgentInterface):
    """Agent that yields TOOL_CALL with requires_confirmation=True."""

    async def execute(self, context):
        session = context.session
        task = session.tasks[-1] if session.tasks else None
        task_id = task.id if task else "unknown"
        sid = session.id

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.AGENT_STARTED,
            source="test_agent", payload={"description": getattr(task, "description", "")},
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.AGENT_THINKING,
            source="test_agent", payload={"content": "Need to delete a file..."},
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.TOOL_CALL,
            source="test_agent",
            payload={
                "tool": "delete_file",
                "requires_confirmation": True,
                "description": "Delete /etc/passwd",
                "args": {"path": "/etc/passwd"},
            },
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.TOOL_RESULT,
            source="test_agent",
            payload={
                "tool": "delete_file",
                "success": True,
                "duration_ms": 5.0,
                "stdout": "File deleted after approval",
            },
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.LLM_FINISHED,
            source="test_agent",
            payload={"content": "Task completed after user approval."},
        )


class _RejectTestAgent(AgentInterface):
    """Agent that yields TOOL_CALL with confirmation but should be cancelled."""

    async def execute(self, context):
        session = context.session
        task = session.tasks[-1]
        task_id = task.id
        sid = session.id

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.AGENT_STARTED,
            source="test_agent", payload={"description": "risky operation"},
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.AGENT_THINKING,
            source="test_agent", payload={"content": "Planning risky operation..."},
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.TOOL_CALL,
            source="test_agent",
            payload={
                "tool": "rm_rf",
                "requires_confirmation": True,
                "description": "rm -rf /",
                "args": {"path": "/"},
            },
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.TOOL_RESULT,
            source="test_agent",
            payload={
                "tool": "rm_rf",
                "success": True,
                "duration_ms": 0,
                "stdout": "Should never reach here if rejected",
            },
        )

        yield Event(
            session_id=sid, task_id=task_id, type=EventType.LLM_FINISHED,
            source="test_agent", payload={"content": "done"},
        )


class TestApprovalFlow:
    async def test_approve_resumes_and_completes(self, fresh_orchestrator):
        orch = fresh_orchestrator
        orch.set_agent(_ApprovalTestAgent())

        session_id = "test-approve-session"
        env = Environment()
        task = Task(session_id=session_id, description="Delete a file")

        await orch.submit_task(session_id, task, env)

        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.WAITING_USER, f"Expected WAITING_USER, got {task.status}"

        session = orch.get_session(session_id)
        assert session is not None
        approval_events = [e for e in session.execution_history if e.type == EventType.WAITING_APPROVAL]
        assert len(approval_events) == 1
        assert approval_events[0].payload["tool"] == "delete_file"

        ok = await orch.approve_task(task.id)
        assert ok is True

        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.COMPLETED, f"Expected COMPLETED, got {task.status}"

    async def test_reject_cancels_task(self, fresh_orchestrator):
        orch = fresh_orchestrator
        orch.set_agent(_RejectTestAgent())

        session_id = "test-reject-session"
        env = Environment()
        task = Task(session_id=session_id, description="rm -rf /")

        await orch.submit_task(session_id, task, env)

        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.WAITING_USER, f"Expected WAITING_USER, got {task.status}"

        ok = await orch.reject_task(task.id)
        assert ok is True

        await asyncio.sleep(0.3)

        assert task.status == TaskStatus.CANCELLED, f"Expected CANCELLED, got {task.status}"

    async def test_approve_invalid_task_returns_false(self, fresh_orchestrator):
        orch = fresh_orchestrator
        ok = await orch.approve_task("nonexistent-task")
        assert ok is False

    async def test_reject_invalid_task_returns_false(self, fresh_orchestrator):
        orch = fresh_orchestrator
        ok = await orch.reject_task("nonexistent-task")
        assert ok is False

    async def test_no_approval_on_non_confirmed_tool(self, fresh_orchestrator):
        from moza.agents.mock_agent import MockAgent

        orch = fresh_orchestrator
        orch.set_agent(MockAgent())

        from moza.tools.filesystem_tool import FilesystemTool
        from moza.tools.registry import get_tool_registry
        registry = get_tool_registry()
        await registry.load(FilesystemTool())

        session_id = "test-no-approval"
        env = Environment()
        task = Task(session_id=session_id, description="Normal task")

        await orch.submit_task(session_id, task, env)

        await asyncio.sleep(2.5)

        assert task.status == TaskStatus.COMPLETED, f"Expected COMPLETED, got {task.status}"
        session = orch.get_session(session_id)
        approval_events = [e for e in session.execution_history if e.type == EventType.WAITING_APPROVAL]
        assert len(approval_events) == 0

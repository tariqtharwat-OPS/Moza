"""
Phase 2.14 — Replay API Integration Tests.

Tests the four replay endpoints:
  GET    /v1/sessions
  GET    /v1/sessions/{session_id}
  GET    /v1/sessions/{session_id}/events
  POST   /v1/sessions/{session_id}/replay

Uses the same e2e_app fixture pattern as test_e2e_flow.py.
"""

import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from httpx import ASGITransport

from moza.core.event_recorder import EventRecorder
from moza.core.models import Event, EventType


# ---------------------------------------------------------------------------
# Fixture: replay-enabled FastAPI app
# ---------------------------------------------------------------------------

@pytest.fixture
async def replay_app(tmp_path):
    from fastapi import FastAPI

    app = FastAPI()

    from moza.api.routes.replay import router as replay_router
    app.include_router(replay_router)

    # Point SessionManager + EventRecorder at the same tmp path
    import moza.core.session_manager as sm_mod
    from moza.core.session_manager import SessionManager
    sm_mod._manager = SessionManager(base_path=str(tmp_path / "sessions"))

    import moza.core.event_recorder as er_mod
    er_mod._recorder = EventRecorder(base_path=str(tmp_path / "sessions"))

    import moza.core.event_bus as eb_mod
    eb_mod._event_bus = None

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_dummy_events(session_id: str, task_id: str, n: int = 4) -> list[Event]:
    now = datetime.now(timezone.utc)
    events = [
        Event(
            id=f"ev{i}", timestamp=now, session_id=session_id, task_id=task_id,
            type=EventType.AGENT_THINKING, source="test",
            payload={"content": f"step {i}"},
        )
        for i in range(n - 1)
    ]
    events.append(
        Event(
            id=f"ev{n-1}", timestamp=now, session_id=session_id, task_id=task_id,
            type=EventType.TASK_COMPLETED, source="test",
            payload={"task_id": task_id},
        ),
    )
    return events


def _seed_session(recorder: EventRecorder, session_id: str, task_id: str, n_events: int = 4):
    events = _create_dummy_events(session_id, task_id, n_events)
    for ev in events:
        recorder.record(ev)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReplayAPI:
    """Test all four replay endpoints."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, replay_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:
            resp = await client.get("/v1/sessions")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, replay_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:
            resp = await client.get("/v1/sessions/ghost")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_events_session_not_found(self, replay_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:
            resp = await client.get("/v1/sessions/ghost/events")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_replay_session_not_found(self, replay_app):
        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:
            resp = await client.post("/v1/sessions/ghost/replay")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_full_crud_lifecycle(self, replay_app, tmp_path):
        """Seed a session with events, then exercise all four endpoints."""

        import moza.core.event_recorder as er_mod
        import moza.core.session_manager as sm_mod

        recorder: EventRecorder = er_mod._recorder
        session_id = "replay-test-session"
        task_id = "replay-task-001"

        _seed_session(recorder, session_id, task_id, n_events=5)

        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:

            # ── 1. GET /sessions ───────────────────────────────────────────
            resp = await client.get("/v1/sessions")
            assert resp.status_code == 200
            sessions = resp.json()
            assert isinstance(sessions, list)
            assert len(sessions) >= 1
            found = [s for s in sessions if s["session_id"] == session_id]
            assert len(found) == 1, f"Session {session_id} not in list: {sessions}"
            summary = found[0]
            assert summary["task_count"] >= 1
            assert summary["total_events"] >= 5
            assert summary["first_event_at"] is not None
            assert summary["last_event_at"] is not None

            # ── 2. GET /sessions/{session_id} ──────────────────────────────
            resp = await client.get(f"/v1/sessions/{session_id}")
            assert resp.status_code == 200
            detail = resp.json()
            assert detail["session_id"] == session_id
            assert len(detail["tasks"]) >= 1
            task_info = detail["tasks"][0]
            assert task_info["task_id"] == task_id
            assert task_info["event_count"] == 5
            assert task_info["status"] == "completed"

            # ── 3. GET /sessions/{session_id}/events ───────────────────────
            resp = await client.get(f"/v1/sessions/{session_id}/events")
            assert resp.status_code == 200
            body = resp.json()
            assert body["session_id"] == session_id
            assert body["event_count"] == 5
            assert len(body["events"]) == 5
            types = [e["type"] for e in body["events"]]
            assert types[:4] == ["agent_thinking"] * 4
            assert types[-1] == "task_completed"

            # ── 4. GET /sessions/{session_id}/events?task_id=... ──────────
            resp = await client.get(f"/v1/sessions/{session_id}/events?task_id={task_id}")
            assert resp.status_code == 200
            body2 = resp.json()
            assert body2["event_count"] == 5
            assert len(body2["events"]) == 5

            # ── 5. POST /sessions/{session_id}/replay ──────────────────────
            import moza.core.event_bus as eb_mod
            eb_mod._event_bus = None
            event_bus = eb_mod.get_event_bus()
            queue = event_bus.subscribe(session_id)

            resp = await client.post(f"/v1/sessions/{session_id}/replay")
            assert resp.status_code == 200
            replay_result = resp.json()
            assert replay_result["session_id"] == session_id
            assert replay_result["replayed"] == 5
            assert replay_result["total"] == 5
            assert replay_result["status"] == "replay_initiated"

            # Verify events arrived on the bus
            received = []
            while True:
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=2.0)
                    received.append(ev)
                except asyncio.TimeoutError:
                    break
            assert len(received) == 5
            assert received[-1].type == EventType.TASK_COMPLETED

    @pytest.mark.asyncio
    async def test_replay_multiple_tasks(self, replay_app, tmp_path):
        """Verify session with two tasks is handled correctly."""

        import moza.core.event_recorder as er_mod
        import moza.core.session_manager as sm_mod

        recorder: EventRecorder = er_mod._recorder
        session_id = "multi-task-session"

        _seed_session(recorder, session_id, "task-alpha", n_events=3)
        _seed_session(recorder, session_id, "task-beta", n_events=2)

        async with httpx.AsyncClient(
            transport=ASGITransport(app=replay_app), base_url="http://test",
        ) as client:

            # List sessions
            resp = await client.get("/v1/sessions")
            sessions = resp.json()
            found = [s for s in sessions if s["session_id"] == session_id]
            assert len(found) == 1
            assert found[0]["task_count"] == 2
            assert found[0]["total_events"] == 5

            # Session detail
            resp = await client.get(f"/v1/sessions/{session_id}")
            detail = resp.json()
            assert detail["task_count"] == 2
            task_ids = [t["task_id"] for t in detail["tasks"]]
            assert "task-alpha" in task_ids
            assert "task-beta" in task_ids

            # All events
            resp = await client.get(f"/v1/sessions/{session_id}/events")
            assert resp.status_code == 200
            assert resp.json()["event_count"] == 5

            # Filter by task
            resp = await client.get(f"/v1/sessions/{session_id}/events?task_id=task-alpha")
            assert resp.status_code == 200
            assert resp.json()["event_count"] == 3
            resp = await client.get(f"/v1/sessions/{session_id}/events?task_id=task-beta")
            assert resp.status_code == 200
            assert resp.json()["event_count"] == 2



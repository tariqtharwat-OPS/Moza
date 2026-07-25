"""
Replay API — exposes recorded execution history for debugging and replay.

Endpoints:
  GET    /sessions                     → list of session summaries
  GET    /sessions/{session_id}        → session metadata + tasks
  GET    /sessions/{session_id}/events → full event stream
  POST   /sessions/{session_id}/replay → re-emit events to EventBus
"""

from fastapi import APIRouter, HTTPException

from moza.core.event_bus import get_event_bus
from moza.core.models import Event
from moza.core.session_manager import get_manager

router = APIRouter(prefix="/v1", tags=["replay"])


def _get_events_or_404(session_id: str, task_id: str | None = None) -> list[dict]:
    events = get_manager().get_events(session_id, task_id)
    if events is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return events


# ── list all sessions ──────────────────────────────────────────────────────


@router.get("/sessions")
async def list_sessions():
    """Return lightweight metadata for every recorded session."""
    return get_manager().list_sessions()


# ── single session detail ──────────────────────────────────────────────────


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Return full metadata for a single session (includes task list)."""
    meta = get_manager().get_session(session_id)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return meta


# ── events ─────────────────────────────────────────────────────────────────


@router.get("/sessions/{session_id}/events")
async def get_events(session_id: str, task_id: str | None = None):
    """Return all recorded events for a session, optionally filtered by task."""
    events = _get_events_or_404(session_id, task_id)
    return {"session_id": session_id, "task_id": task_id, "event_count": len(events), "events": events}


# ── replay ─────────────────────────────────────────────────────────────────


@router.post("/sessions/{session_id}/replay")
async def replay_session(session_id: str):
    """Re-emit all recorded events for a session to the EventBus."""
    mgr = get_manager()
    session = mgr.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    events_raw = mgr.get_events(session_id)
    if not events_raw:
        raise HTTPException(status_code=404, detail=f"No events found for session {session_id}")

    event_bus = get_event_bus()
    replayed = 0
    for raw in events_raw:
        try:
            event = Event.model_validate(raw)
            await event_bus.publish(session_id, event)
            replayed += 1
        except Exception:
            pass

    return {
        "session_id": session_id,
        "replayed": replayed,
        "total": len(events_raw),
        "status": "replay_initiated",
    }

"""
Session Manager — reads recorded execution data from disk.

Directory layout (written by EventRecorder):
    {base}/{session_id}/tasks/{task_id}/events.jsonl

Also reads optional artifacts written by BenchmarkRecorder:
    {base}/{session_id}/prompt.txt
    {base}/{session_id}/context.json
    {base}/{session_id}/tool_calls.jsonl
    {base}/{session_id}/tool_results.jsonl
"""

import json
from pathlib import Path


DEFAULT_BASE = "sessions"
_manager: "SessionManager | None" = None


def _is_task_dir(d: Path) -> bool:
    return d.is_dir() and d.name != "__pycache__" and len(d.name) >= 8


class SessionManager:
    """Read-only interface over recorded session data on disk."""

    def __init__(self, base_path: str | Path = DEFAULT_BASE) -> None:
        self._base = Path(base_path)

    # ── listing ────────────────────────────────────────────────────────────

    def list_sessions(self) -> list[dict]:
        """Return lightweight summaries of all recorded sessions."""
        if not self._base.is_dir():
            return []
        out: list[dict] = []
        for entry in sorted(self._base.iterdir()):
            if entry.is_dir() and not entry.name.startswith("_"):
                info = self._session_summary(entry)
                if info:
                    out.append(info)
        return out

    # ── single session ─────────────────────────────────────────────────────

    def get_session(self, session_id: str) -> dict | None:
        """Return full metadata for a session, or None."""
        path = self._base / session_id
        if not path.is_dir():
            return None
        return self._session_detail(path)

    # ── events ─────────────────────────────────────────────────────────────

    def get_events(self, session_id: str, task_id: str | None = None) -> list[dict] | None:
        """Return all events for a session, optionally filtered by task."""
        path = self._base / session_id
        if not path.is_dir():
            return None
        events: list[dict] = []
        tasks_dir = path / "tasks"
        if not tasks_dir.is_dir():
            return events
        for tdir in sorted(tasks_dir.iterdir()):
            if task_id is not None and tdir.name != task_id:
                continue
            if _is_task_dir(tdir):
                events.extend(self._read_events(tdir / "events.jsonl"))
        return events

    def get_task_ids(self, session_id: str) -> list[str] | None:
        """Return list of task IDs for a session."""
        path = self._base / session_id
        if not path.is_dir():
            return None
        tasks_dir = path / "tasks"
        if not tasks_dir.is_dir():
            return []
        return sorted(t.name for t in tasks_dir.iterdir() if _is_task_dir(t))

    # ── replay ─────────────────────────────────────────────────────────────

    def read_events_for_replay(self, session_id: str) -> list[dict] | None:
        """Same as get_events but returns raw line-by-line dicts."""
        return self.get_events(session_id)

    # ── internal helpers ───────────────────────────────────────────────────

    def _session_summary(self, path: Path) -> dict | None:
        """Lightweight summary (no event bodies)."""
        tasks_dir = path / "tasks"
        if not tasks_dir.is_dir():
            return None
        task_dirs = sorted(t.name for t in tasks_dir.iterdir() if _is_task_dir(t))
        if not task_dirs:
            return None

        total_events = 0
        first_ts: str | None = None
        last_ts: str | None = None
        tasks_meta: list[dict] = []

        for tname in task_dirs:
            evs = self._read_events(tasks_dir / tname / "events.jsonl")
            total_events += len(evs)
            if evs:
                ts0 = evs[0].get("timestamp", "")
                ts1 = evs[-1].get("timestamp", "")
                if first_ts is None or ts0 < first_ts:
                    first_ts = ts0
                if last_ts is None or ts1 > last_ts:
                    last_ts = ts1

                # derive status from last event type
                status = self._derive_status(evs[-1].get("type", ""))
            else:
                status = "empty"

            desc = self._find_description(evs)
            tasks_meta.append({
                "task_id": tname,
                "event_count": len(evs),
                "status": status,
                "description": desc,
            })

        return {
            "session_id": path.name,
            "task_count": len(task_dirs),
            "total_events": total_events,
            "first_event_at": first_ts,
            "last_event_at": last_ts,
            "tasks": tasks_meta,
        }

    def _session_detail(self, path: Path) -> dict:
        """Full detail (includes everything from summary)."""
        summary = self._session_summary(path) or {}
        # Could add file-level artifact info here in the future
        return summary

    @staticmethod
    def _read_events(file_path: Path) -> list[dict]:
        if not file_path.is_file():
            return []
        events: list[dict] = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return events

    @staticmethod
    def _derive_status(last_event_type: str) -> str:
        mapping = {
            "task_completed": "completed",
            "task_failed": "failed",
            "task_cancelled": "cancelled",
        }
        return mapping.get(last_event_type, "unknown")

    @staticmethod
    def _find_description(events: list[dict]) -> str:
        for ev in events:
            pl = ev.get("payload", {})
            desc = pl.get("description") or pl.get("task", {}).get("description", "")
            if desc:
                return desc
        return ""


def get_manager() -> SessionManager:
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager

"""
Execution Recorder for MOZA AI Operating System.

Appends every Event published by the EventBus to a JSONL file,
enabling future Replay and audit. Each event is a single JSON line in:
    sessions/{session_id}/tasks/{task_id}/events.jsonl
"""

import json
import os
from pathlib import Path

from loguru import logger

from moza.core.models import Event


class EventRecorder:
    """
    Persists Events to JSONL files organised by session/task.

    Thread-safe for async use: each write opens, appends, and closes
    the file immediately to avoid conflicts.
    """

    def __init__(self, base_path: str | Path = "sessions") -> None:
        self._base = Path(base_path)

    def _ensure_dir(self, session_id: str, task_id: str) -> Path:
        dir_path = self._base / session_id / "tasks" / task_id
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _file_path(self, session_id: str, task_id: str) -> Path:
        return self._ensure_dir(session_id, task_id) / "events.jsonl"

    def record(self, event: Event) -> None:
        """Append a single Event as a JSON line to the task's event log."""
        file_path = self._file_path(event.session_id, event.task_id)
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
        except OSError as e:
            logger.error(f"EventRecorder: failed to write {file_path}: {e}")

    def replay(self, session_id: str, task_id: str) -> list[Event]:
        """Read all events for a session/task (for future Replay feature)."""
        file_path = self._file_path(session_id, task_id)
        if not file_path.exists():
            return []
        events: list[Event] = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(Event.model_validate_json(line))
        return events

    def get_log_path(self, session_id: str, task_id: str) -> Path:
        """Return the path to the JSONL file for inspection."""
        return self._file_path(session_id, task_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if any recorded data exists for a session."""
        return (self._base / session_id).exists()


_recorder: EventRecorder | None = None


def get_recorder() -> EventRecorder:
    global _recorder
    if _recorder is None:
        _recorder = EventRecorder()
    return _recorder

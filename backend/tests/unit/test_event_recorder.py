import json
from datetime import datetime, timezone

import pytest

from moza.core.event_recorder import EventRecorder
from moza.core.models import Event, EventType


class TestEventRecorder:
    def test_record_and_replay(self, tmp_path):
        recorder = EventRecorder(base_path=str(tmp_path / "sessions"))

        event = Event(
            session_id="s1",
            task_id="t1",
            type=EventType.AGENT_STARTED,
            source="test",
            payload={"msg": "hello"},
        )
        recorder.record(event)

        log_path = recorder.get_log_path("s1", "t1")
        assert log_path.exists()

        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["type"] == "agent_started"
        assert parsed["payload"]["msg"] == "hello"

    def test_replay_returns_events(self, tmp_path):
        recorder = EventRecorder(base_path=str(tmp_path / "sessions"))

        events = [
            Event(session_id="s1", task_id="t1", type=EventType.AGENT_STARTED, source="test"),
            Event(session_id="s1", task_id="t1", type=EventType.TOOL_CALL, source="test", payload={"tool": "ls"}),
            Event(session_id="s1", task_id="t1", type=EventType.TASK_COMPLETED, source="test"),
        ]
        for e in events:
            recorder.record(e)

        replayed = recorder.replay("s1", "t1")
        assert len(replayed) == 3
        assert replayed[0].type == EventType.AGENT_STARTED
        assert replayed[1].type == EventType.TOOL_CALL
        assert replayed[2].type == EventType.TASK_COMPLETED

    def test_replay_nonexistent_returns_empty(self, tmp_path):
        recorder = EventRecorder(base_path=str(tmp_path / "sessions"))
        assert recorder.replay("no-session", "no-task") == []

    def test_session_exists(self, tmp_path):
        recorder = EventRecorder(base_path=str(tmp_path / "sessions"))
        assert recorder.session_exists("s1") is False
        recorder.record(Event(session_id="s1", task_id="t1", type=EventType.AGENT_STARTED, source="test"))
        assert recorder.session_exists("s1") is True

    def test_multiple_events_same_task(self, tmp_path):
        recorder = EventRecorder(base_path=str(tmp_path / "sessions"))
        for i in range(5):
            recorder.record(Event(
                session_id="s1", task_id="t1",
                type=EventType.LLM_TOKEN,
                source="test",
                payload={"token": f"word{i}"},
            ))
        replayed = recorder.replay("s1", "t1")
        assert len(replayed) == 5
        assert [e.payload["token"] for e in replayed] == [f"word{i}" for i in range(5)]

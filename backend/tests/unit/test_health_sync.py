import os
import time
from unittest.mock import patch

import pytest

from moza.core.event_bus import EventBus, SYSTEM_SESSION
from moza.core.models import EventType
from moza.gateway.health_tracker import HealthTracker
from moza_orchestrator.orchestrator import FailoverError, MozaOrchestrator


def _config(**overrides):
    cfg = {
        "ranking": [
            {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile",
             "ctx": 128000, "rpm": 30, "tpm": 5000},
        ],
        "apiKeys": {"groq": "sk-test"},
        "baseURLs": {"groq": "https://api.groq.com/openai/v1"},
        "routing_rules": [],
        "fallback_chain": [],
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def event_bus(tmp_path):
    """EventBus backed by a temp recorder so no session files hit the repo."""
    from moza.core.event_recorder import EventRecorder
    recorder = EventRecorder(base_path=str(tmp_path / "sessions"))
    with patch("moza.core.event_recorder._recorder", recorder):
        yield EventBus()


def _drain(queue):
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


class TestHealthTrackerPublishesEvents:
    def test_publishes_provider_failed_on_cooldown(self, event_bus):
        q = event_bus.subscribe(SYSTEM_SESSION)
        ht = HealthTracker(event_bus=event_bus)
        ht.set_cooldown("groq", "llama-3.3-70b-versatile", 60, "rate_limit")
        events = _drain(q)
        assert len(events) == 1
        assert events[0].type == EventType.PROVIDER_FAILED
        assert events[0].payload["provider"] == "groq"
        assert events[0].payload["error_type"] == "rate_limit"
        assert events[0].session_id == SYSTEM_SESSION

    def test_publishes_provider_recovered_after_success(self, event_bus):
        q = event_bus.subscribe(SYSTEM_SESSION)
        ht = HealthTracker(event_bus=event_bus)
        ht.set_cooldown("groq", "m", 60, "rate_limit")
        _drain(q)
        ht.record_success("groq", "m", 1.0)
        events = _drain(q)
        assert len(events) == 1
        assert events[0].type == EventType.PROVIDER_RECOVERED
        assert events[0].payload["provider"] == "groq"

    def test_no_event_without_event_bus(self):
        ht = HealthTracker()
        ht.set_cooldown("groq", "m", 60, "rate_limit")
        assert ht.is_on_cooldown(provider="groq")


class TestOrchestratorUsesUnifiedHealth:
    def test_cooldowns_property_proxies_to_tracker(self):
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker()
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            assert orch.cooldowns == {}
            ht.set_cooldown("groq", "m", 60, "rate_limit")
            assert "groq" in orch.cooldowns
            assert orch.cooldowns["groq"] > time.time()

    def test_is_available_respects_tracker_cooldown(self):
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker()
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            entry = {"provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000}
            assert orch._is_available(entry)
            ht.set_cooldown("groq", "m", 60, "rate_limit")
            assert not orch._is_available(entry)

    def test_handle_failover_updates_shared_tracker(self):
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker()
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            entry = {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000}
            err = FailoverError("groq", "llama-3.3-70b-versatile", "rate_limit", "rate limited")
            orch._handle_failover(entry, err)
            assert ht.is_on_cooldown(provider="groq")
            assert "groq" in orch.cooldowns

    def test_failover_event_visible_on_bus(self, event_bus):
        q = event_bus.subscribe(SYSTEM_SESSION)
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker(event_bus=event_bus)
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            entry = {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000}
            orch._handle_failover(entry, FailoverError("groq", "llama-3.3-70b-versatile", "rate_limit", "x"))
        events = _drain(q)
        assert len(events) == 1
        assert events[0].type == EventType.PROVIDER_FAILED

    def test_clear_cooldowns_resets_tracker(self):
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker()
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            ht.set_cooldown("groq", "m", 60, "rate_limit")
            assert ht.is_on_cooldown(provider="groq")
            orch._clear_provider_cooldowns()
            assert not ht.is_on_cooldown(provider="groq")
            assert orch.cooldowns == {}

    def test_record_success_enriches_tracker(self):
        with patch.dict(os.environ, {}, clear=True):
            ht = HealthTracker()
            orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)
            entry = {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000}
            orch._record_success(entry, 1.5, 100)
            assert ht.average_latency("groq") == 1.5
            assert ht._stats["groq"].successful_requests == 1


class TestBackwardCompatibility:
    def test_without_tracker_keeps_local_cooldowns(self):
        with patch.dict(os.environ, {}, clear=True):
            orch = MozaOrchestrator(ranking_config=_config())
            entry = {"rank": 1, "provider": "groq", "model": "llama-3.3-70b-versatile", "ctx": 128000}
            orch._handle_failover(entry, FailoverError("groq", "llama-3.3-70b-versatile", "rate_limit", "x"))
            assert "groq" in orch.cooldowns
            assert orch.cooldowns["groq"] > time.time()
            assert not orch._is_available(entry)

    def test_legacy_three_strike_record_failure(self):
        ht = HealthTracker()
        ht.record_failure("groq", "m")
        assert not ht.is_on_cooldown(provider="groq")
        ht.record_failure("groq", "m")
        assert not ht.is_on_cooldown(provider="groq")
        ht.record_failure("groq", "m")
        assert ht.is_on_cooldown(provider="groq")

    def test_record_failure_with_error_type_applies_immediate_cooldown(self):
        ht = HealthTracker()
        with patch("moza.gateway.health_tracker.time.time", return_value=1000.0):
            ht.record_failure("groq", "m", error_type="rate_limit", duration=60)
            assert ht.is_on_cooldown(provider="groq")
            assert ht.get_cooldowns()["groq"] == 1060.0

    def test_success_clears_cooldown(self):
        ht = HealthTracker()
        ht.set_cooldown("groq", "m", 60)
        assert ht.is_on_cooldown(provider="groq")
        ht.record_success("groq", "m", 1.0)
        assert not ht.is_on_cooldown(provider="groq")
        assert "groq" not in ht.get_cooldowns()

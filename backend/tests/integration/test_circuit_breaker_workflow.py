import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from moza.core.event_bus import EventBus, SYSTEM_SESSION
from moza.core.models import EventType
from moza.gateway.health_tracker import CircuitState, HealthTracker
from moza_orchestrator.orchestrator import FailoverError, MozaOrchestrator


class FakeResponse:
    def __init__(self, status_code, json_data, headers=None):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}

    def json(self):
        return self._json


def _patch_async_post(fake_post):
    """Patch httpx.AsyncClient so .post() returns fake_post's sync response."""
    client = MagicMock()

    async def _post(*args, **kwargs):
        return fake_post(*args, **kwargs)

    client.post = _post
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return patch("moza_orchestrator.orchestrator.httpx.AsyncClient", return_value=cm)


def _config():
    return {
        "ranking": [
            {"rank": 1, "provider": "provider_a", "model": "model-a", "ctx": 128000},
            {"rank": 2, "provider": "provider_b", "model": "model-b", "ctx": 128000},
        ],
        "apiKeys": {
            "provider_a": {
                "key1": "sk-provider-a-key1",
                "key2": "sk-provider-a-key2",
                "key3": "sk-provider-a-key3",
            },
            "provider_b": "sk-provider-b",
        },
        "baseURLs": {
            "provider_a": "https://provider-a.example/v1",
            "provider_b": "https://provider-b.example/v1",
        },
        "routing_rules": [],
        "fallback_chain": [
            {"provider": "provider_b", "model": "model-b", "reason": "fallback"}
        ],
    }


def _drain(queue):
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


@pytest.fixture
def event_bus(tmp_path):
    from moza.core.event_recorder import EventRecorder
    recorder = EventRecorder(base_path=str(tmp_path / "sessions"))
    with patch("moza.core.event_recorder._recorder", recorder):
        yield EventBus()


@pytest.mark.asyncio
async def test_circuit_breaker_workflow(event_bus):
    """
    ADR-006 Phase 5 workflow test:
    - Provider A Key1→429, Key2→429, Key3→429 → circuit OPEN
    - Routes to Provider B → 200 OK
    - After 30s (circuit HALF_OPEN) → probe Provider A → 200 → CLOSED
    - Assert EventBus emits provider_failed and provider_recovered at right times.
    """
    q = event_bus.subscribe(SYSTEM_SESSION)

    with patch.dict(os.environ, {}, clear=True):
        ht = HealthTracker(event_bus=event_bus)
        orch = MozaOrchestrator(ranking_config=_config(), health_tracker=ht)

        # --- Request 1: Provider A all 3 keys 429 -> circuit OPEN -> Provider B 200 ---
        call_count = {"provider_a": 0, "provider_b": 0}

        def fake_post(url, headers=None, json=None, **kwargs):
            if "provider-a.example" in str(url):
                call_count["provider_a"] += 1
                return FakeResponse(
                    429,
                    {"error": "rate limited"},
                    headers={"retry-after": "60"},
                )
            elif "provider-b.example" in str(url):
                call_count["provider_b"] += 1
                return FakeResponse(
                    200,
                    {
                        "choices": [{"message": {"content": "fallback ok"}}],
                        "usage": {"total_tokens": 10},
                    },
                )
            return FakeResponse(500, {})

        with _patch_async_post(fake_post):
            result = await orch.complete_with_tools(
                [{"role": "user", "content": "test"}]
            )

        assert result["content"] == "fallback ok"
        assert call_count["provider_a"] == 3  # all 3 keys tried
        assert call_count["provider_b"] == 1  # fallback served the request

        # Circuit should be OPEN for provider_a
        assert ht.get_circuit_state("provider_a") == CircuitState.OPEN

        # EventBus: provider_failed for provider_a with circuit_state="open"
        events = _drain(q)
        failed_events = [e for e in events if e.type == EventType.PROVIDER_FAILED]
        assert len(failed_events) == 1
        assert failed_events[0].payload["provider"] == "provider_a"
        assert failed_events[0].payload.get("circuit_state") == "open"
        assert failed_events[0].payload["error_type"] == "rate_limit"

        # --- Request 2: before 30s -> circuit still OPEN -> Provider B serves ---
        call_count["provider_a"] = 0
        call_count["provider_b"] = 0

        with _patch_async_post(fake_post):
            result2 = await orch.complete_with_tools(
                [{"role": "user", "content": "test2"}]
            )

        assert result2["content"] == "fallback ok"
        assert call_count["provider_a"] == 0  # circuit OPEN -> skipped
        assert call_count["provider_b"] == 1

        # Circuit still OPEN
        assert ht.get_circuit_state("provider_a") == CircuitState.OPEN

        # --- Request 3: after 30s -> circuit HALF_OPEN -> probe Provider A -> 200 -> CLOSED ---
        # Simulate 30s elapsed by setting circuit_opened_at in the past
        provider_a_stats = ht._stats["provider_a"]
        provider_a_stats.circuit_opened_at = time.time() - 31

        call_count["provider_a"] = 0
        call_count["provider_b"] = 0

        def fake_post_a_ok(url, headers=None, json=None, **kwargs):
            if "provider-a.example" in str(url):
                call_count["provider_a"] += 1
                return FakeResponse(
                    200,
                    {
                        "choices": [{"message": {"content": "provider a ok"}}],
                        "usage": {"total_tokens": 10},
                    },
                )
            elif "provider-b.example" in str(url):
                call_count["provider_b"] += 1
                return FakeResponse(
                    200,
                    {
                        "choices": [{"message": {"content": "fallback ok"}}],
                        "usage": {"total_tokens": 10},
                    },
                )
            return FakeResponse(500, {})

        with _patch_async_post(fake_post_a_ok):
            result3 = await orch.complete_with_tools(
                [{"role": "user", "content": "test3"}]
            )

        assert result3["content"] == "provider a ok"
        assert call_count["provider_a"] == 1  # probe hit provider A
        assert call_count["provider_b"] == 0  # provider B not used

        # Circuit should be CLOSED after successful probe
        assert ht.get_circuit_state("provider_a") == CircuitState.CLOSED

        # EventBus: provider_recovered for provider_a
        events = _drain(q)
        recovered_events = [e for e in events if e.type == EventType.PROVIDER_RECOVERED]
        assert len(recovered_events) == 1
        assert recovered_events[0].payload["provider"] == "provider_a"
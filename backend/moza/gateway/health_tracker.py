import time
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from moza.core.event_bus import EventBus, SYSTEM_SESSION
from moza.core.models import Event, EventType


@dataclass
class ProviderHealth:
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0
    cooldown_error_type: str = ""


class HealthTracker:
    """Master source of truth for provider health (ADR-006 Phase 3).

    Owns cooldown state that `MozaOrchestrator` used to keep locally, and
    publishes `provider_failed` / `provider_recovered` events to the EventBus
    whenever cooldown state transitions so all layers stay synchronized.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._stats: dict[str, ProviderHealth] = {}
        self._model_stats: dict[str, ProviderHealth] = {}
        self._event_bus = event_bus

    def _ensure(self, key: str, store: dict) -> ProviderHealth:
        if key not in store:
            store[key] = ProviderHealth()
        return store[key]

    def _publish(self, event_type: EventType, provider: str, model: str, **extra) -> None:
        if self._event_bus is None:
            return
        try:
            event = Event(
                session_id=SYSTEM_SESSION,
                task_id=provider,
                type=event_type,
                source="health_tracker",
                payload={"provider": provider, "model": model, **extra},
            )
            self._event_bus.publish_nowait(SYSTEM_SESSION, event)
        except Exception as e:
            logger.warning(f"HealthTracker: failed to publish {event_type.value} event: {e}")

    def _apply_cooldown(
        self,
        provider: str,
        model: str,
        ph: ProviderHealth,
        mh: ProviderHealth,
        cooldown_until: float,
        error_type: str,
    ) -> None:
        was_on_cooldown = ph.cooldown_until > time.time()
        ph.cooldown_until = cooldown_until
        ph.cooldown_error_type = error_type
        mh.cooldown_until = cooldown_until
        if not was_on_cooldown:
            self._publish(
                EventType.PROVIDER_FAILED,
                provider,
                model,
                cooldown_until=cooldown_until,
                error_type=error_type,
            )

    def record_success(self, provider: str, model: str, latency: float) -> None:
        ph = self._ensure(provider, self._stats)
        was_on_cooldown = ph.cooldown_until > time.time()
        ph.successful_requests += 1
        ph.total_latency += latency
        ph.last_success_time = time.time()
        ph.consecutive_failures = 0
        ph.cooldown_until = 0.0
        ph.cooldown_error_type = ""

        mh = self._ensure(model, self._model_stats)
        mh.successful_requests += 1
        mh.total_latency += latency
        mh.last_success_time = time.time()
        mh.consecutive_failures = 0
        mh.cooldown_until = 0.0

        if was_on_cooldown:
            self._publish(EventType.PROVIDER_RECOVERED, provider, model, latency=latency)

    def record_failure(
        self,
        provider: str,
        model: str,
        error_type: str = "",
        duration: Optional[float] = None,
    ) -> None:
        """Record a failure.

        When `error_type` or `duration` is given, a cooldown of the given
        duration (default 60s) is applied immediately (orchestrator-driven).
        With only `(provider, model)` the legacy behaviour is preserved:
        cooldown is applied after 3 consecutive failures.
        """
        ph = self._ensure(provider, self._stats)
        ph.failed_requests += 1
        ph.consecutive_failures += 1

        mh = self._ensure(model, self._model_stats)
        mh.failed_requests += 1
        mh.consecutive_failures += 1

        if error_type or duration is not None:
            cooldown_until = time.time() + (duration if duration is not None else 60.0)
            self._apply_cooldown(provider, model, ph, mh, cooldown_until, error_type or "unknown")
            return

        if ph.consecutive_failures >= 3:
            self._apply_cooldown(provider, model, ph, mh, time.time() + 60.0, "legacy")

    def set_cooldown(
        self,
        provider: str,
        model: str,
        duration: float,
        error_type: str = "",
    ) -> None:
        """Force a provider into cooldown for `duration` seconds."""
        ph = self._ensure(provider, self._stats)
        ph.failed_requests += 1
        ph.consecutive_failures += 1

        mh = self._ensure(model, self._model_stats)
        mh.failed_requests += 1
        mh.consecutive_failures += 1

        self._apply_cooldown(provider, model, ph, mh, time.time() + duration, error_type or "unknown")

    def clear_cooldown(self, provider: str, model: str = "") -> None:
        """Clear cooldown for a provider (publishes recovery if one was active)."""
        ph = self._stats.get(provider)
        if ph is None:
            return
        was_on_cooldown = ph.cooldown_until > time.time()
        ph.cooldown_until = 0.0
        ph.cooldown_error_type = ""
        if model:
            mh = self._model_stats.get(model)
            if mh:
                mh.cooldown_until = 0.0
        if was_on_cooldown:
            self._publish(EventType.PROVIDER_RECOVERED, provider, model or provider)

    def reset(self) -> None:
        """Clear all cooldowns and per-provider failure state (ADR-006 sync)."""
        now = time.time()
        for ph in self._stats.values():
            ph.cooldown_until = 0.0
            ph.cooldown_error_type = ""
            ph.consecutive_failures = 0
        for mh in self._model_stats.values():
            mh.cooldown_until = 0.0
            mh.consecutive_failures = 0

    def get_cooldowns(self) -> dict[str, float]:
        """Active per-provider cooldown deadlines (provider -> unix timestamp)."""
        now = time.time()
        return {
            provider: ph.cooldown_until
            for provider, ph in self._stats.items()
            if ph.cooldown_until > now
        }

    def is_on_cooldown(self, provider: str = "", model: str = "") -> bool:
        now = time.time()
        if provider:
            ph = self._stats.get(provider)
            if ph and ph.cooldown_until > now:
                return True
        if model:
            mh = self._model_stats.get(model)
            if mh and mh.cooldown_until > now:
                return True
        return False

    def average_latency(self, provider: str) -> float:
        ph = self._stats.get(provider)
        if not ph or ph.successful_requests == 0:
            return 0.0
        return ph.total_latency / ph.successful_requests

    def summary(self) -> dict:
        return {
            provider: {
                "success": s.successful_requests,
                "failures": s.failed_requests,
                "avg_latency": round(s.total_latency / s.successful_requests, 2) if s.successful_requests else 0.0,
                "consecutive_failures": s.consecutive_failures,
                "on_cooldown": s.cooldown_until > time.time(),
            }
            for provider, s in self._stats.items()
        }

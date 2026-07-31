import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from loguru import logger

from moza.core.event_bus import EventBus, SYSTEM_SESSION
from moza.core.models import Event, EventType


class CircuitState(str, Enum):
    """Formal circuit breaker states (ADR-006 Phase 5)."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_OPEN_TIMEOUT = 30  # seconds before OPEN -> HALF_OPEN


@dataclass
class ProviderHealth:
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0
    cooldown_error_type: str = ""
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_consecutive_failures: int = 0
    circuit_failure_type: str = ""
    circuit_opened_at: float = 0.0


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
        # ADR-006 Phase 5: every recorded failure feeds the circuit breaker.
        circuit_opened = self._count_circuit_failure(provider, model, ph, error_type)
        if not was_on_cooldown and not circuit_opened:
            self._publish(
                EventType.PROVIDER_FAILED,
                provider,
                model,
                cooldown_until=cooldown_until,
                error_type=error_type,
            )

    def _count_circuit_failure(
        self,
        provider: str,
        model: str,
        ph: ProviderHealth,
        error_type: str,
        defer_open: bool = False,
    ) -> bool:
        """Count a same-type failure and open the breaker at the threshold.

        CLOSED: consecutive same-type failures accumulate; at the threshold
        the circuit transitions to OPEN. HALF_OPEN: a failed probe re-opens
        the circuit immediately.

        ``defer_open=True`` accumulates failures toward the threshold without
        flipping the circuit OPEN — used during 429 key cycling (ADR-006 Phase
        5) so the breaker only opens once every key for the provider has failed.

        Returns True when this call transitioned the circuit to OPEN.
        """
        if ph.circuit_state == CircuitState.OPEN:
            return False  # already open; failures don't change state

        if ph.circuit_state == CircuitState.HALF_OPEN:
            ph.circuit_state = CircuitState.OPEN
            ph.circuit_opened_at = time.time()
            ph.circuit_failure_type = error_type
            self._publish(
                EventType.PROVIDER_FAILED,
                provider,
                model,
                error_type=error_type,
                circuit_state="open",
            )
            return True

        if ph.circuit_failure_type == error_type:
            ph.circuit_consecutive_failures += 1
        else:
            ph.circuit_consecutive_failures = 1
            ph.circuit_failure_type = error_type

        if (
            not defer_open
            and ph.circuit_consecutive_failures >= CIRCUIT_FAILURE_THRESHOLD
        ):
            ph.circuit_state = CircuitState.OPEN
            ph.circuit_opened_at = time.time()
            logger.warning(
                f"Circuit OPEN for {provider}/{model} after "
                f"{ph.circuit_consecutive_failures} consecutive {error_type} failures"
            )
            self._publish(
                EventType.PROVIDER_FAILED,
                provider,
                model,
                error_type=error_type,
                circuit_state="open",
            )
            return True
        return False

    def record_circuit_failure(
        self,
        provider: str,
        model: str,
        error_type: str,
        defer_open: bool = False,
    ) -> None:
        """Record a failure toward the circuit breaker WITHOUT a cooldown.

        Used during 429 key cycling (ADR-006 Phase 5): each failed key is
        counted but the provider is not cooled down until all keys fail.
        Pass ``defer_open=True`` to keep the circuit closed while cycling.
        """
        ph = self._ensure(provider, self._stats)
        mh = self._ensure(model, self._model_stats)
        ph.failed_requests += 1
        mh.failed_requests += 1
        self._count_circuit_failure(provider, model, ph, error_type, defer_open=defer_open)

    def get_circuit_state(self, provider: str) -> CircuitState:
        """Return the provider's circuit state, lazily flipping OPEN->HALF_OPEN.

        An OPEN circuit automatically transitions to HALF_OPEN after
        ``CIRCUIT_OPEN_TIMEOUT`` seconds so a single probe request is allowed.
        """
        ph = self._stats.get(provider)
        if ph is None:
            return CircuitState.CLOSED
        if (
            ph.circuit_state == CircuitState.OPEN
            and time.time() - ph.circuit_opened_at >= CIRCUIT_OPEN_TIMEOUT
        ):
            ph.circuit_state = CircuitState.HALF_OPEN
            logger.info(f"Circuit HALF_OPEN for {provider}: probe allowed")
        return ph.circuit_state

    def is_circuit_open(self, provider: str) -> bool:
        return self.get_circuit_state(provider) == CircuitState.OPEN

    def allows_request(self, provider: str) -> bool:
        """Circuit-breaker gate: reject when OPEN, probe once when HALF_OPEN."""
        state = self.get_circuit_state(provider)
        if state == CircuitState.OPEN:
            return False
        if state == CircuitState.HALF_OPEN:
            return True
        return True

    def record_success(self, provider: str, model: str, latency: float) -> None:
        ph = self._ensure(provider, self._stats)
        was_on_cooldown = ph.cooldown_until > time.time()
        was_circuit_open = ph.circuit_state in (CircuitState.OPEN, CircuitState.HALF_OPEN)
        ph.successful_requests += 1
        ph.total_latency += latency
        ph.last_success_time = time.time()
        ph.consecutive_failures = 0
        ph.cooldown_until = 0.0
        ph.cooldown_error_type = ""
        # ADR-006 Phase 5: any success resets the consecutive failure tally; a
        # success in HALF_OPEN closes the circuit (single probe -> closed).
        ph.circuit_consecutive_failures = 0
        ph.circuit_failure_type = ""
        if was_circuit_open:
            ph.circuit_state = CircuitState.CLOSED
            ph.circuit_opened_at = 0.0
            logger.info(f"Circuit CLOSED for {provider} after successful probe")

        mh = self._ensure(model, self._model_stats)
        mh.successful_requests += 1
        mh.total_latency += latency
        mh.last_success_time = time.time()
        mh.consecutive_failures = 0
        mh.cooldown_until = 0.0

        if was_on_cooldown or was_circuit_open:
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
        """Clear cooldowns and legacy failure counts (ADR-006 sync).

        Circuit breaker state is intentionally preserved: an OPEN circuit must
        survive across requests so the 30s -> HALF_OPEN probe works (ADR-006
        Phase 5). Only transient cooldowns / per-request failure tallies reset.
        """
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
            if ph is not None:
                # ADR-006 Phase 5: the circuit breaker gates requests. OPEN
                # blocks; HALF_OPEN explicitly allows the single recovery probe
                # even if a cooldown deadline is still set (additive cooldown,
                # but the probe must be able to reach the provider).
                state = self.get_circuit_state(provider)
                if state == CircuitState.OPEN:
                    return True
                if state == CircuitState.HALF_OPEN:
                    return False
                if ph.cooldown_until > now:
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
                "circuit_state": self.get_circuit_state(provider).value,
            }
            for provider, s in self._stats.items()
        }

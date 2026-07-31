import time
from dataclasses import dataclass, field


@dataclass
class ProviderHealth:
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0


class HealthTracker:
    def __init__(self) -> None:
        self._stats: dict[str, ProviderHealth] = {}
        self._model_stats: dict[str, ProviderHealth] = {}

    def _ensure(self, key: str, store: dict) -> ProviderHealth:
        if key not in store:
            store[key] = ProviderHealth()
        return store[key]

    def record_success(self, provider: str, model: str, latency: float) -> None:
        ph = self._ensure(provider, self._stats)
        ph.successful_requests += 1
        ph.total_latency += latency
        ph.last_success_time = time.time()
        ph.consecutive_failures = 0
        ph.cooldown_until = 0.0

        mh = self._ensure(model, self._model_stats)
        mh.successful_requests += 1
        mh.total_latency += latency
        mh.last_success_time = time.time()
        mh.consecutive_failures = 0
        mh.cooldown_until = 0.0

    def record_failure(self, provider: str, model: str) -> None:
        ph = self._ensure(provider, self._stats)
        ph.failed_requests += 1
        ph.consecutive_failures += 1
        if ph.consecutive_failures >= 3:
            ph.cooldown_until = time.time() + 60.0

        mh = self._ensure(model, self._model_stats)
        mh.failed_requests += 1
        mh.consecutive_failures += 1
        if mh.consecutive_failures >= 3:
            mh.cooldown_until = time.time() + 60.0

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

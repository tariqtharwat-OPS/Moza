"""
Moza Orchestrator - Multi-Provider Failover System

Implements intelligent failover across 8 providers with 26 ranked models.
Features smart routing (vision, large-context, coding), silent auto-fallback
with cooldown management, proxy support for IP blocks, and never exposes
API errors to end users.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger

# VPN Rotation (ADR-006 Phase 4: IP-change confirmation before retries)
# Walk up from src/moza_orchestrator to the repo root to find scripts/.
SCRIPTS_DIR = next(
    (p / "scripts" for p in [Path(__file__).parents[i] for i in range(6)]
     if (p / "scripts" / "rotate_vpn.py").exists()),
    Path(__file__).parents[0] / "scripts",
)
ROTATE_VPN_SCRIPT = SCRIPTS_DIR / "rotate_vpn.py"

IP_CHECK_URL = "https://api.ipify.org?format=json"
IP_CHECK_TIMEOUT = 5
VPN_ROTATION_TIMEOUT = 30
VPN_POLL_INTERVAL = 3
VPN_CHECK_FAILED_DELAY = 5

# Synchronized with config.json (live ranking, routing_rules, fallback_chain)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")

# Mapping: config.json provider name -> environment variable name
# Phase 1 of ADR-006: env var takes precedence over config.json
ENV_KEY_MAP = {
    "groq": "GROQ_API_KEY",
    "github": "GITHUB_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "sambanova": "SAMBANOVA_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "cloudflare": "CLOUDFLARE_API_KEY",
    "opencode-zen": "OPENCODE_ZEN_API_KEY",
}

# Browser-like headers to reduce Cloudflare WAF blocks
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Per-provider timeout overrides (some providers are slower)
PROVIDER_TIMEOUTS = {
    "nvidia": 30,
    "sambanova": 20,
    "openrouter-youssef": 20,
}


def _load_config() -> Dict:
    path = os.path.abspath(CONFIG_PATH)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

_LIVE = _load_config()

RANKING_CONFIG = _LIVE if _LIVE else {
    "ranking": [],
    "apiKeys": {},
    "baseURLs": {},
    "routing_rules": [],
    "fallback_chain": []
}


class FailoverError(Exception):
    """Exception raised when failover is triggered."""
    def __init__(self, provider: str, model: str, error_type: str, message: str):
        self.provider = provider
        self.model = model
        self.error_type = error_type
        self.message = message
        super().__init__(f"{provider}/{model} {error_type}: {message}")


class MozaOrchestrator:
    """
    Multi-Provider Failover Orchestrator for Moza AI System.

    Routes requests through 8 providers with 26 ranked models, providing
    transparent failover for rate limits, auth errors, IP blocks, timeouts.
    Supports HTTP/HTTPS proxy for bypassing IP-based blocks.
    """

    def __init__(self, ranking_config: Optional[Dict] = None, health_tracker: Optional[Any] = None):
        cfg = ranking_config if ranking_config else RANKING_CONFIG
        self.ranking = cfg.get("ranking", [])
        raw_keys = cfg.get("apiKeys", {})
        self.keys = {}  # provider -> current key string
        self.key_lists = {}  # provider -> list of all keys
        self.key_index = {}  # provider -> current index
        # ADR-006 Phase 3: unified health state. When a HealthTracker is
        # provided it becomes the master source of truth for cooldowns.
        self._health_tracker = health_tracker
        
        for provider, key_data in raw_keys.items():
            # Phase 1 of ADR-006: check env var first (env takes precedence)
            env_var = ENV_KEY_MAP.get(provider)
            env_val = os.environ.get(env_var) if env_var else None

            if env_val:
                self.key_lists[provider] = [env_val]
                self.keys[provider] = env_val
                self.key_index[provider] = 0
                logger.info(f"Loaded key for {provider} from environment ({env_var})")
                continue

            # Fallback to config.json (deprecated — Phase 2 will remove)
            if isinstance(key_data, str):
                self.key_lists[provider] = [key_data]
                self.keys[provider] = key_data
                self.key_index[provider] = 0
                logger.info(f"Loaded key for {provider} from config.json (deprecated)")
            elif isinstance(key_data, dict):
                key_list = []
                for name, val in key_data.items():
                    if isinstance(val, str) and val.startswith(("sk-", "gsk_", "github_", "nvapi-", "csk-", "cfut_")):
                        key_list.append(val)
                    elif isinstance(val, dict) and "token" in val:
                        key_list.append(f"{val.get('account_id','')}|{val.get('token','')}")
                if key_list:
                    self.key_lists[provider] = key_list
                    self.keys[provider] = key_list[0]
                    self.key_index[provider] = 0
                    logger.info(f"Loaded key for {provider} from config.json (deprecated)")
            if provider not in self.keys:
                logger.warning(f"No key found for provider {provider} (no env var, no valid config entry)")

        self.urls = cfg.get("baseURLs", {})

        self.routing_rules = cfg.get("routing_rules", [])
        self.fallback_chain = cfg.get("fallback_chain", [])

        # Proxy support (standard env vars)
        self._proxy = (
            os.environ.get("HTTPS_PROXY")
            or os.environ.get("HTTP_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("http_proxy")
            or ""
        )
        if self._proxy:
            logger.info(f"Proxy configured: {self._proxy[:40]}...")

        # State management
        self._cooldowns = {}   # local fallback when no HealthTracker provided
        self.dead_providers = set()   # permanent failures (auth, dead)
        self.blocked_providers = {}   # provider -> unix_timestamp (IP blocks)
        self.call_history = []
        # ADR-006 Phase 5: keys that hit 429 in the current rotation cycle,
        # so we only re-open the circuit / apply cooldown once ALL keys fail.
        self._rate_limited_keys = {}   # provider -> set of failed keys

        self._setup_logging()

    @property
    def cooldowns(self) -> Dict[str, float]:
        """Read-only proxy to the unified HealthTracker (ADR-006 Phase 3).

        When a HealthTracker is attached, this returns its active cooldown
        deadlines; otherwise it proxies the local fallback dictionary.
        """
        if self._health_tracker is not None:
            return self._health_tracker.get_cooldowns()
        return dict(self._cooldowns)

    def _is_provider_on_cooldown(self, provider: str) -> bool:
        if self._health_tracker is not None:
            return self._health_tracker.is_on_cooldown(provider=provider)
        return self._cooldowns.get(provider, 0) > time.time()

    def _set_provider_cooldown(self, provider: str, model: str, duration: float, error_type: str) -> None:
        """Set a cooldown on the unified HealthTracker (or local fallback)."""
        if self._health_tracker is not None:
            self._health_tracker.set_cooldown(provider, model, duration, error_type)
        else:
            self._cooldowns[provider] = time.time() + duration

    def _clear_provider_cooldowns(self) -> None:
        if self._health_tracker is not None:
            self._health_tracker.reset()
        else:
            self._cooldowns.clear()

    def _setup_logging(self):
        logger.add(
            "moza_failover.log",
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            level="INFO"
        )

    def _is_available(self, entry: Dict, max_tokens: int = 0) -> bool:
        """Check if provider is available based on cooldown, block, and context."""
        provider = entry["provider"]

        if provider in self.dead_providers:
            return False

        now = time.time()
        if self._is_provider_on_cooldown(provider):
            return False
        if self.blocked_providers.get(provider, 0) > now:
            return False

        if max_tokens > 0 and max_tokens > entry["ctx"] * 0.9:
            return False

        return True

    def _get_cooldown_duration(self, error_type: str) -> int:
        cooldowns = {
            "rate_limit": 60,
            "auth_error": 3600,
            "ip_blocked": 300,
            "insufficient_credits": 3600,
            "quality_fail": 300,
            "timeout": 30,
            "server_error": 60,
            "dead": 3600,
        }
        return cooldowns.get(error_type, 60)

    def _handle_failover(self, entry: Dict, error: "FailoverError"):
        """Handle failover logic and update provider state."""
        provider = entry["provider"]
        now = time.time()
        cooldown_duration = self._get_cooldown_duration(error.error_type)

        if error.error_type == "ip_blocked":
            self.blocked_providers[provider] = now + cooldown_duration
            logger.warning(
                f"RANK {entry['rank']} {provider}/{entry['model']} IP_BLOCKED "
                f"(cooldown {cooldown_duration}s)"
            )
            self._set_provider_cooldown(provider, entry["model"], cooldown_duration, error.error_type)
            self._maybe_rotate_vpn()
            return

        if error.error_type in ("auth_error", "dead"):
            # Try cycling to next key for this provider
            if self._cycle_provider_key(provider):
                logger.info(f"RANK {entry['rank']} {provider}/{entry['model']} AUTH_ERROR -> cycled to next key")
                return  # Don't add to dead_providers, try next key
            else:
                self.dead_providers.add(provider)
                self._set_provider_cooldown(provider, entry["model"], cooldown_duration, error.error_type)
        else:
            self._set_provider_cooldown(provider, entry["model"], cooldown_duration, error.error_type)

        logger.info(
            f"RANK {entry['rank']} {provider}/{entry['model']} "
            f"{error.error_type.upper()} -> failover"
        )

    def _get_public_ip(self) -> Optional[str]:
        """Fetch the current public IP via ipify (None on any failure)."""
        try:
            response = httpx.get(
                IP_CHECK_URL,
                timeout=IP_CHECK_TIMEOUT,
                headers=BROWSER_HEADERS,
            )
            if response.status_code == 200:
                return response.json().get("ip")
        except Exception as e:
            logger.warning(f"Public IP check failed: {e}")
        return None

    def _wait_for_ip_change(self, old_ip: str) -> Optional[str]:
        """Poll the public IP every 3s until it changes or the 30s timeout."""
        start = time.time()
        while time.time() - start < VPN_ROTATION_TIMEOUT:
            time.sleep(VPN_POLL_INTERVAL)
            new_ip = self._get_public_ip()
            if new_ip and new_ip != old_ip:
                logger.info(f"VPN rotated, new IP: {new_ip}")
                return new_ip
        return None

    def _maybe_rotate_vpn(self) -> bool:
        """Rotate VPN and wait for confirmed IP change (ADR-006 Phase 4).

        Returns True if the IP changed (or could not be verified, so we
        optimistically assume rotation succeeded), False on timeout.
        """
        blocked_count = sum(
            1 for p, t in self.blocked_providers.items()
            if t > time.time()
        )
        if blocked_count < 2 or not ROTATE_VPN_SCRIPT.exists():
            return False

        logger.warning(f"{blocked_count} providers IP-blocked, triggering VPN rotation")
        old_ip = self._get_public_ip()
        if old_ip is None:
            logger.warning("Could not verify public IP; assuming rotation may have worked")
            time.sleep(VPN_CHECK_FAILED_DELAY)
            return True

        try:
            subprocess.Popen(
                ["python", str(ROTATE_VPN_SCRIPT), "--skip", "openvpn", "proxy", "manual"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error(f"VPN rotation trigger failed: {e}")
            return False

        new_ip = self._wait_for_ip_change(old_ip)
        if new_ip is None:
            logger.warning("VPN rotation timed out, IP unchanged; forcing fallback to next provider")
            return False
        return True

    def _cycle_provider_key(self, provider: str) -> bool:
        """Cycle to the next API key for a provider. Returns True if successful."""
        if provider not in self.key_lists:
            return False
        keys = self.key_lists[provider]
        if len(keys) <= 1:
            return False  # No alternative keys
        
        current_idx = self.key_index.get(provider, 0)
        next_idx = (current_idx + 1) % len(keys)
        
        if next_idx == current_idx:
            return False  # Full cycle, no more keys
        
        self.key_index[provider] = next_idx
        self.keys[provider] = keys[next_idx]
        
        logger.info(f"Provider {provider}: cycled key index {current_idx} -> {next_idx}")
        
        # Trigger VPN rotation when cycling keys (new IP for new key)
        self._maybe_rotate_vpn()
        
        return True

    def _validate_quality(self, response: str) -> bool:
        # Allow short responses like "OK" for ping tests
        stripped = response.strip()
        if stripped.upper() in ("OK", "OK - GROQ WORKING", "OK - GITHUB MODELS WORKING"):
            return True
        if len(response) < 10:
            return False
        return True

    def _record_success(self, entry: Dict, duration: float, tokens: int):
        self.call_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rank": entry["rank"],
            "provider": entry["provider"],
            "model": entry["model"],
            "duration": duration,
            "tokens": tokens,
            "success": True
        })
        logger.info(
            f"RANK {entry['rank']} {entry['provider']}/{entry['model']} "
            f"SUCCESS {duration:.1f}s {tokens} tokens"
        )
        if self._health_tracker is not None:
            self._health_tracker.record_success(entry["provider"], entry["model"], duration)

    def _make_request(self, entry: Dict, messages: List[Dict], **kwargs) -> str | Dict:
        result = self._make_request_raw(entry, messages, **kwargs)
        if isinstance(result, str):
            return result
        tool_calls = result.get("tool_calls", [])
        if tool_calls:
            return result
        return result.get("content", "")

    def _make_request_with_tools(self, entry: Dict, messages: List[Dict], **kwargs) -> Dict:
        return self._make_request_raw(entry, messages, **kwargs)

    def _build_client_kwargs(self, entry: Dict, **kwargs) -> Dict:
        """Build httpx request kwargs with proxy and timeout support."""
        provider = entry["provider"]
        client_kwargs: Dict = {
            "timeout": kwargs.get("timeout") or PROVIDER_TIMEOUTS.get(provider, 12),
        }
        if self._proxy:
            client_kwargs["proxies"] = self._proxy
        return client_kwargs

    def _make_request_raw(self, entry: Dict, messages: List[Dict], **kwargs) -> str | Dict:
        """Make HTTP request to provider. Returns content string or dict with tool_calls."""
        provider = entry["provider"]
        model = entry["model"]
        base_url = self.urls.get(provider, "")
        api_key = self.keys.get(provider, "")

        if not base_url:
            raise FailoverError(provider, model, "config_error",
                                f"No base URL configured for {provider}")
        if not api_key:
            raise FailoverError(provider, model, "config_error",
                                f"No API key configured for {provider}")

        # Handle Cloudflare: extract account_id from key pair (account_id|token)
        if provider == "cloudflare" and "|" in api_key:
            parts = api_key.split("|", 1)
            account_id, cf_token = parts[0], parts[1]
            base_url = f"{base_url}/{account_id}/ai/v1"
            api_key = cf_token

        tools = kwargs.get("tools") or kwargs.get("tool_schemas")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **BROWSER_HEADERS,
        }

        if provider == "mistral":
            headers["Accept"] = "application/json"
        elif provider == "glm-zhipu":
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        if "stream" in kwargs:
            payload["stream"] = kwargs["stream"]
            if kwargs["stream"]:
                payload["stream_options"] = {"include_usage": True}

        url = f"{base_url}/chat/completions"
        client_kwargs = self._build_client_kwargs(entry, **kwargs)

        start_time = time.time()
        try:
            response = httpx.post(url, headers=headers, json=payload, **client_kwargs)
            duration = time.time() - start_time

            # Handle all HTTP status codes explicitly
            if response.status_code == 402:
                raise FailoverError(
                    provider, model, "insufficient_credits",
                    f"Insufficient credits: {response.text[:200]}"
                )

            if response.status_code == 403:
                raise FailoverError(
                    provider, model, "ip_blocked",
                    f"IP blocked / access denied: {response.text[:200]}"
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 60))
                raise FailoverError(
                    provider, model, "rate_limit",
                    f"Rate limited. Retry after {retry_after}s"
                )

            if response.status_code == 401:
                raise FailoverError(
                    provider, model, "auth_error",
                    f"Authentication failed: {response.text[:200]}"
                )

            if response.status_code in (400, 422) and tools:
                logger.warning(f"{provider}/{model} does not support tools, retrying without")
                kwargs.pop("tools", None)
                kwargs.pop("tool_schemas", None)
                payload.pop("tools", None)
                payload.pop("tool_choice", None)
                response = httpx.post(url, headers=headers, json=payload, **client_kwargs)
                duration = time.time() - start_time

                if response.status_code == 403:
                    raise FailoverError(provider, model, "ip_blocked",
                                        f"IP blocked: {response.text[:200]}")
                if response.status_code in (401,):
                    raise FailoverError(provider, model, "auth_error",
                                        f"Authentication failed: {response.text[:200]}")
                if response.status_code >= 500:
                    raise FailoverError(provider, model, "server_error",
                                        f"Server error: {response.status_code}")
                if response.status_code >= 400:
                    raise FailoverError(provider, model, "http_error",
                                        f"HTTP {response.status_code}: {response.text[:200]}")
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"].get("content", "") or ""
                    tokens = result.get("usage", {}).get("total_tokens", 0)
                    self._record_success(entry, duration, tokens)
                    return content
                else:
                    raise FailoverError(provider, model, "invalid_response",
                                        "No choices in response after retry")

            if response.status_code >= 500:
                raise FailoverError(provider, model, "server_error",
                                    f"Server error: {response.status_code}")

            if response.status_code >= 400:
                raise FailoverError(provider, model, "http_error",
                                    f"HTTP {response.status_code}: {response.text[:200]}")

            result = response.json()

            if kwargs.get("stream", False):
                return result

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"].get("content", "") or ""
                tokens = result.get("usage", {}).get("total_tokens", 0)
                tool_calls = self._try_extract_tool_calls(result)
                self._record_success(entry, duration, tokens)
                if tools and tool_calls:
                    return {"content": content, "tool_calls": tool_calls}
                return content
            else:
                raise FailoverError(provider, model, "invalid_response",
                                    "No choices in response")

        except httpx.TimeoutException:
            raise FailoverError(provider, model, "timeout", "Request timed out")
        except json.JSONDecodeError:
            raise FailoverError(provider, model, "invalid_json", "Invalid JSON response")

    def _rule_matches(self, rule: Dict, messages: List[Dict]) -> bool:
        keywords = rule.get("trigger_keywords", [])
        if not keywords:
            return True
        text = " ".join(msg.get("content", "") for msg in messages).lower()
        return any(kw in text for kw in keywords)

    def _select_best_model(self, messages: List[Dict], **kwargs) -> Dict:
        """Select the best model using routing_rules from config."""
        max_tokens = kwargs.get("max_tokens", 0)

        for rule in self.routing_rules:
            if self._rule_matches(rule, messages):
                targets = rule.get("target_models", [])
                for target in targets:
                    match = next(
                        (m for m in self.ranking
                         if m["provider"] == target["provider"]
                         and m["model"] == target["model"]
                         and self._is_available(m, max_tokens)),
                        None
                    )
                    if match:
                        logger.info(
                            f"Routing rule '{rule['rule']}' -> "
                            f"{target['provider']}/{target['model']} "
                            f"({target.get('reason','')})"
                        )
                        return match

        available = [m for m in self.ranking if self._is_available(m, max_tokens)]
        if available:
            return available[0]
        raise Exception("No available models")

    def _record_circuit_failure(self, provider: str, model: str, error_type: str, defer_open: bool = False) -> None:
        """Record a circuit-breaker failure on the shared HealthTracker (ADR-006 Phase 5)."""
        if self._health_tracker is not None:
            self._health_tracker.record_circuit_failure(provider, model, error_type, defer_open=defer_open)

    def _handle_rate_limit_cycle(self, entry: Dict, error: "FailoverError") -> bool:
        """Cycle to a fresh API key on a 429 (ADR-006 Phase 5).

        Marks the current key as rate-limited, counts the failure toward the
        circuit breaker WITHOUT opening it (defer), and selects the next key
        that has not yet been rate-limited in this rotation cycle.

        Returns True when a fresh key was selected (caller must retry the same
        entry immediately, without cooldown or circuit breaker). Returns False
        when every key for the provider has already failed with 429 — the
        caller then applies the normal cooldown, which opens the circuit at
        the 3-failure threshold.
        """
        provider = entry["provider"]
        model = entry["model"]
        keys = self.key_lists.get(provider, [])
        current_key = self.keys.get(provider, "")

        rl_set = self._rate_limited_keys.setdefault(provider, set())
        rl_set.add(current_key)

        if len(keys) <= 1:
            return False

        current_idx = self.key_index.get(provider, 0)
        for offset in range(1, len(keys) + 1):
            next_idx = (current_idx + offset) % len(keys)
            if keys[next_idx] not in rl_set:
                # Count toward the breaker but keep it closed while keys remain.
                self._record_circuit_failure(provider, model, "rate_limit", defer_open=True)
                self.key_index[provider] = next_idx
                self.keys[provider] = keys[next_idx]
                logger.warning(
                    f"RANK {entry['rank']} {provider}/{model} RATE_LIMIT "
                    f"-> cycled to key index {next_idx}, retrying"
                )
                return True
        return False

    async def _try_with_key_retry(self, entry: Dict, messages: List[Dict], **kwargs) -> str | Dict:
        """Call an entry, retrying on 429 by cycling API keys (ADR-006 Phase 5).

        On a 429 with a fresh key available, the key is cycled and the same
        entry is retried immediately without tripping the circuit breaker or
        applying a cooldown. When every key has failed with 429 the error is
        re-raised so the caller's normal failover applies (which opens the
        circuit at the 3-failure threshold). Non-rate-limit errors propagate
        immediately.
        """
        provider = entry["provider"]
        max_attempts = max(1, len(self.key_lists.get(provider, [])))
        last_error: Optional[FailoverError] = None
        for _ in range(max_attempts):
            try:
                return await self._try_call(entry, messages, **kwargs)
            except FailoverError as e:
                last_error = e
                if e.error_type == "rate_limit" and self._handle_rate_limit_cycle(entry, e):
                    continue
                raise
        assert last_error is not None
        raise last_error

    async def _try_call(self, entry: Dict, messages: List[Dict], **kwargs) -> str:
        """Call a single model, converting any exception to FailoverError."""
        try:
            result = await self._call_model(entry, messages, **kwargs)
            return result
        except FailoverError:
            raise
        except Exception as e:
            raise FailoverError(
                entry["provider"], entry["model"], "unknown",
                str(e)
            )

    async def complete(self, messages: List[Dict], **kwargs) -> str:
        """Complete the request with silent auto-fallback."""
        smart_entry = None
        try:
            smart_entry = self._select_best_model(messages, **kwargs)
            result = await self._try_with_key_retry(smart_entry, messages, **kwargs)
            if self._validate_quality(result):
                return result
        except Exception as e:
            if smart_entry:
                if isinstance(e, FailoverError):
                    self._handle_failover(smart_entry, e)
                logger.warning(f"Smart route failed, falling back: {e}")
            else:
                logger.warning(f"No smart route available, using fallback chain")

        for fallback in self.fallback_chain:
            entry = next(
                (m for m in self.ranking
                 if m["provider"] == fallback["provider"]
                 and m["model"] == fallback["model"]),
                None
            )
            if not entry:
                continue
            if not self._is_available(entry, kwargs.get("max_tokens", 0)):
                continue

            try:
                logger.info(
                    f"Fallback -> {fallback['provider']}/{fallback['model']} "
                    f"({fallback.get('reason','')})"
                )
                result = await self._try_with_key_retry(entry, messages, **kwargs)
                if self._validate_quality(result):
                    return result
                raise FailoverError(
                    entry["provider"], entry["model"], "quality_fail",
                    "Quality validation failed"
                )
            except FailoverError as e:
                self._handle_failover(entry, e)
                continue
            except Exception as e:
                logger.warning(
                    f"Fallback {entry['provider']}/{entry['model']} "
                    f"unexpected error: {e}"
                )
                continue

        raise Exception("All fallback chain models exhausted")

    async def _call_model(self, entry: Dict, messages: List[Dict], **kwargs) -> str:
        """Call a specific model with error handling."""
        if kwargs.get("stream", False):
            return await self._call_streaming(entry, messages, **kwargs)
        return self._make_request(entry, messages, **kwargs)

    async def complete_with_tools(self, messages: List[Dict], **kwargs) -> Dict:
        """Complete request and return structured response (with auto-fallback)."""
        self.dead_providers.clear()
        self._clear_provider_cooldowns()

        smart_entry = None
        try:
            smart_entry = self._select_best_model(messages, **kwargs)
            result = await self._try_with_key_retry(smart_entry, messages, **kwargs)
            if isinstance(result, dict):
                return result
            content = str(result) if not isinstance(result, str) else result
            if self._validate_quality(content):
                return {"content": content, "tool_calls": []}
        except Exception as e:
            if smart_entry:
                if isinstance(e, FailoverError):
                    self._handle_failover(smart_entry, e)
                logger.warning(f"Smart route failed in complete_with_tools: {e}")

        for fallback in self.fallback_chain:
            entry = next(
                (m for m in self.ranking
                 if m["provider"] == fallback["provider"]
                 and m["model"] == fallback["model"]),
                None
            )
            if not entry:
                continue
            if not self._is_available(entry, kwargs.get("max_tokens", 0)):
                continue

            try:
                result = await self._try_with_key_retry(entry, messages, **kwargs)
                if isinstance(result, dict):
                    return result
                content = str(result) if not isinstance(result, str) else result
                if self._validate_quality(content):
                    return {"content": content, "tool_calls": []}
                raise FailoverError(
                    entry["provider"], entry["model"], "quality_fail",
                    "Quality validation failed"
                )
            except FailoverError as e:
                self._handle_failover(entry, e)
                continue
            except Exception as e:
                logger.warning(
                    f"Fallback {entry['provider']}/{entry['model']} "
                    f"unexpected error: {e}"
                )
                continue

        raise Exception("All fallback chain models exhausted")

    def _try_extract_tool_calls(self, result: Dict) -> list[Dict]:
        """Extract tool_calls from API response."""
        if "choices" not in result or not result["choices"]:
            return []
        msg = result["choices"][0].get("message", {})
        raw = msg.get("tool_calls", None) or []
        normalized = []
        for tc in raw:
            normalized.append({
                "id": tc.get("id", ""),
                "type": "function",
                "function": {
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": tc.get("function", {}).get("arguments", ""),
                }
            })
        return normalized

    async def _call_streaming(self, entry: Dict, messages: List[Dict], **kwargs) -> str:
        """Handle streaming requests with seamless failover."""
        provider = entry["provider"]
        model = entry["model"]
        base_url = self.urls.get(provider, "")
        api_key = self.keys.get(provider, "")

        if not base_url or not api_key:
            raise FailoverError(provider, model, "config_error",
                                "Missing base URL or API key")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            **BROWSER_HEADERS,
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        client_kwargs = {
            "timeout": kwargs.get("timeout") or PROVIDER_TIMEOUTS.get(provider, 12),
        }
        if self._proxy:
            client_kwargs["proxies"] = self._proxy

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                async with client.stream(
                    "POST",
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("retry-after", 60))
                        raise FailoverError(provider, model, "rate_limit",
                                            f"Rate limited. Retry after {retry_after}s")

                    if response.status_code == 403:
                        raise FailoverError(provider, model, "ip_blocked",
                                            "IP blocked / access denied")

                    if response.status_code == 402:
                        raise FailoverError(provider, model, "insufficient_credits",
                                            "Insufficient credits")

                    if response.status_code in (401,):
                        raise FailoverError(provider, model, "auth_error",
                                            "Authentication failed")

                    if response.status_code >= 400:
                        raise FailoverError(provider, model, "http_error",
                                            f"HTTP {response.status_code}")

                    full_content = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_content += content
                            except json.JSONDecodeError:
                                continue

                    return full_content

        except httpx.TimeoutException:
            raise FailoverError(provider, model, "timeout",
                                "Streaming request timed out")
        except FailoverError:
            raise
        except Exception as e:
            raise FailoverError(provider, model, "stream_error", str(e))

    def get_stats(self) -> Dict:
        """Get statistics about orchestrator performance."""
        total_calls = len(self.call_history)
        successful_calls = sum(1 for call in self.call_history if call.get("success", False))
        failed_calls = total_calls - successful_calls

        now = time.time()
        blocked_info = {
            p: int(self.blocked_providers[p] - now)
            for p in self.blocked_providers
            if self.blocked_providers[p] > now
        }
        cooldown_info = {
            p: int(self.cooldowns[p] - now)
            for p in self.cooldowns
            if self.cooldowns[p] > now
        }

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "dead_providers": list(self.dead_providers),
            "blocked_providers": blocked_info,
            "cooldown_providers": cooldown_info,
        }

import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import litellm
from loguru import logger

from moza.config.models import MOZAConfig
from moza.gateway.health_tracker import HealthTracker


@dataclass
class NormalizedResponse:
    """Unified response contract between Router and Agent Loop.

    Guarantees the Agent Loop always receives the same structure
    regardless of whether the response came from the orchestrator,
    a direct LiteLLM call, or any future provider.
    """
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    provider: str = "unknown"
    model: str = "unknown"
    usage: dict = field(default_factory=dict)


def normalize_litellm_tool_call(tc: Any) -> dict:
    """Convert a LiteLLM tool call object to a plain dict."""
    return {
        "id": tc.id,
        "type": "function",
        "function": {
            "name": tc.function.name,
            "arguments": tc.function.arguments,
        },
    }

# Try to import MozaOrchestrator from the installed package
try:
    from moza_orchestrator import MozaOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False
    MozaOrchestrator = None


_RETRYABLE_PATTERNS = re.compile(
    r"(403|429|rate.limit|cloudflare|cloud.flare|unavailable|"
    r"auth|unauthorized|api.key|invalid.key|blocked|forbidden|"
    r"too.many.requests|service.unavailable|connection.refused|"
    r"timeout|timed.out|internal.server.error|bad.gateway)",
    re.IGNORECASE,
)


def _load_keys(prefix: str, count: int = 3) -> list[str]:
    """Load API keys from env vars like PREFIX, PREFIX_2, PREFIX_3."""
    keys: list[str] = []
    for i in range(1, count + 1):
        var = f"{prefix}_{i}" if i > 1 else prefix
        val = os.environ.get(var, "")
        if val:
            keys.append(val)
    return keys


@dataclass
class ProviderEntry:
    name: str
    base_url: str
    models: list[str]
    api_keys: list[str]


class LLMRouter:
    def __init__(self, config: MOZAConfig) -> None:
        self._config = config
        self._health = HealthTracker()
        self._network_recovery_done = False
        
        if ORCHESTRATOR_AVAILABLE and config.use_orchestrator:
            self._orchestrator = MozaOrchestrator()
            self._use_orchestrator = True
            logger.info("LLMRouter: MozaOrchestrator initialized with 19 ranked models across 7 providers")
        else:
            self._orchestrator = None
            self._use_orchestrator = False
            logger.info("LLMRouter: Using fallback single-provider mode")

    @property
    def health(self) -> HealthTracker:
        return self._health

    def _is_retryable(self, error: Exception) -> bool:
        err_str = str(error)
        return bool(_RETRYABLE_PATTERNS.search(err_str))

    def _should_retry(self, error: Exception) -> bool:
        return self._is_retryable(error)

    async def _execute_network_recovery(self) -> None:
        logger.warning("LLMRouter: executing network recovery (ipconfig)")
        commands = [
            ["ipconfig", "/release"],
            ["ipconfig", "/renew"],
            ["ipconfig", "/flushdns"],
        ]
        for cmd in commands:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=30.0
                )
                if proc.returncode != 0:
                    logger.warning(
                        f"Network recovery: {' '.join(cmd)} exited {proc.returncode}: "
                        f"{stderr.decode(errors='replace')[:200]}"
                    )
                else:
                    logger.info(f"Network recovery: {' '.join(cmd)} OK")
            except asyncio.TimeoutError:
                logger.warning(f"Network recovery: {' '.join(cmd)} timed out")
            except FileNotFoundError:
                logger.warning(
                    "Network recovery: ipconfig not found (not Windows or not in PATH)"
                )
                break
            except PermissionError:
                logger.warning(
                    "Network recovery: ipconfig requires Administrator privileges, "
                    "attempting to continue"
                )
            except Exception as e:
                logger.warning(f"Network recovery: {' '.join(cmd)} failed: {e}")

    def _build_kwargs(
        self,
        model: str,
        api_key: str,
        base_url: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tool_choice: str | None = None,
    ) -> dict:
        kwargs: dict = {
            "model": model,
            "messages": messages,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["api_base"] = base_url
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"
            kwargs["parallel_tool_calls"] = False
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if "groq" in base_url:
            kwargs["custom_llm_provider"] = "groq"
        return kwargs

    async def _try_request(
        self,
        model: str,
        api_key: str,
        base_url: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        kwargs = self._build_kwargs(
            model=model,
            api_key=api_key,
            base_url=base_url,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = await litellm.acompletion(**kwargs)
        return response

    async def route(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        browser_mode: bool = False,
        tool_choice: str | None = None,
    ) -> NormalizedResponse:
        """Route request through MozaOrchestrator or fallback to single provider.

        Returns a NormalizedResponse — the unified contract between Router
        and Agent Loop, regardless of provider.

        Args:
            tool_choice: Override tool_choice ("auto", "required", "none", or tool name).
                         Pass "required" to force the LLM to emit a tool call.
        """
        if self._use_orchestrator:
            return await self._route_with_orchestrator(messages, tools, temperature, max_tokens)
        else:
            return await self._route_with_fallback(messages, tools, temperature, max_tokens, browser_mode, tool_choice)
    
    async def _route_with_orchestrator(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> NormalizedResponse:
        """Route request through MozaOrchestrator with intelligent failover."""
        try:
            orchestrator_messages = []
            for i, msg in enumerate(messages):
                if msg.get("role") == "system":
                    orchestrator_messages.append(msg)
                elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                    # Convert assistant tool_calls message to text for provider compatibility
                    tc_desc = "; ".join(
                        f"{tc['function']['name']}({tc['function']['arguments']})"
                        for tc in msg["tool_calls"]
                    )
                    orchestrator_messages.append({
                        "role": "assistant",
                        "content": f"I called tools: {tc_desc}",
                    })
                elif msg.get("role") == "tool":
                    tool_msg = {
                        "role": "user", 
                        "content": f"Tool result: {msg.get('content', '')}"
                    }
                    orchestrator_messages.append(tool_msg)
                else:
                    orchestrator_messages.append(msg)
            
            # Prepare kwargs for orchestrator
            kwargs = {}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if tools:
                kwargs["tools"] = tools
            
            # Make request through orchestrator
            start = time.monotonic()
            orch_result = await self._orchestrator.complete_with_tools(
                orchestrator_messages, **kwargs
            )
            latency = time.monotonic() - start
            
            # Get current stats to determine which provider was used
            last_call = self._orchestrator.call_history[-1] if self._orchestrator.call_history else {}
            
            logger.info(
                f"Router: {last_call.get('provider', 'unknown')}/{last_call.get('model', 'unknown')} "
                f"OK ({latency:.2f}s)"
            )
            
            response_content = orch_result.get("content", "")
            response_tool_calls = orch_result.get("tool_calls", [])
            
            return NormalizedResponse(
                content=response_content or "",
                tool_calls=response_tool_calls,
                provider=last_call.get("provider", "unknown"),
                model=last_call.get("model", "unknown"),
                usage={"total_tokens": last_call.get("tokens", 0)},
            )
            
        except Exception as e:
            logger.error(f"Router: orchestrator failed: {e}")
            
            # Execute network recovery as a last resort
            if not self._network_recovery_done:
                logger.warning("Router: executing network recovery")
                await self._execute_network_recovery()
                self._network_recovery_done = True
                
                # Try one more time
                try:
                    orch_result = await self._orchestrator.complete_with_tools(
                        orchestrator_messages, **kwargs
                    )
                    return NormalizedResponse(
                        content=orch_result.get("content", ""),
                        tool_calls=orch_result.get("tool_calls", []),
                        provider="recovery",
                        model="unknown",
                        usage={"total_tokens": 0},
                    )
                except Exception as retry_e:
                    logger.error(f"Router: recovery attempt also failed: {retry_e}")
            
            notification = (
                "\n\n⚠️ All AI providers exhausted. Please check your internet connection "
                "or try again later."
            )
            raise RuntimeError(f"All providers exhausted. Error: {e}" + notification)
    
    async def _route_with_fallback(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        browser_mode: bool = False,
        tool_choice: str | None = None,
    ) -> NormalizedResponse:
        """Fallback to single-provider direct LiteLLM call (orchestrator unavailable)."""
        from moza.config.models import ProviderConfig
        provider: ProviderConfig = self._config.get_provider()
        kwargs = self._build_kwargs(
            model=provider.model,
            api_key=provider.api_key or "",
            base_url=provider.base_url or "",
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            tool_choice=tool_choice,
        )
        raw = await litellm.acompletion(**kwargs)
        choice = raw.choices[0]
        msg = choice.message
        return NormalizedResponse(
            content=msg.content or "",
            tool_calls=[normalize_litellm_tool_call(tc) for tc in (msg.tool_calls or [])],
            provider=provider.name or "fallback",
            model=provider.model,
            usage={"total_tokens": choice.usage.total_tokens if hasattr(choice, "usage") and choice.usage else 0},
        )

    def summary(self) -> dict:
        """Return summary of router status."""
        if self._use_orchestrator:
            stats = self._orchestrator.get_stats()
            return {
                "orchestrator": {
                    "total_models": 19,
                    "providers": 7,
                    "success_rate": stats["success_rate"],
                    "dead_providers": stats["dead_providers"],
                    "cooldown_providers": stats["cooldown_providers"],
                },
                "health": self._health.summary(),
            }
        else:
            return {
                "orchestrator": {
                    "enabled": False,
                    "mode": "fallback",
                },
                "health": self._health.summary(),
            }

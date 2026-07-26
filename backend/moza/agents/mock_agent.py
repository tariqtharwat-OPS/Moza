import asyncio
import re
import time
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType, ToolResultPayload


_SIMPLE_PATTERNS = re.compile(
    r"^\s*(say|tell|write|give|respond|answer|reply|echo)\b.*\b(hello|hi|hey|bonjour|hola|hi there|greeting)\b",
    re.IGNORECASE,
)
_WH_WORDS = re.compile(r"^\s*(what|who|when|where|why|how)\s", re.IGNORECASE)
_SHORT_ACK = re.compile(r"^\s*(yes|no|maybe|sure|ok|thanks|thank you)\s*$", re.IGNORECASE)
_GREETING_ONLY = re.compile(
    r"^\s*(hi|hey|hello)\b.*$",
    re.IGNORECASE,
)

# Arabic simple greeting patterns (no \b — word boundaries don't work with Arabic)
_ARABIC_CMD_GREET = re.compile(
    r"^\s*(قل|قول|اكتب|جاوب|رد)\s.*(مرحب|سلام)", re.IGNORECASE
)
_ARABIC_GREET_SHORT = re.compile(
    r"^[\s\u0600-\u06FF]{1,30}$"
)
_ARABIC_HAS_GREET = re.compile(r"(مرحب|سلام)", re.IGNORECASE)


def _is_simple_conversational(text: str) -> bool:
    """Detect if the task is a simple conversational request that needs no tools."""
    t = text.strip()
    if not t:
        return False
    if _SIMPLE_PATTERNS.match(t):
        return True
    if _WH_WORDS.match(t) and len(t) < 60:
        return True
    if _SHORT_ACK.match(t):
        return True
    if _GREETING_ONLY.match(t):
        return True
    if _ARABIC_CMD_GREET.match(t):
        return True
    if _ARABIC_HAS_GREET.search(t) and _ARABIC_GREET_SHORT.match(t):
        return True
    if re.match(r"say .+ in one word", t, re.IGNORECASE):
        return True
    return False


def _detect_language(text: str) -> str:
    """Rough language detection: if text contains Arabic chars, respond in Arabic."""
    if re.search(r"[\u0600-\u06FF]", text):
        return "arabic"
    return "english"


_SIMPLE_RESPONSES = {
    "english": {
        "hello": "Hello!",
        "hi": "Hi there!",
        "hey": "Hey!",
        "how are you": "I'm doing great, thanks for asking! How can I help you today?",
        "مرحبا": "Hello!",
        "what is your name": "I'm MOZA, an AI operating system agent.",
        "what's your name": "I'm MOZA, an AI operating system agent.",
    },
    "arabic": {
        "hello": "مرحباً",
        "hi": "مرحباً",
        "hey": "مرحباً",
        "مرحبا": "مرحباً",
    },
}


def _simple_reply(text: str) -> str:
    """Generate an appropriate direct reply for a simple conversational task."""
    lang = _detect_language(text)
    t = text.strip().lower()

    exact_responses = _SIMPLE_RESPONSES[lang]
    for key, reply in exact_responses.items():
        if key in t:
            return reply

    if lang == "arabic":
        return "مرحباً"
    return "Hello! How can I help you today?"


class MockAgent(AgentInterface):
    async def execute(
        self,
        context: ExecutionContext,
    ) -> AsyncGenerator[Event, None]:
        session = context.session
        task = session.tasks[-1] if session.tasks else None
        task_id = task.id if task else "unknown"
        task_desc = task.description if task else ""
        registry = context.tool_registry

        # ── Simple conversational tasks: respond directly, no tools ──────────
        if _is_simple_conversational(task_desc):
            yield Event(
                session_id=session.id,
                task_id=task_id,
                type=EventType.AGENT_THINKING,
                source="mock_agent",
                payload={"content": "Simple request detected. Responding directly."},
            )
            await asyncio.sleep(0.2)

            reply = _simple_reply(task_desc)

            yield Event(
                session_id=session.id,
                task_id=task_id,
                type=EventType.LLM_TOKEN,
                source="mock_agent",
                payload={"content": reply},
            )
            await asyncio.sleep(0.1)

            yield Event(
                session_id=session.id,
                task_id=task_id,
                type=EventType.LLM_FINISHED,
                source="mock_agent",
                payload={"content": reply},
            )
            return

        # ── Complex tasks: use tools ─────────────────────────────────────────
        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="mock_agent",
            payload={"content": f"Analyzing task: {task_desc}"},
        )
        await asyncio.sleep(0.3)
        context.cancellation_token.raise_if_cancelled()

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="mock_agent",
            payload={"content": "I have the context. Breaking down the problem..."},
        )
        await asyncio.sleep(0.3)
        context.cancellation_token.raise_if_cancelled()

        tools = registry.get_all()
        tool_list = ", ".join(t.name for t in tools)

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.TOOL_SELECTED,
            source="mock_agent",
            payload={
                "content": f"Available tools: {tool_list}",
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "version": t.version,
                        "capabilities": t.capabilities,
                        "requires_confirmation": t.requires_confirmation,
                        "is_destructive": t.is_destructive,
                    }
                    for t in tools
                ],
            },
        )
        await asyncio.sleep(0.3)
        context.cancellation_token.raise_if_cancelled()

        for tool in tools:
            yield Event(
                session_id=session.id,
                task_id=task_id,
                type=EventType.TOOL_CALL,
                source="mock_agent",
                payload={
                    "tool": tool.name,
                    "description": tool.description,
                    "capabilities": tool.capabilities,
                    "args": {"action": "demo", "path": "."},
                },
            )
            await asyncio.sleep(0.2)
            context.cancellation_token.raise_if_cancelled()

            try:
                tool_start = time.monotonic()
                raw = await registry.execute_tool(
                    tool.name,
                    action="read",
                    path=".",
                )
                elapsed = (time.monotonic() - tool_start) * 1000
                if isinstance(raw, dict):
                    result_payload = ToolResultPayload(
                        success=raw.get("success", True),
                        duration_ms=raw.get("duration_ms", elapsed),
                        exit_code=raw.get("exit_code", 0),
                        stdout=raw.get("stdout", ""),
                        stderr=raw.get("stderr", ""),
                        metadata={"raw": raw},
                    )
                else:
                    result_payload = ToolResultPayload.ok(
                        stdout=str(raw), duration_ms=elapsed
                    )
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="mock_agent",
                    payload={"tool": tool.name, **result_payload.model_dump()},
                )
            except Exception as e:
                logger.warning(f"MockAgent: tool {tool.name} execution skipped: {e}")
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="mock_agent",
                    payload={
                        "tool": tool.name,
                        **ToolResultPayload.error(str(e)).model_dump(),
                    },
                )
            await asyncio.sleep(0.2)

        context.cancellation_token.raise_if_cancelled()

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.LLM_FINISHED,
            source="mock_agent",
            payload={
                "content": (
                    f"Task completed! Analyzed: '{task_desc}'.\n"
                    f"Used tools: {tool_list}.\n"
                    "Golden Rule of Mutation proven — all tool calls went through "
                    "ToolRegistry -> Tool Execution -> Event Emission."
                ),
            },
        )

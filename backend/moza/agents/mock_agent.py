import asyncio
import time
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType, ToolResultPayload


class MockAgent(AgentInterface):
    async def execute(
        self,
        context: ExecutionContext,
    ) -> AsyncGenerator[Event, None]:
        session = context.session
        task = session.tasks[-1] if session.tasks else None
        task_id = task.id if task else "unknown"
        registry = context.tool_registry

        yield Event(
            session_id=session.id,
            task_id=task_id,
            type=EventType.AGENT_THINKING,
            source="mock_agent",
            payload={"content": f"Analyzing task: {task.description if task else 'unknown'}"},
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
                    f"Task completed! Analyzed: '{task.description if task else 'unknown'}'.\n"
                    f"Used tools: {tool_list}.\n"
                    "Golden Rule of Mutation proven — all tool calls went through "
                    "ToolRegistry -> Tool Execution -> Event Emission."
                ),
            },
        )

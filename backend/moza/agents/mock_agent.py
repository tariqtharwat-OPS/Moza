import asyncio
from collections.abc import AsyncGenerator

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.models import Event, EventType


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
                result = await registry.execute_tool(
                    tool.name,
                    action="read",
                    path=".",
                )
                yield Event(
                    session_id=session.id,
                    task_id=task_id,
                    type=EventType.TOOL_RESULT,
                    source="mock_agent",
                    payload={
                        "tool": tool.name,
                        "result": result,
                        "status": "success",
                    },
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
                        "result": {"warning": str(e)},
                        "status": "skipped",
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

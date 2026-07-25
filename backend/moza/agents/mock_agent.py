import asyncio
from collections.abc import AsyncGenerator

from moza.agents.interfaces import AgentInterface
from moza.core.event_bus import EventBus
from moza.core.models import Event, EventType, Session, Task
from moza.tools.registry import ToolRegistry


class MockAgent(AgentInterface):
    async def execute(
        self,
        session: Session,
        task: Task,
        registry: ToolRegistry,
        event_bus: EventBus,
    ) -> AsyncGenerator[Event, None]:
        yield Event(
            session_id=session.id,
            task_id=task.id,
            type=EventType.AGENT_THINKING,
            source="mock_agent",
            payload={"content": f"Analyzing task: {task.description}"},
        )
        await asyncio.sleep(0.3)

        yield Event(
            session_id=session.id,
            task_id=task.id,
            type=EventType.AGENT_THINKING,
            source="mock_agent",
            payload={"content": "I have the context. Breaking down the problem..."},
        )
        await asyncio.sleep(0.3)

        tools = registry.get_all()
        if tools:
            tool_list = ", ".join(t.name for t in tools)
            yield Event(
                session_id=session.id,
                task_id=task.id,
                type=EventType.TOOL_SELECTED,
                source="mock_agent",
                payload={
                    "content": f"Available tools: {tool_list}",
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "version": t.version,
                            "requires_confirmation": t.requires_confirmation,
                            "is_destructive": t.is_destructive,
                        }
                        for t in tools
                    ],
                },
            )
            await asyncio.sleep(0.3)

        yield Event(
            session_id=session.id,
            task_id=task.id,
            type=EventType.TOOL_CALL,
            source="mock_agent",
            payload={"tool": "mock_executor", "args": {"task": task.description}},
        )
        await asyncio.sleep(0.5)

        yield Event(
            session_id=session.id,
            task_id=task.id,
            type=EventType.TOOL_RESULT,
            source="mock_agent",
            payload={
                "tool": "mock_executor",
                "result": "Simulated execution complete.",
            },
        )

        yield Event(
            session_id=session.id,
            task_id=task.id,
            type=EventType.LLM_FINISHED,
            source="mock_agent",
            payload={
                "content": f"Task completed! Analyzed: '{task.description}'. This is a mock — real agent integration coming next step.",
            },
        )

import asyncio
from collections.abc import AsyncGenerator

from moza.core.models import ExecutionStep, StepType, Task, Workspace
from moza.agents.interfaces import AgentInterface
from moza.tools.registry import ToolRegistry


class MockAgent(AgentInterface):
    async def execute_task(
        self,
        task: Task,
        workspace: Workspace,
        tool_registry: ToolRegistry,
    ) -> AsyncGenerator[ExecutionStep, None]:
        yield ExecutionStep(
            task_id=task.id,
            session_id=task.session_id,
            step_type=StepType.THOUGHT,
            payload={"content": f"Analyzing task: {task.description}"},
        )
        await asyncio.sleep(0.3)

        yield ExecutionStep(
            task_id=task.id,
            session_id=task.session_id,
            step_type=StepType.THOUGHT,
            payload={"content": "I have the context. Breaking down the problem..."},
        )
        await asyncio.sleep(0.3)

        tools = tool_registry.get_all()
        if tools:
            tool_list = ", ".join(t.name for t in tools)
            yield ExecutionStep(
                task_id=task.id,
                session_id=task.session_id,
                step_type=StepType.THOUGHT,
                payload={"content": f"Available tools: {tool_list}"},
            )
            await asyncio.sleep(0.3)

        yield ExecutionStep(
            task_id=task.id,
            session_id=task.session_id,
            step_type=StepType.TOOL_CALL,
            payload={"tool": "mock_executor", "args": {"task": task.description}},
        )
        await asyncio.sleep(0.5)

        yield ExecutionStep(
            task_id=task.id,
            session_id=task.session_id,
            step_type=StepType.TOOL_RESULT,
            payload={
                "tool": "mock_executor",
                "result": "Simulated execution complete.",
            },
        )

        yield ExecutionStep(
            task_id=task.id,
            session_id=task.session_id,
            step_type=StepType.MESSAGE,
            payload={
                "content": f"Task completed! Analyzed: '{task.description}'. This is a mock — real agent integration coming next step."
            },
        )

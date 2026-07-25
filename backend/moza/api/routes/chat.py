import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from moza.agents.interfaces import AgentInterface
from moza.agents.mock_agent import MockAgent
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.models import ExecutionStep, Task, TaskStatus, Workspace
from moza.gateway.interfaces import LLMProvider
from moza.tools.registry import get_tool_registry

router = APIRouter(prefix="/v1", tags=["chat"])


class TaskRequest(BaseModel):
    session_id: str | None = None
    description: str
    workspace_path: str = ""


def get_llm() -> LLMProvider:
    from moza.main import app_state
    return app_state.llm


def get_agent() -> AgentInterface:
    return MockAgent()


@router.post("/task/execute")
async def task_execute(
    request: TaskRequest,
    agent: AgentInterface = Depends(get_agent),
):
    session_id = request.session_id or uuid4().hex[:12]
    workspace = Workspace(root_path=request.workspace_path)
    task = Task(session_id=session_id, description=request.description)

    return EventSourceResponse(
        _task_stream(agent, task, workspace, session_id)
    )


async def _task_stream(
    agent: AgentInterface, task: Task, workspace: Workspace, session_id: str
):
    event_bus: EventBus = get_event_bus()
    queue = event_bus.subscribe(session_id)
    tool_registry = get_tool_registry()

    task.status = TaskStatus.RUNNING

    async def run_agent():
        async for step in agent.execute_task(task, workspace, tool_registry):
            await event_bus.publish(session_id, step)
        task.status = TaskStatus.COMPLETED
        await event_bus.publish_and_complete(session_id,
            ExecutionStep(
                task_id=task.id,
                session_id=session_id,
                step_type="message",
                payload={"content": "", "done": True},
            )
        )

    asyncio.create_task(run_agent())

    try:
        while True:
            step = await queue.get()
            if step is None:
                break
            yield {"event": "step", "data": step.model_dump_json()}
    finally:
        event_bus.unsubscribe(session_id, queue)

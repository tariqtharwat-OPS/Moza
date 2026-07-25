import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from moza.agents.interfaces import AgentInterface
from moza.agents.mock_agent import MockAgent
from moza.core.event_bus import get_event_bus
from moza.core.models import Workspace
from moza.orchestrator.orchestrator import get_orchestrator
from moza.orchestrator.service import TaskService, get_task_service
from moza.core.models import Task

router = APIRouter(prefix="/v1", tags=["task"])


class TaskRequest(BaseModel):
    session_id: str | None = None
    description: str
    workspace_path: str = ""


@router.post("/task/execute")
async def task_execute(request: TaskRequest):
    session_id = request.session_id or uuid4().hex[:12]
    workspace = Workspace(root_path=request.workspace_path)
    task = Task(session_id=session_id, description=request.description)

    orchestrator = get_orchestrator()
    agent: AgentInterface = MockAgent()
    orchestrator.set_agent(agent)

    task_service: TaskService = get_task_service()
    await task_service.submit_task(session_id, task, workspace)

    event_bus = get_event_bus()
    queue = event_bus.subscribe(session_id)

    async def event_stream():
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield {"event": "step", "data": event.model_dump_json()}
        finally:
            event_bus.unsubscribe(session_id, queue)

    return EventSourceResponse(event_stream())

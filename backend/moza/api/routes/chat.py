import asyncio
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from moza.agents.interfaces import AgentInterface
from moza.agents.litellm_tool_agent import LiteLLMToolAgent
from moza.agents.mock_agent import MockAgent
from moza.config.models import MOZAConfig
from moza.core.event_bus import get_event_bus
from moza.core.models import Environment, Task
from moza.orchestrator.orchestrator import get_orchestrator
from moza.orchestrator.service import TaskService, get_task_service

router = APIRouter(prefix="/v1", tags=["task"])


class TaskRequest(BaseModel):
    session_id: str | None = None
    description: str
    workspace_path: str = ""


def _create_agent(agent_type: str, config: MOZAConfig | None = None) -> AgentInterface:
    if agent_type == "litellm" or agent_type == "groq" or agent_type == "openrouter":
        provider = None
        if agent_type != "litellm":
            provider = agent_type
        return LiteLLMToolAgent(config, provider_name=provider, max_steps=15) if config else MockAgent()
    if agent_type == "openhands":
        from moza.agents.openhands_adapter import OpenHandsAdapter
        return OpenHandsAdapter()
    return MockAgent()


@router.post("/task/execute")
async def task_execute(request: Request, body: TaskRequest):
    config: MOZAConfig = request.app.state.config
    session_id = body.session_id or uuid4().hex[:12]
    environment = Environment(filesystem={"root_path": body.workspace_path})
    task = Task(session_id=session_id, description=body.description)

    event_bus = get_event_bus()
    queue = event_bus.subscribe(session_id)

    orchestrator = get_orchestrator()
    if orchestrator.agent is None:
        agent = _create_agent(config.agent_type, config)
        orchestrator.set_agent(agent)

    task_service: TaskService = get_task_service()
    await task_service.submit_task(session_id, task, environment)

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


@router.post("/task/{task_id}/approve")
async def approve_tool(task_id: str):
    task_service = get_task_service()
    ok = await task_service.approve_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No pending approval for task {task_id}")
    return {"ok": True, "task_id": task_id, "action": "approved"}


@router.post("/task/{task_id}/reject")
async def reject_tool(task_id: str):
    task_service = get_task_service()
    ok = await task_service.reject_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No pending approval for task {task_id}")
    return {"ok": True, "task_id": task_id, "action": "rejected"}

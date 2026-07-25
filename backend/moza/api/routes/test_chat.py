"""
Pure LLM Chat Test Route — Phase 2.6 Environment Sanity Check.

Bypasses Orchestrator, ToolRegistry, EventRecorder, and all Agents.
Direct, isolated pipe to LiteLLMAdapter to prove LLM connectivity
and SSE streaming work flawlessly before any tooling is attached.

CRITICAL: This route MUST NOT import or use:
  - Orchestrator / TaskService
  - ToolRegistry / any Tool
  - EventBus / EventRecorder
  - AgentInterface / MockAgent / OpenHandsAdapter
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from moza.config.models import MOZAConfig
from moza.gateway.interfaces import ChatMessage, ChatRequest

router = APIRouter(prefix="/v1/test", tags=["test"])


class TestChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None


@router.post("/chat")
async def test_chat(request: Request, body: TestChatRequest):
    config: MOZAConfig = request.app.state.config
    llm = request.app.state.llm

    messages = []
    if body.system_prompt:
        messages.append(ChatMessage(role="system", content=body.system_prompt))
    messages.append(ChatMessage(role="user", content=body.message))

    chat_request = ChatRequest(messages=messages, stream=True)

    async def event_stream():
        async for token in llm.stream_completion(chat_request):
            yield {"event": "token", "data": token}

    return EventSourceResponse(event_stream())

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from moza.gateway.interfaces import ChatRequest, LLMProvider

router = APIRouter(prefix="/v1", tags=["chat"])


def get_llm() -> LLMProvider:
    from moza.main import app_state
    return app_state.llm


@router.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    llm: LLMProvider = Depends(get_llm),
):
    if request.stream:
        return EventSourceResponse(_stream_generator(llm, request))
    response = await llm.chat_completion(request)
    return response.model_dump(exclude_none=True)


async def _stream_generator(llm: LLMProvider, request: ChatRequest):
    async for chunk in llm.stream_completion(request):
        yield {"event": "delta", "data": chunk}

from collections.abc import AsyncGenerator

import litellm

from moza.config.models import MOZAConfig
from moza.gateway.interfaces import ChatMessage, ChatRequest, ChatResponse, LLMProvider


class LiteLLMAdapter(LLMProvider):
    def __init__(self, config: MOZAConfig) -> None:
        self._config = config
        litellm.drop_params = config.litellm.drop_params
        litellm.add_function_to_prompt = config.litellm.add_function_to_prompt

    def _resolve_model(self, request: ChatRequest) -> str:
        if request.model:
            return request.model
        provider = self._config.default_provider
        return provider.model

    def _build_kwargs(self, request: ChatRequest) -> dict:
        provider = self._config.default_provider
        kwargs: dict = {
            "model": self._resolve_model(request),
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if provider.api_key:
            kwargs["api_key"] = provider.api_key
        if provider.base_url:
            kwargs["api_base"] = provider.base_url
        return kwargs

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        kwargs = self._build_kwargs(request)
        response = await litellm.acompletion(**kwargs)
        return ChatResponse(
            id=response.id,
            model=response.model,
            content=response.choices[0].message.content or "",
            usage=response.usage.model_dump() if response.usage else None,
        )

    async def stream_completion(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        kwargs = self._build_kwargs(request)
        kwargs["stream"] = True
        stream = await litellm.acompletion(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

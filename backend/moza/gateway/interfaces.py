from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: dict | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse: ...

    @abstractmethod
    async def stream_completion(
        self, request: ChatRequest
    ) -> AsyncGenerator[str, None]: ...

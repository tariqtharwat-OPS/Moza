from abc import ABC, abstractmethod
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    parameters: list[ToolParameter] = Field(default_factory=list)
    returns: str = ""
    requires_confirmation: bool = False
    is_destructive: bool = False
    capabilities: list[str] = Field(default_factory=list)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any: ...

    async def on_load(self) -> None:
        """Called when the tool is loaded into the registry."""
        pass

    async def on_unload(self) -> None:
        """Called when the tool is removed from the registry."""
        pass


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    async def load(self, tool: BaseTool) -> None:
        logger.info(f"Loading tool: {tool.name} v{tool.version}")
        self._tools[tool.name] = tool
        await tool.on_load()

    def register(self, tool: BaseTool) -> None:
        """Sync alias for load() - prefer async load() for new code."""
        self._tools[tool.name] = tool

    async def unload(self, tool_name: str) -> None:
        tool = self._tools.pop(tool_name, None)
        if tool:
            logger.info(f"Unloading tool: {tool_name}")
            await tool.on_unload()

    async def reload(self, tool_name: str) -> None:
        existing = self._tools.get(tool_name)
        if existing:
            logger.info(f"Reloading tool: {tool_name}")
            await existing.on_unload()
            await existing.on_load()

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_all(self) -> list[BaseTool]:
        return list(self._tools.values())

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool not found in registry: {name}")
        return await tool.execute(**kwargs)

    def get_capabilities(self) -> dict[str, list[str]]:
        return {
            tool.name: tool.capabilities
            for tool in self._tools.values()
        }


_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry

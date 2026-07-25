from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from moza.core.models import ExecutionStep, Task, Workspace
from moza.tools.registry import ToolRegistry


class AgentInterface(ABC):
    @abstractmethod
    async def execute_task(
        self,
        task: Task,
        workspace: Workspace,
        tool_registry: ToolRegistry,
    ) -> AsyncGenerator[ExecutionStep, None]: ...

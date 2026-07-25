from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from moza.core.context import ExecutionContext
from moza.core.models import Event


class AgentInterface(ABC):
    """
    Abstract base contract for all MOZA agents (OpenHands, Aider, Cline, etc.).

    GOLDEN RULE: Agents MUST NEVER write to the Workspace directly.
    All mutations MUST flow through: Agent -> ToolRegistry -> Tool Execution
    -> Event Emission -> Workspace Update.
    """

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
    ) -> AsyncGenerator[Event, None]: ...

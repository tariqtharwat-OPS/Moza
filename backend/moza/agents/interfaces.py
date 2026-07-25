from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from moza.core.event_bus import EventBus
from moza.core.models import Event, Session, Task
from moza.tools.registry import ToolRegistry


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
        session: Session,
        task: Task,
        registry: ToolRegistry,
        event_bus: EventBus,
    ) -> AsyncGenerator[Event, None]: ...

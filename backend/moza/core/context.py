from dataclasses import dataclass

from moza.core.cancellation import CancellationToken
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.models import Environment, Session
from moza.tools.registry import ToolRegistry, get_tool_registry


@dataclass
class ExecutionContext:
    """
    Unified execution context passed to all Agents.

    Contains everything an Agent needs to execute a Task within a Session,
    including the CancellationToken for cooperative cancellation.

    GOLDEN RULE: Agents MUST NEVER write to the Environment directly.
    All mutations MUST flow through: Agent -> ToolRegistry -> Tool Execution
    -> Event Emission -> Environment Update.
    """
    session: Session
    environment: Environment
    tool_registry: ToolRegistry
    event_bus: EventBus
    cancellation_token: CancellationToken

    @classmethod
    def build(
        cls,
        session: Session,
        environment: Environment,
        tool_registry: ToolRegistry | None = None,
        event_bus: EventBus | None = None,
        workspace: Environment | None = None,
    ) -> "ExecutionContext":
        env = environment or workspace
        return cls(
            session=session,
            environment=env,
            tool_registry=tool_registry or get_tool_registry(),
            event_bus=event_bus or get_event_bus(),
            cancellation_token=CancellationToken(),
        )

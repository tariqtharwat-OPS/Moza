"""
Task Orchestrator for MOZA AI Operating System.

GOLDEN RULE OF MUTATION:
Agents MUST NEVER write to the Workspace directly. All mutations MUST flow through:
    Agent -> ToolRegistry -> Tool Execution -> Event Emission -> Workspace Update.
This ensures 100% traceability and replayability.

The Orchestrator is the central dispatcher:
    1. Receives Tasks from the API layer.
    2. Assigns Tasks to Agents.
    3. Routes Events from Agents to the EventBus.
    4. Manages Task lifecycle (submit/cancel/resume).
"""

import asyncio
from datetime import datetime, timezone

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.models import Event, EventType, Session, Task, TaskStatus, Workspace
from moza.tools.registry import ToolRegistry, get_tool_registry


class Orchestrator:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._agent: AgentInterface | None = None
        self._event_bus: EventBus = get_event_bus()
        self._tool_registry: ToolRegistry = get_tool_registry()

    def set_agent(self, agent: AgentInterface) -> None:
        self._agent = agent

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def create_session(self, session_id: str, workspace: Workspace) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(
                id=session_id, workspace=workspace
            )
        return self._sessions[session_id]

    async def submit_task(
        self, session_id: str, task: Task, workspace: Workspace
    ) -> None:
        if self._agent is None:
            raise RuntimeError("No agent configured in orchestrator")

        session = self.create_session(session_id, workspace)
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.now(timezone.utc)
        session.tasks.append(task)

        context = ExecutionContext.build(
            session=session,
            workspace=workspace,
            tool_registry=self._tool_registry,
            event_bus=self._event_bus,
        )

        started_event = Event(
            session_id=session_id,
            task_id=task.id,
            type=EventType.AGENT_STARTED,
            source="orchestrator",
            payload={"description": task.description},
        )
        session.execution_history.append(started_event)
        await self._event_bus.publish(session_id, started_event)

        async_task = asyncio.create_task(
            self._run_agent(context, session_id, task, session)
        )
        self._running_tasks[task.id] = async_task

    async def _run_agent(
        self,
        context: ExecutionContext,
        session_id: str,
        task: Task,
        session: Session,
    ) -> None:
        try:
            assert self._agent is not None
            async for event in self._agent.execute(context):
                session.execution_history.append(event)
                await self._event_bus.publish(session_id, event)

            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.now(timezone.utc)

            completed_event = Event(
                session_id=session_id,
                task_id=task.id,
                type=EventType.TASK_COMPLETED,
                source="orchestrator",
                payload={"task_id": task.id},
            )
            session.execution_history.append(completed_event)
            await self._event_bus.publish_and_complete(session_id, completed_event)
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.updated_at = datetime.now(timezone.utc)
            context.cancellation_token.cancel()
            cancelled_event = Event(
                session_id=session_id,
                task_id=task.id,
                type=EventType.TASK_FAILED,
                source="orchestrator",
                payload={"error": "Task cancelled", "task_id": task.id},
            )
            session.execution_history.append(cancelled_event)
            await self._event_bus.publish_and_complete(session_id, cancelled_event)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.updated_at = datetime.now(timezone.utc)
            failed_event = Event(
                session_id=session_id,
                task_id=task.id,
                type=EventType.TASK_FAILED,
                source="orchestrator",
                payload={"error": str(e), "task_id": task.id},
            )
            session.execution_history.append(failed_event)
            await self._event_bus.publish_and_complete(session_id, failed_event)
        finally:
            self._running_tasks.pop(task.id, None)

    async def cancel_task(self, task_id: str) -> bool:
        asyncio_task = self._running_tasks.get(task_id)
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            return True
        return False

    async def resume_task(self, task_id: str) -> None:
        raise NotImplementedError("Task resume not yet implemented")


_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

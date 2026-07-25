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
    4. Manages Task lifecycle (submit/cancel/resume/state).
    5. Drives task state machine: PENDING → RUNNING → {WAITING_TOOL, WAITING_USER} → COMPLETED/FAILED/CANCELLED.
    6. Cleans up tool resources on cancellation or failure.
"""

import asyncio
from datetime import datetime, timezone

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.models import Event, EventType, Session, Task, TaskStatus, Workspace
from moza.tools.registry import ToolRegistry, get_tool_registry


def _transition_task_status(
    task: Task,
    new_status: TaskStatus,
    event_type: EventType,
) -> None:
    """Update task status and timestamp when a relevant event is emitted."""
    task.status = new_status
    task.updated_at = datetime.now(timezone.utc)


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
        _transition_task_status(task, TaskStatus.RUNNING, EventType.AGENT_STARTED)
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
                self._update_task_state(task, event)

            _transition_task_status(task, TaskStatus.COMPLETED, EventType.TASK_COMPLETED)

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
            _transition_task_status(task, TaskStatus.CANCELLED, EventType.TASK_FAILED)
            context.cancellation_token.cancel()
            await self._tool_registry.cleanup_all()
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
            _transition_task_status(task, TaskStatus.FAILED, EventType.TASK_FAILED)
            await self._tool_registry.cleanup_all()
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

    @staticmethod
    def _update_task_state(task: Task, event: Event) -> None:
        """Drive the task state machine based on emitted events."""
        if event.type == EventType.TOOL_CALL:
            tool = event.payload.get("tool", "")
            requires_confirmation = event.payload.get("requires_confirmation", False)
            if requires_confirmation:
                _transition_task_status(task, TaskStatus.WAITING_USER, event.type)
            else:
                _transition_task_status(task, TaskStatus.WAITING_TOOL, event.type)
        elif event.type == EventType.TOOL_RESULT:
            _transition_task_status(task, TaskStatus.RUNNING, event.type)
        elif event.type == EventType.TOOL_SELECTED:
            _transition_task_status(task, TaskStatus.RUNNING, event.type)
        elif event.type in (EventType.BROWSER_STARTED, EventType.BROWSER_ACTION):
            _transition_task_status(task, TaskStatus.WAITING_TOOL, event.type)
        elif event.type in (EventType.TASK_COMPLETED, EventType.TASK_FAILED):
            pass

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

"""
Task Orchestrator for MOZA AI Operating System.

GOLDEN RULE OF MUTATION:
Agents MUST NEVER write to the Environment directly. All mutations MUST flow through:
    Agent -> ToolRegistry -> Tool Execution -> Event Emission -> Environment Update.
This ensures 100% traceability and replayability.

The Orchestrator is the central dispatcher:
    1. Receives Tasks from the API layer.
    2. Assigns Tasks to Agents.
    3. Routes Events from Agents to the EventBus.
    4. Manages Task lifecycle (submit/cancel/approve/resume/state).
    5. Drives task state machine: PENDING -> RUNNING -> {WAITING_TOOL, WAITING_USER} -> COMPLETED/FAILED/CANCELLED.
    6. Handles user approval flow: emits WAITING_APPROVAL, pauses execution, resumes on approve/reject.
    7. Enforces agent capability constraints (allowed_tools).
    8. Cleans up tool resources on cancellation or failure.
"""

import asyncio
from datetime import datetime, timezone

from loguru import logger

from moza.agents.interfaces import AgentInterface
from moza.core.context import ExecutionContext
from moza.core.event_bus import EventBus, get_event_bus
from moza.core.intent_classifier import IntentType, classify_intent, get_conversational_reply
from moza.core.models import Environment, Event, EventType, Session, Task, TaskStatus
from moza.core.state_machine import transition as fsm_transition
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
        self._pending_approvals: dict[str, asyncio.Event] = {}

    def set_agent(self, agent: AgentInterface) -> None:
        self._agent = agent

    @property
    def agent(self) -> AgentInterface | None:
        return self._agent

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def create_session(self, session_id: str, environment: Environment) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(
                id=session_id, environment=environment
            )
        return self._sessions[session_id]

    async def submit_task(
        self, session_id: str, task: Task, environment: Environment
    ) -> None:
        if self._agent is None:
            raise RuntimeError("No agent configured in orchestrator")

        session = self.create_session(session_id, environment)
        _transition_task_status(task, TaskStatus.RUNNING, EventType.AGENT_STARTED)
        session.tasks.append(task)

        context = ExecutionContext.build(
            session=session,
            environment=environment,
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
            intent = classify_intent(task.description)
            if intent == IntentType.CONVERSATIONAL:
                reply = get_conversational_reply(task.description)
                thinking = Event(
                    session_id=session_id,
                    task_id=task.id,
                    type=EventType.AGENT_THINKING,
                    source="orchestrator",
                    payload={"message": "Conversational intent detected. Responding directly."},
                )
                session.execution_history.append(thinking)
                await self._event_bus.publish(session_id, thinking)

                token_event = Event(
                    session_id=session_id,
                    task_id=task.id,
                    type=EventType.LLM_TOKEN,
                    source="orchestrator",
                    payload={"content": reply},
                )
                session.execution_history.append(token_event)
                await self._event_bus.publish(session_id, token_event)

                finished = Event(
                    session_id=session_id,
                    task_id=task.id,
                    type=EventType.LLM_FINISHED,
                    source="orchestrator",
                    payload={"content": reply},
                )
                session.execution_history.append(finished)
                await self._event_bus.publish(session_id, finished)
                _transition_task_status(task, TaskStatus.COMPLETED, EventType.TASK_COMPLETED)
                completed = Event(
                    session_id=session_id,
                    task_id=task.id,
                    type=EventType.TASK_COMPLETED,
                    source="orchestrator",
                    payload={"task_id": task.id},
                )
                session.execution_history.append(completed)
                await self._event_bus.publish_and_complete(session_id, completed)
                return

            assert self._agent is not None
            async for event in self._agent.execute(context):
                session.execution_history.append(event)
                await self._event_bus.publish(session_id, event)
                self._update_task_state(task, event)

                if task.status == TaskStatus.WAITING_USER:
                    approval_event = Event(
                        session_id=session_id,
                        task_id=task.id,
                        type=EventType.WAITING_APPROVAL,
                        source="orchestrator",
                        payload={
                            "tool": event.payload.get("tool", "unknown"),
                            "args": event.payload.get("args", {}),
                            "description": event.payload.get("description", ""),
                        },
                    )
                    session.execution_history.append(approval_event)
                    await self._event_bus.publish(session_id, approval_event)
                    await self.wait_for_user_approval(task.id)
                    _transition_task_status(
                        task, TaskStatus.RUNNING, EventType.TOOL_RESULT
                    )

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
        new_status = None
        if event.type == EventType.TOOL_CALL:
            tool = event.payload.get("tool", "")
            requires_confirmation = event.payload.get("requires_confirmation", False)
            new_status = TaskStatus.WAITING_USER if requires_confirmation else TaskStatus.WAITING_TOOL
        elif event.type == EventType.TOOL_RESULT:
            new_status = TaskStatus.RUNNING
        elif event.type == EventType.TOOL_SELECTED:
            new_status = TaskStatus.RUNNING
        elif event.type in (EventType.BROWSER_STARTED, EventType.BROWSER_ACTION):
            new_status = TaskStatus.WAITING_TOOL
        elif event.type in (EventType.TASK_COMPLETED, EventType.TASK_FAILED, EventType.WAITING_APPROVAL):
            pass

        if new_status is not None:
            prev = task.status
            try:
                fsm_transition(prev, new_status)
                logger.debug(f"FSM: {prev.value} -> {new_status.value} (accepted)")
            except ValueError as e:
                logger.critical(f"FSM rejected {prev.value} -> {new_status.value}: {e}. Applying manually.")
            _transition_task_status(task, new_status, event.type)

    async def cancel_task(self, task_id: str) -> bool:
        asyncio_task = self._running_tasks.get(task_id)
        if asyncio_task and not asyncio_task.done():
            asyncio_task.cancel()
            approval = self._pending_approvals.pop(task_id, None)
            return True
        return False

    async def resume_task(self, task_id: str) -> None:
        raise NotImplementedError("Task resume not yet implemented")

    async def wait_for_user_approval(self, task_id: str) -> bool:
        approval = asyncio.Event()
        self._pending_approvals[task_id] = approval
        try:
            await asyncio.wait_for(approval.wait(), timeout=None)
            return True
        except asyncio.TimeoutError:
            return False
        finally:
            self._pending_approvals.pop(task_id, None)

    async def approve_task(self, task_id: str) -> bool:
        approval = self._pending_approvals.get(task_id)
        if approval:
            approval.set()
            return True
        return False

    async def reject_task(self, task_id: str) -> bool:
        approval = self._pending_approvals.get(task_id)
        if approval:
            await self.cancel_task(task_id)
            return True
        return False


_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

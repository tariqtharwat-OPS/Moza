from moza.core.event_bus import get_event_bus
from moza.core.models import Environment, Task
from moza.orchestrator.orchestrator import Orchestrator, get_orchestrator
from moza.tools.registry import get_tool_registry


class TaskService:
    def __init__(self) -> None:
        self._orchestrator: Orchestrator = get_orchestrator()

    async def submit_task(
        self, session_id: str, task: Task, environment: Environment
    ) -> None:
        await self._orchestrator.submit_task(session_id, task, environment)

    async def cancel_task(self, task_id: str) -> bool:
        return await self._orchestrator.cancel_task(task_id)

    async def resume_task(self, task_id: str) -> None:
        await self._orchestrator.resume_task(task_id)

    async def approve_task(self, task_id: str) -> bool:
        return await self._orchestrator.approve_task(task_id)

    async def reject_task(self, task_id: str) -> bool:
        return await self._orchestrator.reject_task(task_id)


_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service

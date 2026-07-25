import asyncio
from collections import defaultdict

from moza.core.models import ExecutionStep


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[ExecutionStep]]] = defaultdict(list)

    def subscribe(self, session_id: str) -> asyncio.Queue[ExecutionStep]:
        queue: asyncio.Queue[ExecutionStep] = asyncio.Queue()
        self._queues[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[ExecutionStep]) -> None:
        if session_id in self._queues:
            self._queues[session_id].remove(queue)
            if not self._queues[session_id]:
                del self._queues[session_id]

    async def publish(self, session_id: str, step: ExecutionStep) -> None:
        for queue in self._queues.get(session_id, []):
            await queue.put(step)

    async def publish_and_complete(self, session_id: str, step: ExecutionStep) -> None:
        await self.publish(session_id, step)
        for queue in self._queues.get(session_id, []):
            await queue.put(None)  # sentinel


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

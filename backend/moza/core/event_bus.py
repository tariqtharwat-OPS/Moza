import asyncio
from collections import defaultdict

from loguru import logger

from moza.core.event_recorder import get_recorder
from moza.core.models import Event


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[Event | None]]] = defaultdict(list)
        self._recorder = get_recorder()

    def subscribe(self, session_id: str) -> asyncio.Queue[Event | None]:
        queue: asyncio.Queue[Event | None] = asyncio.Queue()
        self._queues[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[Event | None]) -> None:
        if session_id in self._queues:
            self._queues[session_id].remove(queue)
            if not self._queues[session_id]:
                del self._queues[session_id]

    async def publish(self, session_id: str, event: Event) -> None:
        try:
            self._recorder.record(event)
        except Exception as e:
            logger.warning(f"EventBus: recorder failed for event {event.id}: {e}")
        for queue in self._queues.get(session_id, []):
            await queue.put(event)

    async def publish_and_complete(self, session_id: str, event: Event) -> None:
        await self.publish(session_id, event)
        for queue in self._queues.get(session_id, []):
            await queue.put(None)


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

import asyncio


class CancellationException(Exception):
    pass


class CancellationToken:
    """
    Async-friendly cancellation signal.

    Can be awaited via `wait()` or polled via `is_cancelled()`.
    Propagates cleanly through async contexts — when cancelled,
    any code can call `raise_if_cancelled()` to abort cooperative tasks.
    """

    def __init__(self) -> None:
        self._event = asyncio.Event()

    def cancel(self) -> None:
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise CancellationException("Task has been cancelled.")

    async def wait(self) -> None:
        await self._event.wait()

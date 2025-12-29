import asyncio
from collections.abc import Awaitable, Callable

AsyncHandler = Callable[..., Awaitable[None]]


class AsyncEvent:
    """Class for asynchronous notification of all subscribers."""

    def __init__(self):
        self._handlers: dict[str, AsyncHandler] = {}
        self._lock = asyncio.Lock()

    async def add(self, key: str, handler: AsyncHandler):
        """Add new handler to the handlers list.

        Args:
            key (str): Unique identifier for the handler
            handler (AsyncHandler): Asynchronous callable object for hotifications:
                Example:
                    async def my_handler(some_arg1, some_arg2, *args, **kwargs):...
        """
        async with self._lock:
            if key not in self._handlers:
                self._handlers[key] = handler

    async def remove(self, key: str):
        """Remove the handler from the list."""
        async with self._lock:
            self._handlers.pop(key, None)

    async def emit(self, *args, **kwargs):
        """ "Notifies all subscribers."""
        async with self._lock:
            handlers = list(self._handlers.values())  # snapshot

        await asyncio.gather(
            *(handler(*args, **kwargs) for handler in handlers), return_exceptions=False
        )

    def is_empty(self) -> bool:
        """Checks whether subscribers exist."""
        return not self._handlers

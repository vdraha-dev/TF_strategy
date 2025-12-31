import asyncio
import logging
from contextlib import suppress

import websockets

from ..async_event import AsyncHandler

logger = logging.getLogger(__name__)


class AsyncWSListener:
    """Lightweight listener for WS connection."""

    def __init__(
        self,
        url: str,
        msg_handler: AsyncHandler,
        reconnect_delay: float = 5.0,
    ):
        self._url = url
        self.msg_handler = msg_handler
        self.reconnect_delay = reconnect_delay

        self._task: asyncio.Task | None = None
        self._send_task: asyncio.Task | None = None

        self._ws: websockets.ClientConnection | None = None
        self._send_queue: asyncio.Queue[str | None] = asyncio.Queue()

        self._start_event = asyncio.Event()
        self._stop_event = asyncio.Event()

    @property
    def url(self):
        """URL for connection"""
        return self._url

    async def _listen(self):
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self.url) as ws:
                    self._ws = ws
                    self._start_event.set()  # signal about correct connection

                    # We launch a separate task for sending messages.
                    self._send_task = asyncio.create_task(self._send_loop())

                    async for msg in ws:
                        await self.msg_handler(msg)

            except (websockets.ConnectionClosed, OSError) as e:
                self._ws = None
                self._start_event.clear()

                if self._stop_event.is_set():
                    # if stop_event is set, then dont reconnect
                    break

                logger.error(
                    f"[{self.url}] Connection lost: {e}. "
                    f"Reconnecting in {self.reconnect_delay}s..."
                )
                await asyncio.sleep(self.reconnect_delay)
            finally:
                # Stopped send loop when connection is broken
                if self._send_task and not self._send_task.done():
                    await self._close_send_loop()

    async def _send_loop(self):
        """Loop for sending messages from queue."""
        while self._ws is not None and not self._stop_event.is_set():
            try:
                msg = await self._send_queue.get()

                if msg is None:  # signal for closing
                    return

                if self._ws:
                    try:
                        await self._ws.send(msg)
                    except Exception as e:
                        logger.error(f"[{self.url}] Failed to send message: {e}")

            except asyncio.CancelledError:
                break

    async def _close_send_loop(self):
        """Correctly stops send_loop."""
        if self._send_task and not self._send_task.done():
            await self._send_queue.put(None)
            try:
                await asyncio.wait_for(self._send_task, timeout=5.0)
            except TimeoutError:
                self._send_task.cancel()
                await asyncio.gather(self._send_task, return_exceptions=True)

    async def start(self):
        """Starts the listener for ws connection."""
        if self._stop_event:
            self._start_event.clear()
            self._stop_event.clear()

            self._task = asyncio.create_task(self._listen())

            # wait for successful connection
            try:
                await asyncio.wait_for(self._start_event.wait(), timeout=10.0)
            except TimeoutError as e:
                # stops if connection broken
                await self.stop()
                raise ConnectionError(
                    f"Failed to connect to {self.url} within 10s"
                ) from e

    async def stop(self):
        """Stops the listener for ws connection."""
        if not self._stop_event.is_set():
            self._stop_event.set()

            # closes ws connection
            if self._ws:
                with suppress(Exception):
                    await self._ws.close()

            # stops the main task
            if self._task and not self._task.done():
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

    async def send(self, msg: str):
        """Adds a message to the queue for sending."""
        if msg is not None and not self._stop_event.is_set():
            await self._send_queue.put(msg)

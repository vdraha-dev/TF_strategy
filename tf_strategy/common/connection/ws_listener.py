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

        self._stop_event.set()

    @property
    def url(self):
        """URL for connection."""
        return self._url

    @property
    def is_started(self):
        """Return True if the listener is started."""
        return not self._stop_event.is_set()

    @property
    def is_connected(self):
        """Return True if connection is open."""
        return self._start_event.is_set()

    async def _listen(self):
        while self.is_started:
            need_reconnect = False
            try:
                async with websockets.connect(self.url) as ws:
                    self._ws = ws
                    self._start_event.set()  # signal about created connection

                    # We launch a separate task for sending messages.
                    self._send_task = asyncio.create_task(self._send_loop())

                    async for msg in ws:
                        await self.msg_handler(msg)

            except (websockets.ConnectionClosed, OSError) as e:
                need_reconnect = True

                logger.error(
                    f"[{self.url}] Connection lost: {e}. "
                    f"Reconnecting in {self.reconnect_delay}s..."
                )
            finally:
                self._ws = None
                self._start_event.clear()

                # Stopped send loop when connection is broken
                if self._send_task and not self._send_task.done():
                    await self._close_send_loop()

            if need_reconnect:
                await asyncio.sleep(self.reconnect_delay)

    async def _send_loop(self):
        """Loop for sending messages from queue."""
        while self._ws is not None and self.is_started:
            try:
                msg = await self._send_queue.get()

                if msg is None:  # signal for closing
                    return

                if self._ws and self.is_connected:
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
        if not self.is_started:
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
        if self.is_started:
            self._stop_event.set()
            self._start_event.clear()

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
        if msg is not None and self.is_started:
            await self._send_queue.put(msg)

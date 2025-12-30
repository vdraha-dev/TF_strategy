import asyncio
import logging

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
        self.url = url
        self.msg_handler = msg_handler
        self.reconnect_delay = reconnect_delay

        self._task: asyncio.Task | None = None
        self._send_task: asyncio.Task | None = None
        self._stopped = True

        self._ws: websockets.ClientConnection | None = None
        self._send_queue: asyncio.Queue[str | None] = asyncio.Queue()

        self._is_connected = asyncio.Event()

    async def _listen(self):
        while not self._stopped:
            try:
                async with websockets.connect(self.url) as ws:
                    self._ws = ws
                    self._is_connected.set()

                    # We launch a separate task for sending messages.
                    self._send_task = asyncio.create_task(self._send_loop())
                    async for msg in ws:
                        await self.msg_handler(msg)
            except (websockets.ConnectionClosed, OSError) as e:
                self._ws = None

                logger.error(
                    f"[{self.url}] Connection lost: {e}. Reconnecting in {self.reconnect_delay}s..."
                )
                await asyncio.sleep(self.reconnect_delay)

    async def _send_loop(self):
        while self._ws is not None and not self._stopped:
            msg = await self._send_queue.get()

            if msg is None:
                return

            if self._ws:
                try:
                    await self._ws.send(msg)
                except Exception as e:
                    logger.error(f"[{self.url}] Failed to send message: {e}")

    async def _close_send_loop(self):
        # need for close _send_loop
        if self._send_task and not self._send_task.done():
            await self._send_queue.put(None)
            await self._send_task

    async def start(self):
        """Starts the listener for ws connection."""
        if self._stopped:
            self._stopped = False
            self._task = asyncio.create_task(self._listen())
            await self._is_connected.wait()

    async def stop(self):
        """Stops the listener for ws connection."""
        if not self._stopped:
            self._stopped = True
            await self._close_send_loop()
            if self._task:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

    async def send(self, msg: str):
        """Adds a message to the queue for sending."""
        if msg is None:
            return
        await self._send_queue.put(msg)

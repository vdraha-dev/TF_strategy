import asyncio

import httpx

from tf_strategy.common.connection.ws_listener import AsyncHandler, AsyncWSListener
from tf_strategy.common.tools import remove_event


class PrivateWSListener(AsyncWSListener):
    def __init__(
        self,
        url: str,
        api_key: str,
        msg_handler: AsyncHandler,
        reconnect_delay: float = 5.0,
    ):
        super().__init__(url, msg_handler, reconnect_delay)
        self._api_key = api_key
        self._listen_key: str | None = None
        self._keepalive_task: asyncio.Task | None = None

        self._session = httpx.AsyncClient(
            base_url="https://api.binance.com/api/v3/userDataStream"
        )

    @property
    def url(self):
        return self._url.rstrip("/") + "/" + self._listen_key

    async def start(self):
        if not self.is_started:

            # blocking repeated starts
            async with remove_event(self._stop_event):
                # when we are in this block others see self.is_started = True
                # create listener key for create private connection
                self._listen_key = await self._create_listen_key()

            await super().start()

            # create task for updating the listen key every 30 min
            self._keepalive_task = asyncio.create_task(self._keepalive_listen_key())

    async def stop(self):
        if self.is_started:
            await super().stop()
            if self._keepalive_task:
                await asyncio.gather(self._keepalive_task, return_exceptions=True)

    async def _create_listen_key(self) -> str:
        resp: httpx.Response = await self._session.post(
            headers={"X-MBX-APIKEY": self._api_key},
        )
        resp.raise_for_status()
        data = await resp.json()
        return data["listenKey"]

    async def _keepalive_listen_key(self):
        interval = 30 * 60

        while self.is_started:
            try:
                # wait for timeout or set()
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
                break  # stop_event was set
            except TimeoutError:
                pass  # Timeout - time to update the listen key

            try:
                response = await self._session.put(
                    "",
                    headers={"X-MBX-APIKEY": self._api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as e:
                print(f"Keepalive failed: {e}")

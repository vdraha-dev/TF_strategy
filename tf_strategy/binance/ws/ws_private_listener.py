import asyncio

import httpx

from tf_strategy.common.connection.ws_listener import AsyncHandler, AsyncWSListener


class PrivateWSListener(AsyncWSListener):
    def __init__(
        self,
        url: str,
        api_key: str,
        msg_handler: AsyncHandler,
        reconnect_delay: float = 5.0,
    ):
        super().__init__(url, msg_handler, reconnect_delay)
        self._p_url = url
        self._api_key = api_key
        self._listen_key: str | None = None
        self._keepalive_task: asyncio.Task | None = None

        self._session = httpx.AsyncClient(
            base_url="https://api.binance.com/api/v3/userDataStream"
        )

    async def start(self):
        if self._stopped:
            self._listen_key = await self._create_listen_key()
            self._url = self._p_url.rstrip("/") + "/" + self._listen_key

            await super().start()
            self._keepalive_task = asyncio.create_task(self._keepalive_listen_key())

    async def stop(self):
        if not self._stopped:
            await super().stop()
            if self._keepalive_task:
                self._keepalive_task.cancel()
                await asyncio.gather(self._keepalive_task, return_exceptions=True)

    async def _create_listen_key(self) -> str:
        resp: httpx.Response = await self._session.post(
            headers={"X-MBX-APIKEY": self._api_key},
        )
        resp.raise_for_status()
        data = await resp.json()
        return data["listenKey"]

    async def _keepalive_listen_key(self):
        while not self._stopped:
            await asyncio.sleep(30 * 60)
            try:
                response: httpx.Response = await self._session.put(
                    headers={"X-MBX-APIKEY": self._api_key},
                )
                response.raise_for_status()
            except httpx.TimeoutException:
                await asyncio.sleep(self.reconnect_delay)

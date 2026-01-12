import logging
import time
from uuid import uuid4

import orjson
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

from tf_strategy.binance.schemas import BalanceForAsset, OrderReport
from tf_strategy.common.async_event import AsyncEvent, AsyncHandler
from tf_strategy.common.connection.ws_listener import AsyncWSListener
from tf_strategy.common.tools import get_signed_payload

logger = logging.getLogger(__name__)


class BinancePrivateWS:
    """"""

    def __init__(
        self,
        url: str,
        api_key: str,
        private_key: PrivateKeyTypes,
        reconnect_delay: float = 5,
    ):
        self._url = url
        self._api_key: str = api_key
        self._private_key = private_key
        self._reconnect_delay = reconnect_delay

        self._is_started = False
        self._listener: AsyncWSListener | None = None

        self._wallet_eventer: AsyncEvent | None = None
        self._orders_eventer: AsyncEvent | None = None

    async def start(self):
        if not self._is_started:
            self._is_started = True
            logger.info("Private Binance connection is starting ...")
            self._listener = AsyncWSListener(
                url=self._url,
                on_message=self._msg_preprocessing,
                reconnect_delay=self._reconnect_delay,
                on_connected=self._on_connected,
            )

            self._wallet_eventer = AsyncEvent()
            self._orders_eventer = AsyncEvent()

            await self._listener.start()

    async def stop(self):
        if self._is_started:
            self._is_started = False
            logger.info("Private Binance connection is stopping ...")
            await self._listener.stop()
            self._listenert = None
            self._wallet_eventer = None
            self._orders_eventer = None

    async def wallet_subscribe(self, handler: AsyncHandler) -> str:
        """
        Subscribe to Wallet updates.

        Registers an asynchronous handler that will be
        invoked for each incomin gwallet update.

        Args:
            handler (AsyncHandler):
                Asynchronous callback invoked on each wallet event.

        Returns:
            str:
                Unique handler token used to unsubscribe from the stream.
        """
        token = uuid4()
        await self._wallet_eventer.add(token, handler)
        return token

    async def wallet_unsubscribe(self, handler_token: str):
        """
        Unsubscribe from Wallet events.


        Args:
            handler_token (str): Handler token for unsubscribing.
        """
        await self._orders_eventer.remove(handler_token)

    async def orders_subscribe(self, handler: AsyncHandler) -> str:
        """
        Subscribe to Orders updates.

        Registers an asynchronous handler that will be
        invoked for each incoming order update.

        Args:
            handler (AsyncHandler):
                Asynchronous callback invoked on each order event.

        Returns:
            str:
                Unique handler token used to unsubscribe from the stream.
        """
        token = uuid4()
        await self._orders_eventer.add(token, handler)
        return token

    async def orders_unsubscribe(self, handler_token: str):
        """
        Unsubscribe from Wallet events.


        Args:
            handler_token (str): Handler token for unsubscribing.
        """
        await self._orders_eventer.remove(handler_token)

    async def _on_connected(self):
        await self._log_on_subscription()

    async def _log_on_subscription(self):
        await self._listener.send(
            orjson.dumps(
                {
                    'id': 'logon_id',
                    'method': 'session.logon',
                    'params': get_signed_payload(
                        self._private_key,
                        {'apiKey': self._api_key, 'timestamp': int(time.time() * 1000)},
                    ),
                }
            ).decode()
        )

    async def _user_data_subscription(self):
        await self._listener.send(
            orjson.dumps(
                {'id': 'user_data_id', 'method': 'userDataStream.subscribe'}
            ).decode()
        )

    async def _msg_preprocessing(self, msg: str):
        msg: dict = orjson.loads(msg)

        if event := msg.get("event"):
            match event["e"]:
                case "executionReport":
                    await self._orders_eventer.emit(
                        order_report=OrderReport.model_validate(event)
                    )

                case "outboundAccountPosition":
                    await self._wallet_eventer.emit(
                        balances_for_asset=[
                            BalanceForAsset.model_validate(i) for i in event["B"]
                        ]
                    )

        # processing subscription msgs
        if id := msg.get("id"):
            match id:

                # processing logon subscription msgs
                case "logon_id":
                    if msg["status"] == 200:
                        await self._user_data_subscription()
                    else:
                        logger.error(
                            "Failed to send auth message." "Try again..."
                            if self._listener.is_connected
                            else "WS connection not established." f": {msg}"
                        )

                        if self._listener.is_connected:
                            await self._log_on_subscription()

                # processing user_datas' subscription msgs
                case "user_data_id":
                    if msg["status"] != 200:
                        logger.error(
                            "Failed to subscribe on UserData." "Try again..."
                            if self._listener.is_connected
                            else "WS connection not established." f": {msg}"
                        )

                        if self._listener.is_connected:
                            await self._user_data_subscription()

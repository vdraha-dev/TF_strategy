import logging
from uuid import uuid4

import orjson

from tf_strategy.common.async_event import AsyncEvent, AsyncHandler
from tf_strategy.common.connection.ws_listener import AsyncWSListener
from tf_strategy.common.enums import TimeInterval

from ..schemas import Kline, Symbol
from ._inner_ws_schemas import (
    KlineKey,
    PublicSubscriptionCreator,
    WSKeyCreator,
)

logger = logging.getLogger(__name__)


class BinancePublicWS:
    """Client for Binance public WebSocket subscriptions."""

    def __init__(self, url: str, reconnect_delay: float = 5):
        """
        Initialize the BinancePublicWS client.

        Args:
            base_url (str): Base URL for Binance WebSocket API.
        """

        self._url = url
        self._reconnect_delay = reconnect_delay

        self._is_started = False
        self._listener: AsyncWSListener | None = None

        self._subscriptions: dict[tuple, AsyncEvent] = {}
        """Dictionary of running subscriptions and its event handler.

        Key is created using WSKeyCreator.
        """

        self._handlers: dict[str, tuple] = {}
        """Dictionary for comparing the handler
        and the subscription to which it is subordinate.

        Value is created using WSKeyCreator.
        """

    async def start(self):
        if not self._is_started:
            self._is_started = True
            logger.info("Public Binance connection is starting ...")
            self._listener = AsyncWSListener(
                url=self._url,
                msg_handler=self._msg_preprocessing,
                reconnect_delay=self._reconnect_delay,
            )
            await self._listener.start()

    async def stop(self):
        if self._is_started:
            self._is_started = False
            logger.info("Public Binance connection is stopping ...")
            await self._listener.stop()
            self._listenert = None
            self._subscriptions.clear()
            self._handlers.clear()

    async def kline_subscribe(
        self,
        symbol: Symbol,
        time_interval: TimeInterval,
        handler: AsyncHandler,
    ) -> str:
        """
        Subscribe to Kline (candlestick) stream for a specific symbol and interval.

        Registers an asynchronous handler that will be invoked for each incoming
        kline update. If the WebSocket connection is not active, it will be created
        automatically.

        Args:
            symbol (Symbol):
                Trading pair to subscribe to (e.g. BTC/USDT).

            time_interval (TimeInterval):
                Candlestick interval (e.g. 1m, 5m, 1h).

            handler (AsyncHandler):
                Asynchronous callback invoked on each kline event.

                The handler must have the following signature::

                    async def handler(
                        symbol: str,
                        time_interval: str,
                        kline: Kline,
                        is_closed: bool,
                    ) -> None

                Where:
                - ``symbol`` is the upercase trading symbol (e.g. "BTCUSDT")
                - ``time_interval`` is the kline interval string
                - ``kline`` is the parsed Kline object
                - ``is_closed`` indicates whether the candle is final

        Returns:
            str:
                Unique handler token used to unsubscribe from the stream.

        Raises:
            ValueError:
                If the subscription key is invalid or unsupported.
        """

        subscr_key = WSKeyCreator.kline_key(symbol, time_interval)
        token = str(uuid4())

        await self._subscribe(subscr_key, token, handler)

        return token

    async def kline_unsubscribe(
        self,
        *,
        handler_token: str | None = None,
        symbol: Symbol | None = None,
        time_interval: TimeInterval | None = None,
    ):
        """
        Unsubscribe from Kline events.

        Can unsubscribe by:
        - handler_token
        - symbol and time_interval (unsubscribe from this channel and remove all handlers for it)
        - symbol (unsubscribe from all channels with this symbol and remove handlers for them)

        Args:
            handler_token (str | None, optional): Handler token for unsubscribing. Defaults to None.
            symbol (Symbol | None, optional): Symbol to unsubscribe from. Defaults to None.
            time_interval (TimeInterval | None, optional): Candle timeframe for unsubscribing. Defaults to None.

        Raises:
            ValueError:
                If the subscription key is invalid or unsupported.
        """
        if handler_token:
            await self._unsubscribe(handler_token=handler_token)

        elif symbol and time_interval:
            await self._unsubscribe(
                subscr_key=WSKeyCreator.kline_key(symbol, time_interval)
            )

        elif symbol:
            keys = [
                key
                for key in self._subscriptions
                if key.symbol == symbol.symbol.lower() and key.channel == "kline"
            ]
            for key in keys:
                await self._unsubscribe(subscr_key=key)

        else:
            logger.warning(
                "Invalid parameters passed. Parameters cannot be empty or contain only TimeInterval."
            )

    async def _subscribe(
        self, subscr_key: tuple, handler_token: str, handler: AsyncHandler
    ) -> bool:
        """Return true if new channel was created, false if only handler was added to existing channel."""
        is_new_channel = False

        # create a new connection if they doesnt exists
        if subscr_key not in self._subscriptions:
            await self._listener.send(self._make_subscription_msg(subscr_key))
            self._subscriptions[subscr_key] = AsyncEvent()
            is_new_channel = True

        # required to remove the handler by identifier
        self._handlers[handler_token] = subscr_key
        await self._subscriptions[subscr_key].add(handler_token, handler)

        return is_new_channel

    async def _unsubscribe(
        self, *, subscr_key: tuple | None = None, handler_token: str | None = None
    ) -> bool:
        """Return true if channel was unsubscribed, false if only handler was removed"""
        key_for_unsubscribe = subscr_key

        if handler_token:
            # check that this subscription exists
            subscr_key = self._handlers.pop(handler_token, None)
            if not subscr_key or subscr_key not in self._subscriptions:
                return

            # delete handler from the eventer
            eventer = self._subscriptions.get(subscr_key, None)
            if not eventer:
                return

            await eventer.remove(handler_token)

            if eventer.is_empty():
                key_for_unsubscribe = subscr_key

        elif subscr_key:
            self._handlers = {k: v for k, v in self._handlers if v != subscr_key}

        if key_for_unsubscribe:
            self._subscriptions.pop(key_for_unsubscribe)
            await self._listener.send(self._make_subscription_msg(subscr_key, False))
            return True
        return False

    def _make_subscription_msg(self, subscr_key: tuple, is_subscription: bool = True):
        match subscr_key, is_subscription:
            case KlineKey() as key, True:
                return PublicSubscriptionCreator.kline_subscription_msg(
                    symbol=key.symbol, time_interval=key.time_interval
                )
            case KlineKey() as key, False:
                return PublicSubscriptionCreator.kline_unsubscription_msg(
                    symbol=subscr_key.symbol, time_interval=subscr_key.time_interval
                )
            case _:
                raise ValueError(f"Unknown subscription key: {subscr_key}")

    async def _msg_preprocessing(self, msg: str):
        msg = orjson.loads(msg)

        if "e" not in msg:
            logger.debug(msg)
            return

        if msg["e"] == "kline":
            await self._kline_preprocessor(msg)

        else:
            logger.warning(msg)

    async def _kline_preprocessor(self, msg: dict):
        """
        {
            "e": "kline",         // Event type
            "E": 1672515782136,   // Event time
            "s": "BNBBTC",        // Symbol
            "k": {
                "t": 1672515780000, // Kline start time
                "T": 1672515839999, // Kline close time
                "s": "BNBBTC",      // Symbol
                "i": "1m",          // Interval
                "f": 100,           // First trade ID
                "L": 200,           // Last trade ID
                "o": "0.0010",      // Open price
                "c": "0.0020",      // Close price
                "h": "0.0025",      // High price
                "l": "0.0015",      // Low price
                "v": "1000",        // Base asset volume
                "n": 100,           // Number of trades
                "x": false,         // Is this kline closed?
                "q": "1.0000",      // Quote asset volume
                "V": "500",         // Taker buy base asset volume
                "Q": "0.500",       // Taker buy quote asset volume
                "B": "123456"       // Ignore
            }
        }
        """
        subscr_key = WSKeyCreator.kline_key(msg["s"].lower(), msg["k"]["i"])
        await self._subscriptions[subscr_key].emit(
            symbol=msg["s"],
            time_interval=msg["k"]["i"],
            kline=Kline.model_validate(msg["k"]),
            is_closed=msg["k"]["x"],
        )

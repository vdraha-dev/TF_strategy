import logging
from uuid import uuid4

from tf_strategy.common.async_event import AsyncHandler
from tf_strategy.connector.common.connection.ws_listener import AsyncWSListener
from tf_strategy.connector.common.enums import TimeInterval

from ._inner_ws_schemas import HandlerToken, KlineKey, WSKeyCreator
from ..schemas import Symbol
from .ws_paths import ws_path

logger = logging.getLogger(__name__)


class BinancePublicWS:
    """Client for Binance public WebSocket subscriptions."""
    
    def __init__(self, base_url: str):
        """
        Initialize the BinancePublicWS client.

        Args:
            base_url (str): Base URL for Binance WebSocket API.
        """

        self._base_url = base_url
        self._subscriptions: dict[KlineKey, AsyncWSListener] = {}
        self._handlers: dict[str, HandlerToken] = {}

    async def kline_subscribe(
        self,
        symbol: Symbol,
        time_interval: TimeInterval,
        handler: AsyncHandler,
    ) -> str:
        """
        Subscribe to Kline (candlestick) events for a given symbol and time interval.

        Creates a new WebSocket connection if it does not exist,
        and adds an async handler to process incoming messages.

        Args:
            symbol (Symbol): Symbol to subscribe.
            time_interval (TimeInterval): Candle timeframe (e.g., 1m, 5m).
            handler (AsyncHandler): Asynchronous function/coroutine to handle messages.

        Returns:
            str: Unique handler token, used for unsubscribing.
        """
        subscr_key = WSKeyCreator.kline_key(symbol, time_interval)
        token = str(uuid4())

        # create a new connection if they doesnt exists
        if subscr_key not in self._subscriptions:
            ws_listener = AsyncWSListener(
                f"{self._base_url}{ws_path.public.klines(symbol=symbol.symbol, time_interval=time_interval)}"
            )
            ws_listener.start()
            self._subscriptions[subscr_key] = ws_listener

        # add handler to connection
        listener = self._subscriptions[subscr_key]
        await listener.add_handler(token, handler)

        # required to remove the handler by identifier
        self._handlers[token] = HandlerToken(subscr_key, handler)

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
        - symbol and time_interval (remove all handlers)
        - symbol (unsubscribe from all timeframes)

        Args:
            handler_token (str | None, optional): Handler token for unsubscribing. Defaults to None.
            symbol (Symbol | None, optional): Symbol to unsubscribe from. Defaults to None.
            time_interval (TimeInterval | None, optional): Candle timeframe for unsubscribing. Defaults to None.
        """
        if handler_token:
            # if all parameters are passed or only the handler identifier,
            # this block will be executed

            info = self._handlers.pop(handler_token, None)
            if not info:
                return

            subscr_key = info.subscription_key
            subscription = self._subscriptions.get(subscr_key)
            if not subscription:
                return

            await subscription.remove_handler(handler_token)

            if subscription.is_empty():
                await subscription.stop()
                self._subscriptions.pop(subscr_key)
                logger.info(
                    f"Listener for channel {ws_path.public.klines(subscr_key.symbol, subscr_key.time_interval)} closed."
                )
            else:
                logger.info(
                    f"Handler for channel {ws_path.public.klines(subscr_key.symbol, subscr_key.time_interval)} removed."
                )

        elif symbol and time_interval:
            await self._kline_unsubscribe_all_for_key(symbol, time_interval)

        elif symbol:
            keys = [
                key
                for key in self._subscriptions
                if key.symbol == symbol.symbol and key.channel == "kline"
            ]
            for key in keys:
                await self._kline_unsubscribe_all_for_key(symbol, key.time_interval)

        else:
            logger.warning(
                "Invalid parameters passed. Parameters cannot be empty or contain only TimeInterval."
            )

    async def _kline_unsubscribe_all_for_key(
        self, symbol: Symbol, time_interval: TimeInterval
    ):
        """
        Internal method to fully unsubscribe from Kline events by key.

        Closes the WebSocket connection and removes all associated handlers.

        Args:
            symbol (Symbol): Symbol to unsubscribe.
            time_interval (TimeInterval): Candle timeframe to unsubscribe.
        """
        subscr_key = WSKeyCreator.kline_key(symbol, time_interval)

        subscription = self._subscriptions.pop(subscr_key, None)
        if subscription:
            await subscription.stop()

        self._handlers = {
            k: v for k, v in self._handlers.items() if v.subscription_key != subscr_key
        }

        logger.info(
            f"Listener for kline channel {ws_path.public.klines(subscr_key.symbol, subscr_key.time_interval)} closed."
        )

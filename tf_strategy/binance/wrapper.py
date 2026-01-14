from datetime import datetime

from tf_strategy.common.async_event import AsyncHandler
from tf_strategy.common.base import ConnectorBase
from tf_strategy.common.enums import Status, TimeInterval
from tf_strategy.common.schemas import (
    BalanceForAsset,
    CancelOrder,
    ConnectorConfig,
    Kline,
    Order,
    OrderOCO,
    OrderReport,
    Symbol,
    Wallet,
)

from .rest.private_rest import BinancePrivateREST
from .rest.public_rest import BinancePublicREST
from .ws.private_ws import BinancePrivateWS
from .ws.public_ws import BinancePublicWS


class BinanceWrapper(ConnectorBase):
    def __init__(self, config: ConnectorConfig, reconnect_delay: float = 5):
        """
        Initialize Binance exchange wrapper.

        This wrapper provides a unified high-level interface over Binance
        REST and WebSocket APIs, managing public/private connections,
        authentication, and local cached state such as wallet balances
        and open orders.

        Args:
            config (ConnectorConfig):
                Configuration object containing REST/WS URLs and API credentials.
            reconnect_delay (float):
                Delay in seconds before attempting to reconnect WebSocket
                connections after a disconnect.
        """

        # rest connection
        self._public_rest = BinancePublicREST(url=config.public_rest_url)
        self._private_rest = BinancePrivateREST(
            url=config.private_rest_url,
            api_key=config.api_key,
            private_key=config.private_key,
        )

        # ws connection
        self._public_ws = BinancePublicWS(
            url=config.public_ws_url, reconnect_delay=reconnect_delay
        )
        self._private_ws = BinancePrivateWS(
            url=config.private_ws_url,
            api_key=config.api_key,
            private_key=config.private_key,
            reconnect_delay=reconnect_delay,
        )

        self._wallet: Wallet = Wallet(balance={})
        self._open_orders: dict[str, OrderReport] = {}

        self._is_started: bool = False

    async def start(self):
        if not self._is_started:
            self._is_started = True

            await self._public_ws.start()
            await self._private_ws.start()

            await self._private_ws.wallet_subscribe(self._update_wallet)
            await self._private_ws.orders_subscribe(self._update_order_reports)

            await self._refresh_wallet()
            await self._refresh_open_orders()

    async def stop(self):
        if self._is_started:
            self._is_started = False

            await self._public_ws.stop()
            await self._private_ws.stop()

            self._wallet = Wallet(balance={})
            self._open_orders = {}

    ###################
    ### Public REST ###
    ###################
    async def get_historical_candles(
        self,
        symbol: Symbol,
        interval: TimeInterval,
        *,
        limit: int | None = None,
        start_ts: datetime | int | None = None,
        end_ts: datetime | int | None = None,
        timezone: str | None = None,
    ) -> list[Kline]:
        """
        Fetch historical kline/candlestick bars for a symbol.

        Klines are uniquely identified by their open time.

        If `start_ts` and `end_ts` are not provided, the most recent klines are returned.

        The `timezone` parameter affects how kline intervals are interpreted,
        but does NOT affect `start_ts` and `end_ts`, which are always interpreted in UTC.

        Supported values for `timezone`:
            - Hours and minutes (e.g. "-1:00", "05:45")
            - Only hours (e.g. "0", "8", "-4")
            - Accepted range is strictly from "-12:00" to "+14:00" (inclusive)

        Args:
            symbol (Symbol): Trading symbol (e.g. BTC/USDT).
            interval (TimeInterval): Kline interval (e.g. 1m, 5m, 1h).
            limit (int, optional): Number of klines to return. Defaults to None.
            start_ts (datetime, optional): Start time in UTC. Defaults to None.
            end_ts (datetime, optional): End time in UTC. Defaults to None.
            timezone (str, optional): Timezone used to interpret kline intervals. Defaults to UTC.

        Raises:
            Exception: Raised when an unexpected error occurs.

        Returns:
            list: List of klines, where each kline is represented as:
                [
                    1499040000000, "0.01634790", "0.80000000",
                    "0.01575800", "0.01577100", "148976.11427815",
                    1499644799999, "2434.19055334", 308,
                    "1756.87402397", "28.46694368", "0"
                ]
        """
        return await self._public_rest.get_historical_candles(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_ts=start_ts,
            end_ts=end_ts,
            timezone=timezone,
        )

    ####################
    ### Private REST ###
    ####################
    async def send_order(self, order: Order) -> OrderReport | None:
        """
        Send a trading order to the exchange.

        This method signs and sends an order request to the private REST API.
        If the request is successful, the response is validated and converted
        into an `OrderReport` model. In case of an HTTP error, the error is
        logged and `None` is returned.

        Args:
            order (Order):
                The order object containing all required order parameters.

        Returns:
            (OrderReport | None):
                The validated order report if the request succeeds,
                otherwise `None` if an error occurs.
        """
        response = await self._private_rest.send_order(order)
        return response

    async def send_oco_order(
        self, order: OrderOCO
    ) -> tuple[OrderReport, OrderReport] | None:
        """
        Send an OCO (One-Cancels-Other) order to the exchange.

        This method signs and sends an OCO order request to the private REST API.
        If the request is successful, the response is validated and converted
        into a tuple of `OrderReport` models. In case of an HTTP error, the error is
        logged and `None` is returned.

        Args:
            order (OrderOCO):
                The OCO order object containing all required order parameters.

        Returns:
            (tuple[OrderReport, OrderReport] | None):
                A tuple of validated order reports if the request succeeds,
                otherwise `None` if an error occurs.
        """
        response = await self._private_rest.send_oco_order(order)
        return response

    async def cancel_order(self, order: CancelOrder) -> OrderReport:
        """
        Cancel an existing order on the exchange.

        This method signs and sends an order request to the private REST API.
        If the request is successful, the response is validated and converted
        into an `OrderReport` model. In case of an HTTP error, the error is
        logged and `None` is returned.

        Args:
            order (CancelOrder):
                The order object containing all required order parameters.

        Returns:
            (OrderReport | None):
                The validated order report if the request succeeds,
                otherwise `None` if an error occurs.
        """
        response = await self._private_rest.cancel_order(order)
        return response

    async def wallet(self, refresh: bool = False) -> Wallet:
        """
        Retrieve the current wallet state for the account.

        This method fetches account information from the exchange and converts
        the balances data into a `Wallet` object, where each asset is mapped
        to a `BalanceForAsset` instance containing free and locked amounts.
        If `refresh` is set to True, the open orders are first fetched
        from the exchange via the private REST API and the local cache is updated.

        Args:
            refresh (bool):
                Whether to refresh open orders from the exchange before
                returning the result.

        Returns:
            Wallet: A wallet object containing balances for all non-zero assets.
        """
        if refresh:
            await self._refresh_wallet()
        return self._wallet

    async def open_orders(
        self, symbol: Symbol | None = None, refresh: bool = False
    ) -> dict[str, OrderReport]:
        """
        Retrieve open orders for the account.

        This method returns a cached view of open orders. If `refresh` is set
        to True, the open orders are first fetched from the exchange via the
        private REST API and the local cache is updated.

        Args:
            symbol (Symbol | None):
                Optional trading symbol to filter open orders.
                If None, all open orders are returned.
            refresh (bool):
                Whether to refresh open orders from the exchange before
                returning the result.

        Returns:
            dict[str, OrderReport]:
                A dictionary mapping order IDs to order reports.
        """
        if refresh:
            await self._refresh_open_orders()

        if not symbol:
            return self._open_orders

        return {k: v for k, v in self._open_orders.items() if v.symbol == symbol.symbol}

    async def _refresh_wallet(self):
        """
        Refresh the cached wallet state from the exchange.

        This internal method fetches the latest wallet balances from the
        private REST API and updates the local wallet cache if the request
        succeeds.
        """
        wallet = await self._private_rest.wallet()
        if wallet:
            self._wallet = wallet

    async def _refresh_open_orders(self):
        """
        Refresh the cached open orders from the exchange.

        This internal method fetches all currently open orders from the
        private REST API and updates the local open orders cache if the
        request succeeds.
        """
        open_orders = await self._private_rest.get_open_orders()
        if open_orders:
            self._open_orders = {order.order_id: order for order in open_orders}

    #################
    ### Public WS ###
    #################
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
        return await self._public_ws.kline_subscribe(
            symbol=symbol, time_interval=time_interval, handler=handler
        )

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
        return await self._public_ws.kline_unsubscribe(
            handler_token=handler_token, symbol=symbol, time_interval=time_interval
        )

    ##################
    ### Private WS ###
    ##################

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
        await self._private_ws.wallet_subscribe(handler)

    async def wallet_unsubscribe(self, handler_token: str):
        """
        Unsubscribe from Wallet events.


        Args:
            handler_token (str): Handler token for unsubscribing.

        """
        await self._private_ws.wallet_unsubscribe(handler_token)

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
        await self._private_ws.orders_subscribe(handler)

    async def orders_unsubscribe(self, handler_token: str):
        """
        Unsubscribe from Wallet events.


        Args:
            handler_token (str): Handler token for unsubscribing.
        """
        await self._private_ws.orders_unsubscribe(handler_token)

    async def _update_wallet(self, balances_for_asset: list[BalanceForAsset]):
        for b in balances_for_asset:
            self._wallet.balance[b.asset] = b

    async def _update_order_reports(self, order_report: OrderReport):
        if order_report.status in [Status.Canceled, Status.Rejected, Status.Expired]:
            self._open_orders.pop(order_report.order_id)

        else:
            self._open_orders[order_report.order_id] = order_report

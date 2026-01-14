from abc import ABC, abstractmethod
from datetime import datetime

from tf_strategy.common.async_event import AsyncHandler
from tf_strategy.common.enums import TimeInterval
from tf_strategy.common.schemas import (
    CancelOrder,
    Kline,
    Order,
    OrderOCO,
    OrderReport,
    Symbol,
    Wallet,
)


class ConnectorBase(ABC):
    """
    Interface for Binance exchange connector.

    Defines the contract for interacting with Binance exchange
    through REST and WebSocket APIs.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start the connector and establish connections."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the connector and close all connections."""
        ...

    @abstractmethod
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

        Args:
            symbol (Symbol): Trading symbol (e.g. BTC/USDT).
            interval (TimeInterval): Kline interval (e.g. 1m, 5m, 1h).
            limit (int, optional): Number of klines to return. Defaults to None.
            start_ts (datetime, optional): Start time in UTC. Defaults to None.
            end_ts (datetime, optional): End time in UTC. Defaults to None.
            timezone (str, optional): Timezone used to interpret kline intervals. Defaults to UTC.

        Returns:
            list[Kline]: List of klines.
        """
        ...

    @abstractmethod
    async def send_order(self, order: Order) -> OrderReport | None:
        """
        Send a trading order to the exchange.

        Args:
            order (Order): The order object containing all required order parameters.

        Returns:
            OrderReport | None: The validated order report if the request succeeds,
                otherwise None if an error occurs.
        """
        ...

    @abstractmethod
    async def send_oco_order(
        self, order: OrderOCO
    ) -> tuple[OrderReport, OrderReport] | None:
        """
        Send an OCO (One-Cancels-Other) order to the exchange.

        Args:
            order (OrderOCO): The OCO order object containing all required order parameters.

        Returns:
            tuple[OrderReport, OrderReport] | None: A tuple of validated order reports if the request succeeds,
                otherwise None if an error occurs.
        """
        ...

    @abstractmethod
    async def cancel_order(self, order: CancelOrder) -> OrderReport:
        """
        Cancel an existing order on the exchange.

        Args:
            order (CancelOrder): The order object containing all required order parameters.

        Returns:
            OrderReport: The validated order report if the request succeeds,
                otherwise None if an error occurs.
        """
        ...

    @abstractmethod
    async def wallet(self, refresh: bool = False) -> Wallet:
        """
        Retrieve the current wallet state for the account.

        Args:
            refresh (bool): Whether to refresh wallet from the exchange before
                returning the result.

        Returns:
            Wallet: A wallet object containing balances for all non-zero assets.
        """
        ...

    @abstractmethod
    async def open_orders(
        self, symbol: Symbol | None = None, refresh: bool = False
    ) -> dict[str, OrderReport]:
        """
        Retrieve open orders for the account.

        Args:
            symbol (Symbol | None): Optional trading symbol to filter open orders.
                If None, all open orders are returned.
            refresh (bool): Whether to refresh open orders from the exchange before
                returning the result.

        Returns:
            dict[str, OrderReport]: A dictionary mapping order IDs to order reports.
        """
        ...

    @abstractmethod
    async def kline_subscribe(
        self,
        symbol: Symbol,
        time_interval: TimeInterval,
        handler: AsyncHandler,
    ) -> str:
        """
        Subscribe to Kline (candlestick) stream for a specific symbol and interval.

        Args:
            symbol (Symbol): Trading pair to subscribe to (e.g. BTC/USDT).
            time_interval (TimeInterval): Candlestick interval (e.g. 1m, 5m, 1h).
            handler (AsyncHandler): Asynchronous callback invoked on each kline event.

        Returns:
            str: Unique handler token used to unsubscribe from the stream.
        """
        ...

    @abstractmethod
    async def kline_unsubscribe(
        self,
        *,
        handler_token: str | None = None,
        symbol: Symbol | None = None,
        time_interval: TimeInterval | None = None,
    ) -> None:
        """
        Unsubscribe from Kline events.

        Args:
            handler_token (str | None, optional): Handler token for unsubscribing. Defaults to None.
            symbol (Symbol | None, optional): Symbol to unsubscribe from. Defaults to None.
            time_interval (TimeInterval | None, optional): Candle timeframe for unsubscribing. Defaults to None.
        """
        ...

    @abstractmethod
    async def wallet_subscribe(self, handler: AsyncHandler) -> str:
        """
        Subscribe to Wallet updates.

        Args:
            handler (AsyncHandler): Asynchronous callback invoked on each wallet event.

        Returns:
            str: Unique handler token used to unsubscribe from the stream.
        """
        ...

    @abstractmethod
    async def wallet_unsubscribe(self, handler_token: str) -> None:
        """
        Unsubscribe from Wallet events.

        Args:
            handler_token (str): Handler token for unsubscribing.
        """
        ...

    @abstractmethod
    async def orders_subscribe(self, handler: AsyncHandler) -> str:
        """
        Subscribe to Orders updates.

        Args:
            handler (AsyncHandler): Asynchronous callback invoked on each order event.

        Returns:
            str: Unique handler token used to unsubscribe from the stream.
        """
        ...

    @abstractmethod
    async def orders_unsubscribe(self, handler_token: str) -> None:
        """
        Unsubscribe from Orders events.

        Args:
            handler_token (str): Handler token for unsubscribing.
        """
        ...

import logging
from decimal import Decimal, ROUND_DOWN
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from tf_strategy.binance.wrapper import BinanceWrapper
from tf_strategy.common.base import ConnectorBase
from tf_strategy.common.enums import Status, TimeInterval, Type
from tf_strategy.common.schemas import (
    CancelOrder,
    Kline,
    Order,
    OrderOCO,
    OrderReport,
    Symbol,
)
from tf_strategy.strategy.base import BaseStrategy, TradeSignal

logger = logging.getLogger(__name__)


class TradeConfig(BaseModel):
    """Configuration for trading a specific symbol.

    Attributes:
        symbol: The trading pair (e.g., BTCUSDT).
        max_open_positions: Maximum number of concurrent positions allowed.
        quantity: Quantity to trade per position.
        stop_loss: Stop loss percentage as a decimal (e.g., 0.02 for 2%).
        take_profit: Take profit percentage as a decimal (e.g., 0.05 for 5%).
    """

    symbol: Symbol
    max_open_positions: int
    quantity: Decimal
    stop_loss: Decimal
    take_profit: Decimal


class OpenPosition(BaseModel):
    """Represents an open trading position with associated orders.

    Attributes:
        open_position: The initial order that opened the position.
        take_profit: The take profit order associated with this position.
        stop_loss: The stop loss order associated with this position.
    """

    open_position: OrderReport
    take_profit: OrderReport
    stop_loss: OrderReport


class StrategyWorkerData(BaseModel):
    """Container for strategy worker state and configuration.

    Attributes:
        strategy: The strategy instance being executed.
        config: Trading configuration for this strategy worker.
        connector: Binance API wrapper for order execution and data fetching.
        open_positions: List of currently open positions.
        extra: Dictionary for storing additional worker-specific data (e.g., subscriptions).
    """

    strategy: BaseStrategy
    config: TradeConfig
    connector: BinanceWrapper
    open_positions: list[OpenPosition] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class Trader:
    """Manages multiple trading strategy workers and their positions.

    The Trader class coordinates the execution of multiple trading strategies,
    handling position management, order execution, and strategy updates.
    """

    def __init__(self):
        """Initialize the Trader with an empty workers dictionary."""
        self._workers: dict[str, StrategyWorkerData] = {}

    async def create_strategy_worker(
        self,
        strategy: BaseStrategy,
        config: TradeConfig,
        connector: ConnectorBase,
        timeframe: TimeInterval,
    ) -> str:
        """Create and register a new strategy worker.

        This method initializes a strategy worker by:
        1. Fetching historical candle data
        2. Initializing the strategy with historical data
        3. Setting up a WebSocket subscription for real-time candle updates

        Args:
            strategy: The strategy instance to execute.
            config: Trading configuration including symbol and risk parameters.
            connector: Binance API wrapper for data and order operations.
            timeframe: The timeframe for candle analysis and trading signals.

        Returns:
            Subscription token serving as the unique identifier for this worker.
        """

        # load last historical data
        data = await connector.get_historical_candles(
            symbol=config.symbol, interval=timeframe
        )
        df = pd.DataFrame(
            {
                "open": [i.open_price for i in data],
                "close": [i.close_price for i in data],
                "high": [i.high_price for i in data],
                "low": [i.low_price for i in data],
                "volume": [i.volume for i in data],
            },
            index=[pd.to_datetime(i.close_time, unit='ms') for i in data],
        )

        # initialize strategy with historical data
        strategy.update_batch(df)

        worker_data = StrategyWorkerData(
            strategy=strategy, config=config, connector=connector
        )

        async def process_position(**kwargs):
            """Process incoming candle data and execute trading signals.

            This callback function is triggered on each closed candle matching
            the configured timeframe and symbol. It:
            1. Updates the strategy with new candle data
            2. Generates trading signals
            3. Executes position opening orders when signals are generated

            Args:
                **kwargs: Event data containing 'kline', 'is_closed', 'time_interval', and 'symbol'.
            """

            if kline := kwargs.get("kline") and kwargs.get("is_closed"):
                kline: Kline
                # add new candle to dataframe
                df.loc[pd.to_datetime(kline.close_time, unit='ms')] = [
                    kline.open_price,
                    kline.close_price,
                    kline.high_price,
                    kline.low_price,
                    kline.volume,
                ]
                # update strategy with new candle
                strategy.update_incremental(df)

                # check for trading signal
                if strategy.get_last_signal() == TradeSignal.OpenPosition:
                    if (
                        len(worker_data.open_positions)
                        >= worker_data.config.max_open_positions
                    ):
                        # do nothing if max open positions reached
                        return

                    order_report = await worker_data.connector.send_order(
                        Order(
                            symbol=worker_data.config.symbol,
                            type=Type.Market,
                            side="BUY",
                            quantity=worker_data.config.quantity,  # example fixed quantity
                        )
                    )

                    if order_report and order_report.status == Status.Filled:
                        oco_report = await worker_data.connector.send_oco_order(
                            OrderOCO(
                                symbol=worker_data.config.symbol,
                                side="SELL",
                                quantity=order_report.executed_qty,
                                above_type=Type.TakeProfit,
                                # TODO: need add quantize to connector information about symbol price precision
                                above_price=(
                                    order_report.price
                                    * (1 + worker_data.config.take_profit)
                                ).quantize(Decimal("0.000000"), rounding=ROUND_DOWN),
                                below_type=Type.StopLoss,
                                below_price=(
                                    order_report.price
                                    * (1 - worker_data.config.stop_loss)
                                ).quantize(Decimal("0.000000"), rounding=ROUND_DOWN),
                            )
                        )

                        if oco_report:
                            # save open position with associated orders
                            worker_data.open_positions.append(
                                OpenPosition(
                                    open_position=order_report,
                                    take_profit=(
                                        oco_report[0]
                                        if oco_report[0].type == Type.TakeProfit
                                        else oco_report[1]
                                    ),
                                    stop_loss=(
                                        oco_report[0]
                                        if oco_report[0].type == Type.StopLoss
                                        else oco_report[1]
                                    ),
                                )
                            )
                        else:
                            # immediate close position if oco order failed
                            cancel_report = await worker_data.connector.cancel_order(
                                CancelOrder(
                                    symbol=worker_data.config.symbol,
                                    order_id=order_report.order_id,
                                )
                            )

                            if (
                                cancel_report
                                and cancel_report.status == Status.Canceled
                            ):
                                logger.info(
                                    "Position closed due to OCO order failure",
                                    extra={
                                        "connector": "TODO: add `name` for connector"
                                    },
                                )
                            else:
                                logger.error(
                                    "Failed to close position after OCO order failure",
                                    extra={
                                        "connector": "TODO: add `name` for connector"
                                    },
                                )
                    else:
                        # TODO: add `name` for connector
                        logger.error(
                            "Failed to open position: Order not filled",
                            extra={"connector": "TODO: add `name` for connector"},
                        )
                        pass

            elif order_report := kwargs.get("order_report"):
                order_report: OrderReport

                if (
                    order_report.type in [Type.TakeProfit, Type.StopLoss]
                    and order_report.status == Status.Filled
                ):
                    cl = [
                        i
                        for i in worker_data.open_positions
                        if i.take_profit.order_id == order_report.order_id
                        or i.stop_loss.order_id == order_report.order_id
                    ]
                    worker_data.open_positions.remove(cl[0])

                    # if connector is not support oco orders
                    # need close opposite order manually
                    # or emulate oco order in connector         <-- prefer this option

        # make subscription on kline updates
        candle_subscribe = await worker_data.connector.kline_subscribe(
            symbol=config.symbol, time_interval=timeframe, callback=process_position
        )
        worker_data.extra["kline_subscribe"] = candle_subscribe

        # save the subscription token and will it use as strategy worker token
        self._workers[candle_subscribe] = worker_data

        # make other subscriptions if needed
        order_update = await worker_data.connector.orders_subscribe(
            handler=process_position
        )
        worker_data.extra["open_orders"] = order_update

        return candle_subscribe

    async def close_strategy_worker(self, worker_token: str) -> None:
        """Close and remove a strategy worker by its token.

        This method unsubscribes from all WebSocket subscriptions associated
        with the strategy worker and removes it from the internal registry.

        Args:
            worker_token: The unique identifier for the strategy worker to close.
        """
        if worker_token not in self._workers:
            return

        worker_data = self._workers[worker_token]

        # unsubscribe from kline updates
        if "kline_subscribe" in worker_data.extra:
            await worker_data.connector.kline_unsubscribe(
                handler_token=worker_data.extra["kline_subscribe"]
            )

        # unsubscribe from order updates
        if "open_orders" in worker_data.extra:
            await worker_data.connector.orders_unsubscribe(
                handler_token=worker_data.extra["open_orders"]
            )

        # remove the worker from registry
        self._workers.pop(worker_token)

from decimal import Decimal
from typing import ClassVar

from pydantic import AliasChoices, Field, model_validator

from tf_strategy.common.enums import TimeInForce
from tf_strategy.common.schemas import BalanceForAsset
from tf_strategy.common.schemas import (
    Kline as CommonKline,
)
from tf_strategy.common.schemas import (
    Order as CommonOrder,
)
from tf_strategy.common.schemas import (
    OrderReport as CommonOrderReport,
)
from tf_strategy.common.schemas import (
    PartialyFill as CommonPartialyFill,
)
from tf_strategy.common.schemas import (
    Symbol as CommonSymbol,
)
from tf_strategy.common.schemas import (
    Wallet as CommonWallet,
)


class Symbol(CommonSymbol):
    """Binance Symbol"""

    _fmt = "{}{}"


class Kline(CommonKline):
    """Binance Kline"""

    open_time: int = Field(alias="t")
    open_price: Decimal = Field(alias="o")
    high_price: Decimal = Field(alias="h")
    low_price: Decimal = Field(alias="l")
    close_price: Decimal = Field(alias="c")
    volume: Decimal = Field(alias="v")
    close_time: int = Field(alias="T")
    quote_asset_volume: Decimal = Field(alias="q")
    number_of_trades: int = Field(alias="n")
    taker_buy_base_volume: Decimal = Field(alias="V")
    taker_buy_quote_volume: Decimal = Field(alias="Q")

    _kline_fields: ClassVar[tuple[str, ...]] = (
        "t",  # open time
        "o",  # open
        "h",  # high
        "l",  # low
        "c",  # close
        "v",  # volume
        "T",  # close time
        "q",  # quote asset volume
        "n",  # number of trades
        "V",  # taker buy base
        "Q",  # taker buy quote
    )

    @classmethod
    def from_list(cls, raw: list) -> Kline:
        data = dict(zip(cls._kline_fields, raw, strict=True))
        return cls.model_validate(data)


class Wallet(CommonWallet):
    balance: dict[str, BalanceForAsset]

    @model_validator(mode="before")
    @classmethod
    def build_balance_map(cls, data):
        """
        Convert Binance balances list into a dict keyed by asset symbol.
        """
        if isinstance(data["balance"], list):
            data["balance"] = {item["asset"]: item for item in data["balance"]}
        return data


class Order(CommonOrder):
    """Binance Order"""

    @classmethod
    def create_order_payload(cls, self: CommonOrder) -> dict:
        payload = {
            "symbol": self.symbol.symbol,
            "side": self.side.value,
            "type": self.type.value,
        }

        if self.time_in_force:
            payload["timeInForce"] = self.time_in_force.value

        if self.quantity:
            payload["quantity"] = str(self.quantity)

        if self.quote_order_qty:
            payload["quoteOrderQty"] = str(self.quote_order_qty)

        if self.price:
            payload["price"] = str(self.price)

        if self.new_client_order_id:
            payload["newClientOrderId"] = self.new_client_order_id

        if self.stop_price:
            payload["stopPrice"] = self.stop_price

        return payload


class PartialyFill(CommonPartialyFill):
    """Binance PartialyFill"""

    commission_asset: str | None = Field(default=None, alias="commisionAsset")
    trade_id: int | None = Field(default=None, alias="tradeId")


class OrderReport(CommonOrderReport):
    """Binance OrderReport"""

    order_id: int = Field(alias="orderId")
    client_order_id: str = Field(alias="clientOrderId")
    transaction_time: int = Field(validation_alias=AliasChoices("transactTime", "time"))

    #
    orig_qty: Decimal | None = Field(default=None, alias="origQty")
    executed_qty: Decimal | None = Field(default=None, alias="executedQty")
    orig_quote_order_qty: Decimal | None = Field(
        default=None, alias="origQuoteOrderQty"
    )
    cummulative_quote_qty: Decimal | None = Field(
        default=None, alias="cummulativeQuoteQty"
    )
    time_in_force: TimeInForce | None = Field(default=None, alias="timeInForce")

    fills: list[PartialyFill] | None = Field(default=None, alias="fills")

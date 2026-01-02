from decimal import Decimal

from pydantic import Field

from tf_strategy.common.enums import TimeInForce
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


class Symbol(CommonSymbol):
    """Binance Symbol"""

    _fmt = "{}{}"


class Kline(CommonKline):
    """Binance Kline"""

    @classmethod
    def from_list(cls, raw: list) -> Kline:
        return cls(
            open_time=raw[0],
            open_price=Decimal(raw[1]),
            high_price=Decimal(raw[2]),
            low_price=Decimal(raw[3]),
            close_price=Decimal(raw[4]),
            volume=Decimal(raw[5]),
            close_time=raw[6],
            quote_asset_volume=Decimal(raw[7]),
            number_of_trades=int(raw[8]),
            taker_buy_base_volume=Decimal(raw[9]),
            taker_buy_quote_volume=Decimal(raw[10]),
        )

    @classmethod
    def from_dict(cls, raw: dict) -> Kline:
        return cls(
            open_time=raw["t"],
            open_price=Decimal(raw["o"]),
            high_price=Decimal(raw["h"]),
            low_price=Decimal(raw["l"]),
            close_price=Decimal(raw["c"]),
            volume=Decimal(raw["v"]),
            close_time=raw["T"],
            quote_asset_volume=Decimal(raw["q"]),
            number_of_trades=int(raw["n"]),
            taker_buy_base_volume=Decimal(raw["V"]),
            taker_buy_quote_volume=Decimal(raw["Q"]),
        )


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
    transaction_time: int = Field(alias="transactTime")

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

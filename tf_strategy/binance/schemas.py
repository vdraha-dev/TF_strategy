from decimal import Decimal

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

    def create_order_payload(self) -> str:
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


class OrderReport(CommonOrderReport):
    """Binance OrderReport"""

    @classmethod
    def from_dict(cls, raw: dict) -> OrderReport: ...

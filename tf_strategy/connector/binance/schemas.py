from decimal import Decimal

from tf_strategy.connector.common.schemas import Kline as CommonKline
from tf_strategy.connector.common.schemas import Symbol as CommonSymbol


class Symbol(CommonSymbol):
    _fmt = "{}{}"


class Kline(CommonKline):
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

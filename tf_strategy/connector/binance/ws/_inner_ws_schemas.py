from collections import namedtuple
from dataclasses import dataclass

from tf_strategy.common.async_event import AsyncHandler
from tf_strategy.connector.common.enums import TimeInterval

from ..schemas import Symbol

KlineKey = namedtuple(
    "KlineKey", ["symbol", "time_interval", "channel"], defaults=["kline"]
)


@dataclass(frozen=True)
class HandlerToken:
    subscription_key: KlineKey
    handler: AsyncHandler


class WSKeyCreator:
    """Class for creating uniquely interpreted keys for each WS subscription"""

    @classmethod
    def kline_key(cls, symbol: Symbol, time_interval: TimeInterval) -> KlineKey:
        return KlineKey(symbol=symbol.symbol, time_interval=time_interval)

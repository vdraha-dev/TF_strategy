from collections import namedtuple
from collections.abc import Iterable
from itertools import count

import orjson

from tf_strategy.common.enums import TimeInterval

from ..schemas import Symbol

KlineKey = namedtuple(
    "KlineKey", ["symbol", "time_interval", "channel"], defaults=["kline"]
)


class WSKeyCreator:
    """Class for creating uniquely interpreted keys for each WS subscription"""

    @classmethod
    def kline_key(
        cls, symbol: Symbol | str, time_interval: TimeInterval | str
    ) -> KlineKey:
        if not isinstance(symbol, str):
            symbol = symbol.symbol

        if not isinstance(time_interval, str):
            time_interval = time_interval.value

        return KlineKey(symbol=symbol.lower(), time_interval=time_interval)


class PublicSubscriptionCreator:
    """"""

    _id = count(1)
    _subscribe_core = {"method": "SUBSCRIBE"}
    _unsubscribe_core = {"method": "UNSUBSCRIBE"}

    @classmethod
    def _new_core(cls, core: dict, params: Iterable[str]):
        return {
            **core,
            "id": next(cls._id),
            "params": list(params),
        }

    @classmethod
    def _format_symbol(cls, symbol: Symbol | str):
        if isinstance(symbol, str):
            return symbol.lower()
        return symbol.symbol.lower()

    @classmethod
    def kline_subscription_msg(
        cls, symbol: Symbol | str, time_interval: TimeInterval | str
    ):
        return orjson.dumps(
            cls._new_core(
                cls._subscribe_core,
                (f"{cls._format_symbol(symbol)}@kline_{time_interval}",),
            )
        ).decode()

    @classmethod
    def kline_unsubscription_msg(
        cls, symbol: Symbol | str, time_interval: TimeInterval | str
    ):
        return orjson.dumps(
            cls._new_core(
                cls._unsubscribe_core,
                (f"{cls._format_symbol(symbol)}@kline_{time_interval}",),
            )
        ).decode()

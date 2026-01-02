from enum import StrEnum


class TimeInterval(StrEnum):
    _1s = "1s"
    _1m = "1m"
    _3m = "3m"
    _5m = "5m"
    _15m = "15m"
    _30m = "30m"
    _1h = "1h"
    _2h = "2h"
    _4h = "4h"
    _6h = "6h"
    _8h = "8h"
    _12h = "12h"
    _1d = "1d"
    _2d = "3d"
    _1M = "1M"


class Side(StrEnum):
    Buy = "BUY"
    Sell = "SELL"


class Type(StrEnum):
    Limit = "LIMIT"
    Market = "MARKET"
    StopLoss = "STOP_LOSS"
    StopLossLimit = "STOP_LOSS_LIMIT"
    TakeProfit = "TAKE_PROFIT"
    TakeProfitLimit = "TAKE_PROFIT_LIMIT"
    LimitMaker = "LIMIT_MAKER"

    @property
    def requires_price(self) -> bool:
        return self in {
            Type.Limit,
            Type.StopLossLimit,
            Type.TakeProfitLimit,
            Type.LimitMaker,
        }


class TimeInForce(StrEnum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class Status(StrEnum):
    New = "NEW"
    PendingNew = "PENDING_NEW"
    PartiallyFilled = "PARTIALLY_FILLED"
    Filled = "FILLED"
    Canceled = "CANCELED"
    PendingCancel = "PENDING_CANCEL"
    Rejected = "REJECTED"
    EXPIRED = "EXPIRED"

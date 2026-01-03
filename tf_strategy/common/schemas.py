from decimal import Decimal
from typing import get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    computed_field,
    field_validator,
    model_validator,
)

from .enums import Side, Status, TimeInForce, Type


class Symbol(BaseModel):
    first: str
    second: str

    _fmt = PrivateAttr(default="{}/{}")

    @computed_field
    @property
    def symbol(self) -> str:
        """Create a symbol from parts."""
        return self._fmt.format(self.first, self.second)

    @computed_field
    @property
    def r_symbol(self) -> str:
        """Create a reverse symbol from parts."""
        return self._fmt.format(self.second, self.first)

    def set_format(self, fmt: str):
        """Sets formatting for a symbol.

        fmt must be in the format:
        "{}{}", "{}/{}", "{}-{}" ...
        """
        if fmt.count("{}") != 2:
            raise ValueError("Format must contain exactly two '{}' placeholders")

        self._fmt = fmt

    @field_validator("first", "second", mode="before")
    @classmethod
    def to_upper(cls, v: str) -> str:
        """Normalize symbol parts to uppercase."""
        return v.upper()


class Kline(BaseModel):
    open_time: int  # POSIX timestamp in ms
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    close_time: int  # POSIX timestamp in ms
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_volume: Decimal  # Taker buy base asset volume
    taker_buy_quote_volume: Decimal  # Taker buy quote asset volume

    model_config = ConfigDict(validate_by_name=True)


class BalanceForAsset(BaseModel):
    asset: str
    free: Decimal
    locked: Decimal


class Wallet(BaseModel):
    balance: dict[str, BalanceForAsset]


class Order(BaseModel):
    symbol: Symbol
    side: Side
    type: Type
    time_in_force: TimeInForce | None = None
    quantity: Decimal | None = None
    quote_order_qty: Decimal | None = None
    price: Decimal | None = None
    new_client_order_id: str | None = None
    stop_price: Decimal | None = None

    @model_validator(mode="after")
    def check_decimals_value(cls, values: Order):
        for field_name, field_info in Order.model_fields.items():
            if isinstance(field_info.annotation, Decimal) or Decimal in get_args(
                field_info.annotation
            ):
                value = getattr(values, field_name)

                if value is not None and value < Decimal("0"):
                    raise ValueError(f"Field '{field_name}' must be greater than zero")

        return values

    @model_validator(mode="after")
    def check_quantity(cls, values: Order):
        q = values.quantity
        qq = values.quote_order_qty

        # neither provided
        if not q and not qq:
            raise ValueError("Either quantity or quote_order_qty must be set")

        # both provided
        if q and qq:
            raise ValueError("Quantity and quote_order_qty cannot be used together")

        return values

    @model_validator(mode="after")
    def check_price(cls, values: Order):
        if values.type.requires_price and values.price is None:
            raise ValueError("A non-market order must contain a price")

        return values

    @model_validator(mode="after")
    def check_time_in_force(cls, values: Order):
        if values.type != Type.Market and not values.time_in_force:
            raise ValueError("A non-market order must contain time_in_force")

        if values.type == Type.Market and values.time_in_force:
            raise ValueError("In a market order field time_in_force must be None")

        return values


class PartialyFill(BaseModel):
    price: Decimal
    qty: Decimal
    commission: Decimal = Field(default_factory=Decimal)
    commission_asset: str | None = None

    model_config = ConfigDict(validate_by_name=True)


class OrderReport(BaseModel):
    symbol: str
    order_id: str
    client_order_id: str
    transaction_time: int

    #
    price: Decimal | None = None
    orig_qty: Decimal | None = None
    executed_qty: Decimal | None = None
    orig_quote_order_qty: Decimal | None = None
    cummulative_quote_qty: Decimal | None = None
    status: Status | None = None
    time_in_force: TimeInForce | None = None
    type: Type | None = None
    side: Side | None = None

    #
    fills: list[PartialyFill] | None = None

    model_config = ConfigDict(validate_by_name=True)


class CancelOrder(BaseModel):
    symbol: Symbol
    order_id: str | None = None
    client_order_id: str | None = None

    # need if Exchange allow create custom
    # id for cancel order
    new_client_order_id: str | None = None

    @model_validator(mode="before")
    def order_id_check(cls, data: dict):
        if data["order_id"] is None and data["client_order_id"] is None:
            raise ValueError("Either orderI_id or client_order_id must be set")

        return data

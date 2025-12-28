from pydantic import BaseModel, PrivateAttr, computed_field, field_validator
from decimal import Decimal
from datetime import datetime

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
    open_time: int                  # POSIX timestamp in ms
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    close_time: int                 # POSIX timestamp in ms
    quote_asset_volume: Decimal
    number_of_trades: int
    taker_buy_base_volume: Decimal  # Taker buy base asset volume
    taker_buy_quote_volume: Decimal # Taker buy quote asset volume
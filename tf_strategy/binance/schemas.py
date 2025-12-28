from pydantic import BaseModel, PrivateAttr, computed_field, field_validator


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

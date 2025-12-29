from pydantic import BaseModel, Field, model_validator

__all__ = ["ws_path"]


class PublicSubPath(BaseModel):
    version: str

    def klines(self, symbol: str, time_interval: str) -> str:
        return f"/{symbol.lower()}@kline_{time_interval}"


class PrivateSubPath(BaseModel):
    version: str


class Path(BaseModel):
    """Class for creating a correct subpath for WS subscription."""

    version: str = Field(default="v3")
    public: PublicSubPath | None = None
    private: PrivateSubPath | None = None

    @model_validator(mode="after")
    def build_subpaths(self):
        self.public = PublicSubPath(version=self.version)
        self.private = PrivateSubPath(version=self.version)
        return self


ws_path = Path()
"""Assistant for creating the correct subpath for WS subscription."""

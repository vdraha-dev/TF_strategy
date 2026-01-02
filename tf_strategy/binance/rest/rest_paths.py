from pydantic import BaseModel, Field, computed_field, model_validator

__all__ = ["rest_path"]


class PublicSubPath(BaseModel):
    version: str

    @computed_field
    @property
    def klines(self) -> str:
        return f"/api/{self.version}/klines"


class PrivateSubPath(BaseModel):
    version: str

    @computed_field
    @property
    def account(self) -> str:
        return f"/api/{self.version}/account"

    @computed_field
    @property
    def order(self) -> str:
        return f"/api/{self.version}/order"

    @computed_field
    @property
    def open_orders(self) -> str:
        return f"/api/{self.version}/openOrders"


class Path(BaseModel):
    version: str = Field(default="v3")
    public: PublicSubPath | None = None
    private: PrivateSubPath | None = None

    @model_validator(mode="after")
    def build_subpaths(self):
        self.public = PublicSubPath(version=self.version)
        self.private = PrivateSubPath(version=self.version)
        return self


rest_path = Path()

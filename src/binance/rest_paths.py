from pydantic import BaseModel, computed_field, Field, model_validator

__all__ = ["rest_path"]

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


class PublicSubPath(BaseModel):
    version: str
    
    @computed_field
    @property
    def klines(self) -> str:
        return f"/api/{self.version}/klines"
    

class PrivateSubPath(BaseModel):
    version: str

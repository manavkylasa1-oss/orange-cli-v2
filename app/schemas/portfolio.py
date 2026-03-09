from pydantic import BaseModel, Field


class PortfolioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    description: str | None = Field(default=None, max_length=500)

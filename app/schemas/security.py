from pydantic import BaseModel, Field


class SecurityQuote(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    date: str
    price: float = Field(..., gt=0)
    issuer: str

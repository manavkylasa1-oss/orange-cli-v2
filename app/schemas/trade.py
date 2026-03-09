from pydantic import BaseModel, Field


class TradeRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    portfolio_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

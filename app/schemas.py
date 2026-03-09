from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    password: str
    firstname: str
    lastname: str
    balance: float


class UpdateBalanceRequest(BaseModel):
    username: str
    new_balance: float


class CreatePortfolioRequest(BaseModel):
    name: str
    description: str


class BuyTradeRequest(BaseModel):
    ticker: str
    portfolio_id: int
    quantity: int


class SellTradeRequest(BaseModel):
    ticker: str
    portfolio_id: int
    quantity: int


class AccessGrantRequest(BaseModel):
    user_id: str
    role: str

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=30)
    password: str = Field(..., min_length=1, max_length=128)
    firstname: str = Field(..., min_length=1, max_length=30)
    lastname: str = Field(..., min_length=1, max_length=30)
    balance: float = Field(..., ge=0)


class UserBalanceUpdate(BaseModel):
    username: str = Field(..., min_length=1, max_length=30)
    new_balance: float = Field(..., ge=0)

from pydantic import BaseModel, Field


class PortfolioAccessRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30)
    role: str = Field(..., pattern=r'^(viewer|manager)$')

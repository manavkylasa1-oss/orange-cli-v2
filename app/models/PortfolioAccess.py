from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db

if TYPE_CHECKING:
    from app.models import Portfolio, User


class PortfolioAccess(db.Model):
    __tablename__ = 'portfolio_access'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'), nullable=False)
    username: Mapped[str] = mapped_column(String(30), ForeignKey('user.username'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'viewer' or 'manager'

    portfolio: Mapped['Portfolio'] = relationship(
        'Portfolio',
        foreign_keys='[PortfolioAccess.portfolio_id]',
        back_populates='access_grants',
    )
    user: Mapped['User'] = relationship(
        'User',
        foreign_keys='[PortfolioAccess.username]',
        back_populates='portfolio_accesses',
    )

    if TYPE_CHECKING:
        def __init__(self, *, portfolio_id: int, username: str, role: str) -> None: ...

    def __to_dict__(self):
        return {
            'portfolio_id': self.portfolio_id,
            'username': self.username,
            'role': self.role,
        }

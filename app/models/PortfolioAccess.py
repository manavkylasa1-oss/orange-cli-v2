from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import db


class PortfolioAccess(db.Model):
    __tablename__ = 'portfolio_access'
    __table_args__ = (UniqueConstraint('portfolio_id', 'user_id', name='uq_portfolio_user_access'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey('portfolio.id'), nullable=False)
    user_id: Mapped[str] = mapped_column(String(30), ForeignKey('user.username'), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

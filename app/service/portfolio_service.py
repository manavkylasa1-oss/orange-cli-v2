from typing import List

from app.db import db
from app.models import Portfolio, User


class UnsupportedPortfolioOperationError(Exception):
    pass


def create_portfolio(name: str, description: str, user: User) -> int:
    if not name or not description or not user:
        raise UnsupportedPortfolioOperationError('Invalid input for portfolio creation')
    portfolio = Portfolio(name=name, description=description, user=user)
    db.session.add(portfolio)
    db.session.flush()
    return portfolio.id


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    return db.session.query(Portfolio).filter_by(owner=user.username).all()


def get_all_portfolios() -> List[Portfolio]:
    return db.session.query(Portfolio).all()


def get_portfolio_by_id(portfolio_id: int) -> Portfolio | None:
    return db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()


def delete_portfolio(portfolio_id: int):
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist')
    db.session.delete(portfolio)
    db.session.flush()

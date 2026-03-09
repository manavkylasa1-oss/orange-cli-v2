from typing import List

from app.db import db
from app.models import Portfolio, User


class UnsupportedPortfolioOperationError(Exception):
    pass


class PortfolioOperationError(Exception):
    pass


def create_portfolio(name: str, description: str, user: User) -> int:
    if not name or not description or not user:
        raise UnsupportedPortfolioOperationError(
            f'Invalid input[name:{name}, description: {description}, user: {user}]. Please try again.'
        )
    portfolio = Portfolio(name=name, description=description, user=user)
    try:
        db.session.add(portfolio)
        db.session.flush()
        return portfolio.id
    except Exception as e:
        raise PortfolioOperationError(f'Failed to create portfolio due to error: {str(e)}')


def get_portfolios_by_user(user: User) -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).filter_by(owner=user.username).all()
        return portfolios
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_all_portfolios() -> List[Portfolio]:
    try:
        portfolios = db.session.query(Portfolio).all()
        return portfolios
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolios due to error: {str(e)}')


def get_portfolio_by_id(portfolio_id: int, execution_username: str = None) -> Portfolio | None:
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        if portfolio and execution_username:
            from app.services import authorization_service
            if not authorization_service.can_view_portfolio(portfolio_id, execution_username):
                raise UnsupportedPortfolioOperationError(f'User {execution_username} is not authorized to view portfolio {portfolio_id}')
        return portfolio
    except UnsupportedPortfolioOperationError as e:
        raise e
    except Exception as e:
        raise PortfolioOperationError(f'Failed to retrieve portfolio due to error: {str(e)}')


def delete_portfolio(portfolio_id: int, execution_username: str = None):
    try:
        portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
        if not portfolio:
            raise UnsupportedPortfolioOperationError(f'Portfolio with id {portfolio_id} does not exist')
        
        if execution_username:
            from app.services import authorization_service
            if not authorization_service.is_owner(portfolio_id, execution_username):
                raise UnsupportedPortfolioOperationError(f'User {execution_username} is not authorized to delete portfolio {portfolio_id}')
                
        db.session.delete(portfolio)
        db.session.flush()
    except UnsupportedPortfolioOperationError as e:
        raise e
    except Exception as e:
        raise e

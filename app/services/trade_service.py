import datetime

from app.db import db
from app.models import Investment, Portfolio, Security, Transaction
from app.services import alpha_vantage_client, authorization_service
from app.services.authorization_service import AuthorizationException


class TradeExecutionException(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


def _ensure_security_exists(ticker: str, issuer: str, price: float) -> Security:
    """
    Ensures a Security record exists in the database for referential integrity.
    If it doesn't exist, it creates a placeholder based on Alpha Vantage data.
    """
    security = db.session.query(Security).filter_by(ticker=ticker).one_or_none()
    if not security:
        security = Security(ticker=ticker, issuer=issuer, price=price)
        db.session.add(security)
    else:
        # Update the price to the latest known price from Alpha Vantage
        security.price = price
        security.issuer = issuer
    db.session.flush()
    return security


def execute_purchase_order(portfolio_id: int, ticker: str, quantity: int, execution_username: str):
    """
    Execute a purchase order for a given portfolio, security ticker, and quantity.
    """
    if not authorization_service.can_trade_portfolio(portfolio_id, execution_username):
        raise TradeExecutionException(
            f"User {execution_username} is not authorized to trade in portfolio {portfolio_id}"
        )
        
    if portfolio_id is None or not ticker or not quantity or quantity <= 0:
        raise TradeExecutionException(
            f'Invalid purchase order parameters [portfolio_id={portfolio_id}, ticker={ticker}, quantity={quantity}]'
        )
        
    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist.')
        
    user = portfolio.user
    if not user:
        raise TradeExecutionException(f'User associated with the portfolio ({portfolio_id}) does not exist.')

    # Get live quote from Alpha Vantage
    quote = alpha_vantage_client.get_quote(ticker=ticker)
    if not quote:
        raise TradeExecutionException(f'Could not fetch live quote for ticker {ticker} from Alpha Vantage.')
        
    # Ensure security placeholder exists for referential integrity
    security = _ensure_security_exists(ticker=quote.ticker, issuer=quote.issuer, price=quote.price)

    total_cost = quote.price * quantity
    if user.balance < total_cost:
        raise InsufficientFundsError('Insufficient funds to complete the purchase.')

    existing_investment = next((inv for inv in portfolio.investments if inv.ticker == ticker), None)
    if existing_investment:
        existing_investment.quantity += quantity
    else:
        portfolio.investments.append(Investment(ticker=ticker, quantity=quantity))

    user.balance -= total_cost
    db.session.add(
        Transaction(
            portfolio_id=portfolio.id,
            username=user.username,
            ticker=ticker,
            quantity=quantity,
            price=quote.price,
            transaction_type='BUY',
            date_time=datetime.datetime.now(),
        )
    )
    db.session.flush()


def execute_sell_order(portfolio_id: int, ticker: str, quantity: int, execution_username: str):
    """
    Liquidate shares of a security from a portfolio using the live Alpha Vantage price.
    """
    if not authorization_service.can_trade_portfolio(portfolio_id, execution_username):
        raise TradeExecutionException(
            f"User {execution_username} is not authorized to trade in portfolio {portfolio_id}"
        )

    if portfolio_id is None or not ticker or not quantity or quantity <= 0:
        raise TradeExecutionException(
            f'Invalid sell order parameters [portfolio_id={portfolio_id}, ticker={ticker}, quantity={quantity}]'
        )

    portfolio = db.session.query(Portfolio).filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise TradeExecutionException(f'Portfolio with id {portfolio_id} does not exist')
        
    user = portfolio.user
    
    investment = next(
        (inv for inv in portfolio.investments if inv.ticker == ticker),
        None,
    )
    if not investment:
        raise TradeExecutionException(
            f'No investment with ticker {ticker} exists in portfolio with id {portfolio_id}'
        )
        
    if investment.quantity < quantity:
        raise TradeExecutionException(
            f'Cannot liquidate {quantity} shares of {ticker}. Only {investment.quantity} shares available in portfolio'
        )

    # Get live quote from Alpha Vantage
    quote = alpha_vantage_client.get_quote(ticker=ticker)
    if not quote:
        raise TradeExecutionException(f'Could not fetch live quote for ticker {ticker} from Alpha Vantage.')
        
    # Ensure security placeholder exists for referential integrity
    _ensure_security_exists(ticker=quote.ticker, issuer=quote.issuer, price=quote.price)

    total_proceeds = quote.price * quantity
    user.balance += total_proceeds
    
    if investment.quantity == quantity:
        db.session.delete(investment)
    else:
        investment.quantity -= quantity
        
    db.session.add(
        Transaction(
            portfolio_id=portfolio.id,
            username=user.username,
            ticker=ticker,
            quantity=quantity,
            price=quote.price,
            transaction_type='SELL',
            date_time=datetime.datetime.now(),
        )
    )
    db.session.flush()

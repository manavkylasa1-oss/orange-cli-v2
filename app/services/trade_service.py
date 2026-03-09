import datetime

from app.errors import APIError
from app.models import Investment, Portfolio, Security, Transaction
from app.services.alpha_vantage_client import get_quote


def execute_buy(portfolio_id: int, ticker: str, quantity: int):
    if quantity <= 0:
        raise APIError('bad_request', 'Quantity must be > 0', 400)
    portfolio = Portfolio.query.filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)

    quote = get_quote(ticker)
    if not quote:
        raise APIError('not_found', f'Invalid ticker {ticker}', 404)

    security = Security.query.filter_by(ticker=quote.ticker).one_or_none()
    if not security:
        security = Security(ticker=quote.ticker, issuer=quote.issuer, price=quote.price)
        from app.db import db

        db.session.add(security)
    else:
        security.price = quote.price
        security.issuer = quote.issuer

    user = portfolio.user
    total = quote.price * quantity
    if user.balance < total:
        raise APIError('forbidden', 'Insufficient funds', 400)

    inv = Investment.query.filter_by(portfolio_id=portfolio_id, ticker=quote.ticker).one_or_none()
    if inv:
        inv.quantity += quantity
    else:
        from app.db import db

        db.session.add(Investment(portfolio_id=portfolio_id, ticker=quote.ticker, quantity=quantity))

    user.balance -= total
    from app.db import db

    db.session.add(
        Transaction(
            username=user.username,
            portfolio_id=portfolio.id,
            ticker=quote.ticker,
            transaction_type='BUY',
            quantity=quantity,
            price=quote.price,
            date_time=datetime.datetime.utcnow(),
        )
    )


def execute_sell(portfolio_id: int, ticker: str, quantity: int):
    if quantity <= 0:
        raise APIError('bad_request', 'Quantity must be > 0', 400)
    portfolio = Portfolio.query.filter_by(id=portfolio_id).one_or_none()
    if not portfolio:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    quote = get_quote(ticker)
    if not quote:
        raise APIError('not_found', f'Invalid ticker {ticker}', 404)

    inv = Investment.query.filter_by(portfolio_id=portfolio_id, ticker=quote.ticker).one_or_none()
    if not inv or inv.quantity < quantity:
        raise APIError('forbidden', 'Insufficient holdings', 400)

    inv.quantity -= quantity
    if inv.quantity == 0:
        from app.db import db

        db.session.delete(inv)

    user = portfolio.user
    proceeds = quote.price * quantity
    user.balance += proceeds
    from app.db import db

    db.session.add(
        Transaction(
            username=user.username,
            portfolio_id=portfolio.id,
            ticker=quote.ticker,
            transaction_type='SELL',
            quantity=quantity,
            price=quote.price,
            date_time=datetime.datetime.utcnow(),
        )
    )

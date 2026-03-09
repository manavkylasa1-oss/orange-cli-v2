from typing import List

from app.db import db
from app.models import Transaction


def get_transactions_by_user(username: str) -> List[Transaction]:
    return db.session.query(Transaction).filter(Transaction.username == username).all()


def get_transactions_by_portfolio_id(portfolio_id: int) -> List[Transaction]:
    return db.session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).all()


def get_transactions_by_ticker(ticker: str) -> List[Transaction]:
    return db.session.query(Transaction).filter(Transaction.ticker == ticker).all()

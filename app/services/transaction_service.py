from typing import List

from app.db import db
from app.models import Transaction


def get_transactions_by_user(username: str) -> List[Transaction]:
    transactions = db.session.query(Transaction).filter(Transaction.username == username).all()
    return transactions


def get_transactions_by_portfolio_id(portfolio_id: int) -> List[Transaction]:
    transactions = db.session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).all()
    return transactions


def get_transactions_by_ticker(ticker: str) -> List[Transaction]:
    transactions = db.session.query(Transaction).filter(Transaction.ticker == ticker).all()
    return transactions

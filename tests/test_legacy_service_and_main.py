import app.main as main_module
import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.db import db
from app.models import Portfolio, Transaction, User


def test_main_module_loads_app():
    assert main_module.app is not None


def test_legacy_services_smoke(app):
    with app.app_context():
        u = User(username='legacy', password='p', firstname='l', lastname='g', balance=100)
        db.session.add(u)
        db.session.commit()

        assert user_service.get_user_by_username('legacy') is not None
        pid = portfolio_service.create_portfolio('L', 'legacy', u)
        db.session.commit()
        assert portfolio_service.get_portfolio_by_id(pid) is not None
        assert len(portfolio_service.get_portfolios_by_user(u)) == 1
        assert len(portfolio_service.get_all_portfolios()) >= 1

        db.session.add(
            Transaction(
                username='legacy',
                portfolio_id=pid,
                ticker='AAPL',
                transaction_type='BUY',
                quantity=1,
                price=1.0,
                date_time=__import__('datetime').datetime.utcnow(),
            )
        )
        db.session.commit()
        assert len(transaction_service.get_transactions_by_user('legacy')) == 1
        assert len(transaction_service.get_transactions_by_portfolio_id(pid)) == 1
        assert len(transaction_service.get_transactions_by_ticker('AAPL')) >= 1

        tx = Transaction.query.filter_by(portfolio_id=pid).one()
        db.session.delete(tx)
        db.session.commit()
        portfolio_service.delete_portfolio(pid)
        db.session.commit()
        assert Portfolio.query.filter_by(id=pid).one_or_none() is None

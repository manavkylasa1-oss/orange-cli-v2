import pytest
from app.models import User, Portfolio
from app.services.portfolio_service import create_portfolio
from app.services.security_service import get_all_securities, SecurityException, get_security_by_ticker
from app.services.user_service import create_user
from app.services import transaction_service

@pytest.fixture(autouse=True)
def setup(app, db_session):
    with app.app_context():
        create_user(username="user", password="secret", firstname="Firstname", lastname="Lastname", balance=1000.00)
        db_session.commit()
        user = db_session.query(User).filter_by(username="user").one()
        assert user is not None
        create_portfolio("Test Portfolio", "Test Portfolio Description", user)
        db_session.commit()
        portfolio = db_session.query(Portfolio).filter_by(name="Test Portfolio").one()
        assert portfolio is not None
        return {
            "user": user,
            "portfolio": portfolio
        }

def test_get_security_by_ticker(app, db_session):
    with app.app_context():
        security = get_security_by_ticker("AAPL")
        assert security is not None
        assert security.ticker == "AAPL"
        assert security.price == 150.00

def test_get_all_securities(app, db_session):
    with app.app_context():
        securities = get_all_securities()
        assert securities is not None
        assert len(securities) == 3
        tickers = [sec.ticker for sec in securities]
        assert "AAPL" in tickers
        assert "GOOGL" in tickers
        assert "MSFT" in tickers

def test_exception_from_get_all_securities(app, db_session, monkeypatch):
    with app.app_context():
        def mock_query_failure(*args, **kwargs):
            raise Exception("Database connection error")
        monkeypatch.setattr(db_session, 'query', mock_query_failure)
        with pytest.raises(SecurityException) as e:
            get_all_securities()
        assert "Failed to retrieve securities due to error: Database connection error" in str(e.value)
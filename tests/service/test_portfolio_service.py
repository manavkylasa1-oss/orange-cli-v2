import pytest
import app.services.portfolio_service as portfolio_service
from app.models import Investment, Portfolio, User

@pytest.fixture(autouse=True)
def setup(app, db_session):
    with app.app_context():
        user = User(username="testuser", password="testpass", firstname="Test", lastname="User", balance=1000.0)
        db_session.add(user)
        db_session.commit()
        portfolio1 = Portfolio(name="Portfolio 1", description="First portfolio", user=user)
        portfolio2 = Portfolio(name="Portfolio 2", description="Second portfolio", user=user)
        db_session.add_all([portfolio1, portfolio2])
        portfolio1.investments.append(Investment(ticker="AAPL", quantity=10))
        db_session.commit()
        yield {
            "user": user,
            "portfolio1": portfolio1,
            "portfolio2": portfolio2
        }

def test_get_portfolios_by_user_db_failure(app, db_session, monkeypatch):
    with app.app_context():
        def failing_get_session(_):
            raise Exception("Database query error")
        monkeypatch.setattr(db_session, 'query', failing_get_session)
        with pytest.raises(Exception) as e:
            portfolio_service.get_portfolios_by_user(User(username="testuser"))
        assert "Failed to retrieve portfolios due to error: Database query error" in str(e.value)

def test_get_all_portfolios(app, db_session):
    with app.app_context():
        portfolios = portfolio_service.get_all_portfolios()
        assert len(portfolios) >= 2
        names = [p.name for p in portfolios]
        assert "Portfolio 1" in names
        assert "Portfolio 2" in names

def test_get_all_portfolios_db_failure(app, db_session, monkeypatch):
    with app.app_context():
        def failing_get_session(*args, **kwargs):
            raise Exception("Database connection error")
        monkeypatch.setattr(db_session, 'query', failing_get_session)
        with pytest.raises(Exception) as e:
            portfolio_service.get_all_portfolios()
        assert "Failed to retrieve portfolios due to error: Database connection error" in str(e.value)

def test_get_portfolio_by_id(app, setup, db_session):
    with app.app_context():
        portfolio = setup["portfolio1"]
        retrieved_portfolio = portfolio_service.get_portfolio_by_id(portfolio.id)
        assert retrieved_portfolio is not None
        assert retrieved_portfolio.name == "Portfolio 1"
        assert retrieved_portfolio.description == "First portfolio"

def test_get_portfolio_by_id_db_failure(app, db_session, monkeypatch):
    with app.app_context():
        def failing_get_session(_):
            raise Exception("Database connection error")
        monkeypatch.setattr(db_session, "query", failing_get_session)
        with pytest.raises(Exception) as e:
            portfolio_service.get_portfolio_by_id(1)
        assert "Failed to retrieve portfolio due to error: Database connection error" in str(e.value)

def test_get_portfolio_by_invalid_id(app, db_session):
    with app.app_context():
        invalid_id = 9999
        assert portfolio_service.get_portfolio_by_id(invalid_id) is None

def test_create_portfolio(app, setup, db_session):
    with app.app_context():
        user = setup["user"]
        user_portfolios_before = portfolio_service.get_portfolios_by_user(user)
        assert len(user_portfolios_before) == 2
        portfolio_service.create_portfolio("Test Portfolio", "A test portfolio", user)
        user_portfolios_after = portfolio_service.get_portfolios_by_user(user)
        assert len(user_portfolios_after) == 3
        assert user_portfolios_after[-1].name == "Test Portfolio"
        assert user_portfolios_after[-1].description == "A test portfolio"

def test_create_portfolio_invalid_input(app, db_session):
    with app.app_context():
        user = User(username="testuser", password="testpass", firstname="Test", lastname="User", balance=1000.0)
        with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
            portfolio_service.create_portfolio("", "A test portfolio", user)
        with pytest.raises(portfolio_service.UnsupportedPortfolioOperationError):
            portfolio_service.create_portfolio("Test Portfolio", "", user)

def test_create_portfolio_db_failure(app, db_session, monkeypatch):
    with app.app_context():
        def failing_get_session(*args, **kwargs):
            raise Exception("Database connection error")
        monkeypatch.setattr(db_session, 'add', failing_get_session)
        with pytest.raises(Exception) as e:
            portfolio_service.create_portfolio("Fail Portfolio", "This should fail", User(username="user", password="pw", firstname="F", lastname="L"))
        assert "Failed to create portfolio due to error: Database connection error" in str(e.value)
        
def test_delete_portfolio(app, setup, db_session):
    with app.app_context():
        user = setup["user"]
        portfolio = Portfolio(name="To Be Deleted", description="This portfolio will be deleted", user=user)
        db_session.add(portfolio)
        db_session.commit()
        portfolio_service.delete_portfolio(portfolio.id)
        deleted_portfolio = db_session.query(Portfolio).filter_by(id=portfolio.id).one_or_none()
        assert deleted_portfolio is None

def test_delete_portfolio_invalid_id(app, db_session):
    with app.app_context():
        with pytest.raises(Exception):
            portfolio_service.delete_portfolio(9999)

def test_delete_portfolio_invalid_id(app, db_session):
    with app.app_context():
        with pytest.raises(Exception):
            portfolio_service.delete_portfolio(9999)
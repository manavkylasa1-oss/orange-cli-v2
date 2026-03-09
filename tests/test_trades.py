import pytest
import datetime
import functools
from flask import g
from app.models import User, Portfolio, Investment, Transaction, Security
from app.services import trade_service
from app.schemas.security import SecurityQuote
import app.auth.auth as auth_module

@pytest.fixture
def trade_setup(app, db_session):
    with app.app_context():
        user = User(username="tradetestuser", password="password", firstname="Trade", lastname="Test", balance=1000.0)
        db_session.add(user)
        db_session.commit()
        
        portfolio = Portfolio(name="Trade Portfolio", description="Portfolio for testing trades", user=user)
        db_session.add(portfolio)
        db_session.commit()
        
        # Add an initial investment for selling
        inv = Investment(ticker="AAPL", quantity=10)
        portfolio.investments.append(inv)
        db_session.commit()
        
        yield {
            "user": user,
            "portfolio": portfolio,
            "investment": inv
        }

def test_execute_purchase_order_success(app, db_session, trade_setup, monkeypatch):
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        user = trade_setup["user"]
        
        # Mock Alpha Vantage quote
        mock_quote = SecurityQuote(ticker="MSFT", issuer="Microsoft Corp", price=200.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        trade_service.execute_purchase_order(portfolio.id, "MSFT", 2, user.username)
        
        # Verify balance
        assert user.balance == 1000.0 - (200.0 * 2)
        
        # Verify investment
        msft_inv = next((inv for inv in portfolio.investments if inv.ticker == "MSFT"), None)
        assert msft_inv is not None
        assert msft_inv.quantity == 2
        
        # Verify transaction record
        tx = db_session.query(Transaction).filter_by(ticker="MSFT", transaction_type="BUY").one()
        assert tx.quantity == 2
        assert tx.price == 200.0

def test_execute_purchase_order_insufficient_funds(app, trade_setup, monkeypatch):
    # Note: trade_setup already has a user with 1000.0 balance
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        
        mock_quote = SecurityQuote(ticker="GOOGL", issuer="Alphabet Inc", price=2000.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        with pytest.raises(trade_service.InsufficientFundsError):
            trade_service.execute_purchase_order(portfolio.id, "GOOGL", 1, trade_setup["user"].username)

def test_execute_sell_order_success(app, db_session, trade_setup, monkeypatch):
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        user = trade_setup["user"]
        
        # AAPL was added in setup with quantity 10
        mock_quote = SecurityQuote(ticker="AAPL", issuer="Apple Inc", price=150.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        trade_service.execute_sell_order(portfolio.id, "AAPL", 4, user.username)
        
        # Verify balance
        assert user.balance == 1000.0 + (150.0 * 4)
        
        # Verify investment
        aapl_inv = next((inv for inv in portfolio.investments if inv.ticker == "AAPL"), None)
        assert aapl_inv.quantity == 6
        
        # Verify transaction record
        tx = db_session.query(Transaction).filter_by(ticker="AAPL", transaction_type="SELL").one()
        assert tx.quantity == 4
        assert tx.price == 150.0

def test_execute_sell_order_full_liquidation(app, db_session, trade_setup, monkeypatch):
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        
        mock_quote = SecurityQuote(ticker="AAPL", issuer="Apple Inc", price=150.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        trade_service.execute_sell_order(portfolio.id, "AAPL", 10, trade_setup["user"].username)
        
        # Verify investment is gone by querying the DB
        aapl_inv = db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker="AAPL").one_or_none()
        assert aapl_inv is None

def test_execute_sell_order_no_holdings(app, trade_setup, monkeypatch):
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        
        mock_quote = SecurityQuote(ticker="MSFT", issuer="Microsoft Corp", price=200.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        with pytest.raises(trade_service.TradeExecutionException) as e:
            trade_service.execute_sell_order(portfolio.id, "MSFT", 1, trade_setup["user"].username)
        assert "No investment with ticker MSFT exists" in str(e.value)

@pytest.fixture
def mock_auth(monkeypatch):
    # Mock the internal calls of the decorator since it's already applied
    monkeypatch.setattr(auth_module, "get_token_auth_header", lambda: "dummy_token")
    
    def mock_decode(*args, **kwargs):
        return {"username": g.get("current_user", "tradetestuser")}
    
    import jwt
    monkeypatch.setattr(jwt, "decode", mock_decode)
    
    # We also need to mock PyJWKClient to avoid network calls
    class MockJWKClient:
        def __init__(self, *args, **kwargs): pass
        def get_signing_key_from_jwt(self, *args, **kwargs):
            class MockKey:
                key = "dummy_key"
            return MockKey()
            
    monkeypatch.setattr(auth_module, "PyJWKClient", MockJWKClient)

def test_execute_purchase_order_unauthorized(app, trade_setup, monkeypatch):
    with app.app_context():
        portfolio = trade_setup["portfolio"]
        # 'unauthorized_user' is not authorized
        mock_quote = SecurityQuote(ticker="MSFT", issuer="Microsoft Corp", price=200.0, date="2026-03-08")
        monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
        
        with pytest.raises(trade_service.TradeExecutionException) as e:
            trade_service.execute_purchase_order(portfolio.id, "MSFT", 1, "unauthorized_user")
        assert "is not authorized to trade" in str(e.value)

# --- Route Tests ---

def test_route_buy_success(app, db_session, trade_setup, monkeypatch, mock_auth):
    client = app.test_client()
    portfolio = trade_setup["portfolio"]
    user = trade_setup["user"]
    
    # Mock Alpha Vantage
    mock_quote = SecurityQuote(ticker="MSFT", issuer="Microsoft Corp", price=100.0, date="2026-03-08")
    monkeypatch.setattr("app.services.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
    
    # Ensure g.current_user is set to the owner
    with app.test_request_context():
        g.current_user = user.username
        response = client.post('/trades/buy', json={
            "portfolio_id": portfolio.id,
            "ticker": "MSFT",
            "quantity": 5
        })
    
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Purchase order executed successfully'
    
    # Verify DB commit
    with app.app_context():
        inv = db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker="MSFT").one()
        assert inv.quantity == 5

def test_route_buy_insufficient_funds(app, trade_setup, monkeypatch, mock_auth):
    client = app.test_client()
    portfolio = trade_setup["portfolio"]
    user = trade_setup["user"]
    
    # Mock Alpha Vantage expensive stock
    mock_quote = SecurityQuote(ticker="BRK.A", issuer="Berkshire", price=500000.0, date="2026-03-08")
    monkeypatch.setattr("app.service.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
    
    with app.test_request_context():
        g.current_user = user.username
        response = client.post('/trades/buy', json={
            "portfolio_id": portfolio.id,
            "ticker": "BRK.A",
            "quantity": 1
        })
    
    assert response.status_code == 400
    assert response.get_json()['error'] == 'InsufficientFundsError'

def test_route_sell_success(app, db_session, trade_setup, monkeypatch, mock_auth):
    client = app.test_client()
    portfolio = trade_setup["portfolio"]
    user = trade_setup["user"]
    
    # AAPL has quantity 10 from setup
    mock_quote = SecurityQuote(ticker="AAPL", issuer="Apple Inc", price=150.0, date="2026-03-08")
    monkeypatch.setattr("app.service.alpha_vantage_client.get_quote", lambda ticker: mock_quote)
    
    with app.test_request_context():
        g.current_user = user.username
        response = client.post('/trades/sell', json={
            "portfolio_id": portfolio.id,
            "ticker": "AAPL",
            "quantity": 4
        })
    
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Investment liquidated successfully'
    
    # Verify DB commit
    with app.app_context():
        inv = db_session.query(Investment).filter_by(portfolio_id=portfolio.id, ticker="AAPL").one()
        assert inv.quantity == 6

def test_route_buy_validation_error(app, mock_auth):
    client = app.test_client()
    # Missing quantity
    with app.test_request_context():
        g.current_user = "test_user"
        response = client.post('/trades/buy', json={
            "portfolio_id": 1,
            "ticker": "MSFT"
        })
    
    assert response.status_code == 422
    assert response.get_json()['error'] == 'Validation Error'


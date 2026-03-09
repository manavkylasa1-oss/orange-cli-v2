import pytest
from app.schemas.trade import TradeRequest
from pydantic import ValidationError

def test_trade_request_validation():
    # Valid request
    req = TradeRequest(portfolio_id=1, ticker="AAPL", quantity=10)
    assert req.portfolio_id == 1
    assert req.ticker == "AAPL"
    assert req.quantity == 10

    # Missing field
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id=1, ticker="AAPL")

    # Invalid type
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id="abc", ticker="AAPL", quantity=10)

    # Invalid quantity
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id=1, ticker="AAPL", quantity=0)
    
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id=1, ticker="AAPL", quantity=-5)

def test_trade_request_ticker_validation():
    # Ticker too short
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id=1, ticker="", quantity=10)
    
    # Ticker too long
    with pytest.raises(ValidationError):
        TradeRequest(portfolio_id=1, ticker="VERYLONGTICKER", quantity=10)

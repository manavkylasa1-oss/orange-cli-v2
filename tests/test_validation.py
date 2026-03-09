from app.schemas import BuyTradeRequest
from tests.conftest import auth_header


def test_pydantic_accepts_valid_input():
    req = BuyTradeRequest.model_validate({'ticker': 'AAPL', 'portfolio_id': 1, 'quantity': 2})
    assert req.ticker == 'AAPL'


def test_pydantic_validation_error_returns_422(client):
    res = client.post('/trades/buy', json={'portfolio_id': 'x'}, headers=auth_header())
    assert res.status_code == 422
    body = res.get_json()
    assert body['error'] == 'validation_error'

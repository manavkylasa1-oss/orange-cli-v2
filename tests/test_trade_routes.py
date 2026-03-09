from app.models import Investment, Transaction


def _quote(*args, **kwargs):
    return type('Q', (), {'ticker': 'AAPL', 'issuer': 'Apple', 'price': 50.0, 'date': '2026-01-01'})()


def test_buy_creates_transaction_and_investment(client, app, monkeypatch):
    monkeypatch.setattr('app.services.trade_service.get_quote', _quote)
    res = client.post('/trades/buy', json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 2}, headers={'Authorization': 'Bearer valid-owner'})
    assert res.status_code == 201
    with app.app_context():
        assert Investment.query.filter_by(portfolio_id=1, ticker='AAPL').one().quantity == 2
        assert Transaction.query.filter_by(portfolio_id=1, transaction_type='BUY').count() == 1


def test_sell_insufficient_holdings(client, monkeypatch):
    monkeypatch.setattr('app.services.trade_service.get_quote', _quote)
    res = client.post('/trades/sell', json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1}, headers={'Authorization': 'Bearer valid-owner'})
    assert res.status_code == 400

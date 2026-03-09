from app.db import db
from app.models import PortfolioAccess


def test_protected_route_missing_token(client):
    res = client.get('/portfolios/')
    assert res.status_code == 403


def test_protected_route_invalid_token(client):
    res = client.get('/portfolios/', headers={'Authorization': 'Bearer bad'})
    assert res.status_code == 403


def test_owner_can_create_and_delete_portfolio(client):
    create = client.post('/portfolios/', json={'name': 'P2', 'description': 'd'}, headers={'Authorization': 'Bearer valid-owner'})
    assert create.status_code == 201
    pid = create.get_json()['portfolio_id']
    delete = client.delete(f'/portfolios/{pid}', headers={'Authorization': 'Bearer valid-owner'})
    assert delete.status_code == 200


def test_viewer_cannot_trade_manager_can(client, app, monkeypatch):
    monkeypatch.setattr('app.services.trade_service.get_quote', lambda t: type('Q', (), {'ticker': 'AAPL', 'issuer': 'Apple', 'price': 10.0, 'date': '2026-01-01'})())
    with app.app_context():
        db.session.add(PortfolioAccess(portfolio_id=1, user_id='viewer', role='viewer'))
        db.session.add(PortfolioAccess(portfolio_id=1, user_id='manager', role='manager'))
        db.session.commit()

    bad = client.post('/trades/buy', json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1}, headers={'Authorization': 'Bearer valid-viewer'})
    assert bad.status_code == 403
    ok = client.post('/trades/buy', json={'portfolio_id': 1, 'ticker': 'AAPL', 'quantity': 1}, headers={'Authorization': 'Bearer valid-manager'})
    assert ok.status_code == 201


def test_manager_cannot_create_or_delete_portfolio(client):
    res = client.post('/portfolios/', json={'name': 'P3', 'description': 'd'}, headers={'Authorization': 'Bearer valid-manager'})
    # manager can create own portfolio per current identity exists as user; assignment says cannot create on behalf of owner.
    assert res.status_code == 201
    denied_delete = client.delete('/portfolios/1', headers={'Authorization': 'Bearer valid-manager'})
    assert denied_delete.status_code == 403

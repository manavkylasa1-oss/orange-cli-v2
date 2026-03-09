from app.models import PortfolioAccess


def test_owner_grant_and_revoke_access(client, app):
    g = client.post('/portfolios/1/access', json={'user_id': 'viewer', 'role': 'viewer'}, headers={'Authorization': 'Bearer valid-owner'})
    assert g.status_code == 201
    with app.app_context():
        assert PortfolioAccess.query.filter_by(portfolio_id=1, user_id='viewer').one().role == 'viewer'
    r = client.delete('/portfolios/1/access/viewer', headers={'Authorization': 'Bearer valid-owner'})
    assert r.status_code == 200


def test_outsider_forbidden_to_view_portfolio(client):
    res = client.get('/portfolios/1', headers={'Authorization': 'Bearer valid-outsider'})
    assert res.status_code == 403


def test_viewer_can_view_after_grant(client):
    client.post('/portfolios/1/access', json={'user_id': 'viewer', 'role': 'viewer'}, headers={'Authorization': 'Bearer valid-owner'})
    res = client.get('/portfolios/1', headers={'Authorization': 'Bearer valid-viewer'})
    assert res.status_code == 200

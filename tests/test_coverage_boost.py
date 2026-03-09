import pytest
from flask import g
from app.auth import auth as auth_module

@pytest.fixture
def mock_auth(monkeypatch):
    """Mocks authentication for route tests."""
    monkeypatch.setattr(auth_module, "get_token_auth_header", lambda: "dummy_token")
    
    def mock_decode(*args, **kwargs):
        return {"username": g.get("current_user", "test_user"), "sub": "123"}
    
    import jwt
    monkeypatch.setattr(jwt, "decode", mock_decode)
    
    class MockJWKClient:
        def __init__(self, *args, **kwargs): pass
        def get_signing_key_from_jwt(self, *args, **kwargs):
            class MockKey:
                key = "dummy_key"
            return MockKey()
            
    monkeypatch.setattr(auth_module, "PyJWKClient", MockJWKClient)
    yield

def test_get_portfolios_authenticated(client, mock_auth, db_session, app):
    with app.test_request_context():
        g.current_user = "test_user"
        response = client.get('/portfolios/')
        if response.status_code != 200:
            print(f"DEBUG: {response.get_json()}")
        assert response.status_code == 200

def test_get_users_authenticated(client, mock_auth, app):
    with app.test_request_context():
        g.current_user = "test_user"
        response = client.get('/users/')
        if response.status_code != 200:
            print(f"DEBUG: {response.get_json()}")
        assert response.status_code == 200

def test_get_securities_authenticated(client, mock_auth, app):
    with app.test_request_context():
        g.current_user = "test_user"
        response = client.get('/securities/')
        if response.status_code != 200:
            print(f"DEBUG: {response.get_json()}")
        assert response.status_code == 200

def test_create_portfolio_validation_error(client, mock_auth, app):
    with app.test_request_context():
        g.current_user = "test_user"
        # Missing 'name'
        response = client.post('/portfolios/', json={"description": "test"})
        assert response.status_code == 422
        assert response.get_json()['error'] == 'Validation Error'

def test_update_balance_validation_error(client, mock_auth, app):
    with app.test_request_context():
        g.current_user = "test_user"
        # Invalid balance (negative)
        response = client.put('/users/update-balance', json={"username": "test_user", "new_balance": -100})
        assert response.status_code == 422
        assert response.get_json()['error'] == 'Validation Error'

import base64
import importlib
import json
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.auth import auth


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def _build_token(private_key, kid='k1'):
    header = {'alg': 'RS256', 'kid': kid, 'typ': 'JWT'}
    payload = {
        'sub': 'owner',
        'iss': 'https://issuer.example.com',
        'aud': 'test-client',
        'exp': int(time.time()) + 3600,
    }
    hb = _b64(json.dumps(header).encode())
    pb = _b64(json.dumps(payload).encode())
    signing_input = f'{hb}.{pb}'.encode()
    sig = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f'{hb}.{pb}.{_b64(sig)}'


def _jwk_from_public_key(public_key):
    numbers = public_key.public_numbers()
    n = _b64(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, 'big'))
    e = _b64(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, 'big'))
    return {'kty': 'RSA', 'kid': 'k1', 'n': n, 'e': e}


def test_auth_validate_token_path(app, monkeypatch):
    importlib.reload(auth)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks = {'keys': [_jwk_from_public_key(private_key.public_key())]}
    token = _build_token(private_key)

    monkeypatch.setattr(auth, '_get_jwks', lambda: jwks)
    with app.app_context():
        claims = auth.validate_token(token)
        assert claims['sub'] == 'owner'


def test_user_routes_and_security_route(client, monkeypatch):
    list_res = client.get('/users/', headers={'Authorization': 'Bearer valid-owner'})
    assert list_res.status_code == 200

    create_res = client.post(
        '/users/',
        json={'username': 'u1', 'password': 'p', 'firstname': 'f', 'lastname': 'l', 'balance': 1},
        headers={'Authorization': 'Bearer valid-owner'},
    )
    assert create_res.status_code == 201

    bal_res = client.put(
        '/users/update-balance',
        json={'username': 'u1', 'new_balance': 3},
        headers={'Authorization': 'Bearer valid-owner'},
    )
    assert bal_res.status_code == 200

    monkeypatch.setattr(
        'app.routes.security_routes.get_quote',
        lambda _t: type('Q', (), {'ticker': 'AAPL', 'issuer': 'Apple', 'price': 3.0, 'date': '2026-01-01'})(),
    )
    sec_res = client.get('/securities/AAPL', headers={'Authorization': 'Bearer valid-owner'})
    assert sec_res.status_code == 200

    del_res = client.delete('/users/u1', headers={'Authorization': 'Bearer valid-owner'})
    assert del_res.status_code == 200

import base64
import json
from functools import wraps
from urllib.request import urlopen

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from flask import current_app, g, jsonify, request

_jwks_cache = None


class AuthError(Exception):
    pass


def _b64url_decode(data: str) -> bytes:
    pad = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    with urlopen(current_app.config['COGNITO_JWKS_URL'], timeout=10) as resp:
        _jwks_cache = json.loads(resp.read().decode('utf-8'))
    return _jwks_cache


def _public_key_from_jwk(jwk: dict):
    n = int.from_bytes(_b64url_decode(jwk['n']), 'big')
    e = int.from_bytes(_b64url_decode(jwk['e']), 'big')
    return rsa.RSAPublicNumbers(e, n).public_key()


def validate_token(token: str) -> dict:
    try:
        header_b64, payload_b64, sig_b64 = token.split('.')
    except ValueError as exc:
        raise AuthError('Malformed token') from exc

    header = json.loads(_b64url_decode(header_b64))
    payload = json.loads(_b64url_decode(payload_b64))
    signature = _b64url_decode(sig_b64)

    if header.get('alg') != 'RS256':
        raise AuthError('Unsupported signing algorithm')

    jwks = _get_jwks()
    key = next((k for k in jwks.get('keys', []) if k.get('kid') == header.get('kid')), None)
    if key is None:
        raise AuthError('Unknown key id')

    signed = f'{header_b64}.{payload_b64}'.encode('utf-8')
    public_key = _public_key_from_jwk(key)
    try:
        public_key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())
    except Exception as exc:
        raise AuthError('Invalid signature') from exc

    issuer = current_app.config['COGNITO_ISSUER']
    audience = current_app.config['COGNITO_CLIENT_ID']

    if payload.get('iss') != issuer:
        raise AuthError('Invalid issuer')

    aud = payload.get('aud')
    if isinstance(aud, list):
        valid_aud = audience in aud
    else:
        valid_aud = aud == audience
    if not valid_aud:
        raise AuthError('Invalid audience')

    import time

    if int(payload.get('exp', 0)) <= int(time.time()):
        raise AuthError('Token expired')

    return payload


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'forbidden', 'detail': 'Missing bearer token'}), 403
        token = auth_header.replace('Bearer ', '', 1).strip()
        try:
            claims = validate_token(token)
        except Exception:
            return jsonify({'error': 'forbidden', 'detail': 'Invalid or expired token'}), 403

        g.current_user = claims.get('sub') or claims.get('username')
        return fn(*args, **kwargs)

    return wrapper

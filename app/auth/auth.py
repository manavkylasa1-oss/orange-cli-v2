import functools
import requests
from flask import current_app, g, jsonify, request
import jwt
from jwt import PyJWKClient

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"error": "Authorization header is missing",
                         "detail": "Authorization header is expected"}, 403)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"error": "Invalid header",
                         "detail": "Authorization header must start with Bearer"}, 403)
    elif len(parts) == 1:
        raise AuthError({"error": "Invalid header",
                         "detail": "Token not found"}, 403)
    elif len(parts) > 2:
        raise AuthError({"error": "Invalid header",
                         "detail": "Authorization header must be Bearer token"}, 403)

    token = parts[1]
    return token

def require_auth(f):
    """Determines if the Access Token is valid"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = get_token_auth_header()
            
            region = current_app.config['COGNITO_REGION']
            user_pool_id = current_app.config['COGNITO_USER_POOL_ID']
            app_client_id = current_app.config['COGNITO_APP_CLIENT_ID']
            
            jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
            issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
            
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=app_client_id,
                issuer=issuer
            )
            
            g.current_user = payload.get("username") or payload.get("cognito:username") or payload.get("sub")
            if not g.current_user:
                raise AuthError({"error": "Invalid token", "detail": "User identity missing in token"}, 403)
                
        except jwt.ExpiredSignatureError:
            raise AuthError({"error": "Token expired", "detail": "Token has expired"}, 403)
        except jwt.InvalidIssuerError:
            raise AuthError({"error": "Invalid issuer", "detail": "Token issuer is invalid"}, 403)
        except jwt.InvalidAudienceError:
            raise AuthError({"error": "Invalid audience", "detail": "Token audience is invalid"}, 403)
        except AuthError as e:
            raise e
        except Exception as e:
            raise AuthError({"error": "Invalid token", "detail": str(e)}, 403)

        return f(*args, **kwargs)

    return decorated

from flask import Flask, jsonify
from pydantic import ValidationError

from app.cache import cache
from app.db import db
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp
from app.services.trade_service import InsufficientFundsError, TradeExecutionException
from app.services.user_service import UnsupportedUserOperationError
from app.services.portfolio_service import UnsupportedPortfolioOperationError
from app.services.security_service import SecurityException
from app.auth.auth import AuthError
from app.services.authorization_service import AuthorizationException


def create_app(config):
    try:
        app = Flask(__name__)
        app.config.from_object(config)

        # register extensions
        db.init_app(app)
        cache.init_app(app)

        # register blueprints
        app.register_blueprint(user_bp, url_prefix='/users')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
        app.register_blueprint(security_bp, url_prefix='/securities')
        app.register_blueprint(trade_bp, url_prefix='/trades')

        # centralized error handlers
        @app.errorhandler(ValidationError)
        def handle_pydantic_validation_error(e: ValidationError):
            # Return 422 Unprocessable Entity for schema validation failures
            return jsonify({
                'error': 'Validation Error',
                'detail': e.errors()
            }), 422

        @app.errorhandler(InsufficientFundsError)
        @app.errorhandler(TradeExecutionException)
        @app.errorhandler(UnsupportedUserOperationError)
        @app.errorhandler(UnsupportedPortfolioOperationError)
        @app.errorhandler(SecurityException)
        def handle_service_errors(e):
            db.session.rollback()
            return jsonify({
                'error': e.__class__.__name__,
                'detail': str(e)
            }), 400

        @app.errorhandler(AuthError)
        def handle_auth_error(e: AuthError):
            db.session.rollback()
            return jsonify({
                'error': e.error.get('error', 'Authentication Error'),
                'detail': e.error.get('detail', str(e))
            }), e.status_code

        @app.errorhandler(AuthorizationException)
        def handle_authorization_error(e: AuthorizationException):
            db.session.rollback()
            return jsonify({
                'error': 'AuthorizationException',
                'detail': str(e)
            }), 403

        @app.errorhandler(Exception)
        def handle_generic_exception(e: Exception):
            # Enforce transactional boundary by rolling back on unhandled exceptions
            db.session.rollback()
            return jsonify({
                'error': 'Internal Server Error',
                'detail': str(e)
            }), 500

        return app
    except Exception as e:
        print(f'Error creating app: {e}')
        raise

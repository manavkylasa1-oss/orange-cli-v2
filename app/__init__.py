from flask import Flask, jsonify
from pydantic import ValidationError

from app.cache import cache
from app.db import db
from app.errors import APIError
from app.routes import portfolio_bp, security_bp, trade_bp, user_bp


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    cache.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/users')
    app.register_blueprint(portfolio_bp, url_prefix='/portfolios')
    app.register_blueprint(security_bp, url_prefix='/securities')
    app.register_blueprint(trade_bp, url_prefix='/trades')

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({'error': 'validation_error', 'detail': err.errors()}), 422

    @app.errorhandler(APIError)
    def handle_api_error(err):
        db.session.rollback()
        return jsonify({'error': err.error, 'detail': err.detail}), err.status_code

    @app.errorhandler(Exception)
    def handle_exception(err):
        db.session.rollback()
        return jsonify({'error': 'internal_error', 'detail': str(err)}), 500

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok'}), 200

    return app

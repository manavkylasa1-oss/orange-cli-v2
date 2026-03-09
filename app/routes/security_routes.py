from flask import Blueprint, jsonify

import app.service.transaction_service as transaction_service
from app.auth.auth import require_auth
from app.services.alpha_vantage_client import get_quote

security_bp = Blueprint('security', __name__)


@security_bp.route('/<ticker>', methods=['GET'])
@require_auth
def get_security(ticker):
    quote = get_quote(ticker)
    if quote is None:
        return jsonify({'error': f'Security {ticker} not found'}), 404
    return jsonify({'ticker': quote.ticker, 'issuer': quote.issuer, 'price': quote.price, 'date': quote.date}), 200


@security_bp.route('/<ticker>/transactions', methods=['GET'])
@require_auth
def get_security_transactions(ticker):
    transactions = transaction_service.get_transactions_by_ticker(ticker.upper())
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200

from flask import Blueprint, jsonify, request, g

from app.db import db
from app.schemas.trade import TradeRequest
from app.services import trade_service
from app.services.trade_service import InsufficientFundsError, TradeExecutionException
from app.auth.auth import require_auth

trade_bp = Blueprint('trade', __name__)


@trade_bp.route('/buy', methods=['POST'])
@require_auth
def execute_purchase_order():
    req_data = request.get_json()
    validated_data = TradeRequest(**req_data)

    trade_service.execute_purchase_order(
        portfolio_id=validated_data.portfolio_id,
        ticker=validated_data.ticker.upper(),
        quantity=validated_data.quantity,
        execution_username=g.current_user
    )
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
@require_auth
def liquidate_investment():
    req_data = request.get_json()
    validated_data = TradeRequest(**req_data)

    trade_service.execute_sell_order(
        portfolio_id=validated_data.portfolio_id,
        ticker=validated_data.ticker.upper(),
        quantity=validated_data.quantity,
        execution_username=g.current_user
    )
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200

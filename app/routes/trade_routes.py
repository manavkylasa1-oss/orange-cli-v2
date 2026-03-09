from flask import Blueprint, g, jsonify, request

import app.service.portfolio_service as portfolio_service
from app.auth.auth import require_auth
from app.db import db
from app.errors import APIError
from app.schemas import BuyTradeRequest, SellTradeRequest
from app.services.portfolio_access_service import ROLE_MANAGER, has_access
from app.services.trade_service import execute_buy, execute_sell

trade_bp = Blueprint('trade', __name__)


def _assert_can_trade(portfolio_id: int):
    p = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not p:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    if p.owner != g.current_user and not has_access(portfolio_id, g.current_user, ROLE_MANAGER):
        raise APIError('forbidden', 'Manager access required for trades', 403)


@trade_bp.route('/buy', methods=['POST'])
@require_auth
def execute_purchase_order():
    req_data = BuyTradeRequest.model_validate(request.get_json())
    _assert_can_trade(req_data.portfolio_id)
    execute_buy(req_data.portfolio_id, req_data.ticker, req_data.quantity)
    db.session.commit()
    return jsonify({'message': 'Purchase order executed successfully'}), 201


@trade_bp.route('/sell', methods=['POST'])
@require_auth
def liquidate_investment():
    req_data = SellTradeRequest.model_validate(request.get_json())
    _assert_can_trade(req_data.portfolio_id)
    execute_sell(req_data.portfolio_id, req_data.ticker, req_data.quantity)
    db.session.commit()
    return jsonify({'message': 'Investment liquidated successfully'}), 200

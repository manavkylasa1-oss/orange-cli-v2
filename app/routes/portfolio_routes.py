from flask import Blueprint, g, jsonify, request

import app.service.portfolio_service as portfolio_service
import app.service.transaction_service as transaction_service
import app.service.user_service as user_service
from app.auth.auth import require_auth
from app.db import db
from app.errors import APIError
from app.schemas import AccessGrantRequest, CreatePortfolioRequest
from app.services.portfolio_access_service import (
    ROLE_VIEWER,
    grant_access,
    has_access,
    revoke_access,
)

portfolio_bp = Blueprint('portfolio', __name__)


def _assert_portfolio_access(portfolio_id: int, required_role: str):
    p = portfolio_service.get_portfolio_by_id(portfolio_id)
    if p is None:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    user = g.current_user
    if p.owner == user:
        return p
    if not has_access(portfolio_id, user, required_role):
        raise APIError('forbidden', 'Insufficient portfolio access', 403)
    return p


@portfolio_bp.route('/', methods=['GET'])
@require_auth
def get_all_portfolios():
    portfolios = portfolio_service.get_all_portfolios()
    visible = [p for p in portfolios if p.owner == g.current_user or has_access(p.id, g.current_user, ROLE_VIEWER)]
    return jsonify([portfolio.__to_dict__() for portfolio in visible]), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@require_auth
def get_portfolio(portfolio_id):
    portfolio = _assert_portfolio_access(portfolio_id, ROLE_VIEWER)
    return jsonify(portfolio.__to_dict__()), 200


@portfolio_bp.route('/user/<username>', methods=['GET'])
@require_auth
def get_portfolios_by_user(username):
    if g.current_user != username:
        raise APIError('forbidden', 'Cannot view another user portfolios', 403)
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': f'User {username} not found'}), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/', methods=['POST'])
@require_auth
def create_portfolio():
    req_data = CreatePortfolioRequest.model_validate(request.get_json())
    user = user_service.get_user_by_username(g.current_user)
    if user is None:
        raise APIError('not_found', f'User {g.current_user} not found', 404)
    portfolio_id = portfolio_service.create_portfolio(name=req_data.name, description=req_data.description, user=user)
    db.session.commit()
    return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@require_auth
def delete_portfolio(portfolio_id):
    p = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not p:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    if p.owner != g.current_user:
        raise APIError('forbidden', 'Only owner can delete portfolio', 403)
    portfolio_service.delete_portfolio(portfolio_id)
    db.session.commit()
    return jsonify({'message': 'Portfolio deleted successfully'}), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@require_auth
def get_portfolio_transactions(portfolio_id):
    _assert_portfolio_access(portfolio_id, ROLE_VIEWER)
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200


@portfolio_bp.route('/<int:portfolio_id>/access', methods=['POST'])
@require_auth
def grant_portfolio_access(portfolio_id):
    p = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not p:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    if p.owner != g.current_user:
        raise APIError('forbidden', 'Only owner can grant access', 403)
    req = AccessGrantRequest.model_validate(request.get_json())
    grant_access(portfolio_id, req.user_id, req.role)
    db.session.commit()
    return jsonify({'message': 'Access granted'}), 201


@portfolio_bp.route('/<int:portfolio_id>/access/<user_id>', methods=['DELETE'])
@require_auth
def revoke_portfolio_access(portfolio_id, user_id):
    p = portfolio_service.get_portfolio_by_id(portfolio_id)
    if not p:
        raise APIError('not_found', f'Portfolio {portfolio_id} not found', 404)
    if p.owner != g.current_user:
        raise APIError('forbidden', 'Only owner can revoke access', 403)
    revoke_access(portfolio_id, user_id)
    db.session.commit()
    return jsonify({'message': 'Access revoked'}), 200

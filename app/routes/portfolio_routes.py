from flask import Blueprint, jsonify, request, g
from app.auth.auth import require_auth

import app.services.portfolio_service as portfolio_service
import app.services.transaction_service as transaction_service
import app.services.user_service as user_service
from app.db import db
from app.schemas.portfolio import PortfolioRequest
from app.schemas.access import PortfolioAccessRequest
from app.services.authorization_service import AuthorizationException

portfolio_bp = Blueprint('portfolio', __name__)


@portfolio_bp.route('/', methods=['GET'])
@require_auth
def get_all_portfolios():
    portfolios = portfolio_service.get_all_portfolios()
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
@require_auth
def get_portfolio(portfolio_id):
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, execution_username=g.current_user)
    if portfolio is None:
        return jsonify({'error': 'Portfolio not found', 'detail': f'Portfolio {portfolio_id} not found'}), 404
    return jsonify(portfolio.__to_dict__()), 200


@portfolio_bp.route('/user/<username>', methods=['GET'])
@require_auth
def get_portfolios_by_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': 'User not found', 'detail': f'User {username} not found'}), 404
    portfolios = portfolio_service.get_portfolios_by_user(user)
    return jsonify([portfolio.__to_dict__() for portfolio in portfolios]), 200


@portfolio_bp.route('/', methods=['POST'])
@require_auth
def create_portfolio():
    try:
        req_data = request.get_json()
        validated_data = PortfolioRequest(**req_data)
        
        # In this context, 'owner' is the currently authenticated user
        user = user_service.get_user_by_username(g.current_user)
        if user is None:
            return jsonify({'error': 'User not found', 'detail': f'User {g.current_user} not found'}), 404
            
        portfolio_id = portfolio_service.create_portfolio(
            name=validated_data.name,
            description=validated_data.description,
            user=user,
        )
        db.session.commit()
        return jsonify({'message': 'Portfolio created successfully', 'portfolio_id': portfolio_id}), 201
    except Exception as e:
        # Fallback for unexpected errors, though many are handled by global handlers
        raise e


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
@require_auth
def delete_portfolio(portfolio_id):
    portfolio_service.delete_portfolio(portfolio_id, execution_username=g.current_user)
    db.session.commit()
    return jsonify({'message': 'Portfolio deleted successfully'}), 200


@portfolio_bp.route('/<int:portfolio_id>/transactions', methods=['GET'])
@require_auth
def get_portfolio_transactions(portfolio_id):
    transactions = transaction_service.get_transactions_by_portfolio_id(portfolio_id)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200


@portfolio_bp.route('/<int:portfolio_id>/access', methods=['POST'])
@require_auth
def grant_access(portfolio_id):
    req_data = request.get_json()
    validated_data = PortfolioAccessRequest(**req_data)
    
    # Only owner can grant access
    import app.services.authorization_service as auth_service
    if not auth_service.is_owner(portfolio_id, g.current_user):
        raise AuthorizationException("Only the portfolio owner can grant access.")
        
    auth_service.grant_access(portfolio_id, validated_data.username, validated_data.role)
    db.session.commit()
    return jsonify({'message': f'Access granted to {validated_data.username} as {validated_data.role}'}), 201


@portfolio_bp.route('/<int:portfolio_id>/access/<username>', methods=['DELETE'])
@require_auth
def revoke_access(portfolio_id, username):
    # Only owner can revoke access
    import app.services.authorization_service as auth_service
    if not auth_service.is_owner(portfolio_id, g.current_user):
        raise AuthorizationException("Only the portfolio owner can revoke access.")
        
    auth_service.revoke_access(portfolio_id, username)
    db.session.commit()
    return jsonify({'message': f'Access revoked for {username}'}), 200

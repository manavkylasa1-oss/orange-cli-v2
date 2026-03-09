from flask import Blueprint, jsonify, request
from app.auth.auth import require_auth

import app.services.transaction_service as transaction_service
import app.services.user_service as user_service
from app.db import db
from app.schemas.user import UserCreate, UserBalanceUpdate

user_bp = Blueprint('user', __name__)


@user_bp.route('/', methods=['GET'])
@require_auth
def get_users():
    users = user_service.get_all_users()
    return jsonify([user.__to_dict__() for user in users]), 200


@user_bp.route('/<username>', methods=['GET'])
@require_auth
def get_user(username):
    user = user_service.get_user_by_username(username)
    if user is None:
        return jsonify({'error': 'User Not Found', 'detail': f'User {username} not found'}), 404
    return jsonify(user.__to_dict__()), 200


@user_bp.route('/', methods=['POST'])
@require_auth
def create_user():
    req_data = request.get_json()
    validated_data = UserCreate(**req_data)
    user_service.create_user(
        username=validated_data.username, 
        password=validated_data.password, 
        firstname=validated_data.firstname, 
        lastname=validated_data.lastname, 
        balance=validated_data.balance
    )
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201


@user_bp.route('/update-balance', methods=['PUT'])
@require_auth
def update_balance():
    req_data = request.get_json()
    validated_data = UserBalanceUpdate(**req_data)
    user_service.update_user_balance(username=validated_data.username, new_balance=validated_data.new_balance)
    db.session.commit()
    return jsonify({'message': 'User balance updated successfully'}), 200


@user_bp.route('/<username>', methods=['DELETE'])
@require_auth
def delete_user(username):
    user_service.delete_user(username)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200


@user_bp.route('/<username>/transactions', methods=['GET'])
@require_auth
def get_user_transactions(username):
    transactions = transaction_service.get_transactions_by_user(username)
    return jsonify([transaction.__to_dict__() for transaction in transactions]), 200

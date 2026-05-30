from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or user.password != data['password']:
        return jsonify({'msg': 'Invalid username or password'}), 401

    token = create_access_token(identity=user.username)
    return jsonify(access_token=token)

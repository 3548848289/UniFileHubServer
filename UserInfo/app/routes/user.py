from flask import Blueprint, jsonify, request
from app.models import User,UserInfo,db
from app.utils import generate_password_hash, decode_avatar, save_avatar
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    avatar_base64 = data.get('avatar')

    if not all([username, password, avatar_base64]):
        return jsonify({"error": "Missing required fields"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    # 保存头像
    avatar_filename = save_avatar(username, avatar_base64)

    # 创建用户
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=password, share_token = hashed_password, avatar=avatar_filename)
    db.session.add(user)

    user_info = UserInfo(username=username)
    db.session.add(user_info)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 200



@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        user = User.query.filter_by(username=username).first()
        print("Received data:", user)  # 调试用

        if user and user.password == password:
            # 生成 JWT token
            token = create_access_token(identity=username)
            refresh_token = create_refresh_token(identity=username)

            avatar = user.avatar
            avatar_url = f"/avatars/{avatar}" if avatar else None

            return jsonify({
                "message": "Login successful",
                "username": username,
                "avatar_url": avatar_url,
                "access_token": token,   # <- 返回给 Qt 客户端
                "refresh_token": refresh_token
            }), 200
        elif user:
            return jsonify({"message": "Invalid username or password"}), 401
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        print("Error occurred:", e)
        return jsonify({"error": str(e)}), 500


@user_bp.route('/')
def hello():
    return "Hello, Flask!"


@user_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    avatar = user.avatar
    avatar_url = f"/avatars/{avatar}" if avatar else None

    return jsonify({
        "message": "Session valid",
        "username": username,
        "avatar_url": avatar_url,
    }), 200


@user_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    token = create_access_token(identity=username)
    return jsonify({
        "message": "Token refreshed",
        "access_token": token,
        "username": username,
    }), 200

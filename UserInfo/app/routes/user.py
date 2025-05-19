from flask import Blueprint, jsonify, request
from app.models import User,UserInfo,db
from app.utils import generate_password_hash, decode_avatar, save_avatar

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
        print("Received data:", user)  # 调试用，查看收到的请求数据

        if user:
            if user.password == password:
                avatar = user.avatar  # 假设头像存储路径在数据库中的 `avatar` 字段

                # 确保 avatar 是一个正确的字符串，不包含 b'...' 的字节类型标记
                if avatar:
                    avatar_url = f"/avatars/{avatar}"
                    # avatar_url = f"/avatars/{avatar.decode('utf-8')}"  # 这里将字节类型转换为字符串
                else:
                    avatar_url = None

                return jsonify({"message": "Login successful", "username": username, "avatar_url": avatar_url}), 200
            else:
                return jsonify({"message": "Invalid username or password"}), 401
        else:
            return jsonify({"message": "User not found"}), 404  # 用户未找到

    except Exception as e:
        print("Error occurred:", e)  # 打印异常信息到服务器日志
        return jsonify({"error": str(e)}), 500  # 返回详细错误信息



@user_bp.route('/')
def hello():
    return "Hello, Flask!"

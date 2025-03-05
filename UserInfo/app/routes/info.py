from datetime import datetime

from flask import Blueprint, jsonify, request
from app import db  # 引用应用中的 db 实例
from app.models import User, UserInfo  # 引用模型
import base64
import os

# 创建蓝图
info_bp = Blueprint('info', __name__, url_prefix='/info')


@info_bp.route('/', methods=['POST'])
def test1():
    return 'test1'


# 获取用户信息
@info_bp.route('/get_user_info', methods=['POST'])
def get_user_info():
    print("get_user_info")

    # 从请求体中获取 JSON 数据
    data = request.get_json()
    username = data.get('username')

    # 根据用户名查询用户信息
    user_info = UserInfo.query.filter_by(username=username).first()
    user_avator = User.query.filter_by(username=username).first()

    # 如果没有找到对应用户，则返回 404 错误
    if user_info is None:
        return jsonify({'error': 'User not found'}), 404

    # 假设 avatar 存储的是文件名
    avator_filename = user_avator.avatar
    if isinstance(avator_filename, bytes):  # 如果是字节类型，解码为字符串
        avator_filename = avator_filename.decode('utf-8')

    # 项目路径下的 avatars 文件夹
    avatar_folder = os.path.join(os.getcwd(), 'avatars')

    # 读取图片文件并转换为 Base64
    avatar_path = os.path.join(avatar_folder, avator_filename)
    with open(avatar_path, 'rb') as img_file:
        avator_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    # 将用户信息转换为字典格式
    user_data = {
        'id': user_info.id,
        'username': user_info.username,
        'name': user_info.name,
        'motto': user_info.motto,
        'gender': user_info.gender,
        'birthday': user_info.birthday.strftime('%Y-%m-%d') if user_info.birthday else None,
        'location': user_info.location,
        'company': user_info.company,
        'avator_base64': avator_base64  # 返回 Base64 编码的图片
    }

    # 返回 JSON 格式的响应
    return jsonify(user_data)


# 更新用户信息
@info_bp.route('/update_user_info', methods=['POST'])
def update_user_info():

    # 从请求中获取数据
    data = request.get_json()
    username = data.get('username')
    name = data.get('name')
    motto = data.get('motto')
    gender = data.get('gender')
    birthday_str = data.get('birthday')
    birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
    print(birthday)
    location = data.get('location')
    company = data.get('company')
    try:
        user_info = UserInfo.query.filter_by(username=username).first() # 查找数据库中是否存在该用户
        if user_info:
            user_info.username = username
            user_info.name = name
            user_info.motto = motto
            user_info.gender = gender
            user_info.birthday = birthday
            user_info.location = location
            user_info.company = company
        else:
            user_info = UserInfo(
                name=name, motto=motto, gender=gender, birthday=birthday,
                location=location, company=company
            )
            db.session.add(user_info)

        # 提交更改到数据库
        db.session.commit()
        return jsonify({"status": "success", "message": "User information updated successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error: {str(e)}")  # 打印出异常信息，帮助定位问题
        return jsonify({"status": "error", "message": f"Error updating user information: {str(e)}"}), 500

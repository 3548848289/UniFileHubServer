from flask import Blueprint, send_from_directory, jsonify
import os

avatar_bp = Blueprint('avatar', __name__)

@avatar_bp.route('/avatars/<filename>', methods=['GET'])
def get_avatar(filename):
    print("Request received for avatar:", filename)  # 输出请求的文件名
    try:
        avatar_folder = os.path.join(os.getcwd(), 'avatars')
        print("Avatar folder path:", avatar_folder)  # 输出头像文件夹路径
        return send_from_directory(avatar_folder, filename)  # 返回头像文件
    except Exception as e:
        print("Error:", e)  # 打印错误信息
        return jsonify({"error": "Avatar not found"}), 404  # 如果文件不存在，则返回 404

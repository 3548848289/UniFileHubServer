from flask import Blueprint, send_from_directory, jsonify
import os

avatar_bp = Blueprint('avatar', __name__)

@avatar_bp.route('/avatars/<filename>', methods=['GET'])
def get_avatar(filename):
    print("Request received for avatar:", filename)
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        avatar_folder = os.path.abspath(os.path.join(current_dir, "../..", "avatars"))
        print("Avatar folder path:", avatar_folder)
        return send_from_directory(avatar_folder, filename)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Avatar not found"}), 404

import base64
import os
from PIL import Image
from io import BytesIO
import random
from werkzeug.utils import secure_filename


def generate_password_hash(password):
    return str(random.randint(100000, 999999))


def decode_avatar(avatar_base64):
    try:
        return base64.b64decode(avatar_base64)
    except Exception:
        raise ValueError("Invalid avatar format")


def save_avatar(username, avatar_base64):
    avatar_data = decode_avatar(avatar_base64)

    # 使用 PIL 处理图片
    image = Image.open(BytesIO(avatar_data))
    project_root = os.getcwd()
    avatars_folder = os.path.join(project_root, 'avatars')
    os.makedirs(avatars_folder, exist_ok=True)

    # 定义文件名和完整路径
    avatar_filename = secure_filename(f"{username}_avatar.png")
    avatar_path = os.path.join(avatars_folder, avatar_filename)
    image.save(avatar_path, format="PNG")
    return avatar_filename

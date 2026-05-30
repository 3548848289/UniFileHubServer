import os
from flask import current_app
from werkzeug.utils import secure_filename
from app.models import File
import  time
from app.extensions import db

class StorageService:

    @staticmethod
    def get_user_root(username):
        """
        用户根目录
        """
        root = os.path.join(current_app.config['STORAGE_ROOT'], username)
        os.makedirs(root, exist_ok=True)
        return root

    @staticmethod
    def get_parent_path(username, parent_id):
        """
        根据 parent_id 获取真实父目录路径
        """
        if parent_id == 0:
            return StorageService.get_user_root(username)

        parent = File.query.filter_by(
            id=parent_id,
            username=username,
            is_dir=True
        ).first()

        if not parent:
            raise Exception("Parent directory not found")

        return parent.path


    def save_file(username, parent_id, file):
        # 获取父目录路径
        parent_path = StorageService.get_parent_path(username, parent_id)

        # 获取文件名和扩展名
        filename = file.filename
        basename, ext = os.path.splitext(filename)

        # 检查文件是否已存在，并生成新的文件名（类似于Windows (1), (2)的方式）
        new_filename = filename
        file_path = os.path.join(parent_path, new_filename)

        counter = 1
        while os.path.exists(file_path):
            # 如果文件已存在，给文件名加上 (counter) 后缀
            new_filename = f"{basename} ({counter}){ext}"
            file_path = os.path.join(parent_path, new_filename)
            counter += 1

        current_app.logger.info(f"文件保存路径: {file_path}")

        try:
            # 保存文件到指定路径
            file.save(file_path)

            return file_path
        except Exception as e:
            current_app.logger.error(f"保存文件失败: {e}")
            raise
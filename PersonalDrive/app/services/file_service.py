from app.models.file import File
from app.extensions import db
from flask import current_app
import os
import shutil
from app.services.storage_service import StorageService

class FileService:

    @staticmethod
    def list(username, parent_id):
        files = File.query.filter_by(username=username, parent_id=parent_id).all()
        return [{
            'id': f.id,
            'name': f.name,
            'is_dir': f.is_dir,
            'size': f.size
        } for f in files]

    @staticmethod
    def create_file_record(username, parent_id, name, path):
        try:
            size = os.path.getsize(path)
            file = File(username=username, parent_id=parent_id, name=name, path=path, size=size)
            db.session.add(file)
            db.session.commit()
            return file
        except Exception as e:
            db.session.rollback()
            raise Exception(f"文件记录创建失败: {str(e)}")


    @staticmethod
    def get_file(file_id, username):
        return File.query.filter_by(id=file_id, username=username).first()

    @staticmethod
    def get_path(dir_id, username):

        path = []

        if dir_id == 0:
            return [{
                "id": 0,
                "name": "个人云盘",
                "is_dir": True
            }]

        current = File.query.filter_by(
            id=dir_id,
            username=username,
            is_dir=True
        ).first()

        if not current:
            return None

        # 向上回溯父目录
        while current:
            path.insert(0, {
                "id": current.id,
                "name": current.name,
                "is_dir": True
            })

            if current.parent_id == 0:
                break

            current = File.query.filter_by(
                id=current.parent_id,
                username=username,
                is_dir=True
            ).first()

        path.insert(0, {
            "id": 0,
            "name": "个人云盘",
            "is_dir": True
        })

        return path

    @staticmethod
    def delete_file_record(file_record: File):
        """删除单个文件的数据库记录"""
        db.session.delete(file_record)
        db.session.commit()

    @staticmethod
    def delete_directory(dir_record: File):
        """
        递归删除目录及其子文件 / 子目录
        """
        try:
            # 1. 删除子内容
            children = File.query.filter_by(parent_id=dir_record.id).all()
            for child in children:
                if child.is_dir:
                    FileService.delete_directory(child)
                else:
                    if child.path and os.path.exists(child.path):
                        os.remove(child.path)
                    FileService.delete_file_record(child)

            # 2. 删除当前目录（物理）
            if dir_record.path and os.path.exists(dir_record.path):
                os.rmdir(dir_record.path)

            # 3. 删除当前目录数据库记录
            FileService.delete_file_record(dir_record)

            return True, "Deleted successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def clear_user_drive(username):
        try:
            storage_root = os.path.abspath(current_app.config['STORAGE_ROOT'])
            user_root = os.path.abspath(os.path.join(storage_root, username))

            if os.path.commonpath([storage_root, user_root]) != storage_root or user_root == storage_root:
                return False, "Invalid storage path"

            os.makedirs(user_root, exist_ok=True)

            for entry_name in os.listdir(user_root):
                entry_path = os.path.join(user_root, entry_name)
                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
                else:
                    os.remove(entry_path)

            deleted_count = File.query.filter_by(username=username).count()
            File.query.filter_by(username=username).delete(synchronize_session=False)
            db.session.commit()

            return True, deleted_count
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def create_directory(username, parent_id, folder_name):
        try:
            base_path = StorageService.get_parent_path(username, parent_id)
            folder_name = StorageService.sanitize_name(folder_name)
            folder_path = StorageService.ensure_child_path(base_path, os.path.join(base_path, folder_name))

            os.makedirs(folder_path, exist_ok=True)

            record = File(
                username=username,
                parent_id=parent_id,
                name=folder_name,
                path=folder_path,
                is_dir=True,
                size=0
            )

            db.session.add(record)
            db.session.commit()

            return True, "ok"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def _shift_descendant_paths(dir_record, old_path, new_path):
        """目录物理位置/名称变化后，同步修正其所有后代记录的 path 前缀"""
        old_prefix = old_path.rstrip(os.sep) + os.sep
        new_prefix = new_path.rstrip(os.sep) + os.sep
        frontier = [dir_record.id]
        while frontier:
            children = File.query.filter(File.parent_id.in_(frontier)).all()
            frontier = []
            for child in children:
                if child.path and child.path.startswith(old_prefix):
                    child.path = new_prefix + child.path[len(old_prefix):]
                if child.is_dir:
                    frontier.append(child.id)

    @staticmethod
    def rename_item(file_id, username, new_name):
        try:
            new_name = StorageService.sanitize_name(new_name)
            # 获取文件/目录记录
            file_record = FileService.get_file(file_id, username)
            if not file_record:
                return False, "File not found"

            # 获取父目录路径
            parent_path = StorageService.get_parent_path(username, file_record.parent_id)

            # 构建新的文件/目录路径
            new_path = StorageService.ensure_child_path(parent_path, os.path.join(parent_path, new_name))

            old_path = file_record.path

            # 重命名物理文件/目录
            if os.path.exists(file_record.path):
                os.rename(file_record.path, new_path)

            # 更新数据库记录
            file_record.name = new_name
            file_record.path = new_path
            # 文件夹重命名后，磁盘上后代位置已随目录变化，需同步修正后代记录的 path
            if file_record.is_dir:
                FileService._shift_descendant_paths(file_record, old_path, new_path)
            db.session.commit()

            return True, file_record
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def move_item(file_id, username, new_parent_id):
        try:
            file_record = FileService.get_file(file_id, username)
            if not file_record:
                return False, "File not found"

            if file_record.is_dir and file_record.id == new_parent_id:
                return False, "不能移动到自身"

            if file_record.parent_id == new_parent_id:
                return False, "文件已在该目录中"

            # 目标必须是当前用户存在的目录（0 表示根目录）
            if new_parent_id == 0:
                target_path = StorageService.get_user_root(username)
            else:
                parent = File.query.filter_by(
                    id=new_parent_id,
                    username=username,
                    is_dir=True
                ).first()
                if not parent:
                    return False, "目标目录不存在"
                target_path = parent.path

            # 文件夹不能移入自己的子目录
            if file_record.is_dir:
                frontier = [file_record.id]
                while frontier:
                    rows = File.query.filter(File.parent_id.in_(frontier)).all()
                    if any(row.id == new_parent_id for row in rows):
                        return False, "不能移动到自身的子目录中"
                    frontier = [row.id for row in rows]

            # 目标目录中不能有同名项（数据库与磁盘双重校验，磁盘校验可覆盖大小写差异）
            conflict = File.query.filter_by(
                username=username,
                parent_id=new_parent_id,
                name=file_record.name
            ).first()
            if conflict:
                return False, "目标目录已存在同名文件或文件夹"

            new_path = StorageService.ensure_child_path(
                target_path,
                os.path.join(target_path, file_record.name)
            )
            if os.path.exists(new_path):
                return False, "目标目录已存在同名文件或文件夹"

            old_path = file_record.path
            os.makedirs(target_path, exist_ok=True)
            if old_path and os.path.exists(old_path):
                shutil.move(old_path, new_path)

            file_record.parent_id = new_parent_id
            file_record.path = new_path
            # 移动文件夹时，后代的物理位置都随目录变化，同步修正后代记录的 path
            if file_record.is_dir:
                FileService._shift_descendant_paths(file_record, old_path, new_path)
            db.session.commit()

            return True, file_record
        except Exception as e:
            db.session.rollback()
            return False, str(e)

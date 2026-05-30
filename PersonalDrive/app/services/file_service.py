from app.models.file import File
from app.extensions import db
import os
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
    def create_directory(username, parent_id, folder_name):
        try:
            base_path = StorageService.get_parent_path(username, parent_id)
            folder_path = os.path.join(base_path, folder_name)

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
    def rename_item(file_id, username, new_name):
        try:
            # 获取文件/目录记录
            file_record = FileService.get_file(file_id, username)
            if not file_record:
                return False, "File not found"

            # 获取父目录路径
            parent_path = StorageService.get_parent_path(username, file_record.parent_id)
            
            # 构建新的文件/目录路径
            new_path = os.path.join(parent_path, new_name)
            
            # 重命名物理文件/目录
            if os.path.exists(file_record.path):
                os.rename(file_record.path, new_path)
            
            # 更新数据库记录
            file_record.name = new_name
            file_record.path = new_path
            db.session.commit()
            
            return True, file_record
        except Exception as e:
            db.session.rollback()
            return False, str(e)

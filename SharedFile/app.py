from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import random
import string
from werkzeug.utils import secure_filename

# 配置数据库路径
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///D:\CxxProgram\SmartDesk\.build\SmartDesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁用对象修改追踪

db = SQLAlchemy(app)

current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大文件为16MB

class SharedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    local_file_path = db.Column(db.String(255), nullable=False)
    remote_file_name = db.Column(db.String(255), nullable=False)
    share_token = db.Column(db.String(255), nullable=False)

    def __init__(self, local_file_path, remote_file_name, share_token):
        self.local_file_path = local_file_path
        self.remote_file_name = remote_file_name
        self.share_token = share_token

    def __repr__(self):
        return f'<SharedFile {self.remote_file_name}>'

def generate_share_token(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def init_db():
    with app.app_context():  # 使用应用上下文
        db.create_all()

init_db()


@app.route('/<filename>', methods=['PUT'])
def save_file(filename):
    filename = secure_filename(filename)
    unique_filename = str(uuid.uuid4()) + os.path.splitext(filename)[-1]
    init_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    backup_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        with open(backup_path, 'wb') as f:
            f.write(request.data)
    except Exception as e:
        print(f"Error occurred while saving the file: {str(e)}")
        return jsonify({'error': 'File save error', 'message': str(e)}), 500

    try:
        shared_file = SharedFile(
            local_file_path=init_path,  remote_file_name=unique_filename,  share_token=generate_share_token()
        )

        db.session.add(shared_file)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': 'Database error', 'message': str(e)}), 500

    return jsonify({"message": "File uploaded successfully", "filename": unique_filename}), 200
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

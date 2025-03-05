# import os
# from flask import Flask, request
# from werkzeug.utils import secure_filename
# from flask import jsonify, send_file
#
# app = Flask(__name__)
#
# # 上传文件的根目录
# UPLOAD_DIR = '/home/ubuntu/windows/Internet/Mytrain/mytxt2/fileHistory/uploads'
# os.makedirs(UPLOAD_DIR, exist_ok=True)
#
# ALLOWED_EXT = {'csv', 'db', 'txt', 'cpp', 'h', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
#
#
# # 判断文件是否允许
# def is_allowed(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT
#
#
# def unique_name(directory, filename):
#     base, ext = os.path.splitext(filename)
#
#     # 生成初始的新文件名
#     new_filename = f"{base}1{ext}"  # 初始文件名为 FileItemWidget1.cpp
#     counter = 1  # 初始化计数器
#
#     # 检查文件是否存在，如果存在，则生成新文件名
#     while os.path.exists(os.path.join(directory, new_filename)):
#         counter += 1  # 增加计数器
#         new_filename = f"{base}{counter}{ext}"  # 更新文件名格式为 FileItemWidget2.cpp 等
#
#     return new_filename
#
#
# @app.route('/online/<filename>', methods=['PUT'])
# def save_file(filename):
#     file_path = os.path.join("/home/ubuntu/windows/Internet/Mytrain/mytxt2/resources", filename)
#
#     with open(file_path, 'wb') as f:
#         f.write(request.data)
#
#     return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
#
#
# @app.route('/upload/<filename>', methods=['PUT'])
# def upload(filename):
#     if not is_allowed(filename):
#         return "Unsupported file type", 400
#
#     if request.content_length == 0:
#         return "No file provided", 400
#
#     path = request.args.get('path')
#     if not path:
#         return "File path not provided", 400
#
#     user_path = os.path.join(UPLOAD_DIR, path)
#     os.makedirs(user_path, exist_ok=True)
#
#     folder_name = filename.replace('.', '_')
#     final_path = os.path.join(user_path, folder_name)
#     os.makedirs(final_path, exist_ok=True)
#     save_name = unique_name(final_path, secure_filename(filename))
#     save_path = os.path.join(final_path, save_name)
#
#     if os.path.exists(save_path):
#         return "File already exists", 409  # 409 Conflict
#
#     try:
#         with open(save_path, 'wb') as f:
#             f.write(request.data)
#         return "Upload successful", 200
#     except Exception as e:
#         return f"Upload failed: {str(e)}", 500
#
#
# # 下载文件接口
# @app.route('/download/<dirname>/<filename>', methods=['GET'])
# def download(dirname, filename):
#     safe_dirname = secure_filename(dirname).replace('.', '_')
#     dir_path = os.path.join(UPLOAD_DIR, safe_dirname)
#
#     # 检查文件是否存在
#     file_path = os.path.join(dir_path, secure_filename(filename))
#     if not os.path.exists(file_path):
#         return "File not found", 404
#
#     # 发送文件进行下载
#     try:
#         return send_file(file_path, as_attachment=True)
#     except Exception as e:
#         return f"Failed to download file: {str(e)}", 500
#
#
# # 获取指定目录下所有文件的接口
# @app.route('/list/<dirname>', methods=['GET'])
# def list_files(dirname):
#     safe_dirname = secure_filename(dirname).replace('.', '_')
#     dir_path = os.path.join(UPLOAD_DIR, safe_dirname)
#
#     # 检查目录是否存在
#     if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
#         return jsonify({"error": "Directory not found"}), 404
#
#     # 获取目录下的所有文件
#     files = os.listdir(dir_path)
#     return jsonify({"files": files})
#
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
#
#     from flask import Flask, jsonify, request
#     from flask_sqlalchemy import SQLAlchemy
#
#     app = Flask(__name__)
#     app.config.from_object('config.Config')
#
#     # 初始化 SQLAlchemy
#     db = SQLAlchemy(app)
#
#
#     class Submission(db.Model):
#         id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#         file_path = db.Column(db.Text, nullable=False)
#         submit_time = db.Column(db.DateTime, default=db.func.current_timestamp())
#         records = db.relationship('SubmissionRecord', backref='submission', cascade='all, delete-orphan')
#
#
#     class SubmissionRecord(db.Model):
#         id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#         submission_id = db.Column(db.Integer, db.ForeignKey('submission.id', ondelete='CASCADE'))
#         remote_file_name = db.Column(db.String(255), nullable=False)
#         submit_time = db.Column(db.DateTime, default=db.func.current_timestamp())
#
#
#     @app.route('/record_submission', methods=['POST'])
#     def record_submission():
#         data = request.get_json()
#         file_path = data.get('file_path')
#
#         try:
#             # 查询是否已有记录
#             submission = Submission.query.filter_by(file_path=file_path).first()
#
#             if submission:
#                 submission_id = submission.id
#                 print(f"Existing submission found with ID: {submission_id}")
#             else:
#                 # 插入新记录
#                 submission = Submission(file_path=file_path)
#                 db.session.add(submission)
#                 db.session.commit()
#                 submission_id = submission.id
#                 print(f"New submission recorded with ID: {submission_id}")
#
#             # 生成新的文件名
#             submission_count = SubmissionRecord.query.filter_by(submission_id=submission_id).count()
#
#             new_submission_number = submission_count + 1
#             remote_file_name = f"{file_path.split('/')[-1].split('.')[0]}{new_submission_number}.cpp"
#
#             record = SubmissionRecord(submission_id=submission_id, remote_file_name=remote_file_name)
#             db.session.add(record)
#             db.session.commit()
#
#             return jsonify({"message": "Submission recorded successfully", "remote_file_name": remote_file_name}), 200
#
#         except Exception as e:
#             db.session.rollback()
#             return jsonify({"error": str(e)}), 500
#
#
#     if __name__ == '__main__':
#         app.run(host='0.0.0.0', port=5000, debug=True)

import os
from flask import Flask, request, send_from_directory, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXT = {'csv', 'db', 'txt', 'cpp', 'h', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def is_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def unique_name(directory, filename):
    base, ext = os.path.splitext(filename)

    # 生成初始的新文件名
    new_filename = f"{base}1{ext}"  # 初始文件名为 FileItemWidget1.cpp
    counter = 1  # 初始化计数器

    # 检查文件是否存在，如果存在，则生成新文件名
    while os.path.exists(os.path.join(directory, new_filename)):
        counter += 1  # 增加计数器
        new_filename = f"{base}{counter}{ext}"  # 更新文件名格式为 FileItemWidget2.cpp 等

    return new_filename


@app.route('/<filename>', methods=['PUT'])  # 上传文件接口
def upload_file(filename):
    file_data = request.data
    if file_data:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return jsonify({"message": "File uploaded successfully", "file_path": file_path}), 200
    else:
        return jsonify({"message": "No file provided"}), 400


# 下载文件接口
@app.route('/uploads/<filename>', methods=['GET'], strict_slashes=False)
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


# 获取指定目录下所有文件的接口
@app.route('/list', methods=['GET'], strict_slashes=False)
def list_files():
    dir_path = os.path.join(UPLOAD_FOLDER)

    # 检查目录是否存在
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return jsonify({"error": "Directory not found"}), 404

    # 获取目录下的所有文件
    files = os.listdir(dir_path)
    return jsonify({"files": files})

@app.route('/exists/<filename>', methods=['GET'])
def check_file_exists(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    exists = os.path.exists(file_path)

    print(file_path)
    return jsonify({"exists": exists}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

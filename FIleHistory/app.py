import os
from flask import Flask, request, send_from_directory, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
    print(exists)
    return jsonify({"exists": exists}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

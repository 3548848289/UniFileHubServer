import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from flask import jsonify, send_file

app = Flask(__name__)

# 上传文件的根目录
UPLOAD_DIR = '/home/ubuntu/windows/Internet/Mytrain/mytxt2/fileHistory/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {'csv', 'db', 'txt', 'cpp', 'h', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# 判断文件是否允许
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

@app.route('/online/<filename>', methods=['PUT'])
def save_file(filename):
    file_path = os.path.join("/home/ubuntu/windows/Internet/Mytrain/mytxt2/resources", filename)
    
    with open(file_path, 'wb') as f:
        f.write(request.data)

    return jsonify({"message": "File uploaded successfully", "filename": filename}), 200


@app.route('/upload/<filename>', methods=['PUT'])
def upload(filename):
    if not is_allowed(filename):
        return "Unsupported file type", 400

    if request.content_length == 0:
        return "No file provided", 400

    path = request.args.get('path')
    if not path:
        return "File path not provided", 400

    user_path = os.path.join(UPLOAD_DIR, path)
    os.makedirs(user_path, exist_ok=True)

    folder_name = filename.replace('.', '_')
    final_path = os.path.join(user_path, folder_name)
    os.makedirs(final_path, exist_ok=True)
    save_name = unique_name(final_path, secure_filename(filename))
    save_path = os.path.join(final_path, save_name)

    if os.path.exists(save_path):
        return "File already exists", 409  # 409 Conflict

    try:
        with open(save_path, 'wb') as f:
            f.write(request.data)
        return "Upload successful", 200
    except Exception as e:
        return f"Upload failed: {str(e)}", 500


# 下载文件接口
@app.route('/download/<dirname>/<filename>', methods=['GET'])
def download(dirname, filename):

    safe_dirname = secure_filename(dirname).replace('.', '_')
    dir_path = os.path.join(UPLOAD_DIR, safe_dirname)

    # 检查文件是否存在
    file_path = os.path.join(dir_path, secure_filename(filename))
    if not os.path.exists(file_path):
        return "File not found", 404

    # 发送文件进行下载
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Failed to download file: {str(e)}", 500

# 获取指定目录下所有文件的接口
@app.route('/list/<dirname>', methods=['GET'])
def list_files(dirname):
    safe_dirname = secure_filename(dirname).replace('.', '_')
    dir_path = os.path.join(UPLOAD_DIR, safe_dirname)

    # 检查目录是否存在
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return jsonify({"error": "Directory not found"}), 404

    # 获取目录下的所有文件
    files = os.listdir(dir_path)
    return jsonify({"files": files})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

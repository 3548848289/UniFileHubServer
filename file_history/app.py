import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from flask import jsonify, send_file

app = Flask(__name__)

# 上传文件的根目录
UPLOAD_DIR = '/home/ubuntu/windows/Internet/Mytrain/mytxt2/file_history/uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {'db', 'txt', 'cpp', 'h', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# 判断文件是否允许
def is_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


# 生成唯一文件名，从 xxx_1.xxx 开始
def unique_name(dir_path, filename):
    name, ext = os.path.splitext(filename)
    count = 1
    new_name = f"{name}_{count}{ext}"  # 从 xxx_1 开始
    while os.path.exists(os.path.join(dir_path, new_name)):
        count += 1
        new_name = f"{name}_{count}{ext}"
    return new_name

# 上传文件接口
@app.route('/upload/<filename>', methods=['PUT'])
def upload(filename):
    if not is_allowed(filename):
        return "Unsupported file type", 400

    if request.content_length == 0:
        return "No file provided", 400

    # 创建文件目录，点号替换为下划线
    clean_name = filename.replace('.', '_') 
    dir_path = os.path.join(UPLOAD_DIR, secure_filename(clean_name))
    os.makedirs(dir_path, exist_ok=True)

    # 生成唯一文件名，从 xxx_1 开始
    save_name = unique_name(dir_path, secure_filename(filename))
    save_path = os.path.join(dir_path, save_name)
    
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

import os
from flask import Flask, request
from werkzeug.utils import secure_filename
from flask import jsonify, send_file

app = Flask(__name__)

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

    user_path = os.path.join(UPLOAD_FOLDER, path)
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

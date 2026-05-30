import os
import random
import shutil
import string
from datetime import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:Mysql20039248@127.0.0.1:3306/SmartDesk?charset=utf8mb4",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

SHAREDCSV_RESOURCE_DIR = os.getenv(
    "SHAREDCSV_RESOURCE_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SharedCSV", "resources"),
)


class SharedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_file_path = db.Column(db.String(255), nullable=False)
    remote_file_name = db.Column(db.String(255), nullable=False)
    share_token = db.Column(db.String(255), nullable=False)

    def __init__(self, local_file_path, remote_file_name, share_token):
        self.local_file_path = local_file_path
        self.remote_file_name = remote_file_name
        self.share_token = share_token


def generate_share_token(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@app.route("/<filename>", methods=["PUT"])
def save_file(filename):
    share_token = request.args.get("share_token") or generate_share_token()

    filename = secure_filename(filename)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)

    try:
        with open(full_path, "wb") as file_obj:
            file_obj.write(request.data)

        os.makedirs(SHAREDCSV_RESOURCE_DIR, exist_ok=True)
        target_path = os.path.join(SHAREDCSV_RESOURCE_DIR, filename)
        shutil.copy(full_path, target_path)
    except Exception as exc:
        return jsonify({"error": "File save or copy error", "message": str(exc)}), 500

    try:
        shared_file = SharedFile(
            local_file_path=full_path,
            remote_file_name=filename,
            share_token=share_token,
        )
        db.session.add(shared_file)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": "DB error", "message": str(exc)}), 500

    return (
        jsonify(
            {
                "message": "File uploaded and copied successfully",
                "filename": filename,
                "share_token": share_token,
            }
        ),
        200,
    )


@app.route("/get_shared_files", methods=["GET"])
def get_shared_files():
    share_token = request.args.get("share_token")
    if not share_token:
        return jsonify({"error": "Missing share_token"}), 400

    files = SharedFile.query.filter_by(share_token=share_token).all()
    result = [
        {
            "remote_file_name": shared_file.remote_file_name,
            "local_file_path": shared_file.local_file_path,
        }
        for shared_file in files
    ]

    return jsonify({"files": result})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)

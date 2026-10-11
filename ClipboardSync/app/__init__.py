import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager


db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # multipart 上传需要比单张图片上限略大的请求体预算
    app.config['MAX_CONTENT_LENGTH'] = app.config['CLIPBOARD_MAX_IMAGE_BYTES'] + 1024 * 1024

    os.makedirs(app.config['CLIPBOARD_IMAGE_STORE_ROOT'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)

    from app.routes.clipboard import clipboard_bp
    from app.routes.images import clipboard_images_bp
    app.register_blueprint(clipboard_bp)
    app.register_blueprint(clipboard_images_bp)

    return app

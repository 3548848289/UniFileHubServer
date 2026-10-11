from flask import Flask
from .config import Config
from .extensions import db, jwt
from .routes import register_blueprints
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 允许通过 URL query 传 token：QML 的 Image 组件无法设置请求头，
    # 客户端缩略图（/api/drive/thumb）只能以 ?token= 方式鉴权
    app.config["JWT_TOKEN_LOCATION"] = ["headers", "query_string"]
    app.config["JWT_QUERY_STRING_NAME"] = "token"

    db.init_app(app)
    Migrate(app, db)

    jwt.init_app(app)

    register_blueprints(app)
    return app

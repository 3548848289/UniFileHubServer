import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'avatars')

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from app.routes import user_bp, avatar_bp, submission_bp, info_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(avatar_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(info_bp)

    # 注册错误处理
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app

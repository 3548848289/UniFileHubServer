from flask import Flask
from .config import Config
from .extensions import db, jwt
from .routes import register_blueprints
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    jwt.init_app(app)

    register_blueprints(app)
    return app

from .auth import bp as auth_bp
from .drive import bp as drive_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(drive_bp)

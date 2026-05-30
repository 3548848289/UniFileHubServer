from app.extensions import db

class User(db.Model):
    __tablename__ = 'User'
    username = db.Column(db.String(10), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    share_token = db.Column(db.String(255), unique=True, nullable=False)
    avatar = db.Column(db.String(255), nullable=False)

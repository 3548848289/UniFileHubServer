from app import db
from sqlalchemy.dialects import mysql


class CloudClipboardItem(db.Model):
    __tablename__ = 'CloudClipboardItem'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), nullable=False, index=True)
    content = db.Column(db.Text().with_variant(mysql.MEDIUMTEXT(), 'mysql'), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())


class CloudClipboardImage(db.Model):
    __tablename__ = 'CloudClipboardImage'
    __table_args__ = (
        db.UniqueConstraint('username', 'image_hash', name='uq_clipboard_image_user_hash'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), nullable=False, index=True)
    image_hash = db.Column(db.String(64), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(64), nullable=False, default='image/png')
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

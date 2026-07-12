from app import db


class CloudClipboardItem(db.Model):
    __tablename__ = 'CloudClipboardItem'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

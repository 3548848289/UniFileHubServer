from app.extensions import db
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), db.ForeignKey('User.username'))
    parent_id = db.Column(db.Integer, default=0)
    name = db.Column(db.String(255))
    path = db.Column(db.String(512))
    size = db.Column(db.BigInteger)
    is_dir = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

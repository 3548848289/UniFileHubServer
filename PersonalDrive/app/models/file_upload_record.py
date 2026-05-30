from app.extensions import db

class FileUploadRecord(db.Model):
    __tablename__ = 'file_upload_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    drive_item_id = db.Column(db.Integer, db.ForeignKey('drive_item.id', ondelete='CASCADE'), nullable=False)

    client_platform = db.Column(db.String(32))  # Windows / Mac / Linux / Mobile
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())

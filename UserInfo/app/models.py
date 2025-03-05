from app import db


class Submission(db.Model):
    __tablename__ = 'Submission'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_path = db.Column(db.Text, nullable=False)
    submit_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    records = db.relationship('SubmissionRecord', backref='Submission', cascade='all, delete-orphan')


class SubmissionRecord(db.Model):
    __tablename__ = 'SubmissionRecord'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('Submission.id', ondelete='CASCADE'))
    remote_file_name = db.Column(db.String(255), nullable=False)
    submit_time = db.Column(db.DateTime, default=db.func.current_timestamp())


class User(db.Model):
    __tablename__ = 'User'
    username = db.Column(db.String(10), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    share_token = db.Column(db.String(255), unique=True, nullable=False)
    avatar = db.Column(db.String(255), nullable=False)


class UserInfo(db.Model):
    __tablename__ = 'UserInfo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(10), db.ForeignKey('User.username', ondelete='CASCADE'))
    name = db.Column(db.String(20))
    motto = db.Column(db.String(50))
    gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    birthday = db.Column(db.Date)
    location = db.Column(db.String(100))
    company = db.Column(db.String(100))

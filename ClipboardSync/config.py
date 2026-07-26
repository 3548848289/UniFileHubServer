import os
from datetime import timedelta


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:Mysql20039248@127.0.0.1:3306/SmartDesk?charset=utf8mb4',
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    CLIPBOARD_MAX_CONTENT_BYTES = min(
        int(os.getenv('CLIPBOARD_MAX_CONTENT_BYTES', str(16 * 1024 * 1024 - 1))),
        16 * 1024 * 1024 - 1,
    )

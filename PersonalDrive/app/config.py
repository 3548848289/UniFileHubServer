import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:Mysql20039248@127.0.0.1:3306/SmartDesk?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORAGE_ROOT = os.getenv("STORAGE_ROOT", os.path.abspath("app/storage"))
    DOWNLOAD_RATE_LIMIT_BYTES_PER_SECOND = int(
        os.getenv("DOWNLOAD_RATE_LIMIT_BYTES_PER_SECOND", 100 * 1024 * 1024)
    )

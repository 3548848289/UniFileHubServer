import os

class Config:
    SECRET_KEY = "dev-secret"
    JWT_SECRET_KEY = "jwt-secret-key"

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Mysql20039248@127.0.0.1/SmartDesk'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STORAGE_ROOT = os.path.abspath('app/storage')

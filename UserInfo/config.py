class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Mysql20039248@127.0.0.1/SmartDesk'  # 数据库连接字符串
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭对象修改追踪，避免警告

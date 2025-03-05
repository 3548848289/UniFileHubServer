from flask import Blueprint, jsonify
from app import db  # 引用应用中的 db 对象

db_blueprint = Blueprint('db', __name__)

@db_blueprint.route('/create_tables', methods=['POST'])
def create_tables():
    try:
        db.create_all()  # 创建所有定义的表
        return jsonify({"message": "All tables created successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

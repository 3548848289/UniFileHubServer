from flask import Blueprint, request, jsonify

from app import db
from app.models import Submission, SubmissionRecord

submission_bp = Blueprint('submission', __name__)


@submission_bp.route('/submission', methods=['GET'])
def avatar_route():
    return "submission route is working!"


@submission_bp.route('/record_submission', methods=['POST'])
def record_submission():
    data = request.get_json()
    file_path = data.get('file_path')

    try:
        # 查询是否已有记录
        submission = Submission.query.filter_by(file_path=file_path).first()

        if submission:
            submission_id = submission.id
            print(f"Existing submission found with ID: {submission_id}")
        else:
            # 插入新记录
            submission = Submission(file_path=file_path)
            db.session.add(submission)
            db.session.commit()
            submission_id = submission.id
            print(f"New submission recorded with ID: {submission_id}")

        # 生成新的文件名
        submission_count = SubmissionRecord.query.filter_by(submission_id=submission_id).count()

        new_submission_number = submission_count + 1
        remote_file_name = f"{file_path.split('/')[-1].split('.')[0]}{new_submission_number}.cpp"

        record = SubmissionRecord(submission_id=submission_id, remote_file_name=remote_file_name)
        db.session.add(record)
        db.session.commit()

        return jsonify({"message": "Submission recorded successfully", "remote_file_name": remote_file_name}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

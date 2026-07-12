import hashlib

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import CloudClipboardItem


clipboard_bp = Blueprint('clipboard', __name__)


@clipboard_bp.route('/clipboard/items', methods=['GET'])
@jwt_required()
def list_items():
    username = get_jwt_identity()
    items = (CloudClipboardItem.query
             .filter_by(username=username)
             .order_by(CloudClipboardItem.created_at.desc(), CloudClipboardItem.id.desc())
             .limit(100)
             .all())

    return jsonify({
        'items': [
            {
                'id': item.id,
                'content': item.content,
                'created_at': item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ]
    }), 200


@clipboard_bp.route('/clipboard/items', methods=['POST'])
@jwt_required()
def create_item():
    username = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()

    if not content:
        return jsonify({'message': 'content is required'}), 400

    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    existing = (CloudClipboardItem.query
                .filter_by(username=username, content_hash=content_hash)
                .order_by(CloudClipboardItem.id.desc())
                .first())
    if existing and existing.content == content:
        return jsonify({
            'message': 'already synced',
            'id': existing.id,
        }), 200

    item = CloudClipboardItem(
        username=username,
        content=content,
        content_hash=content_hash,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        'message': 'ok',
        'id': item.id,
    }), 201


@clipboard_bp.route('/clipboard/items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    username = get_jwt_identity()
    item = CloudClipboardItem.query.filter_by(id=item_id, username=username).first()

    if not item:
        return jsonify({'message': 'item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200

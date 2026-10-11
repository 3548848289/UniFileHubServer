import hashlib
import queue

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import db
from app.models import CloudClipboardItem, CloudClipboardImage
from app.realtime import (
    broadcast_clipboard_changed,
    sse_event,
    subscribe,
    unsubscribe,
)
from app.routes.images import delete_image_files


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


@clipboard_bp.route('/clipboard/items', methods=['DELETE'])
@jwt_required()
def clear_items():
    username = get_jwt_identity()
    deleted_count = (CloudClipboardItem.query
                     .filter_by(username=username)
                     .delete(synchronize_session=False))

    images = CloudClipboardImage.query.filter_by(username=username).all()
    deleted_image_count = 0
    for image in images:
        if delete_image_files(image):
            deleted_image_count += 1
        db.session.delete(image)

    db.session.commit()
    broadcast_clipboard_changed(username, 'cleared')

    return jsonify({
        'message': 'cleared',
        'deleted_count': deleted_count,
        'deleted_image_count': deleted_image_count,
    }), 200


@clipboard_bp.route('/clipboard/events', methods=['GET'])
@jwt_required()
def clipboard_events():
    username = get_jwt_identity()
    subscriber = subscribe(username)

    @stream_with_context
    def event_stream():
        try:
            yield sse_event('connected', {'message': 'ok'})
            while True:
                try:
                    payload = subscriber.get(timeout=25)
                    yield sse_event('clipboard_changed', payload)
                except queue.Empty:
                    yield ': ping\n\n'
        finally:
            unsubscribe(username, subscriber)

    return Response(event_stream(), mimetype='text/event-stream')


@clipboard_bp.route('/clipboard/items', methods=['POST'])
@jwt_required()
def create_item():
    username = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    content = data.get('content') or ''

    if not isinstance(content, str):
        return jsonify({'message': 'content must be text'}), 400

    if not content.strip():
        return jsonify({'message': 'content is required'}), 400

    content_bytes = len(content.encode('utf-8'))
    max_content_bytes = current_app.config['CLIPBOARD_MAX_CONTENT_BYTES']
    if content_bytes > max_content_bytes:
        return jsonify({
            'message': 'content is too large',
            'max_bytes': max_content_bytes,
            'actual_bytes': content_bytes,
        }), 413

    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    existing = (CloudClipboardItem.query
                .filter_by(username=username, content_hash=content_hash)
                .order_by(CloudClipboardItem.id.desc())
                .first())
    if existing and existing.content == content:
        broadcast_clipboard_changed(username, 'already_synced')
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
    broadcast_clipboard_changed(username, 'created')

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
    broadcast_clipboard_changed(username, 'deleted')
    return jsonify({'message': 'deleted'}), 200

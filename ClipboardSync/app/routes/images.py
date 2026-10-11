import hashlib
import os
from io import BytesIO

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app import db
from app.models import CloudClipboardImage
from app.realtime import broadcast_clipboard_changed


clipboard_images_bp = Blueprint('clipboard_images', __name__)

# PIL 图片格式 → (文件扩展名, MIME 类型)
_FORMAT_META = {
    'PNG': ('png', 'image/png'),
    'JPEG': ('jpg', 'image/jpeg'),
    'GIF': ('gif', 'image/gif'),
    'BMP': ('bmp', 'image/bmp'),
    'WEBP': ('webp', 'image/webp'),
}


def _user_store_dir(username):
    root = current_app.config['CLIPBOARD_IMAGE_STORE_ROOT']
    user_dir = os.path.join(root, secure_filename(username) or '_unknown')
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def _image_file_path(image):
    return os.path.join(
        current_app.config['CLIPBOARD_IMAGE_STORE_ROOT'],
        secure_filename(image.username) or '_unknown',
        image.filename,
    )


def delete_image_files(image):
    """删除图片对应的磁盘文件，返回文件是否真的被删除。"""
    try:
        path = _image_file_path(image)
    except Exception:
        return False
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError:
        pass
    return False


def _prune_old_images(username):
    """超出单用户上限时删除最旧的图片（行 + 文件）。"""
    max_count = current_app.config['CLIPBOARD_IMAGE_MAX_COUNT']
    stale = (CloudClipboardImage.query
             .filter_by(username=username)
             .order_by(CloudClipboardImage.created_at.desc(), CloudClipboardImage.id.desc())
             .offset(max_count)
             .all())
    for image in stale:
        delete_image_files(image)
        db.session.delete(image)


def _serialize_image(image):
    return {
        'id': image.id,
        'filename': image.filename,
        'mime_type': image.mime_type,
        'size_bytes': image.size_bytes,
        'width': image.width,
        'height': image.height,
        'created_at': image.created_at.isoformat() if image.created_at else None,
    }


@clipboard_images_bp.route('/clipboard/images', methods=['GET'])
@jwt_required()
def list_images():
    username = get_jwt_identity()
    images = (CloudClipboardImage.query
              .filter_by(username=username)
              .order_by(CloudClipboardImage.created_at.desc(), CloudClipboardImage.id.desc())
              .limit(current_app.config['CLIPBOARD_IMAGE_MAX_COUNT'])
              .all())

    return jsonify({'images': [_serialize_image(image) for image in images]}), 200


@clipboard_images_bp.route('/clipboard/images', methods=['POST'])
@jwt_required()
def upload_image():
    username = get_jwt_identity()
    uploaded = request.files.get('file')
    if uploaded is None or not uploaded.filename:
        return jsonify({'message': 'file is required'}), 400

    data = uploaded.read()
    if not data:
        return jsonify({'message': 'file is empty'}), 400

    max_image_bytes = current_app.config['CLIPBOARD_MAX_IMAGE_BYTES']
    if len(data) > max_image_bytes:
        return jsonify({
            'message': 'image is too large',
            'max_bytes': max_image_bytes,
            'actual_bytes': len(data),
        }), 413

    # 用 PIL 校验确实是图片，并取真实尺寸，不信任表单里的 width/height
    try:
        with Image.open(BytesIO(data)) as img:
            pil_format = (img.format or '').upper()
            width, height = img.size
    except (UnidentifiedImageError, OSError):
        return jsonify({'message': 'file is not a valid image'}), 400

    extension, mime_type = _FORMAT_META.get(pil_format, ('png', 'image/png'))
    image_hash = hashlib.sha256(data).hexdigest()
    filename = f'{image_hash}.{extension}'

    existing = CloudClipboardImage.query.filter_by(
        username=username, image_hash=image_hash).first()
    if existing:
        broadcast_clipboard_changed(username, 'already_synced')
        return jsonify({
            'message': 'already synced',
            'id': existing.id,
        }), 200

    file_path = os.path.join(_user_store_dir(username), filename)
    try:
        with open(file_path, 'wb') as f:
            f.write(data)
    except OSError:
        return jsonify({'message': 'failed to store image'}), 500

    image = CloudClipboardImage(
        username=username,
        image_hash=image_hash,
        filename=filename,
        mime_type=mime_type,
        size_bytes=len(data),
        width=width,
        height=height,
    )
    db.session.add(image)
    try:
        db.session.commit()
    except IntegrityError:
        # 并发上传同一张图：文件内容一致，回退为已同步
        db.session.rollback()
        delete_image_files(image)
        existing = CloudClipboardImage.query.filter_by(
            username=username, image_hash=image_hash).first()
        if existing:
            broadcast_clipboard_changed(username, 'already_synced')
            return jsonify({
                'message': 'already synced',
                'id': existing.id,
            }), 200
        return jsonify({'message': 'failed to store image'}), 500

    _prune_old_images(username)
    db.session.commit()
    broadcast_clipboard_changed(username, 'created')

    return jsonify({
        'message': 'ok',
        'id': image.id,
    }), 201


@clipboard_images_bp.route('/clipboard/images/<int:image_id>/data', methods=['GET'])
@jwt_required()
def download_image(image_id):
    username = get_jwt_identity()
    image = CloudClipboardImage.query.filter_by(id=image_id, username=username).first()

    if not image:
        return jsonify({'message': 'image not found'}), 404

    file_path = _image_file_path(image)
    if not os.path.isfile(file_path):
        return jsonify({'message': 'image file missing'}), 404

    return send_file(file_path, mimetype=image.mime_type, conditional=True)


@clipboard_images_bp.route('/clipboard/images/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_image(image_id):
    username = get_jwt_identity()
    image = CloudClipboardImage.query.filter_by(id=image_id, username=username).first()

    if not image:
        return jsonify({'message': 'image not found'}), 404

    delete_image_files(image)
    db.session.delete(image)
    db.session.commit()
    broadcast_clipboard_changed(username, 'deleted')
    return jsonify({'message': 'deleted'}), 200

from flask import Blueprint, request, jsonify, Response, current_app, stream_with_context, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timezone
import mimetypes
import os
import shutil
import time
from urllib.parse import quote
from app.services.file_service import FileService
from app.services.storage_service import StorageService
from app.models import File

bp = Blueprint('drive', __name__, url_prefix='/api/drive')

# 支持生成缩略图的图片扩展名（Pillow 原生支持的格式）
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}


def iter_limited_file(file_path, bytes_per_second, chunk_size=64 * 1024):
    sent_bytes = 0
    started_at = time.monotonic()

    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break

            sent_bytes += len(chunk)
            yield chunk

            if bytes_per_second > 0:
                expected_elapsed = sent_bytes / bytes_per_second
                actual_elapsed = time.monotonic() - started_at
                delay = expected_elapsed - actual_elapsed
                if delay > 0:
                    time.sleep(delay)


def content_disposition_for_download(filename):
    fallback = filename.encode('ascii', 'ignore').decode('ascii') or 'download'
    fallback = fallback.replace('\\', '_').replace('/', '_').replace('"', "'")
    return f'attachment; filename="{fallback}"; filename*=UTF-8\'\'{quote(filename)}'


def utc_isoformat(value):
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat()


@bp.route('/check_name', methods=['GET'])
@jwt_required()
def check_name():
    username = get_jwt_identity()
    parent_id = request.args.get('parent_id', 0, type=int)
    name = request.args.get('name') or ''

    try:
        safe_name = StorageService.sanitize_name(name)
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    existing = File.query.filter_by(username=username, parent_id=parent_id, name=safe_name).first()
    return jsonify({
        'exists': existing is not None,
        'item': {
            'id': existing.id,
            'name': existing.name,
            'is_dir': existing.is_dir,
            'size': existing.size,
            'created_at': utc_isoformat(existing.created_at),
        } if existing else None,
    }), 200


@bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    username = get_jwt_identity()

    parent_id = request.form.get('parent_id', 0, type=int)
    file = request.files.get('file')

    if not file:
        return jsonify({'msg': '未提供文件'}), 422

    # 获取上传的文件名
    target_name = request.form.get('target_name') or file.filename
    overwrite = (request.form.get('overwrite') or '').lower() in {'1', 'true', 'yes', 'on'}
    filename = target_name

    # 直接使用文件名，无需转码
    current_app.logger.info(f"接收到文件: {filename}")

    try:
        safe_target_name = StorageService.sanitize_name(target_name)
        conflict = File.query.filter_by(username=username, parent_id=parent_id, name=safe_target_name).first()
        if overwrite and conflict:
            if conflict.is_dir:
                return jsonify({'msg': 'Cannot overwrite a folder with a file'}), 400
            if conflict.path and os.path.exists(conflict.path):
                os.remove(conflict.path)
            FileService.delete_file_record(conflict)

        save_path = StorageService.save_file(
            username,
            parent_id,
            file,
            target_name=safe_target_name,
            auto_rename=not overwrite
        )
        # 使用保存后的文件名（可能是处理过的新文件名）
        saved_filename = os.path.basename(save_path)
        record = FileService.create_file_record(username, parent_id, saved_filename, save_path)
        return jsonify({
            'msg': '文件上传成功',
            'id': record.id,
            'name': record.name,
            'is_dir': record.is_dir,
            'size': record.size,
            'parent_id': record.parent_id,
            'created_at': utc_isoformat(record.created_at)
        }), 200
    except ValueError as e:
        current_app.logger.warning(f"Invalid upload request: {str(e)}")
        return jsonify({'msg': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"上传失败: {str(e)}")
        return jsonify({'msg': '文件上传失败', 'error': str(e)}), 500


@bp.route('/batch_upload', methods=['POST'])
@jwt_required()
def batch_upload_files():
    username = get_jwt_identity()
    parent_id = request.form.get('parent_id', 0, type=int)
    files = request.files.getlist('files') or request.files.getlist('file')

    files = [file for file in files if file and file.filename]
    if not files:
        return jsonify({'msg': '未提供文件'}), 422

    uploaded = []
    failed = []

    for file in files:
        original_name = file.filename
        try:
            save_path = StorageService.save_file(username, parent_id, file)
            saved_filename = os.path.basename(save_path)
            record = FileService.create_file_record(username, parent_id, saved_filename, save_path)
            uploaded.append({
                'id': record.id,
                'name': record.name,
                'size': record.size,
                'parent_id': record.parent_id,
                'created_at': utc_isoformat(record.created_at),
                'original_name': original_name,
            })
        except Exception as e:
            current_app.logger.warning(f"批量上传文件失败: {original_name}: {str(e)}")
            failed.append({
                'name': original_name,
                'error': str(e),
            })

    status_code = 200 if not failed else 207
    return jsonify({
        'msg': '批量上传完成' if not failed else '批量上传部分失败',
        'success_count': len(uploaded),
        'failed_count': len(failed),
        'files': uploaded,
        'failed': failed,
    }), status_code


@bp.route('/download/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    username = get_jwt_identity()
    file_record = FileService.get_file(file_id, username)
    if not file_record:
        return jsonify({'msg': 'File not found'}), 404

    if not file_record.path or not os.path.isfile(file_record.path):
        return jsonify({'msg': 'File not found'}), 404

    rate_limit = current_app.config.get('DOWNLOAD_RATE_LIMIT_BYTES_PER_SECOND', 10 * 1024 * 1024)
    filename = file_record.name or os.path.basename(file_record.path)
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    headers = {
        'Content-Disposition': content_disposition_for_download(filename),
        'Content-Length': str(os.path.getsize(file_record.path)),
    }

    return Response(
        stream_with_context(iter_limited_file(file_record.path, rate_limit)),
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True,
    )


def generate_thumbnail(src_path, cache_path, max_px):
    """生成 JPEG 缩略图：EXIF 方向校正，透明背景铺白"""
    from PIL import Image, ImageOps

    with Image.open(src_path) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_px, max_px))

        has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
        if has_alpha:
            rgba = img.convert('RGBA')
            canvas = Image.new('RGB', rgba.size, (255, 255, 255))
            canvas.paste(rgba, mask=rgba.split()[-1])
            canvas.save(cache_path, 'JPEG', quality=85)
        else:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(cache_path, 'JPEG', quality=85)


def remove_thumbnail_cache(file_ids):
    """删除文件时清理其缩略图缓存（尽力而为，不影响主流程）"""
    cache_root = current_app.config.get('THUMB_CACHE_ROOT')
    if not cache_root:
        return
    for file_id in file_ids:
        shutil.rmtree(os.path.join(cache_root, str(file_id)), ignore_errors=True)


@bp.route('/thumb/<int:file_id>', methods=['GET'])
@jwt_required()
def thumb_file(file_id):
    username = get_jwt_identity()
    file_record = FileService.get_file(file_id, username)
    if not file_record or file_record.is_dir:
        return jsonify({'msg': 'File not found'}), 404

    ext = os.path.splitext(file_record.name or '')[1].lower()
    if ext not in IMAGE_EXTS:
        return jsonify({'msg': 'Not a supported image'}), 404

    if not file_record.path or not os.path.isfile(file_record.path):
        return jsonify({'msg': 'File not found'}), 404

    # 缩略图边长限制在 16~512，避免恶意请求撑爆缓存
    max_px = max(16, min(512, request.args.get('w', 128, type=int)))

    # 缓存键带源文件 mtime：文件内容按 id 不可变，但数据库重建后 id 可能复用，
    # mtime 参与键名可避免把旧文件的缩略图发给同名同 id 的新文件
    cache_dir = os.path.join(current_app.config['THUMB_CACHE_ROOT'], str(file_id))
    os.makedirs(cache_dir, exist_ok=True)
    src_mtime = int(os.path.getmtime(file_record.path))
    cache_path = os.path.join(cache_dir, f'{max_px}_{src_mtime}.jpg')

    if not os.path.isfile(cache_path):
        tmp_path = cache_path + '.tmp'
        try:
            generate_thumbnail(file_record.path, tmp_path, max_px)
            os.replace(tmp_path, cache_path)
        except Exception:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            return jsonify({'msg': 'Thumbnail generation failed'}), 404

    response = send_file(cache_path, mimetype='image/jpeg', conditional=True)
    response.headers['Cache-Control'] = 'private, max-age=86400'
    return response

@bp.route('/list', methods=['GET'])
@jwt_required()
def list_files():
    username = get_jwt_identity()
    parent_id = request.args.get('parent_id', 0, type=int)

    files = File.query.filter_by(username=username, parent_id=parent_id)\
                      .order_by(File.is_dir.desc(), File.name.asc())\
                      .all()

    return jsonify([
        {
            "id": f.id,
            "name": f.name,
            "is_dir": f.is_dir,
            "size": f.size,
            "parent_id": f.parent_id,
            "created_at": utc_isoformat(f.created_at)
        }
        for f in files
    ])


@bp.route('/path', methods=['GET'])
@jwt_required()
def get_path():
    username = get_jwt_identity()
    dir_id = request.args.get('dir_id', 0, type=int)

    # 从数据库获取完整路径信息
    path = FileService.get_path(dir_id, username)

    if path is None:
        return jsonify({'msg': 'Directory not found'}), 404

    return jsonify(path)


@bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_drive():
    username = get_jwt_identity()

    success, result = FileService.clear_user_drive(username)
    if not success:
        return jsonify({'msg': result}), 500

    # 清空网盘时整体重建缩略图缓存目录（缓存按 id+mtime 键，重建成本低）
    shutil.rmtree(current_app.config.get('THUMB_CACHE_ROOT', ''), ignore_errors=True)

    return jsonify({'msg': 'ok', 'deleted_count': result})


@bp.route('/delete/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    username = get_jwt_identity()

    # 获取文件记录
    file_record = FileService.get_file(file_id, username)
    if not file_record:
        return jsonify({'msg': 'File not found'}), 404

    # 如果是目录，可能需要递归删除子文件
    if file_record.is_dir:
        # 先收集自身及全部后代 id，删除成功后清理对应缩略图缓存
        related_ids = [file_record.id]
        frontier = [file_record.id]
        while frontier:
            rows = File.query.filter(File.parent_id.in_(frontier)).all()
            frontier = [row.id for row in rows]
            related_ids.extend(frontier)

        success, msg = FileService.delete_directory(file_record)
        if not success:
            return jsonify({'msg': msg}), 400
        remove_thumbnail_cache(related_ids)
    else:
        try:
            # 删除实际文件
            if os.path.exists(file_record.path):
                os.remove(file_record.path)
            # 删除数据库记录
            FileService.delete_file_record(file_record)
        except Exception as e:
            return jsonify({'msg': f'Deletion failed: {str(e)}'}), 500

        remove_thumbnail_cache([file_id])

    return jsonify({'msg': 'ok'})


@bp.route('/new_folder/<int:parent_id>/<folder_name>', methods=['POST'])
@jwt_required()
def new_folder(parent_id, folder_name):
    username = get_jwt_identity()

    success, msg = FileService.create_directory(
        username=username,
        parent_id=parent_id,
        folder_name=folder_name
    )

    if not success:
        return jsonify({'msg': msg}), 400

    return jsonify({'msg': 'ok'})

@bp.route('/rename', methods=['POST'])
@jwt_required()
def rename_item():
    username = get_jwt_identity()
    data = request.get_json()
    
    # 获取请求参数
    item_id = data.get('item_id')
    new_name = data.get('new_name')
    
    # 验证参数
    if not item_id or not new_name:
        return jsonify({'msg': 'Missing required parameters'}), 400
    
    try:
        # 调用文件服务进行重命名
        success, result = FileService.rename_item(item_id, username, new_name)
        
        if not success:
            return jsonify({'msg': result}), 400
        
        # 返回更新后的文件信息
        return jsonify({
            "id": result.id,
            "name": result.name,
            "is_dir": result.is_dir,
            "size": result.size,
            "parent_id": result.parent_id,
            "created_at": utc_isoformat(result.created_at)
        }), 200
    except Exception as ex:
        current_app.logger.error(f"Rename failed: {str(e)}")
        return jsonify({'msg': 'Rename failed', 'error': str(e)}), 500



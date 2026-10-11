# -*- coding: utf-8 -*-
"""缩略图生成逻辑验证脚本（本地运行，不依赖数据库）"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from app.routes.drive import IMAGE_EXTS, generate_thumbnail


def make_test_images(tmp):
    # 1. 大 JPEG，带 EXIF Orientation=6（旋转 90°，验证 exif_transpose）
    img = Image.new('RGB', (2000, 1000), (200, 60, 60))
    exif = img.getexif()
    exif[274] = 6  # Orientation tag
    img.save(os.path.join(tmp, 'photo.jpg'), exif=exif)

    # 2. 透明 PNG（验证铺白底）
    img = Image.new('RGBA', (800, 400), (0, 0, 0, 0))
    for x in range(0, 800, 40):
        for y in range(0, 400, 40):
            if (x + y) % 80 == 0:
                img.putpixel((x, y), (30, 120, 255, 255))
    img.save(os.path.join(tmp, 'logo.png'))

    # 3. GIF
    Image.new('P', (300, 300), 3).save(os.path.join(tmp, 'anim.gif'))

    # 4. 损坏文件
    with open(os.path.join(tmp, 'broken.jpg'), 'wb') as f:
        f.write(b'\xff\xd8\xff not really a jpeg')


def main():
    tmp = tempfile.mkdtemp(prefix='thumb_test_')
    make_test_images(tmp)

    cases = [
        ('photo.jpg', 'JPEG'), ('logo.png', 'PNG'), ('anim.gif', 'GIF'),
    ]
    for name, _ in cases:
        src = os.path.join(tmp, name)
        out = os.path.join(tmp, name + '.thumb.jpg')
        generate_thumbnail(src, out, 128)
        with Image.open(out) as thumb:
            assert max(thumb.size) <= 128, f'{name}: size {thumb.size}'
            print(f'{name}: OK, thumb={thumb.size}, mode={thumb.mode}')

    # EXIF 方向校正：原图 2000x1000 + Orientation=6 → 转正后缩略图应为竖版 (高>宽)
    with Image.open(os.path.join(tmp, 'photo.jpg.thumb.jpg')) as thumb:
        assert thumb.height > thumb.width, f'EXIF orientation not applied: {thumb.size}'
        print('photo.jpg: EXIF 方向已校正 ->', thumb.size)

    # 损坏文件必须抛异常，且不留下半成品
    broken_out = os.path.join(tmp, 'broken.thumb.jpg')
    try:
        generate_thumbnail(os.path.join(tmp, 'broken.jpg'), broken_out, 128)
        raise AssertionError('损坏文件未抛出异常')
    except Exception:
        assert not os.path.exists(broken_out), '失败时留下了半成品缓存文件'
        print('broken.jpg: 正确抛出异常，无残留文件')

    # 扩展名判断
    assert '.jpg' in IMAGE_EXTS and '.webp' in IMAGE_EXTS and '.txt' not in IMAGE_EXTS
    print('IMAGE_EXTS: OK')
    print('ALL THUMB TESTS PASSED')


if __name__ == '__main__':
    main()

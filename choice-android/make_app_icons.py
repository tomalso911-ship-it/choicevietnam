# -*- coding: utf-8 -*-
"""
Choice Viet Nam APK icon generator

用法：
    1. 先用 image_gen 或设计师出图，得到一张 1024x1024 的方形 Logo PNG。
    2. 把 PNG 路径填到下面的 SOURCE。
    3. 运行：python make_app_icons.py

产物：
    app/src/main/res/mipmap-*/ic_launcher.png
    app/src/main/res/mipmap-*/ic_launcher_round.png
    app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml
    app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml
"""
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "icon_source.png")

RES_DIR = os.path.join(HERE, "app", "src", "main", "res")

SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


def make_circular(src: Image.Image) -> Image.Image:
    """把方形图裁成圆形（透明背景），用于 legacy round icon。"""
    size = src.size[0]
    mask = Image.new("L", (size, size), 0)
    draw = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)
    draw.paste(src, (0, 0), mask)
    return draw


def main():
    if not os.path.isfile(SOURCE):
        print("[ERROR] 找不到源图标：%s" % SOURCE)
        print("请先生成 1024x1024 的方形 Logo PNG，并把 SOURCE 变量指向它。")
        return 1

    src = Image.open(SOURCE).convert("RGBA")
    if src.size[0] != src.size[1]:
        print("[WARN] 源图不是正方形，将按中心裁切。")
        w, h = src.size
        s = min(w, h)
        left = (w - s) // 2
        top = (h - s) // 2
        src = src.crop((left, top, left + s, top + s))

    if src.size[0] != 1024:
        src = src.resize((1024, 1024), Image.LANCZOS)

    for folder, size in SIZES.items():
        out_dir = os.path.join(RES_DIR, folder)
        os.makedirs(out_dir, exist_ok=True)

        square = src.resize((size, size), Image.LANCZOS)
        square_path = os.path.join(out_dir, "ic_launcher.png")
        square.save(square_path, "PNG")

        circle = make_circular(square)
        round_path = os.path.join(out_dir, "ic_launcher_round.png")
        circle.save(round_path, "PNG")

        print("  -> %s/ic_launcher.png (%dx%d)" % (folder, size, size))
        print("  -> %s/ic_launcher_round.png (%dx%d)" % (folder, size, size))

    # Adaptive icons for API 26+
    any_dir = os.path.join(RES_DIR, "mipmap-anydpi-v26")
    os.makedirs(any_dir, exist_ok=True)

    adaptive_xml = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher" />
</adaptive-icon>
'''
    with open(os.path.join(any_dir, "ic_launcher.xml"), "w", encoding="utf-8") as f:
        f.write(adaptive_xml)
    with open(os.path.join(any_dir, "ic_launcher_round.xml"), "w", encoding="utf-8") as f:
        f.write(adaptive_xml)

    print("[OK] icons generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

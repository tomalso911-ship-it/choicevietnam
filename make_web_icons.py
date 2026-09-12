# -*- coding: utf-8 -*-
"""生成网页版 / PWA 图标 —— 与手机(APK)、电脑(EXE)【同一个 AGI 徽标】。

统一来源：android/logo_agi.svg
渲染方式：直接调用 android/make_app_icons.py（APK 用的就是它），
          保证三端画出来的图形一模一样。

产出（都在项目根目录，供 index.html / manifest.json 引用）：
  favicon.svg            矢量图标（浏览器标签、主 PWA）
  icon-192.png           PWA 192
  icon-512.png           PWA 512
  icon-512-maskable.png  PWA 可遮罩版（内容缩到 80% 安全区，四边留白）
  apple-touch-icon.png   iOS 添加到主屏幕（180）

用法：python make_web_icons.py
"""
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
ANDROID = os.path.join(ROOT, "android")
SVG = os.path.join(ANDROID, "logo_agi.svg")

if not os.path.isfile(SVG):
    print("缺少 %s" % SVG)
    sys.exit(1)

sys.path.insert(0, ANDROID)
import make_app_icons as mki  # noqa: E402  （APK 图标的同一套绘制代码）

RENDER = 512


def logo(size):
    """渲染 AGI 徽标（与 APK 的 ic_launcher.png 完全相同）"""
    return mki.make_icon(size).convert("RGBA")


def maskable(size, content_ratio=0.8):
    """可遮罩图标：内容缩到 80% 安全区，整幅白底（遮罩裁切时不会切到字）"""
    inner = int(round(size * content_ratio))
    lg = logo(inner)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    off = (size - inner) // 2
    canvas.paste(lg, (off, off))
    return canvas


print("=" * 58)
print("  生成网页版 / PWA 图标（AGI 徽标，与 APK 同源）")
print("=" * 58)
print("  源: android/logo_agi.svg\n")

base = logo(RENDER)
base.save(os.path.join(ROOT, "icon-512.png"), "PNG")
print("  icon-512.png            512x512")

logo(192).save(os.path.join(ROOT, "icon-192.png"), "PNG")
print("  icon-192.png            192x192")

maskable(512).save(os.path.join(ROOT, "icon-512-maskable.png"), "PNG")
print("  icon-512-maskable.png   512x512 (内容 80% 安全区)")

logo(180).save(os.path.join(ROOT, "apple-touch-icon.png"), "PNG")
print("  apple-touch-icon.png    180x180 (iOS)")

# ---- favicon.svg：直接用同一个矢量文件（并在 <svg> 上补 width/height，
#      部分浏览器渲染 favicon 时需要）----
with open(SVG, "r", encoding="utf-8") as f:
    svg = f.read()

end = svg.index(">") + 1
tag = svg[:end]
if "width=" not in tag:
    svg = svg[:end - 1] + ' width="640" height="640"' + svg[end - 1:]
    print("  (已为 <svg> 补上 width/height)")

with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
print("  favicon.svg             矢量 (viewBox 0 0 640 640)")

# ---- 校验：AGI 徽标应含 黑/红/黄/蓝 四色 ----
px = base.convert("RGB").getcolors(maxcolors=1000000) or []
have = {c for _, c in px}
marks = {"黑": (0, 0, 0), "红": (0xB4, 0x05, 0x00),
         "黄": (0xFD, 0xC1, 0x01), "蓝": (0x21, 0x50, 0x65)}
hit = [k for k, v in marks.items()
       if any(abs(a - v[0]) < 12 and abs(b - v[1]) < 12 and abs(c - v[2]) < 12
              for a, b, c in have)]
print("\n  颜色校验: %s" % ("/".join(hit) if hit else "异常！未识别到 AGI 配色"))
print("=" * 58)
print("  完成。三端(网页/手机/电脑)图标现已统一为 AGI 徽标。")
print("=" * 58)

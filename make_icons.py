#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 PWA 图标（纯标准库实现 PNG 编码，无需 Pillow）
设计：紫色底 + 白色柱状图（象征项目管理数据看板）
输出：icon-192.png / icon-512.png / icon-512-maskable.png
maskable 版本：背景铺满整幅，内容缩到中心 80%（安全区），适配 Android 自适应图标裁剪
"""
import zlib, struct, os

BG = (107, 92, 231)      # 主题紫 #6b5ce7
FG = (255, 255, 255)     # 白

# 以 512x512 为设计基准：三根柱子 (x中心, 宽度, 顶端y, 底端y) + 一条底线
BARS = [(186, 66, 250, 372), (256, 66, 168, 372), (326, 66, 92, 372)]
BASE_Y0, BASE_Y1, BASE_X0, BASE_X1 = 372, 396, 140, 372


def write_png(path, size, pixel_fn):
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter type 0 (None)
        for x in range(size):
            r, g, b = pixel_fn(x, y)
            raw.append(r); raw.append(g); raw.append(b)
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', comp)
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def make_pixel_fn(size, maskable=False):
    scale = 0.8 if maskable else 1.0  # maskable 内容缩到中心 80%

    def pixel_fn(x, y):
        # 把实际坐标换算回 512 设计坐标
        if maskable:
            dx = (x - size / 2.0) / scale + 256.0
            dy = (y - size / 2.0) / scale + 256.0
        else:
            dx = x * 512.0 / size
            dy = y * 512.0 / size
        for bx, bw, top, bot in BARS:
            if abs(dx - bx) <= bw / 2.0 and top <= dy <= bot:
                return FG
        if BASE_Y0 <= dy <= BASE_Y1 and BASE_X0 <= dx <= BASE_X1:
            return FG
        return BG
    return pixel_fn


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    write_png(os.path.join(base, 'icon-192.png'), 192, make_pixel_fn(192, False))
    write_png(os.path.join(base, 'icon-512.png'), 512, make_pixel_fn(512, False))
    write_png(os.path.join(base, 'icon-512-maskable.png'), 512, make_pixel_fn(512, True))
    for n in ['icon-192.png', 'icon-512.png', 'icon-512-maskable.png']:
        p = os.path.join(base, n)
        print('%-26s %6d bytes' % (n, os.path.getsize(p)))


if __name__ == '__main__':
    main()

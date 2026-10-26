#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HOI4 DDS 图标工具 —— 生成 / 检查 HOI4 1.19.3 可读的 DDS 贴图。

用法（在知识库根目录或任意目录执行）：

    # 1) 从 PNG 生成 64x64 图标（默认：与原版 UI 图标一致的 32-bit 未压缩 DDS）
    python dds_helper.py make input.png out.dds --width 100 --height 88   # 国策图标

    # 2) 生成纯色占位图（画图标前的临时素材）
    python dds_helper.py solid out.dds --width 60 --height 68 --color "#3a6ea5" --alpha 255

    # 3) 生成 DXT5/BC3 压缩版（体积 1/4，游戏内支持，与原版字体图集同格式）
    python dds_helper.py make input.png out.dds --width 100 --height 88   # 国策图标 --format dxt5

    # 4) 检查一个 DDS 的头部信息（判断“黑块/花屏”的根因）
    python dds_helper.py check "E:/Steam/steamapps/common/Hearts of Iron IV/gfx/interface/observer_button.dds"

依赖：Pillow（本机 C:\\Users\\17876\\.dsh\\...\\python.exe 自带 Pillow 12.3）。

两种输出格式的取舍（详见 knowledge/05_presentation/gfx_sprites.md）：
  * raw32  —— 与原版 UI 图标字节布局一致：128 字节头 + width*height*4 字节 BGRA。
               flags=0x81007，pitch 字段写“总字节数”（原版写法），像素 32 位未压缩。
               优点：与原版完全同构，最不容易出问题；缺点：64x64 也要 16 KB。
  * dxt5   —— Pillow 的 BC3/DXT5 输出，fourCC='DXT5'，体积为未压缩的 1/4。
               原版字体图集(gfx/fonts/chinese/*.dds)就是 DXT5，因此引擎肯定能读。
Pillow 两种输出都不写 mipmap —— 原版 UI 图标同样没有 mipmap。
"""
from __future__ import annotations

import argparse
import struct
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    raise SystemExit("需要 Pillow：pip install pillow（本机 DSH 自带 Python 已含 Pillow）")

DDS_MAGIC = b"DDS "
# DDSD_CAPS|DDSD_HEIGHT|DDSD_WIDTH|DDSD_PIXELFORMAT|DDSD_PITCH|DDSD_LINEARSIZE
FLAGS_RAW32_VANILLA = 0x81007
FLAGS_RAW32_PIL = 0x100F
DDPF_ALPHAPIXELS = 0x1
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40
DDSCAPS_TEXTURE = 0x1000

FOURCC_NAMES = {
    b"DXT1": "BC1/DXT1 (无 alpha 或 1-bit alpha)",
    b"DXT3": "BC2/DXT3 (显式 4-bit alpha)",
    b"DXT5": "BC3/DXT5 (插值 alpha，UI 首选压缩格式)",
    b"ATI2": "BC5/ATI2 (两个通道，法线贴图用)",
    b"DX10": "DX10 扩展头（D3D11 风格，HOI4 不推荐）",
}


def _dds_header(width: int, height: int, *, dxt: str | None, vanilla_pitch: bool) -> bytes:
    """构造 128 字节 DDS 头。"""
    if dxt:
        fourcc = dxt.encode("ascii")  # b'DXT5' / b'DXT1' / b'DXT3'
        block = 16 if dxt in ("DXT3", "DXT5") else 8
        linear = max(1, (width + 3) // 4) * max(1, (height + 3) // 4) * block
        pf_flags = DDPF_FOURCC
        bits, rm, gm, bm, am = 0, 0, 0, 0, 0
        pitch_or_linear = linear
        flags = FLAGS_RAW32_VANILLA  # 0x81007：CPS|HEIGHT|WIDTH|PIXELFORMAT|PITCH|LINEARSIZE
    else:
        fourcc = b"\x00\x00\x00\x00"
        pf_flags = DDPF_RGB | DDPF_ALPHAPIXELS
        bits, rm, gm, bm, am = 32, 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000
        # 原版 UI 图标把该字段当“总字节数”用（64x64 -> 16384），
        # 标准 D3D9 把它当“每行字节数”用（64x64 -> 256）。两种解释都能被
        # 常见读取器接受；默认 output 与原版一致。
        pitch_or_linear = width * height * 4 if vanilla_pitch else width * 4
        flags = FLAGS_RAW32_VANILLA if vanilla_pitch else FLAGS_RAW32_PIL

    h = bytearray()
    h += DDS_MAGIC
    h += struct.pack("<I", 124)              # dwSize
    h += struct.pack("<I", flags)            # dwFlags
    h += struct.pack("<I", height)           # dwHeight
    h += struct.pack("<I", width)            # dwWidth
    h += struct.pack("<I", pitch_or_linear)  # dwPitchOrLinearSize
    h += struct.pack("<I", 0)                # dwDepth
    h += struct.pack("<I", 0)                # dwMipMapCount（0=无 mipmap）
    h += b"\x00" * 44                        # dwReserved1[11]
    h += struct.pack("<I", 32)               # ddspf.dwSize
    h += struct.pack("<I", pf_flags)         # ddspf.dwFlags
    h += fourcc                              # ddspf.dwFourCC
    h += struct.pack("<I", bits)             # ddspf.dwRGBBitCount
    h += struct.pack("<I", rm)
    h += struct.pack("<I", gm)
    h += struct.pack("<I", bm)
    h += struct.pack("<I", am)
    h += struct.pack("<I", DDSCAPS_TEXTURE)  # dwCaps
    h += struct.pack("<I", 0)                # dwCaps2
    h += struct.pack("<I", 0)                # dwCaps3
    h += struct.pack("<I", 0)                # dwCaps4
    h += struct.pack("<I", 0)                # dwReserved2
    assert len(h) == 128, len(h)
    return bytes(h)


def save_hoi4_dds(img: Image.Image, path: str, fmt: str = "raw32") -> None:
    """把 Pillow 图像按 HOI4 可读的 DDS 写出。

    fmt = raw32（默认，未压缩 BGRA，原版 UI 图标同构）
        | dxt5 | dxt1 | dxt3（Pillow 直接写压缩块，再改写头部字段）
    """
    img = img.convert("RGBA")
    w, h = img.size
    if fmt != "raw32" and (w % 4 or h % 4):
        raise SystemExit(f"尺寸 {w}x{h} 不是 4 的倍数，DXT 压缩会花屏；未压缩（raw32）不受此限制")

    if fmt == "raw32":
        # DDS 未压缩 32bpp 的内存排列是 BGRA（掩码 0x00ff0000/0x0000ff00/... 的
        # 小端解释），Pillow 没有 BGRA 编码器，用通道交换得到同样字节流。
        r, g, b, a = img.split()
        raw = Image.merge("RGBA", (b, g, r, a)).tobytes()
        with open(path, "wb") as f:
            f.write(_dds_header(w, h, dxt=None, vanilla_pitch=True))
            f.write(raw)
        return

    dxt = {"dxt1": "DXT1", "dxt3": "DXT3", "dxt5": "DXT5"}[fmt]
    tmp = path + ".pil.tmp.dds"
    img.save(tmp, format="DDS", pixel_format=dxt)
    with open(tmp, "rb") as f:
        body = f.read()[128:]  # 丢掉 Pillow 的头，只保留压缩数据
    with open(path, "wb") as f:
        f.write(_dds_header(w, h, dxt=dxt, vanilla_pitch=True))
        f.write(body)
    import os

    os.remove(tmp)


def check(path: str) -> int:
    with open(path, "rb") as f:
        head = f.read(148)
    if head[:4] != DDS_MAGIC:
        print(f"{path}\n  不是 DDS 文件（magic={head[:4]!r}）")
        return 1
    (size, flags, height, width, pitch, depth, mips) = struct.unpack("<7I", head[4:32])
    pf_size, pf_flags, fourcc, bits, rm, gm, bm, am = struct.unpack("<2I4s5I", head[76:108])
    caps = struct.unpack("<I", head[108:112])[0]
    expected = 128 + width * height * 4 if pf_flags & DDPF_RGB else None
    print(f"{path}")
    print(f"  {width}x{height}  mips={mips}  dwFlags=0x{flags:05x}  pitch/linear={pitch}")
    if pf_flags & DDPF_FOURCC:
        print(f"  压缩格式: {FOURCC_NAMES.get(fourcc, repr(fourcc))}")
    else:
        print(f"  未压缩: {bits}bpp  R=0x{rm:08x} G=0x{gm:08x} B=0x{bm:08x} A=0x{am:08x}")
    print(f"  caps=0x{caps:04x}  实际字节={__import__('os').path.getsize(path)}"
          + (f"  未压缩理论字节={expected}" if expected else ""))
    if width % 4 or height % 4:
        print("  ⚠️ 尺寸不是 4 的倍数：DXT 压缩会花屏（未压缩没问题）")
    if pf_flags & DDPF_FOURCC and fourcc == b"DX10":
        print("  ⚠️ DX10 扩展头：HOI4 不保证支持，请另存为 DXT5/未压缩")
    return 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="HOI4 DDS 图标生成/检查工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("make", help="PNG -> HOI4 DDS")
    m.add_argument("src")
    m.add_argument("dst")
    m.add_argument("--size", type=int, default=64)
    m.add_argument("--width", type=int, default=None)
    m.add_argument("--height", type=int, default=None)
    m.add_argument("--format", choices=["raw32", "dxt5", "dxt1", "dxt3"], default="raw32")
    m.add_argument("--no-resize", action="store_true", help="保持原尺寸（DXT 要求 4 的倍数；raw32 不要求）")

    s = sub.add_parser("solid", help="生成纯色占位 DDS")
    s.add_argument("dst")
    s.add_argument("--size", type=int, default=64)
    s.add_argument("--width", type=int, default=None)
    s.add_argument("--height", type=int, default=None)
    s.add_argument("--color", default="#3a6ea5")
    s.add_argument("--alpha", type=int, default=255)
    s.add_argument("--format", choices=["raw32", "dxt5", "dxt1", "dxt3"], default="raw32")

    c = sub.add_parser("check", help="打印 DDS 头部并给出常见问题提示")
    c.add_argument("src")

    a = ap.parse_args(argv)

    if a.cmd == "make":
        img = Image.open(a.src).convert("RGBA")
        if not a.no_resize:
            w = a.width or a.size
            h = a.height or a.size
            img = img.resize((w, h), Image.LANCZOS)
        save_hoi4_dds(img, a.dst, a.format)
        print(f"写出 {a.dst} ({img.size[0]}x{img.size[1]}, {a.format})")
        return check(a.dst)

    if a.cmd == "solid":
        r, g, b = (int(a.color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        w = a.width or a.size
        h = a.height or a.size
        img = Image.new("RGBA", (w, h), (r, g, b, a.alpha))
        save_hoi4_dds(img, a.dst, a.format)
        print(f"写出 {a.dst} ({w}x{h}, {a.format})")
        return check(a.dst)

    return check(a.src)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

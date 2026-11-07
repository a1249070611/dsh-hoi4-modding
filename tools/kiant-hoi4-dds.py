#!/usr/bin/env python3
"""DDS 探测与转换：读头部、算体积、判断能不能被 HOI4 接受。

为什么自己写而不依赖 Pillow：
  Pillow 写 DDS 只出未压缩 32bpp，读也只认有限几种；而实际需求是
  「看这个文件到底是什么格式、尺寸对不对、体积正常不正常」——这只需要头部。
  零依赖，python 自带 struct 就够。

用法：
    python tools/kiant-hoi4-dds.py info <file.dds> [file2.dds ...]     # 单个/多个详查
    python tools/kiant-hoi4-dds.py scan <dir>                          # 统计一个目录的格式分布
    python tools/kiant-hoi4-dds.py check <file.dds> --expect 64x64     # 校验尺寸
"""
from __future__ import annotations

import os
import struct
import sys
from collections import Counter

# DDS 头部固定 128 字节
DDS_MAGIC = b"DDS "
HEADER_SIZE = 128

DDPF_FOURCC = 0x4
DDPF_RGB = 0x40
DDPF_ALPHAPIXELS = 0x1


def parse_header(path: str) -> dict | None:
    """按 DDS_HEADER 结构解出关键字段。

    字段偏移（相对文件头）：
        0   magic "DDS "
        4   dwSize (124)
        8   dwFlags
        12  dwHeight
        16  dwWidth
        20  dwPitchOrLinearSize
        24  dwDepth
        28  dwMipMapCount
        76  DDS_PIXELFORMAT 开始（32 字节）
            76 dwSize / 80 dwFlags / 84 dwFourCC / 88 dwRGBBitCount
            92 dwRBitMask / 96 dwGBitMask / 100 dwBBitMask / 104 dwABitMask
        108 dwCaps
        112 dwCaps2
    """
    try:
        with open(path, "rb") as f:
            h = f.read(HEADER_SIZE)
    except OSError as e:
        return {"error": str(e)}
    if len(h) < HEADER_SIZE:
        return {"error": "文件小于 128 字节，不是合法 DDS"}
    if h[:4] != DDS_MAGIC:
        return {"error": f"magic 不对：{h[:4]!r}"}

    height, width = struct.unpack("<II", h[12:20])
    pitch = struct.unpack("<I", h[20:24])[0]
    depth = struct.unpack("<I", h[24:28])[0]
    mips = struct.unpack("<I", h[28:32])[0]
    pf_size, pf_flags, fourcc, rgbbits, rmask, gmask, bmask, amask = struct.unpack(
        "<II4sIIIII", h[76:108]
    )
    caps = struct.unpack("<I", h[108:112])[0]
    caps2 = struct.unpack("<I", h[112:116])[0]

    fc = fourcc.decode("latin1").rstrip("\0")
    if pf_flags & DDPF_FOURCC:
        fmt = fc or "(未知 FOURCC)"
    elif pf_flags & DDPF_RGB:
        fmt = f"未压缩 {rgbbits}bpp"
    else:
        fmt = "(未声明)"

    return {
        "path": path,
        "width": width,
        "height": height,
        "pitch": pitch,
        "depth": depth,
        "mips": mips or 1,
        "format": fmt,
        "fourcc": fc,
        "rgbbits": rgbbits,
        "masks": (rmask, gmask, bmask, amask),
        "has_alpha": bool(pf_flags & DDPF_ALPHAPIXELS),
        "file_size": os.path.getsize(path),
        "caps2": caps2,
    }


def _level_size(w: int, h: int, fmt: str) -> int:
    """单级 mip 的字节数。算不出返回 0。"""
    if "32bpp" in fmt:
        return w * h * 4
    if "24bpp" in fmt:
        return w * h * 3
    # 块压缩格式必须**向上**取整。原来写的是 w // 4，72 能整除看着没问题，
    # 但 21 // 4 = 5（实际要 6 个块，最后一行只覆盖 1 像素也得占满一块），
    # 于是 72x21 的 DXT5 被算成 1440 B、实际 1728 B，工具反而诬告文件「偏大」。
    # 一张图只要宽或高不是 4 的倍数就会踩到。
    if "DXT1" in fmt:
        return ((w + 3) // 4) * ((h + 3) // 4) * 8
    if fmt in ("DXT3", "DXT5", "RXGB"):
        return ((w + 3) // 4) * ((h + 3) // 4) * 16
    return 0  # DX10 要读扩展头才知道，不猜


def expected_size(info: dict) -> tuple[int, int]:
    """返回 (单级像素数据字节, 含全部 mipmap 的像素数据字节)。

    **不含 128 字节文件头**——调用方拿 file_size 比较时要自己减 header。
    原先这里把 header 加进了返回值，而 cmd_info 比较时又减了 header，
    两边口径不一致，导致 2 万个正常文件被报「偏大」。宁可返回值语义单一。

    算这个是为了抓「尺寸与体积对不上」的文件——多半是改图时截断或塞错。
    """
    fmt = info["format"]
    base = _level_size(info["width"], info["height"], fmt)
    if not base:
        return 0, 0
    total = base
    cw, ch = info["width"], info["height"]
    for _ in range(info["mips"] - 1):
        cw, ch = max(1, cw // 2), max(1, ch // 2)
        # 逐级按自己的尺寸重算，不要拿上一级除 4：宽高各自减半后
        # 块数不一定是上一级的一半（奇偶交替时会差一块），累加会漂。
        total += _level_size(cw, ch, fmt)
    return base, total


def cmd_info(files: list[str]) -> int:
    for p in files:
        info = parse_header(p)
        if not info or "error" in info:
            print(f"✗ {p}: {(info or {}).get('error', '读不出')}")
            continue
        base, with_mips = expected_size(info)
        actual = info["file_size"] - HEADER_SIZE
        verdict = ""
        if base:
            if actual < base * 0.9:
                verdict = f"  ⚠ 偏小（理论至少 {base} B，实际 {actual} B）"
            elif info["mips"] == 1 and actual > base * 1.1:
                verdict = f"  ⚠ 偏大（单级理论 {base} B，实际 {actual} B）"
        m = info["masks"]
        print(f"{os.path.basename(p)}")
        print(f"  {info['width']}x{info['height']}  {info['format']}  "
              f"mips={info['mips']}  文件 {info['file_size'] / 1024:.1f} KB{verdict}")
        print(f"  masks R={m[0]:#x} G={m[1]:#x} B={m[2]:#x} A={m[3]:#x}  alpha={'有' if info['has_alpha'] else '无'}")
    return 0


def cmd_scan(root: str) -> int:
    fmt_counter: Counter[str] = Counter()
    size_counter: Counter[str] = Counter()
    odd = []
    n = 0
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if not f.lower().endswith(".dds"):
                continue
            p = os.path.join(dp, f)
            info = parse_header(p)
            if not info or "error" in info:
                odd.append((p, (info or {}).get("error", "?")))
                continue
            n += 1
            fmt_counter[info["format"]] += 1
            size_counter[f"{info['width']}x{info['height']}"] += 1
    print(f"扫描 {root}：{n} 个 DDS" + (f"，{len(odd)} 个读不出" if odd else ""))
    print("\n格式分布：")
    for k, v in fmt_counter.most_common():
        print(f"  {k:20} {v:6}  {v * 100 // max(n, 1)}%")
    print("\n尺寸 Top 10：")
    for k, v in size_counter.most_common(10):
        print(f"  {k:14} {v:5}")
    for p, e in odd[:5]:
        print(f"  ✗ {p}: {e}")
    return 0


def cmd_check(path: str, expect: str) -> int:
    info = parse_header(path)
    if not info or "error" in info:
        print(f"✗ 读不出：{(info or {}).get('error')}")
        return 1
    want = expect.lower().split("x")
    if len(want) != 2:
        print("--expect 格式应为 宽x高，例如 64x64")
        return 1
    ew, eh = int(want[0]), int(want[1])
    ok = info["width"] == ew and info["height"] == eh
    print(f"{path}")
    print(f"  实际 {info['width']}x{info['height']}  期望 {ew}x{eh}  → {'✓ 一致' if ok else '✗ 不一致'}")
    if not ok:
        print(f"  提示：改图时尺寸不符会导致拉伸或裁切，细节见 05_presentation/icon-specs.md")
    return 0 if ok else 2


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "info" and len(argv) > 1:
        return cmd_info(argv[1:])
    if cmd == "scan" and len(argv) > 1:
        return cmd_scan(argv[1])
    if cmd == "check" and len(argv) > 1:
        expect = ""
        if "--expect" in argv:
            i = argv.index("--expect")
            expect = argv[i + 1] if i + 1 < len(argv) else ""
        if not expect:
            print("check 需要 --expect 宽x高")
            return 1
        return cmd_check(argv[1], expect)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

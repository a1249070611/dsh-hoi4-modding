#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科技卡图标导入：照片/矢量图 → 173×77 DDS（去背 + 安全区 + 卡片预览）。

针对 HOI4 科技卡的几何：卡 183×84、Icon 控件中心 x=74 → 图标内容需左留 20、右留 4（默认）。
支持透明 PNG（最佳）、白底、8px 棋盘格（白 + 灰）三种常见输入。

用法:
  # 单张（透明 PNG 或白底照片）
  python tech_icon_import.py "虎式E型.png" out/GER_tiger_e.dds

  # 批量目录 + 别名表
  python tech_icon_import.py ./矢量图 out/ --alias alias.json --card-preview preview.png

  # 自定义尺寸（例如装备 2D 图标 89×38 时）
  python tech_icon_import.py in.png out.dds --width 89 --height 38 --margin-left 4 --margin-right 4

依赖：Pillow；DDS 写出调用同目录 dds_helper.py（raw32）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:  # pragma: no cover
    raise SystemExit("需要 Pillow：pip install pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _paths import find_game_dir
except Exception:  # pragma: no cover
    def find_game_dir():
        return None

DDS_HELPER = Path(__file__).resolve().parent / "dds_helper.py"


# ---------------------------------------------------------------- 去背
def border_pixels(im: Image.Image):
    w, h = im.size
    px = im.load()
    for x in range(w):
        yield px[x, 0]
        yield px[x, h - 1]
    for y in range(h):
        yield px[0, y]
        yield px[w - 1, y]


def bg_like(r: int, g: int, b: int, mode: str) -> bool:
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn > 14:          # 有明显颜色 → 不是背景
        return False
    v = (r + g + b) // 3
    if mode == "white":
        return v >= 235
    if mode == "checker":     # 棋盘格：白 + 灰（130/192）
        return v >= 235 or 110 <= v <= 210
    return v >= 235


def detect_mode(im: Image.Image) -> str:
    """auto：有透明通道用 alpha；否则看边框颜色判断白底/棋盘格。"""
    if im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 250:
        return "alpha"
    counts = {"white": 0, "checker": 0, "other": 0}
    for r, g, b, _a in border_pixels(im):
        mx, mn = max(r, g, b), min(r, g, b)
        v = (r + g + b) // 3
        if mx - mn <= 14 and v >= 235:
            counts["white"] += 1
        elif mx - mn <= 14 and 110 <= v <= 210:
            counts["checker"] += 1
        else:
            counts["other"] += 1
    if counts["white"] >= counts["other"] * 3:
        return "white"
    return "checker"


def remove_background(im: Image.Image, mode: str):
    """返回 (前景 alpha mask L, 背景已透明的 RGBA)。"""
    im = im.convert("RGBA")
    if mode == "alpha":
        return im.getchannel("A"), im

    # 1) 背景候选 mask：bg-like=255
    w, h = im.size
    px = im.load()
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if bg_like(r, g, b, mode):
                mp[x, y] = 255

    # 2) 从边界 flood fill（128 = 已确认背景）
    draw = ImageDraw.Draw(mask)
    seeds = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
            [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    for s in seeds:
        if mp[s] == 255:
            draw.floodfill(mask, s, 128, thresh=0)

    # 3) 生成前景 alpha：背景=0，其余=255；内部洞按“白涂装保护”规则处理
    fg = Image.new("L", (w, h), 0)
    fp = fg.load()
    holes = 0
    for y in range(h):
        for x in range(w):
            v = mp[x, y]
            if v == 128:
                continue
            if v == 255:  # 内部洞（被前景包围的背景色）
                r, g, b, _a = px[x, y]
                rel_y = y / max(1, h - 1)
                if (r + g + b) / 3 >= 235 and rel_y < 0.8:
                    fp[x, y] = 255          # 白色涂装/编号：保留
                else:
                    holes += 1              # 其余洞留透明（履带缝等）
                continue
            fp[x, y] = 255

    # 4) 腐蚀 1px 去白边
    fg = fg.filter(ImageFilter.MinFilter(3))
    rgba = im.copy()
    rgba.putalpha(fg)
    return fg, rgba


# ---------------------------------------------------------------- 安全区缩放
def resize_rgba(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    """RGB 与 alpha 分别 LANCZOS 缩放（Pillow 无预乘，照片缩放边缘可能有轻微灰边）。"""
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b)).resize(size, Image.LANCZOS)
    a2 = a.resize(size, Image.LANCZOS)
    return Image.merge("RGBA", (*rgb.split(), a2))


def place_with_margins(im: Image.Image, out_w: int, out_h: int,
                       margin_left: int, margin_right: int, margin_y: int) -> Image.Image:
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        return Image.new("RGBA", (out_w, out_h))
    im = im.crop(bbox)
    avail_w = max(1, out_w - margin_left - margin_right)
    avail_h = max(1, out_h - 2 * margin_y)
    scale = min(avail_w / im.width, avail_h / im.height)
    new = max(1, int(round(im.width * scale))), max(1, int(round(im.height * scale)))
    im = resize_rgba(im, new)
    canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    x = margin_left + (avail_w - new[0]) // 2
    y = margin_y + (avail_h - new[1]) // 2
    canvas.alpha_composite(im, (x, y))
    return canvas


# ---------------------------------------------------------------- 卡片预览
def card_preview(icon: Image.Image, out: Path, game: Path | None, card_bg: str | None = None):
    bg = None
    if card_bg:
        bg = Path(card_bg)
    elif game:
        c = game / "gfx/interface/techtree/technology_available_item_bg.dds"
        if c.exists():
            bg = c
    if not bg or not bg.exists():
        print("[!] 找不到卡片背景，跳过 --card-preview")
        return
    card = Image.open(bg).convert("RGBA").resize((183, 84), Image.LANCZOS)
    card.alpha_composite(icon, (74 - icon.width // 2, 50 - icon.height // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    card.save(out)
    print("[preview]", out)


# ---------------------------------------------------------------- 主流程
def convert_one(src: Path, dst: Path, args, game) -> bool:
    try:
        im = Image.open(src).convert("RGBA")
    except Exception as e:
        print(f"[!] 读图失败 {src}: {e}")
        return False
    mode = args.mode
    if mode == "auto":
        mode = detect_mode(im)
    if mode == "none":
        alpha = im.getchannel("A")
        rgba = im
    else:
        alpha, rgba = remove_background(im, mode)
    icon = place_with_margins(rgba, args.width, args.height,
                              args.margin_left, args.margin_right, args.margin_y)
    png = dst.with_suffix(".png")
    dst.parent.mkdir(parents=True, exist_ok=True)
    icon.save(png)
    env = None
    r = subprocess.run([sys.executable, str(DDS_HELPER), "make", str(png), str(dst),
                        "--width", str(args.width), "--height", str(args.height)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if r.returncode != 0:
        print(f"[!] DDS 生成失败 {dst}: {(r.stderr or r.stdout or '').strip()[:200]}")
        return False
    if args.card_preview:
        card_preview(icon, Path(args.card_preview), game, args.card_bg)
    bbox = icon.getchannel("A").getbbox() or (0, 0, 0, 0)
    print(f"[ok] {src.name} -> {dst.name}  mode={mode}  bbox={bbox}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="科技卡图标导入（照片/矢量 → 173×77 DDS）")
    ap.add_argument("input", help="图片文件或目录")
    ap.add_argument("output", help="输出 .dds 路径；输入为目录时为输出目录")
    ap.add_argument("--mode", default="auto", choices=["auto", "alpha", "white", "checker", "none"])
    ap.add_argument("--width", type=int, default=173)
    ap.add_argument("--height", type=int, default=77)
    ap.add_argument("--margin-left", type=int, default=20)
    ap.add_argument("--margin-right", type=int, default=4)
    ap.add_argument("--margin-y", type=int, default=2)
    ap.add_argument("--card-preview", default=None, help="输出一张 183×84 合成卡预览 PNG")
    ap.add_argument("--card-bg", default=None, help="卡片背景 DDS（默认从游戏目录找）")
    ap.add_argument("--alias", default=None, help="JSON：文件名 stem / 中文名 → 科技 id")
    ap.add_argument("--game", default=None)
    args = ap.parse_args()

    game = Path(args.game) if args.game else find_game_dir()
    src = Path(args.input)
    dst = Path(args.output)
    aliases = {}
    if args.alias:
        aliases = json.loads(Path(args.alias).read_text(encoding="utf-8"))

    if src.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        files = [p for p in sorted(src.rglob("*")) if p.suffix.lower() in exts]
        if not files:
            print("[!] 目录里没有图片")
            return 1
        ok = 0
        for f in files:
            name = aliases.get(f.stem, aliases.get(f.name, f.stem))
            out = dst / f"{name}.dds"
            if convert_one(f, out, args, game):
                ok += 1
        print(f"[done] {ok}/{len(files)}")
        return 0 if ok else 1

    if src.is_file():
        name = aliases.get(src.stem, aliases.get(src.name, dst.stem))
        if dst.suffix.lower() != ".dds":
            dst = dst / f"{name}.dds"
        return 0 if convert_one(src, dst, args, game) else 1

    print("[!] 输入不存在:", src)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

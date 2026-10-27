#!/usr/bin/env python3
"""检查 item 模板尺寸与 item 背景精灵贴图的实际像素是否匹配。

这是"小框科技却显示成大框"的专用体检：item 模板的 size 只决定排版，
背景贴图按自身像素尺寸绘制；`..._small_<state>_item_bg` 若仍指向 203x84 的大图，
画面上就是"小框模板 + 大框外观 + 整体偏位"。

用法：
    python item_sprite_check.py "<Mod目录>"
    python item_sprite_check.py "<Mod目录>" --folder trm_armour_ger_folder --folder infantry_folder
    python item_sprite_check.py "<Mod目录>" --json sprites.json

依赖：Pillow 可选（没有则只检查定义与文件是否存在，不做像素比对）。
只读，不修改文件。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdx_parser as pdx  # noqa: E402
import _paths  # noqa: E402

GUI_REL = Path("interface/countrytechtreeview.gui")
STATES = ("unavailable", "available", "researched", "currently_researching")
SIZE_TOLERANCE = 32  # 像素容差：模板宽与贴图宽差超过它就算可疑


def scalar_of(blk, *names: str) -> str | None:
    wanted = {n.lower() for n in names}
    for entry in blk.pairs():
        if entry.key.lower() in wanted:
            v = entry.scalar
            if v is not None:
                return v
    return None


def block_of(blk, *names: str):
    wanted = {n.lower() for n in names}
    for entry in blk.pairs():
        if entry.key.lower() in wanted:
            b = entry.block
            if b is not None:
                return b
    return None


def parse_gui(mod: Path):
    """返回 {模板名: {"size": (w,h), "position": (x,y)}}"""
    out = {}
    gui = mod / GUI_REL
    if not gui.is_file():
        return out
    block, _ = pdx.parse_file(str(gui))
    for entry in block.walk():
        blk = entry.block
        if blk is None or entry.key != "containerWindowType":
            continue
        name = scalar_of(blk, "name")
        if not name or not name.startswith("techtree_") or not name.endswith("_item"):
            continue
        size = block_of(blk, "size")
        pos = block_of(blk, "position")
        wh = None
        if size:
            w = scalar_of(size, "width")
            h = scalar_of(size, "height")
            if w and h:
                wh = (int(float(w.rstrip("%"))), int(float(h.rstrip("%"))))
        xy = None
        if pos:
            x = scalar_of(pos, "x")
            y = scalar_of(pos, "y")
            if x and y:
                xy = (int(float(x)), int(float(y)))
        out[name] = {"size": wh, "position": xy}
    return out


def parse_sprites(mod: Path):
    """返回 {sprite 名: {"texture": 相对路径, "frames": int|None}}"""
    out = {}
    for gfx in sorted((mod / "interface").rglob("*.gfx")):
        try:
            block, _ = pdx.parse_file(str(gfx))
        except Exception:
            continue
        for entry in block.walk():
            blk = entry.block
            if blk is None or entry.key.lower() not in ("spritetype", "frameanimatedspritetype"):
                continue
            name = scalar_of(blk, "name")
            tex = scalar_of(blk, "texturefile")
            if not name or not tex:
                continue
            frames = scalar_of(blk, "noOfFrames")
            out[name] = {"texture": tex.replace("\\", "/"), "frames": int(frames) if frames else None}
    return out


def texture_size(mod: Path, game: Path | None, rel: str):
    """读贴图实际像素；Pillow 不可用或读不了时返回 None。"""
    for base in (mod, game):
        if base is None:
            continue
        p = base / rel
        if not p.is_file():
            continue
        try:
            from PIL import Image  # 可选依赖
        except Exception:
            return None
        try:
            with Image.open(p) as im:
                return im.size
        except Exception:
            return None
    return None


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="item 模板尺寸 vs 背景精灵像素（只读）")
    ap.add_argument("mod", help="Mod 根目录")
    ap.add_argument("--folder", action="append", default=None,
                    help="只检查这些 folder（默认：所有同时有 _item 与 _small_item 的）")
    ap.add_argument("--json", help="把结果写成 JSON")
    args = ap.parse_args(argv)

    mod = Path(args.mod).expanduser()
    if not mod.is_dir():
        print(f"目录不存在：{mod}")
        return 2
    game = _paths.find_game_dir()

    gui = parse_gui(mod)
    sprites = parse_sprites(mod)

    folders = set()
    for name in gui:
        m = re.match(r"^techtree_(.+)_(small_item|item)$", name)
        if m:
            folders.add(m.group(1))
    if args.folder:
        folders = set(args.folder)

    try:
        from PIL import Image  # noqa: F401
        have_pillow = True
    except Exception:
        have_pillow = False

    print(f"Mod：{mod}")
    print(f"游戏目录：{game or '未探测到（跳过原版贴图解析）'}")
    print(f"Pillow：{'可用' if have_pillow else '不可用（只做定义/存在性检查）'}")
    print()

    rows = []
    problems = 0
    for folder in sorted(folders):
        big = gui.get(f"techtree_{folder}_item")
        small = gui.get(f"techtree_{folder}_small_item")
        if big is None and small is None:
            continue
        print(f"=== {folder}")
        for label, tmpl in (("item", big), ("small_item", small)):
            if tmpl is None:
                print(f"  {label:10s} (模板未定义)")
                continue
            size = tmpl.get("size")
            print(f"  {label:10s} 模板 size={size} position={tmpl.get('position')}")
            prefix = f"GFX_technology_{folder}_" + ("small_" if label == "small_item" else "")
            for st in STATES:
                sname = f"{prefix}{st}_item_bg"
                sp = sprites.get(sname)
                if sp is None:
                    print(f"    {st:20s} 精灵未定义：{sname}")
                    rows.append(dict(folder=folder, template=label, state=st, sprite=sname,
                                     template_size=size, texture=None, texture_size=None,
                                     status="sprite-missing"))
                    # 普通 item 缺 folder 级精灵 = 正常回退到通用大图；
                    # small_item 缺精灵 = 会回退到大图 → 小框显示成大框，是真问题
                    if label == "small_item":
                        problems += 1
                        print(f"    !! 小框精灵缺失，会回退到通用大图 → 看起来仍是大框：{sname}")
                    continue
                rel = sp["texture"]
                px = texture_size(mod, game, rel)
                frames = sp["frames"] or 1
                frame_px = (px[0] // frames, px[1]) if px and frames else px
                status = "ok"
                detail = ""
                if px is None:
                    status = "texture-unreadable"
                    detail = rel + ("（文件不存在或无法解析）" if not have_pillow else "")
                else:
                    tw = size[0] if size else None
                    fw = frame_px[0]
                    if tw and abs(fw - tw) > SIZE_TOLERANCE:
                        status = "size-mismatch"
                        problems += 1
                        detail = f"贴图单帧 {fw}x{frame_px[1]} vs 模板宽 {tw}"
                    elif label == "small_item" and size and size[0] > 100:
                        status = "small-template-too-big"
                        problems += 1
                        detail = f"small_item 模板宽 {size[0]} 偏大（通常应为 72 左右）"
                print(f"    {st:20s} {rel:60s} 像素={px} 帧数={frames if sp['frames'] else '-'} {status} {detail}")
                rows.append(dict(folder=folder, template=label, state=st, sprite=sname,
                                 template_size=size, texture=rel, texture_size=px,
                                 frames=frames, status=status))
        print()

    print(f"可疑项：{problems}")
    if problems:
        print("提示：size-mismatch 就是『小框模板 + 大图背景』的典型症状，")
        print("      把小框精灵的 textureFile 换成 72x72 的小图（如 tech_doctrine_*_item_bg.dds）。")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print("JSON →", args.json)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

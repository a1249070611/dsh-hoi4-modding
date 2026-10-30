#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""坦克设计器体检：窗口/槽位/模块/底盘槽数/背景贴图（HOI4 1.19.x）。

只读诊断，不改任何文件。排错第一步：先跑这个，确认“界面有几个槽位位置、每个底盘有几个槽、
槽位按钮多大、窗口背景多高”。

用法:
  python tank_designer_probe.py
  python tank_designer_probe.py --game "E:/Steam/steamapps/common/Hearts of Iron IV"
  python tank_designer_probe.py --mod "C:/.../my_mod"
"""
from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _paths import find_game_dir
except Exception:  # pragma: no cover
    def find_game_dir():
        return None


# ---------------------------------------------------------------- PDX 小工具
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def depth_map(text: str) -> list[int]:
    """每个字符位置所处的花括号深度（跳过注释与字符串）。"""
    depths: list[int] = []
    d = 0
    in_str = False
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if not in_str and c == "#":
            while i < n and text[i] != "\n":
                depths.append(d)
                i += 1
            continue
        if c == '"':
            in_str = not in_str
            depths.append(d)
            i += 1
            continue
        depths.append(d)
        if not in_str:
            if c == "{":
                d += 1
            elif c == "}":
                d -= 1
        i += 1
    return depths


BLOCK_START = re.compile(r"(?m)^[ \t]*([A-Za-z0-9_@.\-]+)\s*=\s*\{")


def blocks_at(text: str, depths: list[int], target: int):
    """产出 (name, start, open_idx, close_idx, body)：深度 == target 的块。"""
    out = []
    for m in BLOCK_START.finditer(text):
        if depths[m.start()] != target:
            continue
        open_idx = m.end() - 1
        d = depths[open_idx]
        j = open_idx
        close_idx = len(text) - 1
        while j < len(text):
            if text[j] == "}" and depths[j] == d:
                close_idx = j
                break
            j += 1
        body = text[open_idx + 1:close_idx]
        out.append((m.group(1), m.start(), open_idx, close_idx, body))
    return out


def child_blocks(body: str):
    """body 内第一层 name = { ... } 子块（返回 (name, body)）。"""
    d = depth_map(body)
    return [(n, b) for (n, _s, _o, _c, b) in blocks_at(body, d, 0)]


def attr_after(text: str, name: str, attr: str, span: int = 3000):
    i = text.find(f'name = "{name}"')
    if i < 0:
        i = text.find(f'name="{name}"')
    if i < 0:
        return None
    m = re.search(attr + r"\s*=\s*\{([^}]*)\}", text[i:i + span])
    return m.group(1) if m else None


def width_height(snippet: str | None):
    if not snippet:
        return None
    w = re.search(r"width\s*=\s*(\d+)", snippet)
    h = re.search(r"height\s*=\s*(\d+)", snippet)
    return (int(w.group(1)), int(h.group(1))) if (w and h) else None


# ---------------------------------------------------------------- DDS / GFX
def dds_size(path: Path):
    try:
        with open(path, "rb") as f:
            head = f.read(128)
        if head[:4] != b"DDS ":
            return None
        height = struct.unpack("<I", head[12:16])[0]
        width = struct.unpack("<I", head[16:20])[0]
        return width, height
    except Exception:
        return None


def gfx_sprite_texture(game: Path, sprite_name: str):
    for f in (game / "interface").glob("**/*.gfx"):
        try:
            t = read(f)
        except Exception:
            continue
        m = re.search(r'name\s*=\s*"' + re.escape(sprite_name) + r'"(.{0,600}?)texturefile\s*=\s*"([^"]+)"',
                      t, re.S)
        if m:
            return game / m.group(2)
    return None


# ---------------------------------------------------------------- 报告
def main() -> int:
    ap = argparse.ArgumentParser(description="坦克设计器体检（只读）")
    ap.add_argument("--game", default=None)
    ap.add_argument("--mod", default=None)
    args = ap.parse_args()

    game = Path(args.game) if args.game else find_game_dir()
    if not game or not (game / "interface" / "tank_designer_view.gui").exists():
        print("[!] 找不到游戏目录，请用 --game 指定 Hearts of Iron IV 根目录")
        return 2

    tv = game / "interface" / "tank_designer_view.gui"
    ed = game / "interface" / "equipmentdesignerview.gui"
    text = read(tv)

    print("=" * 72)
    print("坦克设计器体检 @", game)
    print("=" * 72)

    win = width_height(attr_after(text, "tank_designer_view", "size"))
    print(f"[窗口] tank_designer_view size = {win}")

    mod_pos = attr_after(text, "equipment_modules", "position")
    mod_size = width_height(attr_after(text, "equipment_modules", "size"))
    print(f"[容器] equipment_modules pos={mod_pos.strip() if mod_pos else None} size={mod_size}")
    bp_pos = attr_after(text, "equipment_preview", "position")
    bp_size = width_height(attr_after(text, "equipment_preview", "size"))
    print(f"[蓝图] equipment_preview pos={bp_pos.strip() if bp_pos else None} size={bp_size}")

    print("[槽位位置]")
    macros = dict(re.findall(r"@([A-Za-z0-9_]+)\s*=\s*(-?\d+)", text))
    for m in re.finditer(r'name\s*=\s*"(pos_custom_module_slot_window_\d+)"', text):
        name = m.group(1)
        pm = re.search(r"position\s*=\s*\{([^}]*)\}", text[m.start():m.start() + 300])
        if not pm:
            continue
        raw = pm.group(1)
        for k, v in macros.items():
            raw = raw.replace("@" + k, v)
        nums = re.findall(r"-?\d+", raw)
        if len(nums) >= 2:
            print(f"  {name:36s} x={int(nums[0]):4d} y={int(nums[1]):4d}")

    if ed.exists():
        m = re.search(r'name\s*=\s*"equipment_designer_module_slot_entry"(.{0,300}?)size\s*=\s*\{([^}]*)\}',
                      read(ed), re.S)
        if m:
            print(f"[模板] equipment_designer_module_slot_entry size={width_height(m.group(2))}")

    bgm = re.search(r'background\s*=\s*\{[^}]*?spriteType\s*=\s*"([^"]+)"', text, re.S)
    if bgm:
        sprite = bgm.group(1)
        tex = gfx_sprite_texture(game, sprite)
        if tex and tex.exists():
            size = dds_size(tex)
            print(f"[背景] {sprite} -> {tex.name} {size}")
            if win and size and size[0] < win[0]:
                print("  [!] 背景宽度 < 窗口宽度")
            if win and size and size[1] < win[1]:
                print("  [!] 背景高度 < 窗口高度：内容会溢出窗口（见 references/tank-designer.md §4.3）")

    hidden = []
    for m in re.finditer(r'name\s*=\s*"([a-z_0-9]+)"\s*\n\s*position\s*=\s*\{\s*x\s*=\s*(-4000|-5000)', text):
        hidden.append(m.group(1))
    if hidden:
        print(f"[隐藏] {len(hidden)} 个元素被移出屏幕：{', '.join(hidden[:12])}"
              + (" ..." if len(hidden) > 12 else ""))

    # ---- 模块（游戏 + mod 覆盖）
    mod_dirs = []
    if args.mod:
        mod_dirs.append(Path(args.mod) / "common" / "units" / "equipment" / "modules")
    mod_dirs.append(game / "common" / "units" / "equipment" / "modules")
    cats: dict[str, int] = {}
    module_count = 0
    module_ids: set[str] = set()
    for d in mod_dirs:
        if not d.exists():
            continue
        for f in d.glob("*.txt"):
            t = read(f)
            dm = depth_map(t)
            for name, _s, _o, _c, body in blocks_at(t, dm, 0):
                if name != "equipment_modules":
                    continue
                for mod_id, mod_body in child_blocks(body):
                    if mod_id in ("limit",):
                        continue
                    module_count += 1
                    module_ids.add(mod_id)
                    cm = re.search(r"category\s*=\s*([A-Za-z0-9_]+)", mod_body)
                    if cm:
                        cats[cm.group(1)] = cats.get(cm.group(1), 0) + 1
    print(f"[模块] {len(module_ids)} 个模块（含重复 id），{len(cats)} 个类别")
    for c in sorted(cats):
        print(f"  {c:34s} {cats[c]:3d} 个模块")

    # ---- 底盘槽数
    chassis_files = []
    if args.mod:
        mp = Path(args.mod) / "common" / "units" / "equipment" / "tank_chassis.txt"
        if mp.exists():
            chassis_files.append(("mod", mp))
    gp = game / "common" / "units" / "equipment" / "tank_chassis.txt"
    if gp.exists():
        chassis_files.append(("game", gp))
    for label, cf in chassis_files:
        t = read(cf)
        dm = depth_map(t)
        rows = []
        for name, _s, _o, _c, body in blocks_at(t, dm, 1) + blocks_at(t, dm, 0):
            if "is_archetype = yes" not in body:
                continue
            ms = re.search(r"module_slots\s*=\s*\{", body)
            if not ms:
                rows.append((name, 0, []))
                continue
            i = body.find("{", ms.start())
            d = 0
            j = i
            while j < len(body):
                if body[j] == "{":
                    d += 1
                elif body[j] == "}":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            slots = [n for n, _b in child_blocks(body[i + 1:j])]
            rows.append((name, len(slots), slots))
        if rows:
            print(f"[底盘-{label}] archetype 槽位：")
            for name, n, slots in rows:
                print(f"  {name:32s} {n:2d} 槽" + (f": {', '.join(slots)}" if slots else ""))

    print("-" * 72)
    npos = len(re.findall(r'name\s*=\s*"pos_custom_module_slot_window_\d+"', text))
    print(f"[结论] 设计器槽位位置数 = {npos}；槽位按钮数量由底盘 module_slots 决定，第 N 个槽 → 第 N 个位置。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

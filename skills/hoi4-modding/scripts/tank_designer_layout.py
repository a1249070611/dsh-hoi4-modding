#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成自定义槽位布局的 tank_designer_view.gui（坦克设计器）。

从原版 GUI 复制并改写，不修改游戏目录；输出到 mod 的 interface/ 下。
默认预设 = 16 槽紧凑布局（窗口高度不变 542）：
  上排 7 槽（y=0） + 第二排 2 槽（通信/工程，y=50，蓝图两角） + 下排 7 槽（y=300）

用法:
  python tank_designer_layout.py --mod "C:/.../my_mod"                 # 写入 mod/interface/tank_designer_view.gui
  python tank_designer_layout.py --out ./tmp.gui --dry-run             # 只看将生成什么
  python tank_designer_layout.py --mod ... --preset 16-tall --background-sprite GFX_NS_bg
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from _paths import find_game_dir
except Exception:  # pragma: no cover
    def find_game_dir():
        return None

POS_PAT = re.compile(r'position\s*=\s*\{\s*x\s*=\s*(-?\d+)\s*y\s*=\s*(-?\d+)\s*\}')

SLOT_W = 76          # equipment_designer_module_slot_entry 的实际宽度
BOTTOM_ELEMENTS = [
    "reset_button", "duplicate_button", "save_button", "experience_bg", "experience",
    "resources_bg", "production_resources", "refit_cost", "production_value",
]

PRESETS = {
    "16-compact": dict(
        window_h=542,
        modules_size=(512, 350),
        preview=(3, 50),
        rows=(0, 50, 300),
        note="16 槽紧凑版：不加高窗口，第二排两个槽压在蓝图顶部左右角",
    ),
    "16-tall": dict(
        window_h=760,
        modules_size=(512, 570),
        preview=(2, 182),
        rows=(22, 100, 486),
        note="16 槽加高版：需要自己提供加高后的窗口背景 sprite（否则内容溢出）",
    ),
}


def read(p: Path) -> str:
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def hide(text: str, name: str) -> str:
    start = text.find(f'name = "{name}"')
    if start < 0:
        start = text.find(f'name="{name}"')
    if start < 0:
        print(f"[!] 元素不存在，跳过：{name}")
        return text
    m = POS_PAT.search(text, start)
    if not m:
        print(f"[!] 找不到 position，跳过：{name}")
        return text
    return text[:m.start()] + "position = { x = -4000 y = -4000 }" + text[m.end():]


def shift(text: str, name: str, dy: int) -> str:
    if dy == 0:
        return text
    start = text.find(f'name = "{name}"')
    if start < 0:
        start = text.find(f'name="{name}"')
    if start < 0:
        print(f"[!] 元素不存在，跳过：{name}")
        return text
    m = POS_PAT.search(text, start)
    if not m:
        print(f"[!] 找不到 position，跳过：{name}")
        return text
    x, y = int(m.group(1)), int(m.group(2))
    if x <= -1000:
        return text  # 已隐藏
    return text[:m.start()] + f"position = {{ x = {x} y = {y + dy} }}" + text[m.end():]


def build_slot_section(rows: tuple[int, int, int]) -> str:
    r0, r1, r2 = rows
    lines = ["\t\t\t@fixed_btn_mod_col_0 = 0"]
    for i in range(1, 7):
        lines.append(f"\t\t\t@fixed_btn_mod_col_{i} = {72 * i}")
    lines += [
        "",
        f"\t\t\t@fixed_btn_mod_row_0 = {r0}",
        f"\t\t\t@fixed_btn_mod_row_1 = {r1}",
        f"\t\t\t@fixed_btn_mod_row_2 = {r2}",
        "",
        "\t\t\tpositionType = {",
        '\t\t\t\tname = "ypos_module_row_0"',
        "\t\t\t\tposition = { x=0 y=@fixed_btn_mod_row_0 }",
        "\t\t\t}",
        "",
        "\t\t\t# 上排 7 槽（0-6）",
    ]
    for i in range(7):
        lines += [
            "\t\t\tpositionType = {",
            f'\t\t\t\tname = "pos_custom_module_slot_window_{i}"',
            f"\t\t\t\tposition = {{ x=@fixed_btn_mod_col_{i} y=@fixed_btn_mod_row_0 }}",
            "\t\t\t}",
        ]
    lines += [
        "",
        "\t\t\t# 第二排 2 槽（7=通信/左角，8=工程/右角）",
        "\t\t\tpositionType = {",
        '\t\t\t\tname = "pos_custom_module_slot_window_7"',
        "\t\t\t\tposition = { x=@fixed_btn_mod_col_0 y=@fixed_btn_mod_row_1 }",
        "\t\t\t}",
        "\t\t\tpositionType = {",
        '\t\t\t\tname = "pos_custom_module_slot_window_8"',
        "\t\t\t\tposition = { x=@fixed_btn_mod_col_6 y=@fixed_btn_mod_row_1 }",
        "\t\t\t}",
        "",
        "\t\t\t# 下排 7 槽（9-15）",
    ]
    for i in range(7):
        lines += [
            "\t\t\tpositionType = {",
            f'\t\t\t\tname = "pos_custom_module_slot_window_{9 + i}"',
            f"\t\t\t\tposition = {{ x=@fixed_btn_mod_col_{i} y=@fixed_btn_mod_row_2 }}",
            "\t\t\t}",
        ]
    return "\n".join(lines) + "\n\n\t\t\t######################################################################\n\t\t\t"


def main() -> int:
    ap = argparse.ArgumentParser(description="生成自定义坦克设计器布局（不修改游戏目录）")
    ap.add_argument("--game", default=None)
    ap.add_argument("--mod", default=None, help="mod 根目录（输出到 interface/tank_designer_view.gui）")
    ap.add_argument("--out", default=None, help="直接指定输出 gui 路径")
    ap.add_argument("--preset", default="16-compact", choices=sorted(PRESETS))
    ap.add_argument("--height", type=int, default=None, help="覆盖窗口高度")
    ap.add_argument("--background-sprite", default=None, help="替换窗口背景精灵名（加高窗口时必填）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    game = Path(args.game) if args.game else find_game_dir()
    if not game or not (game / "interface" / "tank_designer_view.gui").exists():
        print("[!] 找不到游戏目录，请用 --game 指定")
        return 2
    src = game / "interface" / "tank_designer_view.gui"
    cfg = PRESETS[args.preset]
    window_h = args.height or cfg["window_h"]
    mod_w, mod_h = cfg["modules_size"]
    px, py = cfg["preview"]
    rows = cfg["rows"]

    out = Path(args.out) if args.out else None
    if not out and args.mod:
        out = Path(args.mod) / "interface" / "tank_designer_view.gui"
    if not out:
        print("[!] 请给 --mod 或 --out")
        return 2
    out = out.resolve()
    try:
        out.relative_to(game.resolve())
        print("[!] 拒绝写入游戏目录；请输出到 mod 目录")
        return 2
    except ValueError:
        pass

    text = read(src)

    # 1) 窗口高度
    text = text.replace("size = { width = 1091 height = 542 }",
                        f"size = {{ width = 1091 height = {window_h} }}", 1)
    # 2) 模块容器 / 蓝图
    text = re.sub(r'(name = "equipment_modules"\s*\n\s*position = \{[^}]*\}\s*\n\s*size = \{)[^}]*(\})',
                  lambda m: m.group(1) + f" width={mod_w} height={mod_h}" + m.group(2),
                  text, count=1)
    text = re.sub(r'(name = "equipment_preview"\s*\n\s*position = \{)[^}]*\}',
                  lambda m: m.group(1) + f" x={px} y={py} }}", text, count=1)
    # 3) 槽位位置段
    start = text.find("@fixed_btn_mod_col_0 = 1")
    end = text.find("# Equipment upgrades", start)
    if start < 0 or end < 0:
        print("[!] 原版 GUI 结构变化：找不到槽位段/升级区标记")
        return 2
    text = text[:start] + build_slot_section(rows) + text[end:]
    # 4) 背景
    if args.background_sprite:
        text = text.replace('spriteType ="GFX_tank_designer_popup_bg"',
                            f'spriteType ="{args.background_sprite}"', 1)
    # 5) 隐藏原版控件
    for name in ("equipment_upgrade_0", "equipment_upgrade_1",
                 "auto_upgrade_button", "auto_button", "auto_upgraded_checkbox_button",
                 "niche_button", "tag_icon_bg"):
        text = hide(text, name)
    # 6) 加高时底部元素一起下移
    dy = window_h - 542
    for name in BOTTOM_ELEMENTS:
        text = shift(text, name, dy)

    # 校验括号
    if text.count("{") != text.count("}"):
        print(f"[!] 生成的 GUI 括号不配平：{{={text.count('{')} }}={text.count('}')}，已中止")
        return 2

    # 报告
    print(f"[布局] {args.preset}: 窗口 1091x{window_h}; 容器 {mod_w}x{mod_h}; 蓝图 ({px},{py}); 行 {rows}")
    print("  上排 7 槽 (y=%d) | 第二排 2 槽 (y=%d, 左角/右角) | 下排 7 槽 (y=%d)" % rows)
    if SLOT_W > 72:
        print(f"  [!] 槽位宽 {SLOT_W}px > 列距 72px：相邻槽有 {SLOT_W - 72}px 叠压（原版同样如此；要消除需加宽容器）")
    if window_h != 542 and not args.background_sprite:
        print("  [!] 窗口加高但未换背景精灵：原版背景贴图固定 1092x553，内容会溢出（见 references/tank-designer.md §4.3）")
    if args.dry_run:
        print("[dry-run] 未写文件。目标：", out)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("[ok] 写入", out, f"({len(text.split(chr(10)))} 行)")
    print("     下一步：把该文件所在 mod 装上，重启游戏开坦克设计器验收（新开档/旧档都看）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

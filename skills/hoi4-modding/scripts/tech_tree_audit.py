#!/usr/bin/env python3
"""科技页完整性审计：注册表 ↔ GUI 页面/页签/item 模板/网格 ↔ 科技 ↔ 本地化。

用法：
    python tech_tree_audit.py "<Mod目录>"
    python tech_tree_audit.py "<Mod目录>" --json report.json
    python tech_tree_audit.py "<Mod目录>" --only trm_armour_ger_folder

检查项（每个 technology_folders 条目）：
  * GUI 里是否有同名页面容器（`containerWindowType name = "<folder>"`）
  * 是否有页签按钮（`buttonType name = "<folder>_tab"`）
  * 是否有 item 模板（`techtree_<folder>_item`）与小框模板（`_small_item`）
  * 是否有 gridboxtype
  * 是否有科技使用该 folder（反向：注册表有页面但没科技 → 空页）
  * 科技里出现但注册表没有的 folder（孤儿 folder）

只读，不修改任何文件。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdx_parser as pdx  # noqa: E402

TAGS_REL = Path("common/technology_tags")
GUI_REL = Path("interface/countrytechtreeview.gui")


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace")


def folder_registry(mod: Path) -> list[str]:
    out: list[str] = []
    for p in sorted((mod / TAGS_REL).glob("*.txt")):
        block, _ = pdx.parse_file(str(p))
        for hdr in block.find_blocks("technology_folders"):
            for entry in hdr.pairs():
                if entry.block is not None:
                    out.append(entry.key)
    return out


def gui_index(mod: Path):
    gui = mod / GUI_REL
    if not gui.is_file():
        return {}, {}, {}
    block, _ = pdx.parse_file(str(gui))
    pages, tabs, tmpl = {}, {}, {}
    for entry in block.walk():
        blk = entry.block
        if blk is None:
            continue
        name = blk.first_scalar("name")
        if not name:
            continue
        if entry.key == "containerWindowType":
            pages[name] = blk
        elif entry.key == "buttonType":
            tabs[name] = blk
    for name, blk in pages.items():
        if name.startswith("techtree_"):
            tmpl[name] = blk
    return pages, tabs, tmpl


def tech_folders(mod: Path) -> dict[str, list[str]]:
    used: dict[str, list[str]] = {}
    for p in sorted((mod / "common" / "technologies").glob("*.txt")):
        block, _ = pdx.parse_file(str(p))
        wrappers = list(block.find_blocks("technologies")) or [block]
        for hdr in wrappers:
            for entry in hdr.pairs():
                tech = entry.block
                if tech is None:
                    continue
                for fe in tech.get_all("folder"):
                    fblk = fe.block
                    if fblk is None:
                        continue
                    f = fblk.first_scalar("name")
                    if f:
                        used.setdefault(f, []).append(entry.key)
    return used


def localisation_keys(mod: Path) -> set[str]:
    keys: set[str] = set()
    loc_root = mod / "localisation"
    if not loc_root.is_dir():
        return keys
    for p in loc_root.rglob("*.yml"):
        for line in read_text(p).splitlines():
            m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*:", line)
            if m:
                keys.add(m.group(1))
    return keys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="科技页完整性审计（只读）")
    ap.add_argument("mod", help="Mod 根目录（含 descriptor.mod 或 interface/）")
    ap.add_argument("--json", help="把结果写成 JSON")
    ap.add_argument("--only", action="append", default=None, help="只看这些 folder（可多次）")
    args = ap.parse_args(argv)

    mod = Path(args.mod).expanduser()
    if not mod.is_dir():
        print(f"目录不存在：{mod}")
        return 2

    reg = folder_registry(mod)
    pages, tabs, _ = gui_index(mod)
    used = tech_folders(mod)
    loc = localisation_keys(mod)
    only = set(args.only) if args.only else None

    rows = []
    for f in reg:
        if only and f not in only:
            continue
        page = f in pages
        grids = 0
        if page:
            grids = sum(1 for e in pages[f].pairs() if e.key.lower() == "gridboxtype")
        techs = len(used.get(f, []))
        row = dict(
            folder=f,
            page=page,
            tab=(f + "_tab") in tabs,
            item=f"techtree_{f}_item" in pages,
            small_item=f"techtree_{f}_small_item" in pages,
            grids=grids,
            techs=techs,
            loc_name=f in loc,
        )
        row["problems"] = [
            k for k, bad in (
                ("无页面", not row["page"]),
                ("无页签", not row["tab"]),
                ("无item模板", not row["item"]),
                ("无网格", row["grids"] == 0),
                ("无科技", row["techs"] == 0),
            ) if bad
        ]
        rows.append(row)

    orphans = sorted(f for f in used if f not in set(reg))
    print(f"{'folder':40s} {'页':2s} {'签':2s} {'item':4s} {'small':5s} {'网格':4s} {'科技':4s} {'loc':3s} 问题")
    for r in rows:
        print(
            f"{r['folder']:40s} {'Y' if r['page'] else 'N':2s} {'Y' if r['tab'] else 'N':2s} "
            f"{'Y' if r['item'] else 'N':4s} {'Y' if r['small_item'] else 'N':5s} "
            f"{r['grids']:4d} {r['techs']:4d} {'Y' if r['loc_name'] else 'N':3s} "
            + ",".join(r["problems"])
        )
    bad = sum(1 for r in rows if r["problems"])
    print(f"\n注册表 folder {len(reg)} 个；本次检查 {len(rows)} 个；有问题 {bad} 个")
    if orphans:
        print("科技引用了但注册表没有的 folder：", orphans)
    else:
        print("科技引用的 folder 全部已注册")

    if args.json:
        Path(args.json).write_text(
            json.dumps(dict(folders=rows, orphan_folders=orphans, registry_size=len(reg),
                            problem_count=bad), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("JSON →", args.json)
    return 0 if bad == 0 and not orphans else 1


if __name__ == "__main__":
    raise SystemExit(main())

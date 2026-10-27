#!/usr/bin/env python3
"""把 technology_folders 的可用性条件从"运行时旗帜"改成"国家标签"。

背景：引擎建页画线时会对 folder 的 available 触发器做二次运行时求值，
`has_country_flag = XXX_air / XXX_armor` 在新开档里不成立时，
该页每条 path 会被静默丢弃 —— 表现是"科技方框全在、连线一条没有、error.log 干净"。
正确写法是 `original_tag = XXX`（详见 references/tech-tree-ui.md §3）。

用法：
    python tech_folder_available.py "<Mod目录>" --check    # 只报告，不改
    python tech_folder_available.py "<Mod目录>" --apply    # 改写（自动备份）
    python tech_folder_available.py "<Mod目录>" --revert   # 从最近备份还原

规则：
    has_country_flag = GER_air   -> original_tag = GER
    has_country_flag = ENG_armor -> original_tag = ENG
    无法推断的（自定义名如 GEN_air）保留原样并在报告里列出，交人工判断。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TAG_FILE = Path("common/technology_tags/00_technology.txt")
BACKUP_DIRNAME = ".dsh_techfolder_backup"
FLAG_RE = re.compile(r"has_country_flag\s*=\s*([A-Za-z0-9_]+)")
INFER_RE = re.compile(r"^([A-Z]{3})_(?:air|armou?r)(?:_|$)")
# 个别 Mod 用非常规旗帜名时，可在这里补映射
EXTRA_MAP = {}


def infer_tag(flag: str) -> str | None:
    if flag in EXTRA_MAP:
        return EXTRA_MAP[flag]
    m = INFER_RE.match(flag)
    return m.group(1) if m else None


def read_lines(path: Path) -> tuple[list[str], bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace").splitlines(keepends=True), bom


def write_lines(path: Path, lines: list[str], bom: bool) -> None:
    data = "".join(lines).encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)


def folder_block_range(lines: list[str]) -> tuple[int, int] | None:
    """返回 technology_folders 块的 [起始行, 结束行]（含两端），找不到返回 None。"""
    start = None
    depth = 0
    for i, line in enumerate(lines):
        code = line.split("#", 1)[0]
        if start is None and re.search(r"\btechnology_folders\s*=\s*\{", code):
            start = i
            depth = code.count("{") - code.count("}")
            continue
        if start is not None:
            depth += code.count("{") - code.count("}")
            if depth <= 0:
                return start, i
    return None


def patch(lines: list[str], lo: int, hi: int):
    changes = []
    unknown = []
    out = list(lines)
    for i in range(lo, hi + 1):
        line = out[i]

        def repl(m: re.Match) -> str:
            flag = m.group(1)
            tag = infer_tag(flag)
            if tag is None:
                unknown.append(flag)
                return m.group(0)
            changes.append((flag, tag))
            return f"original_tag = {tag}"

        head = line
        new_line = FLAG_RE.sub(repl, head)
        if new_line != line:
            out[i] = new_line
    return out, changes, sorted(set(unknown))


def latest_backup(mod: Path) -> Path | None:
    root = mod / BACKUP_DIRNAME
    if not root.is_dir():
        return None
    candidates = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)
    return candidates[-1] if candidates else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="technology_folders.available: 旗帜判定 → 国家标签")
    ap.add_argument("mod", help="Mod 根目录")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="只报告（默认动作）")
    mode.add_argument("--apply", action="store_true", help="写入修改（自动备份）")
    mode.add_argument("--revert", action="store_true", help="从最近备份还原")
    args = ap.parse_args(argv)

    mod = Path(args.mod).expanduser()
    tags = mod / TAG_FILE
    if not mod.is_dir():
        print(f"目录不存在：{mod}")
        return 2

    if args.revert:
        bak = latest_backup(mod)
        if not bak:
            print("没有找到备份目录：", mod / BACKUP_DIRNAME)
            return 1
        for p in bak.glob("**/*.txt"):
            rel = p.relative_to(bak)
            dest = mod / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            print("还原", rel)
        return 0

    if not tags.is_file():
        print(f"找不到注册表：{tags}")
        return 2

    lines, bom = read_lines(tags)
    span = folder_block_range(lines)
    if span is None:
        print("找不到 technology_folders 块")
        return 2
    lo, hi = span
    patched, changes, unknown = patch(lines, lo, hi)

    by_flag: dict[str, str] = {}
    for flag, tag in changes:
        by_flag[flag] = tag
    print(f"technology_folders 块：第 {lo + 1}-{hi + 1} 行；命中 {len(changes)} 处 flag")
    for flag, tag in sorted(by_flag.items()):
        print(f"  {flag:14s} -> original_tag = {tag}")
    if unknown:
        print("无法推断、保持原样的旗帜：", ", ".join(unknown))

    if args.check:
        print("\n[check] 未写入。用 --apply 应用。")
        return 0

    if not changes:
        print("没有需要改的内容。")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = mod / BACKUP_DIRNAME / stamp
    dest = bak / TAG_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tags, dest)
    write_lines(tags, patched, bom)
    print(f"\n已写入 {tags}")
    print(f"备份：{bak}（--revert 可还原）")
    print("提醒：必须【新开档】验证连线；旧存档可能掩盖问题。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

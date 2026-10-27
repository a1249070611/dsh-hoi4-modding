#!/usr/bin/env python3
"""error.log 快速分诊：先分清"哪一类问题"，再决定查哪里。

用法：
    python errorlog_triage.py                       # 自动找玩家目录 logs/error.log
    python errorlog_triage.py "<error.log 路径>"
    python errorlog_triage.py --keyword britishair   # 只看含关键字的行
    python errorlog_triage.py --json triage.json

分类：科技树 / 贴图缺失 / scope / 未知 effect-trigger-modifier / 括号 token / 动态 token / 本地化 / 其他
只读，不修改任何文件。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths  # noqa: E402

CATEGORIES = [
    ("科技树-网格", re.compile(r"Found no grid box for tech|Found multiple potential grid boxes")),
    ("科技树-连线", re.compile(r"Trying to draw a path in Folder|Trying to draw exclusive line segment")),
    ("科技树-坐标", re.compile(r"has no coordinates in folder")),
    ("科技树-其它", re.compile(r"countrytechtreeview\.cpp")),
    ("贴图缺失", re.compile(r"texture.*(?:not found|missing|Could not find)|Could not find texture|"
                            r"texturefile.*(?:not found|missing)", re.I)),
    ("scope 错误", re.compile(r"Invalid Scope")),
    ("未知 effect/trigger/modifier",
     re.compile(r"Unknown effect-type|Unknown trigger-type|Unknown modifier|Not a valid value")),
    ("括号/token", re.compile(r"Unexpected token|Unbalanced|unexpected end")),
    ("动态 token / OOS", re.compile(r"dynamic token|OOS", re.I)),
    ("本地化缺失", re.compile(r"Missing localisation|missing localisation|Localisation.*not found", re.I)),
]
LINE_RE = re.compile(r"^\[[^\]]*\]\[[^\]]*\]\[([^\]]+)\]:\s*(.*)$")


def classify(msg: str) -> str:
    for name, rx in CATEGORIES:
        if rx.search(msg):
            return name
    return "其它"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="error.log 分诊（只读）")
    ap.add_argument("log", nargs="?", help="error.log 路径（默认自动探测）")
    ap.add_argument("--keyword", help="只统计含该关键字的行")
    ap.add_argument("--json", help="输出 JSON")
    ap.add_argument("--show", type=int, default=5, help="每类展示多少条（默认 5）")
    args = ap.parse_args(argv)

    if args.log:
        log = Path(args.log).expanduser()
    else:
        user = _paths.find_user_dir()
        if not user:
            print("探测不到玩家目录，请显式传入 error.log 路径")
            return 2
        log = user / "logs" / "error.log"
    if not log.is_file():
        print(f"找不到日志：{log}")
        return 2

    text = log.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    print(f"日志：{log}")
    print(f"行数：{len(lines)}  大小：{log.stat().st_size / 1024:.0f} KB")
    if lines:
        print(f"首行：{lines[0][:120]}")
        print(f"末行：{lines[-1][:120]}")

    counts: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    files: Counter[str] = Counter()
    for line in lines:
        if args.keyword and args.keyword.lower() not in line.lower():
            continue
        m = LINE_RE.match(line)
        msg = m.group(2) if m else line
        where = m.group(1) if m else ""
        cat = classify(msg)
        counts[cat] += 1
        if where:
            files[where] += 1
        if len(samples[cat]) < args.show:
            samples[cat].append(line[:200])

    print("\n=== 分类计数 ===")
    for name, _ in CATEGORIES:
        print(f"  {name:24s} {counts.get(name, 0):6d}")
    print(f"  {'其它':24s} {counts.get('其它', 0):6d}")

    for name, _ in CATEGORIES:
        if not samples.get(name):
            continue
        print(f"\n--- {name}（前 {len(samples[name])} 条）")
        for s in samples[name]:
            print("   " + s)

    print("\n=== 判语 ===")
    tech_total = sum(counts.get(k, 0) for k in ("科技树-网格", "科技树-连线", "科技树-坐标", "科技树-其它"))
    if tech_total == 0:
        print("日志里没有科技树相关记录。若此时'页面有方框但没有任何连线'，")
        print("说明连线在建页阶段被静默跳过：优先检查 technology_folders 的 available 是否用了")
        print("has_country_flag（应改成 original_tag），见 references/tech-tree-ui.md §3。")
    elif counts.get("科技树-网格"):
        print("有 `Found no grid box`：该科技的 <分支根>_tree 网格缺失，去 GUI 里补网格。")
    elif counts.get("科技树-连线") or counts.get("科技树-坐标"):
        print("有坐标系相关报错：检查 path 两端是否同 folder、坐标是否可解析。")
    else:
        print("只有科技树其它记录（例如网格候选冲突 Found multiple ...），按具体条目排查。")

    if args.json:
        Path(args.json).write_text(
            json.dumps(dict(log=str(log), lines=len(lines), counts=dict(counts),
                            files=dict(files.most_common(20))), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print("JSON →", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

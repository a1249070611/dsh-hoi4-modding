#!/usr/bin/env python3
"""全量普查游戏目录：按扩展名、目录、体量建立清单。

为什么要这个脚本而不是几条 shell 命令：
  1. 6 万个文件、10 GB，要反复扫；每次都手敲命令既慢又不可复现
  2. 要拿来做「格式 → 目录」的交叉分析，shell 拼不动
  3. 结果要落盘成 JSON，供后续文档和自检复用

用法：
    python tools/kiant-hoi4-survey.py                    # 全量普查，写 knowledge/survey.local.json
    python tools/kiant-hoi4-survey.py --game "<HOI4 目录>"  # 指定游戏目录（否则自动探测）
    python tools/kiant-hoi4-survey.py --ext dds          # 只看某类扩展名在哪些目录
    python tools/kiant-hoi4-survey.py --dir common       # 只看某个目录下的类型构成
    python tools/kiant-hoi4-survey.py --top 30           # 只看最大的 N 个目录

输出默认落 survey.local.json（含本机路径，已 gitignore）。
仓库里那份 survey.json 是 game_root 为空的基线，只在显式传
--out=survey.json 时才覆盖。
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

# 和其他工具一样自动定位游戏目录，不写死路径——
# 写死会让别人 clone 下来直接跑不动，也会把自己机器上的路径带进版本库。
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-server"))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "survey.json")


def resolve_game(argv: list[str]) -> str:
    """游戏目录的来源优先级：--game 参数 > 自动探测。

    自动探测复用 kb.find_game_dir()（查 Steam 库配置、常见安装位置），
    与 kiant_hoi4_self_check / validate_mod 用的是同一套逻辑。
    """
    for i, a in enumerate(argv):
        if a == "--game" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--game="):
            return a.split("=", 1)[1]
    try:
        import kb
        found = kb.find_game_dir()
    except Exception:
        found = None
    return found or ""

# 这些目录不是游戏内容，是运行时/发行物，普查时单列
NON_CONTENT = {"cef", "pdx_launcher", "crash_reporter", "previewer_assets", "assets", "tweakergui_assets", "pdx_online_assets"}


def walk(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("__pycache__",)]
        for f in fn:
            p = os.path.join(dp, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            yield p, st.st_size


def ext_of(name: str) -> str:
    i = name.rfind(".")
    return name[i + 1:].lower() if i > 0 else "(无扩展名)"


def rel_dir(path: str, root: str) -> str:
    """返回两级目录，够用来归类又不至于太碎。"""
    d = os.path.dirname(os.path.relpath(path, root)).replace("\\", "/")
    if d in ("", "."):
        return "(根目录)"
    parts = d.split("/")
    return parts[0] if len(parts) == 1 else "/".join(parts[:2])


def main(argv: list[str]) -> int:
    GAME = resolve_game(argv)
    if not GAME:
        print("找不到游戏目录。用 --game \"<你的 HOI4 安装目录>\" 指定，")
        print('例如：--game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"')
        return 1
    if not os.path.isdir(GAME):
        print(f"游戏目录不存在: {GAME}")
        return 1

    ext_count: dict[str, int] = defaultdict(int)
    ext_bytes: dict[str, int] = defaultdict(int)
    ext_dirs: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    dir_count: dict[str, int] = defaultdict(int)
    dir_bytes: dict[str, int] = defaultdict(int)
    dir_ext: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    samples: dict[str, list[str]] = defaultdict(list)
    total = total_bytes = 0

    for path, size in walk(GAME):
        rel = os.path.relpath(path, GAME).replace("\\", "/")
        e = ext_of(path)
        d2 = rel_dir(path, GAME)
        total += 1
        total_bytes += size
        ext_count[e] += 1
        ext_bytes[e] += size
        ext_dirs[e][d2] += 1
        dir_count[d2] += 1
        dir_bytes[d2] += size
        dir_ext[d2][e] += 1
        if len(samples[e]) < 6:
            samples[e].append(rel)

    data = {
        "game_root": GAME,
        "total_files": total,
        "total_mb": round(total_bytes / 1048576, 1),
        "extensions": {
            e: {
                "count": ext_count[e],
                "mb": round(ext_bytes[e] / 1048576, 2),
                "dirs": dict(sorted(ext_dirs[e].items(), key=lambda x: -x[1])[:12]),
                "samples": samples[e],
            }
            for e in sorted(ext_count, key=lambda x: -ext_count[x])
        },
        "directories": {
            d: {
                "count": dir_count[d],
                "mb": round(dir_bytes[d] / 1048576, 1),
                "exts": dict(sorted(dir_ext[d].items(), key=lambda x: -x[1])[:10]),
            }
            for d in sorted(dir_count, key=lambda x: -dir_bytes[x])
        },
    }

    here = os.path.dirname(os.path.abspath(__file__))
    # 默认写 survey.local.json：它含本机路径，已 gitignore，
    # 不会污染仓库里那份 game_root 为空的基线。
    # 想更新入库基线（不含路径）时手动传 --out survey.json。
    name = "survey.json" if "--out=survey.json" in argv else "survey.local.json"
    out = os.path.abspath(os.path.join(here, "..", "knowledge", name))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # ---- 终端摘要 ----
    if argv and argv[0] == "--ext":
        e = argv[1].lower()
        if e not in data["extensions"]:
            print(f"没有 {e} 这类文件")
            return 1
        info = data["extensions"][e]
        print(f".{e}  共 {info['count']} 个 / {info['mb']} MB")
        print("分布:")
        for d, n in info["dirs"].items():
            print(f"  {n:6}  {d}")
        print("样本:")
        for s in info["samples"]:
            print("  ", s)
        return 0

    if argv and argv[0] == "--dir":
        d = argv[1].rstrip("/")
        hit = {k: v for k, v in data["directories"].items() if k.startswith(d)}
        for k, v in sorted(hit.items(), key=lambda x: -x[1]["count"]):
            print(f"{k:36} {v['count']:6} 文件 {v['mb']:9.1f} MB  {v['exts']}")
        return 0

    top = int(argv[1]) if len(argv) > 1 and argv[0] == "--top" else 20

    print(f"总计 {total} 个文件 / {data['total_mb']} MB")
    print(f"\n-- 扩展名 Top {top} --")
    for e, info in list(data["extensions"].items())[:top]:
        print(f"  .{e:14} {info['count']:6} 个 {info['mb']:9.2f} MB")
    print(f"\n-- 目录 Top {top}（按体积）--")
    for d, info in list(data["directories"].items())[:top]:
        print(f"  {d:30} {info['count']:6} 文件 {info['mb']:8.1f} MB")
    print(f"\n已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

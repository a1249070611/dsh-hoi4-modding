#!/usr/bin/env python3
"""中文字体体检：找出 GUI 里用了「没有中文分片」的字体名。

背景（1.19.3 实测）：
    `interface/core_chinese.gfx` 用 37 个 `bitmapfont_override` 块，给每个字体名挂
    4 个 `gfx/fonts/chinese/<name>_Nof4` 中文分片。游戏全部 .fnt 自身的 CJK 字形数为 0，
    汉字只存在于这些分片里。因此：
      * 名字在 override 名单里  -> 写中文正常
      * 名字不在名单里（如 hoi_14mbs）-> 中文必然显示成 `????`
    这和有没有装字体 mod 无关，只和 `core_chinese.gfx` 覆盖了哪些名字有关。

用法：
    python font_audit.py "<Mod目录>"
    python font_audit.py "<Mod目录>" --game "E:/Steam/steamapps/common/Hearts of Iron IV"
    python font_audit.py "<Mod目录>" --json report.json
    python font_audit.py "<Mod目录>" --list-supported

只读，不修改任何文件。退出码：0 = 全部安全；1 = 发现无中文分片的字体。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths  # noqa: E402

# Windows 控制台默认 GBK，直接 print 中文/emoji 会 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

# core_chinese.gfx 缺失时的兜底名单（1.19.3 实测，38 个名字）。
FALLBACK_SUPPORTED = {
    "ToolTip_Font", "AnimatedMapText", "Main_14", "Main_14_black", "Main_14_bold",
    "Main_14_eu", "Main_14_grey", "Main_16", "Arial12", "cg_16b", "garamond_14",
    "hoi4_typewriter16", "hoi4_typewriter16_inverted", "hoi4_typewriter22",
    "hoi4_typewriter22_inverted", "hoi_16mbs", "hoi_18", "hoi_18b", "hoi_18mbs",
    "hoi_20b", "hoi_20bs", "hoi_22chat", "hoi_22tech", "hoi_24header", "hoi_30",
    "hoi_30header", "hoi_33", "hoi_36header", "hoi_arrow_font", "nsb_hoi_24header",
    "nsb_hoi_36header", "tahoma_60", "vic_18", "vic_18_black", "vic_22", "vic_36",
    "vic_36_black",
}

FONT_RE = re.compile(r'\bfont\s*=\s*"([^"]+)"')
OVERRIDE_NAME_RE = re.compile(r'\bname\s*=\s*"([^"]+)"')


def load_supported(game: Path | None) -> tuple[set[str], str]:
    """返回 (支持中文的字体名集合, 来源说明)。"""
    if game:
        gfx = game / "interface" / "core_chinese.gfx"
        if gfx.is_file():
            text = gfx.read_text(encoding="utf-8", errors="replace")
            names: set[str] = set()
            # 只在 bitmapfont_override 块里取 name，避免误抓其它 gfx 定义。
            for chunk in re.split(r"bitmapfont_override\s*=\s*\{", text)[1:]:
                depth, end = 1, 0
                for i, ch in enumerate(chunk):
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                body = chunk[:end] if end else chunk
                m = OVERRIDE_NAME_RE.search(body)
                if m:
                    names.add(m.group(1))
            if names:
                return names, f"{gfx}"
    return set(FALLBACK_SUPPORTED), "内置名单（未找到 core_chinese.gfx）"


def scan(mod: Path) -> list[dict]:
    hits: list[dict] = []
    roots = [mod / "interface", mod / "gfx"]
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.gui")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for m in FONT_RE.finditer(line):
                    hits.append({
                        "file": str(path.relative_to(mod)).replace("\\", "/"),
                        "line": lineno,
                        "font": m.group(1),
                    })
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="检查 GUI 字体是否有中文分片")
    ap.add_argument("mod", nargs="?", help="Mod 目录")
    ap.add_argument("--game", help="HOI4 游戏目录（默认自动探测）")
    ap.add_argument("--json", dest="json_out", help="把报告写成 JSON")
    ap.add_argument("--list-supported", action="store_true", help="只打印支持中文的字体名")
    args = ap.parse_args()

    game = Path(args.game) if args.game else _paths.find_game_dir()
    supported, source = load_supported(game)

    if args.list_supported:
        print(f"# {len(supported)} 个字体有中文分片  （来源：{source}）")
        for name in sorted(supported):
            print(name)
        return 0

    if not args.mod:
        ap.error("需要 Mod 目录（或用 --list-supported）")
    mod = Path(args.mod)
    if not mod.is_dir():
        ap.error(f"不是目录：{mod}")

    hits = scan(mod)
    bad = [h for h in hits if h["font"] not in supported]
    bad_names = sorted({h["font"] for h in bad})

    print(f"字体来源：{source}")
    print(f"GUI 中出现的 font= 引用：{len(hits)} 处，涉及 {len({h['font'] for h in hits})} 个字体名")
    if not bad:
        print("[OK] 全部字体都有中文分片")
    else:
        print(f"[FAIL] {len(bad_names)} 个字体名没有中文分片，写中文会显示 ????" )
        for name in bad_names:
            where = [h for h in bad if h["font"] == name]
            print(f"  - {name}  ({len(where)} 处)")
            for h in where[:5]:
                print(f"      {h['file']}:{h['line']}")
            if len(where) > 5:
                print(f"      … 另有 {len(where) - 5} 处")
        print("\n修法：换成支持中文的名字（hoi_16mbs / hoi_18mbs / hoi_20bs / hoi_24header / "
              "hoi_36header / Main_14 / ToolTip_Font 等），或参考 references/fonts-and-cjk.md 自建分片。")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps({
            "source": source,
            "supported": sorted(supported),
            "references": hits,
            "unsupported": bad_names,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"报告：{args.json_out}")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
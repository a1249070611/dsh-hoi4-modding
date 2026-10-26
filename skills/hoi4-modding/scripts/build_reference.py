"""从游戏自带 documentation/*.md 生成可检索的参考数据集与速查表。

输入（只读，默认取本机 1.19.3 安装）：
  documentation/effects_documentation.md
  documentation/triggers_documentation.md
  documentation/modifiers_documentation.md
  documentation/console_commands_documentation.md

输出（默认工作区 reference/）：
  effects.json / triggers.json / modifiers.json / console.json
  CHEATSHEET_effects.md / CHEATSHEET_triggers.md / CHEATSHEET_modifiers.md / CHEATSHEET_console.md
  index.md

用法：
  python tools/build_reference.py
  python tools/build_reference.py --game "E:/Steam/steamapps/common/Hearts of Iron IV" --out reference
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

try:
    from _paths import find_game_dir
except Exception:  # 单独拷贝本文件时退化
    def find_game_dir():
        env = os.environ.get("HOI4_GAME")
        return Path(env) if env else Path(r"E:\Steam\steamapps\common\Hearts of Iron IV")

DEFAULT_GAME = find_game_dir() or Path(r"E:\Steam\steamapps\common\Hearts of Iron IV")
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "reference"

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SCOPE_HEADER_RE = re.compile(r"^(Effects|Triggers|Modifiers) for scope\s+(.+)$", re.I)
SPAN_ID_RE = re.compile(r'<span id="([^"]+)"></span>')
HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class DocEntry:
    name: str
    scopes: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    desc: str = ""
    example: str = ""
    categories: list[str] = field(default_factory=list)
    modified_types: str = ""
    source: str = ""
    extra: dict = field(default_factory=dict)


def collapse(text: str, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "\\|")
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def split_list(value: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"[,/]", value) if p.strip()]
    return parts


def first_fence_body(lines: list[str]) -> list[str]:
    """返回第一段 ``` 代码块内部行。"""
    inside = False
    buf: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if inside:
                return buf
            inside = True
            continue
        if inside:
            buf.append(line.rstrip("\n"))
    return buf


def parse_markdown_doc(path: Path, kind: str) -> tuple[list[DocEntry], list[dict]]:
    """解析 effects/triggers/modifiers 文档。返回 (entries, sections)。
    kind: 'effect' | 'trigger' | 'modifier'
    """
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    entries: list[DocEntry] = []
    sections: list[dict] = []
    current_scope_section: str | None = None

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        m = SECTION_RE.match(line)
        if not m:
            i += 1
            continue
        header = m.group(1).strip()
        scope_m = SCOPE_HEADER_RE.match(HTML_TAG_RE.sub("", header))
        if scope_m:
            current_scope_section = scope_m.group(2).strip()
            sections.append({"title": header, "scope": current_scope_section, "line": i + 1})
            i += 1
            continue
        if header.lower().startswith(("table of content", "all console", "all tweakable")):
            i += 1
            continue

        # 收集条目正文
        body: list[str] = []
        j = i + 1
        while j < n and not SECTION_RE.match(lines[j]):
            body.append(lines[j])
            j += 1

        if kind == "modifier":
            name = header
            span = SPAN_ID_RE.search(name)
            span_id = span.group(1) if span else ""
            name = HTML_TAG_RE.sub("", name).strip()
            if not name or " " in name:
                i = j
                continue
            entry = DocEntry(name=name, source=path.name, extra={"span_id": span_id})
            for raw in body:
                s = raw.strip()
                if s.startswith("* **Description**:"):
                    entry.desc = s.split(":", 1)[1].strip()
                elif s.startswith("* **Categories**:"):
                    entry.categories = split_list(s.split(":", 1)[1])
                elif s.startswith("* **Modified types**:"):
                    entry.modified_types = s.split(":", 1)[1].strip()
                elif s.lower().startswith("* number with"):
                    entry.extra.setdefault("precision", s)
            if not entry.desc:
                entry.desc = next((l.strip() for l in body if l.strip()), "")
            entries.append(entry)
        else:
            if not NAME_RE.match(header):
                i = j
                continue
            entry = DocEntry(name=header, source=path.name)
            for raw in body:
                s = raw.strip()
                if s.lower().startswith("* supported scopes:"):
                    entry.scopes = split_list(s.split(":", 1)[1])
                elif s.lower().startswith("* supported targets:"):
                    entry.targets = split_list(s.split(":", 1)[1])
            fence = first_fence_body(body)
            body_text = "\n".join(fence).strip() or "\n".join(l for l in body if l.strip()).strip()
            if body_text:
                first_line = next((l.strip() for l in body_text.splitlines() if l.strip()), "")
                entry.desc = first_line
                entry.example = body_text
            entries.append(entry)
        i = j

    # 去重（名称 + 描述 + 行内容全同视为重复）
    seen: set[tuple] = set()
    uniq: list[DocEntry] = []
    for e in entries:
        key = (e.name, e.desc, e.modified_types)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    return uniq, sections


def parse_console_doc(path: Path) -> list[DocEntry]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    entries: list[DocEntry] = []
    i = 0
    while i < len(lines):
        m = SECTION_RE.match(lines[i])
        if not m:
            i += 1
            continue
        header = m.group(1).strip()
        if header.lower().startswith(("table of content", "all console", "all tweakable")):
            i += 1
            continue
        body = []
        j = i + 1
        while j < len(lines) and not SECTION_RE.match(lines[j]):
            body.append(lines[j])
            j += 1
        desc_lines = []
        bullets = []
        for raw in body:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("* "):
                bullets.append(s[2:])
            elif not desc_lines or (desc_lines and not s.startswith('"')):
                desc_lines.append(s)
        entries.append(
            DocEntry(
                name=header,
                desc=collapse(" ".join(desc_lines))[:400],
                extra={"bullets": bullets},
                source=path.name,
            )
        )
        i = j
    return entries


def write_json(path: Path, entries: list[DocEntry], meta: dict) -> None:
    payload = {
        "meta": meta,
        "count": len(entries),
        "entries": [asdict(e) for e in entries],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def md_table(rows: list[list[str]], header: list[str]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return out


def write_effects_cheatsheet(path: Path, entries: list[DocEntry], title: str, kind: str) -> None:
    lines = [f"# {title}", ""]
    lines.append(f"> 自动生成自游戏 `documentation/`（1.19.3），共 **{len(entries)}** 条。")
    lines.append("> 说明列取首行描述；完整示例见 `reference/{}.json` 或游戏文档。".format("effects" if kind == "effect" else "triggers"))
    lines.append("")
    by_scope: dict[str, list[DocEntry]] = {}
    for e in entries:
        for scope in e.scopes or ["（未标注）"]:
            by_scope.setdefault(scope, []).append(e)
    for scope in sorted(by_scope):
        items = sorted(by_scope[scope], key=lambda x: x.name.lower())
        lines.append(f"## {scope}（{len(items)}）")
        lines.append("")
        rows = []
        for e in items:
            extra = ""
            if kind == "trigger" and e.targets:
                extra = "目标: " + ", ".join(e.targets)
            rows.append([f"`{e.name}`", collapse(e.desc, 110), extra])
        lines.extend(md_table(rows, ["名称", "说明", "备注"]))
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_modifiers_cheatsheet(path: Path, entries: list[DocEntry]) -> None:
    lines = [
        "# Modifiers 速查表",
        "",
        f"> 自动生成自 `documentation/modifiers_documentation.md`（1.19.3），共 **{len(entries)}** 条（含模板型 modifier，如 `<Building>_max_level_terrain_limit`）。",
        "> 同一名称可能对应多个适用对象，`Modified types` 见 JSON。",
        "",
    ]
    by_cat: dict[str, list[DocEntry]] = {}
    for e in entries:
        cat = e.categories[0] if e.categories else "（未分类）"
        by_cat.setdefault(cat, []).append(e)
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=lambda x: x.name.lower())
        lines.append(f"## {cat}（{len(items)}）")
        lines.append("")
        rows = [[f"`{e.name}`", collapse(e.desc, 120)] for e in items]
        lines.extend(md_table(rows, ["Modifier", "说明"]))
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_console_cheatsheet(path: Path, entries: list[DocEntry], tweakables: list[DocEntry]) -> None:
    lines = ["# 控制台命令速查表", "", f"> 自动生成自 `documentation/console_commands_documentation.md`（1.19.3）。命令 {len(entries)} 个，可调参数 {len(tweakables)} 个。", ""]
    lines.append("## 控制台命令")
    lines.append("")
    rows = [[f"`{e.name}`", collapse(e.desc, 110)] for e in sorted(entries, key=lambda x: x.name.lower())]
    lines.extend(md_table(rows, ["命令", "说明"]))
    lines.append("")
    lines.append("## 可调参数（Tweakable Variables）")
    lines.append("")
    rows = [[f"`{e.name}`", collapse(e.desc, 110)] for e in sorted(tweakables, key=lambda x: x.name.lower())]
    lines.extend(md_table(rows, ["参数", "说明"]))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    docs = args.game / "documentation"
    if not docs.is_dir():
        raise SystemExit(f"找不到游戏文档目录：{docs}")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    version = (args.game / "hoi4_rev.txt").read_text(encoding="utf-8", errors="ignore").strip()

    effects, _ = parse_markdown_doc(docs / "effects_documentation.md", "effect")
    triggers, _ = parse_markdown_doc(docs / "triggers_documentation.md", "trigger")
    modifiers, _ = parse_markdown_doc(docs / "modifiers_documentation.md", "modifier")

    console_entries: list[DocEntry] = []
    console_tweaks: list[DocEntry] = []
    console_path = docs / "console_commands_documentation.md"
    if console_path.exists():
        all_console = parse_console_doc(console_path)
        # 文档里用 "## All Tweakable Variables" 分界
        text = console_path.read_text(encoding="utf-8-sig")
        split_at = text.find("## All Tweakable Variables")
        console_text = text[: split_at if split_at > 0 else len(text)]
        tweak_text = text[split_at:] if split_at > 0 else ""
        console_entries = parse_console_doc_from_text(console_text)
        console_tweaks = parse_console_doc_from_text(tweak_text)

    meta = {"game_version_rev": version, "generated_at": today, "source": "game documentation/*.md"}
    write_json(out / "effects.json", effects, meta)
    write_json(out / "triggers.json", triggers, meta)
    write_json(out / "modifiers.json", modifiers, meta)
    write_json(out / "console.json", console_entries + console_tweaks, meta)

    write_effects_cheatsheet(out / "CHEATSHEET_effects.md", effects, "Effects 速查表（按作用域）", "effect")
    write_effects_cheatsheet(out / "CHEATSHEET_triggers.md", triggers, "Triggers 速查表（按作用域）", "trigger")
    write_modifiers_cheatsheet(out / "CHEATSHEET_modifiers.md", modifiers)
    write_console_cheatsheet(out / "CHEATSHEET_console.md", console_entries, console_tweaks)

    effect_scopes = sorted({s for e in effects for s in e.scopes})
    index = [
        "# 参考数据索引（自动生成）",
        "",
        f"- 生成时间：{today}",
        f"- 游戏版本：1.19.3.0（rev `{version}`）",
        f"- 来源：`{docs}`",
        "",
        "## 数据集",
        "",
        "| 文件 | 条目数 | 内容 |",
        "|---|---|---|",
        f"| `effects.json` | {len(effects)} | effect 全量（作用域/目标/说明/示例） |",
        f"| `triggers.json` | {len(triggers)} | trigger 全量 |",
        f"| `modifiers.json` | {len(modifiers)} | modifier 全量（含模板型、适用对象、分类） |",
        f"| `console.json` | {len(console_entries) + len(console_tweaks)} | 控制台命令 + 可调参数 |",
        f"| `CHEATSHEET_effects.md` | {len(effects)} | 按作用域分组的中文速查表 |",
        f"| `CHEATSHEET_triggers.md` | {len(triggers)} | 同上 |",
        f"| `CHEATSHEET_modifiers.md` | {len(modifiers)} | 按分类分组 |",
        f"| `CHEATSHEET_console.md` | {len(console_entries) + len(console_tweaks)} | 命令列表 |",
        "",
        "## 用法",
        "",
        "```python",
        "import json",
        "data = json.load(open('reference/effects.json', encoding='utf-8'))",
        "country_effects = [e['name'] for e in data['entries'] if 'COUNTRY' in e['scopes']]",
        "print(len(country_effects), country_effects[:10])",
        "```",
        "",
        "```bash",
        "grep -i 'add_ideas' reference/CHEATSHEET_effects.md",
        "```",
        "",
        f"## 作用域覆盖（effects 共 {len(effect_scopes)} 种）",
        "",
        "、".join(f"`{s}`" for s in effect_scopes),
        "",
        "> 注意：本数据由文档自动解析，条目说明可能含游戏内部术语；写 Mod 时以「文档 + 游戏内实际测试」为准。",
    ]
    (out / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    print(f"effects: {len(effects)}")
    print(f"triggers: {len(triggers)}")
    print(f"modifiers: {len(modifiers)}")
    print(f"console: {len(console_entries)} commands, {len(console_tweaks)} tweakables")
    print(f"output: {out}")
    return 0


def parse_console_doc_from_text(text: str) -> list[DocEntry]:
    """直接解析一段控制台文档文本（用于按「命令/可调参数」切分后分别解析）。"""
    entries: list[DocEntry] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = SECTION_RE.match(lines[i])
        if not m:
            i += 1
            continue
        header = m.group(1).strip()
        if header.lower().startswith(("table of content", "all console", "all tweakable", "# console")):
            i += 1
            continue
        body = []
        j = i + 1
        while j < len(lines) and not SECTION_RE.match(lines[j]):
            body.append(lines[j])
            j += 1
        desc_lines, bullets = [], []
        for raw in body:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("* "):
                bullets.append(s[2:])
            else:
                desc_lines.append(s)
        entries.append(
            DocEntry(
                name=header,
                desc=collapse(" ".join(desc_lines))[:400],
                extra={"bullets": bullets},
                source="console_commands_documentation.md",
            )
        )
        i = j
    return entries


if __name__ == "__main__":
    raise SystemExit(main())

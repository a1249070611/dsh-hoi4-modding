"""HOI4 Mod 静态校验器（1.19.3 适配）。

检查项
  结构   : descriptor.mod / 同级 .mod / path / supported_version / picture
  语法   : .txt/.gfx/.gui 解析（括号、引号、key=value）、UTF-8、BOM
  本地化 : .yml BOM、首行 l_<lang>:、重复 key、key 缺失（国策/事件/理念/决议/角色/科技）
  资源   : GFX 精灵引用是否存在（Mod + 原版）、texturefile 路径是否存在
  冲突   : Mod 内重复 ID、与原版 ID 冲突（国策/理念/决议/科技/角色/事件）
  其它   : replace_path、tags、thumbnail

用法
  python tools/hoi4_lint.py example_mods/hello_hoi4
  python tools/hoi4_lint.py example_mods/hello_hoi4 --json
  python tools/hoi4_lint.py example_mods/hello_hoi4 --no-vanilla   # 跳过原版对比（快）
  python tools/hoi4_lint.py --refresh-cache                        # 重建原版索引

退出码：0 = 无 error；1 = 有 error。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pdx_parser as pdx  # noqa: E402

try:
    from _paths import find_game_dir
except Exception:  # 单独拷贝本文件时退化
    def find_game_dir():
        env = os.environ.get("HOI4_GAME")
        return Path(env) if env else Path(r"E:\Steam\steamapps\common\Hearts of Iron IV")

DEFAULT_GAME = find_game_dir() or Path(r"E:\Steam\steamapps\common\Hearts of Iron IV")
CACHE_PATH = Path(__file__).resolve().parent / ".cache" / "vanilla_index.json"
TARGET_VERSION = "1.19"

SCRIPT_EXTS = {".txt", ".gfx", ".gui"}
TEXT_EXTS = {".txt", ".gfx", ".gui", ".yml", ".asset", ".csv", ".md", ".json"}
DECISION_KEYS = {
    "available", "visible", "complete_effect", "remove_effect", "timeout_effect",
    "days_remove", "days_mission_timeout", "fire_only_once", "cost", "target_trigger",
    "custom_cost_trigger", "custom_cost_text", "is_good", "cancel_effect", "cancel_trigger",
}
SPRITE_RE = re.compile(r'\bname\s*=\s*"?((?:GFX_)[A-Za-z0-9_.\-]+)"?')
EVENT_ID_RE = re.compile(r"\bid\s*=\s*([a-z][a-z0-9_]*\.\d+)\b")
LOC_LINE_RE = re.compile(r'^\s*([A-Za-z0-9_@.\-]+):\d*\s+(.*)$')


@dataclass
class Issue:
    severity: str  # error | warning | info
    code: str
    path: str
    line: int
    message: str

    def sort_key(self):
        return (self.path, self.line, self.severity)

    def as_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "line": self.line,
            "message": self.message,
        }


@dataclass
class Report:
    mod: str
    issues: list[Issue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add(self, severity: str, code: str, path: str, line: int, message: str):
        self.issues.append(Issue(severity, code, path, line, message))

    def errors(self):
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self):
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> dict:
        data = {
            "mod": self.mod,
            "errors": len(self.errors()),
            "warnings": len(self.warnings()),
            "issues": [i.as_dict() for i in sorted(self.issues, key=lambda x: x.sort_key())],
        }
        data.update(self.stats)
        return data


# ---------------------------------------------------------------------------
# 原版索引（一次性缓存）
# ---------------------------------------------------------------------------

def _parse_dir_ids(game: Path, subdir: str, container: str | None) -> set[str]:
    ids: set[str] = set()
    root = game / subdir
    if not root.exists():
        return ids
    for path in root.rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        if container:
            for block in tree.find_blocks(container):
                for e in block.pairs():
                    if isinstance(e.value, pdx.Block):
                        ids.add(e.key)
        else:
            for e in tree.pairs():
                if isinstance(e.value, pdx.Block) and not e.key.startswith("@"):
                    ids.add(e.key)
    return ids


def build_vanilla_index(game: Path) -> dict:
    print(f"[cache] 构建原版索引（{game}）…", file=sys.stderr)
    idx: dict[str, list[str]] = {}

    sprites: set[str] = set()
    texfiles: set[str] = set()
    for path in (game / "interface").rglob("*.gfx"):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        sprites.update(SPRITE_RE.findall(text))
        texfiles.update(re.findall(r'texturefile\s*=\s*"([^"]+)"', text))
    for path in (game / "gfx").rglob("*.gfx"):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        sprites.update(SPRITE_RE.findall(text))

    loc_keys: set[str] = set()
    for path in (game / "localisation" / "english").glob("*.yml"):
        try:
            for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                m = LOC_LINE_RE.match(line)
                if m:
                    loc_keys.add(m.group(1))
        except OSError:
            continue

    focus_ids: set[str] = set()
    for path in (game / "common" / "national_focus").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for block in tree.find_blocks("focus"):
            val = block.first_scalar("id")
            if val:
                focus_ids.add(val)

    idea_ids: set[str] = set()
    for path in (game / "common" / "ideas").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for ideas_block in tree.find_blocks("ideas"):
            for container in ideas_block.pairs():
                if isinstance(container.value, pdx.Block):
                    for e in container.value.pairs():
                        if isinstance(e.value, pdx.Block):
                            idea_ids.add(e.key)

    decision_ids, category_ids = extract_decision_ids(game / "common" / "decisions")

    tech_ids: set[str] = set()
    for path in (game / "common" / "technologies").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for block in tree.find_blocks("technologies"):
            for e in block.pairs():
                if isinstance(e.value, pdx.Block):
                    tech_ids.add(e.key)

    char_ids: set[str] = set()
    for path in (game / "common" / "characters").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for block in tree.find_blocks("characters"):
            for e in block.pairs():
                if isinstance(e.value, pdx.Block):
                    char_ids.add(e.key)

    event_ids: set[str] = set()
    for path in (game / "events").rglob("*.txt"):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        event_ids.update(EVENT_ID_RE.findall(text))

    scripted_effect_names: set[str] = set()
    for path in (game / "common" / "scripted_effects").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for e in tree.pairs():
            if isinstance(e.value, pdx.Block) and not e.key.startswith("@"):
                scripted_effect_names.add(e.key)

    on_action_names: set[str] = set()
    for path in (game / "common" / "on_actions").rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for e in tree.pairs():
            if isinstance(e.value, pdx.Block):
                on_action_names.add(e.key)

    mio_ids = _parse_dir_ids(game, "common/military_industrial_organization/organizations", None)
    sp_ids = _parse_dir_ids(game, "common/special_projects/projects", None)

    idx = {
        "game": str(game),
        "version": _read_version(game),
        "sprites": sorted(sprites),
        "texturefiles": sorted(texfiles),
        "loc": sorted(loc_keys),
        "focus": sorted(focus_ids),
        "ideas": sorted(idea_ids),
        "decisions": sorted(decision_ids),
        "decision_categories": sorted(category_ids),
        "technologies": sorted(tech_ids),
        "characters": sorted(char_ids),
        "events": sorted(event_ids),
        "scripted_effects": sorted(scripted_effect_names),
        "on_actions": sorted(on_action_names),
        "mios": sorted(mio_ids),
        "special_projects": sorted(sp_ids),
    }
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(idx, ensure_ascii=False, indent=0), encoding="utf-8")
    print(
        f"[cache] sprites={len(sprites)} loc={len(loc_keys)} focus={len(focus_ids)} "
        f"ideas={len(idea_ids)} decisions={len(decision_ids)} techs={len(tech_ids)} "
        f"chars={len(char_ids)} events={len(event_ids)}",
        file=sys.stderr,
    )
    return idx


def _read_version(game: Path) -> str:
    try:
        text = (game / "launcher-settings.json").read_text(encoding="utf-8-sig", errors="ignore")
        m = re.search(r'"rawVersion"\s*:\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    except OSError:
        pass
    return "unknown"


def load_vanilla_index(game: Path, refresh: bool = False) -> dict:
    if not refresh and CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if data.get("game") == str(game):
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return build_vanilla_index(game)


# ---------------------------------------------------------------------------
# 提取器
# ---------------------------------------------------------------------------

def extract_decision_ids(decisions_dir: Path) -> tuple[set[str], set[str]]:
    decision_ids: set[str] = set()
    category_ids: set[str] = set()
    if not decisions_dir.exists():
        return decision_ids, category_ids
    for path in decisions_dir.rglob("*.txt"):
        try:
            tree, _ = pdx.parse_file(path)
        except Exception:
            continue
        for e in tree.pairs():
            if not isinstance(e.value, pdx.Block):
                continue
            block = e.value
            child_blocks = [c for c in block.pairs() if isinstance(c.value, pdx.Block)]
            is_category = bool(child_blocks) and any(
                any(k.key in DECISION_KEYS for k in c.value.pairs()) for c in child_blocks
            )
            if is_category:
                category_ids.add(e.key)
                for c in child_blocks:
                    if any(k.key in DECISION_KEYS for k in c.value.pairs()):
                        decision_ids.add(c.key)
            elif any(k.key in DECISION_KEYS for k in block.pairs()):
                decision_ids.add(e.key)
        # 兼容 decision = { id = xxx } 写法
        for block in tree.find_blocks("decision"):
            val = block.first_scalar("id")
            if val:
                decision_ids.add(val)
    return decision_ids, category_ids


def extract_focuses(tree: pdx.Block) -> list[tuple[str, str | None, str | None, int]]:
    """-> [(id, loc_key_hint, icon, line)]"""
    out = []
    for block in tree.find_blocks("focus"):
        id_entry = block.get("id")
        if not id_entry or id_entry.scalar is None:
            continue
        loc_hint = None
        text_entry = block.get("text")
        if text_entry and text_entry.scalar:
            loc_hint = text_entry.scalar
        icon = block.first_scalar("icon")
        out.append((id_entry.scalar, loc_hint, icon, id_entry.line))
    return out


def extract_events(tree: pdx.Block) -> list[dict]:
    out = []
    for kind in ("country_event", "news_event", "state_event", "unit_leader_event", "operative_leader_event"):
        for block in tree.find_blocks(kind):
            id_entry = block.get("id")
            if not id_entry or id_entry.scalar is None:
                continue
            out.append(
                {
                    "id": id_entry.scalar,
                    "line": id_entry.line,
                    "has_title": block.get("title") is not None,
                    "has_desc": block.get("desc") is not None,
                    "picture": block.first_scalar("picture"),
                    "kind": kind,
                }
            )
    return out


def extract_ideas(tree: pdx.Block) -> list[tuple[str, str | None, int]]:
    out = []
    for ideas_block in tree.find_blocks("ideas"):
        for container in ideas_block.pairs():
            if not isinstance(container.value, pdx.Block):
                continue
            for e in container.value.pairs():
                if isinstance(e.value, pdx.Block):
                    out.append((e.key, e.value.first_scalar("picture"), e.line))
    return out


def extract_decisions(tree: pdx.Block) -> tuple[list[tuple[str, str | None, int]], list[dict]]:
    """-> ([(category_id, icon, line)], [decision dict])"""
    cats: list[tuple[str, str | None, int]] = []
    decs: list[dict] = []
    for e in tree.pairs():
        if not isinstance(e.value, pdx.Block):
            continue
        block = e.value
        children = [c for c in block.pairs() if isinstance(c.value, pdx.Block)]
        is_cat = bool(children) and any(
            any(k.key in DECISION_KEYS for k in c.value.pairs()) for c in children
        )
        if is_cat:
            cats.append((e.key, block.first_scalar("icon"), e.line))
            for c in children:
                if any(k.key in DECISION_KEYS for k in c.value.pairs()):
                    decs.append({"id": c.key, "line": c.line, "icon": c.value.first_scalar("icon"), "has_desc": c.value.get("desc") is not None})
        elif any(k.key in DECISION_KEYS for k in block.pairs()):
            decs.append({"id": e.key, "line": e.line, "icon": block.first_scalar("icon"), "has_desc": block.get("desc") is not None})
    for block in tree.find_blocks("decision"):
        val = block.first_scalar("id")
        if val:
            decs.append({"id": val, "line": block.line, "icon": block.first_scalar("icon"), "has_desc": block.get("desc") is not None})
    return cats, decs


def extract_characters(tree: pdx.Block) -> list[dict]:
    out = []
    for block in tree.find_blocks("characters"):
        for e in block.pairs():
            if not isinstance(e.value, pdx.Block):
                continue
            char = e.value
            info = {
                "id": e.key,
                "line": e.line,
                "name": char.first_scalar("name"),
                "portraits": [],
                "advisor_tokens": [],
            }
            for p in char.find_blocks("portraits"):
                for pe in p.pairs():
                    if pe.scalar and str(pe.scalar).startswith("GFX_"):
                        info["portraits"].append((pe.scalar, pe.line))
                    elif isinstance(pe.value, pdx.Block):
                        for sub in pe.value.pairs():
                            if sub.scalar and str(sub.scalar).startswith("GFX_"):
                                info["portraits"].append((sub.scalar, sub.line))
            for adv in char.find_blocks("advisor"):
                tok = adv.first_scalar("idea_token")
                if tok:
                    info["advisor_tokens"].append((tok, adv.line))
            out.append(info)
    return out


def extract_technologies(tree: pdx.Block) -> list[tuple[str, int]]:
    out = []
    for block in tree.find_blocks("technologies"):
        for e in block.pairs():
            if isinstance(e.value, pdx.Block) and not e.key.startswith("@"):
                out.append((e.key, e.line))
    return out


def extract_named_blocks(tree: pdx.Block, container: str | None = None) -> list[tuple[str, int]]:
    out = []
    if container:
        found = False
        for block in tree.find_blocks(container):
            found = True
            for e in block.pairs():
                if isinstance(e.value, pdx.Block):
                    out.append((e.key, e.line))
        if found:
            return out
    for e in tree.pairs():
        if isinstance(e.value, pdx.Block) and not e.key.startswith("@"):
            out.append((e.key, e.line))
    return out


# ---------------------------------------------------------------------------
# 校验主逻辑
# ---------------------------------------------------------------------------

class Linter:
    def __init__(self, mod_dir: Path, game: Path, vanilla: dict | None, strict: bool = False):
        self.mod = mod_dir.resolve()
        self.game = game
        self.vanilla = vanilla or {}
        self.strict = strict
        self.report = Report(mod=str(self.mod))
        self.mod_sprites: set[str] = set()
        self.mod_loc: dict[str, tuple[str, int]] = {}
        self.mod_loc_dups: list[tuple[str, str, int]] = []

    # ---- 工具 ----
    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.mod)).replace("\\", "/")
        except ValueError:
            return str(path)

    def add(self, severity: str, code: str, path: Path | str, line: int, message: str):
        self.report.add(severity, code, self.rel(Path(path)) if isinstance(path, Path) else str(path), line, message)

    def err(self, code: str, path, line: int, message: str):
        self.add("error", code, path, line, message)

    def warn(self, code: str, path, line: int, message: str):
        self.add("warning", code, path, line, message)

    # ---- 1. 结构 ----
    def check_structure(self):
        mod = self.mod
        descriptor = mod / "descriptor.mod"
        if not descriptor.exists():
            self.err("mod.descriptor_missing", mod / "descriptor.mod", 1, "缺少 descriptor.mod（Mod 根目录必需）")
        else:
            self._check_descriptor(descriptor, is_mod_file=False)
        sibling = mod.parent / f"{mod.name}.mod"
        if sibling.exists():
            self._check_descriptor(sibling, is_mod_file=True)
        else:
            self.warn("mod.sibling_mod_missing", mod / f"{mod.name}.mod", 1, f"缺少同级 {mod.name}.mod，启动器无法直接识别（install_mod.py 可生成）")

        if not any((mod / d).exists() for d in ("common", "events", "history", "interface", "gfx", "localisation", "map")):
            self.warn("mod.empty", mod, 1, "未发现任何内容目录（common/events/history/interface/gfx/localisation/map）")

    def _check_descriptor(self, path: Path, is_mod_file: bool):
        tree, errors = pdx.parse_file(path)
        for e in errors:
            self.err("mod.descriptor_parse", path, e.line, f"descriptor 解析失败：{e.message}")
        name = tree.first_scalar("name")
        if not name:
            self.err("mod.descriptor_name", path, 1, "descriptor 缺少 name")
        sv = tree.first_scalar("supported_version")
        if not sv:
            self.err("mod.descriptor_version", path, 1, "descriptor 缺少 supported_version")
        elif not (sv.startswith(TARGET_VERSION + ".") or sv == TARGET_VERSION or sv.startswith(TARGET_VERSION + "*")):
            self.warn("mod.version_mismatch", path, 1, f"supported_version={sv!r} 与当前游戏 {TARGET_VERSION}.x 不一致")
        picture = tree.first_scalar("picture")
        if picture:
            candidates = [self.mod / picture, path.parent / picture]
            if not any(c.exists() for c in candidates):
                self.warn("mod.thumbnail_missing", path, 1, f"picture={picture!r} 文件不存在（应在 Mod 根目录）")
        if is_mod_file:
            p = tree.first_scalar("path")
            if not p:
                self.err("mod.path_missing", path, 1, ".mod 文件缺少 path（启动器靠它定位内容）")
            else:
                target = Path(p.replace("\\\\", "\\"))
                if not target.exists():
                    self.err("mod.path_not_found", path, 1, f"path 指向的目录不存在：{p}")
                elif target.resolve() != self.mod:
                    self.warn("mod.path_mismatch", path, 1, f"path 指向 {target}，与当前校验目录 {self.mod} 不一致")
        for entry in tree.find_entries("replace_path"):
            if entry.scalar:
                self.report.stats.setdefault("replace_paths", []).append(entry.scalar)
        tags = tree.get_all("tags")
        for t in tags:
            if isinstance(t.value, pdx.Block):
                vals = [e.key for e in t.value.pairs()]
                if not vals:
                    self.warn("mod.tags_empty", path, t.line, "tags 为空")

    # ---- 2. 脚本解析 ----
    def check_scripts(self) -> dict[Path, pdx.Block]:
        trees: dict[Path, pdx.Block] = {}
        count = 0
        for path in self.mod.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCRIPT_EXTS:
                continue
            if ".verified" in path.parts:
                continue
            count += 1
            try:
                raw = path.read_bytes()
            except OSError as exc:
                self.err("io.read", path, 1, f"无法读取：{exc}")
                continue
            if raw.startswith(b"\xef\xbb\xbf") and path.suffix.lower() in (".txt", ".gfx", ".gui"):
                self.warn("enc.bom_script", path, 1, "脚本文件带 UTF-8 BOM；建议去掉（游戏虽能读，但部分工具会异常）")
            tree, errors = pdx.parse_text(raw.decode("utf-8-sig", errors="replace"), str(path))
            for e in errors:
                self.err("syntax.parse", path, e.line, e.message)
            if path.suffix.lower() == ".txt":
                trees[path] = tree
        self.report.stats["script_files"] = count
        return trees

    # ---- 3. 本地化 ----
    def check_localisation(self):
        loc_dir = self.mod / "localisation"
        if not loc_dir.exists():
            self.warn("loc.missing", loc_dir, 1, "没有 localisation/ 目录")
            return
        for path in loc_dir.rglob("*.yml"):
            self._check_loc_file(path)
        # 重复 key
        for key, rel, line in self.mod_loc_dups:
            self.err("loc.duplicate_key", self.mod / rel, line, f"本地化 key 重复：{key}")

    def _check_loc_file(self, path: Path):
        raw = path.read_bytes()
        lang_dir = path.parent.name
        expected = f"l_{lang_dir}"
        text = raw.decode("utf-8-sig", errors="replace")
        has_non_ascii = any(ord(ch) > 127 for ch in text)
        has_bom = raw.startswith(b"\xef\xbb\xbf")
        if has_non_ascii and not has_bom:
            self.err("loc.no_bom", path, 1, "含非 ASCII 字符但没有 UTF-8 BOM，游戏会乱码/报错")
        first = next((l for l in text.splitlines() if l.strip()), "")
        if not re.match(r"^\s*l_[a-z_]+:\s*$", first):
            self.warn("loc.first_line", path, 1, f"首行应为 l_<lang>:（当前 {first[:40]!r}）")
        else:
            declared = first.strip().rstrip(":")
            if declared != expected:
                self.warn("loc.lang_mismatch", path, 1, f"目录是 {lang_dir}，但文件声明 {declared}")
        seen: dict[str, int] = {}
        rel = self.rel(path)
        for lineno, line in enumerate(text.splitlines(), 1):
            m = LOC_LINE_RE.match(line)
            if not m:
                continue
            key = m.group(1)
            if not m.group(2).strip().startswith('"'):
                self.warn("loc.format", path, lineno, f"key {key} 的值未以双引号开始")
            if key in seen:
                self.mod_loc_dups.append((key, rel, lineno))
            else:
                seen[key] = lineno
                self.mod_loc.setdefault(key, (rel, lineno))

    def has_loc(self, key: str) -> bool:
        if key in self.mod_loc:
            return True
        if self.vanilla and key in self._vanilla_loc_set():
            return True
        return False

    def _vanilla_loc_set(self) -> set[str]:
        if not hasattr(self, "_vanilla_loc_cache"):
            self._vanilla_loc_cache = set(self.vanilla.get("loc", []))
        return self._vanilla_loc_cache

    # ---- 4. 内容语义 ----
    def check_content(self, trees: dict[Path, pdx.Block]):
        self._defined: dict[str, list[tuple[str, str, int]]] = {}

        for path, tree in trees.items():
            rel = self.rel(path)
            if "/national_focus/" in f"/{rel}" or rel.startswith("common/national_focus/"):
                for fid, loc_hint, icon, line in extract_focuses(tree):
                    self._add_def("focus", fid, rel, line)
                    if not self.has_loc(fid):
                        self.err("loc.missing_focus", path, line, f"国策 {fid} 缺少本地化 key（默认用 id 作为 key）")
                    if loc_hint and not self.has_loc(loc_hint):
                        self.err("loc.missing_focus_text", path, line, f"国策 {fid} 的 text={loc_hint} 缺少本地化")
                    self._check_icon(path, line, icon, "focus")
            elif rel.startswith("events/") or "/events/" in f"/{rel}":
                for ev in extract_events(tree):
                    self._add_def("event", ev["id"], rel, ev["line"])
                    if not ev["has_title"] and not self.has_loc(f"{ev['id']}.t"):
                        self.warn("loc.missing_event_title", path, ev["line"], f"事件 {ev['id']} 无 title，默认 key {ev['id']}.t 不存在")
                    if not ev["has_desc"] and not self.has_loc(f"{ev['id']}.d"):
                        self.warn("loc.missing_event_desc", path, ev["line"], f"事件 {ev['id']} 无 desc，默认 key {ev['id']}.d 不存在")
                    self._check_icon(path, ev["line"], ev["picture"], "event")
            elif rel.startswith("common/decisions/"):
                cats, decs = extract_decisions(tree)
                for cid, icon, line in cats:
                    self._add_def("decision_category", cid, rel, line)
                    if not self.has_loc(cid):
                        self.warn("loc.missing_decision_category", path, line, f"决议类别 {cid} 缺少本地化 key")
                    self._check_icon(path, line, icon, "decision_category")
                for dec in decs:
                    self._add_def("decision", dec["id"], rel, dec["line"])
                    if not self.has_loc(dec["id"]):
                        self.err("loc.missing_decision", path, dec["line"], f"决议 {dec['id']} 缺少本地化 key")
                    if not dec["has_desc"] and not self.has_loc(f"{dec['id']}_desc"):
                        self.warn("loc.missing_decision_desc", path, dec["line"], f"决议 {dec['id']} 缺少 {dec['id']}_desc")
                    self._check_icon(path, dec["line"], dec["icon"], "decision")
            elif rel.startswith("common/ideas/"):
                for iid, picture, line in extract_ideas(tree):
                    self._add_def("idea", iid, rel, line)
                    if not self.has_loc(iid):
                        self.err("loc.missing_idea", path, line, f"理念 {iid} 缺少本地化 key")
                    if not self.has_loc(f"{iid}_desc"):
                        self.warn("loc.missing_idea_desc", path, line, f"理念 {iid} 缺少 {iid}_desc")
                    self._check_icon(path, line, picture, "idea")
            elif rel.startswith("common/characters/"):
                for ch in extract_characters(tree):
                    self._add_def("character", ch["id"], rel, ch["line"])
                    if ch["name"] and not self.has_loc(ch["name"]):
                        self.err("loc.missing_character_name", path, ch["line"], f"角色 {ch['id']} 的 name={ch['name']} 缺少本地化")
                    for tok, line in ch["advisor_tokens"]:
                        self._add_def("advisor_idea", tok, rel, line)
                        if not self.has_loc(tok):
                            self.err("loc.missing_advisor", path, line, f"顾问 idea_token={tok} 缺少本地化 key")
                    for gfx, line in ch["portraits"]:
                        if not self.has_sprite(gfx):
                            self.err("gfx.missing_portrait", path, line, f"肖像 sprite 不存在：{gfx}")
            elif rel.startswith("common/technologies/"):
                for tid, line in extract_technologies(tree):
                    self._add_def("technology", tid, rel, line)
                    if not self.has_loc(tid):
                        self.warn("loc.missing_tech", path, line, f"科技 {tid} 缺少本地化 key")
            elif rel.startswith("common/scripted_effects/"):
                for name, line in extract_named_blocks(tree, "scripted_effects"):
                    self._add_def("scripted_effect", name, rel, line)
            elif rel.startswith("common/scripted_triggers/"):
                for name, line in extract_named_blocks(tree, "scripted_triggers"):
                    self._add_def("scripted_trigger", name, rel, line)
            elif rel.startswith("common/on_actions/"):
                for name, line in extract_named_blocks(tree, "on_actions"):
                    self._add_def("on_action", name, rel, line)
            elif rel.startswith("common/military_industrial_organization/organizations/"):
                for name, line in extract_named_blocks(tree, "organizations"):
                    self._add_def("mio", name, rel, line)
            elif rel.startswith("common/special_projects/projects/"):
                for name, line in extract_named_blocks(tree, "special_projects"):
                    self._add_def("special_project", name, rel, line)

    def _add_def(self, kind: str, name: str, rel: str, line: int):
        self._defined.setdefault(kind, []).append((name, rel, line))

    # ---- 5. 资源 ----
    def collect_sprites(self):
        for path in self.mod.rglob("*.gfx"):
            try:
                text = path.read_text(encoding="utf-8-sig", errors="ignore")
            except OSError:
                continue
            rel = self.rel(path)
            if re.search(r"\bspriteType\d*\s*=\s*\{", text) and not rel.startswith("interface/"):
                self.warn(
                    "gfx.wrong_location",
                    path,
                    1,
                    "2D spriteType 定义应放在 interface/*.gfx；放在 gfx/ 下游戏可能不会加载（原版 2D sprite 全在 interface/）",
                )
            self.mod_sprites.update(SPRITE_RE.findall(text))
            for tex in re.findall(r'texturefile\s*=\s*"([^"]+)"', text):
                candidate = self.mod / tex.replace("\\", "/")
                if not candidate.exists():
                    game_candidate = self.game / tex.replace("\\", "/")
                    if not game_candidate.exists():
                        self.err("gfx.texture_missing", path, 1, f"texturefile 不存在：{tex}（Mod 与原版都没有）")

    def has_sprite(self, name: str) -> bool:
        if not name or name.startswith("["):
            return True  # 动态/脚本化名称
        if name in self.mod_sprites:
            return True
        if self.vanilla and name in self._vanilla_sprite_set():
            return True
        return False

    def _vanilla_sprite_set(self) -> set[str]:
        if not hasattr(self, "_vanilla_sprites_cache"):
            self._vanilla_sprites_cache = set(self.vanilla.get("sprites", []))
        return self._vanilla_sprites_cache

    def _check_icon(self, path: Path, line: int, icon: str | None, kind: str):
        if not icon:
            return
        if icon.startswith("["):
            return
        if kind == "decision":
            if icon.startswith("GFX_"):
                ok = self.has_sprite(icon)
                hint = ""
            else:
                ok = self.has_sprite(f"GFX_decision_{icon}") or self.has_sprite(icon)
                hint = f"（尝试 GFX_decision_{icon}）"
            if not ok:
                self.err("gfx.missing_decision_icon", path, line, f"决议图标找不到：{icon}{hint}")
        elif kind == "decision_category":
            if icon.startswith("GFX_"):
                ok = self.has_sprite(icon)
                hint = ""
            else:
                ok = self.has_sprite(f"GFX_decision_category_{icon}") or self.has_sprite(icon)
                hint = f"（尝试 GFX_decision_category_{icon}）"
            if not ok:
                self.err("gfx.missing_category_icon", path, line, f"决议类别图标找不到：{icon}{hint}")
        elif kind == "idea":
            # 理念 picture 通常写 token（不带 GFX_ 前缀），引擎去找 GFX_idea_<token>；
            # 也允许直接写完整 sprite 名。
            if icon.startswith("GFX_"):
                ok = self.has_sprite(icon)
                hint = ""
            else:
                ok = self.has_sprite(f"GFX_idea_{icon}") or self.has_sprite(icon)
                hint = f"（尝试 GFX_idea_{icon}）"
            if not ok:
                self.err("gfx.missing_idea_picture", path, line, f"理念图标找不到：{icon}{hint}")
        else:
            if not icon.startswith("GFX_"):
                self.warn("gfx.no_prefix", path, line, f"{kind} 图标 {icon!r} 不以 GFX_ 开头，可能无法显示")
                return
            if not self.has_sprite(icon):
                self.err("gfx.missing", path, line, f"{kind} 图标 sprite 不存在：{icon}")

    # ---- 6. 冲突 ----
    def check_conflicts(self):
        for kind, defs in self._defined.items():
            seen: dict[str, tuple[str, int]] = {}
            for name, rel, line in defs:
                if name in seen:
                    first_rel, first_line = seen[name]
                    # on_actions 允许跨文件同名（游戏会合并/覆盖），不视为重复
                    severity = "warning" if kind == "on_action" else "error"
                    self.add(severity, "id.duplicate", self.mod / rel, line, f"{kind} ID 重复：{name}（另一处 {first_rel}:{first_line}）")
                else:
                    seen[name] = (rel, line)
            if self.vanilla:
                vanilla_kind = {
                    "focus": "focus",
                    "idea": "ideas",
                    "decision": "decisions",
                    "decision_category": "decision_categories",
                    "technology": "technologies",
                    "character": "characters",
                    "event": "events",
                    "scripted_effect": "scripted_effects",
                    "on_action": "on_actions",
                    "mio": "mios",
                    "special_project": "special_projects",
                }.get(kind)
                if vanilla_kind:
                    vanilla_set = set(self.vanilla.get(vanilla_kind, []))
                    for name, rel, line in defs:
                        if name in vanilla_set:
                            self.warn("id.overrides_vanilla", self.mod / rel, line, f"{kind} ID {name} 与原版重名：会覆盖/冲突，确认这是有意为之")

    # ---- 运行 ----
    def run(self) -> Report:
        if not self.mod.is_dir():
            self.err("mod.not_found", self.mod, 1, "Mod 目录不存在")
            return self.report
        self.check_structure()
        trees = self.check_scripts()
        self.collect_sprites()
        self.check_localisation()
        self.check_content(trees)
        self.check_conflicts()
        return self.report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="HOI4 Mod 静态校验器")
    ap.add_argument("mod", type=Path, help="Mod 目录")
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--no-vanilla", action="store_true", help="跳过原版对比（不构建缓存）")
    ap.add_argument("--refresh-cache", action="store_true", help="强制重建原版索引缓存")
    args = ap.parse_args(argv)

    vanilla = None
    if not args.no_vanilla:
        if not args.game.exists():
            print(f"[warn] 找不到游戏目录 {args.game}，将跳过原版对比", file=sys.stderr)
        else:
            vanilla = load_vanilla_index(args.game, refresh=args.refresh_cache)

    linter = Linter(args.mod, args.game, vanilla)
    report = linter.run()
    data = report.summary()
    data["script_files"] = report.stats.get("script_files", 0)
    data["vanilla_index"] = bool(vanilla)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"== HOI4 Lint: {data['mod']}")
        if data["issues"]:
            current = None
            for issue in data["issues"]:
                if issue["path"] != current:
                    current = issue["path"]
                    print(f"\n{current}")
                print(f"  {issue['severity']:<7} {issue['code']:<28} line {issue['line']:<6} {issue['message']}")
        print(f"\n脚本文件: {data['script_files']} | errors: {data['errors']} | warnings: {data['warnings']} | 原版对比: {'on' if data['vanilla_index'] else 'off'}")
    return 1 if data["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

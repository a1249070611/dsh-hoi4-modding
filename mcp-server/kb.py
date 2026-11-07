"""Knowledge base for HOI4 modding.

Indexes three kinds of sources into one SQLite file:
  - game   : the vanilla install (definitions, localisation, interface, assets)
  - mod    : any mod folder, vanilla or third-party, used as reference material
  - notes  : a folder of markdown notes the user drops in

Two full-text indexes, deliberately:
  code : unicode61  -> identifiers, token-level matching for scripts
  text : trigram    -> localisation strings and notes; Chinese needs substring
                       matching, which unicode61 cannot do

Everything runs offline on local files. No network, no game process.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from typing import Any, Iterable, Iterator

import cw

# 索引库落在**家目录**下的固定相对位置，不放在插件目录里。
# 这样升级、换版本、重新解压都不会丢索引，也不会有任何本机路径被写进代码。
# 需要换位置（多环境、CI、把库放到共享盘）时设 HOI4_KB_DB。
DEFAULT_DB = os.environ.get("HOI4_KB_DB", "").strip() or os.path.join(
    os.path.expanduser("~"), ".dsh-hoi4-modding", "kb.sqlite"
)

CODE_EXT = {".txt", ".gui", ".gfx", ".asset", ".lua"}
TEXT_EXT = {".yml", ".md", ".json", ".csv"}
SKIP_DIRS = {
    ".git", ".svn", "__pycache__", "node_modules", ".vscode", ".idea",
    "dumps", "crashes", "save games", "logs", "shadercache", "gfx",
}
MAX_BODY = 24000
DOC_BODY = 400_000  # 游戏自带 documentation/*.md 单篇可达 8000+ 行，截断会丢掉大半字段
TEXT_BODY = 8000

# 原版带 10 种语言，每种约 13 万条 —— 全存下来是 130 万行、350MB、9 分钟，
# 而其中九成你永远不会查。默认只留英文与简中：写 mod 时查 key 拼写用英文，
# 汉化时查译文用简中，够用。要全量就显式传 langs=[]（空表示不过滤）。
DEFAULT_LOC_LANGS = ("english", "simp_chinese")

# 只有「目录名确实是一种语言」时才按语言跳过。不能一律按 localisation/xxx/ 过滤——
# 因为 localisation/replace/ 是覆盖语义的目录，里面是语言混合的，跳过就丢内容。
KNOWN_LANGS = frozenset({
    "english", "french", "german", "spanish", "polish", "russian", "italian",
    "braz_por", "brazilian_portuguese", "portuguese", "japanese", "korean",
    "simp_chinese", "trad_chinese", "chinese", "turkish", "hungarian", "czech",
})
LOC_DIR_RE = re.compile(r"(?i)(?:^|/)localisation/([^/]+)/")

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS sources (
    name TEXT PRIMARY KEY,
    path TEXT,
    kind TEXT,
    indexed_at REAL,
    file_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    source TEXT,
    relpath TEXT,
    ext TEXT,
    size INTEGER,
    mtime REAL,
    UNIQUE(source, relpath)
);
CREATE INDEX IF NOT EXISTS idx_files_src ON files(source);

CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY,
    name TEXT,
    kind TEXT,
    source TEXT,
    relpath TEXT,
    line INTEGER,
    extra TEXT
);
CREATE INDEX IF NOT EXISTS idx_sym_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_sym_kind ON symbols(kind);
CREATE INDEX IF NOT EXISTS idx_sym_src ON symbols(source);
-- 增量重建时每个文件都要按 (source, relpath) 删旧行。只有 source 单列索引时，
-- 每次删除都要扫该源的全部行：5145 个文件 × 12 万行 = 7 亿次行访问，
-- 一个五千文件的源就要 12 分钟。复合索引把它降到 O(1)。
CREATE INDEX IF NOT EXISTS idx_sym_src_rel ON symbols(source, relpath);

CREATE TABLE IF NOT EXISTS loc (
    id INTEGER PRIMARY KEY,
    key TEXT,
    lang TEXT,
    value TEXT,
    source TEXT,
    relpath TEXT,
    line INTEGER
);
CREATE INDEX IF NOT EXISTS idx_loc_key ON loc(key);
CREATE INDEX IF NOT EXISTS idx_loc_src_rel ON loc(source, relpath);

CREATE VIRTUAL TABLE IF NOT EXISTS code USING fts5(
    body, relpath UNINDEXED, source UNINDEXED, kind UNINDEXED, tokenize='unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS text USING fts5(
    title, body, ref UNINDEXED, source UNINDEXED, category UNINDEXED, tokenize='trigram'
);
"""


# --------------------------------------------------------------------------- #
# Connection / schema
# --------------------------------------------------------------------------- #

def connect(db_path: str = "") -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """给旧库补 enc 列。

    files.enc 记录每个文件实际用的解码（utf-8 / gbk / cp1252 / latin-1 / utf-8?）。
    旧库没有这一列：ALTER 后已有行全是空串，增量构建把它们当「解码方式未知」，
    下一轮会重读一遍——一次性成本，换来用新解码链修正旧库里所有乱码文件。
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(files)")}
    if "enc" not in cols:
        conn.execute("ALTER TABLE files ADD COLUMN enc TEXT NOT NULL DEFAULT ''")


def meta_get(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def available(db_path: str = "") -> bool:
    """True when an index file already exists. Never creates one."""
    return os.path.isfile(db_path or DEFAULT_DB)


def loc_keys(db_path: str = "") -> set[str]:
    """Every localisation key known across indexed sources.

    Used to avoid reporting a missing key that another installed mod provides —
    a translation submod in isolation looks like it is missing tens of thousands
    of keys, which is technically true and practically useless.
    """
    path = db_path or DEFAULT_DB
    if not os.path.isfile(path):
        return set()
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=15)
        rows = conn.execute("SELECT DISTINCT key FROM loc").fetchall()
        conn.close()
    except sqlite3.Error:
        return set()
    return {r[0] for r in rows if r[0]}


def names_by_kind(db_path: str = "", kinds: Iterable[str] | None = None) -> dict[str, set[str]]:
    """Load symbol names grouped by kind, for cross-reference validation."""
    path = db_path or DEFAULT_DB
    if not os.path.isfile(path):
        return {}
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
    except sqlite3.Error:
        return {}
    out: dict[str, set[str]] = {}
    sql = "SELECT kind, name FROM symbols"
    params: list[Any] = []
    if kinds:
        placeholders = ",".join("?" for _ in kinds)
        sql += f" WHERE kind IN ({placeholders})"
        params = list(kinds)
    try:
        for kind, name in conn.execute(sql, params):
            out.setdefault(kind, set()).add(name)
    except sqlite3.Error:
        conn.close()
        return {}
    conn.close()
    return out


def meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, str(value)))


# --------------------------------------------------------------------------- #
# Source discovery
# --------------------------------------------------------------------------- #

def _steam_install_dirs() -> list[str]:
    """Steam 客户端自己的安装目录。

    以前只写死 C:\\Program Files (x86)\\Steam，装在别的盘就完全探测不到——
    Steam 装在 E:\\Steam 时，游戏永远索引不进来，所有依赖原版的检查都会降级。
    所以先问注册表，再扫盘符。
    """
    found: list[str] = []

    def _add(path: str) -> None:
        # Windows 上 "e:\steam" 与 "E:\Steam" 是同一个目录，按大小写不敏感去重
        key = os.path.normcase(os.path.normpath(path))
        if key not in {os.path.normcase(os.path.normpath(p)) for p in found}:
            found.append(os.path.normpath(path))

    if os.name == "nt":
        try:
            import winreg  # type: ignore[import-not-found]

            for hive, key in (
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            ):
                for value in ("SteamPath", "InstallPath"):
                    try:
                        with winreg.OpenKey(hive, key) as k:
                            p = winreg.QueryValueEx(k, value)[0]
                    except OSError:
                        continue
                    if p and os.path.isdir(p):
                        _add(p)
        except Exception:  # pragma: no cover - 非 Windows 或注册表被锁
            pass

    # 注册表读不到时的兜底：扫盘符。成本是一次 listdir，值得。
    if os.name == "nt":
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            for rel in ("Steam", "SteamLibrary", r"Program Files (x86)\Steam"):
                cand = f"{letter}:\\" + rel
                if os.path.isdir(os.path.join(cand, "steamapps")):
                    _add(cand)

    for cand in (
        os.path.expanduser("~/.steam/steam"),
        os.path.expanduser("~/.local/share/Steam"),
        os.path.expanduser("~/Library/Application Support/Steam"),
    ):
        if os.path.isdir(cand):
            _add(cand)
    return found


def _steam_libraries() -> list[str]:
    """Best-effort Steam library discovery. Returns candidate roots."""
    roots: list[str] = []
    vdf_candidates = [os.path.join(d, "steamapps", "libraryfolders.vdf") for d in _steam_install_dirs()]
    for vdf in vdf_candidates:
        if not os.path.isfile(vdf):
            continue
        try:
            raw = open(vdf, "r", encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for match in re.finditer(r'"path"\s+"([^"]+)"', raw):
            roots.append(match.group(1).replace("\\\\", "\\"))
    return roots


def find_game_dir() -> str:
    """Locate the HOI4 install root (the folder containing common/ and events/)."""
    env = os.environ.get("HOI4_GAME", "").strip()
    if env and os.path.isdir(os.path.join(env, "common")):
        return env
    if env and os.path.isdir(os.path.join(env, "Hearts of Iron IV", "common")):
        return os.path.join(env, "Hearts of Iron IV")

    candidates: list[str] = []
    for lib in _steam_libraries():
        candidates.append(os.path.join(lib, "steamapps", "common", "Hearts of Iron IV"))
    for root in _steam_install_dirs():
        candidates.append(os.path.join(root, "steamapps", "common", "Hearts of Iron IV"))
    candidates += [
        r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV",
        r"C:\Program Files\Steam\steamapps\common\Hearts of Iron IV",
        r"D:\SteamLibrary\steamapps\common\Hearts of Iron IV",
        r"E:\SteamLibrary\steamapps\common\Hearts of Iron IV",
        os.path.expanduser("~/.steam/steam/steamapps/common/Hearts of Iron IV"),
        os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Hearts of Iron IV"),
    ]
    for cand in candidates:
        if os.path.isdir(os.path.join(cand, "common")):
            return cand
    return ""


def find_user_dir() -> str:
    env = os.environ.get("HOI4_USER_DIR", "").strip()
    if env and os.path.isdir(env):
        return env
    candidates = [
        os.path.expanduser("~/Documents/Paradox Interactive/Hearts of Iron IV"),
        os.path.expanduser("~/OneDrive/Documents/Paradox Interactive/Hearts of Iron IV"),
        os.path.expanduser("~/.local/share/Paradox Interactive/Hearts of Iron IV"),
    ]
    for cand in candidates:
        if os.path.isdir(cand):
            return cand
    return ""


def detect_sources(mods_root: str = "", include_mods: bool = False) -> list[dict]:
    """默认源 = 原版 + 参考库 + 本机笔记。

    第三方模组**默认不收**。原因：一个装了 50 个工坊模组的机器，首次索引会被拖到
    几十分钟；而且其中不少是半成品、纯汉化或改坏的包，收进来只会让检索结果变脏。
    要用必须显式要求（`only=mod`、`include_mods=true`，或在 sources.json 里点名）。
    """
    sources: list[dict] = []
    game = find_game_dir()
    if game:
        sources.append({"name": "vanilla", "path": game, "kind": "game"})

    if include_mods:
        # 优先级：调用参数 > HOI4_MODS_ROOT 环境变量 > 用户数据目录下的 mod/
        # 中间那层是为了「mod 装在前导 mods 目录」这种非默认布局，
        # 否则用户只能去改 sources.json 一个个点名。
        user_dir = find_user_dir()
        env_mods = os.environ.get("HOI4_MODS_ROOT", "").strip()
        mod_dir = mods_root or env_mods or (os.path.join(user_dir, "mod") if user_dir else "")
        if mod_dir and os.path.isdir(mod_dir):
            for entry in sorted(os.listdir(mod_dir)):
                full = os.path.join(mod_dir, entry)
                if not os.path.isdir(full):
                    continue
                if entry.startswith(".") or entry in SKIP_DIRS:
                    continue
                if not os.path.isfile(os.path.join(full, "descriptor.mod")):
                    continue
                sources.append({"name": f"mod:{entry}", "path": full, "kind": "mod"})

    here = os.path.dirname(os.path.abspath(__file__))
    for name, rel, kind in (
        ("notes", os.path.join(here, "..", "knowledge", "notes"), "notes"),
        ("refs", os.path.join(here, "..", "references"), "notes"),
    ):
        p = os.path.normpath(rel)
        if os.path.isdir(p):
            sources.append({"name": name, "path": p, "kind": kind})

    # 作者维护的远端知识库（已同步到本地缓存时才算一个源）。
    # 它排在 refs 之后，检索结果里能看出条目来自哪边。
    try:
        import remote as _remote

        rs = _remote.as_source()
        if rs:
            sources.append(rs)
    except Exception:  # pragma: no cover - 远端模块缺失不应影响本地构建
        pass
    return sources


def _resolve_source_path(raw: str) -> str:
    """把 sources.json 里的 path 解析成实际路径。

    支持三种写法，优先级从推荐到不推荐：

    1. **相对路径**：以插件根目录为基准。插件自带的 `knowledge/notes`、`references`
       就该这么写——写绝对路径的话，别人 clone 下来路径全错，而这两处路径
       对所有安装者其实是同一个相对位置。
    2. **~/ 开头**：家目录。跨机器也能用。
    3. **绝对路径**：只在确实要固定某个本机位置时才用。

    解析不出来的（盘符不存在、目录被删）原样返回，交给后面的存在性检查过滤，
    不在这里静默丢掉——否则用户只会看到「源莫名其妙少了一个」。
    """
    p = (raw or "").strip()
    if not p:
        return ""
    if p.startswith("~"):
        return os.path.normpath(os.path.expanduser(p))
    if os.path.isabs(p):
        return os.path.normpath(p)
    # 相对路径：以插件根目录（mcp-server 的上一级）为基准
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(root, p))


def load_source_config() -> list[dict]:
    """Read knowledge/sources.json if the user curated one.

    返回的每条都带解析后的绝对路径。配置文件里写相对路径是推荐做法，
    这样同一份配置在不同机器上都能用。
    """
    cfg = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "sources.json")
    )
    if os.path.isfile(cfg):
        try:
            data = json.load(open(cfg, "r", encoding="utf-8"))
            extra = data.get("sources", [])
            if extra:
                out = []
                for s in extra:
                    if not isinstance(s, dict):
                        continue
                    item = dict(s)
                    item["path"] = _resolve_source_path(str(s.get("path") or ""))
                    if item["path"]:
                        out.append(item)
                if out:
                    return out
        except (OSError, json.JSONDecodeError):
            pass
    return []


# --------------------------------------------------------------------------- #
# Symbol extraction
# --------------------------------------------------------------------------- #

TECH_MARKERS = {"start_year", "research_cost", "path", "enable_equipments", "categories", "x", "y"}
EVENT_KINDS = {
    "country_event", "news_event", "state_event",
    "unit_leader_event", "operative_leader_event",
}


def _text(block: cw.Node, key: str) -> str:
    st = cw.get_one(block, key) if isinstance(block, cw.Block) else None
    return cw.as_text(st.value) if st else ""


def _has_any(block: cw.Node, keys: tuple[str, ...]) -> bool:
    if not isinstance(block, cw.Block):
        return False
    return any(cw.get_one(block, k) is not None for k in keys)


def _char_probe(block: cw.Node) -> tuple[bool, str]:
    """角色块识别，兼容 char{...} / char{instance{...}} / TAG{char{...}} 三种布局。"""
    if not isinstance(block, cw.Block):
        return False, ""
    nm = cw.get_one(block, "name")
    if nm is not None:
        return True, cw.as_text(nm.value)
    if cw.get_one(block, "portraits") is not None:
        return True, ""
    inst = cw.get_one(block, "instance")
    if inst is not None and isinstance(inst.value, cw.Block):
        return True, _text(inst.value, "name")
    return False, ""


DOC_SCOPE_RE = re.compile(r"^\*\s*Supported Scopes?:\s*(.+)$", re.IGNORECASE)
DOC_HEAD_RE = re.compile(r"^##\s+([a-z_][a-z0-9_]*)\s*$")


def _extract_engine_docs(relpath: str, text: str) -> list[tuple[str, str, int, str]]:
    """从游戏自带 documentation/*.md 抽出 effect / trigger / modifier 名与作用域。

    这是本机能回答「这个 effect 真的存在吗、支持哪些 scope」的唯一权威来源，
    比任何教程都准。每个 `## name` 是一个词条，作用域写在正文里：
        * Supported Scopes: COUNTRY
    顶部的 `## Effects for scope X` 只是分组标题，不能用来推每条的作用域。
    """
    lower = relpath.lower()
    if lower.endswith("effects_documentation.md"):
        kind = "effect"
    elif lower.endswith("triggers_documentation.md"):
        kind = "trigger"
    elif lower.endswith("modifiers_documentation.md"):
        kind = "modifier"
    else:
        return []

    lines = text.splitlines()
    total = len(lines)
    out: list[tuple[str, str, int, str]] = []
    for i, line in enumerate(lines):
        m = DOC_HEAD_RE.match(line)
        if not m:
            continue
        scope = ""
        for j in range(i + 1, min(i + 12, total)):
            if lines[j].startswith("## "):
                break
            ms = DOC_SCOPE_RE.match(lines[j])
            if ms:
                scope = ms.group(1).strip()
                break
        out.append((m.group(1), kind, i + 1, scope))
    return out


def extract_symbols(relpath: str, text: str) -> dict[str, Any]:
    """Pull every named thing a file declares, plus asset references."""
    # 前置补一个 "/"，让下面那一串 "/xxx/" in lower 的判断对**顶层目录**也成立。
    # 不加的话 `events/AAT_Denmark.txt` 匹配不到 "/events/"，2 万条事件一条都抽不到；
    # 而 `common/national_focus/x.txt` 因为中间有斜杠能匹配上，所以这个洞只有
    # 顶层目录才暴露——静默丢数据，不报错。
    lower = "/" + relpath.lower().replace("\\", "/").lstrip("/")
    out: dict[str, Any] = {"symbols": [], "refs": [], "loc": [], "parse_errors": []}

    if lower.endswith(".yml"):
        out["loc"] = _extract_loc(relpath, text)
        return out

    if lower.endswith(".md"):
        out["symbols"] = _extract_engine_docs(relpath, text)
        return out

    if lower.endswith((".json", ".csv")):
        return out

    if lower.endswith(".lua"):
        for idx, line in enumerate(text.splitlines(), 1):
            m = re.match(r"\s*NDefines\.(\w+)\.(\w+)\s*=", line)
            if m:
                out["symbols"].append((f"NDefines.{m.group(1)}.{m.group(2)}", "define", idx, ""))
        return out

    try:
        root, errors = cw.parse(text)
    except Exception as exc:  # pragma: no cover - parser is defensive already
        out["parse_errors"].append({"message": str(exc)})
        return out
    for e in errors:
        out["parse_errors"].append(e)

    add = out["symbols"].append

    # ---- localisation-adjacent refs are collected regardless of folder ---- #
    for path, st in cw.walk(root):
        if st.key in {"texturefile", "textureFile"}:
            out["refs"].append({"kind": "texture", "target": cw.as_text(st.value)})
        elif st.key in {"mesh", "pdxmesh", "file"} and isinstance(st.value, cw.Scalar):
            val = cw.as_text(st.value)
            if val and "/" in val:
                out["refs"].append({"kind": "file", "target": val})

    if "/national_focus/" in lower:
        for tree in cw.get_all(root, "focus_tree"):
            if not isinstance(tree.value, cw.Block):
                continue
            add((_text(tree.value, "id"), "focus_tree", tree.line, ""))
            for st in cw.get_all(tree.value, "focus"):
                if isinstance(st.value, cw.Block):
                    add((_text(st.value, "id"), "focus", st.line, _text(st.value, "icon")))
            for st in cw.get_all(tree.value, "shared_focus"):
                if isinstance(st.value, cw.Block):
                    add((_text(st.value, "id"), "focus", st.line, _text(st.value, "icon")))

    elif "/ideas/" in lower:
        for ideas in cw.get_all(root, "ideas"):
            if not isinstance(ideas.value, cw.Block):
                continue
            for cat in cw.stmts(ideas.value):
                if not isinstance(cat.value, cw.Block):
                    continue
                for idea in cw.stmts(cat.value):
                    if isinstance(idea.value, cw.Block) and not idea.key.startswith("@"):
                        add((idea.key, "idea", idea.line, cat.key))

    elif "/decisions/" in lower or "/decisions_" in lower:
        for cat in cw.stmts(root):
            if not isinstance(cat.value, cw.Block):
                continue
            if not any(
                s.key in {"icon", "allowed", "visible", "available", "on_map_mode", "priority"}
                for s in cw.stmts(cat.value)
            ):
                continue
            add((cat.key, "decision_category", cat.line, ""))
            for dec in cw.stmts(cat.value):
                if isinstance(dec.value, cw.Block) and dec.key not in {
                    "allowed", "visible", "available", "target_trigger", "target_root_trigger"
                }:
                    add((dec.key, "decision", dec.line, _text(dec.value, "icon")))

    elif "/technolog" in lower:
        for techs in cw.get_all(root, "technologies"):
            if not isinstance(techs.value, cw.Block):
                continue
            for folder in cw.stmts(techs.value):
                if not isinstance(folder.value, cw.Block):
                    continue
                has_marker = any(s.key in TECH_MARKERS for s in cw.stmts(folder.value))
                if has_marker:
                    add((folder.key, "tech", folder.line, ""))
                    continue
                for tech in cw.stmts(folder.value):
                    if isinstance(tech.value, cw.Block):
                        add((tech.key, "tech", tech.line, folder.key))

    elif "/scripted_effects/" in lower:
        for st in cw.stmts(root):
            if isinstance(st.value, cw.Block):
                add((st.key, "scripted_effect", st.line, ""))
    elif "/scripted_triggers/" in lower:
        for st in cw.stmts(root):
            if isinstance(st.value, cw.Block):
                add((st.key, "scripted_trigger", st.line, ""))
    elif "/scripted_guis/" in lower:
        for st in cw.stmts(root):
            if isinstance(st.value, cw.Block):
                add((st.key, "scripted_gui", st.line, ""))
    elif "/characters/" in lower:
        for chars in cw.get_all(root, "characters"):
            if not isinstance(chars.value, cw.Block):
                continue
            for child in cw.stmts(chars.value):
                if not isinstance(child.value, cw.Block):
                    continue
                ok, nm = _char_probe(child.value)
                if ok:
                    add((child.key, "character", child.line, nm))
                    continue
                for ch in cw.stmts(child.value):
                    ok2, nm2 = _char_probe(ch.value)
                    if ok2:
                        add((ch.key, "character", ch.line, nm2))
    elif "/on_actions/" in lower:
        for oa in cw.get_all(root, "on_actions"):
            if isinstance(oa.value, cw.Block):
                for st in cw.stmts(oa.value):
                    add((st.key, "on_action", st.line, ""))
    elif "/events/" in lower:
        for kind in EVENT_KINDS:
            for st in cw.get_all(root, kind):
                if isinstance(st.value, cw.Block):
                    add((_text(st.value, "id"), "event", st.line, kind))

    elif lower.endswith(".gfx"):
        for path, st in cw.walk(root):
            if st.key == "name" and isinstance(st.value, cw.Scalar):
                val = cw.as_text(st.value)
                if val.startswith("GFX_"):
                    add((val, "sprite", st.line, ""))
    elif lower.endswith(".asset"):
        for st in cw.get_all(root, "entity"):
            if isinstance(st.value, cw.Block):
                add((_text(st.value, "name"), "entity", st.line, ""))
    elif lower.endswith(".gui"):
        # 只收顶层窗口名。子控件名动辄上万个，收进来会把符号表淹掉。
        roots = cw.get_all(root, "guiTypes")
        containers = roots if roots else [cw.Stmt("__root__", "=", root, 0)]
        for holder in containers:
            if not isinstance(holder.value, cw.Block):
                continue
            for win in cw.stmts(holder.value):
                if not isinstance(win.value, cw.Block):
                    continue
                nm = _text(win.value, "name")
                if nm:
                    add((nm, "gui_window", win.line, win.key))

    out["symbols"] = [s for s in out["symbols"] if s[0]]
    return out


LOC_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*\d*\s+"(.*)"\s*$')
LOC_HEADER_RE = re.compile(r"^\s*l_([a-z_]+)\s*:\s*$")


def _extract_loc(relpath: str, text: str) -> list[tuple[str, str, str, int]]:
    lang = "english"
    rows: list[tuple[str, str, str, int]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        m = LOC_HEADER_RE.match(line)
        if m:
            lang = m.group(1)
            continue
        e = LOC_ENTRY_RE.match(line)
        if e:
            rows.append((e.group(1), lang, e.group(2), lineno))
    return rows


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

def _iter_files(root: str) -> Iterator[tuple[str, str]]:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in CODE_EXT or ext in TEXT_EXT:
                full = os.path.join(base, name)
                yield full, os.path.relpath(full, root).replace("\\", "/")


# utf-8 失败后按顺序尝试的编码。GBK 在 cp1252 之前：GBK 双字节序列几乎总能被
# cp1252 「成功」解码成乱码，cp1252 放前面会把中文文件吃掉；latin-1 全字节可解，
# 放最后兜底，保证永不走到 errors="replace"。
DECODE_FALLBACKS = ("gbk", "cp1252", "latin-1")


def _decode(raw: bytes) -> tuple[str, str, int]:
    """解码一个待索引文件，返回 (text, encoding, n_replaced)。

    之前一律 utf-8-sig + errors="replace"：GBK 文件整篇变 U+FFFD 乱码照常进索引，
    而且增量构建看到 size/mtime 没变就跳过，永远不会重试。现在：

    1. 先按 utf-8-sig 宽松解码并数 U+FFFD——0 个就是干净的 utf-8，到此为止；
    2. 乱码既多（≥8 处）又密（占比 > 0.5%）说明整个文件大概率不是 UTF-8
       （纯 GBK 中文文件约一半字节非法），按链 gbk → cp1252 → latin-1 严格重试。
       **两个条件缺一不可**：只有占比没有下限的话，短文件坏一个字节就会触发
       整文件换编码——而 UTF-8 中文经 GBK 解码「几乎总能成功」（UTF-8 连续字节
       大多落在 GBK 尾字节区），结果是拿全文乱码换掉一处 U+FFFD；
    3. 只有零星坏字节时保留 utf-8 宽松结果并记为 `utf-8?`，宁可留几个 U+FFFD
       也不赌一次整篇错解。
    """
    text = raw.decode("utf-8-sig", errors="replace")
    bad = text.count("\ufffd")
    if not bad:
        return text, "utf-8", 0
    if bad >= 8 and bad * 200 > len(text):  # 乱码又多又密 → 整文件换编码重试
        body = raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw
        for enc in DECODE_FALLBACKS:
            try:
                return body.decode(enc), enc, 0
            except (UnicodeDecodeError, ValueError):
                continue
    return text, "utf-8?", bad


def build(
    sources: list[dict],
    db_path: str = "",
    incremental: bool = True,
    max_files_per_source: int = 0,
    progress_every: int = 0,
    loc_langs: Iterable[str] | None = None,
) -> dict[str, Any]:
    conn = connect(db_path)
    conn.execute("PRAGMA synchronous=OFF")  # 构建期换速度，崩溃最多重跑一次
    conn.execute("PRAGMA cache_size=-64000")
    report: dict[str, Any] = {"sources": [], "started": time.strftime("%Y-%m-%d %H:%M:%S")}

    keep_langs = set(DEFAULT_LOC_LANGS if loc_langs is None else loc_langs)
    report["loc_langs"] = sorted(keep_langs) if keep_langs else "all"

    for src in sources:
        name, path, kind = src.get("name", ""), src.get("path", ""), src.get("kind", "mod")
        if not name or not os.path.isdir(path):
            report["sources"].append({"name": name, "error": f"目录不存在: {path}"})
            continue

        known: dict[str, tuple[int, float, str]] = {}
        # 全量重建也要读 known：stale 清理（删除已从磁盘消失的文件行）对
        # 两种模式同样必要。只放在 incremental 分支里的话，全量重建不清
        # ghost，删掉的文件永久残留在五张表里继续被检索命中。
        for relpath, size, mtime, enc in conn.execute(
            "SELECT relpath, size, mtime, enc FROM files WHERE source=?", (name,)
        ):
            known[relpath] = (size, mtime, enc)

        # 这个源已经索引过的文件集合。用来决定「要不要先删旧行」：
        # 首次索引时一个都不用删（表里本来就没有），而 FTS5 的
        # `DELETE ... WHERE source=? AND relpath=?` 在 UNINDEXED 列上是全表扫描，
        # 每个新文件都跑一次等于把构建搞成 O(n²)。
        existing = {r for (r,) in conn.execute("SELECT relpath FROM files WHERE source=?", (name,))}

        added = updated = skipped = skipped_lang = 0
        symbols_total = loc_total = 0
        decode_stats: dict[str, int] = {}
        decode_issues: list[str] = []
        seen: set[str] = set()
        started = time.time()

        rows: list[tuple] = []
        truncated = False
        for idx, (full, relpath) in enumerate(_iter_files(path)):
            if max_files_per_source and idx >= max_files_per_source:
                truncated = True
                break
            if progress_every and idx and idx % progress_every == 0:
                print(f"  {name}: {idx} files...", flush=True)
            if keep_langs:
                m = LOC_DIR_RE.search(relpath)
                if m and m.group(1).lower() in KNOWN_LANGS and m.group(1).lower() not in keep_langs:
                    skipped_lang += 1
                    continue
            try:
                st = os.stat(full)
            except OSError:
                continue
            seen.add(relpath)
            prev = known.get(relpath)
            # prev[2] 是上次的解码标记：为空 = 迁移前的旧行，解码方式未知，
            # 不跳过——重读一遍用新解码链定案，旧库里的乱码文件由此获得一次
            # 自愈机会。utf-8?（个别坏字节）仍可跳过：size/mtime 没变的话
            # 重读结果相同，等文件真被改了自然重新索引。
            if (
                incremental
                and prev
                and prev[0] == st.st_size
                and abs(prev[1] - st.st_mtime) < 1
                and prev[2]
            ):
                skipped += 1
                continue

            try:
                raw = open(full, "rb").read()
            except OSError:
                continue
            text, enc_used, n_bad = _decode(raw)
            decode_stats[enc_used] = decode_stats.get(enc_used, 0) + 1
            if enc_used == "utf-8?" and n_bad:
                decode_issues.append(f"{relpath} ({n_bad} 处乱码)")
            ext = os.path.splitext(relpath)[1].lower()

            # 游戏自带的 documentation/*.md 与 common/**/_documentation.md 是字段级
            # 最权威的来源，但正文是英文、且单篇能到 8000 行。走 code(unicode61)
            # 索引而不是 trigram：英文标识符精确匹配更准，也不用为 40 万字符建 trigram。
            # 用户自己的笔记是中文，仍走 text(trigram) 以便子串匹配。
            is_md = ext == ".md"
            is_doc = is_md and kind != "notes"
            # .md 也要抽：游戏自带的 documentation/*.md 里每个 `## name` 就是一条
            # effect/trigger 定义，是判断「这个 effect 真的存在吗」的唯一权威来源。
            extracted = extract_symbols(relpath, text)

            is_code = ext in CODE_EXT or is_doc
            if relpath in existing:
                conn.execute("DELETE FROM symbols WHERE source=? AND relpath=?", (name, relpath))
                conn.execute("DELETE FROM loc WHERE source=? AND relpath=?", (name, relpath))
                conn.execute("DELETE FROM text WHERE source=? AND ref=?", (name, relpath))
                conn.execute("DELETE FROM code WHERE source=? AND relpath=?", (name, relpath))

            conn.execute(
                "INSERT OR REPLACE INTO files(source,relpath,ext,size,mtime,enc) VALUES(?,?,?,?,?,?)",
                (name, relpath, ext, st.st_size, st.st_mtime, enc_used),
            )

            if is_code:
                cap = DOC_BODY if is_md else MAX_BODY
                conn.execute(
                    "INSERT INTO code(body,relpath,source,kind) VALUES(?,?,?,?)",
                    (text[:cap], relpath, name, "md" if is_md else ext.lstrip(".")),
                )
            elif ext in TEXT_EXT and ext != ".yml":
                # .yml 不进 trigram：十万级词条逐条建索引会把全量构建拖到十几分钟。
                # 本地化检索改走 loc 表的子串匹配，见 search()。
                conn.execute(
                    "INSERT INTO text(title,body,ref,source,category) VALUES(?,?,?,?,?)",
                    (os.path.basename(relpath), text[:TEXT_BODY], relpath, name,
                     "doc" if kind == "notes" else "loc"),
                )

            if extracted["symbols"]:
                conn.executemany(
                    "INSERT INTO symbols(name,kind,source,relpath,line,extra) VALUES(?,?,?,?,?,?)",
                    [(s[0], s[1], name, relpath, s[2], s[3]) for s in extracted["symbols"]],
                )
                symbols_total += len(extracted["symbols"])

            if extracted["loc"]:
                loc_rows = extracted["loc"]
                if keep_langs:
                    loc_rows = [r for r in loc_rows if r[1] in keep_langs]
                if loc_rows:
                    conn.executemany(
                        "INSERT INTO loc(key,lang,value,source,relpath,line) VALUES(?,?,?,?,?,?)",
                        [(k, lg, v, name, relpath, n) for k, lg, v, n in loc_rows],
                    )
                    loc_total += len(loc_rows)

            if prev:
                updated += 1
            else:
                added += 1

        if not truncated:
            # stale = 已索引但本轮没在磁盘上见到的文件。max_files_per_source
            # 截断时 seen 只装了前 N 个，直接删会把上限之后的全部行误删——
            # 试跑一次就把完整索引毁掉，所以截断时跳过清理。
            stale = set(known) - seen
            for relpath in stale:
                conn.execute("DELETE FROM files WHERE source=? AND relpath=?", (name, relpath))
                conn.execute("DELETE FROM symbols WHERE source=? AND relpath=?", (name, relpath))
                conn.execute("DELETE FROM loc WHERE source=? AND relpath=?", (name, relpath))
                conn.execute("DELETE FROM text WHERE source=? AND ref=?", (name, relpath))
                conn.execute("DELETE FROM code WHERE source=? AND relpath=?", (name, relpath))
        stale_removed = len(set(known) - seen) if not truncated else 0

        conn.execute(
            "INSERT OR REPLACE INTO sources(name,path,kind,indexed_at,file_count) VALUES(?,?,?,?,?)",
            (name, path, kind, time.time(), len(seen)),
        )
        conn.commit()

        report["sources"].append(
            {
                "name": name,
                "kind": kind,
                "path": path,
                "files": len(seen),
                "added": added,
                "updated": updated,
                "unchanged": skipped,
                "skipped_other_langs": skipped_lang,
                "stale_removed": stale_removed,
                "stale_skipped": truncated,
                "symbols": symbols_total,
                "loc_entries": loc_total,
                "decoding": decode_stats,
                "decode_issues": decode_issues[:20],
                "seconds": round(time.time() - started, 2),
            }
        )

    meta_set(conn, "last_build", report["started"])
    conn.commit()
    report["total_symbols"] = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    report["db_path"] = db_path or DEFAULT_DB
    conn.close()
    return report


# --------------------------------------------------------------------------- #
# Query
# --------------------------------------------------------------------------- #

def _tokens(query: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+", query)


def _zh_ngrams(s: str, n: int = 2) -> list[str]:
    """把无空格的中文串切成 n 字滑窗。

    中文不写空格，整串当短语等于要求这几个字在原文里**逐字相邻**。
    「国策树坐标」五个字连在一起在语料里几乎不存在，于是必然 0 命中——
    而用户的意思是「同时讲国策树和坐标的文档」。

    取 2 字而不是 3 字：3 字滑窗会把「坐标」这种二字词整段切掉，
    只留下「策树坐」这类跨词无意义片段。2 字覆盖所有二字词，
    代价是「的的」这类噪声，所以只用于打分、不用于筛选。
    """
    s = re.sub(r"[^\u4e00-\u9fff]", "", s)
    if len(s) < n:
        return [s] if s else []
    return [s[i:i + n] for i in range(len(s) - n + 1)]


def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _like(s: str) -> str:
    """LIKE 模式串转义。% _ \\ 是通配符与转义符，loc key 大量含下划线，
    不转义时 GER_autobahn 的 _ 被当任意单字符，把不相干的键一起召回——
    是召回噪声，不是相关性。所有 LIKE 参数必须先过这里，SQL 侧配 ESCAPE '\\'。"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _authority(source: str, relpath: str) -> str:
    """给检索结果标出处等级，冲突时按这个顺序取信。

    游戏自带文档 > 域级 _documentation.md > 原版实例文件。
    没标 = 普通脚本或第三方 mod，当参考不当结论。
    """
    p = relpath.replace("\\", "/").lower()
    if p.startswith("documentation/"):
        return "game-doc"          # documentation/effects_documentation.md 等，字段级权威
    if p.endswith("_documentation.md") or "/documentation.md" in p:
        return "domain-doc"        # common/**/_documentation.md，域级权威
    if source == "vanilla" or source.startswith("vanilla"):
        return "vanilla-instance"  # 原版实例，没有文档的域只能靠它
    return ""


PLATFORM_SOURCES = ("remote",)


def _tier(source: str) -> str:
    """哪些源算"平台资料库"。

    平台库 = 作者维护、不定期更新到开源平台的那份（同步到本地缓存后源名叫 remote）。
    其余（原版、随包参考库、本机笔记、模组）都算本地库。
    """
    return "platform" if source in PLATFORM_SOURCES else "local"


def _platform_state() -> str:
    """平台库处于哪种状态：'ready' 已同步 / 'configured' 配了仓库但没同步 / 'unconfigured' 没配。

    这个区分是为了让提示语准确：没配仓库时叫用户去跑 pull，跑了一定失败。
    """
    try:
        import remote as _remote
    except Exception:
        return "unconfigured"
    cfg = None
    try:
        cfg = _remote.load_config()
    except Exception:
        pass
    if not cfg:
        return "unconfigured"
    try:
        return "ready" if _remote.as_source() else "configured"
    except Exception:
        return "configured"


def _query_hits(
    conn,
    query: str,
    limit: int,
    kind: str,
    sources: list[str],
    include_text: bool,
) -> list[dict]:
    """在指定的源集合里跑一次完整检索（代码 / 词条 / 文档）。"""
    toks = _tokens(query)
    hits: list[dict] = []
    src_sql = ""
    base_params: list = []
    if sources:
        src_sql = " AND source IN (" + ",".join("?" for _ in sources) + ")"
        base_params = list(sources)

    if toks:
        expr = " AND ".join(f'"{t}"' for t in toks)
        sql = (
            "SELECT relpath, source, kind, snippet(code,0,'[',']',' … ',14) AS sn, rank "
            "FROM code WHERE code MATCH ?" + src_sql
        )
        params: list = [expr] + base_params
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        try:
            for relpath, src, kd, sn, rank in conn.execute(sql, params):
                hit = {
                    "type": "code", "source": src, "relpath": relpath, "snippet": sn,
                    "score": round(-rank, 4) if rank else 0, "kind": kd,
                    "tier": _tier(src),
                }
                tier = _authority(src, relpath)
                if tier:
                    hit["authority"] = tier
                hits.append(hit)
        except sqlite3.OperationalError:
            pass

        # 官方文档优先露头：默认按 FTS rank 排，documentation/*.md 常被几千个
        # 脚本文件挤到 limit 之外，agent 就会以为「没有文档」。
        if not kind:
            try:
                doc_sql = (
                    "SELECT relpath, source, kind, snippet(code,0,'[',']',' … ',14) AS sn "
                    "FROM code WHERE code MATCH ? AND kind = 'md'" + src_sql + " LIMIT 2"
                )
                for relpath, src, kd, sn in conn.execute(doc_sql, [expr] + base_params):
                    hits.insert(0, {
                        "type": "code", "source": src, "relpath": relpath, "snippet": sn,
                        "score": 0, "kind": kd, "tier": _tier(src),
                        "authority": _authority(src, relpath),
                    })
            except sqlite3.OperationalError:
                pass

    if include_text and len(query.strip()) >= 2:
        like = f"%{_like(query.strip())}%"
        try:
            loc_sql = (
                "SELECT key, lang, value, source, relpath, line FROM loc "
                "WHERE (key LIKE ? ESCAPE '\\' OR value LIKE ? ESCAPE '\\')" + src_sql
            )
            params = [like, like] + base_params + [limit]
            loc_sql += " LIMIT ?"
            for key, lang, value, src, relpath, line in conn.execute(loc_sql, params):
                hits.append({
                    "type": "loc", "source": src, "relpath": relpath, "line": line,
                    "title": key, "lang": lang, "snippet": (value or "")[:200],
                    "tier": _tier(src),
                })
        except sqlite3.OperationalError:
            pass

        # trigram 少于 3 字符查不到（"前置""方框"），多词又要求字面相邻，
        # 这两种退回 LIKE 逐词处理。文档表只有百来行，全扫比让人猜划算。
        safe = query.strip().replace('"', " ")
        # 切词：中文连串与 ASCII 词各自成段。之前先用 [A-Za-z0-9_] 抽 ASCII、
        # 再把剩余中文整串切滑窗，混排查询「focus树坐标」的 focus 约束在
        # text 路径静默消失，退化成纯中文查询。
        terms = [t for t in re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9_.\-]+", safe) if len(t) > 1]
        zh_groups: list[list[str]] = []  # 每个中文段一组 2 字滑窗，组内 OR
        ascii_terms: list[str] = []
        for t in terms:
            if _has_cjk(t):
                zh_groups.append(_zh_ngrams(t, 2))
            else:
                ascii_terms.append(t)

        try:
            if zh_groups:
                # 中文组内 OR（任一滑窗命中即算），组间 AND；ASCII 词是精确
                # 约束，单独一组 AND 进去。整体加括号：不加的话
                # `A OR B AND source IN (...)` 里 AND 优先级更高，source 过滤
                # 只绑到最后一段，其余段越权命中——踩过一次。
                def _zh_rows(zgs: list[list[str]], ats: list[str]) -> list[tuple]:
                    parts = [
                        "("
                        + " OR ".join(
                            "(body LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')" for _ in g
                        )
                        + ")"
                        for g in zgs
                    ]
                    parts += [
                        "(body LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')" for _ in ats
                    ]
                    where = "(" + " AND ".join(parts) + ")"
                    params: list = []
                    for g in zgs:
                        for bit in g:
                            params += [f"%{_like(bit)}%", f"%{_like(bit)}%"]
                    for t in ats:
                        params += [f"%{_like(t)}%", f"%{_like(t)}%"]
                    params += base_params
                    return conn.execute(
                        f"SELECT title, body, ref, source, category FROM text WHERE {where}"
                        + src_sql,
                        params,
                    ).fetchall()

                rows = _zh_rows(zh_groups, ascii_terms)
                if not rows and ascii_terms:
                    # ASCII 约束太严（文档可能只写了中文说法）→ 退回纯中文。
                    # 至少不比旧版差：旧版是直接把 ASCII 段丢掉。
                    rows = _zh_rows(zh_groups, [])
                # 纯词频打分：全部片段（滑窗 + ASCII 词）的出现总次数。
                # 实测排序质量足够（国策树坐标 → focus-trees.md，本地化编码
                # → localisation.md）。不加标题加权——title 与 ref 都是英文
                # 文件名，中文查询命不中，加了也是 0，反而误导后来的人以为
                # 有主题加权。
                scored = []
                bits_all = [b for g in zh_groups for b in g] + ascii_terms
                for title, body, ref, src, category in rows:
                    blob = f"{title or ''} {body or ''}"
                    score = sum(blob.count(t) for t in bits_all)
                    scored.append((score, title, body, ref, src, category))
                scored.sort(key=lambda x: -x[0])
                rows = [x[1:] for x in scored[:limit]]
            elif len(ascii_terms) == 1 and len(ascii_terms[0]) >= 3:
                rows = conn.execute(
                    "SELECT title, body, ref, source, category FROM text WHERE text MATCH ?"
                    + src_sql + " LIMIT ?",
                    [f'"{safe}"'] + base_params + [limit],
                ).fetchall()
            elif ascii_terms:
                # 同样整体加括号。这里是 AND，本来优先级就比 OR 高，暂时不会出错，
                # 但和上面那条保持一致，将来改成 OR 时不会再踩同一个坑。
                where = (
                    "("
                    + " AND ".join(
                        "(body LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\')"
                        for _ in ascii_terms
                    )
                    + ")"
                )
                params = []
                for t in ascii_terms:
                    params += [f"%{_like(t)}%", f"%{_like(t)}%"]
                params += base_params + [limit]
                rows = conn.execute(
                    f"SELECT title, body, ref, source, category FROM text WHERE {where}"
                    + src_sql + " LIMIT ?",
                    params,
                ).fetchall()
            else:
                rows = []
            for title, body, ref, src, category in rows:
                hits.append({
                    "type": category, "source": src, "relpath": ref, "title": title,
                    "snippet": (body or "")[:200], "tier": _tier(src),
                })
        except sqlite3.OperationalError:
            pass

    # 代码与文档优先，本地化词条垫底；同层内平台库优先于本地库。
    prio = {"code": 0, "doc": 1, "note": 1, "loc": 2}
    hits.sort(key=lambda h: (0 if h.get("tier") == "platform" else 1, prio.get(h.get("type"), 1)))
    return hits


def search(
    query: str,
    db_path: str = "",
    limit: int = 20,
    kind: str = "",
    source: str = "",
    include_text: bool = True,
    scope: str = "auto",
) -> dict[str, Any]:
    """两级资料库检索。默认平台库优先。

    scope:
      auto     先查平台库；有命中就只返平台库的（并说明本地库没查），没命中才退到本地
      platform 只查平台库
      local    只查本地库
      all      两级一起查，平台库排前面
    """
    conn = connect(db_path)
    have_sources = {r[0] for r in conn.execute("SELECT DISTINCT source FROM files")}
    platform = [s for s in PLATFORM_SOURCES if s in have_sources]
    local = sorted(have_sources - set(PLATFORM_SOURCES))

    if source:
        platform = [source] if source in platform else []
        local = [source] if source in local else []

    scope = (scope or "auto").lower()
    if scope == "platform":
        buckets = [("platform", platform)]
    elif scope == "local":
        buckets = [("local", local)]
    elif scope == "all":
        buckets = [("platform", platform), ("local", local)]
    else:
        buckets = [("platform", platform), ("local", local)]

    out_hits: list[dict] = []
    answered_from = None
    tiers: dict[str, int] = {}
    message = ""

    for idx, (tier, srcs) in enumerate(buckets):
        if not srcs:
            tiers[tier] = 0
            continue
        got = _query_hits(conn, query, limit, kind, srcs, include_text)
        tiers[tier] = len(got)
        if got:
            out_hits.extend(got)
            if answered_from is None:
                answered_from = tier
            if scope == "auto":
                # auto 的语义是「平台命中就收工」；all 才继续往下叠。
                if tier == "platform" and idx + 1 < len(buckets):
                    message = ("平台资料库命中 %d 条，已返回；本地库未检索。"
                               "需要一起看就传 scope=all。" % len(got))
                break
        elif scope == "auto" and tier == "platform" and idx + 1 < len(buckets):
            message = "平台资料库没有命中，以下来自本地库。"

    if scope == "all" and out_hits:
        prio2 = {"code": 0, "doc": 1, "note": 1, "loc": 2}
        out_hits.sort(key=lambda h: (0 if h.get("tier") == "platform" else 1, prio2.get(h.get("type"), 1)))

    conn.close()
    if scope in ("auto", "platform") and not platform:
        # 平台库不可用，这时候「本地命中」不能让人以为是平台给的。
        # 还要区分「没配仓库」和「配了没同步」——前者叫用户去 pull 是跑不通的。
        state = _platform_state()
        if state == "unconfigured":
            prefix = ("平台资料库未配置（knowledge/remote.json 的 repo 是空的，"
                      "本插件当前只带本地两级资料库）")
            tip = "配好 repo 后跑 kiant_hoi4_kb_sync action=pull 才会多出平台层。"
        elif state == "configured":
            prefix = "平台资料库已配置但还没同步过"
            tip = "跑一次 kiant_hoi4_kb_sync action=pull 即可拉取。"
        else:
            prefix = "平台资料库没有可用条目"
            tip = "跑 kiant_hoi4_kb_sync action=status 看看远端状态。"

        if scope == "auto" and out_hits:
            message = f"{prefix}，以下结果全部来自本地库。{tip}"
        elif not out_hits:
            message = f"{prefix}。{tip}也可以先用 scope=local 只查本地库。"

    return {
        "query": query,
        "scope": scope,
        "answered_from": answered_from,
        "tiers": tiers,
        "message": message,
        "hit_count": len(out_hits),
        "hits": out_hits[:limit],
    }


def lookup(kind: str, db_path: str = "", tag: str = "", limit: int = 3, context_lines: int = 30) -> dict[str, Any]:
    """Return real examples of a content kind, with a code excerpt."""
    conn = connect(db_path)
    sql = (
        "SELECT DISTINCT source, relpath FROM symbols WHERE kind=? "
        + ("AND name LIKE ? ESCAPE '\\' " if tag else "")
        + "ORDER BY source, relpath LIMIT ?"
    )
    params: list[Any] = [kind]
    if tag:
        params.append(f"%{_like(tag)}%")
    params.append(limit * 4)

    picked: list[dict] = []
    seen_files: set[tuple[str, str]] = set()
    for source, relpath in conn.execute(sql, params):
        if (source, relpath) in seen_files:
            continue
        seen_files.add((source, relpath))
        row = conn.execute(
            "SELECT line FROM symbols WHERE kind=? AND source=? AND relpath=? LIMIT 1",
            (kind, source, relpath),
        ).fetchone()
        line = row[0] if row else 1
        body_row = conn.execute(
            "SELECT body FROM code WHERE source=? AND relpath=?", (source, relpath)
        ).fetchone()
        excerpt = ""
        if body_row:
            lines = body_row[0].splitlines()
            start = max(0, line - 3)
            excerpt = "\n".join(lines[start : start + context_lines])
        names = [
            n for (n,) in conn.execute(
                "SELECT name FROM symbols WHERE kind=? AND source=? AND relpath=? LIMIT 12",
                (kind, source, relpath),
            )
        ]
        picked.append(
            {"source": source, "relpath": relpath, "line": line, "symbols": names, "excerpt": excerpt}
        )
        if len(picked) >= limit:
            break

    total = conn.execute("SELECT COUNT(*) FROM symbols WHERE kind=?", (kind,)).fetchone()[0]
    by_kind = {
        k: c
        for k, c in conn.execute(
            "SELECT kind, COUNT(*) FROM symbols GROUP BY kind ORDER BY COUNT(*) DESC"
        )
    }
    conn.close()
    return {
        "kind": kind,
        "total_symbols_of_kind": total,
        "examples": picked,
        "available_kinds": by_kind,
    }


def find_symbol(name: str, db_path: str = "", limit: int = 40) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT kind, source, relpath, line, extra FROM symbols WHERE name=? LIMIT ?",
        (name, limit),
    ).fetchall()
    locs = conn.execute(
        "SELECT lang, value, source, relpath, line FROM loc WHERE key=? LIMIT 20", (name,)
    ).fetchall()
    conn.close()
    return {
        "name": name,
        "definitions": [
            {"kind": k, "source": s, "relpath": r, "line": ln, "extra": e}
            for k, s, r, ln, e in rows
        ],
        "localisation": [
            {"lang": la, "value": v, "source": s, "relpath": r, "line": ln}
            for la, v, s, r, ln in locs
        ],
        "found": bool(rows or locs),
    }


def stats(db_path: str = "") -> dict[str, Any]:
    conn = connect(db_path)
    _srcs = [
        (n, k, p, c, t)
        for n, k, p, c, t in conn.execute(
            "SELECT name, kind, path, file_count, indexed_at FROM sources ORDER BY kind, name"
        )
    ]
    out: dict[str, Any] = {
        "tiers": {
            "platform": [n for n, *_ in _srcs if _tier(n) == "platform"],
            "local": [n for n, *_ in _srcs if _tier(n) == "local"],
        },
        "db_path": db_path or DEFAULT_DB,
        "sources": [
            {"name": n, "kind": k, "path": p, "files": c, "tier": _tier(n),
             "indexed_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(t)) if t else None}
            for n, k, p, c, t in _srcs
        ],
        "symbols_by_kind": {
            k: c for k, c in conn.execute(
                "SELECT kind, COUNT(*) FROM symbols GROUP BY kind ORDER BY COUNT(*) DESC"
            )
        },
        "loc_entries": conn.execute("SELECT COUNT(*) FROM loc").fetchone()[0],
        "code_docs": conn.execute("SELECT COUNT(*) FROM code").fetchone()[0],
        "text_docs": conn.execute("SELECT COUNT(*) FROM text").fetchone()[0],
        "last_build": meta_get(conn, "last_build"),
    }
    conn.close()
    return out


# --------------------------------------------------------------------------- #
# Notes
# --------------------------------------------------------------------------- #

def add_note(title: str, body: str, tag: str = "", db_path: str = "") -> dict[str, Any]:
    conn = connect(db_path)
    conn.execute(
        "INSERT INTO text(title,body,ref,source,category) VALUES(?,?,?,?,?)",
        (title, body, f"note://{int(time.time())}", "notes", "note"),
    )
    if tag:
        conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (f"note_tag:{title}", tag))
    conn.commit()
    conn.close()
    return {"ok": True, "title": title, "chars": len(body), "tag": tag}


def list_notes(db_path: str = "", limit: int = 50) -> dict[str, Any]:
    conn = connect(db_path)
    rows = conn.execute(
        "SELECT title, body, ref FROM text WHERE category='note' ORDER BY rowid DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return {
        "count": len(rows),
        "notes": [{"title": t, "preview": (b or "")[:120], "ref": r} for t, b, r in rows],
    }

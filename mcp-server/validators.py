"""Pluggable content validators.

Each validator owns one content type (technology, assets, UI, on_actions, ...).
They all share one context and return the same issue shape, so adding a new
content type is three steps: write a function, decorate it, done.

Design rule: a validator must never produce a false positive just because the
vanilla index is missing. When it cannot verify something without external
knowledge, it says so explicitly instead of guessing.
"""

from __future__ import annotations

import difflib
import os
import re
from typing import Any, Callable

import cw

# --------------------------------------------------------------------------- #
# Context
# --------------------------------------------------------------------------- #

class Ctx:
    """Everything a validator needs, gathered once."""

    def __init__(self, mod_root: str, definitions: dict, loc_keys: dict, kb_names: dict | None = None,
                 vanilla_root: str = "", external_loc: set | None = None,
                 has_dependencies: bool = False, loc_coverage: float = 100.0,
                 loc_partial: bool = False, assume_complete: bool = True) -> None:
        self.mod_root = mod_root
        self.definitions = definitions
        self.loc_keys = loc_keys
        # kb_names: {kind: set(names)} from the knowledge base, or None
        self.kb_names = kb_names
        self.vanilla_root = vanilla_root
        # 被依赖模组/base mod 提供的本地化键。汉化子模组只翻译一部分，
        # 缺的键由父模组补，不能算错误。
        self.external_loc = external_loc or set()
        self.has_dependencies = has_dependencies
        self.loc_coverage = loc_coverage
        self.loc_partial = loc_partial
        # 光「索引了原版」不足以判 error：模组声明了 replace_path 时原版那一整个
        # 目录按设计就不加载，声明了 dependencies 时内容由父模组提供。
        # 这两种情况下「原版里没有」只说明「不在原版」，不能推断「不存在」。
        self.assume_complete = assume_complete
        self._cache: dict[str, Any] = {}

    @property
    def have_vanilla(self) -> bool:
        """能不能拿「原版里没有」当作「确实不存在」的证据。"""
        return bool(self.vanilla_root) and self.assume_complete

    # -- helpers ---------------------------------------------------------- #

    def rel(self, path: str) -> str:
        try:
            return os.path.relpath(path, self.mod_root).replace("\\", "/")
        except ValueError:
            return path.replace("\\", "/")

    def mod_file(self, relpath: str) -> str:
        return os.path.join(self.mod_root, relpath.replace("/", os.sep))

    def has_external(self) -> bool:
        return bool(self.kb_names)

    def loc_known(self, key: str) -> bool:
        return key in self.loc_keys or key in self.external_loc

    def loc_level(self, default: str = "error") -> str:
        """缺本地化键该报多重。三级判断，宁可少报也不误报：

        - 声明了 dependencies（汉化子模组）→ info，键由父模组提供
        - 判定为翻译子模组（键多且覆盖不足七成）→ info，同上
        - 没索引原版                     → warn，无法确认是否原版已有
        - 索引了原版 + 覆盖良好           → error，可信任
        """
        if default != "error":
            return default
        if self.has_dependencies or self.loc_partial:
            return "info"
        if not self.vanilla_root:
            return "warn"
        return "error"

    def known(self, kind: str) -> set[str]:
        names: set[str] = set()
        for item in self.definitions.get(kind, []):
            ident = item.get("id") or ""
            if ident:
                names.add(ident)
        if self.kb_names:
            names |= self.kb_names.get(kind, set())
        return names

    def script_files(self, *needles: str, exts=(".txt",)) -> list[str]:
        """按目录片段筛选脚本文件。

        比较时给两侧都补上首尾斜杠：relbase 是 "interface" 这种不带斜杠的形式，
        而调用方传的是 "/interface/"，直接 `in` 判断永远匹配不到——顶层目录
        就会被整个漏掉（曾经导致 assets / sprites 校验器对顶层 interface/ 视而不见）。
        """
        wanted = [(n if n.startswith("/") else "/" + n).lower() for n in needles if n.strip("/")]
        out: list[str] = []
        for base, dirs, files in os.walk(self.mod_root):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".vscode"}]
            key = "/" + self.rel(base).strip("/").lower()
            if not key.endswith("/"):
                key += "/"
            if wanted and not any(n in key for n in wanted):
                continue
            for name in files:
                if os.path.splitext(name)[1].lower() in exts:
                    out.append(os.path.join(base, name))
        return sorted(out)

    def cached(self, key: str, producer: Callable[[], Any]) -> Any:
        if key not in self._cache:
            self._cache[key] = producer()
        return self._cache[key]


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

VALIDATORS: list[dict] = []


def validator(vid: str, title: str, needs_kb: bool = False):
    def deco(fn: Callable[[Ctx], list[dict]]):
        VALIDATORS.append({"id": vid, "title": title, "fn": fn, "needs_kb": needs_kb})
        return fn

    return deco


def run(ctx: Ctx, only: list[str] | None = None) -> dict[str, Any]:
    results = []
    all_issues: list[dict] = []
    for spec in VALIDATORS:
        if only and spec["id"] not in only:
            continue
        if spec["needs_kb"] and not ctx.has_external():
            results.append(
                {
                    "id": spec["id"],
                    "title": spec["title"],
                    "status": "skipped",
                    "reason": "需要知识库；先跑 kiant_hoi4_kb_build 索引原版或参考模组",
                    "issues": 0,
                }
            )
            continue
        try:
            found = spec["fn"](ctx) or []
        except Exception as exc:  # a broken validator must not kill the report
            results.append(
                {"id": spec["id"], "title": spec["title"], "status": "error",
                 "reason": f"{type(exc).__name__}: {exc}", "issues": 0}
            )
            continue
        for issue in found:
            issue.setdefault("validator", spec["id"])
        all_issues.extend(found)
        results.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "status": "ok",
                "issues": len(found),
                "errors": sum(1 for i in found if i.get("level") == "error"),
                "warnings": sum(1 for i in found if i.get("level") == "warn"),
            }
        )
    return {"validators": results, "issues": all_issues}


# --------------------------------------------------------------------------- #
# Shared scanning helpers
# --------------------------------------------------------------------------- #

def collect_sprites(ctx: Ctx) -> set[str]:
    """Sprite names defined by the mod, plus vanilla ones when indexable."""

    def build() -> set[str]:
        names: set[str] = set()
        for path in ctx.script_files("/interface/", exts=(".gfx",)):
            try:
                root, _ = cw.parse_file(path)
            except OSError:
                continue
            for _p, st in cw.walk(root):
                if st.key == "name" and isinstance(st.value, cw.Scalar):
                    val = cw.as_text(st.value)
                    if val.startswith("GFX_"):
                        names.add(val)
        if ctx.kb_names:
            names |= ctx.kb_names.get("sprite", set())
        return names

    return ctx.cached("sprites", build)


def collect_textures(ctx: Ctx) -> list[tuple[str, str, int]]:
    """(relpath, texturefile, line) for every texture reference in the mod."""

    def build() -> list[tuple[str, str, int]]:
        out: list[tuple[str, str, int]] = []
        for path in ctx.script_files("/interface/", "/gfx/", exts=(".gfx", ".asset")):
            try:
                root, _ = cw.parse_file(path)
            except OSError:
                continue
            relpath = ctx.rel(path)
            for _p, st in cw.walk(root):
                if st.key in {"texturefile", "textureFile"}:
                    out.append((relpath, cw.as_text(st.value), st.line))
        return out

    return ctx.cached("textures", build)


def _asset_exists(ctx: Ctx, ref: str) -> bool:
    if not ref:
        return True
    clean = ref.replace("\\", "/").strip()
    if os.path.isfile(ctx.mod_file(clean)):
        return True
    if ctx.vanilla_root and os.path.isfile(os.path.join(ctx.vanilla_root, clean.replace("/", os.sep))):
        return True
    return False


# --------------------------------------------------------------------------- #
# 1. Technology
# --------------------------------------------------------------------------- #

@validator("technology", "科技树")
def check_technology(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    tech_ids = ctx.known("tech")
    if not tech_ids:
        return issues

    for path in ctx.script_files("/technolog"):
        relpath = ctx.rel(path)
        try:
            root, _ = cw.parse_file(path)
        except OSError:
            continue
        for techs in cw.get_all(root, "technologies"):
            if not isinstance(techs.value, cw.Block):
                continue
            for tech in cw.stmts(techs.value):
                if not isinstance(tech.value, cw.Block):
                    continue
                tid = tech.key
                targets: list[tuple[str, int]] = []
                for st in cw.get_all(tech.value, "path"):
                    if isinstance(st.value, cw.Block):
                        for ref in cw.get_all(st.value, "leads_to_tech"):
                            targets.append((cw.as_text(ref.value), ref.line))
                for st in cw.get_all(tech.value, "dependencies"):
                    if isinstance(st.value, cw.Block):
                        for ref in cw.stmts(st.value):
                            targets.append((ref.key, ref.line))
                for target, line in targets:
                    if target and target not in tech_ids:
                        issues.append(
                            {
                                # 没索引原版时，目标很可能就是原版科技，不能报警告
                                "level": "warn" if ctx.have_vanilla else "info",
                                "kind": "tech",
                                "file": relpath,
                                "line": line,
                                "message": f"科技 {tid} 的前置/后继目标 '{target}' 未找到定义"
                                + ("" if ctx.have_vanilla else "（原版未索引或不完整，可能来自原版/父模组）"),
                                "hint": "拼写错误，或目标科技在未索引的其他 mod 里。索引原版后可以确认。",
                            }
                        )
                # 科技必须有本地化名与描述
                if not ctx.loc_known(tid):
                    issues.append(
                        {
                            "level": ctx.loc_level("error"),
                            "kind": "tech",
                            "file": relpath,
                            "line": tech.line,
                            "message": f"科技 {tid} 缺少本地化键",
                            "hint": "科技名显示为空，科技树会出现空白格子。",
                        }
                    )
                if not ctx.loc_known(f"{tid}_desc"):
                    issues.append(
                        {
                            "level": "info" if ctx.loc_level("error") == "info" else "warn",
                            "kind": "tech",
                            "file": relpath,
                            "line": tech.line,
                            "message": f"科技 {tid} 缺少 _desc 描述键",
                            "hint": "悬停提示会是空的，不影响功能。",
                        }
                    )
    return issues


# --------------------------------------------------------------------------- #
# 2. Assets: textures / meshes / sprites
# --------------------------------------------------------------------------- #

@validator("assets", "贴图与模型资产")
def check_assets(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    # 没索引原版时无法判断「文件不存在」还是「原版有」。
    # 子模组普遍直接复用原版 gfx/，一律报 error 会让每个正常模组都刷几千条假错误。
    missing_level = "error" if ctx.have_vanilla else "info"
    missing_note = "" if ctx.have_vanilla else "（原版未索引或不完整，可能由原版/父模组提供）"

    for relpath, ref, line in collect_textures(ctx):
        if not ref:
            continue
        if not _asset_exists(ctx, ref):
            issues.append(
                {
                    "level": missing_level,
                    "kind": "texture",
                    "file": relpath,
                    "line": line,
                    "message": f"贴图文件不存在：{ref}{missing_note}",
                    "hint": "路径相对 mod 根目录、用正斜杠、带扩展名。缺文件时游戏内显示粉黑方块。",
                }
            )

    mesh_refs: list[tuple[str, str, int]] = []
    for path in ctx.script_files("/gfx/", "/interface/", exts=(".asset",)):
        try:
            root, _ = cw.parse_file(path)
        except OSError:
            continue
        relpath = ctx.rel(path)
        for _p, st in cw.walk(root):
            if st.key in {"mesh", "pdxmesh"} and isinstance(st.value, cw.Scalar):
                val = cw.as_text(st.value)
                if val and "/" in val:
                    mesh_refs.append((relpath, val, st.line))
    for relpath, ref, line in mesh_refs:
        if not _asset_exists(ctx, ref):
            issues.append(
                {
                    "level": missing_level,
                    "kind": "mesh",
                    "file": relpath,
                    "line": line,
                    "message": f"模型文件不存在：{ref}{missing_note}",
                    "hint": ".mesh 是二进制资产，路径大小写敏感，Steam Deck 上大小写错会直接加载失败。",
                }
            )
    return issues


# --------------------------------------------------------------------------- #
# 3. Sprite references from content definitions
# --------------------------------------------------------------------------- #

@validator("sprites", "图标引用")
def check_sprite_refs(ctx: Ctx) -> list[dict]:
    """聚合报告：同一个缺失 sprite 只报一条，带出现次数。

    逐实例报告在真实大模组上会产出三万条同类 info，把真正的问题淹掉。
    """
    sprites = collect_sprites(ctx)
    # 知识库里索引到的原版/mod sprite 也要算「已知」，否则每个复用原版图标的
    # 模组都会被打成「未定义」——而这些恰恰是最常见、最正确的写法。
    kb_sprites = (ctx.kb_names or {}).get("sprite", set())
    known_all = sprites | kb_sprites
    if not known_all:
        return []
    have_vanilla = ctx.have_vanilla

    missing: dict[str, dict] = {}

    def check(item: dict, candidates: list[str], what: str) -> None:
        if any(c in known_all for c in candidates):
            return
        name = candidates[0]
        rec = missing.setdefault(
            name, {"count": 0, "item": item, "what": what}
        )
        rec["count"] += 1

    def refs_of(item: dict, fallback_keys: list[str]) -> list[list[str]]:
        """把一条定义的 icon/picture 引用展开成「候选组」列表。

        icons 可以写成条件块（`icon = { A = {...} B = yes }`），一个块里
        可能声明好几个 sprite；标量写法则只有一个。`pictures` 存的是
        全部原始引用，`extra` 是老字段（只存标量），作为兜底。
        """
        pics = item.get("pictures")
        if pics:
            return [[p] for p in pics]
        legacy = item.get("extra") or ""
        if not legacy:
            return []
        return [[legacy] + [f.format(legacy) for f in fallback_keys[1:]]]

    for item in ctx.definitions.get("focus", []):
        for candidates in refs_of(item, [""]):
            check(item, candidates, "国策图标")

    for item in ctx.definitions.get("idea", []):
        for candidates in refs_of(item, ["", "GFX_idea_{:s}", "GFX_{:s}"]):
            check(item, candidates, "国家精神图标")

    for item in ctx.definitions.get("decision", []):
        for candidates in refs_of(item, ["", "GFX_decision_{:s}", "GFX_{:s}"]):
            check(item, candidates, "决议图标")

    for item in ctx.definitions.get("event", []):
        for candidates in refs_of(item, [""]):
            check(item, candidates, "事件配图")

    issues: list[dict] = []
    for name, rec in sorted(missing.items(), key=lambda kv: -kv[1]["count"]):
        item = rec["item"]
        issues.append(
            {
                "level": "warn" if have_vanilla else "info",
                "kind": "sprite",
                "file": item.get("file"),
                "line": item.get("line"),
                "message": f"{rec['what']}引用的 sprite '{name}' 未在 mod 中定义（共 {rec['count']} 处）"
                + ("" if have_vanilla else "；未索引原版，可能来自原版"),
                "hint": "若是原版 sprite 可忽略；否则在 interface/*.gfx 注册，注意不同字段的 GFX_ 前缀规则不同。",
                "occurrences": rec["count"],
            }
        )
    return issues[:60]


# --------------------------------------------------------------------------- #
# 4. GUI
# --------------------------------------------------------------------------- #

@validator("ui", "界面文件")
def check_ui(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    seen: dict[str, str] = {}
    missing_sprites: dict[str, dict] = {}
    sprites = collect_sprites(ctx)

    for path in ctx.script_files("/interface/", exts=(".gui",)):
        relpath = ctx.rel(path)
        try:
            root, errors = cw.parse_file(path)
        except OSError:
            continue
        for e in errors[:5]:
            issues.append(
                {
                    # 解析器的诊断分 error/warn 两级（单引号提示是 warn），
                    # 一律标 error 会把可容忍的小问题抬成硬错误。
                    "level": e.get("level", "error"),
                    "kind": "gui",
                    "file": relpath,
                    "line": e.get("line"),
                    "message": f"界面文件语法问题：{e.get('message')}",
                    "hint": ".gui 结构脆弱，一个括号错位会导致整个窗口不显示。",
                }
            )
        for holder in cw.get_all(root, "guiTypes"):
            if not isinstance(holder.value, cw.Block):
                continue
            for win in cw.stmts(holder.value):
                if not isinstance(win.value, cw.Block):
                    continue
                name = _text_of(win.value, "name")
                if not name:
                    continue
                if name in seen:
                    issues.append(
                        {
                            "level": "warn",
                            "kind": "gui",
                            "file": relpath,
                            "line": win.line,
                            "message": f"窗口名 '{name}' 重复（另一处在 {seen[name]}）",
                            "hint": "同名窗口会互相覆盖，后加载的生效。",
                        }
                    )
                else:
                    seen[name] = relpath
                for _p, st in cw.walk(win.value):
                    if st.key in {"spriteType", "quadTextureSprite"} and isinstance(st.value, cw.Scalar):
                        ref = cw.as_text(st.value)
                        if ref.startswith("GFX_") and sprites and ref not in sprites:
                            # 按 sprite 名聚合：同一个缺失图标在几十个界面文件里出现是常事，
                            # 逐条报会把别的问题全淹掉。
                            rec = missing_sprites.setdefault(
                                ref, {"count": 0, "file": relpath, "line": st.line}
                            )
                            rec["count"] += 1

    for ref, rec in sorted(missing_sprites.items(), key=lambda kv: -kv[1]["count"])[:60]:
        issues.append(
            {
                "level": "warn" if ctx.have_vanilla else "info",
                "kind": "gui",
                "file": rec["file"],
                "line": rec["line"],
                "message": f"界面引用的 sprite '{ref}' 未找到（共 {rec['count']} 处）"
                + ("" if ctx.have_vanilla else "；原版未索引或不完整，可能来自原版/父模组"),
                "hint": "缺 sprite 时该控件显示为空白，界面仍能打开。",
                "occurrences": rec["count"],
            }
        )
    return issues


def _text_of(block: cw.Node, key: str) -> str:
    st = cw.get_one(block, key) if isinstance(block, cw.Block) else None
    return cw.as_text(st.value) if st else ""


# --------------------------------------------------------------------------- #
# 5. on_actions
# --------------------------------------------------------------------------- #

@validator("on_actions", "事件钩子")
def check_on_actions(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    events = ctx.known("event")
    if not events:
        return issues

    for path in ctx.script_files("/on_actions/"):
        relpath = ctx.rel(path)
        try:
            root, _ = cw.parse_file(path)
        except OSError:
            continue
        for holder in cw.get_all(root, "on_actions"):
            if not isinstance(holder.value, cw.Block):
                continue
            for hook in cw.stmts(holder.value):
                if not isinstance(hook.value, cw.Block):
                    continue
                # events/random_events 不一定挂在 hook 的直接子层——主流写法是
                # on_startup = { effect = { events = { usa.6 } } }，藏在 effect
                # 块里。只查直接子层会漏掉绝大多数真实用例，必须 walk 整棵子树。
                for _trail, st in cw.walk(hook.value):
                    key = st.key
                    if key not in ("events", "random_events"):
                        continue
                    if not isinstance(st.value, cw.Block):
                        continue
                    # events = { usa.6 } 是裸 token（Scalar），random_events
                    # = { 100 = usa.6 } 是 key=value（Stmt）。只遍历 stmts()
                    # 会把前者整块跳过——on_actions 校验曾因此对最常用的
                    # events 写法零检出。cw.entries() 统一两种形态。
                    for entry_key, entry_val in cw.entries(st.value):
                        line = getattr(entry_val, "line", st.line)
                        if key == "random_events" and entry_key.isdigit():
                            # 权重 = 事件id（标准写法），事件 id 在值里
                            target = cw.as_text(entry_val) if isinstance(entry_val, cw.Scalar) else ""
                            if target.isdigit():
                                # 写反了：100 = usa.6 才是对的
                                issues.append(
                                    {
                                        "level": "warn",
                                        "kind": "on_action",
                                        "file": relpath,
                                        "line": line,
                                        "message": (
                                            f"on_action '{hook.key}' 的 random_events 写法反了："
                                            f"应为「权重 = 事件」，现在是「{entry_key} = {target}」"
                                        ),
                                        "hint": "random_events 的键是权重（数字），值才是事件 id。",
                                    }
                                )
                                continue
                        else:
                            # events = { usa.6 }（裸 token，键即 id），或
                            # random_events = { usa.6 }（不带权重的裸写法，也合法）
                            target = entry_key
                        if not target:
                            continue
                        # random_events 里 `17000 = 0` 的意思是「这个权重不触发任何事件」，
                        # 原版大量使用，不是错误。
                        if target == "0" or target == "none":
                            continue
                        if target not in events:
                            issues.append(
                                {
                                    # 没索引原版时，事件很可能就是原版的
                                    "level": "warn" if ctx.have_vanilla else "info",
                                    "kind": "on_action",
                                    "file": relpath,
                                    "line": line,
                                    "message": f"on_action '{hook.key}' 引用了不存在的事件 {target}"
                                    + ("" if ctx.have_vanilla else "（原版未索引或不完整，可能来自原版/父模组）"),
                                    "hint": "事件 id 拼错，或该事件属于未索引的其他 mod。钩子本身仍会触发，只是事件不弹出。",
                                }
                            )
    return issues


# --------------------------------------------------------------------------- #
# 6. Country history
# --------------------------------------------------------------------------- #

@validator("history", "国家历史")
def check_history(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    ideas = ctx.known("idea")
    for path in ctx.script_files("/history/countries/"):
        relpath = ctx.rel(path)
        try:
            root, _ = cw.parse_file(path)
        except OSError:
            continue
        for st in cw.get_all(root, "add_ideas"):
            if not isinstance(st.value, cw.Block):
                continue
            # add_ideas = { my_spirit } 是裸 token（Scalar），add_ideas = { x = y }
            # 是 Stmt。只遍历 stmts() 会把前者整块跳过。cw.entries() 统一两种形态。
            for name, val in cw.entries(st.value):
                if name and ideas and name not in ideas:
                    issues.append(
                        {
                            "level": "warn",
                            "kind": "history",
                            "file": relpath,
                            "line": st.line,
                            "message": f"开局 add_ideas 引用了未定义的精神 '{name}'",
                            "hint": "原版精神需索引原版后才能确认；否则检查拼写。",
                        }
                    )
        for st in cw.get_all(root, "oob"):
            ref = cw.as_text(st.value)
            if not ref:
                continue
            candidates = [
                ctx.mod_file(f"history/units/{ref}.txt"),
                os.path.join(ctx.vanilla_root, "history", "units", f"{ref}.txt") if ctx.vanilla_root else "",
            ]
            if not any(c and os.path.isfile(c) for c in candidates):
                issues.append(
                    {
                        # 未索引原版时，oob 很可能就是原版自带的那个编制文件
                        "level": "error" if ctx.have_vanilla else "info",
                        "kind": "history",
                        "file": relpath,
                        "line": st.line,
                        "message": f"oob 指向的编制文件不存在：history/units/{ref}.txt"
                        + ("" if ctx.have_vanilla else "（原版未索引或不完整，可能由原版/父模组提供）"),
                        "hint": "缺 oob 会导致该国开局没有部队，且日志里只有一行 Failed to load。",
                    }
                )
    return issues


# --------------------------------------------------------------------------- #
# 7. defines
# --------------------------------------------------------------------------- #

@validator("defines", "引擎常量")
def check_defines(ctx: Ctx) -> list[dict]:
    issues: list[dict] = []
    for path in ctx.script_files("/defines/", exts=(".lua",)):
        relpath = ctx.rel(path)
        try:
            text = open(path, "r", encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        opens, closes = text.count("{"), text.count("}")
        if opens != closes:
            issues.append(
                {
                    "level": "error",
                    "kind": "defines",
                    "file": relpath,
                    "message": f"大括号不配对（{opens} 个 {{ 对 {closes} 个 }}）",
                    "hint": "defines 是 Lua 语法，少一个括号整个文件不生效，所有常量静默回退到原版。",
                }
            )
        # Lua 表形式（NDefines = { NGame = { ... } }）的内部键本来就不带前缀，
        # 逐行前缀检查会把每一行都报成 warn——表形式文件整篇误报。检测到表
        # 形式就跳过逐行检查；前缀检查只对「逐行赋值」写法有意义。大括号
        # 配平检查对两种写法都保留。
        is_table_form = bool(re.search(r"\bNDefines\w*\s*=\s*\{", text))
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("--"):
                continue
            # 合法的前缀有两种：NDefines.NXxx 与 NDefines_Graphics.NXxx
            if not is_table_form and not re.search(r"\bNDefines\w*\.", stripped) and "=" in stripped:
                issues.append(
                    {
                        "level": "warn",
                        "kind": "defines",
                        "file": relpath,
                        "line": lineno,
                        "message": "赋值语句没有 NDefines. 前缀",
                        "hint": "只写 NDefines.NGame.XXX = 值 才有意义，裸变量不会影响游戏。",
                    }
                )
    return issues


# --------------------------------------------------------------------------- #
# 8. music
# --------------------------------------------------------------------------- #

_PLAY_SONG_RE = re.compile(r'play_song\s*=\s*"([^"]+)"')


def _collect_music_defs(root: str) -> dict[str, str]:
    """收集 <root>/music/ 下的歌曲定义（music = { name = ... }）。

    两层结构的第一层：.asset 与 station .txt 都可能带定义块；
    没有 name 的块（station 的选曲表）自然被跳过。
    """
    defined: dict[str, str] = {}
    mdir = os.path.join(root, "music")
    if not os.path.isdir(mdir):
        return defined
    for base, _dirs, files in os.walk(mdir):
        for fn in files:
            if not fn.lower().endswith((".asset", ".txt")):
                continue
            full = os.path.join(base, fn)
            try:
                block, _errs = cw.parse_file(full)
            except OSError:
                continue
            for stmt in cw.get_all(block, "music"):
                if not isinstance(stmt.value, cw.Block):
                    continue
                name_stmt = cw.get_one(stmt.value, "name")
                if name_stmt is not None:
                    name = cw.as_text(name_stmt.value)
                    if name and name not in defined:
                        defined[name] = full
    return defined


@validator("music", "音乐引用")
def check_music(ctx: Ctx) -> list[dict]:
    """音乐两层结构完整性（出处：EB-022 / audio.md §6.3）。

    play_song 的官方语义是 "Plays song from database"——歌必须先进
    music/ 的 .asset 定义层，引用未定义的歌名**静默跳过**，不进日志。
    工坊实测有整 mod 因此不出声。本检查做三件事：

    1. mod 内 play_song / 电台 song 引用了不存在的歌名 → 未索引原版时 warn
       （歌可能在原版 music/music.asset 里），索引了原版仍缺 → error；
    2. 定义块指向的音频文件不存在 → error（file 相对本文件目录）；
    3. music/ 里混入非 .ogg 音频 → warn（原版全库只用 OGG Vorbis）。
    """
    issues: list[dict] = []

    defined = _collect_music_defs(ctx.mod_root)
    mod_defined = set(defined)
    if ctx.vanilla_root:
        for name, full in _collect_music_defs(ctx.vanilla_root).items():
            defined.setdefault(name, full)
    # 引用可以被父模组/已索引来源补足时，不再按「未定义」报
    defined |= {n: "" for n in ctx.known("music")}

    # 1. 定义块指向的音频文件必须存在（只查 mod 自己的；原版的必然存在）
    mod_def_files = {full for name, full in defined.items() if full.startswith(ctx.mod_root)}
    for full in mod_def_files:
        block, _errs = cw.parse_file(full)
        for stmt in cw.get_all(block, "music"):
            if not isinstance(stmt.value, cw.Block):
                continue
            name_stmt = cw.get_one(stmt.value, "name")
            file_stmt = cw.get_one(stmt.value, "file")
            if name_stmt is None or file_stmt is None:
                continue
            name = cw.as_text(name_stmt.value)
            fname = cw.as_text(file_stmt.value)
            if not name or not fname:
                continue
            audio = os.path.join(os.path.dirname(full), fname)
            if not os.path.isfile(audio):
                issues.append(
                    {
                        "level": "error",
                        "kind": "music",
                        "file": ctx.rel(full),
                        "line": stmt.line,
                        "message": f"歌曲 {name} 指向的音频文件不存在: {fname}",
                        "hint": "file 相对本 .asset/.txt 所在目录；缺文件则这首歌静默不出声。",
                    }
                )

    # 3. music/ 里混入非 ogg
    mdir = os.path.join(ctx.mod_root, "music")
    if os.path.isdir(mdir):
        for base, _dirs, files in os.walk(mdir):
            for fn in files:
                if fn.lower().endswith((".mp3", ".wav", ".flac", ".m4a")):
                    issues.append(
                        {
                            "level": "warn",
                            "kind": "music",
                            "file": ctx.rel(os.path.join(base, fn)),
                            "message": f"音乐目录里的非 ogg 音频: {fn}",
                            "hint": "原版 music/ 全库只用 OGG Vorbis（44100Hz）；"
                            "mp3/wav 不会被任何层引用，转码后重命名指回 .asset。",
                        }
                    )

    # 2. 引用查定义：电台选曲表 + 全脚本 play_song
    missing_hint = "歌曲必须先在 music/ 的 .asset/.txt 里定义（music = { name = ... }），"
    if os.path.isdir(mdir):
        for base, _dirs, files in os.walk(mdir):
            for fn in files:
                if not fn.lower().endswith(".txt"):
                    continue
                full = os.path.join(base, fn)
                block, _errs = cw.parse_file(full)
                for stmt in cw.get_all(block, "music"):
                    if not isinstance(stmt.value, cw.Block):
                        continue
                    song_stmt = cw.get_one(stmt.value, "song")
                    if song_stmt is None:
                        continue
                    song = cw.as_text(song_stmt.value)
                    if song and song not in defined:
                        issues.append(
                            {
                                "level": "error" if ctx.have_vanilla else "warn",
                                "kind": "music",
                                "file": ctx.rel(full),
                                "line": stmt.line,
                                "message": f"电台选曲引用了未定义的歌曲: {song}",
                                "hint": missing_hint + "未定义时该曲目永远不被播放。",
                            }
                        )

    for path in ctx.script_files(exts=(".txt",)):
        try:
            text = open(path, "r", encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for song in _PLAY_SONG_RE.findall(line):
                if song not in defined:
                    issues.append(
                        {
                            "level": "error" if ctx.have_vanilla else "warn",
                            "kind": "music",
                            "file": ctx.rel(path),
                            "line": lineno,
                            "message": f"play_song 引用了未定义的歌曲: {song}",
                            "hint": missing_hint + '官方语义 "Plays song from database"，'
                            "没进库就静默跳过（不报错）。",
                        }
                    )
    return issues


# --------------------------------------------------------------------------- #
# 9. focus_tree
# --------------------------------------------------------------------------- #

_MAX_FOCUS_ISSUES = 300  # 参照 MD focus 工具的截断上限，防巨树刷屏


def _collect_focus_data(ctx: Ctx) -> dict[str, Any]:
    """收集 mod 内全部 focus 定义与文件级 shared_focus，供跨树解析。

    返回 {trees: [{id, focuses: {fid: {...}}, order: [fid]}], shared: set}
    """
    trees: list[dict] = []
    shared_global: set[str] = set()
    for path in ctx.script_files("/national_focus/"):
        try:
            block, _errs = cw.parse_file(path)
        except OSError:
            continue
        relpath = ctx.rel(path)

        def _grab(st, tree_id: str) -> None:
            if not isinstance(st.value, cw.Block):
                return
            fid = cw.as_text(cw.get_one(st.value, "id").value) if cw.get_one(st.value, "id") else ""
            if not fid:
                return
            # 坐标两种写法都收：原版主流是直接 x=/y=（generic.txt 56 处），
            # 少数文件用 position = { x y }（australia.txt 等）
            xy = cw.get_one(st.value, "x")
            yy = cw.get_one(st.value, "y")
            if xy is None or yy is None:
                pos = cw.get_one(st.value, "position")
                if pos is not None and isinstance(pos.value, cw.Block):
                    if xy is None:
                        xy = cw.get_one(pos.value, "x")
                    if yy is None:
                        yy = cw.get_one(pos.value, "y")
            x = cw.as_text(xy.value) if xy is not None and isinstance(xy.value, cw.Scalar) else ""
            y = cw.as_text(yy.value) if yy is not None and isinstance(yy.value, cw.Scalar) else ""
            prereqs = []
            pr = cw.get_one(st.value, "prerequisite")
            if pr and isinstance(pr.value, cw.Block):
                for cell in cw.stmts(pr.value):
                    opts = [cw.as_text(c.value) for c in getattr(cell.value, "items", []) if isinstance(c, cw.Scalar)] if isinstance(cell.value, cw.Block) else [cw.as_text(cell.value)]
                    prereqs.append(opts)
            mux = []
            mx = cw.get_one(st.value, "mutually_exclusive")
            if mx is not None:
                if isinstance(mx.value, cw.Scalar):
                    mux = [cw.as_text(mx.value)]
                elif isinstance(mx.value, cw.Block):
                    # 两种写法都收：mutually_exclusive = F1 与
                    # mutually_exclusive = { focus = F1 }（块内是 Stmt）
                    for c in mx.value.items:
                        if isinstance(c, cw.Scalar):
                            mux.append(cw.as_text(c))
                        elif isinstance(c, cw.Stmt):
                            if isinstance(c.value, cw.Scalar):
                                mux.append(cw.as_text(c.value))
                            else:
                                mux += [cw.as_text(g) for g in c.value.items
                                        if isinstance(g, cw.Scalar)]
            rel = cw.get_one(st.value, "relative_position_id")
            rel_id = cw.as_text(rel.value) if rel else ""
            trees[-1]["focuses"][fid] = {
                "x": x, "y": y, "prereqs": prereqs, "mux": mux,
                "relative": rel_id, "line": st.line, "file": relpath,
                "tree": tree_id,
            }
            trees[-1]["order"].append(fid)

        for st in cw.stmts(block):
            if st.key != "focus_tree" or not isinstance(st.value, cw.Block):
                continue
            tree_id = ""
            id_stmt = cw.get_one(st.value, "id")
            if id_stmt is not None:
                tree_id = cw.as_text(id_stmt.value)
            trees.append({"id": tree_id, "focuses": {}, "order": [], "file": relpath})
            for inner in cw.stmts(st.value):
                if inner.key in {"focus", "shared_focus"}:
                    _grab(inner, tree_id)
        for st in cw.stmts(block):
            if st.key == "shared_focus" and isinstance(st.value, cw.Block):
                fid = cw.as_text(cw.get_one(st.value, "id").value) if cw.get_one(st.value, "id") else ""
                if fid:
                    shared_global.add(fid)
    return {"trees": trees, "shared": shared_global}


@validator("focus_tree", "国策树语义")
def check_focus_tree(ctx: Ctx) -> list[dict]:
    """国策树语义校验（吸收自 hoi4modutils fork 的 validation.ts + MD 工具规则码）。

    五类结构问题，全部纯图算法：前置引用不存在、前置成环、互斥引用缺失/自引、
    同树同坐标重叠、relative_position_id 断链。前置/互斥目标允许落在
    本树、文件级 shared_focus、其他树或原版索引（known("focus")）。
    """
    issues: list[dict] = []
    data = ctx.cached("focus_data", lambda: _collect_focus_data(ctx))
    known_focus = ctx.known("focus")
    all_local: set[str] = set()
    for t in data["trees"]:
        all_local |= set(t["focuses"])
    resolvable = all_local | data["shared"] | known_focus

    def _loc(fid: str, info: dict) -> dict:
        return {"file": info["file"], "line": info["line"], "kind": "focus_tree",
                "focus": fid, "tree": info["tree"]}

    n_issues = 0
    for tree in data["trees"]:
        focuses = tree["focuses"]

        # 1. 前置引用不存在 + 2. 环检测 + 3. 互斥
        for fid, info in focuses.items():
            for group in info["prereqs"]:
                for target in group:
                    if target and target not in resolvable:
                        issues.append({**_loc(fid, info), "level": "warn",
                            "message": f"国策 {fid} 的前置 {target} 不存在",
                            "hint": "前置 id 拼错或目标在本树/共享段/原版里都找不到；"
                            "前置断链会让该国策永远无法解锁。"})
                        n_issues += 1
            for target in info["mux"]:
                if target == fid:
                    issues.append({**_loc(fid, info), "level": "error",
                        "message": f"国策 {fid} 与自身互斥",
                        "hint": "mutually_exclusive 指向自己，引擎会忽略或产生未定义行为。"})
                    n_issues += 1
                elif target and target not in resolvable:
                    issues.append({**_loc(fid, info), "level": "warn",
                        "message": f"国策 {fid} 的互斥对象 {target} 不存在",
                        "hint": "互斥 id 拼错或目标缺失；互斥断链会让「二选一」失效。"})
                    n_issues += 1
            rel = info["relative"]
            if rel and rel not in resolvable and rel != fid:
                issues.append({**_loc(fid, info), "level": "warn",
                    "message": f"国策 {fid} 的 relative_position_id {rel} 不存在",
                    "hint": "相对定位断链时坐标回退为绝对值，节点会重叠或错位"
                    "（见 EB-021）。"})
                n_issues += 1
            if n_issues >= _MAX_FOCUS_ISSUES:
                break
        if n_issues >= _MAX_FOCUS_ISSUES:
            break

        # 4. 环检测（本树内 DFS；跨树/跨 mod 环无法静态判定，不报）
        color: dict[str, int] = {}

        def _cycle(fid: str, stack: list[str]) -> None:
            nonlocal n_issues
            if n_issues >= _MAX_FOCUS_ISSUES or color.get(fid) == 2:
                return
            if color.get(fid) == 1:
                cycle = stack[stack.index(fid):] + [fid]
                anchor = focuses.get(fid, {"file": tree["file"], "line": 0, "tree": tree["id"]})
                issues.append({**_loc(fid, anchor), "level": "error",
                    "message": f"国策前置成环: {' -> '.join(cycle)}",
                    "hint": "环上的国策互相等待，全部永远无法解锁。"})
                n_issues += 1
                return
            color[fid] = 1
            for group in focuses[fid]["prereqs"]:
                for target in group:
                    if target in focuses:
                        _cycle(target, stack + [fid])
            color[fid] = 2

        for fid in focuses:
            _cycle(fid, [])
            if n_issues >= _MAX_FOCUS_ISSUES:
                break

        # 5. 同树坐标重叠（相对定位已解算的目标不豁免；断链的 relative 视为
        #    实际落在原始坐标上，照样参与重叠判定）
        seen_pos: dict[tuple[str, str], str] = {}
        for fid in tree["order"]:
            info = focuses[fid]
            if not info["x"] or not info["y"]:
                continue
            exempt = info["relative"] != "" and info["relative"] in resolvable
            key = (info["x"], info["y"])
            if key in seen_pos and not exempt:
                issues.append({**_loc(fid, info), "level": "warn",
                    "message": f"国策 {fid} 与 {seen_pos[key]} 坐标重叠（x={info['x']} y={info['y']}）",
                    "hint": "同树同坐标会叠卡；若其中一方使用了有效的 relative_position_id "
                    "偏移则可合法共享基准坐标，此报错可忽略。"})
                n_issues += 1
                if n_issues >= _MAX_FOCUS_ISSUES:
                    break
            elif key not in seen_pos:
                seen_pos[key] = fid

    return issues


# --------------------------------------------------------------------------- #
# 10. loc_commands
# --------------------------------------------------------------------------- #

# 本地化 Get* 命令表。借用自 CWTools hoi4-config（Config/localisation.cwt，
# MIT © 2018 tboby），按其「命令 = 适用 scope」的 curated 清单收 Name/Date/
# Politics/State/Character/Air/Token/BOP 八组。scripted_localisation 里
# 自定义的 Get* 会单独收集，不计为未知。
LOC_COMMANDS = frozenset({
    "GetDateText", "GetDate", "GetMonth", "GetYear",
    "GetName", "GetNameWithFlag", "GetNameDef", "GetNameDefCap", "GetTag",
    "GetAdjective", "GetAdjectiveCap", "GetOldName", "GetOldNameDef",
    "GetOldNameDefCap", "GetOldAdjective", "GetOldAdjectiveCap",
    "GetNonIdeologyName", "GetNonIdeologyNameDef", "GetNonIdeologyNameDefCap",
    "GetNonIdeologyAdjective", "GetNonIdeologyAdjectiveCap",
    "GetLeader", "GetManpower", "GetFactionName", "GetAgency", "GetFlag",
    "GetPartySupport", "GetLastElection", "GetRulingParty",
    "GetRulingPartyLong", "GetRulingIdeology", "GetRulingIdeologyNoun",
    "GetCommunistParty", "GetDemocraticParty", "GetFascistParty",
    "GetNeutralParty", "GetCommunistLeader", "GetDemocraticLeader",
    "GetFascistLeader", "GetNeutralLeader",
    "GetID", "GetCapitalVictoryPointName", "GetSurname", "GetFullName",
    "GetSheHe", "GetSheHeCap", "GetHerHim", "GetHerHimCap", "GetHerHis",
    "GetHerHisCap", "GetHersHis", "GetHersHisCap", "GetHerselfHimself",
    "GetHerselfHimselfCap", "GetIdeology", "GetIdeologyGroup",
    "GetRank", "GetCodeName", "GetCallsign", "GetWing", "GetWingShort",
    "GetAceType", "GetMissionRegion",
    "GetTokenKey", "GetTokenLocalizedKey", "GetDateString",
    "GetDateStringShortMonth", "GetDateStringNoHour", "GetDateStringNoHourLong",
    "GetActiveSideName", "GetTrendingSideName", "GetRightSideName",
    "GetLeftSideName", "GetChangeRateDesc", "GetPowerBalanceName",
    "GetPowerBalanceModDesc", "GetActiveRangeName", "GetActiveRangeModDesc",
    "GetActiveRangeRuleDesc", "GetBopTrendTexticon",
})

_LOC_CMD_RE = re.compile(r"\[([^\[\]]*)\]")
_LOC_GET_RE = re.compile(r"(?:^|\.)((?:[A-Za-z0-9_]+\.)?Get[A-Za-z0-9_]*)\s*$")


def _collect_scripted_loc_names(root_dir: str) -> set[str]:
    """收集 scripted_localisation 里自定义的 Get* 函数名（defined_text 的 name）。"""
    names: set[str] = set()
    sdir = os.path.join(root_dir, "common", "scripted_localisation")
    if not os.path.isdir(sdir):
        return names
    for base, _dirs, files in os.walk(sdir):
        for fn in files:
            if not fn.lower().endswith(".txt"):
                continue
            try:
                block, _errs = cw.parse_file(os.path.join(base, fn))
            except OSError:
                continue
            for path, st in cw.walk(block):
                if st.key == "name" and isinstance(st.value, cw.Scalar):
                    v = cw.as_text(st.value)
                    if v.startswith("Get"):
                        names.add(v)
    return names


@validator("loc_commands", "本地化命令")
def check_loc_commands(ctx: Ctx) -> list[dict]:
    """本地化值里 [Root.GetXxx] 命令存在性（吸收自 CWTools localisation.cwt）。

    「loc 里写错命令名 → 界面显示原样文字」一类问题的机器判定（见 EB-001）。
    三级分诊（RT56 全量语料校准：209 条原始命中里 154 条是大小写变体、
    5 条真拼错、其余为查无定义的悬空引用）：

    1. 精确命中已知清单（CWTools curated 表 + mod/原版 scripted_localisation）
       → 静默；
    2. 大小写变体（引擎不区分大小写，见 AUTHORITY）→ 静默；
    3. 编辑距离 ≤2 的近匹配 → **warn「疑似拼错」**并给出最接近的命令；
    4. 其余 → info「不在已知清单」（可能是未安装 DLC / 未索引来源的命令）。
    """
    issues: list[dict] = []
    custom = _collect_scripted_loc_names(ctx.mod_root)
    if ctx.vanilla_root:
        custom |= _collect_scripted_loc_names(ctx.vanilla_root)
    known_cmd = LOC_COMMANDS | custom
    known_lower = {k.lower(): k for k in known_cmd}
    known_list = sorted(known_cmd)

    for path in ctx.script_files("/localisation/", exts=(".yml",)):
        relpath = ctx.rel(path)
        try:
            text = open(path, "r", encoding="utf-8-sig", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if ":" not in line:
                continue
            value = line.split(":", 1)[1]
            for bracket in _LOC_CMD_RE.findall(value):
                for part in bracket.split("."):
                    m = _LOC_GET_RE.match(part.strip())
                    if not m:
                        continue
                    cmd = m.group(1).rsplit(".", 1)[-1]
                    if cmd in known_cmd or cmd.lower() in known_lower:
                        continue
                    near = difflib.get_close_matches(cmd, known_list, n=1, cutoff=0.8)
                    if near:
                        issues.append(
                            {
                                "level": "warn",
                                "kind": "loc_commands",
                                "file": relpath,
                                "line": lineno,
                                "message": f"本地化命令 {cmd} 疑似拼错，最接近的是 {near[0]}",
                                "hint": "引擎对命令名不区分大小写，但拼写错误不在容差内："
                                "写错的命令显示为原样文字（EB-001）。",
                            }
                        )
                    else:
                        issues.append(
                            {
                                "level": "info",
                                "kind": "loc_commands",
                                "file": relpath,
                                "line": lineno,
                                "message": f"本地化命令 {cmd} 不在已知清单中",
                                "hint": "可能是未安装 DLC / 未索引来源的 scripted_localisation "
                                "命令；若确认存在可忽略本条。",
                            }
                        )
    return issues

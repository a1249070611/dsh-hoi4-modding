"""Pluggable content validators.

Each validator owns one content type (technology, assets, UI, on_actions, ...).
They all share one context and return the same issue shape, so adding a new
content type is three steps: write a function, decorate it, done.

Design rule: a validator must never produce a false positive just because the
vanilla index is missing. When it cannot verify something without external
knowledge, it says so explicitly instead of guessing.
"""

from __future__ import annotations

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

#!/usr/bin/env python3
"""HOI4 Modkit MCP server.

Speaks the Model Context Protocol over stdio with newline-delimited JSON-RPC.
Zero third-party dependencies, so `git clone` + `python server.py` is enough on
any platform that can run the tool.

Layers:
    cw.py           Clausewitz parser
    checks.py       structural validation (descriptor, loc, ids, syntax)
    validators.py   pluggable per-content-type validators
    kb.py           knowledge base index + retrieval
    preview.py      offline HTML preview
    planner.py      phased plan tracking
    scaffolder.py   code generation + loc repair

Direct CLI mode exists for debugging or for agents that only have a shell:
    python server.py --list
    python server.py --call kiant_hoi4_validate_mod '{"mod_path": "path/to/mod"}'
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import checks
import cw
import kb
import planner
import playbook
import remote
import preview
import scaffolder

SERVER_NAME = "kiant-hoi4-modkit"


def _read_plugin_version(default: str = "0.0.0") -> str:
    """Single source of truth: plugin.json. Keeps MCP handshake in sync with the manifest."""
    manifest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin.json")
    try:
        with open(manifest, "r", encoding="utf-8") as fh:
            return str(json.load(fh).get("version") or default)
    except Exception:
        return default


SERVER_VERSION = _read_plugin_version()
PROTOCOL_VERSION = "2024-11-05"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def _kb_context(db_path: str = "") -> tuple[dict | None, str, set | None]:
    """Return (names_by_kind, vanilla_root, external_loc_keys) when an index exists."""
    if not kb.available(db_path):
        return None, "", None
    names = kb.names_by_kind(db_path)
    return (names or None), kb.find_game_dir(), kb.loc_keys(db_path)


# --------------------------------------------------------------------------- #
# Core tools
# --------------------------------------------------------------------------- #

def tool_validate_mod(args: dict) -> Any:
    deep = bool(args.get("deep", False))
    db_path = args.get("db_path", "")
    names, vanilla, external_loc = (None, "", None)
    if deep or kb.available(db_path):
        names, vanilla, external_loc = _kb_context(db_path)
    return checks.validate_mod(
        args["mod_path"],
        deep=deep,
        kb_names=names,
        vanilla_root=vanilla,
        only_validators=args.get("only_validators"),
        external_loc=external_loc,
        per_check=int(args.get("per_check", 25)),
        max_issues=int(args.get("max_issues", 200)),
    )


def tool_scaffold(args: dict) -> Any:
    return scaffolder.scaffold(
        mod_path=args["mod_path"],
        kind=args["kind"],
        name=args.get("name", ""),
        tag=args.get("tag", "TAG"),
        namespace=args.get("namespace", ""),
        x=int(args.get("x", 0)),
        y=int(args.get("y", 0)),
        icon=args.get("icon", ""),
        capital=int(args.get("capital", 1)),
        force=bool(args.get("force", False)),
        display_name=args.get("display_name", ""),
        version=args.get("version", "0.1.0"),
    )


def tool_scan_localisation(args: dict) -> Any:
    mod_root, _desc, _notes = checks.resolve_mod_root(args["mod_path"])
    out = checks.scan_localisation(mod_root)
    limit = int(args.get("limit", 40))
    out["issues"] = out["issues"][:limit]
    out["key_count"] = len(out["keys"])
    out["sample_keys"] = sorted(out["keys"])[:limit]
    out.pop("keys", None)
    return out


def tool_fix_localisation(args: dict) -> Any:
    mod_root, _desc, _notes = checks.resolve_mod_root(args["mod_path"])
    return scaffolder.fix_localisation(mod_root, dry_run=bool(args.get("dry_run", True)))


def tool_parse_script(args: dict) -> Any:
    path = args["file_path"]
    if not os.path.isfile(path):
        return {"ok": False, "message": f"文件不存在：{path}"}
    root, errors = cw.parse_file(path)
    if args.get("path_filter"):
        wanted = [p.strip() for p in str(args["path_filter"]).split(">") if p.strip()]
        node: cw.Node = root
        for key in wanted:
            nxt = cw.get_one(node, key) if isinstance(node, cw.Block) else None
            if nxt is None:
                return {"ok": False, "message": f"找不到路径段 '{key}'", "at": wanted}
            node = nxt.value
        data = cw.to_python(node)
    else:
        data = cw.to_python(root)
    return {
        "ok": True,
        "file": path,
        "diagnostics": errors,
        "raw_statement_count": sum(1 for _ in cw.walk(root)),
        "tree": data,
    }


def tool_find_duplicates(args: dict) -> Any:
    mod_root, _desc, _notes = checks.resolve_mod_root(args["mod_path"])
    bundle = checks.collect_definitions(mod_root)
    dups = checks.find_duplicates(mod_root, bundle["definitions"])
    return {
        "duplicate_count": len(dups),
        "definitions_scanned": {k: len(v) for k, v in sorted(bundle["definitions"].items())},
        "duplicates": dups,
        "parse_errors": bundle["parse_errors"][:25],
        "note": "scripted_effect / scripted_trigger 允许重名覆盖，已排除在检查之外。",
    }


def tool_analyze_error_log(args: dict) -> Any:
    path = args.get("log_path", "")
    if not path:
        user_dir = kb.find_user_dir()
        candidates = [
            os.path.join(user_dir, "logs", "error.log") if user_dir else "",
            os.path.expanduser("~/Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log"),
            os.path.expanduser("~/.local/share/Paradox Interactive/Hearts of Iron IV/logs/error.log"),
        ]
        for cand in candidates:
            if cand and os.path.isfile(cand):
                path = cand
                break
        if not path:
            return {
                "found": False,
                "tried": [c for c in candidates if c],
                "hint": "把 log_path 显式指到 error.log；游戏需用 -debug_mode 启动才会写详细内容（-debug 是社区讹传，启动器清单里没有）。",
            }
    return checks.analyze_error_log(path, top_n=int(args.get("top_n", 15)))


def tool_list_overrides(args: dict) -> Any:
    mod_root, _desc, _notes = checks.resolve_mod_root(args["mod_path"])
    return checks.list_overrides(mod_root, args["vanilla_path"])


# --------------------------------------------------------------------------- #
# Knowledge base tools
# --------------------------------------------------------------------------- #

def tool_kb_build(args: dict) -> Any:
    action = args.get("action", "build")
    configured = kb.load_source_config()

    if action == "discover":
        # discover 把所有能找到的都列出来（含模组），方便用户挑；
        # 但 build 默认不碰模组，见下面 want_mods。
        sources = configured or kb.detect_sources(args.get("mods_root", ""), include_mods=True)
        for s in sources:
            if s.get("kind") == "mod":
                s["opt_in"] = True
        return {
            "found": len(sources),
            "game_dir": kb.find_game_dir() or "未找到（原版索引不可用，依赖原版的检查会跳过）",
            "user_dir": kb.find_user_dir(),
            "sources": sources,
            "note": "用 action=build 建索引。默认只索引 game / notes / refs；"
            "第三方模组标了 opt_in，要收进来得传 only=mod 或 include_mods=true。"
            "首次全量约 30 秒，之后走增量。",
        }

    only_tokens = {s.strip() for s in str(args.get("only", "")).split(",") if s.strip()}
    want_mods = bool(args.get("include_mods")) or any(
        t == "mod" or t.startswith("mod:") for t in only_tokens
    )
    sources = (
        args.get("sources")
        or configured
        or kb.detect_sources(args.get("mods_root", ""), include_mods=want_mods)
    )
    # 远端知识库的缓存要单独补进来：用户一旦写了 sources.json，它就接管了自动探测，
    # 而那份文件里通常不会列 remote（它是缓存，不是固定目录）。
    _remote_src = remote.as_source()
    if _remote_src and not any(s.get("name") == _remote_src["name"] for s in sources):
        sources.append(_remote_src)

    # 「第二资料库」：用户点名要读某个本地目录时才收（笔记、别人给的文档、旧资料）。
    # 不做自动扫描——目录里可能是任何东西，由用户指定范围。
    for extra in args.get("local_dirs") or []:
        extra = str(extra)
        if not os.path.isdir(extra):
            continue
        # basename 可能为空（如传了盘符根 "C:\\"），此时必须显式给默认名。
        # 之前写成 ("local:" + basename) or "local"——"local:" 恒为真值，
        # or 分支永远不触发，会得到一个以冒号结尾的怪源名。
        base = os.path.basename(os.path.normpath(extra))
        src_name = ("local:" + base) if base else "local"
        if not any(s.get("name") == src_name for s in sources):
            sources.append({"name": src_name, "path": extra, "kind": "notes"})
    if args.get("only"):
        sources = [s for s in sources if s["name"] in only_tokens or s.get("kind") in only_tokens]
    elif args.get("skip_game"):
        sources = [s for s in sources if s.get("kind") != "game"]
    if not sources:
        return {
            "ok": False,
            "message": "没有可索引的源。",
            "hint": '传 sources=[{"name":..,"path":..,"kind":..}]，或先跑 action=discover 看自动发现结果。',
        }
    langs = args.get("loc_langs")
    return kb.build(
        sources,
        args.get("db_path", ""),
        incremental=bool(args.get("incremental", True)),
        max_files_per_source=int(args.get("max_files_per_source", 0)),
        loc_langs=None if langs is None else [str(x) for x in langs],
    )


def tool_kb_sync(args: dict) -> Any:
    action = args.get("action", "status")
    if action == "pull":
        return remote.pull(force=bool(args.get("force")))
    return remote.status()


def tool_kb_search(args: dict) -> Any:
    if not kb.available(args.get("db_path", "")):
        return {"ok": False, "message": "知识库还没建。先跑 kiant_hoi4_kb_build。"}
    return kb.search(
        args["query"],
        args.get("db_path", ""),
        limit=int(args.get("limit", 20)),
        kind=args.get("kind", ""),
        source=args.get("source", ""),
        scope=args.get("scope", "auto"),
    )


def tool_kb_lookup(args: dict) -> Any:
    if not kb.available(args.get("db_path", "")):
        return {"ok": False, "message": "知识库还没建。先跑 kiant_hoi4_kb_build。"}
    return kb.lookup(
        args["kind"],
        args.get("db_path", ""),
        tag=args.get("tag", ""),
        limit=int(args.get("limit", 3)),
        context_lines=int(args.get("context_lines", 30)),
    )


def tool_kb_symbol(args: dict) -> Any:
    if not kb.available(args.get("db_path", "")):
        return {"ok": False, "message": "知识库还没建。先跑 kiant_hoi4_kb_build。"}
    return kb.find_symbol(args["name"], args.get("db_path", ""), limit=int(args.get("limit", 40)))


def tool_kb_note(args: dict) -> Any:
    action = args.get("action", "add")
    if action == "list":
        return kb.list_notes(args.get("db_path", ""), limit=int(args.get("limit", 50)))
    if action == "search":
        return kb.search(args["query"], args.get("db_path", ""), limit=int(args.get("limit", 20)))
    if not args.get("title") or not args.get("body"):
        return {"ok": False, "message": "action=add 需要 title 与 body"}
    return kb.add_note(args["title"], args["body"], args.get("tag", ""), args.get("db_path", ""))


def tool_kb_stats(args: dict) -> Any:
    if not kb.available(args.get("db_path", "")):
        return {
            "indexed": False,
            "hint": "还没建索引。kiant_hoi4_kb_build action=discover 先看能索引什么。",
            "game_dir": kb.find_game_dir() or "未找到",
            "user_dir": kb.find_user_dir() or "未找到",
        }
    out = kb.stats(args.get("db_path", ""))
    out["indexed"] = True
    return out


# --------------------------------------------------------------------------- #
# 体检校验器本身
# --------------------------------------------------------------------------- #

def tool_self_check(args: dict) -> Any:
    """把原版游戏目录当 mod 跑一遍，用「已知正确的语料」反向验证校验器。

    原版是标准答案：它跑出成百上千条 error，只有一种解释——校验器错了，
    不可能是原版错了。这个工具把这件事从「手写 Python」变成一次调用。

    判据是单向的，报告里必须说清楚：
      - 原版跑出错误 → 大概率是假阳性（误报），要逐类查
      - 原版跑出 0 条 → 至少没有系统性误报，**但不保证查得全**
    后者尤其重要：假阴性情不会在这个方法里暴露，只能靠变异测试。
    """
    vanilla = args.get("vanilla_path") or kb.find_game_dir()
    if not vanilla or not os.path.isdir(vanilla):
        return {
            "ok": False,
            "message": "找不到原版游戏目录。传 vanilla_path，或先跑 kiant_hoi4_kb_build 让它自动定位。",
            "searched": kb.find_game_dir() or "未自动找到",
        }

    deep = bool(args.get("deep", False))
    per_check = int(args.get("per_check", 10))
    names, vroot, external_loc = (None, "", None)
    if deep:
        names, vroot, external_loc = _kb_context(args.get("db_path", ""))

    result = checks.validate_mod(
        vanilla,
        deep=deep,
        kb_names=names,
        vanilla_root=vroot,
        external_loc=external_loc,
        per_check=max(per_check, 400),
        max_issues=max(int(args.get("max_issues", 200)), 4000),
    )
    summary = result["summary"]
    errors = summary["errors"]
    by_check = summary["by_check"]
    # 分项必须用 summary["breakdown"]——那是截断前的全量。
    # result["issues"] 是按 per_check 每类只留前 N 条的展示列表，
    # 拿它统计会把 localisation 的 2041 条读成 400 条（per_check 取 400）。
    breakdown = dict(summary["breakdown"])
    issues = result["issues"]

    # 语法类里「文件读到 EOF 还没闭合」——原版实测 19 处，文件真的少写右括号
    # （如 common/ideas/SOV.txt 末尾），游戏照常加载。引擎在 EOF 处自动收尾，
    # 所以这是宽容行为，不是原版写错，也不是必须修的错误。
    # 另外 .txt 扩展名下混着非脚本内容（字体许可证），也会落到语法检查里。
    loc_missing_n = breakdown["localisation_missing_key"]
    syntax_n = breakdown["syntax"]
    unclosed_n = breakdown["syntax_unclosed_at_eof"]

    # 「值得警惕」的量：语法/结构类 + 本地化里非缺键那部分。
    # 缺键已被抽样证实是原版真缺失，不算误报信号。
    suspicious = syntax_n + breakdown["localisation_other"]

    verdict_text = (
        f"按类别看：本地化缺键 {loc_missing_n} 条（原版确有真缺失，抽样核实过），"
        f"语法异常 {syntax_n} 条（其中 {unclosed_n} 条是「文件结尾未闭合」——"
        f"原版真的少写右括号，引擎在 EOF 自动收尾，属宽容行为）。"
    )
    if suspicious > 30:
        verdict_text += (
            " 语法/结构类偏多，值得挑几条回原文核对：如果是「原版这么写、引擎能跑、解析器读不懂」，"
            "那就是校验器的问题，按类修，不要按条改。"
        )
    else:
        verdict_text += " 没有大面积误报迹象。"

    out = {
        "errors": errors,
        "warnings": summary["warnings"],
        "by_check": by_check,
        "breakdown": breakdown,
        "total_issues": summary.get("total_issues", errors + summary["warnings"]),
        "verdict": verdict_text,
        "method": (
            "原版是「已知正确」的语料，判据是单向的：它跑出大量 error → 校验器大概率错了。"
            "**但「0 error」只说明没有系统性误报，不保证查得全**——"
            "假阴性在这个方法里完全看不见，要靠变异测试（tools/kiant-hoi4-mutate.py）兜。"
        ),
        "vanilla_root": vanilla,
        "deep": deep,
        "index": summary.get("index"),
    }

    if args.get("details"):
        out["issues"] = issues[: int(args.get("max_issues", 200))]
        out["shown_by_check"] = result["shown_by_check"]
        out["truncated"] = (
            len(issues) < summary.get("total_issues", 0)
            or any(result["shown_by_check"].get(k, 0) < v for k, v in by_check.items())
        )
    else:
        out["hint"] = "想看明细就再调一次并传 details=true。"
    return out


# --------------------------------------------------------------------------- #
# Preview & plan
# --------------------------------------------------------------------------- #

def tool_preview(args: dict) -> Any:
    mod_root, descriptor, _notes = checks.resolve_mod_root(args["mod_path"])
    deep = bool(args.get("deep", False))
    names, vanilla, external_loc = (None, "", None)
    if deep or kb.available(args.get("db_path", "")):
        names, vanilla, external_loc = _kb_context(args.get("db_path", ""))

    report = checks.validate_mod(
        mod_root, deep=deep, kb_names=names, vanilla_root=vanilla, external_loc=external_loc
    )
    loc = checks.scan_localisation(mod_root)["keys"]
    bundle = checks.collect_definitions(mod_root)

    name = os.path.basename(mod_root)
    version = "0.1.0"
    for cand in (descriptor, os.path.join(mod_root, "descriptor.mod")):
        if cand and os.path.isfile(cand):
            root, _ = cw.parse_file(cand)
            got = cw.as_text(getattr(cw.get_one(root, "name"), "value", None))
            if got:
                name = got
            ver = cw.as_text(getattr(cw.get_one(root, "version"), "value", None))
            if ver:
                version = ver
            break

    out_path = args.get("out_path") or os.path.join(mod_root, ".modkit", "preview.html")
    result = preview.render(
        mod_root=mod_root,
        out_path=out_path,
        name=name,
        version=version,
        definitions=bundle["definitions"],
        loc=loc,
        issues=report["issues"],
    )
    result["summary"] = report["summary"]
    return result


def tool_plan(args: dict) -> Any:
    mod_root, _desc, _notes = checks.resolve_mod_root(args["mod_path"])
    return planner.plan_action(
        mod_root,
        action=args.get("action", "status"),
        steps=args.get("steps"),
        step_id=args.get("step_id", ""),
        status=args.get("status", ""),
        title=args.get("title", ""),
        note=args.get("note", ""),
    )


# --------------------------------------------------------------------------- #
# Error book & solution pool
# --------------------------------------------------------------------------- #

def tool_error_book(args: dict) -> Any:
    action = args.get("action", "search")
    if action == "get":
        return playbook.get("error", args.get("id", ""), args.get("section", ""))
    if action == "list":
        out = playbook.list_entries(
            "error", symptom_class=args.get("symptom_class", ""), severity=args.get("severity", "")
        )
        out.pop("searched", None)
        return out
    if action == "stats":
        return playbook.stats()["error"]
    if action == "lint":
        return playbook.lint()
    return playbook.search(
        args.get("query", ""),
        kind="error",
        symptom_class=args.get("symptom_class", ""),
        severity=args.get("severity", ""),
        limit=int(args.get("limit", 6)),
    )


def tool_solutions(args: dict) -> Any:
    action = args.get("action", "search")
    if action == "get":
        return playbook.get("solution", args.get("id", ""), args.get("section", ""))
    if action == "list":
        out = playbook.list_entries("solution", status=args.get("status", ""))
        out.pop("searched", None)
        return out
    if action == "stats":
        return playbook.stats()["solution"]
    return playbook.search(
        args.get("query", ""),
        kind="solution",
        status=args.get("status", ""),
        limit=int(args.get("limit", 6)),
    )


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

TOOLS: dict[str, tuple[Callable[[dict], Any], dict]] = {
    "kiant_hoi4_self_check": (
        tool_self_check,
        {
            "description": (
                "体检校验器本身：把原版游戏目录当 mod 跑一遍。"
                "原版是「已知正确」的语料，所以它跑出成百上千条 error 只有一个解释——校验器错了。"
                "**改完校验逻辑之后就该跑这个**：假阳性比假阴性更致命，1 万条 error 没人会看，等于没检查。"
                "注意判据是单向的：0 error 只说明没有系统性误报，**不保证查得全**"
                "（假阴性要靠 tools/kiant-hoi4-mutate.py 的变异测试）。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vanilla_path": {
                        "type": "string",
                        "description": "原版游戏根目录，留空则自动定位（读知识库记录或常见 Steam 路径）",
                    },
                    "deep": {
                        "type": "boolean",
                        "description": "跑全类型校验器。需要知识库已索引原版，否则引用类检查会降级",
                    },
                    "db_path": {"type": "string", "description": "知识库路径，默认 ~/.kiant-hoi4-modkit/kb.sqlite"},
                    "per_check": {
                        "type": "integer",
                        "description": "每类最多返回几条明细，默认 10。原版量很大，别开太大",
                    },
                    "details": {
                        "type": "boolean",
                        "description": "是否连同问题明细一起返回。默认只给分类统计",
                    },
                    "max_issues": {"type": "integer", "description": "明细总上限，默认 200"},
                },
                "required": [],
            },
        },
    ),
    "kiant_hoi4_validate_mod": (
        tool_validate_mod,
        {
            "description": (
                "对钢铁雄心4 模组做结构化体检。默认检查描述文件、本地化 BOM/编码/键、"
                "语法括号、重复 id、缺失本地化键、事件 namespace。deep=true 时额外跑"
                "科技/贴图模型/图标引用/界面/事件钩子/国家历史/引擎常量七类校验器。"
                "任何改动后都应该先跑这一步。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mod_path": {"type": "string", "description": "mod 根目录，或外层 .mod 文件路径"},
                    "deep": {"type": "boolean", "description": "启用全类型校验器，跨文件引用检查需知识库支撑"},
                    "db_path": {"type": "string", "description": "知识库路径，默认 ~/.kiant-hoi4-modkit/kb.sqlite"},
                    "only_validators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "只跑指定校验器：technology/assets/sprites/ui/on_actions/history/defines",
                    },
                    "per_check": {
                        "type": "integer",
                        "description": "每类检查最多返回多少条明细，默认 25。大模组建议调小。",
                    },
                    "max_issues": {
                        "type": "integer",
                        "description": "明细总数上限，默认 200。summary.by_check 永远给出完整计数。",
                    },
                },
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_scaffold": (
        tool_scaffold,
        {
            "description": (
                "生成符合 1.19 语法的 HOI4 内容骨架，自动附带带 BOM 的本地化条目。"
                "kind 可选：mod / focus / event / decision / idea / scripted_effect / "
                "scripted_trigger / character / country_history / gfx_sprite / on_action / loc。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mod_path": {"type": "string"},
                    "kind": {"type": "string", "enum": list(scaffolder.SD) + ["loc"]},
                    "name": {"type": "string", "description": "内容标识，如 autobahn"},
                    "tag": {"type": "string", "description": "国家 TAG，如 GER"},
                    "namespace": {"type": "string", "description": "事件命名空间，默认取 tag 小写"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "icon": {"type": "string"},
                    "capital": {"type": "integer"},
                    "display_name": {"type": "string"},
                    "version": {"type": "string"},
                    "force": {"type": "boolean"},
                },
                "required": ["mod_path", "kind"],
            },
        },
    ),
    "kiant_hoi4_scan_localisation": (
        tool_scan_localisation,
        {
            "description": "单独扫描 localisation/：BOM、语言头、键格式、重复键。排查「界面显示键名」先跑这个。",
            "inputSchema": {
                "type": "object",
                "properties": {"mod_path": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_fix_localisation": (
        tool_fix_localisation,
        {
            "description": "修复本地化编码：补 UTF-8 BOM，GBK/GB18030 转 UTF-8。默认 dry_run=true 只报告。",
            "inputSchema": {
                "type": "object",
                "properties": {"mod_path": {"type": "string"}, "dry_run": {"type": "boolean"}},
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_find_duplicate_ids": (
        tool_find_duplicates,
        {
            "description": "查全 mod 范围内重复定义的事件/国策/精神/决议/角色 id，给出首次定义位置。定位「写了却不生效」。",
            "inputSchema": {
                "type": "object",
                "properties": {"mod_path": {"type": "string"}},
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_parse_script": (
        tool_parse_script,
        {
            "description": '把 Clausewitz 脚本解析成 JSON 树，可选 path_filter 下钻（如 "focus_tree>focus"）。读懂原版文件或核对结构时用。',
            "inputSchema": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}, "path_filter": {"type": "string"}},
                "required": ["file_path"],
            },
        },
    ),
    "kiant_hoi4_analyze_error_log": (
        tool_analyze_error_log,
        {
            "description": "解析 error.log：按源文件与消息模板聚类计数，归类为语法/重复/引用缺失/地图数据等并给出排查方向。不传路径时自动查找。",
            "inputSchema": {
                "type": "object",
                "properties": {"log_path": {"type": "string"}, "top_n": {"type": "integer"}},
            },
        },
    ),
    "kiant_hoi4_list_overrides": (
        tool_list_overrides,
        {
            "description": "对比 mod 与原版目录，分出「覆盖原版」与「新增」，读取 replace_path。评估兼容性与 submod 可行性。",
            "inputSchema": {
                "type": "object",
                "properties": {"mod_path": {"type": "string"}, "vanilla_path": {"type": "string"}},
                "required": ["mod_path", "vanilla_path"],
            },
        },
    ),
    "kiant_hoi4_kb_build": (
        tool_kb_build,
        {
            "description": (
                "建立/更新知识库索引。action=discover 先列出能索引的源（原版、已装模组、本地笔记）；"
                "action=build 真正建索引。索引后即可检索原版与其他 mod 的真实写法。"
                "首次全量可能数分钟，之后走增量。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["discover", "build"], "description": "默认 build"},
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "path": {"type": "string"},
                                "kind": {"type": "string", "enum": ["game", "mod", "notes"]},
                            },
                        },
                        "description": "显式指定源；省略则读 knowledge/sources.json 或自动发现",
                    },
                    "only": {"type": "string", "description": "逗号分隔的源名或类型，如 'game'、'notes'、'refs' 或 'mod:你的模组'"},
                    "local_dirs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "额外收入本地第二资料库的目录（绝对路径）。只在用户明确要求读取本地文件时用，"
                        "工具不会自己去扫目录",
                    },
                    "include_mods": {
                        "type": "boolean",
                        "description": "是否把已安装的第三方模组也收进来。默认 false——"
                        "装了几十个工坊模组时首次索引会被拖很久，且半成品模组会污染检索",
                    },
                    "skip_game": {"type": "boolean", "description": "跳过原版，只索引模组"},
                    "incremental": {"type": "boolean", "description": "默认 true，只处理变化的文件"},
                    "max_files_per_source": {"type": "integer", "description": "每个源最多索引多少文件，用于快速试跑"},
                    "loc_langs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "只索引这些语言的本地化，默认 english + simp_chinese。"
                        "传空数组 [] 表示不限（原版 10 种语言共 130 万条，会让构建从 2 分钟变成 9 分钟）",
                    },
                    "db_path": {"type": "string"},
                    "mods_root": {"type": "string", "description": "自定义模组目录，覆盖自动发现"},
                },
            },
        },
    ),
    "kiant_hoi4_kb_search": (
        tool_kb_search,
        {
            "description": (
                "在知识库里全文检索：脚本代码、本地化文本、笔记。"
                "查「某个 effect/trigger 怎么用」「中文文本在哪」都靠它。结果带源/文件/行号。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                    "kind": {
                        "type": "string",
                        "description": "限定文件类型：txt/gfx/gui/asset/lua/md。md 是游戏自带的 documentation，最权威",
                    },
                    "source": {"type": "string", "description": "限定源，如 vanilla 或 mod:你的模组"},
                    "scope": {
                        "type": "string",
                        "enum": ["auto", "platform", "local", "all"],
                        "description": "资料库层级。auto（默认）=先查平台库，命中就返回，没命中才退到本地；"
                        "platform 只查作者维护的平台库；local 只查本机（原版/笔记/模组）；all 两级一起查",
                    },
                    "db_path": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    ),
    "kiant_hoi4_kb_lookup": (
        tool_kb_lookup,
        {
            "description": (
                "取某类内容的真实范例代码。kind 可取 focus/idea/decision/event/tech/"
                "scripted_effect/scripted_trigger/character/on_action/sprite/entity/gui_window。"
                "写新内容前先看两三个原版实现，比凭记忆写可靠。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "tag": {"type": "string", "description": "按名称片段过滤，如 GER"},
                    "limit": {"type": "integer"},
                    "context_lines": {"type": "integer", "description": "每个范例摘多少行，默认 30"},
                    "db_path": {"type": "string"},
                },
                "required": ["kind"],
            },
        },
    ),
    "kiant_hoi4_kb_symbol": (
        tool_kb_symbol,
        {
            "description": "查一个标识符的所有定义位置与本地化文本。跨 mod 撞名、找某国策在哪定义时用。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "limit": {"type": "integer"},
                    "db_path": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    ),
    "kiant_hoi4_kb_note": (
        tool_kb_note,
        {
            "description": "本地资料库补充：把结论、踩坑记录、设计约定写成笔记存入知识库，之后可被检索到。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "search"]},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "tag": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                    "db_path": {"type": "string"},
                },
            },
        },
    ),
    "kiant_hoi4_kb_sync": (
        tool_kb_sync,
        {
            "description": (
                "同步作者维护的远端知识库（开源平台）。status 看本地缓存版本与远端是否一致；"
                "pull 拉取并缓存到本地，之后 kiant_hoi4_kb_build 会多出一个 remote 源。"
                "网络不可用时回退到上次缓存，并明确告知内容可能是旧的。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["status", "pull"], "description": "默认 status"},
                    "force": {"type": "boolean", "description": "pull 时即使版本一致也重新下载"},
                },
            },
        },
    ),
    "kiant_hoi4_kb_stats": (
        tool_kb_stats,
        {
            "description": "知识库现状：有哪些源、各类符号数量、本地化条目数、上次构建时间。判断索引是否够用。",
            "inputSchema": {"type": "object", "properties": {"db_path": {"type": "string"}}},
        },
    ),
    "kiant_hoi4_preview": (
        tool_preview,
        {
            "description": (
                "生成自包含 HTML 预览，不用开游戏：国策树按真实 x/y 坐标渲染并画前置连线，"
                "事件/决议/精神卡片带已解析文本，本地化覆盖率与问题清单一并呈现。"
                "改完内容看一眼就能判断结构对不对。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mod_path": {"type": "string"},
                    "out_path": {"type": "string", "description": "默认 <mod>/.modkit/preview.html"},
                    "deep": {"type": "boolean"},
                    "db_path": {"type": "string"},
                },
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_plan": (
        tool_plan,
        {
            "description": (
                "分阶段计划跟踪。action=init 建默认八阶段（骨架→设计→内容→本地化→校验→游戏内→兼容→发布）；"
                "status 看进度与下一步；update 标记完成；add 加步骤。同时写 .modkit/plan.json 与 ROADMAP.md。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "mod_path": {"type": "string"},
                    "action": {"type": "string", "enum": ["init", "status", "update", "add", "reset"]},
                    "steps": {"type": "array", "description": "字符串或 {id,title,depends,accept}"},
                    "step_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "active", "done", "blocked", "skipped"]},
                    "title": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["mod_path"],
            },
        },
    ),
    "kiant_hoi4_error_book": (
        tool_error_book,
        {
            "description": (
                "查错题本（references/91_error-book/）：18 条已实证的踩坑记录，每条含症状、错误做法、"
                "根因、标准化方案。**遇到问题第一步就查这里**，不要先猜。"
                "query 填你实际看到的现象（报错原文、界面上的错字），不要填原因——错题本按症状组织，"
                "不按原因组织。命中后 action=get 取完整方案直接照做。"
                "action=list 可列出全部，action=stats 看分布，action=lint 检查条目自身完整性。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "get", "list", "stats", "lint"],
                        "description": "默认 search",
                    },
                    "query": {
                        "type": "string",
                        "description": "症状描述。写现象不写原因，例如「科技页连线一条都没有」「中文全是问号」",
                    },
                    "id": {"type": "string", "description": "action=get 用，如 EB-003"},
                    "section": {
                        "type": "string",
                        "description": "只取某一节，如「标准化方案」。不填返回全文",
                    },
                    "symptom_class": {
                        "type": "string",
                        "enum": ["界面显示", "游戏内行为", "日志校验", "工具流程"],
                        "description": "按症状大类过滤",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["阻断", "严重", "一般", "轻微"],
                        "description": "按严重程度过滤",
                    },
                    "limit": {"type": "integer", "description": "最多返回几条，默认 6"},
                },
            },
        },
    ),
    "kiant_hoi4_solutions": (
        tool_solutions,
        {
            "description": (
                "查方案库（references/92_solutions/）：14 条**尚未验证**的解决思路，含旧插件未迁移的 9 个工具。"
                "错题本没命中时才来这里找方向。返回的 status 决定可信度："
                "upstream-only=旧插件有实现可直接抄，suspect=前提可能不成立，rejected=验证过不可行别再试，"
                "promoted=已固化进错题本。**用之前必须自己确认前提成立**，这里每条都可能错。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "get", "list", "stats"],
                        "description": "默认 search",
                    },
                    "query": {"type": "string", "description": "关键词，不填则列出全部"},
                    "id": {"type": "string", "description": "action=get 用，如 SOL-001"},
                    "section": {"type": "string", "description": "只取某一节"},
                    "status": {
                        "type": "string",
                        "enum": ["idea", "upstream-only", "suspect", "rejected", "promoted"],
                        "description": "按状态过滤",
                    },
                    "limit": {"type": "integer", "description": "最多返回几条，默认 6"},
                },
            },
        },
    ),
}


# --------------------------------------------------------------------------- #
# Protocol plumbing
# --------------------------------------------------------------------------- #

def _respond(req_id: Any, result: Any) -> None:
    payload = {"jsonrpc": "2.0", "id": req_id, "result": result}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error(req_id: Any, code: int, message: str) -> None:
    payload = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(req: dict) -> None:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        _respond(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": (
                    "钢铁雄心4 模组开发平台。改完文件先 kiant_hoi4_validate_mod（deep=true 更全）；"
                    "写新内容前用 kiant_hoi4_kb_lookup 看原版实现；"
                    "游戏内表现异常先 kiant_hoi4_analyze_error_log；"
                    "想不开游戏看效果用 kiant_hoi4_preview。"
                ),
            },
        )
        return

    if method in ("notifications/initialized", "notifications/cancelled"):
        return

    if method == "ping":
        _respond(req_id, {})
        return

    if method == "tools/list":
        _respond(
            req_id,
            {
                "tools": [
                    {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
                    for name, (_fn, spec) in TOOLS.items()
                ]
            },
        )
        return

    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in TOOLS:
            _error(req_id, -32602, f"unknown tool: {name}")
            return
        fn = TOOLS[name][0]
        try:
            result = fn(args)
            _respond(req_id, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]})
        except Exception as exc:  # keep the server alive, surface the reason
            sys.stderr.write(traceback.format_exc(limit=3))
            _respond(
                req_id,
                {"content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}], "isError": True},
            )
        return

    if method == "resources/list":
        _respond(req_id, {"resources": []})
        return

    if method == "prompts/list":
        _respond(req_id, {"prompts": []})
        return

    if req_id is not None:
        _error(req_id, -32601, f"method not found: {method}")


def serve() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stderr.write(f"bad json line: {line[:120]}\n")
            continue
        if isinstance(req, list):
            for item in req:
                handle(item)
        else:
            handle(req)


def main(argv: list[str]) -> int:
    if "--list" in argv:
        for name, (_fn, spec) in TOOLS.items():
            print(f"{name}\t{spec['description'][:70]}...")
        return 0
    if "--call" in argv:
        idx = argv.index("--call")
        name = argv[idx + 1]
        args = json.loads(argv[idx + 2]) if len(argv) > idx + 2 else {}
        if name not in TOOLS:
            print(json.dumps({"error": f"unknown tool {name}"}, ensure_ascii=False))
            return 2
        try:
            print(json.dumps(TOOLS[name][0](args), ensure_ascii=False, indent=2))
        except (FileNotFoundError, ValueError, KeyError) as exc:
            print(json.dumps({"error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False, indent=2))
            return 1
        return 0
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

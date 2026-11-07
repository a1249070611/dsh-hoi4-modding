"""Static analysis for Hearts of Iron IV mod folders.

Everything here works offline, on files only. No game install required unless
you explicitly ask for a vanilla comparison.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from typing import Any, Iterable

import cw

SCRIPT_EXT = {".txt", ".gui", ".gfx", ".asset", ".mod"}
LOC_HEADER_RE = re.compile(r"^\s*(l_[a-z]+(?:_[a-z]+)*)\s*:\s*\d*\s*$")
LOC_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9_.\-]+)\s*:\s*\d*\s+"(.*)"\s*$')
EVENT_KINDS = {
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
    "country_events",
}
# 通配符只能出现在最后一段："1.19.*" 合法，"1.*" 会让 error.log 报
# Invalid supported_version；"1.19.x" 也不是合法写法。
SUPPORTED_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)*(?:\.\*)?$")


def _strip_trailing_comment(line: str) -> str:
    """剥掉本地化行末的注释，保留引号内的一切。

    原版实测（1.19.4.2）：localisation/ 下 411 个文件、19061 行是
    `KEY: "文本" # 注释` 的形态。旧正则要求整行以右引号结尾，这些行全部
    被判成「无法解析的行」，连带把键漏收——149170 个键里少收 15955 个
    （+10.7%），然后这些键在 check_missing_loc 里又变成「缺少本地化」的 error。

    做法：找最后一个右引号，只有它后面还有非空内容且含 # 时才截断。
    不用「第一个 # 之前」那种切法——文本里的 # 是合法字符（颜色码 #FF0000、
    标题 #），切在引号内会把译文改坏。
    """
    i = line.rfind('"')
    if i < 0:
        return line
    tail = line[i + 1:]
    if tail.strip() and "#" in tail:
        return line[: i + 1]
    return line


# --------------------------------------------------------------------------- #
# Filesystem helpers
# --------------------------------------------------------------------------- #

def _resolve_mod_path_target(target: str, *bases: str) -> str:
    """把 descriptor 的 path 字段解析成候选目录，命中第一个存在的。

    相对 path 的基准有两种惯例，都真实存在：
      - `path="mod/mymod"` 相对 **用户数据目录**（mod/ 的父级）—— wiki 与启动器惯例
      - `path="mymod"` 相对 **mod/ 目录本身**（.mod 文件所在处）
    只试一个基准会让另一种惯例整条解析失败，所以两个都试。
    """
    if os.path.isabs(target):
        return os.path.normpath(target)
    for base in bases:
        candidate = os.path.normpath(os.path.join(base, target))
        if os.path.isdir(candidate):
            return candidate
    # 都不存在也返回最后一个候选，让调用方报「目录不存在」
    return os.path.normpath(os.path.join(bases[0], target)) if bases else os.path.normpath(target)


def resolve_mod_root(path: str) -> tuple[str, str, list[dict]]:
    """Return (mod_folder, descriptor_path_or_empty, notes)."""
    notes: list[dict] = []
    path = os.path.abspath(path)
    if os.path.isfile(path) and path.lower().endswith(".mod"):
        # The .mod file sits in mod/ and points at its content folder.
        root, errs = cw.parse_file(path)
        notes.extend(errs)
        target = cw.as_text(getattr(cw.get_one(root, "path"), "value", None))
        if target:
            here = os.path.dirname(path)
            # 相对基准有两个：.mod 所在目录，和它的父级（用户数据目录）。
            candidate = _resolve_mod_path_target(target, here, os.path.dirname(here))
            if os.path.isdir(candidate):
                return candidate, path, notes
            notes.append(
                {"level": "error", "message": f".mod points to '{target}' but that folder does not exist"}
            )
        return os.path.dirname(path), path, notes

    if not os.path.isdir(path):
        raise FileNotFoundError(f"not a mod folder: {path}")

    descriptor = os.path.join(path, "descriptor.mod")
    if os.path.isfile(descriptor):
        return path, descriptor, notes

    # Sometimes the user points at mod/ itself, which holds many .mod files.
    mods = [f for f in os.listdir(path) if f.lower().endswith(".mod")]
    if mods and not os.path.isdir(os.path.join(path, "common")):
        for name in mods:
            mod_file = os.path.join(path, name)
            root, _ = cw.parse_file(mod_file)
            target = cw.as_text(getattr(cw.get_one(root, "path"), "value", None))
            if not target:
                continue
            candidate = _resolve_mod_path_target(target, path, os.path.dirname(path))
            if os.path.isdir(candidate):
                return candidate, mod_file, notes
        notes.append(
            {"level": "warn", "message": "folder contains .mod files but none point at an existing mod folder"}
        )
    return path, "", notes


# 这些 .txt 是纯文本附件，不是 Clausewitz 脚本。
# 典型是模组根目录的 Credits.txt —— 用脚本语法去解析它会报一堆「单引号不是字符串定界符」。
NON_SCRIPT_NAMES = frozenset(
    {"credits.txt", "readme.txt", "changelog.txt", "license.txt", "notice.txt", "install.txt"}
)


# HOI4 只会从这些顶层目录加载脚本。mod 根目录下的 .txt 是给人看的
# （Credits.txt / "Unique Commanders IDS.txt" 之类笔记），拿去解析会报一堆假语法错误。
SCRIPT_TOPS = frozenset(
    {
        "common",
        "events",
        "history",
        "gfx",
        "interface",
        "map",
        "sound",
        "music",
        "units",
        "localisation",
        "tutorial",
        "ai",
        "portraits",
    }
)


def _is_script_path(mod_path: str, path: str) -> bool:
    r = rel(mod_path, path)
    head = r.split("/", 1)[0].lower()
    return head in SCRIPT_TOPS


def iter_mod_files(mod_path: str, exts: Iterable[str] = SCRIPT_EXT) -> list[str]:
    wanted = {e.lower() for e in exts}
    found: list[str] = []
    for base, dirs, files in os.walk(mod_path):
        dirs[:] = [d for d in dirs if d not in {".git", ".svn", "__pycache__", "node_modules"}]
        for name in files:
            if name.lower() in NON_SCRIPT_NAMES:
                continue
            if os.path.splitext(name)[1].lower() not in wanted:
                continue
            full = os.path.join(base, name)
            if not _is_script_path(mod_path, full):
                continue
            found.append(full)
    found.sort()
    return found


def rel(mod_path: str, path: str) -> str:
    try:
        return os.path.relpath(path, mod_path).replace("\\", "/")
    except ValueError:  # pragma: no cover - different drives on Windows
        return path.replace("\\", "/")


# --------------------------------------------------------------------------- #
# Descriptor checks
# --------------------------------------------------------------------------- #

def check_descriptor(mod_path: str, descriptor_path: str, notes: list[dict]) -> dict:
    issues: list[dict] = []
    info: dict[str, Any] = {"mod_folder": mod_path, "descriptor": None, "keys": {}}

    candidates: list[str] = []
    if descriptor_path and os.path.isfile(descriptor_path):
        candidates.append(descriptor_path)
    outer = os.path.join(os.path.dirname(mod_path), os.path.basename(mod_path) + ".mod")
    if os.path.isfile(outer) and outer not in candidates:
        candidates.append(outer)

    if not candidates:
        issues.append(
            {
                "level": "error",
                "file": None,
                "message": "找不到描述文件：mod 根目录需要 descriptor.mod，且 mod/ 父目录需要同名 .mod 文件",
                "hint": "两个文件缺一不可，否则启动器里看不到这个 mod。",
            }
        )
        info["issues"] = issues
        return info

    info["descriptor"] = [rel(os.path.dirname(candidates[0]), c) for c in candidates]
    per_file: dict[str, dict] = {}
    for cand in candidates:
        root, errs = cw.parse_file(cand)
        fname = os.path.basename(cand)
        for e in errs:
            issues.append({"level": "error", "file": fname, **e})
        keys = {s.key: cw.as_text(s.value) for s in cw.stmts(root)}
        info["keys"].update(keys)
        per_file[fname] = keys

        # 描述文件本身不能有 BOM。启动器能容忍的情况居多，但创意工坊上传链路读它，
        # 出问题时现象是「名字变问号」而不是报错，极难定位，所以这里提示一句。
        try:
            with open(cand, "rb") as fh:
                raw_head = fh.read(3)
            if raw_head == b"\xef\xbb\xbf":
                issues.append(
                    {
                        "level": "warn",
                        "file": fname,
                        "message": "描述文件带 UTF-8 BOM",
                        "hint": "描述文件按无 BOM 保存（与 .yml 相反）。BOM 会让首个字段名被读成怪字符，"
                        "表现为 mod 名或版本显示异常。",
                    }
                )
        except OSError:
            pass

        # 预览图字段名是 picture，不是 thumbnail。
        if "thumbnail" in keys:
            issues.append(
                {
                    "level": "warn",
                    "file": fname,
                    "message": '预览图字段写成了 thumbnail，应为 picture',
                    "hint": '正确写法：picture="thumbnail.png"（值是文件名，字段名是 picture）。'
                    "写成 thumbnail= 时启动器会报 Unexpected token，预览图不显示。",
                }
            )
        if "picture" in keys:
            thumb = keys["picture"]
            if thumb and not os.path.isfile(os.path.join(os.path.dirname(cand), thumb)):
                issues.append(
                    {
                        "level": "warn",
                        "file": fname,
                        "message": f'picture="{thumb}" 指向的图片不存在',
                        "hint": "预览图放在 mod 文件夹根目录，文件名区分大小写。缺图不影响游戏，只是工坊里没有封面。",
                    }
                )

        for st in cw.get_all(root, "replace_path"):
            val = cw.as_text(st.value)
            if val and val not in info.setdefault("replace_paths", []):
                info["replace_paths"].append(val)

        for st in cw.get_all(root, "dependencies"):
            if isinstance(st.value, cw.Block):
                # 标准写法是裸字符串 dependencies = { "base_mod" }（解析成
                # Scalar）。只遍历 stmts() 恒为空，曾导致所有依赖判定失效、
                # 汉化子模组被误刷几千条缺键 error。entries() 统一两种形态。
                deps = [name for name, _val in cw.entries(st.value)]
                info.setdefault("dependencies", []).extend(d for d in deps if d)

        is_outer = os.path.basename(cand) != "descriptor.mod"
        required = ["name", "supported_version"]
        if is_outer:
            required.append("path")
        for key in required:
            if key not in keys:
                issues.append(
                    {
                        "level": "error",
                        "file": os.path.basename(cand),
                        "message": f"缺少必需字段 {key}",
                        "hint": "外层 .mod 必须含 path；两个文件都应有 name 和 supported_version。",
                    }
                )

        sv = keys.get("supported_version", "")
        if sv and not SUPPORTED_VERSION_RE.match(sv):
            issues.append(
                {
                    "level": "error",
                    "file": os.path.basename(cand),
                    "message": f'supported_version="{sv}" 格式不合法',
                    "hint": '正确写法形如 "1.19.*"、 "1.19.4" 或 "1.19.4.2"；'
                    '通配符只能在最后一段，"1.*" 会让 error.log 报 Invalid supported_version，'
                    '"1.19.x" 也不是合法写法。',
                }
            )
        elif sv and not sv.startswith("1.19"):
            issues.append(
                {
                    "level": "warn",
                    "file": fname,
                    "message": f'supported_version="{sv}" 不是当前主版本 1.19.*',
                    "hint": "它只影响启动器与创意工坊的兼容提示，不阻止引擎加载；"
                    "但标错版本会让玩家以为不能用。",
                }
            )

        if is_outer:
            path_val = keys.get("path", "")
            if path_val:
                if any(ord(ch) > 127 for ch in path_val):
                    issues.append(
                        {
                            "level": "warn",
                            "file": fname,
                            "message": f'path 含非 ASCII 字符：{path_val}',
                            "hint": "中文用户名或中文文件夹名会让启动器能列出这个 mod、但进游戏后内容完全不生效。"
                            '把 mod 目录整个挪到纯 ASCII 路径下（如 D:\\mods\\mymod），再改 path。',
                        }
                    )
                if "\\" in path_val:
                    issues.append(
                        {
                            "level": "warn",
                            "file": fname,
                            "message": 'path 里用了反斜杠 \\',
                            "hint": "Clausewitz 脚本里反斜杠是转义符，路径一律用正斜杠 /。"
                            '写成 path="C:/mods/mymod" 而不是 "C:\\mods\\mymod"。',
                        }
                    )
                # Paradox 解析 path 时以「用户数据目录」（mod/ 的父级）为基准，
                # 但社区里两种写法都有人用，所以两个基准都试。
                bases = [os.path.dirname(cand), os.path.dirname(os.path.dirname(cand))]
                candidates_path = (
                    [path_val]
                    if os.path.isabs(path_val)
                    else [os.path.normpath(os.path.join(b, path_val)) for b in bases]
                )
                if not any(os.path.isdir(p) for p in candidates_path):
                    sibling = os.path.join(os.path.dirname(cand), os.path.basename(path_val.rstrip("/\\")))
                    if os.path.isdir(sibling):
                        issues.append(
                            {
                                "level": "warn",
                                "file": os.path.basename(cand),
                                "message": f'path="{path_val}" 在当前目录布局下解析不到，但同级存在同名文件夹',
                                "hint": "把这两个项目（.mod 与同名文件夹）一起放进 文档/Paradox Interactive/Hearts of Iron IV/mod/ 后即可正常工作。",
                            }
                        )
                    else:
                        issues.append(
                            {
                                "level": "error",
                                "file": os.path.basename(cand),
                                "message": f'path="{path_val}" 指向的目录不存在',
                                "hint": '相对路径以 mod 目录的父级为基准，惯例写成 path="mod/<文件夹名>"。',
                            }
                        )

    # replace_path 必须在两个描述文件里都写。只写一个时游戏照常加载、不报错，
    # 只是替换不生效——文件看起来完全正确，所以这条靠自己几乎发现不了。
    if len(per_file) >= 2 and "descriptor.mod" in per_file:
        outer_name = next((n for n in per_file if n != "descriptor.mod"), None)
        if outer_name:
            has_o = "replace_path" in per_file[outer_name]
            has_i = "replace_path" in per_file["descriptor.mod"]
            if has_o != has_i:
                missing = "descriptor.mod" if has_o else outer_name
                issues.append(
                    {
                        "level": "warn",
                        "file": missing,
                        "message": "replace_path 只写在了一个描述文件里",
                        "hint": "外层 .mod 与内层 descriptor.mod 都要写同样的 replace_path，"
                        "只写一个会静默不生效。",
                    }
                )

    if not os.path.isfile(os.path.join(mod_path, "descriptor.mod")):
        issues.append(
            {
                "level": "warn",
                "message": "mod 文件夹内缺少 descriptor.mod（部分工具依赖它读取元数据）",
                "hint": "把外层 .mod 内容复制进来并去掉 path 一行即可。",
            }
        )

    # Cross-check name consistency between the two descriptors.
    names = set()
    for cand in candidates:
        root, _ = cw.parse_file(cand)
        val = cw.as_text(getattr(cw.get_one(root, "name"), "value", None))
        if val:
            names.add(val)
    if len(names) > 1:
        issues.append(
            {
                "level": "warn",
                "message": f"两个描述文件里的 name 不一致：{sorted(names)}",
                "hint": "启动器按外层 .mod 显示，但创意工坊上传读 descriptor.mod，容易名字对不上。",
            }
        )

    for n in notes:
        issues.append({**n, "file": os.path.basename(descriptor_path) if descriptor_path else None})

    info["issues"] = issues
    return info


# --------------------------------------------------------------------------- #
# Localisation
# --------------------------------------------------------------------------- #

def scan_localisation(mod_path: str) -> dict:
    """Parse every .yml under localisation/. Returns keys + issues."""
    loc_root = os.path.join(mod_path, "localisation")
    result: dict[str, Any] = {
        "root": "localisation" if os.path.isdir(loc_root) else None,
        "files": 0,
        "keys": {},
        "issues": [],
    }
    if not os.path.isdir(loc_root):
        result["issues"].append(
            {
                "level": "error",
                "message": "没有 localisation 文件夹",
                "hint": "所有界面文本都必须在这里定义，否则游戏里显示为键名本身。",
            }
        )
        return result

    for base, _dirs, files in os.walk(loc_root):
        for name in files:
            if not name.lower().endswith(".yml"):
                continue
            # languages.yml 是语言清单的元数据（l_english 一节里列 l_english、
            # l_french……这些是「语言名」，不是词条），不是本地化内容。
            # 当成词条扫会产出 90 条假的「重复的键 l_english」。
            if name.lower() == "languages.yml" and os.path.abspath(base) == os.path.abspath(loc_root):
                continue
            path = os.path.join(base, name)
            result["files"] += 1
            relpath = rel(mod_path, path)
            raw = open(path, "rb").read()

            if not raw.startswith(b"\xef\xbb\xbf"):
                result["issues"].append(
                    {
                        "level": "error",
                        "file": relpath,
                        "message": "缺少 UTF-8 BOM",
                        "hint": "Paradox 只认带 BOM 的 UTF-8；无 BOM 会导致整个文件被忽略。用本插件的 kiant_hoi4_fix_localisation 或编辑器另存为「UTF-8 with BOM」。",
                    }
                )
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                result["issues"].append(
                    {
                        "level": "error",
                        "file": relpath,
                        "message": f"不是合法 UTF-8（{exc.reason}，偏移 {exc.start}）",
                        "hint": "中文 Windows 下编辑器常默认存成 GBK/GB18030，需显式转成 UTF-8。",
                    }
                )
                text = raw.decode("utf-8-sig", errors="replace")

            # 只按 \n 切分，**不要用 splitlines()**。
            # str.splitlines() 认的换行符远不止 \r\n：它还认 U+0085(NEL)、
            # U+2028、U+2029、\v、\f。原版 localisation/braz_por/
            # research_l_braz_por.yml:693 的文本里有 \n 紧接 U+0085（作者本意
            # 是转义换行 + 一个错码字符），splitlines 会在那里把一行劈成两行，
            # 后半截 "ão são só os submarinos..." 没有键名前缀，于是报
            # 「无法解析的行」——纯属解析器自造的假错。引擎只按 \n 分行。
            #
            # 但必须先归一化 \r\n：Windows 上的文件是 CRLF，直接 split("\n")
            # 会让每行尾部留一个 \r，语言头 `l_english:` 匹配不上，
            # 整文件被判「格式不对」。这是换成 split 之后最容易踩的坑。
            lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
            header_seen = False
            any_entries = False
            seen_keys: dict[str, int] = {}
            for lineno, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                # 注释行允许前置空白。原版和很多 mod 都写成 “ # xxx”，
                # 之前只认第 0 列的 #，于是缩进注释被当成「无法解析的行」刷警告。
                if line.lstrip().startswith("#"):
                    continue
                m = LOC_HEADER_RE.match(line)
                if m:
                    header_seen = True
                    continue
                # 行尾注释：原版 411 个文件、19061 行这么写，例如
                #   DEN_x_desc: "$DEN_y_desc$" #TODO_DANNE; Refine if there is time
                #   FRLOC_A: "Sarajéviens" ## EN: Governorate of Sarajevo
                # 只剥最后一个右引号**之后**的注释，绝不动引号内的 #——
                # 本地化文本里 # 是合法字符（颜色码、标题），引号里一切照旧。
                line = _strip_trailing_comment(line)
                e = LOC_ENTRY_RE.match(line)
                if e:
                    key, value = e.group(1), e.group(2)
                    if key in seen_keys:
                        result["issues"].append(
                            {
                                "level": "warn",
                                "file": relpath,
                                "line": lineno,
                                "message": f"重复的键 {key}（首次出现在第 {seen_keys[key]} 行）",
                                "hint": "后出现的会覆盖先出现的；若是刻意覆盖原版文本，请确认加载顺序。",
                            }
                        )
                    seen_keys[key] = lineno
                    result["keys"][key] = value
                    any_entries = True
                    continue
                if line.rstrip().endswith('"') and ":" in line:
                    # Key exists but formatting is off — most often a stray tab.
                    result["issues"].append(
                        {
                            "level": "warn",
                            "file": relpath,
                            "line": lineno,
                            "message": "疑似词条行格式不对，无法解析",
                            "hint": '标准格式是 ` KEY:0 "文本"`，冒号和版本号之间不要有空格外的字符。',
                        }
                    )
                else:
                    result["issues"].append(
                        {
                            "level": "warn",
                            "file": relpath,
                            "line": lineno,
                            "message": "无法解析的行",
                            "hint": "常见原因：文本里的引号没有转义，或一行里塞了多个键。",
                        }
                    )

            if not header_seen:
                # 整文件只有注释、一条有效词条都没有时，不报缺语言头。
                # 原版就有一个这样的文件（localisation/french/career_profile_zelosissimo.yml，
                # 全文是 LocEditor 生成的 "# === [LocEditor:RedundantFile] ..." 说明），
                # 它本来就该被删，但没有语言头也不算「整文件不生效」——里面没内容可生效。
                if any_entries:
                    result["issues"].append(
                        {
                            "level": "error",
                            "file": relpath,
                            "message": "缺少语言头（如 l_english:）",
                            "hint": "文件第一行必须是 l_english: / l_simp_chinese: 之类的语言声明，否则整文件不生效。",
                        }
                    )
    return result


# --------------------------------------------------------------------------- #
# Definition extraction
# --------------------------------------------------------------------------- #

# 只要出现其中任意一个，就说明这个 country_event 块是**定义**而非预约。
# 预约写法 `country_event = { id = X days = 958 random_hours = 12 }` 只有
# id 和计数字段，没有任何内容键。
EVENT_DEF_MARKERS = frozenset(
    {
        "title",
        "desc",
        "option",
        "immediate",
        "trigger",
        "is_triggered_only",
        "fire_only_once",
        "mean_time_to_happen",
        "picture",
        "major",
        "hidden",
        "news_desc_long",
        "news_desc_medium",
        "news_desc_short",
        "after",
    }
)


def _looks_like_event_definition(block: cw.Block) -> bool:
    """区分「事件定义」与「事件预约」。

    history/countries/*.txt 里会写
        country_event = { id = MUN_czech.6 days = 958 random_hours = 12 }
    这是给国家排定未来触发时间，事件本体定义在 events/ 下。
    旧代码不看结构，凡 country_event 块就收进定义表，于是这条预约被当成
    定义校验，报出「MUN_czech.6 的选项没有 name」——定义在别处，纯误报。
    """
    for st in cw.stmts(block):
        if st.key.lower() in EVENT_DEF_MARKERS:
            return True
    return False


def _stmt_value_text(block: cw.Block | cw.Node, key: str) -> str:
    # 用大小写不敏感查找：原版真实存在 `Hidden = yes`、`Picture = ...` 这类
    # 首字母大写写法（实测 10 处），引擎照样认，精确匹配会把字段读成空。
    st = cw.get_one_ci(block, key)
    if st is None:
        return ""
    return cw.as_text(st.value)


def _stmt_keys(block: cw.Block | cw.Node, key: str) -> list[str]:
    """把一个字段可能指向的**所有**本地化键取出来。

    事件的 title / desc 允许写成条件块，而且可以重复出现多次：

        desc = {
            text = iceland_events.17.desc_kingdom
            trigger = { ROOT = { tag = DEN } }
        }
        desc = {
            text = iceland_events.17.desc_generic
            trigger = { ROOT = { ... } }
        }

    原版 1.19.4.2 实测：块形式 desc 214 处、title 18 处，块内声明的
    512 + 46 个键全部真实存在。旧代码用 get_one().as_text() 取值，
    块 → 返回空串 → 整段声明被静默丢弃，于是 140 个事件被判「缺正文键」。

    返回值同时覆盖两种写法，调用方用 need_any() 判定即可。
    """
    out: list[str] = []
    for st in cw.get_all_ci(block, key):
        if isinstance(st.value, cw.Scalar):
            v = st.value.value
            if v:
                out.append(v)
        elif isinstance(st.value, cw.Block):
            # 块形式：键写在 text = 里，trigger 是分支条件，不是键。
            for sub in cw.get_all_ci(st.value, "text"):
                v = cw.as_text(sub.value)
                if v:
                    out.append(v)
    return out


def _stmt_sprites(block: cw.Block | cw.Node, key: str) -> list[str]:
    """取出一个字段引用的**所有** sprite 名，标量与条件块两种写法都认。

    原版 1.19.4.2 实测三种块结构互不相同，不能一套逻辑通用：

    1) 国策 icon —— sprite 名直接当语句键，值是条件（44 处）
           icon = {
               GFX_focus_A = { has_government = democratic }
               GFX_focus_B = yes
           }

    2) 决议 icon —— sprite 名写在 key = 里（66 处）
           icon = {
               key = GFX_decision_foo
               trigger = { original_tag = USA }
           }

    3) 其余（标量）—— 直接是 sprite 名
           icon = GFX_focus_bar

    旧代码统一走 as_text()，块一律返回空串后静默跳过，等于这三类引用
    在 deep 校验里完全不存在：引用了不存在的贴图也不会报。
    """
    out: list[str] = []
    # 字段名本身用不敏感查找（`Picture = ...` 原版有 8 处）。
    # 但块内的 sprite 名是**标识符**，必须原样保留大小写，不能折叠。
    for st in cw.get_all_ci(block, key):
        v = st.value
        if isinstance(v, cw.Scalar):
            if v.value:
                out.append(v.value)
            continue
        if not isinstance(v, cw.Block):
            continue
        # 结构 2：显式 key =
        key_st = cw.get_one_ci(v, "key")
        keyed = cw.as_text(key_st.value) if key_st else ""
        if keyed:
            out.append(keyed)
            continue
        # 结构 1：sprite 名当语句键。
        # 原版实测 108 处以这种方式写（另有 2 处结构 2），块内语句键
        # 100% 是 sprite 名，没有例外；条件表达式在值里（嵌套块），
        # 不在键上，所以这里不需要过滤任何「字段名」。
        for sub in cw.stmts(v):
            out.append(sub.key)
    # 去重但保序：同一 sprite 在一个块里可能因条件重复出现
    seen: set[str] = set()
    uniq: list[str] = []
    for s in out:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)
    return uniq


def _focus_prereq(block: cw.Node) -> list[str]:
    out: list[str] = []
    if not isinstance(block, cw.Block):
        return out
    for st in cw.get_all(block, "prerequisite"):
        if isinstance(st.value, cw.Block):
            for ref in cw.get_all(st.value, "focus"):
                val = cw.as_text(ref.value)
                if val:
                    out.append(val)
    return out


# 决议块独有的“签名”字段。分类块（common/decisions/categories/）里的
# on_map_area / priority / icon / visible / allowed 看起来也像块，但那是分类字段，
# 不是决议。只认这些签名键，就能把两者干净切开。
#
# 注意：target_trigger / target_root_trigger / state_target / highlight_states
# 绝对不能放进来 —— on_map_area = { state=.. name=.. target_root_trigger={..} }
# 里就有它们，一旦当签名就会把每个 on_map_area 当成一条决议。
DECISION_SIGNS = frozenset(
    {
        "available",
        "complete_effect",
        "remove_effect",
        "cancel_effect",
        "timeout_effect",
        "custom_cost_text",
        "cost",
        "days_remove",
        "days_re_enable",
        "days_mission_timeout",
        "mission_timeout",
        "fire_only_once",
        "targets",
        "selectable_mission",
        "ai_will_do",
        "is_good",
        "activation",
        "fixed_random_seed",
    }
)


def _looks_like_decision(block: cw.Node) -> bool:
    """按签名键判断一个二级块到底是「决议」还是「分类字段」。

    categories/*.txt 里普遍出现 on_map_area = { state=.. name=.. zoom=.. }、
    priority = { base = 8 }，之前被当成决议收进定义表，于是全模组刷出几百条
    「decision id 'on_map_area' 重复定义」。只要有一条签名键就认定是决议。
    """
    if not isinstance(block, cw.Block):
        return False
    for st in cw.stmts(block):
        if st.key in DECISION_SIGNS:
            return True
    return False


def _character_probe(block: cw.Node) -> tuple[bool, str]:
    """判断一个块是不是角色定义，并取出显示名。

    三种真实布局都要认：
      char = { name = X portraits = {...} }
      char = { instance = { name = X portraits = {...} } }      ← DLC 分支写法
      TAG  = { char = { ... } }                                  ← 国家容器
    只看固定深度会在第二种上炸出几百条假重复（instance 被当成角色 id）。
    """
    if not isinstance(block, cw.Block):
        return False, ""
    nm = cw.get_one(block, "name")
    if nm is not None:
        return True, cw.as_text(nm.value)
    if cw.get_one(block, "portraits") is not None:
        return True, ""
    inst = cw.get_one(block, "instance")
    if inst is not None and isinstance(inst.value, cw.Block):
        return True, _stmt_value_text(inst.value, "name")
    return False, ""


def _looks_like_character(block: cw.Node) -> bool:
    return _character_probe(block)[0]


def collect_definitions(mod_path: str) -> dict:
    """Gather every id the mod declares, with file + line, plus parse errors."""
    defs: dict[str, list[dict]] = defaultdict(list)
    parse_errors: list[dict] = []
    namespaces: list[dict] = []

    for path in iter_mod_files(mod_path, {".txt"}):
        relpath = rel(mod_path, path)
        try:
            root, errs = cw.parse_file(path)
        except OSError as exc:  # pragma: no cover - unreadable file
            parse_errors.append({"file": relpath, "level": "error", "message": str(exc)})
            continue
        for e in errs:
            parse_errors.append({"file": relpath, **e})

        lower = relpath.lower()

        # --- events ------------------------------------------------------- #
        for ns in cw.get_all(root, "add_namespace"):
            namespaces.append({"namespace": cw.as_text(ns.value), "file": relpath, "line": ns.line})

        for kind in EVENT_KINDS:
            for st in cw.get_all(root, kind):
                if not isinstance(st.value, cw.Block):
                    continue
                # history/ 里的 country_event = { id = X days = N } 是「预约触发」，
                # 不是事件定义。原版 history/countries/CZE - Czechoslovakia.txt:639
                # 就有一条 MUN_czech.6（唯一一例，但校验器会把它当定义，进而报
                # 「选项没有 name」——定义在别处，那次告警纯属误报）。
                # 区分靠特征键：定义一定有 title/desc/option/immediate/trigger/
                # is_triggered_only 里的至少一个，预约只有 id + 计数字段。
                if not _looks_like_event_definition(st.value):
                    continue
                eid = _stmt_value_text(st.value, "id")
                if not eid:
                    parse_errors.append(
                        {
                            "file": relpath,
                            "line": st.line,
                            "level": "error",
                            "message": f"{kind} 缺少 id",
                            "hint": "事件 id 必须写成 <namespace>.<数字>，且 namespace 需在文件顶部 add_namespace 声明。",
                        }
                    )
                    continue
                defs["event"].append(
                    {
                        "id": eid,
                        "file": relpath,
                        "line": st.line,
                        "title": _stmt_value_text(st.value, "title"),
                        "desc": _stmt_value_text(st.value, "desc"),
                        # 块形式（条件分支）的完整键列表。上面两个标量字段只为
                        # preview 等「取一个来展示」的消费方保留，缺键校验必须
                        # 用这两个列表，否则 214 处块形式 desc 会被判缺键。
                        "title_keys": _stmt_keys(st.value, "title"),
                        "desc_keys": _stmt_keys(st.value, "desc"),
                        "extra": _stmt_value_text(st.value, "picture"),
                        "pictures": _stmt_sprites(st.value, "picture"),
                        # 隐藏事件玩家看不到标题/正文/选项，原版对这类事件
                        # 普遍不写本地化、选项直接留空块。校验要据此跳过。
                        "hidden": _stmt_value_text(st.value, "hidden").lower() in ("yes", "true"),
                        "options": [
                            _stmt_value_text(o.value, "name")
                            for o in cw.get_all_ci(st.value, "option")
                            if isinstance(o.value, cw.Block)
                        ],
                        "_block": st.value,
                    }
                )

        # --- focus trees --------------------------------------------------- #
        if "/national_focus/" in lower or lower.startswith("common/national_focus"):
            for tree in cw.get_all(root, "focus_tree"):
                if not isinstance(tree.value, cw.Block):
                    continue
                for st in cw.get_all(tree.value, "focus"):
                    if not isinstance(st.value, cw.Block):
                        continue
                    fid = _stmt_value_text(st.value, "id")
                    defs["focus"].append(
                        {
                            "id": fid,
                            "file": relpath,
                            "line": st.line,
                            # text = 是「显示键」，允许和 id 不同。原版用它避开重名，
                            # 例如 ethiopia.txt:6049 的
                            #   id = ETH_peoples_army
                            #   text = ETH_peoples_army_focus   # 免得和 Mass Assault 学说的 peoples_army 撞
                            # 只按 id 找本地化键，这个国策就会被误报「缺键」。
                            "text": _stmt_value_text(st.value, "text"),
                            "extra": _stmt_value_text(st.value, "icon"),
                            # icon 可以是条件块（原版 44 处），sprite 名写在块内。
                            # 只采标量会让这些国策的图标引用在 deep 校验里消失。
                            "pictures": _stmt_sprites(st.value, "icon"),
                            "x": _stmt_value_text(st.value, "x"),
                            "y": _stmt_value_text(st.value, "y"),
                            # 国策坐标不是绝对的。原版 10625 个国策里有 10984 处
                            # relative_position_id——几乎每个都靠它把 x/y 解释成
                            # 「相对某个锚点的偏移」。不采这一项，画出来的树整体错位。
                            "rel": _stmt_value_text(st.value, "relative_position_id"),
                            "prereq": _focus_prereq(st.value),
                            "tree": _stmt_value_text(tree.value, "id"),
                        }
                    )
                for st in cw.get_all(tree.value, "shared_focus"):
                    if isinstance(st.value, cw.Block):
                        defs["focus"].append(
                            {
                                "id": _stmt_value_text(st.value, "id"),
                                "file": relpath,
                                "line": st.line,
                                "shared": True,
                                "extra": _stmt_value_text(st.value, "icon"),
                                "pictures": _stmt_sprites(st.value, "icon"),
                            }
                        )

        # --- ideas --------------------------------------------------------- #
        if "/ideas/" in lower:
            for ideas in cw.get_all(root, "ideas"):
                if not isinstance(ideas.value, cw.Block):
                    continue
                for cat in cw.stmts(ideas.value):
                    if not isinstance(cat.value, cw.Block):
                        continue
                    for idea in cw.stmts(cat.value):
                        if isinstance(idea.value, cw.Block) and not idea.key.startswith("@"):
                            defs["idea"].append(
                                {
                                    "id": idea.key,
                                    "file": relpath,
                                    "line": idea.line,
                                    "slot": cat.key,
                                    # name = 重定向显示键。原版 6563 个 idea 块里 1392 个用了
                                    # name（21.2%），典型是「同一段文字被多个 idea 复用」：
                                    #   GER_redirecting_naval_production_2 = {
                                    #       name = GER_redirecting_naval_production
                                    # 只按 id 找键会把这 1392 个全报成缺本地化。
                                    "name": _stmt_value_text(idea.value, "name"),
                                    "extra": _stmt_value_text(idea.value, "picture"),
                                    "pictures": _stmt_sprites(idea.value, "picture"),
                                }
                            )

        # --- technologies -------------------------------------------------- #
        if "/technolog" in lower:
            tech_markers = {"start_year", "research_cost", "path", "enable_equipments", "categories"}
            for techs in cw.get_all(root, "technologies"):
                if not isinstance(techs.value, cw.Block):
                    continue
                for entry in cw.stmts(techs.value):
                    if not isinstance(entry.value, cw.Block) or entry.key.startswith("@"):
                        continue
                    has_marker = any(s.key in tech_markers for s in cw.stmts(entry.value))
                    if has_marker:
                        defs["tech"].append({"id": entry.key, "file": relpath, "line": entry.line})
                        continue
                    # 一层目录分组（folder -> tech）的写法
                    for child in cw.stmts(entry.value):
                        if isinstance(child.value, cw.Block):
                            defs["tech"].append(
                                {"id": child.key, "file": relpath, "line": child.line, "folder": entry.key}
                            )

        # --- decisions ----------------------------------------------------- #
        # 结构铁律：common/decisions/*.txt 是「分类 = { 决议... }」；
        # common/decisions/categories/*.txt 只定义分类，里面没有决议。
        # 按这个结构判断比猜字段可靠得多。
        if "/decisions/" in lower:
            cats_only = "/decisions/categories/" in lower
            for cat in cw.stmts(root):
                if not isinstance(cat.value, cw.Block):
                    continue
                defs["decision_category"].append({"id": cat.key, "file": relpath, "line": cat.line})
                if cats_only:
                    continue
                for dec in cw.stmts(cat.value):
                    if not isinstance(dec.value, cw.Block):
                        continue
                    if not _looks_like_decision(dec.value):
                        continue
                    defs["decision"].append(
                        {
                            "id": dec.key,
                            "file": relpath,
                            "line": dec.line,
                            "category": cat.key,
                            "extra": _stmt_value_text(dec.value, "icon"),
                            # 决议的 icon 条件块用 key = GFX_... 写（原版 66 处）。
                            "pictures": _stmt_sprites(dec.value, "icon"),
                        }
                    )

        # --- scripted effects / triggers / guys ---------------------------- #
        for folder, kind in (
            ("/scripted_effects/", "scripted_effect"),
            ("/scripted_triggers/", "scripted_trigger"),
            ("/scripted_guys/", "scripted_guy"),
        ):
            if folder in lower:
                for st in cw.stmts(root):
                    if isinstance(st.value, cw.Block):
                        defs[kind].append({"id": st.key, "file": relpath, "line": st.line})

        # --- characters ---------------------------------------------------- #
        if "/characters/" in lower:
            for chars in cw.get_all(root, "characters"):
                if not isinstance(chars.value, cw.Block):
                    continue
                for child in cw.stmts(chars.value):
                    if not isinstance(child.value, cw.Block):
                        continue
                    ok, nm = _character_probe(child.value)
                    if ok:
                        defs["character"].append(
                            {"id": child.key, "file": relpath, "line": child.line, "name": nm}
                        )
                        continue
                    for ch in cw.stmts(child.value):
                        ok2, nm2 = _character_probe(ch.value)
                        if ok2:
                            defs["character"].append(
                                {"id": ch.key, "file": relpath, "line": ch.line, "name": nm2}
                            )

    for bucket in defs.values():
        for item in bucket:
            item.pop("_block", None)
    return {"definitions": dict(defs), "parse_errors": parse_errors, "namespaces": namespaces}


# 这些类型在 HOI4 里是「跨文件续写」的合法写法，同名不是重复：
#   decision_category —— 分类块本来就被拆到几十个国家文件里各自续写，引擎会合并。
#   scripted_effect / scripted_trigger —— 子模组覆盖父模组是常规操作。
# 把它们排除掉，否则一个正常的大型 mod 会刷出上千条假重复。
MERGEABLE_DUP_KINDS = frozenset({"decision_category", "scripted_effect", "scripted_trigger"})

# 本地化覆盖率低于这个值、且需要的键数够多，才当作「翻译子模组」降噪。
# 小模组缺键就是真缺，不能拿覆盖率当免罪符。
LOC_SUBMOD_COVERAGE = 0.7
LOC_SUBMOD_MIN_KEYS = 200


def find_duplicates(mod_path: str, defs: dict) -> list[dict]:
    issues: list[dict] = []
    for kind, items in defs.items():
        if kind in MERGEABLE_DUP_KINDS:
            continue
        seen: dict[str, dict] = {}
        for item in items:
            ident = item.get("id") or ""
            if not ident:
                continue
            if ident in seen:
                first = seen[ident]
                issues.append(
                    {
                        "level": "error",
                        "kind": kind,
                        "id": ident,
                        "file": item["file"],
                        "line": item["line"],
                        "message": f"{kind} id '{ident}' 重复定义",
                        "hint": f"首次定义在 {first['file']}:{first['line']}。游戏只会采用其中一个，另一个静默失效。",
                    }
                )
            else:
                seen[ident] = item
    return issues


def check_missing_loc(
    mod_path: str,
    defs: dict,
    loc_keys: dict,
    namespaces: list[dict],
    external_loc: set | None = None,
    has_dependencies: bool = False,
) -> list[dict]:
    """missing localisation keys.

    子模组会被孤立校验：它声明了 dependencies，缺的键由被依赖的 mod 提供。
    这种情况下把 error 降级为 info，否则一个正常的汉化子模组会报出几万条「缺键」。
    """
    issues: list[dict] = []
    nsset = {n["namespace"] for n in namespaces}
    # 事件 id 与 add_namespace 的大小写经常不一致（原版真实存在），
    # 引擎按不敏感匹配，校验也折成小写比较。见下面 event 循环的注释。
    nsset_lower = {s.lower() for s in nsset}
    external_loc = external_loc or set()
    tally = {"need": 0, "have": 0}
    local_have = 0

    def need(key: str, item: dict, kind: str, why: str) -> None:
        nonlocal local_have
        if not key:
            return
        # DEBUG_ 前缀是原版自己的调试开关（DEBUG_MUN_show_skoda 之类），
        # 里面 allowed = { always = no }，玩家永远看不到，原版也就不写本地化。
        # 把它们报成缺键等于给每个模组刷几百条假错。
        if key.startswith("DEBUG_"):
            return
        tally["need"] += 1
        if key in loc_keys:
            tally["have"] += 1
            local_have += 1
            return
        if key in external_loc:
            tally["have"] += 1
            return
        issues.append(
            {
                "level": "info" if has_dependencies else "error",
                "kind": kind,
                "missing_key": key,
                "file": item.get("file"),
                "line": item.get("line"),
                "message": f"缺少本地化键 {key}",
                "hint": why,
            }
        )

    def need_any(keys: list[str], item: dict, kind: str, why: str) -> None:
        """多个候选键命中任意一个就算过。

        事件正文键尤其需要：`.desc` 是绝大多数（原版实测 5209 个），
        `.d` 是老写法（1538 个），两种原版都在用。只试一种必然大量误报。
        """
        nonlocal local_have
        keys = [k for k in keys if k]
        if not keys:
            return
        tally["need"] += 1
        for k in keys:
            if k in loc_keys:
                tally["have"] += 1
                local_have += 1
                return
            if k in external_loc:
                tally["have"] += 1
                return
        issues.append(
            {
                "level": "info" if has_dependencies else "error",
                "kind": kind,
                "missing_key": keys[0],
                "file": item.get("file"),
                "line": item.get("line"),
                "message": "缺少本地化键 " + " 或 ".join(keys),
                "hint": why,
            }
        )

    for item in defs.get("focus", []):
        fid = item.get("id")
        if not fid:
            continue
        # text = 优先：它才是引擎真正去查的键，id 只是脚本内部的引用名。
        tkey = item.get("text") or fid
        need(tkey, item, "focus", "国策按钮标题；写在 localisation/<lang>/ 下的 .yml 里。")
        need(f"{tkey}_desc", item, "focus", "国策详情文本，缺了会显示为空面板。")

    for item in defs.get("idea", []):
        iid = item.get("id")
        if not iid or item.get("shared"):
            continue
        nkey = item.get("name") or iid
        need(nkey, item, "idea", "国家精神标题。")
        # idea 的 *_desc 不是必检项：原版 6515 个 idea 里只有 1766 个（27%）
        # 写了 *_desc，其余悬停面板只显示 modifier 列表。旧版把它当必需品，
        # 一个正常模组会被刷出几千条「缺 _desc」。
        # 这里不生成问题条目；想查漏译请用 check_missing_loc 的覆盖率摘要。

    for item in defs.get("decision_category", []):
        cid = item.get("id")
        if not cid:
            continue
        need(cid, item, "decision_category", "决议分类标题（决议面板左侧页签）。")
        # 分类的 *_desc 是可选的：原版 1306 个分类里 792 个（61%）才有。
        # Live 里缺 desc 只是页签没有说明文字，不影响任何功能。

    for item in defs.get("decision", []):
        did = item.get("id")
        if not did:
            continue
        need(did, item, "decision", "决议标题。")
        # 决议的 *_desc 同样是可选的：原版 4186 个决议里只有 1387 个（33%）
        # 写了 *_desc，其余只显示标题和效果。旧版当必需品，误报 2800+ 条。

    for item in defs.get("event", []):
        eid = item.get("id", "")
        if "." in eid:
            ns = eid.rsplit(".", 1)[0]
            # 命名空间匹配**大小写不敏感**。原版 events/BBA_Switzerland.txt
            # 顶部写 add_namespace = BBA_Switzerland（大写 S），文件里 55 个事件
            # 全写成 id = BBA_switzerland.N（小写 s），游戏照常注册。
            # 同文件里 BBA_switzerland_trade / BBA_switzerland_fascist 也全是小写。
            # 精确匹配会在这一个文件上刷 34 条假 error，故统一折成小写比较。
            if ns and ns.lower() not in nsset_lower:
                issues.append(
                    {
                        "level": "error",
                        "kind": "event",
                        "id": eid,
                        "file": item.get("file"),
                        "line": item.get("line"),
                        "message": f"事件命名空间 '{ns}' 未在本文件声明",
                        "hint": "在事件文件顶部加 add_namespace = " + ns + "，否则事件不会被注册。",
                    }
                )
        # 标题 / 正文都可能写成条件块（可重复多次，每块一个 text = 键）。
        # 候选拼法是「声明的键」在前、「引擎默认键」在后：
        # 写了 text = 就以它为准，没写才回退到 <id>.t / <id>.desc / <id>.d。
        title_candidates = list(item.get("title_keys") or [])
        if not title_candidates and item.get("title"):
            title_candidates = [item["title"]]
        title_candidates = title_candidates or [f"{eid}.t"]

        # 正文键两种写法原版都在用：.desc 5209 个、.d 1538 个。
        # 只认 .d 会把一半以上的原版事件判成缺键。
        desc_candidates = list(item.get("desc_keys") or [])
        if not desc_candidates and item.get("desc"):
            desc_candidates = [item["desc"]]
        if not desc_candidates:
            desc_candidates = [f"{eid}.desc", f"{eid}.d"]

        need_any(title_candidates, item, "event", "事件标题键。")
        need_any(desc_candidates, item, "event", "事件正文键。")
        opts = [o for o in item.get("options", []) if o]
        # 隐藏事件（hidden = yes）的选项玩家永远看不到，原版大量直接写
        # 空块 `option = {}` 或干脆不写 option，只为让事件能触发。
        # 实测原版 6950 个事件里：116 个零 option、9 个有 option 无 name，
        # 这 125 个**全部**是 hidden 事件。对它们报「选项缺名称」是纯噪音，
        # 所以 hidden 事件整段跳过选项名检查。
        if not item.get("hidden"):
            if not opts:
                # 选项没写 name 时引擎回退到 <id>.a / <id>.b ……，任何一个字母存在即合法。
                # 旧写法把 issue 追加在 for 循环里，第一个字母（a）找不到就报 warn，
                # 完全不管后面 b/c/d 有没有——原版有大量只写 .b 或 .c 的事件。
                if not any(f"{eid}.{letter}" in loc_keys for letter in "abcdefgh"):
                    issues.append(
                        {
                            "level": "warn",
                            "kind": "event",
                            "id": eid,
                            "file": item.get("file"),
                            "line": item.get("line"),
                            "message": f"事件 {eid} 的选项没有 name，且找不到任何默认键 {eid}.a … {eid}.h",
                            "hint": "选项会自动回退到 <id>.a/<id>.b，但显式写 name 更可控。",
                        }
                    )
            else:
                for okey in opts:
                    need(okey, item, "event", "事件选项文本键。")

    for item in defs.get("character", []):
        name = item.get("name", "")
        if name and name in loc_keys:
            continue
        # 豁免两类「不是 loc 键」的名字：
        #  1. 含空格/标点的字面量（"Alan Brooke (Official)"）
        #  2. 非 ASCII 名（"蒋介石"）——str.isalnum() 对任何 Unicode 字母
        #     都返回 True，不补 isascii 的话中文 mod 直接写字面量名的
        #     每个角色都会被误报「缺少本地化键」。
        if name and (not name.replace("_", "").isalnum() or not name.isascii()):
            continue
        if name:
            need(name, item, "character", "角色显示名；写成 loc 键而非直接写字符串。")

    # 覆盖率：一个只翻译了 43% 的子模组，缺 5 万个键是事实，
    # 但它能正常游玩——缺的键由基础 mod 提供。逐条报 error 等于噪音，
    # 所以改成一条覆盖率摘要 + 个体降级为 info。
    #
    # 但小模组不能这么判：只有 8 个键、缺 6 个，那是真的没写，不是「子模组」。
    # 所以覆盖不足七成只在键数够多（LOC_SUBMOD_MIN_KEYS）时才当作子模组信号。
    need_total = tally["need"]
    # 覆盖率只算「本地写出了多少」，不把外部键算进来。
    # 原因：索引原版之后 external_loc 有十几万条，会把覆盖率抬到七成以上，
    # 于是「翻译子模组」的降级判定失效，某个汉化子模组的 error 从两位数暴涨到 1.9 万条。
    # 外部键的正确用途是「这条要不要逐条报」，不是「这个模组完成度多高」。
    coverage = local_have / need_total if need_total else 1.0
    partial = coverage < LOC_SUBMOD_COVERAGE and need_total >= LOC_SUBMOD_MIN_KEYS
    if partial:
        for item in issues:
            item["level"] = "info"
            item["hint"] = "本地化覆盖率偏低，若这是翻译子模组属正常；否则说明大量文本没写。"

    summary = {
        "level": "info" if (partial or has_dependencies) else "ok",
        "kind": "localisation_summary",
        "message": (
            f"本地化覆盖率 {round(coverage * 100)}%"
            f"（需要 {need_total} 个键，缺 {len(issues)} 个）"
            + ("；覆盖不足七成，可能是依赖其他 mod 的翻译子模组" if partial else "")
            + ("；该 mod 声明了 dependencies" if has_dependencies else "")
        ),
        "hint": "索引原版或被依赖的 mod 后重建知识库，能自动排除由外部提供的键。",
        "coverage": round(coverage * 100, 1),
        "needed": need_total,
        "missing": len(issues),
        "partial": partial,
    }
    return [summary] + issues


# --------------------------------------------------------------------------- #
# Error log
# --------------------------------------------------------------------------- #

LOG_LINE_RE = re.compile(r"^\[(?P<time>[^\]]*)\]\[(?P<src>[^\]]*)\]:?\s*(?P<msg>.*)$")
NOISE_RE = re.compile(r"\d+")


def analyze_error_log(path: str, top_n: int = 15) -> dict:
    if not os.path.isfile(path):
        return {
            "found": False,
            "path": path,
            "message": "找不到 error.log",
            "hint": "路径通常是 文档/Paradox Interactive/Hearts of Iron IV/logs/error.log。用 -debug 启动游戏才有完整信息。",
        }

    raw = open(path, "rb").read()
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    groups: dict[str, dict] = {}
    total = 0
    for idx, line in enumerate(lines, 1):
        if not line.strip():
            continue
        total += 1
        m = LOG_LINE_RE.match(line)
        src = m.group("src") if m else ""
        msg = (m.group("msg") if m else line).strip()
        template = NOISE_RE.sub("#", msg)[:160]
        key = f"{src}|{template}"
        g = groups.setdefault(
            key, {"source": src, "template": template, "count": 0, "samples": [], "first_line": idx}
        )
        g["count"] += 1
        if len(g["samples"]) < 2:
            g["samples"].append(msg[:200])

    ranked = sorted(groups.values(), key=lambda g: -g["count"])[:top_n]
    for g in ranked:
        g["category"], g["hint"] = _classify_log(g["template"])

    categories = Counter(g["category"] for g in ranked)
    return {
        "found": True,
        "path": path,
        "total_lines": total,
        "group_count": len(groups),
        "categories": dict(categories),
        "groups": ranked,
    }


def _classify_log(template: str) -> tuple[str, str]:
    low = template.lower()
    if "unexpected token" in low or "parse error" in low or "malformed" in low:
        return "语法错误", "大多是大括号/等号不配对或漏了引号。用 kiant_hoi4_validate_mod 定位具体文件。"
    if "already defined" in low or "duplicate" in low or "multiple definitions" in low:
        return "重复定义", "同一 id 在两个文件里都定义了。后加载的覆盖前者，容易埋隐性 bug。"
    if "could not find" in low or "not found" in low or "no such" in low or "missing" in low:
        return "引用缺失", "检查 GFX sprite、loc 键、脚本化 effect/trigger 名字是否拼错。"
    if "invalid" in low or "unknown" in low or "not valid" in low:
        return "无效参数", "多半是枚举值写错（如 ideology / slot 名），对照原版同名文件确认。"
    if "is not within" in low or "province" in low or "state" in low:
        return "地图/州数据", "province id 与 state 归属不匹配，常见于改地图或建筑位置。"
    return "其他", "在游戏内用 -debug 打开控制台，配合 error.log 的源文件名定位。"


# --------------------------------------------------------------------------- #
# Vanilla comparison
# --------------------------------------------------------------------------- #

def list_overrides(mod_path: str, vanilla_path: str) -> dict:
    if not os.path.isdir(vanilla_path):
        return {
            "ok": False,
            "message": f"原版目录不存在：{vanilla_path}",
            "hint": "传游戏安装根目录（含 common/ events/ 那一层），不是 mod 目录。",
        }

    overrides: list[str] = []
    added: list[str] = []
    for path in iter_mod_files(mod_path):
        relpath = rel(mod_path, path)
        target = os.path.join(vanilla_path, relpath.replace("/", os.sep))
        if os.path.isfile(target):
            overrides.append(relpath)
        else:
            added.append(relpath)

    replace_paths: list[str] = []
    outer = os.path.join(os.path.dirname(mod_path), os.path.basename(mod_path) + ".mod")
    for cand in (os.path.join(mod_path, "descriptor.mod"), outer):
        if os.path.isfile(cand):
            root, _ = cw.parse_file(cand)
            for st in cw.get_all(root, "replace_path"):
                replace_paths.append(cw.as_text(st.value))

    return {
        "ok": True,
        "mod_folder": os.path.basename(mod_path),
        "override_count": len(overrides),
        "new_file_count": len(added),
        "overrides": overrides[:200],
        "new_files": added[:200],
        "replace_path": replace_paths,
        "risk": (
            "使用了 replace_path：整个原版目录被替换，子模组（submod）将无法再向该目录追加内容，"
            "与其他大改 mod 的兼容性会直接归零。"
            if replace_paths
            else "未使用 replace_path，只覆盖同名文件，兼容性风险较低。"
        ),
        "load_order_hint": "同名文件冲突时后加载的覆盖先加载的；mod 之间按启动器里的排序决定先后。",
    }


# --------------------------------------------------------------------------- #
# Top-level validation
# --------------------------------------------------------------------------- #

def validate_mod(
    mod_path: str,
    max_parse_errors: int = 40,
    deep: bool = False,
    kb_names: dict | None = None,
    vanilla_root: str = "",
    only_validators: list[str] | None = None,
    external_loc: set | None = None,
    per_check: int = 25,
    max_issues: int = 200,
) -> dict:
    mod_root, descriptor_path, notes = resolve_mod_root(mod_path)
    issues: list[dict] = []

    desc = check_descriptor(mod_root, descriptor_path, notes)
    for i in desc["issues"]:
        i.setdefault("validator", "descriptor")
    issues.extend(desc["issues"])

    loc = scan_localisation(mod_root)
    for i in loc["issues"]:
        i.setdefault("validator", "localisation")
    issues.extend(loc["issues"])

    defs_bundle = collect_definitions(mod_root)
    defs = defs_bundle["definitions"]
    for i in defs_bundle["parse_errors"][:max_parse_errors]:
        i.setdefault("validator", "syntax")
    issues.extend(defs_bundle["parse_errors"][:max_parse_errors])

    for i in find_duplicates(mod_root, defs):
        i.setdefault("validator", "duplicates")
        issues.append(i)

    deps = desc.get("dependencies") or []
    replace_paths = desc.get("replace_paths") or []
    # 「原版里没有」能不能当「不存在」的证据。两种情况下不能：
    #   replace_path → 原版那一整个目录按设计不加载，素材自然不在
    #   dependencies → 内容由父模组提供，本机没装父模组就查不到
    assume_complete = not replace_paths and not deps
    loc_report = check_missing_loc(
        mod_root,
        defs,
        loc["keys"],
        defs_bundle["namespaces"],
        external_loc=external_loc,
        has_dependencies=bool(deps),
    )
    loc_coverage = 100.0
    loc_partial = False
    if loc_report and loc_report[0].get("kind") == "localisation_summary":
        loc_coverage = float(loc_report[0].get("coverage", 100.0))
        loc_partial = bool(loc_report[0].get("partial"))
    for i in loc_report:
        i.setdefault("validator", "localisation")
        issues.append(i)

    validator_report: list[dict] = []
    if deep:
        import validators as vmod

        ctx = vmod.Ctx(
            mod_root,
            defs,
            loc["keys"],
            kb_names=kb_names,
            vanilla_root=vanilla_root,
            external_loc=external_loc,
            has_dependencies=bool(deps),
            loc_coverage=loc_coverage,
            loc_partial=loc_partial,
            assume_complete=assume_complete,
        )
        outcome = vmod.run(ctx, only=only_validators)
        validator_report = outcome["validators"]
        issues.extend(outcome["issues"])

    counts = Counter(i.get("level", "info") for i in issues)
    severity_rank = {"error": 0, "warn": 1, "info": 2}
    issues.sort(key=lambda i: severity_rank.get(i.get("level"), 3))

    by_validator = Counter(i.get("validator", "other") for i in issues)

    # 分项统计必须在截断**之前**算。
    # 下面的 picked 会按 per_check 每类只留前 N 条，拿它做统计会得出
    # 「localisation 只有 400 条」这种假数字（原版实测真实值是 2041）。
    # 判读「哪一类偏多」必须基于全量，展示才用 picked。
    breakdown = {
        "localisation_missing_key": sum(
            1 for i in issues
            if i.get("validator") == "localisation" and i.get("missing_key")
        ),
        "localisation_other": sum(
            1 for i in issues
            if i.get("validator") == "localisation" and not i.get("missing_key")
        ),
        "syntax": by_validator.get("syntax", 0),
        "syntax_unclosed_at_eof": sum(
            1 for i in issues
            if i.get("validator") == "syntax" and "unclosed block" in (i.get("message") or "")
        ),
    }
    breakdown["other"] = max(
        0,
        len(issues)
        - breakdown["localisation_missing_key"]
        - breakdown["localisation_other"]
        - breakdown["syntax"],
    )

    # 大模组动辄几万条，平铺截断会只剩某一类问题（永远看不到别的检查项）。
    # 改成「每类各取前 per_check 条」——各检查项都能露面，总数仍然可控。
    per_check = max(1, int(per_check))
    picked: list[dict] = []
    taken: Counter = Counter()
    for i in issues:
        v = i.get("validator", "other")
        if taken[v] >= per_check:
            continue
        taken[v] += 1
        picked.append(i)
    picked.sort(key=lambda i: severity_rank.get(i.get("level"), 3))
    picked = picked[:max(1, int(max_issues))]
    shown_by_check = Counter(i.get("validator", "other") for i in picked)

    # 索引状态的显式声明。没有它，新用户看到 "0 error" 会以为全都查过了，
    # 实际上 assets / sprites / technology 三类因为缺参照物整段降级成 info。
    index_state: dict = {
        "vanilla_indexed": bool(vanilla_root),
        "kb_loaded": bool(kb_names or external_loc),
        "degraded": [] if vanilla_root else ["assets", "sprites", "technology", "history"],
    }
    if not vanilla_root:
        index_state["hint"] = (
            "尚未建索引：assets / sprites / technology / history 四类检查只做到「文件存在」，"
            "判断不了引用是否真有问题。跑一次 kiant_hoi4_kb_build action=build 即可（原版约 30 秒），"
            "之后是增量。"
        )
    elif not kb_names:
        index_state["hint"] = "原版路径已找到但索引未加载，检索类功能不可用；跑一次 kiant_hoi4_kb_build action=build。"

    return {
        "mod_root": mod_root,
        "deep": deep,
        "summary": {
            "errors": counts.get("error", 0),
            "warnings": counts.get("warn", 0),
            "infos": counts.get("info", 0),
            "localisation_files": loc["files"],
            "localisation_keys": len(loc["keys"]),
            "definitions": {k: len(v) for k, v in sorted(defs.items())},
            "by_check": dict(by_validator.most_common()),
            # 全量分项（不受 per_check 截断影响）。判读用这个，不要用 issues 长度。
            "breakdown": breakdown,
            "total_issues": len(issues),
            "index": index_state,
            "verdict": "可以进游戏了" if counts.get("error", 0) == 0 else "还有硬错误，进游戏会静默失效",
        },
        "descriptor": {k: v for k, v in desc.items() if k != "issues"},
        "validators": validator_report,
        "knowledge_base": "已接入" if kb_names else "未接入（deep 模式下依赖原版/参考模组的检查会跳过）",
        "issues": picked,
        "truncated": max(0, len(issues) - len(picked)),
        "shown_by_check": {
            v: f"{shown_by_check.get(v, 0)}/{n}" for v, n in by_validator.most_common()
        },
    }

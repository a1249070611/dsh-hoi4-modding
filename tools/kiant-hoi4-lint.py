#!/usr/bin/env python3
"""Clausewitz 语法体检：括号 / 运算符 / 悬空引用。

为什么需要这个工具：
  引擎对语法错误极其宽容——`x >= 5` 不会报错，而是**静默忽略整条触发器**；
  引用了不存在的 focus id 也不报错，只是那个国策永远灰着。
  这两类错误都不进 error.log，靠进游戏试是查不出来的，只能静态扫。

用法：
    python tools/kiant-hoi4-lint.py <file-or-dir> [...]              # 检查指定文件/目录
    python tools/kiant-hoi4-lint.py <dir> --refs                     # 加查悬空国策引用
    python tools/kiant-hoi4-lint.py <mod> --refs --refs-scope <原版>  # 定义来源含原版，只查 mod 的引用
    python tools/kiant-hoi4-lint.py <dir> --strict                   # 警告也算失败

退出码：0 干净 / 1 有 error / 2 有 warning（仅 --strict）
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-server"))

import cw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MOD_ROOT = os.path.dirname(HERE)

# 引擎**不支持**的比较运算符。原版全量实测：> 13597 次、< 6877 次，
# <= >= == != 各 0 次。写了不报错但不生效，这是最隐蔽的一类错误。
BAD_OPS = re.compile(r'(?<![<>=!])(<=|>=|==|!=)(?![<>=])')

# 引擎能加载的文本类型。yml/gfx 有各自语法，这里只管 Clausewitz 那套。
CW_EXT = (".txt", ".gui", ".gfx", ".asset", ".anim", ".mod")

# ------------------------------------------------------------------------- #
# 悬空引用检查的模型
# ------------------------------------------------------------------------- #
#
# 只查两类**最强、最不会误报**的引用：国策前置 和 国策互斥。
# 为什么只查这两类：
#   - 语义明确：`prerequisite = { focus = X }` 里的 X 必须是一个国策 id。
#   - 引擎对这类错误完全静默：id 打错游戏不报错，只是那个国策永远灰着。
#   - 反之像 `add_idea = X`、`country_event = { id = X }` 这类，X 可能来自
#     原版 / DLC / 别的 mod，单扫一个目录会产生大量假阳性。宁可不查。
#
# 第一版这里留了个半成品：DEF_KEYS / REF_KEYS 两个常量 + 一个 collect 函数，
# 但从没接进 main，等于死了。教训：没接进调用链的功能，别先写进 docstring。

FOCUS_KEY = "focus"


def _short(p: str) -> str:
    """尽量显示成相对 mod 根目录的路径。

    不能直接 relpath：用户很可能去检查原版目录（E: 盘），而本仓库在 C: 盘，
    跨盘符时 ntpath.relpath 会抛 ValueError 直接崩掉整个进程。
    这不是理论风险——第一次在 E:\\Steam 上跑就崩了。
    """
    try:
        return os.path.relpath(p, MOD_ROOT)
    except ValueError:
        return p


def iter_files(targets: list[str]) -> list[str]:
    out: list[str] = []
    for t in targets:
        if os.path.isfile(t):
            out.append(t)
        else:
            for dp, dn, fn in os.walk(t):
                dn[:] = [d for d in dn if not d.startswith(".")]
                for f in fn:
                    if f.lower().endswith(CW_EXT):
                        out.append(os.path.join(dp, f))
    return out


def strip_comment(line: str) -> str:
    """剥掉行尾注释，但引号内的 # 不算注释起点。

    `NOT = { has_dlc = "No Compromise, No Surrender" }` 说明引号里可能有 #，
    直接 split("#") 会把右括号连同字符串一起切掉，凭空造出括号失衡。
    """
    inq = False
    for i, c in enumerate(line):
        if c == '"':
            inq = not inq
        elif c == "#" and not inq:
            return line[:i]
    return line


def check_file(path: str) -> tuple[list[dict], list[dict]]:
    """返回 (errors, warnings)。"""
    errors: list[dict] = []
    warns: list[dict] = []

    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        return [{"line": 0, "msg": f"读不出：{e}"}], []

    # 1. 结构：交给 cw.py。它对「文件末尾少一个 }」会报 unclosed，
    #    但那**是原版常态**——2224 个文件里有十来个这样，游戏照样加载，
    #    引擎把 EOF 当隐式闭合。所以这类降级成 warning，不当 error。
    _root, diags = cw.parse_file(path)
    for d in diags:
        msg = d.get("message", "?")
        if "unclosed block: reached end of file" in msg:
            warns.append({
                "line": d.get("line", 0),
                "msg": "文件末尾缺 }",
                "impact": "引擎容忍（把 EOF 当隐式闭合），原版 2224 个文件里有 14 个这样；"
                          "但补上更规范，某些工具可能不容忍",
            })
        else:
            errors.append({"line": d.get("line", 0), "msg": msg})

    lines = text.splitlines()

    # 2. 不支持的运算符。必须剥注释，否则 `#x >= 5` 这种说明文字会误报。
    for no, line in enumerate(lines, 1):
        code = strip_comment(line)
        for m in BAD_OPS.finditer(code):
            op = m.group(1)
            hint = "取反用 NOT = { }" if op == "!=" else "只能写 > 或 <，或用 NOT 包一层"
            errors.append({
                "line": no,
                "msg": f"引擎不支持的运算符 '{op}'：{code.strip()[:60]}",
                "impact": "整条语句会被引擎静默忽略（不报错），条件永远不生效",
                "fix": hint,
            })

    # 3. 括号平衡。只报「多出来的 }」——那个引擎会报错；
    #    少 } 已被上面归为 warning，不重复报。
    depth = 0
    over_at = 0
    for no, line in enumerate(lines, 1):
        for ch in strip_comment(line):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0 and not over_at:
                    over_at = no
    if over_at:
        errors.append({
            "line": over_at,
            "msg": "多余的 }",
            "impact": "引擎在这一行截断解析，此后的内容全部不生效",
            "fix": "删掉这一行的 }，或检查前面是否少开了块",
        })

    # 4. 空值赋值：`key =` 后面什么都没有，且下一行也不是 {
    for no, line in enumerate(lines, 1):
        code = strip_comment(line).rstrip()
        if re.search(r"=\s*$", code):
            nxt = lines[no] if no < len(lines) else ""
            if not nxt.strip().startswith("{"):
                warns.append({"line": no, "msg": f"'=' 后无值且下一行不是块：{code.strip()[:60]}"})

    return errors, warns


# 声明国策的块名。少认一种就会把那一批全判成悬空——实测踩了两次：
#   只认 `focus`          → abadcom 里 20 个 joint_focus 被漏，原版刷出 966 条假阳性
#   加上 joint_focus      → baltic 里 shared_focus 被漏，仍有 509 条
# 正确做法是照抄 checks.py 里已经处理过的三种（它在采集时早就考虑到了）。
FOCUS_DECL_KEYS = ("focus", "joint_focus", "shared_focus")


def collect_focus_defs(files: list[str]) -> set[str]:
    """收集所有被声明的国策 id。

    三种声明位置都要认：
        focus_tree = { focus = { id = X ... } }     ← 原版主形态
        focus_tree = { joint_focus = { id = X } }   ← 联合国策，多国共用
        focus = { id = X ... }                      ← 顶层直接写（少见但合法）

    注意别把 `prerequisite = { focus = X }` 里那个 `focus` 当成定义——
    那里的 value 是 Scalar 不是 Block，下面用 isinstance 挡住了。
    """
    defs: set[str] = set()
    for p in files:
        if not p.lower().endswith(".txt"):
            continue
        try:
            root, _ = cw.parse_file(p)
        except Exception:
            continue
        for _trail, st in cw.walk(root):
            if st.key not in FOCUS_DECL_KEYS or not isinstance(st.value, cw.Block):
                continue
            idst = cw.get_one(st.value, "id")
            if idst is not None:
                v = cw.as_text(idst.value)
                if v:
                    defs.add(v)
    return defs


def collect_focus_refs(files: list[str]) -> list[tuple[str, int, str]]:
    """收集所有对国策 id 的引用：(文件, 行号, 被引用的 id)。"""
    refs: list[tuple[str, int, str]] = []
    for p in files:
        if not p.lower().endswith(".txt"):
            continue
        try:
            root, _ = cw.parse_file(p)
        except Exception:
            continue
        for _trail, st in cw.walk(root):
            # prerequisite = { focus = A  focus = B }   多个 = 全部满足
            # mutually_exclusive = { focus = X }       二选一
            if st.key not in ("prerequisite", "mutually_exclusive"):
                continue
            if not isinstance(st.value, cw.Block):
                continue
            for st2 in cw.stmts(st.value):
                if st2.key == FOCUS_KEY:
                    v = cw.as_text(st2.value)
                    if v:
                        refs.append((_short(p), st2.line, v))
    return refs


def check_dangling(files: list[str], defs_scope_files: list[str] | None = None) -> list[dict]:
    """找出「引用了但没人定义」的国策 id。

    defs_scope_files 把「定义来源」和「检查范围」分开：
    典型用法是 mod + 原版都参与定义，只检查 mod 里的引用。
    不分开的话，mod 引用原版国策会被全部误判成悬空——假阳性。
    """
    defs = collect_focus_defs(defs_scope_files or files)
    out: list[dict] = []
    for path, line, fid in collect_focus_refs(files):
        if fid not in defs:
            out.append({"file": path, "line": line, "msg": f"悬空引用：没有国策 id = {fid}"})
    return out


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    want_refs = "--refs" in argv
    refs_scope = ""
    if "--refs-scope" in argv:
        i = argv.index("--refs-scope")
        refs_scope = argv[i + 1] if i + 1 < len(argv) else ""
    # 去掉所有 -- 开头的开关和它们的值
    skip_next = False
    clean: list[str] = []
    for a in argv:
        if skip_next:
            skip_next = False
            continue
        if a == "--refs-scope":
            skip_next = True
            continue
        if a.startswith("--"):
            continue
        clean.append(a)
    argv = clean
    if not argv and not refs_scope:
        print(__doc__)
        return 1

    files = iter_files(argv) if argv else []
    if not files and not refs_scope:
        print("没找到可检查的文件（支持 " + " ".join(CW_EXT) + "）")
        return 1

    total_e = total_w = 0
    bad_files = 0
    for p in files:
        e, w = check_file(p)
        if e or w:
            bad_files += 1
            rel = _short(p)
            for d in e[:8]:
                print(f"✗ {rel}:{d['line']}  {d['msg']}")
                # 三段式：发现什么 → 会怎样 → 怎么改（抄 hagane-studio 的
                # ReferenceIntegrityFinding：Consequence + EditAt 两个字段）
                if d.get("impact"):
                    print(f"    后果：{d['impact']}")
                if d.get("fix"):
                    print(f"    改法：{d['fix']}")
            for d in w[:5]:
                print(f"⚠ {rel}:{d['line']}  {d['msg']}")
                if d.get("impact"):
                    print(f"    后果：{d['impact']}")
            if len(e) > 8:
                print(f"  …还有 {len(e)-8} 条")
        total_e += len(e)
        total_w += len(w)

    # 悬空引用：只在显式要求时跑。
    # 因为它需要「全量定义」才能判断，单查一个子目录必然大量假阳性。
    dangling: list[dict] = []
    if want_refs:
        defs_files = files + (iter_files([refs_scope]) if refs_scope else [])
        dangling = check_dangling(files, defs_files)
        for d in dangling[:15]:
            print(f"✗ {d['file']}:{d['line']}  {d['msg']}")
        if len(dangling) > 15:
            print(f"  …还有 {len(dangling)-15} 条悬空引用")
        total_e += len(dangling)

    print(f"\n检查 {len(files)} 个文件：{total_e} 个错误、{total_w} 个警告、{len(files)-bad_files} 个干净")
    if want_refs:
        print(f"悬空引用：{len(dangling)} 条"
              + (f"（定义来源额外含 {refs_scope}）" if refs_scope else "（未指定 --refs-scope，只跟本批文件比对）"))

    # 回执：把「检查了什么」和「没检查什么」分开说清。
    # 照抄 hagane-studio 的 mutation_receipt 思路——"跑过了"不等于"验过了"，
    # 而且必须明确告诉调用方（尤其是 AI）哪些话不能说。
    # 没有这一段，报告里一句"lint 通过"就会被读成"这个 mod 没问题"，
    # 而实际上它只覆盖了括号/运算符/可选引用，游戏内行为、本地化、贴图全没碰。
    print("\n--- 回执 ---")
    print(f"checked_scope:   {len(files)} 个文件的括号 / 运算符 / 空值赋值"
          + ("，以及国策引用完整性" if want_refs else "（未查引用）"))
    print("verification:    syntax_only")
    if not want_refs:
        print("not_checked:     引用完整性（要查请加 --refs 与 --refs-scope）")
    print("not_checked:     本地化键、贴图引用、游戏内行为、引擎实际加载结果")
    print("reporting_rule:  以上结果只说明静态规则内未发现问题，"
          "不代表 mod 能正常运行；不要仅凭此结论宣称「已完成」或「已修复」。")

    if total_e:
        return 1
    if total_w and strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

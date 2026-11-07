#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异测试：验证 selftest 里的断言真的会在代码被改坏时报红。

## 为什么需要它

自检全绿只证明「按现在的代码，这些断言都成立」。它证明不了
**断言本身有没有在测东西**——一个 `assert True` 也能全绿。

变异测试的做法：故意把被测代码改回错误行为，看对应断言会不会报红。
不报红 = 那条断言是恒真的，等于没写。

本项目真实踩过：§16 第一版 12 条断言全绿，变异测试发现 3 条是无效的：
  - 「块形式 desc 不再被当空串丢弃」——它断言 `desc == ""`，
    块被丢弃时这个条件**正好成立**，断言写反了
  - 「icon 块里的条件不会被当 sprite 名」——那条黑名单过滤一次都没命中过，
    删掉代码也不影响结果
  - 「title 块内的键被采集到」——预期标给了采集变异，但真正改坏的是校验回退

## 用法

    python tools/kiant-hoi4-mutate.py            # 跑全部变异
    python tools/kiant-hoi4-mutate.py -v         # 同时打印每个变异的失败详情

退出码 0 = 全部变异都被捕获；1 = 有变异没被捕获（说明有断言无效）。

## 加新变异的规矩

改了一处校验逻辑、加了一条断言，就在 MUTATIONS 里加一条：
把代码改回**错误写法**，指定应该炸掉的断言原文（子串匹配）。
「改回去之后没有任何断言报红」就是这一条断言的死刑判决。

注意：复制整个项目跑，只复制 mcp-server/ 会让一批用例因缺
examples/、references/ 而抛异常，把真实信号淹掉。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"__pycache__", ".git", ".workbuddy"}


def _ignore(_dir, names):
    return [n for n in names if n in SKIP or n.endswith(".zip")]


def run_selftest(proj_dir: str) -> str:
    p = subprocess.run(
        [sys.executable, os.path.join(proj_dir, "mcp-server", "selftest.py")],
        cwd=proj_dir, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return p.stdout + p.stderr


def failures(out: str) -> list[str]:
    return re.findall(r"^\s+- (.+)$", out, re.M)


# fmt: off
MUTATIONS: list[dict] = [
    {
        "name": "desc 块只取第一个（回到 get_one 行为）",
        "file": "mcp-server/checks.py",
        "old": 'out: list[str] = []\n    for st in cw.get_all_ci(block, key):\n'
               '        if isinstance(st.value, cw.Scalar):',
        "new": 'out: list[str] = []\n    for st in cw.get_all_ci(block, key)[:1]:\n'
               '        if isinstance(st.value, cw.Scalar) and key == "__never__":',
        "expect": ["事件 desc 块内的 text 键全部被采集到"],
    },
    {
        "name": "desc 块被当空串丢弃（回到 as_text 行为）",
        "file": "mcp-server/checks.py",
        "old": '        elif isinstance(st.value, cw.Block):\n'
               '            # 块形式：键写在 text = 里，trigger 是分支条件，不是键。\n'
               '            for sub in cw.get_all_ci(st.value, "text"):\n'
               '                v = cw.as_text(sub.value)\n'
               '                if v:\n'
               '                    out.append(v)',
        "new": '        elif isinstance(st.value, cw.Block):\n            pass  # 变异：块直接忽略',
        "expect": ["事件 desc 块内的 text 键全部被采集到",
                   "事件 desc 写成条件块时不误报缺键",
                   "事件 title 块内的 text 键被采集到"],
    },
    {
        "name": "icon 块不认 key = 写法（决议）",
        "file": "mcp-server/checks.py",
        "old": '        key_st = cw.get_one_ci(v, "key")\n'
               '        keyed = cw.as_text(key_st.value) if key_st else ""\n'
               '        if keyed:',
        "new": '        keyed = ""\n        if keyed:',
        "expect": ["decision 的 icon 条件块从 key = 取到 sprite"],
    },
    {
        "name": "icon 块完全不采集（只认标量）",
        "file": "mcp-server/checks.py",
        "old": '        if not isinstance(v, cw.Block):\n'
               '            continue\n'
               '        # 结构 2：显式 key =',
        "new": '        if not isinstance(v, cw.Block):\n'
               '            continue\n'
               '        break  # 变异：块不处理\n'
               '        # 结构 2：显式 key =',
        "expect": ["focus 的 icon 条件块里所有 sprite 都被采集到"],
    },
    {
        "name": "icon 块用 walk 深挖（嵌套条件混进 sprite 名）",
        "file": "mcp-server/checks.py",
        "old": '        for sub in cw.stmts(v):\n            out.append(sub.key)',
        "new": '        for _p, sub in cw.walk(v):\n            out.append(sub.key)',
        "expect": ["focus icon 块只取顶层键，不把嵌套条件表达式当 sprite"],
    },
    {
        "name": "decision icon 取到 key 后继续落进语句键分支",
        "file": "mcp-server/checks.py",
        "old": '        if keyed:\n            out.append(keyed)\n            continue',
        "new": '        if keyed:\n            out.append(keyed)',
        "expect": ["decision icon 块取到 key 后不再把 trigger 当 sprite"],
    },
    {
        "name": "need_any 改成要求全部命中",
        "file": "mcp-server/checks.py",
        "old": '        tally["need"] += 1\n'
               '        for k in keys:\n'
               '            if k in loc_keys:\n'
               '                tally["have"] += 1\n'
               '                local_have += 1\n'
               '                return',
        "new": '        tally["need"] += 1\n'
               '        for k in keys:\n'
               '            if k in loc_keys:\n'
               '                tally["have"] += 1\n'
               '                local_have += 1\n'
               '                continue',
        "expect": ["块里多候选中任一命中即通过"],
    },
    {
        "name": "标题退回只认 .t 默认键（忽略块内声明）",
        "file": "mcp-server/checks.py",
        "old": '        title_candidates = list(item.get("title_keys") or [])',
        "new": '        title_candidates = []',
        "expect": ["事件标题用块内声明的键校验，不误报"],
    },
    # --- 第三轮「原版当 mod 跑」抓出来的五条（1939 → 1838） --------------- #
    {
        "name": "命名空间恢复精确匹配（大小写敏感）",
        "file": "mcp-server/checks.py",
        "old": 'if ns and ns.lower() not in nsset_lower:',
        "new": 'if ns and ns not in nsset:',
        "expect": ["事件命名空间大小写不同不报错"],
    },
    {
        "name": "隐藏事件也检查选项名（去掉 hidden 豁免）",
        "file": "mcp-server/checks.py",
        "old": '        if not item.get("hidden"):',
        "new": '        if True:',
        "expect": ["隐藏事件的空 option 不报「选项缺名称」"],
    },
    {
        "name": "字段名恢复大小写敏感（Hidden 读不到）",
        "file": "mcp-server/checks.py",
        "old": '    st = cw.get_one_ci(block, key)',
        "new": '    st = cw.get_one(block, key)',
        "expect": ["字段名 Hidden（首字母大写）仍被识别为隐藏事件"],
    },
    {
        "name": "事件预约又被当成定义",
        "file": "mcp-server/checks.py",
        "old": '                if not _looks_like_event_definition(st.value):\n                    continue',
        "new": '                if False:\n                    continue',
        "expect": ["history 里的事件预约不被当成事件定义"],
    },
    {
        "name": "本地化分行退回 splitlines()（NEL 当换行）",
        "file": "mcp-server/checks.py",
        "old": '            lines = text.replace("\\r\\n", "\\n").replace("\\r", "\\n").split("\\n")',
        "new": '            lines = text.splitlines()',
        "expect": ["本地化文本里的 U+0085 不被当换行",
                   "U+0085 之后的内容仍属于同一条词条"],
    },
    # --- 跨文档数字漂移 --------------------------------------------------- #
    # 变异点要选对。第一版把 got 改成 real（让比较永远相等），第二版清空
    # 文件元组——两次都没报红，但原因不一样，值得记下来：
    #   1. got = real 会同时让 `if got != real` 永不成立，效果等价于
    #      「检测被拆掉」，那是**正确**的不报红。
    #   2. 清空文件元组也没报红，因为断言当时只写了 `not stale_suspects`，
    #      一份都不扫同样是空列表。**这是断言的漏洞，不是变异的无效**——
    #      说明原来那条断言在「不检查」时也是绿的。
    # 修好断言（同时要求扫满 7 份）之后，清空元组就能被抓到了。
    {
        "name": "跨文档数字漂移检查被跳过（不检查任何文档）",
        "file": "mcp-server/selftest.py",
        "old": '    for fn in _DOC_FILES:\n        p = os.path.join(ROOT, fn)',
        "new": '    for fn in ():\n        p = os.path.join(ROOT, fn)',
        "expect": ["各文档里没有旧版本的技能/工具/篇数/错题本数字"],
    },
    # ---- sources.json 路径解析 ----
    # 这一组防的是「把本机绝对路径写进配置就发出去」。三条变异分别把
    # 相对路径、~ 展开、绝对路径保留各改回错误写法，看断言能不能抓到。
    {
        "name": "相对路径不再以插件根目录为基准（退回按当前工作目录拼）",
        "file": "mcp-server/kb.py",
        "old": '    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n'
               '    return os.path.normpath(os.path.join(root, p))',
        "new": '    return os.path.normpath(p)',
        "expect": ["相对路径以插件根目录为基准"],
    },
    {
        "name": "~ 不再展开成家目录",
        "file": "mcp-server/kb.py",
        "old": '    if p.startswith("~"):\n        return os.path.normpath(os.path.expanduser(p))',
        "new": '    if p.startswith("~") and False:\n        return os.path.normpath(os.path.expanduser(p))',
        "expect": ["~ 展开成家目录"],
    },
    {
        "name": "绝对路径被当成相对路径处理（剥掉盘符再拼）",
        "file": "mcp-server/kb.py",
        "old": '    if os.path.isabs(p):\n        return os.path.normpath(p)',
        # 注意：不能只把条件改成 `and False`。Windows 上 os.path.join(root, "C:\\x")
        # 会直接返回 "C:\\x"（join 遇到绝对路径丢弃前缀），行为没变，断言自然不会炸。
        # 必须让变异真的改变输出，否则测的是「join 的特性」而不是「我们的规则」。
        "new": '    if os.path.isabs(p) and False:\n        return os.path.normpath(p)\n    p = os.path.basename(p)',
        "expect": ["绝对路径原样保留"],
    },
]
# fmt: on


def main(argv: list[str]) -> int:
    verbose = "-v" in argv or "--verbose" in argv

    base = run_selftest(ROOT)
    base_fail = failures(base)
    if "全部通过" not in base:
        print(f"[警告] 基线自检不是全绿，先修它：{base_fail}")
    else:
        print("基线自检：全绿\n")

    caught = 0
    for m in MUTATIONS:
        tmp = tempfile.mkdtemp()
        try:
            proj = os.path.join(tmp, "proj")
            shutil.copytree(ROOT, proj, ignore=_ignore)
            path = os.path.join(proj, m["file"])
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if m["old"] not in text:
                print(f"[跳过] {m['name']}\n        锚点没匹配上（代码改过了，请更新本文件）")
                continue
            with open(path, "w", encoding="utf-8") as f:
                f.write(text.replace(m["old"], m["new"], 1))

            failed = failures(run_selftest(proj))
            new_fail = [f for f in failed if f not in base_fail]
            hit = [e for e in m["expect"] if any(e in f for f in new_fail)]
            missed = [e for e in m["expect"] if e not in hit]
            noise = [f for f in new_fail if "抛异常" in f]

            if hit and not missed and not noise:
                print(f"[✓] {m['name']}")
                for h in hit:
                    print(f"      → 炸掉: {h}")
                caught += 1
            else:
                print(f"[✗] {m['name']}")
                if noise:
                    print(f"      环境噪音（复制不全？）: {noise[:3]}")
                if missed:
                    print(f"      断言无效，改坏了也不报: {missed}")
                if verbose:
                    print(f"      新增失败: {new_fail[:8]}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    total = len(MUTATIONS)
    print(f"\n{caught} / {total} 个变异被正确捕获")
    if caught < total:
        print("有断言是恒真的——它的存在只给人「测过了」的错觉，应删掉或重写。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
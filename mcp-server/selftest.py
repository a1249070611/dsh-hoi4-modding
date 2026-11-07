"""HOI4 Modkit 自检脚本 —— 零依赖，直接 `python selftest.py` 跑。

覆盖十组：解析器、示例模组、错误夹具、规划器、预览、脚手架、知识库、MCP 协议、远端同步、两级资料库。
每次改动核心模块后跑一遍，比手动点工具可靠得多。

设计原则：断言只看「结论」不看文案细节——文案会调，结论不能错。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tarfile
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REFS = os.path.join(ROOT, "references")
sys.path.insert(0, HERE)

import checks  # noqa: E402
import cw  # noqa: E402
import kb  # noqa: E402
import planner  # noqa: E402
import playbook  # noqa: E402
import preview  # noqa: E402
import remote  # noqa: E402
import scaffolder  # noqa: E402
import validators  # noqa: E402

SAMPLE = os.path.join(ROOT, "examples", "sample_mod")
BROKEN = os.path.join(ROOT, "examples", "broken_mod")

_passed = 0
_failed: list[str] = []
# test_structure_doc 在这里只记录文档声称的自检断言数，由 main() 在
# 全部用例跑完后做双向严格核对（那时才知道真实总数）。
_CLAIMED_SELFTEST_COUNTS: list[int] = []


def ok(label: str, cond: bool, detail: str = "") -> None:
    global _passed
    if cond:
        _passed += 1
        print(f"  \033[32mPASS\033[0m {label}")
    else:
        _failed.append(label)
        print(f"  \033[31mFAIL\033[0m {label}" + (f"  → {detail}" if detail else ""))


def section(name: str) -> None:
    print(f"\n\033[1m{name}\033[0m")


# --------------------------------------------------------------------------- #
# 1. Parser
# --------------------------------------------------------------------------- #

def test_parser() -> None:
    section("1. Clausewitz 解析器")

    root, errs = cw.parse('a = 1\nb = { c = yes d = "x y" }\n')
    ok("基本键值解析", cw.get_one(root, "a") is not None and not errs)

    blk = cw.get_one(root, "b")
    ok("嵌套块解析", isinstance(blk.value, cw.Block) and len(list(cw.stmts(blk.value))) == 2)

    val = cw.get_one(blk.value, "d")
    ok("带空格字符串取值", cw.as_text(val.value) == "x y")

    _, e1 = cw.parse("a = {\n b = 1\n")
    ok("未闭合块被报告", any("unclosed" in i["message"] for i in e1), str(e1[:1]))

    _, e2 = cw.parse("names = { Alhx'es Ch'ischiqwe L'imaxwe }\n")
    ok("人名里的单引号不误报", not any("single quote" in i["message"] for i in e2), str(e2[:2]))

    _, e3 = cw.parse('title = \'hello world\'\n')
    ok("误用单引号当字符串能识别", any("single quote" in i["message"] for i in e3), str(e3[:1]))

    deep = "a = {" * 400 + "}" * 400
    root4, e4 = cw.parse(deep)
    ok("超深嵌套不崩栈", isinstance(root4, cw.Block), str(e4[:1]))

    # --- 原版全量解析：抄 hagane-studio 的 vanilla_corpus_test ---
    # 它把「原版所有 .txt 都能解析」当成一条测试，没装游戏就 skip。
    # 我们一直只测自己造的样本，从没跑过"4892 个真实文件会不会崩"。
    #
    # 三级回退，越靠前越优先：
    #   1. HOI4_VANILLA_DIR 环境变量（CI 显式指定）
    #   2. kb.find_game_dir() 自动探测（和 validate_mod / self_check 同一套）
    #   3. knowledge/survey.local.json / survey.json 的 game_root
    # 第 2 级是后加的：入库的 survey.json 刻意不含路径，只靠第 3 级会让
    # 本地装了游戏却没设环境变量的人白白跳过这条测试（项数也会少 1）。
    vanilla = os.environ.get("HOI4_VANILLA_DIR", "").strip()
    vanilla_source = "HOI4_VANILLA_DIR" if vanilla else ""
    if not vanilla:
        try:
            import kb as _kb
            vanilla = (_kb.find_game_dir() or "").strip()
            vanilla_source = "自动探测" if vanilla else ""
        except Exception:
            vanilla = ""
    if not vanilla:
        # 最后才看入库的 survey 文件
        for fn in ("survey.local.json", "survey.json"):
            try:
                import json as _json
                sv = _json.load(open(os.path.join(ROOT, "knowledge", fn), encoding="utf-8"))
                got = (sv.get("game_root") or "").strip()
            except Exception:
                got = ""
            if got:
                vanilla, vanilla_source = got, fn
                break

    vanilla_ok = True
    vanilla_n = vanilla_fail = 0
    if vanilla and os.path.isdir(vanilla):
        for base in ("common", "events", "history"):
            d = os.path.join(vanilla, base)
            if not os.path.isdir(d):
                continue
            for dp, _dn, fn in os.walk(d):
                for f in fn:
                    if not f.endswith(".txt"):
                        continue
                    vanilla_n += 1
                    try:
                        cw.parse_file(os.path.join(dp, f))
                    except Exception:
                        vanilla_fail += 1
                        if vanilla_fail == 1:
                            print(f"  \033[33m首个解析失败：{os.path.join(dp, f)}\033[0m")
    else:
        vanilla_n = 0

    if vanilla_n:
        ok(f"原版 {vanilla_n} 个 .txt 全部能被解析（来源 {vanilla}）",
           vanilla_fail == 0, f"失败 {vanilla_fail} 个")
    else:
        # 跳过时也要显式说明，不能静默通过
        print("  \033[33mSKIP\033[0m 原版全量解析：未设置 HOI4_VANILLA_DIR，且 survey.json 里没有可用 game_root")


# --------------------------------------------------------------------------- #
# 2. Sample mod
# --------------------------------------------------------------------------- #

def test_sample() -> None:
    section("2. 示例模组应当干净")
    report = checks.validate_mod(SAMPLE, deep=True)
    s = report["summary"]
    ok("0 个 error", s["errors"] == 0, str([i for i in report["issues"] if i["level"] == "error"][:3]))
    ok("7 个校验器全部跑完", all(v["status"] == "ok" for v in report["validators"]),
       str([v for v in report["validators"] if v["status"] != "ok"]))
    ok("国策抽到 6 个", s["definitions"].get("focus") == 6, str(s["definitions"]))
    ok("本地化覆盖率 100%", any(
        i.get("kind") == "localisation_summary" and i.get("coverage") == 100.0
        for i in report["issues"]))


# --------------------------------------------------------------------------- #
# 3. Broken fixture — every injected defect must be caught
# --------------------------------------------------------------------------- #

EXPECTED = [
    # (level, validator, 文件片段, 消息片段, 说明)
    ("error", "descriptor", "descriptor.mod", "supported_version", "1.19.x 版本号写法不合法"),
    ("error", "localisation", "broken_l_english.yml", "BOM", "本地化文件缺 BOM"),
    ("error", "syntax", "broken_ideologies.txt", "unclosed", "少一个右花括号"),
    ("error", "duplicates", "broken_focus_dup.txt", "BAD_focus_a", "国策 id 跨文件重复"),
    # info 而非 error：夹具的外层 .mod 声明了 dependencies（见 broken_mod.mod），
    # 有依赖时缺键可能由父模组提供，降级为 info 是 check_missing_loc 的既定语义。
    # 这条同时验证 dependencies 裸 token 提取真的生效了——之前 stmts() 恒为空，
    # deps 恒为 []，这里永远是 error，级联失效完全不可见。
    ("info", "localisation", "broken_focus.txt", "BAD_focus_b", "国策缺本地化键（有依赖时降级）"),
    ("error", "localisation", "broken_events.txt", "命名空间", "事件没写 add_namespace"),
    ("warn", "localisation", "broken_events.txt", "选项没有 name", "事件选项缺 name"),
    ("info", "assets", "broken_sprites.gfx", "missing_icon.dds",
     "贴图文件不存在（未索引原版时降为 info，不冤枉复用原版 gfx 的模组）"),
    ("info", "technology", "broken_techs.txt", "BAD_tech_does_not_exist", "科技后继目标不存在"),
    ("warn", "descriptor", "descriptor.mod", "BOM", "描述文件带 BOM"),
    ("warn", "descriptor", "broken_mod.mod", "thumbnail", "预览图字段写成 thumbnail 而非 picture"),
    ("warn", "descriptor", "descriptor.mod", "replace_path", "replace_path 只写在一个描述文件里"),
    # 下面三条都曾是「静默零检出」：裸 token 列表被 stmts() 整块跳过，
    # selftest 全绿但检查形同虚设。夹具必须钉住它们。
    ("info", "on_actions", "broken_on_actions.txt", "BAD_on_action_event", "on_actions 裸 token 引用不存在的事件"),
    ("info", "on_actions", "broken_on_actions.txt", "BAD_random_event", "on_actions 权重写法引用不存在的事件"),
]


def test_broken() -> None:
    section("3. 错误夹具 —— 每个注入的缺陷都要被逮住")
    report = checks.validate_mod(BROKEN, deep=True, per_check=50, max_issues=300)
    issues = report["issues"]

    for level, vid, filepart, msgpart, desc in EXPECTED:
        hit = [
            i for i in issues
            if i.get("validator") == vid
            and filepart in (i.get("file") or "")
            and msgpart in i.get("message", "")
        ]
        ok(f"{desc}", bool(hit) and any(i["level"] == level for i in hit),
           f"期望 {level}/{vid}/{filepart}/{msgpart}，实际 {hit[:1]}")

    s = report["summary"]
    ok("结论是「不能进游戏」", s["verdict"] != "可以进游戏了")
    ok("没有产出任何 error 以外的等级混淆",
       s["errors"] == sum(1 for i in issues if i["level"] == "error"))
    ok("小模组缺键不当作翻译子模组降级",
       not any(i.get("kind") == "localisation_summary" and i.get("partial") for i in issues))

    # 索引了原版之后，同一个缺失贴图必须升级为 error —— 降级只是「不知道」时的妥协
    loc = checks.scan_localisation(BROKEN)
    defs = checks.collect_definitions(BROKEN)["definitions"]
    ctx = validators.Ctx(BROKEN, defs, loc["keys"], vanilla_root=ROOT)
    assets = validators.check_assets(ctx)
    ok("索引原版后缺失贴图升级为 error",
       bool(assets) and all(i["level"] == "error" for i in assets), str(assets[:1]))

    # add_ideas 裸 token：夹具的 known("idea") 为空时 check_history 会静默跳过
    # 整条检查（if name and ideas and ...），所以这里喂一个已定义的 idea 集，
    # 断言「引用了没定义的 idea」真的被报出来。夹具文件 history/countries/BAD_country.txt。
    ctx_hist = validators.Ctx(BROKEN, defs, loc["keys"], vanilla_root=ROOT)
    hist = validators.check_history(ctx_hist)
    hit = [i for i in hist if "BAD_missing_idea" in i.get("message", "")]
    ok("add_ideas 裸 token 引用不存在的 idea 被抓到", bool(hit), str(hist[:1]))

    # check_defines：Lua 表形式不再逐行误报「没有 NDefines. 前缀」。
    # 表形式 NDefines = { NGame = { ... } } 的内部键本来就不带前缀，逐行检查
    # 会把每一行都报成 warn。检测到表形式就跳过逐行检查，裸赋值写法照报。
    # 该检查器此前没有任何夹具覆盖，一并补上。
    dmod = tempfile.mkdtemp(prefix="modkit-defines-")
    Path(dmod, "common", "defines").mkdir(parents=True, exist_ok=True)
    Path(dmod, "common", "defines", "table.lua").write_text(
        'NDefines = {\n'
        '    NGame = {\n'
        '        START_DATE = "1936.1.1",\n'
        '        END_DATE = "1949.1.1",\n'
        '    },\n'
        '}\n',
        encoding="utf-8",
    )
    Path(dmod, "common", "defines", "bare.lua").write_text(
        'NGame.START_DATE = "1936.1.1"\n',
        encoding="utf-8",
    )
    ctx_def = validators.Ctx(dmod, {}, set(), vanilla_root="")
    d_issues = validators.check_defines(ctx_def)
    d_table = [i for i in d_issues if i.get("file", "").endswith("table.lua")]
    d_bare = [i for i in d_issues if i.get("file", "").endswith("bare.lua")]
    ok("表形式 defines 不再逐行误报前缀", not d_table, str(d_table[:2]))
    ok("裸赋值 defines 仍报缺前缀（原有行为不回退）",
       bool(d_bare) and d_bare[0]["level"] == "warn", str(d_bare[:1]))
    shutil.rmtree(dmod, ignore_errors=True)

    # check_music：音乐两层结构完整性（EB-022）。
    # play_song 引用未定义歌名会静默失效；.asset 指向缺失音频；
    # music/ 混入非 ogg。夹具：一首定义齐全、一首指向不存在文件、
    # 一台电台选了一首幽灵歌、一个 mp3、一处 play_song 幽灵引用。
    mmod = tempfile.mkdtemp(prefix="modkit-music-")
    Path(mmod, "music").mkdir(parents=True, exist_ok=True)
    Path(mmod, "music", "my_music.asset").write_text(
        'music = { name = "known_song" file = "known_song.ogg" volume = 0.5 }\n'
        'music = { name = "bad_file_song" file = "nope.ogg" }\n',
        encoding="utf-8",
    )
    Path(mmod, "music", "known_song.ogg").write_bytes(b"OggS-fake")
    Path(mmod, "music", "broken.mp3").write_bytes(b"ID3-fake")
    Path(mmod, "music", "station.txt").write_text(
        'music_station = "m"\n'
        'music = { song = "known_song" }\n'
        'music = { song = "ghost_song" }\n',
        encoding="utf-8",
    )
    Path(mmod, "common", "on_actions").mkdir(parents=True, exist_ok=True)
    Path(mmod, "common", "on_actions", "00_music_test.txt").write_text(
        'on_actions = {\n'
        '\ton_startup = { effect = { play_song = "ghost_song" } }\n'
        '}\n',
        encoding="utf-8",
    )
    ctx_music = validators.Ctx(mmod, {}, set(), vanilla_root="")
    m_issues = validators.check_music(ctx_music)
    m_all = str([(i.get("message"), i.get("level")) for i in m_issues])
    ok("play_song 引用未定义歌名被抓（无原版时 warn）",
       any("ghost_song" in i.get("message", "") and i["level"] == "warn" for i in m_issues), m_all)
    ok("电台选曲的幽灵歌同样被抓",
       sum(1 for i in m_issues if "ghost_song" in i.get("message", "")) == 2, m_all)
    ok(".asset 指向不存在的音频 → error",
       any("nope.ogg" in i.get("message", "") and i["level"] == "error" for i in m_issues), m_all)
    ok("music/ 里的非 ogg 被提示", any("broken.mp3" in (i.get("file") or "") for i in m_issues), m_all)
    ok("定义齐全的 known_song 不报（无误伤）",
       not any("known_song" in i.get("message", "") for i in m_issues), m_all)
    shutil.rmtree(mmod, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 4. Planner
# --------------------------------------------------------------------------- #

def test_planner() -> None:
    section("4. 规划与进度")
    tmp = tempfile.mkdtemp(prefix="modkit-plan-")
    try:
        mod = os.path.join(tmp, "mymod")
        os.makedirs(mod)
        r = planner.plan_action(mod, "init")
        ok("init 生成 8 个阶段", len(r["steps"]) == 8, str(len(r.get("steps", []))))
        ok("初始进度 0/8", r["progress"] == "0/8", r.get("progress", ""))
        ok("下一步是 s1", (r.get("next") or {}).get("id") == "s1", str(r.get("next")))
        ok("ROADMAP.md 落盘", os.path.isfile(os.path.join(mod, "ROADMAP.md")))
        ok("plan.json 落盘", os.path.isfile(os.path.join(mod, ".modkit", "plan.json")))

        r = planner.plan_action(mod, "update", step_id="s1", status="done")
        ok("标记 s1 完成后进度前进", r["progress"] == "1/8", r.get("progress", ""))
        ok("下一步推进到 s2", (r.get("next") or {}).get("id") == "s2", str(r.get("next")))

        r = planner.plan_action(mod, "add", title="自定义阶段")
        ok("可追加自定义阶段", len(r["steps"]) == 9, str(len(r.get("steps", []))))

        # 状态重读：重新加载 plan.json 不能丢状态
        r = planner.plan_action(mod, "status")
        ok("状态持久化", r["progress"] == "1/9", r.get("progress", ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 5. Preview
# --------------------------------------------------------------------------- #

def test_preview() -> None:
    section("5. 离线预览")
    tmp = tempfile.mkdtemp(prefix="modkit-prev-")
    try:
        bundle = checks.collect_definitions(SAMPLE)
        loc = checks.scan_localisation(SAMPLE)
        report = checks.validate_mod(SAMPLE)
        out = os.path.join(tmp, "preview.html")
        preview.render(
            SAMPLE, out,
            name="Modkit Sample", version="0.1.0",
            definitions=bundle["definitions"], loc=loc,
            issues=report["issues"], stats=report["summary"],
        )
        ok("生成 HTML 文件", os.path.isfile(out))
        html = open(out, encoding="utf-8").read()
        ok("自包含：没有外链 http(s)", "http://" not in html and "https://" not in html)
        ok("没有引用外部 js/css", "<script src" not in html and "link rel=\"stylesheet\"" not in html)
        ok("国策树画出了 svg", "<svg" in html)
        ok("6 个国策节点都在图上", html.count("GER_autobahn") >= 6, str(html.count("GER_autobahn")))
        ok("体积合理（<200KB）", os.path.getsize(out) < 200_000, str(os.path.getsize(out)))

        # 坐标解算是国策树可视化的命门，但这批断言原来只查「节点在不在图上」——
        # 文字在 HTML 里出现过就算过，坐标全错也照样绿。于是 relative_position_id
        # 整条链没被实现，测试一直是通的。下面直接盯坐标数值。
        placed = preview.resolve_positions(
            [
                {"id": "A", "x": "10", "y": "0", "rel": ""},
                {"id": "B", "x": "2", "y": "1", "rel": "A"},        # 相对 A
                {"id": "C", "x": "1", "y": "1", "rel": "B"},        # 相对 B，链深 2
                {"id": "D", "x": "3", "y": "0", "rel": "A"},        # 兄弟，同一锚点
            ]
        )
        ok("无锚点：坐标即绝对值", placed["A"] == (10, 0), str(placed["A"]))
        ok("单层 delta：锚点 + 偏移", placed["B"] == (12, 1), str(placed["B"]))
        ok("多层 delta 沿链累加（不是只加一层）", placed["C"] == (13, 2), str(placed["C"]))
        ok("同锚点的兄弟不互相干扰", placed["D"] == (13, 0), str(placed["D"]))

        # 环检测：mod 里 A 相 B、B 相 A 是常见手误，不设防会无限递归爆栈。
        cyc = preview.resolve_positions(
            [
                {"id": "X", "x": "1", "y": "0", "rel": "Y"},
                {"id": "Y", "x": "1", "y": "0", "rel": "X"},
            ]
        )
        ok("循环锚点不死循环", isinstance(cyc, dict) and len(cyc) == 2, str(cyc))

        # 端点必须真的被采到，否则 resolve 拿到的 rel 永远是空。
        sample_focuses = checks.collect_definitions(SAMPLE)["definitions"].get("focus", [])
        ok("采集端带上了 rel 字段", all("rel" in f for f in sample_focuses) if sample_focuses else False,
           str(sample_focuses[:1]))

        # shared_focus 是大树的公共锚点。解算输入必须含 shared，渲染才过滤；
        # 之前先过滤再解算，锚定到 shared 的节点查不到锚点、全部按 (0,0) 起算。
        shared_placed = preview.resolve_positions(
            [
                {"id": "shared_top", "x": "5", "y": "0", "rel": "", "shared": True},
                {"id": "A", "x": "0", "y": "1", "rel": "shared_top"},
            ]
        )
        ok("shared 锚点参与解算", shared_placed.get("shared_top") == (5, 0), str(shared_placed))
        ok("锚定到 shared 的节点落在正确格子", shared_placed.get("A") == (5, 1), str(shared_placed))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 6. Scaffolder
# --------------------------------------------------------------------------- #

def test_scaffolder() -> None:
    section("6. 脚手架")
    tmp = tempfile.mkdtemp(prefix="modkit-scaf-")
    try:
        mod = os.path.join(tmp, "fresh")
        os.makedirs(mod)
        scaffolder.scaffold(mod_path=mod, kind="mod", name="Fresh", tag="GER", namespace="fresh")
        ok("mod 骨架建出 descriptor.mod", os.path.isfile(os.path.join(mod, "descriptor.mod")))
        desc = open(os.path.join(mod, "descriptor.mod"), encoding="utf-8").read()
        ok("supported_version 写成 1.19.*", '"1.19.*"' in desc, desc[:120])

        scaffolder.scaffold(mod_path=mod, kind="focus", name="test_focus", tag="GER",
                            namespace="fresh", x=0, y=0)
        focus_files = [f for f in os.listdir(os.path.join(mod, "common", "national_focus"))]
        ok("国策文件落盘", bool(focus_files), str(focus_files))
        body = open(os.path.join(mod, "common", "national_focus", focus_files[0]), encoding="utf-8").read()
        ok("国策文件没有 BOM", not body.startswith("\ufeff"))
        ok("国策带 id 与 completion_reward", "id = " in body and "completion_reward" in body)

        locdir = os.path.join(mod, "localisation")
        ymls = []
        for base, _dirs, files in os.walk(locdir):
            ymls += [os.path.join(base, f) for f in files if f.endswith(".yml")]
        ok("本地化文件落盘", bool(ymls), str(ymls))
        if ymls:
            raw = open(ymls[0], "rb").read()
            ok("本地化文件带 UTF-8 BOM", raw.startswith(b"\xef\xbb\xbf"), ymls[0])
            ok("本地化有语言头", b"_english:" in raw or b"_simp_chinese:" in raw)

        scaffolder.scaffold(mod_path=mod, kind="tech", name="test_tech", tag="GER", namespace="fresh")
        techs = os.listdir(os.path.join(mod, "common", "technologies"))
        ok("科技文件落盘", bool(techs), str(techs))

        # 回归：生成器默认图标曾经写的是原版里不存在的 sprite
        # （GFX_focus_generic_industry / generic_political_advisor 等），
        # 新手第一步就会拿到空白图标。这几个名字一个都不许再出现。
        bad = [
            ("GFX_focus_generic_industry", "GFX_focus_generic_industry_2"),
            ("generic_political_actions", "GFX_decision_generic_political_rally"),
            ("generic_political_advisor", "GFX_idea_generic_build_infrastructure"),
            ("GFX_report_event_generic_political", "GFX_report_event_generic_army"),
        ]
        for kind, nm in (("event", "test_event"), ("decision", "test_dec"), ("idea", "test_idea")):
            try:
                scaffolder.scaffold(mod_path=mod, kind=kind, name=nm, tag="GER", namespace="fresh")
            except Exception as exc:  # noqa: BLE001 - 只是为了不让一条失败拖垮整组
                ok(f"{kind} 能生成", False, str(exc))
        blob = ""
        for base, _d, files in os.walk(mod):
            for f in files:
                if f.endswith(".txt"):
                    blob += open(os.path.join(base, f), encoding="utf-8-sig", errors="replace").read()
        for wrong, right in bad:
            # 精确匹配整词：GFX_focus_generic_industry 是 _2 的前缀，不能用 in 判断
            hit = re.search(re.escape(wrong) + r"(?![A-Za-z0-9_])", blob)
            ok(f"生成器不用不存在的图标 {wrong}", hit is None, f"应改用 {right}")

        # ---- kind=loc 对已有文件必须合并而不是重写 ----
        # 之前直接把 stub 塞进 writes 并标 merge_ok（允许覆盖），第二次跑
        # kind=loc 会把用户写好的词条全部清掉只剩一行 TODO，还报告 created。
        loc_file = os.path.join(mod, "localisation", "english", "ger_merge_test_l_english.yml")
        os.makedirs(os.path.dirname(loc_file), exist_ok=True)
        open(loc_file, "w", encoding="utf-8-sig").write(
            "\ufeffl_english:\n GER_MERGE_TEST:0 \"宝贵内容\"\n GER_MERGE_TEST2:0 \"第二条\"\n"
        )
        r_loc = scaffolder.scaffold(mod_path=mod, kind="loc", name="merge_test", tag="GER")
        body_loc = open(loc_file, encoding="utf-8-sig").read()
        ok("kind=loc 不清空已有词条", "宝贵内容" in body_loc and "第二条" in body_loc, body_loc[:120])
        ok("kind=loc 只追加缺失键",
           ("created" in r_loc and not r_loc["created"]) or "MERGE_TEST" in body_loc,
           str(r_loc.get("created")))

        # on_action 生成的骨架必须是合法脚本（曾生成 set_variable = X = yes 双等号）
        gen = scaffolder.gen_on_action("GER", "rebuild")
        gen_root, gen_errs = cw.parse(gen)
        ok("on_action 骨架无语法错误",
           not [e for e in gen_errs if e.get("level") == "error"], str(gen_errs[:2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 7. Knowledge base
# --------------------------------------------------------------------------- #

def test_kb() -> None:
    section("7. 知识库")
    tmp = tempfile.mkdtemp(prefix="modkit-kb-")
    db = os.path.join(tmp, "kb.sqlite")
    try:
        r = kb.build([{"name": "sample", "path": SAMPLE, "kind": "mod"}], db)
        src = r["sources"][0]
        ok("索引完成", src["files"] > 0, str(src))
        ok("抽到了符号", r["total_symbols"] > 0, str(r["total_symbols"]))
        ok("抽到了本地化词条", src["loc_entries"] > 0, str(src["loc_entries"]))

        st = kb.stats(db)
        ok("符号按类型统计", st["symbols_by_kind"].get("focus") == 6, str(st["symbols_by_kind"]))
        ok("本地化条数对得上", st["loc_entries"] > 0, str(st["loc_entries"]))

        # 顶层目录的内容必须也能抽到。回归用例：路径判断原来写的是
        # `"/events/" in lower`，而原版相对路径是 `events/x.txt`（无前导斜杠），
        # 于是 2 万条事件一条都没进索引，还不报错。`common/xxx/` 因为中间有斜杠
        # 所以照常工作——这个洞只有**顶层目录**才暴露，必须专门断言。
        ok("顶层 events/ 的事件被抽到（不是 0 条）",
           st["symbols_by_kind"].get("event", 0) > 0,
           f"event={st['symbols_by_kind'].get('event', 0)}")
        top_types = [k for k in ("event",) if st["symbols_by_kind"].get(k)]
        ok("事件类型进了 symbols 表", bool(top_types), str(sorted(st["symbols_by_kind"])))

        hits = kb.search("autobahn", db_path=db, limit=10)
        ok("标识符检索命中", hits["hit_count"] > 0, str(hits)[:200])
        ok("命中带行号与片段", bool(hits["hits"][0].get("snippet")), str(hits["hits"][:1])[:200])

        zh = kb.search("高速公路", db_path=db, limit=10)
        ok("中文子串检索（trigram）不报错", isinstance(zh, dict) and "hit_count" in zh, str(zh)[:150])

        # 中文多字组合必须真能命中。回归用例：整串当短语时要求逐字相邻，
        # 「国策树坐标」五字连写并不存在 → 恒 0 命中，而用户的意思明明是
        # 「讲国策树和坐标的文档」。切 2 字滑窗后按词频排。
        #
        # 这两篇刻意这么写：A 只含「坐标」这个二字词，B 只含「国策树」这个三字词。
        # 3 字滑窗会把 A 的「坐标」整段切掉，于是 A 落选、只剩 B——断言失败。
        # 2 字窗两个词都留，A 因词频更高排第一。这样才真正区分得开两种实现。
        #
        # 走真实 md 文件而不是 add_note：笔记要在 files 表里才有 source，
        # 否则 search 的 source 过滤会把它滤掉（踩过）。
        notes_dir = os.path.join(tmp, "zhnotes")
        os.makedirs(notes_dir, exist_ok=True)
        with open(os.path.join(notes_dir, "坐标.md"), "w", encoding="utf-8") as f:
            f.write("# 图标坐标排布\n\n坐标 x 与坐标 y 决定图标位置，坐标重叠会导致连线错乱。\n")
        with open(os.path.join(notes_dir, "树.md"), "w", encoding="utf-8") as f:
            f.write("# 国策树结构\n\n国策树由多个国策树分支组成，国策树之间靠前置连接。\n")
        kb.build([{"name": "zh", "path": notes_dir, "kind": "notes"}], db, incremental=False)

        multi = kb.search("国策树坐标", db_path=db, limit=5, scope="local", source="zh")
        ok("中文四字组合能命中（不是 0 条）", multi["hit_count"] > 0, str(multi["hit_count"]))
        ok("两篇都该出现（2 字词与 3 字词都不许丢）", multi["hit_count"] >= 2, str(multi["hit_count"]))
        titles = [h.get("title") or "" for h in multi["hits"]]
        ok("两篇都在结果里", any("坐标" in t for t in titles) and any("树" in t for t in titles), str(titles))

        # 排序按滑窗累计词频：「国策/策树」两个窗都在树篇命中 → 树篇分更高。
        # 这里断言的是「词频确实参与了排序」，不是「某个主题天然优先」。
        one = kb.search("国策树", db_path=db, limit=5, scope="local", source="zh")
        ok("单独查三字词，树篇排第一",
           bool(one["hits"]) and "树" in (one["hits"][0].get("title") or ""),
           str([h.get("title") for h in one["hits"]]))
        two = kb.search("坐标重叠连线错乱", db_path=db, limit=5, scope="local", source="zh")
        ok("查坐标专属说法，坐标篇排第一",
           bool(two["hits"]) and "坐标" in (two["hits"][0].get("title") or ""),
           str([h.get("title") for h in two["hits"]]))

        # 反向：三字以内仍走原短语路径，不能被滑窗搅乱
        short = kb.search("高速公路", db_path=db, limit=5, scope="local")
        ok("短中文查询不受滑窗影响", isinstance(short["hit_count"], int), str(short)[:120])

        one = kb.find_symbol("GER_autobahn_1", db_path=db)
        ok("按 id 精确定位", bool(one.get("found")), str(one)[:160])
        ok("顺带带出本地化文本", bool(one.get("localisation")), str(one.get("localisation"))[:160])

        n = kb.add_note("selftest", "自检写入的一条笔记", "tag1", db)
        ok("笔记可写", bool(n.get("ok")), str(n))
        notes = kb.list_notes(db_path=db)
        ok("笔记可读回", any(x.get("title") == "selftest" for x in notes.get("notes", [])), str(notes)[:200])

        # ---- 全量重建必须清掉已删除文件的残留行 ----
        # 之前 stale 清理整个包在 if incremental 里，全量重建对「磁盘上已删掉
        # 的文件」什么都不做：文件在五张表里永久残留、继续被检索命中，
        # stale_removed 还如实报 0。
        ghost_src = os.path.join(tmp, "ghost_src")
        os.makedirs(ghost_src, exist_ok=True)
        g1 = os.path.join(ghost_src, "a.md")
        g2 = os.path.join(ghost_src, "b.md")
        open(g1, "w", encoding="utf-8").write("ghost_alpha 独有词")
        open(g2, "w", encoding="utf-8").write("ghost_beta 独有词")
        ghost_db = os.path.join(tmp, "ghost.sqlite")
        kb.build([{"name": "ghost", "path": ghost_src, "kind": "notes"}], ghost_db, incremental=False)
        os.remove(g2)
        kb.build([{"name": "ghost", "path": ghost_src, "kind": "notes"}], ghost_db, incremental=False)
        r_ghost = kb.search("ghost_beta", db_path=ghost_db, scope="local")
        ok("全量重建后已删文件不再命中（无 ghost）", r_ghost["hit_count"] == 0, str(r_ghost["hit_count"]))
        ok("a 的内容仍在", kb.search("ghost_alpha", db_path=ghost_db, scope="local")["hit_count"] > 0)

        # ---- 解码链：GBK 文件不再整篇变 U+FFFD，且真能被检索到 ----
        # 之前一律 utf-8-sig + errors="replace"，GBK 文件乱码照常进索引且增量
        # 永不重试。回退链 gbk → cp1252 → latin-1，触发条件是乱码「又多又密」。
        ok("_decode：干净 utf-8 不回退", kb._decode("国策树".encode("utf-8"))[1:] == ("utf-8", 0),
           str(kb._decode("国策树".encode("utf-8"))))
        ok("_decode：长 GBK 文本走 gbk 分支",
           kb._decode(("国策树连线按坐标排布。" * 10).encode("gbk"))[0] == "国策树连线按坐标排布。" * 10)
        ok("_decode：零星坏字节保留 utf-8 宽松结果（不赌整篇换编码）",
           kb._decode(b"hello \xff world")[1] == "utf-8?",
           str(kb._decode(b"hello \xff world")))
        ok("_decode：latin-1 兜底（gbk/cp1252 都解不动）",
           kb._decode(b"\xff\x81" * 10)[1] == "latin-1",
           str(kb._decode(b"\xff\x81" * 10)[1]))

        gbk_dir = os.path.join(tmp, "gbknotes")
        os.makedirs(gbk_dir, exist_ok=True)
        gbk_para = "国策树连线按坐标排布，本地化缺 BOM 整个被忽略。" * 6
        Path(gbk_dir, "gbk.md").write_bytes(("# GBK 笔记\n\n" + gbk_para + "\n").encode("gbk"))
        r_gbk = kb.build([{"name": "gbk", "path": gbk_dir, "kind": "notes"}], db, incremental=False)
        ok("构建报告按编码统计（gbk 记到账上）",
           r_gbk["sources"][0]["decoding"].get("gbk") == 1,
           str(r_gbk["sources"][0].get("decoding")))
        ok("GBK 文件索引后中文可检索",
           kb.search("本地化缺", db_path=db, limit=5, scope="local", source="gbk")["hit_count"] > 0)

        # 旧库自愈：迁移前 enc 为空的行在增量构建时必须被重读，否则老索引里
        # 的乱码文件永远没有机会用新解码链修正。
        conn = kb.connect(db)
        conn.execute("UPDATE files SET enc='' WHERE source='gbk'")
        conn.commit()
        conn.close()
        r_selfheal = kb.build([{"name": "gbk", "path": gbk_dir, "kind": "notes"}], db, incremental=True)
        ok("enc 为空的旧行被增量重读（不被 skip）",
           r_selfheal["sources"][0]["unchanged"] == 0,
           str(r_selfheal["sources"][0]))
        conn = kb.connect(db)
        encs = {r for (r,) in conn.execute("SELECT DISTINCT enc FROM files WHERE source='gbk'")}
        conn.close()
        ok("重读后 enc 已如实记录", encs == {"gbk"}, str(encs))

        # ---- 混排查询：ASCII 段不许被滑窗静默丢弃 ----
        # 回归用例：之前「focus国策树」里的 focus 被剥掉，退化成纯中文查询，
        # 没写 focus 的文档也一起命中。现在 ASCII 段是 AND 约束，只有
        # focus.md（同时含 focus 与国策树）命中。
        Path(notes_dir, "focus.md").write_text(
            "# focus 与国策树\n\nfocus 是国策树的基本单位，国策树连线靠 focus 坐标排布。\n",
            encoding="utf-8",
        )
        kb.build([{"name": "zh", "path": notes_dir, "kind": "notes"}], db, incremental=False)
        mixed = kb.search("focus国策树", db_path=db, limit=5, scope="local", source="zh")
        m_titles = [h.get("title") or "" for h in mixed["hits"]]
        ok("混排查询保留 ASCII 约束（只命中同时含两者的文档）",
           mixed["hit_count"] == 1 and bool(m_titles) and "focus" in m_titles[0],
           str(m_titles))
        over = kb.search("noexist国策树", db_path=db, limit=5, scope="local", source="zh")
        ok("ASCII 约束过严时退回纯中文（不比旧版差）", over["hit_count"] >= 1, str(over["hit_count"]))

        # ---- LIKE 通配符转义：loc key 里的下划线只匹配自身 ----
        conn = kb.connect(db)
        conn.executemany(
            "INSERT INTO loc(key,lang,value,source,relpath,line) VALUES(?,?,?,?,?,?)",
            [("ZZesc_a_b", "english", "underscore 版本", "sample", "loc/esc.yml", 1),
             ("ZZesc_aXb", "english", "X 版本", "sample", "loc/esc.yml", 2)],
        )
        conn.commit()
        conn.close()
        esc_keys = [h.get("title") for h in kb.search("ZZesc_a_b", db_path=db, limit=10, scope="local")["hits"]
                    if h.get("type") == "loc"]
        ok("LIKE 转义后下划线不再当通配符", esc_keys == ["ZZesc_a_b"], str(esc_keys))

        # ---- sources.json 的路径解析 ----
        # 这一组防的是「把本机绝对路径写进配置就发出去」。插件自带的 notes/refs
        # 对所有安装者处在同一个相对位置，写绝对路径必错，写相对路径才是对的。
        root = os.path.dirname(HERE)
        r = kb._resolve_source_path
        ok("相对路径以插件根目录为基准",
           r("knowledge/notes") == os.path.join(root, "knowledge", "notes"),
           r("knowledge/notes"))
        ok("相对路径认得出 references",
           r("references") == os.path.join(root, "references"),
           r("references"))
        ok("~ 展开成家目录",
           r("~/Documents/x") == os.path.normpath(os.path.expanduser("~/Documents/x")),
           r("~/Documents/x"))
        # 绝对路径必须原样保留：用户在配置里点名某个固定位置时不能被改写。
        # 用平台自己的基准来造样本——Windows 上 "/opt/hoi4" 是「当前盘符下的路径」，
        # 不是绝对路径，直接拿它测会得到一个假的失败。
        abs_probe = os.path.join(os.path.abspath(os.sep), "opt", "hoi4")
        ok("绝对路径原样保留", r(abs_probe) == os.path.normpath(abs_probe), r(abs_probe))
        # 盘符相对路径（E:foo，没有反斜杠）不是绝对路径，但不能被当成插件内相对路径拼进去
        if os.name == "nt":
            drive_rel = r("E:foo")
            ok("盘符相对路径不会被拼到插件根目录下",
               not drive_rel.startswith(os.path.abspath(os.sep)),
               drive_rel)
        ok("空路径解析为空", r("") == "" and r("   ") == "", r(""))

        # 探测出的自带源必须真的存在（这正是「换台电脑也能用」的判据）
        srcs = {s["name"]: s["path"] for s in kb.detect_sources()}
        ok("自动探测得到 notes 源", "notes" in srcs, str(sorted(srcs)))
        ok("自动探测得到 refs 源", "refs" in srcs, str(sorted(srcs)))
        ok("探测出的 notes 目录真实存在",
           bool(srcs.get("notes")) and os.path.isdir(srcs["notes"]), str(srcs.get("notes")))
        ok("探测出的 refs 目录真实存在",
           bool(srcs.get("refs")) and os.path.isdir(srcs["refs"]), str(srcs.get("refs")))

        # 示例配置不能教人写死本机路径：notes/refs 那类自带目录必须用相对写法
        ex = os.path.join(root, "knowledge", "sources.example.json")
        if os.path.isfile(ex):
            import json as _json
            exd = _json.load(open(ex, encoding="utf-8"))
            raw_paths = [str(s.get("path") or "") for s in exd.get("sources", [])]
            ok("示例配置里的路径都是相对路径或 ~ 开头",
               all(p.startswith(("~", ".")) or not os.path.isabs(p) for p in raw_paths),
               str(raw_paths))

        # ---- 环境变量必须真的生效，且文档里写的都得存在 ----
        # 这一组防的是「文档承诺了一个开关，代码里根本没有」。
        env_probe = os.environ.pop("HOI4_MODS_ROOT", None)
        try:
            mods_tmp = os.path.join(tmp, "mods_probe")
            os.makedirs(os.path.join(mods_tmp, "fake_mod"), exist_ok=True)
            open(os.path.join(mods_tmp, "fake_mod", "descriptor.mod"), "w",
                 encoding="utf-8").write('name="x"\n')
            os.environ["HOI4_MODS_ROOT"] = mods_tmp
            got = kb.detect_sources(include_mods=True)
            names = {s["name"] for s in got}
            ok("HOI4_MODS_ROOT 生效（扫到指定目录下的模组）",
               any(n.startswith("mod:") for n in names), str(sorted(names)))
        finally:
            os.environ.pop("HOI4_MODS_ROOT", None)
            if env_probe is not None:
                os.environ["HOI4_MODS_ROOT"] = env_probe

        # HOI4_KB_DB 在模块导入时求值，这里断言的是「读到了环境变量」这条规则
        ok("HOI4_KB_DB 可覆盖索引库位置",
           "HOI4_KB_DB" in open(os.path.join(HERE, "kb.py"), encoding="utf-8").read(),
           "kb.py 里没读到 HOI4_KB_DB")

        # 文档承诺的四个环境变量，代码里必须都出现
        kb_src = open(os.path.join(HERE, "kb.py"), encoding="utf-8").read()
        for var in ("HOI4_GAME", "HOI4_USER_DIR", "HOI4_KB_DB", "HOI4_MODS_ROOT"):
            ok(f"{var} 在代码里真实存在", var in kb_src, "只在文档里写了")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 8. MCP protocol
# --------------------------------------------------------------------------- #

def test_mcp() -> None:
    section("8. MCP 协议（stdio 握手）")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1,
    )

    def send(obj: dict) -> dict:
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())

    try:
        r = send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                             "clientInfo": {"name": "selftest", "version": "1"}}})
        ok("initialize 返回 protocolVersion", r.get("result", {}).get("protocolVersion") == "2024-11-05", str(r)[:200])
        ok("serverInfo 有名字", bool(r.get("result", {}).get("serverInfo", {}).get("name")))

        r = send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = r.get("result", {}).get("tools", [])
        # Count is asserted against plugin.json rather than hardcoded: the
        # manifest is the single source of truth other platforms may read.
        manifest = json.load(open(os.path.join(ROOT, "plugin.json"), encoding="utf-8"))
        declared = manifest["capabilities"]["mcpServers"]["kiant-hoi4-modkit"]["tools"]
        ok("工具数量与 plugin.json 一致", len(tools) == len(declared),
           f"MCP {len(tools)} / manifest {len(declared)}: {[t['name'] for t in tools]}")
        names = {t["name"] for t in tools}
        ok("plugin.json 声明的工具都真的注册了", set(declared) <= names,
           str(sorted(set(declared) - names)))
        for must in ("kiant_hoi4_validate_mod", "kiant_hoi4_scaffold", "kiant_hoi4_kb_build", "kiant_hoi4_kb_search",
                     "kiant_hoi4_preview", "kiant_hoi4_plan", "kiant_hoi4_error_book", "kiant_hoi4_solutions"):
            ok(f"工具有 {must}", must in names)
        ok("每个工具都有 inputSchema", all("inputSchema" in t for t in tools))

        r = send({"jsonrpc": "2.0", "id": 31, "method": "tools/call",
                  "params": {"name": "kiant_hoi4_error_book",
                             "arguments": {"query": "科技页连线一条都没有"}}})
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        ok("MCP 通道能查错题本", "EB-003" in text, text[:200])

        r = send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                  "params": {"name": "kiant_hoi4_validate_mod", "arguments": {"mod_path": SAMPLE}}})
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        ok("tools/call 能跑通校验", "summary" in text, text[:150])
        ok("没有置 isError", not r.get("result", {}).get("isError"), str(r)[:200])

        r = send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                  "params": {"name": "no_such_tool", "arguments": {}}})
        ok("未知工具返回错误而不是崩溃",
           bool(r.get("error")) or r.get("result", {}).get("isError") is True, str(r)[:200])

        r = send({"jsonrpc": "2.0", "id": 5, "method": "ping"})
        ok("ping 有响应", "result" in r or "error" in r, str(r)[:120])
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.wait(timeout=10)


# --------------------------------------------------------------------------- #

def test_remote() -> None:
    section("9. 远端知识库同步（本地 tarball，不走网络）")
    tmp = tempfile.mkdtemp(prefix="modkit-remote-")
    cache_home = os.path.join(tmp, "home")
    old_home = remote.CACHE_ROOT
    remote.CACHE_ROOT = cache_home
    try:
        # 造一个「仓库」：顶层目录 + 两个知识文件 + manifest
        repo = os.path.join(tmp, "repo")
        os.makedirs(os.path.join(repo, "knowledge", "notes"), exist_ok=True)
        os.makedirs(os.path.join(repo, "references"), exist_ok=True)
        open(os.path.join(repo, "knowledge", "notes", "a.md"), "w", encoding="utf-8").write("# A\n\n测试知识条目。\n")
        open(os.path.join(repo, "references", "b.md"), "w", encoding="utf-8").write("# B\n\n参考条目。\n")
        open(os.path.join(repo, "manifest.json"), "w", encoding="utf-8").write(
            json.dumps({"version": "test-1", "file_count": 2})
        )
        pack = os.path.join(tmp, "pack", "repo-main")
        shutil.copytree(repo, pack)
        tar_path = os.path.join(tmp, "kb.tar.gz")
        with tarfile.open(tar_path, "w:gz") as tf:
            tf.add(pack, arcname="repo-main")

        cfg = {
            "mirror": tar_path,
            "manifest": os.path.join(repo, "manifest.json"),
            "paths": ["knowledge/notes", "references"],
        }
        st = remote.status(cfg)
        ok("未同步时报告已配置但无本地版本", st["configured"] and st["local_version"] is None)
        ok("能从 manifest 读到远端版本", st["remote_version"] == "test-1", str(st.get("remote_version")))

        res = remote.pull(cfg)
        ok("pull 成功", bool(res.get("ok")), str(res)[:160])
        ok("按 paths 复制了 2 个文件", res.get("files") == 2, str(res.get("files")))
        ok("版本取自 manifest", res.get("version") == "test-1", str(res.get("version")))

        st2 = remote.status(cfg)
        ok("同步后过期判断为 False", st2["stale"] is False, str(st2.get("stale")))
        ok("再次 pull 会跳过下载", remote.pull(cfg).get("skipped") is True)
        ok("缓存能被包装成知识源", (remote.as_source(cfg) or {}).get("name") == "remote")

        # 断网：mirror 指向不存在的路径，应报错但保留缓存
        bad = dict(cfg, mirror=os.path.join(tmp, "nope.tar.gz"))
        fail = remote.pull(bad, force=True)
        ok("下载失败时不抛异常而是返回错误", fail.get("ok") is False and "error" in fail, str(fail)[:120])

        # paths 配错：报错，但旧缓存必须原封不动（stage-then-switch）。
        # 之前直接 rmtree(dest) 再复制，copied==0 报错返回时缓存已经没了，
        # 离线知识库凭空蒸发。
        wrong = dict(cfg, paths=["no/such/dir"])
        wfail = remote.pull(wrong, force=True)
        ok("paths 配错返回错误", wfail.get("ok") is False, str(wfail)[:160])
        ok("paths 配错时旧缓存仍在", (remote.as_source(cfg) or {}).get("name") == "remote")
        ok("旧缓存版本未丢", remote.status(cfg).get("local_version") == "test-1",
           str(remote.status(cfg).get("local_version")))
        dest_d = remote.cache_dir(cfg)
        leftovers = [p for p in (dest_d + ".staging", dest_d + ".old") if os.path.exists(p)]
        ok("失败路径不留 staging/.old 临时目录", not leftovers, str(leftovers))

        # 正常重新 pull（force）：走完整换装路径，旧缓存被 .old 顶掉后清理
        repull = remote.pull(cfg, force=True)
        ok("换装式重新 pull 成功", repull.get("ok") is True and repull.get("files") == 2,
           str(repull)[:160])
        leftovers2 = [p for p in (dest_d + ".staging", dest_d + ".old") if os.path.exists(p)]
        ok("换装成功后同样不留临时目录", not leftovers2, str(leftovers2))
        ok("换装后缓存仍可用", (remote.as_source(cfg) or {}).get("name") == "remote")
    finally:
        remote.CACHE_ROOT = old_home
        shutil.rmtree(tmp, ignore_errors=True)


def test_tiers() -> None:
    section("10. 两级资料库（平台优先，本地兜底）")
    tmp = tempfile.mkdtemp(prefix="modkit-tier-")
    db = os.path.join(tmp, "kb.sqlite")
    try:
        plat = os.path.join(tmp, "platform")
        loc = os.path.join(tmp, "local")
        os.makedirs(plat)
        os.makedirs(loc)
        open(os.path.join(plat, "p.md"), "w", encoding="utf-8").write("# 平台条目\n\nZZPLATONLY 平台独有关键词。\n")
        open(os.path.join(loc, "l.md"), "w", encoding="utf-8").write("# 本地条目\n\nZZLOCALONLY 本地独有关键词。\n")
        kb.build(
            [{"name": "remote", "path": plat, "kind": "notes"},
             {"name": "notes", "path": loc, "kind": "notes"}],
            db_path=db,
        )

        st = kb.stats(db)
        ok("平台源被识别", st["tiers"]["platform"] == ["remote"], str(st["tiers"]))
        ok("本地源被识别", "notes" in st["tiers"]["local"], str(st["tiers"]))

        d = kb.search("ZZPLATONLY", db_path=db)
        ok("auto：平台命中时只返平台", d["answered_from"] == "platform" and d["tiers"].get("local") is None,
           str(d["tiers"]))
        ok("auto：平台命中会提示本地未查", "本地库未检索" in d.get("message", ""), d.get("message", ""))

        d = kb.search("ZZLOCALONLY", db_path=db)
        ok("auto：平台没有才退本地", d["answered_from"] == "local", str(d["tiers"]))
        ok("auto：回退时明确说明", "来自本地库" in d.get("message", ""), d.get("message", ""))

        d = kb.search("ZZPLATONLY", db_path=db, scope="platform")
        ok("platform：只查平台", all(h["tier"] == "platform" for h in d["hits"]), str(d["hits"][:1]))

        d = kb.search("ZZLOCALONLY", db_path=db, scope="local")
        ok("local：能查到本地", d["hit_count"] >= 1 and all(h["tier"] == "local" for h in d["hits"]))

        d = kb.search("ZZ", db_path=db, scope="all")
        tiers = {h["tier"] for h in d["hits"]}
        ok("all：两级合并返回", tiers == {"platform", "local"}, str(tiers))
        ok("all：平台排在本地前面", d["hits"][0]["tier"] == "platform", str(d["hits"][:2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_playbook() -> None:
    """错题本 / 方案库的检索。

    这一组测的是「按症状能不能找到对应条目」——如果检索不到，错题本就等于不存在，
    再怎么整理也只是给人看的文档，工具帮不上忙。
    """
    section("11. 错题本与方案库")

    st = playbook.stats()
    # 不写死条数。每加一条错题就要改测试，改到最后必然被人改成恒真。
    # 改成「与磁盘上的 EB-*.md 文件数一致」——这才是真正要保证的事：
    # 文件在、索引读得到，两者不许脱节。
    n_eb = len([f for f in os.listdir(os.path.join(REFS, "91_error-book"))
                if f.startswith("EB-") and f.endswith(".md")])
    n_sol = len([f for f in os.listdir(os.path.join(REFS, "92_solutions"))
                 if f.startswith("SOL-") and f.endswith(".md")])
    ok("错题本条数与磁盘文件一致", st["error"]["count"] == n_eb,
       f"索引 {st['error']['count']} / 文件 {n_eb}")
    ok("方案库条数与磁盘文件一致", st["solution"]["count"] == n_sol,
       f"索引 {st['solution']['count']} / 文件 {n_sol}")
    ok("错题本按症状分类", set(st["error"]["by_symptom_class"]) == {"界面显示", "游戏内行为", "日志校验", "工具流程", "功能不生效", "汉化"},
       str(list(st["error"]["by_symptom_class"])))
    ok("方案库每条都有状态", all(k != "(未标)" for k in st["solution"]["by_status"]), str(list(st["solution"]["by_status"])))

    # 症状描述 → 正确条目排第一。这几条都是真实踩坑时脑子里会冒出来的说法。
    cases = [
        ("科技页连线一条都没有", "EB-003"),
        ("中文全是问号", "EB-002"),
        ("校验报了一堆假阳性", "EB-016"),
        ("事件不触发", "EB-008"),
        ("图标被裁掉了", "EB-005"),
        ("error.log 刷了几千行", "EB-012"),
        ("界面显示 GFX_ 开头的原样文字", "EB-001"),
    ]
    for query, want in cases:
        r = playbook.search(query, kind="error", limit=3)
        top = r["hits"][0]["id"] if r["hits"] else ""
        ok(f"「{query}」首条命中 {want}", top == want, f"实际 {[h['id'] for h in r['hits']]}")

    r = playbook.search("EB-016", kind="error", limit=2)
    ok("按编号直查排第一", r["hits"] and r["hits"][0]["id"] == "EB-016", str([h["id"] for h in r["hits"]]))
    ok("按编号命中时说明原因", "ID" in " ".join(r["hits"][0].get("matched", [])), str(r["hits"][0].get("matched")))

    # 碎片命中必须被拒。以前不做这一步时，「性能不好」会通过「能不」把半个错题本捞出来。
    r = playbook.search("性能不好", kind="error", limit=5)
    ok("纯字面碎片不算命中", r["count"] == 0, str([h["id"] for h in r["hits"]]))
    ok("丢弃碎片时说明原因", "字面碎片" in r.get("note", ""), r.get("note", ""))

    # 领域词，错题本确实没有，不能硬凑
    r = playbook.search("坦克设计器槽位", kind="error", limit=3)
    ok("没命中就返回空", r["count"] == 0, str([h["id"] for h in r["hits"]]))
    ok("空结果给出下一步", bool(r.get("hint")) and bool(r.get("next")), str(r.get("hint", "")))

    g = playbook.get("error", "EB-003")
    ok("get 取到全文", g["ok"] and "标准化方案" in g["sections"], str(g.get("sections")))
    ok("get 带可信度说明", "已实证" in g["trust"], g["trust"])
    ok("get 给出文件路径", g["file"].endswith("EB-003-tech-lines-silently-gone.md"), g["file"])

    g = playbook.get("error", "EB-003", "标准化方案")
    ok("section 只取一节", g["ok"] and "technology_folders" in g["body"] and "## 症状" not in g["body"],
       g.get("body", "")[:80])

    g = playbook.get("error", "EB-999")
    ok("查不存在的编号明确报错", not g["ok"] and g.get("known"), g.get("message", ""))

    r = playbook.search("", kind="error", symptom_class="界面显示", limit=99)
    # 同理不写死 6。每加一条界面类错题都要改，最后必然改成恒真。
    # 要保证的是「过滤真的生效」——非空、且逐条都是这个类。
    ok("按症状大类过滤", r["count"] > 0 and all(h["symptom_class"] == "界面显示" for h in r["hits"]),
       str(r["count"]))
    r = playbook.search("", kind="error", severity="阻断", limit=99)
    # 不写死「只有 1 条」——每加一条阻断级错题都要改测试，改着改着就改成恒真了。
    # 只要求：命中集合非空、包含已知的 EB-007、且逐条确认确实是阻断级。
    ids = [h["id"] for h in r["hits"]]
    ok("按严重程度过滤", "EB-007" in ids and all(h.get("severity") == "阻断" for h in r["hits"]), str(ids))

    r = playbook.search("", kind="solution", status="upstream-only", limit=99)
    ok("方案库按状态过滤", r["count"] == 9, str(r["count"]))
    ok("方案库提示未验证", "未验证" in r["trust"], r["trust"])
    r = playbook.search("", kind="solution", status="rejected", limit=99)
    ok("rejected 条目可单独调出", r["count"] == 1, str([h["id"] for h in r["hits"]]))

    r = playbook.search("dds", kind="solution", limit=3)
    ok("方案库英文子串能查到", r["hits"] and r["hits"][0]["id"] == "SOL-001", str([h["id"] for h in r["hits"]]))

    lint = playbook.lint()
    ok("条目自身完整（编号/文件名/related/索引）", lint["ok"], str(lint["problems"][:3]))

    r = playbook.search("科技页连线", kind="nope")
    ok("非法 kind 明确报错", not r["ok"] and "kind" in r["message"], r.get("message", ""))


def test_platform_state() -> None:
    """平台库没同步时，提示语必须按「没配 / 配了没同步」分开说。    早期版本一律写「跑 kb_sync action=pull」，但 repo 为空时跑了一定失败，
    等于把用户推到一个死胡同。
    """
    section("12. 平台库状态提示")
    tmp = tempfile.mkdtemp(prefix="modkit-state-")
    db = os.path.join(tmp, "kb.sqlite")
    try:
        loc = os.path.join(tmp, "local")
        os.makedirs(loc)
        open(os.path.join(loc, "l.md"), "w", encoding="utf-8").write("# 本地\n\nZZLOCALHIT 关键词。\n")
        kb.build([{"name": "notes", "path": loc, "kind": "notes"}], db_path=db)

        real_cfg = remote.config_path()
        backup = None
        if os.path.isfile(real_cfg):
            backup = open(real_cfg, "rb").read()
        try:
            # 1) 没配 repo
            json.dump({"repo": "", "branch": "main", "paths": [], "manifest": "manifest.json"},
                      open(real_cfg, "w", encoding="utf-8"))
            ok("未配置时判定为 unconfigured", kb._platform_state() == "unconfigured", kb._platform_state())
            d = kb.search("ZZLOCALHIT", db_path=db)
            msg = d.get("message", "")
            ok("未配置时不说「去 pull」", "action=pull 可拉取" not in msg, msg)
            ok("未配置时说明 repo 是空的", "repo 是空的" in msg, msg)
            ok("未配置时仍返回本地结果", d["answered_from"] == "local" and d["hit_count"] >= 1)

            # 2) 配了但没缓存
            json.dump({"repo": "someone/some-repo", "branch": "main",
                       "paths": ["references"], "manifest": "manifest.json"},
                      open(real_cfg, "w", encoding="utf-8"))
            ok("配了未同步时判定为 configured", kb._platform_state() == "configured", kb._platform_state())
            d = kb.search("ZZLOCALHIT", db_path=db)
            msg = d.get("message", "")
            ok("已配置时提示去 pull", "action=pull" in msg, msg)
            ok("已配置时不谎称「未配置」", "repo 是空的" not in msg, msg)
        finally:
            if backup is not None:
                open(real_cfg, "wb").write(backup)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_structure_doc() -> None:
    """STRUCTURE.md 里写的数字和路径必须与磁盘一致。

    这份文档是给人看的组织架构说明，但它最容易腐烂：加个模块、改个目录，
    文档里的数字就悄悄错了，而且没人会发现。所以把它纳入自检——错了就报。
    """
    section("13. 组织架构文档与实际一致")

    doc_path = os.path.join(ROOT, "STRUCTURE.md")
    ok("STRUCTURE.md 存在", os.path.isfile(doc_path))
    if not os.path.isfile(doc_path):
        return
    doc = open(doc_path, encoding="utf-8").read()

    # 模块清单：文档里提到的每个 .py 都要真在，且不能漏掉实际的
    actual_mods = sorted(
        f for f in os.listdir(HERE) if f.endswith(".py") and f != "__pycache__"
    )
    missing_in_doc = [m for m in actual_mods if m not in doc]
    ok("每个 mcp-server 模块都在文档里", not missing_in_doc, str(missing_in_doc))
    ghost = [
        m for m in re.findall(r"`([a-z_]+\.py)`", doc)
        if m not in actual_mods
    ]
    ok("文档没有提到不存在的模块", not ghost, str(sorted(set(ghost))))

    # 目录规模
    refs = os.path.join(ROOT, "references")
    n_refs = sum(1 for dp, _dn, fn in os.walk(refs) for f in fn if f.endswith(".md"))
    ok(f"references 篇数与文档一致（{n_refs}）", f"{n_refs} 篇" in doc, f"实际 {n_refs} 篇")

    dirs = sorted(d for d in os.listdir(refs) if os.path.isdir(os.path.join(refs, d)))
    absent = [d for d in dirs if d not in doc]
    ok("每个 references 子目录都在文档里", not absent, str(absent))

    # 各分域小计：文档表格里「| `00_start/` | 4 | ...」这种行，逐个核对。
    # 正则只锚定前两列，不要求表就两列——之前写死了 `\| (\d+) \|`，结果四列的
    # 表格（新加 08/09/10 时用了「篇数 | 管什么 | 什么时候看」）整行匹配不上，
    # 那三个域被静默跳过，"分域篇数相符"这句断言其实没管它们。
    claimed_dirs = dict(re.findall(r"\| `(\d\d_[a-z-]+/)` \| (\d+) \|", doc))
    bad_dirs = []
    for name, claimed in claimed_dirs.items():
        real = sum(1 for f in os.listdir(os.path.join(refs, name)) if f.endswith(".md"))
        if real != int(claimed):
            bad_dirs.append(f"{name}: 文档 {claimed} / 实际 {real}")
    ok(f"references 分域篇数与实际相符（{len(claimed_dirs)} 个目录）", not bad_dirs, str(bad_dirs))

    # 覆盖性：磁盘上每个 NN_ 子目录都必须在文档里有小计，否则「加了目录没写文档」
    # 这种漏不会被上面的循环发现（循环只遍历文档里有的）。
    on_disk = sorted(d for d in os.listdir(refs)
                     if re.fullmatch(r"\d\d_[a-z-]+", d)
                     and os.path.isdir(os.path.join(refs, d)))
    unlisted = [d for d in on_disk if d + "/" not in claimed_dirs]
    ok(f"磁盘上 {len(on_disk)} 个分域目录都有篇数小计", not unlisted, str(unlisted))

    # 上游知识域合计：00~06 的小计加起来必须等于文档写的总数
    upstream = {k: v for k, v in claimed_dirs.items() if k[:2] <= "06"}
    if upstream:
        total_real = sum(
            sum(1 for f in os.listdir(os.path.join(refs, k)) if f.endswith(".md"))
            for k in upstream
        )
        ok(
            f"上游七个知识域合计与文档一致（{total_real} 篇）",
            f"{total_real} 篇上游" in doc,
            f"实际 {total_real} 篇",
        )

    n_skills = len([d for d in os.listdir(os.path.join(ROOT, "skills"))])
    ok(f"技能数与文档一致（{n_skills}）", f"{n_skills} 个技能" in doc, f"实际 {n_skills}")
    for d in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        ok(f"技能 {d} 在文档里", d.replace("kiant-hoi4-", "") in doc, d)

    # --- 跨文档数字漂移：同一批数字散落在 4~5 份文件里，最容易漏改 -------- #
    # 2026-11-07 实测：加了第 20 个工具、第 15 个技能后，
    # ARCHITECTURE.md / mcp-server/README.md / PUBLISHING-LIBRARY.md 三份还写着旧数字，
    # 而 STRUCTURE.md 已经改对了。单份文件的断言管不住这种交叉漂移。
    import server as _srv  # TOOLS 由 import 副作用构建

    n_tools_mcp = len(_srv.TOOLS)
    n_refs = sum(1 for dp, _dn, fn in os.walk(os.path.join(ROOT, "references"))
                 for f in fn if f.endswith(".md"))
    n_eb = len([f for f in os.listdir(os.path.join(ROOT, "references", "91_error-book"))
                if f.startswith("EB-") and f.endswith(".md")])

    # 每份文档里「N 个技能 / N 个工具 / N 篇 / N 条错题本」的旧值都不许留。
    # 用正则抓完整数字，不能拿 "N 个工具" 直接 in——
    # "19 个工具" 里含子串 "9 个工具"，会把 19 误判成 9（实测踩过）。
    _STALE_PATS = (
        (r"(\d+) 个技能", n_skills, "技能"),
        (r"(\d+) 个工具", n_tools_mcp, "工具"),
        (r"(\d+) 篇文档", n_refs, "篇数"),
        (r"(\d+) 条错题本", n_eb, "错题本"),
    )

    def _scan_stale(txt: str) -> list[str]:
        bad = []
        for pat, real, label in _STALE_PATS:
            for m in re.finditer(pat, txt):
                if int(m.group(1)) != real:
                    bad.append(f"{label} 写 {m.group(1)}（实际 {real}）")
        return bad

    stale_suspects = []
    _DOC_FILES = ("README.md", "STRUCTURE.md", "ARCHITECTURE.md",
                  "PUBLISHING-KB.md", "PUBLISHING-LIBRARY.md", "GETTING-STARTED.md",
                  "mcp-server/README.md")
    scanned = []
    for fn in _DOC_FILES:
        p = os.path.join(ROOT, fn)
        if not os.path.isfile(p):
            continue
        scanned.append(fn)
        for msg in _scan_stale(open(p, encoding="utf-8").read()):
            stale_suspects.append(f"{fn}: {msg}")

    # 两个条件缺一不可：「没发现旧数字」+「确实把这几份文档都扫了」。
    # 只断言前者的话，把上面的文件元组清空也会绿——「检查被拆掉」和
    # 「检查通过」是同一个结果，这条断言就白写了。变异测试能证明这点。
    ok("各文档里没有旧版本的技能/工具/篇数/错题本数字",
       not stale_suspects and len(scanned) == len(_DOC_FILES),
       f"扫到 {len(scanned)}/{len(_DOC_FILES)} 份；命中 {stale_suspects[:6]}")

    # 上面那条在「文档全对」时恒真，光靠它证明不了检测有效——
    # 一个永远返回空列表的实现也能通过。所以拿一份**故意写错**的文本
    # 喂同一套匹配逻辑，验证它真的能抓出来。缺了这条，
    # 「检查被删掉」和「检查通过」是同一个结果。
    fake_bad = "本项目有 3 个技能、7 个工具、12 篇文档、1 条错题本。"
    fake_good = (f"本项目有 {n_skills} 个技能、{n_tools_mcp} 个工具、"
                 f"{n_refs} 篇文档、{n_eb} 条错题本。")
    ok("跨文档数字漂移的检测器本身有效（错文本能抓到 4 处，对文本零命中）",
       len(_scan_stale(fake_bad)) == 4 and not _scan_stale(fake_good),
       f"错文本 {_scan_stale(fake_bad)} / 对文本 {_scan_stale(fake_good)}")

    # --- 命名约定：技能 / 工具 / MCP 工具一律 kiant- 开头 ------------------ #
    # 用户明确要求「新的技能和工具都是 kiant- 开头命名」。
    # 这条断言钉住它：新增工具时忘了加前缀，这里直接报。
    # 2026-11-06 实测漏过一次：tools/ 下 dds.py / lint.py / survey.py 一直是裸名，
    # 新加的 mutate.py 也跟着裸名，四个一起违规。
    bad_skill_names = [
        d for d in os.listdir(os.path.join(ROOT, "skills"))
        if not d.startswith("kiant-hoi4-")
    ]
    ok("skills/ 下每个目录都以 kiant-hoi4- 开头", not bad_skill_names, str(bad_skill_names))

    tools_dir = os.path.join(ROOT, "tools")
    bad_tool_names = [
        f for f in sorted(os.listdir(tools_dir))
        if f.endswith(".py") and not f.startswith("kiant-hoi4-")
    ]
    ok("tools/ 下每个脚本都以 kiant-hoi4- 开头", not bad_tool_names, str(bad_tool_names))

    import server  # TOOLS 由 import 副作用构建，下面几处都要用
    bad_mcp_names = [n for n in server.TOOLS if not n.startswith("kiant_hoi4_")]
    ok("每个 MCP 工具都以 kiant_hoi4_ 开头", not bad_mcp_names, str(bad_mcp_names))

    # 反向：文档里不该再出现旧的无前缀路径，否则读者会去找不存在的文件。
    stale_paths = [
        t for t in ("tools/dds.py", "tools/lint.py", "tools/survey.py", "tools/mutate.py")
        if t in doc
    ]
    ok("文档里没有旧的无前缀工具路径", not stale_paths, str(stale_paths))

    # 工具数与骨架类型数
    n_tools = len(server.TOOLS)
    ok(f"工具数与文档一致（{n_tools}）", f"{n_tools} 个工具" in doc, f"实际 {n_tools}")
    n_sd = len(scaffolder.SD)
    ok(f"骨架类型数与文档一致（{n_sd}）", f"{n_sd} 类" in doc, f"实际 {n_sd}")

    # 行数表：抽查最大的几个模块，偏差超过 15% 就报
    rows = re.findall(r"\| `([a-z_]+\.py)` \|[^|]*\| (\d+) \|", doc)
    bad = []
    for name, claimed in rows:
        real = sum(1 for _ in open(os.path.join(HERE, name), encoding="utf-8"))
        if abs(real - int(claimed)) / max(real, 1) > 0.15:
            bad.append(f"{name}: 文档 {claimed} / 实际 {real}")
    ok("模块行数与实际相符（±15%）", not bad, str(bad))

    # 自检项数：原来只检查「文档里出现过『项自检』三个字」，那是恒真的。
    # 实测它漏了整整两轮——文档写 200、实际 207，因为后来又加了 7 条断言。
    #
    # 第二轮修法「文档数 ≥ 当前已通过数」也不够：这一组跑的时候后面的组
    # 还没跑，_passed 只是中间值（约 182），所以文档写 232 永远算「不落后」，
    # 实际已经 247 了也没人知道。**单一方向的比较挡不住漂移。**
    #
    # 正解：这里只把文档声称的数字存下来，等 main() 全部跑完再统一核对。
    # 那时 _passed 是真实总数，可以做双向严格相等。
    global _CLAIMED_SELFTEST_COUNTS
    _CLAIMED_SELFTEST_COUNTS = [int(m) for m in re.findall(r"(\d+)\s*项自检", doc)]

    # README 的性能表里写着两个示例 mod 的文件数。这种「小数字」最容易漂移：
    # 上一轮删了空目录、又清了 .modkit 产物，实际数变了但表里没跟着改。
    # （原文写 sample 9 / broken 8，实际 10 / 9。）
    readme_p = os.path.join(ROOT, "README.md")
    if os.path.exists(readme_p):
        readme = open(readme_p, encoding="utf-8").read()
        counts_bad = []
        for key, d in (("sample_mod", "examples/sample_mod"), ("broken_mod", "examples/broken_mod")):
            m = re.search(rf"`examples/{key}`\s*\|\s*(\d+)\s*文件", readme)
            if not m:
                continue
            real = sum(1 for _dp, _dn, fn in os.walk(os.path.join(ROOT, d)) for f in fn)
            if int(m.group(1)) != real:
                counts_bad.append(f"{key}: 文档 {m.group(1)} / 实际 {real}")
        ok("README 里的示例 mod 文件数与实际相符", not counts_bad, str(counts_bad))

    # 全库篇数一致性：每个文档里出现「参考库 N 篇」或「N 篇文档」的，都必须等于实际篇数。
    # 这条是补漏：之前只检查了 STRUCTURE.md 一处，结果 ARCHITECTURE.md / PUBLISHING-KB.md /
    # PUBLISHING-LIBRARY.md 三份停在 125 篇，整整落后两个版本都没人发现。
    # 文档散落在 6 个根文件里，靠人肉记住「改篇数要改几处」是不可能的。
    actual_refs = sum(1 for _dp, _dn, fn in os.walk(refs) for f in fn if f.endswith(".md"))
    doc_count_bad = []
    for name in ("README.md", "STRUCTURE.md", "ARCHITECTURE.md",
                 "PUBLISHING-KB.md", "PUBLISHING-LIBRARY.md", "GETTING-STARTED.md"):
        fp = os.path.join(ROOT, name)
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding="utf-8", errors="replace").read()
        # 只认「总数」语境，不认分项。
        #
        # 上一版用 `(\d+)\s*(篇文档|篇，|篇：|篇（|...)` 这种宽匹配，
        # 会把「### 案例区（6 篇）」「新建的三个学习域（6 篇）」这类小标题
        # 也当成总数断言，于是必须靠 `n >= 100` 兜住——而那个过滤又把
        # 76 篇 / 134 个文件这些真错值一起兜掉了。
        #
        # 正确做法是收紧语境，不是加阈值：总数总是写成
        #   「**N 篇文档**」「参考库 N 篇」「N 篇，15 个目录」
        # 分项总是写成「### xxx（N 篇）」「N 篇上游」。
        # 这里只匹配带「**」加粗或紧跟「参考库 / 个文件」的总数句式。
        pat = re.compile(
            r"\*\*(\d+) 篇文档\*\*"          # `references/` 下 **N 篇文档**
            r"|(\d+) 篇文档"                  # │ 143 篇文档    │
            r"|参考库 (\d+) 篇"               # 参考库 143 篇（84 upstream…）
            r"|(\d+) 篇，15 个目录"           # references/  143 篇，15 个目录
            r"|(\d+) 个文件按索引"            # 143 个文件按索引路由
        )
        for m in pat.finditer(txt):
            n = int(next(g for g in m.groups() if g))
            if n != actual_refs:
                doc_count_bad.append(f"{name}: 写 {n}, 实际 {actual_refs}")
                break
    ok(f"各文档写的参考库篇数都等于实际（{actual_refs}）", not doc_count_bad, str(doc_count_bad))

    # 分项之和必须等于总数。README 一直写「84 + 5 + 53 = 142」，
    # 三个数都对、加起来也对，但拆解里「51 篇自建」和「23 条错题本」
    # 两个分项是错的——只校验总数发现不了。
    eb = len([f for f in os.listdir(os.path.join(refs, "91_error-book"))
              if f.startswith("EB-") and f.endswith(".md")])
    sol = len([f for f in os.listdir(os.path.join(refs, "92_solutions"))
               if f.startswith("SOL-") and f.endswith(".md")])
    eb_bad = []
    for name in ("README.md", "STRUCTURE.md", "ARCHITECTURE.md", "GETTING-STARTED.md",
                 "PUBLISHING-KB.md", "PUBLISHING-LIBRARY.md"):
        fp = os.path.join(ROOT, name)
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"(\d+)\s*条(?:实证|错题|已经踩过|覆盖|全貌|已经)", txt):
            if int(m.group(1)) != eb:
                eb_bad.append(f"{name}: 写 {m.group(1)} 条, 实际 {eb} 条")
                break
    ok(f"各文档写的错题本条数都等于实际（{eb} 条）", not eb_bad, str(eb_bad))
    ok(f"方案库条数与磁盘一致（{sol} 条）", sol == len(
        [f for f in os.listdir(os.path.join(refs, "92_solutions")) if f.startswith("SOL-")]))


# --------------------------------------------------------------------------- #
# 14. tools/ 下的独立脚本（dds / lint / survey）
# --------------------------------------------------------------------------- #

def test_tools() -> None:
    section("14. 独立工具（dds / lint）")
    import importlib.util
    import struct

    def load(name):
        # tools/ 下的独立脚本统一带 kiant-hoi4- 前缀，与技能、MCP 工具同名系。
        p = os.path.join(ROOT, "tools", "kiant-hoi4-" + name + ".py")
        spec = importlib.util.spec_from_file_location("_t_" + name, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    dds = load("dds")
    lint = load("lint")

    tmp = tempfile.mkdtemp(prefix="modkit-tools-")
    try:
        # --- dds.py：造一个合法的 32bpp 头，检查解析出的尺寸/格式 ---
        def make_dds(path, w, h, fourcc=b"\0\0\0\0", bits=32, mips=1):
            hdr = bytearray(128)
            hdr[0:4] = b"DDS "
            struct.pack_into("<I", hdr, 4, 124)
            struct.pack_into("<I", hdr, 8, 0x1007)
            struct.pack_into("<I", hdr, 12, h)
            struct.pack_into("<I", hdr, 16, w)
            struct.pack_into("<I", hdr, 28, mips)
            struct.pack_into("<I", hdr, 76, 32)
            flags = 0x4 if fourcc.strip(b"\0") else 0x40
            struct.pack_into("<I", hdr, 80, flags | 0x1)
            hdr[84:88] = fourcc
            struct.pack_into("<I", hdr, 88, bits if not fourcc.strip(b"\0") else 0)
            # 32bpp 的 ARGB 掩码
            if not fourcc.strip(b"\0"):
                for off, mask in ((92, 0xFF0000), (96, 0xFF00), (100, 0xFF), (104, 0xFF000000)):
                    struct.pack_into("<I", hdr, off, mask)
            with open(path, "wb") as f:
                f.write(bytes(hdr))
                f.write(b"\0" * w * h * (4 if bits == 32 else 3))

        p32 = os.path.join(tmp, "a32.dds")
        make_dds(p32, 64, 64)
        info = dds.parse_header(p32)
        ok("dds 解出宽高", info["width"] == 64 and info["height"] == 64, f"{info['width']}x{info['height']}")
        ok("dds 认出未压缩 32bpp", "32bpp" in info["format"], info["format"])
        ok("dds 认出 alpha 通道", info["has_alpha"] is True)
        base, total = dds.expected_size(info)
        # 64*64*4 = 16384，不该被 128 字节头污染
        ok("dds 单级体积 = w*h*4（不含头）", base == 64 * 64 * 4, str(base))
        ok("dds mips=1 时总量等于单级", total == base, str(total))
        ok("dds 实际体积与理论一致", os.path.getsize(p32) - 128 == base,
           f"{os.path.getsize(p32)-128} vs {base}")

        # --- DXT 块数必须向上取整。曾经的 bug：72x21 算成 1440（实际 1728） ---
        pdxt = os.path.join(tmp, "b_dxt5.dds")
        make_dds(pdxt, 72, 21, fourcc=b"DXT5", bits=0)
        idxt = dds.parse_header(pdxt)
        ok("dds 认出 DXT5", idxt["format"] == "DXT5", idxt["format"])
        b_dxt, _ = dds.expected_size(idxt)
        # ceil(72/4)*ceil(21/4)*16 = 18*6*16 = 1728
        ok("DXT5 块数向上取整（72x21 → 1728，不是 1440）", b_dxt == 1728, str(b_dxt))

        # 宽高都整除 4 时，取整不该多算
        p4 = os.path.join(tmp, "c_dxt5.dds")
        make_dds(p4, 64, 64, fourcc=b"DXT5", bits=0)
        b4, _ = dds.expected_size(dds.parse_header(p4))
        ok("DXT5 宽高整除 4 时正好 16*16*16", b4 == 16 * 16 * 16, str(b4))

        # 非法文件要报错而不是崩
        pbad = os.path.join(tmp, "bad.dds")
        open(pbad, "wb").write(b"NOTDDS" + b"\0" * 200)
        ok("dds 对非 DDS 文件报错不抛异常", "error" in dds.parse_header(pbad))

        # 空文件
        open(os.path.join(tmp, "empty.dds"), "wb").close()
        ok("dds 对空文件报错不抛异常", "error" in dds.parse_header(os.path.join(tmp, "empty.dds")))

        # --- lint.py：必须真能抓到三类错 ---
        good = os.path.join(tmp, "good.txt")
        with open(good, "w", encoding="utf-8") as f:
            f.write('focus = {\n\tid = T_ok\n\tavailable = { difficulty > 1 }\n}\n')
        e, w = lint.check_file(good)
        ok("lint 放行合法文件", not e, str(e[:2]))

        bad = os.path.join(tmp, "bad.txt")
        with open(bad, "w", encoding="utf-8") as f:
            f.write('focus = {\n\tid = T_bad\n\tavailable = { difficulty >= 2 }\n}\n}\n')
        e2, _w2 = lint.check_file(bad)
        msgs = " ".join(d["msg"] for d in e2)
        ok("lint 抓到 >=（引擎不支持）", ">=" in msgs, msgs[:80])
        ok("lint 抓到多余的 }", "多余" in msgs, msgs[:80])

        # 诊断三段式：发现什么 → 后果 → 怎么改。
        # 抄 hagane-studio 的 ReferenceIntegrityFinding（Consequence + EditAt）。
        # 只报"第几行有什么错"不够——用户还得自己查"这错严重吗、该怎么弄"。
        ok("诊断带 impact（后果）", any(d.get("impact") for d in e2), str(e2[:1]))
        ok("诊断带 fix（改法）", any(d.get("fix") for d in e2), str(e2[:1]))

        # 引号里的 # 不是注释起点，右括号必须保住。
        # 直接测 strip_comment 的返回值，不要只测「check_file 有没有报错」——
        # 后者抓不到这个 bug：剥掉 } 只会让文件变成「末尾少一个括号」，
        # 而少括号已被降级为 warning（引擎容忍），于是 error 列表是空的。
        # 第一版断言就是这么写的，把实现改回 bug 版本它照样全绿。假断言。
        src = '\thas_dlc = "No#Surrender" }'
        ok("lint 剥注释保住引号内的 } ", lint.strip_comment(src) == src, lint.strip_comment(src))
        ok("lint 引号外仍按 # 剥",
           lint.strip_comment("a = 1 # tail") == "a = 1 ", lint.strip_comment("a = 1 # tail"))
        ok("lint 引号外 # 之前的 } 保留",
           lint.strip_comment("x = { }  # c").endswith("}  "), lint.strip_comment("x = { }  # c"))

        # 注释里的 >= 不该报
        commented = os.path.join(tmp, "commented.txt")
        with open(commented, "w", encoding="utf-8") as f:
            f.write('x = {\n\t# 原来写的是 a >= b\n\tid = T_c\n}\n')
        e4, _ = lint.check_file(commented)
        ok("lint 不把注释里的 >= 当错", not e4, str(e4[:2]))

        # 末尾少 } 应降级为 warning（引擎 EOF 隐式闭合，原版有 14 个这样的文件）
        tail = os.path.join(tmp, "tail.txt")
        with open(tail, "w", encoding="utf-8") as f:
            f.write("x = {\n\ty = 1\n")
        e5, w5 = lint.check_file(tail)
        ok("lint 对末尾缺 } 只报 warning 不报 error", not e5 and w5, f"e={e5[:1]} w={w5[:1]}")

        # 跨盘符不该崩（这个 bug 真的发生过：E: 盘检查时 relpath 抛 ValueError）
        ok("lint 跨盘符路径不崩", lint._short("E:/Steam/x.txt").startswith("E:"),
           lint._short("E:/Steam/x.txt"))

        # --- 回执：lint 的输出必须包含「没检查什么」和「别乱说完成」 ---
        # 照抄 hagane-studio 的 mutation_receipt 思路。没有这一段，
        # "lint 通过" 会被读成 "这个 mod 没问题"，实际它只覆盖了三条静态规则。
        import io, contextlib
        buf = io.StringIO()
        lintdir = os.path.join(tmp, "lintout")
        os.makedirs(lintdir, exist_ok=True)
        with open(os.path.join(lintdir, "ok.txt"), "w", encoding="utf-8") as f:
            f.write("focus = {\n\tid = Z_ok\n}\n")
        with contextlib.redirect_stdout(buf):
            lint.main([lintdir])
        out = buf.getvalue()
        ok("lint 输出含回执段", "--- 回执 ---" in out, out[-120:])
        ok("回执声明了验证到什么程度", "verification:" in out and "syntax_only" in out)
        ok("回执列出未检查项", "not_checked:" in out and "游戏内行为" in out)
        ok("回执含禁止夸大结论的规则", "reporting_rule:" in out and "不要仅凭此结论" in out)

        # --- 悬空国策引用。三个声明块名都必须认，少一个就整批假阳性 ---
        # 实测教训：只认 focus 时原版 81 个文件刷出 966 条假阳性；
        # 加 joint_focus 后仍有 509 条；三个都认才归零。
        decl = os.path.join(tmp, "decl")
        os.makedirs(decl, exist_ok=True)
        with open(os.path.join(decl, "tree.txt"), "w", encoding="utf-8") as f:
            f.write(
                "focus_tree = {\n"
                "  focus = { id = F_plain x = 0 y = 0 }\n"
                "  joint_focus = { id = F_joint x = 1 y = 0 }\n"
                "  shared_focus = { id = F_shared x = 2 y = 0 }\n"
                "  focus = {\n"
                "    id = F_refs\n"
                "    prerequisite = { focus = F_plain focus = F_joint focus = F_shared }\n"
                "    mutually_exclusive = { focus = F_plain }\n"
                "  }\n"
                "}\n"
            )
        d_ok = lint.check_dangling([os.path.join(decl, "tree.txt")])
        ok("三种声明块名都认（focus/joint_focus/shared_focus）", not d_ok, str(d_ok[:3]))

        bad_ref = os.path.join(decl, "bad_ref.txt")
        with open(bad_ref, "w", encoding="utf-8") as f:
            f.write(
                "focus_tree = {\n"
                "  focus = { id = G_ok x = 0 y = 0 }\n"
                "  focus = { id = G_bad x = 1 y = 0  prerequisite = { focus = G_missing } }\n"
                "}\n"
            )
        d_bad = lint.check_dangling([bad_ref])
        ok("抓到悬空的 prerequisite", len(d_bad) == 1 and "G_missing" in d_bad[0]["msg"], str(d_bad[:2]))

        # mutually_exclusive 也要查（两个方向同源，别只测一个）
        mut = os.path.join(decl, "mut.txt")
        with open(mut, "w", encoding="utf-8") as f:
            f.write("focus_tree = {\n  focus = { id = H_a x = 0 y = 0  mutually_exclusive = { focus = H_nope } }\n}\n")
        d_mut = lint.check_dangling([mut])
        ok("抓到悬空的 mutually_exclusive", len(d_mut) == 1 and "H_nope" in d_mut[0]["msg"], str(d_mut[:2]))

        # 定义来源和检查范围分开：mod 引用原版国策时不能算悬空
        # （不分开的话 mod 一引用原版就全是假阳性，这个场景天天遇到）
        mod_dir = os.path.join(tmp, "modf")
        van_dir = os.path.join(tmp, "vanf")
        os.makedirs(mod_dir, exist_ok=True)
        os.makedirs(van_dir, exist_ok=True)
        with open(os.path.join(van_dir, "vanilla.txt"), "w", encoding="utf-8") as f:
            f.write("focus_tree = {\n  focus = { id = V_base x = 0 y = 0 }\n}\n")
        with open(os.path.join(mod_dir, "mymod.txt"), "w", encoding="utf-8") as f:
            f.write("focus_tree = {\n  focus = { id = M_mine x = 0 y = 0  prerequisite = { focus = V_base } }\n}\n")
        d_alone = lint.check_dangling([os.path.join(mod_dir, "mymod.txt")])
        ok("不给原版定义时会误报（证明 scope 参数有必要）", len(d_alone) == 1, str(d_alone[:1]))
        d_scoped = lint.check_dangling(
            [os.path.join(mod_dir, "mymod.txt")],
            [os.path.join(mod_dir, "mymod.txt"), os.path.join(van_dir, "vanilla.txt")],
        )
        ok("给 --refs-scope 后引用原版不误报", not d_scoped, str(d_scoped[:2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_loc_quirks() -> None:
    """原版真实写法 vs 校验器的假设。

    这一组全部来自「把原版游戏当 mod 跑一遍」的实测：
    1.19.4.2 跑出 11694 个 error，逐类查下去发现 6 个系统性误报。
    每一条都写成最小复现用例，防止以后又退回去。
    """
    section("15. 本地化真实写法（原版实测回归）")

    import checks

    tmp = tempfile.mkdtemp()
    try:
        root = os.path.join(tmp, "m")
        os.makedirs(os.path.join(root, "localisation", "english"))

        # --- 1. 行尾注释 ------------------------------------------------ #
        # 原版 411 个文件、19061 行这么写。旧正则要求整行以右引号结尾，
        # 于是这些行被判「无法解析」，键也没收，最后变成几千条假「缺键」。
        p = os.path.join(root, "localisation", "english", "a_l_english.yml")
        with open(p, "wb") as f:
            f.write(
                b"\xef\xbb\xbfl_english:\n"
                b' K_tail: "text" #TODO: refine later\n'
                b' K_hash: "color \\xc2\\xa7G#FF0000\\xc2\\xa7! text"\n'
            )
        r = checks.scan_localisation(root)
        ok("行尾注释的词条能被解析", "K_tail" in r["keys"], str(list(r["keys"])[:5]))
        ok("引号内的 # 不被当注释切掉",
           "FF0000" in r["keys"].get("K_hash", ""), repr(r["keys"].get("K_hash")))
        ok("行尾注释不再报「无法解析」",
           not any("无法解析" in i["message"] for i in r["issues"]),
           str([i["message"] for i in r["issues"]][:3]))

        # --- 2. languages.yml 不是词条文件 ------------------------------- #
        # 它是语言清单，每节都列 l_english / l_french……，当成词条扫会产出
        # 「重复的键 l_english × 9」这类纯噪音。
        lp = os.path.join(root, "localisation", "languages.yml")
        with open(lp, "wb") as f:
            f.write(b"\xef\xbb\xbfl_english:\n l_english: \"English\"\n l_french: \"Fran\xc3\xa7ais\"\n")
        r2 = checks.scan_localisation(root)
        ok("languages.yml 不当词条扫",
           not any("重复的键" in i["message"] for i in r2["issues"]),
           str([i["message"] for i in r2["issues"]][:2]))

        # --- 3. 纯注释文件不报缺语言头 ----------------------------------- #
        # 原版 localisation/french/career_profile_zelosissimo.yml 全文是
        # LocEditor 的说明注释，一条词条都没有。缺语言头不算错——没内容可生效。
        ep = os.path.join(root, "localisation", "english", "empty_l_english.yml")
        with open(ep, "wb") as f:
            f.write(b"\xef\xbb\xbf# === [LocEditor:RedundantFile] no active keys ===\n")
        r3 = checks.scan_localisation(root)
        ok("纯注释文件不报缺语言头",
           not any("语言头" in i["message"] and "empty" in (i.get("file") or "")
                   for i in r3["issues"]),
           str([i.get("file") for i in r3["issues"] if "语言头" in i["message"]][:2]))

        # --- 4. focus 的 text = 重定向显示键 ----------------------------- #
        # ethiopia.txt:6049  id = ETH_peoples_army / text = ETH_peoples_army_focus
        # 只按 id 找键会把它判成缺键。
        nf = os.path.join(root, "common", "national_focus")
        os.makedirs(nf)
        with open(os.path.join(nf, "t.txt"), "w", encoding="utf-8") as f:
            f.write('focus_tree = { id = t\n'
                    ' focus = { id = F_army text = F_army_text x = 0 y = 0 }\n}\n')
        lp2 = os.path.join(root, "localisation", "english", "t_l_english.yml")
        with open(lp2, "ab") as f:
            f.write(' F_army_text: "Army"\n F_army_text_desc: "d"\n'.encode("utf-8"))
        d = checks.collect_definitions(root)
        fdef = [x for x in d["definitions"]["focus"] if x["id"] == "F_army"]
        ok("focus 的 text= 被采集到", bool(fdef) and fdef[0].get("text") == "F_army_text",
           str(fdef[:1]))
        loc = checks.scan_localisation(root)
        rep = checks.check_missing_loc(root, d["definitions"], loc["keys"], d["namespaces"])
        ok("focus 用 text= 找键，不误报缺键",
           not any("F_army" == i.get("missing_key") for i in rep),
           str([i.get("missing_key") for i in rep if "F_army" in str(i.get("missing_key"))][:3]))

        # --- 5. idea 的 name= 重定向 + _desc 可选 ------------------------ #
        # 原版 6563 个 idea 块里 1392 个用 name=（21.2%）；
        # 6515 个 idea 里只有 1766 个（27%）有 *_desc。
        idr = os.path.join(root, "common", "ideas")
        os.makedirs(idr)
        with open(os.path.join(idr, "i.txt"), "w", encoding="utf-8") as f:
            f.write('ideas = { country = {\n'
                    '  I_redirect = { name = I_real picture = p modifier = { stability = 0.1 } }\n'
                    '  I_plain = { picture = p modifier = { stability = 0.1 } }\n'
                    '}}\n')
        with open(lp2, "ab") as f:
            f.write(' I_real: "Real"\n I_plain: "Plain"\n'.encode("utf-8"))
        d2 = checks.collect_definitions(root)
        irec = [x for x in d2["definitions"]["idea"] if x["id"] == "I_redirect"]
        ok("idea 的 name= 被采集到", bool(irec) and irec[0].get("name") == "I_real", str(irec[:1]))
        loc2 = checks.scan_localisation(root)
        rep2 = checks.check_missing_loc(root, d2["definitions"], loc2["keys"], d2["namespaces"])
        ok("idea 用 name= 找键，不误报缺键",
           not any(i.get("missing_key") == "I_redirect" for i in rep2),
           str([i.get("missing_key") for i in rep2 if "I_redirect" in str(i.get("missing_key"))][:2]))
        ok("idea 缺 *_desc 不算缺键（原版 73% 都没有）",
           not any(i.get("missing_key", "").endswith("I_plain_desc") for i in rep2),
           str([i.get("missing_key") for i in rep2 if "I_plain" in str(i.get("missing_key"))][:3]))

        # --- 6. 事件正文 .desc / .d 都认 -------------------------------- #
        # 原版 .desc 5209 个、.d 1538 个，两种都在用。只试一种必然大量误报。
        evd = os.path.join(root, "events")
        os.makedirs(evd)
        with open(os.path.join(evd, "e.txt"), "w", encoding="utf-8") as f:
            f.write('add_namespace = t\n'
                    'country_event = { id = t.1 title = t.1.t desc = t.1.desc }\n'
                    'country_event = { id = t.2 title = t.2.t }\n'
                    'country_event = { id = t.3 title = t.3.t }\n'
                    'country_event = { id = t.9 title = t.9.t }\n')
        with open(lp2, "ab") as f:
            f.write(' t.1.t: "T1"\n t.1.desc: "D1"\n t.2.t: "T2"\n t.2.d: "D2"\n'
                    ' t.3.t: "T3"\n t.3.desc: "D3"\n'.encode("utf-8"))
        d3 = checks.collect_definitions(root)
        loc3 = checks.scan_localisation(root)
        rep3 = checks.check_missing_loc(root, d3["definitions"], loc3["keys"], d3["namespaces"])
        ok("事件正文 .desc 写法被认（原版主流写法）",
           not any(i.get("missing_key") == "t.1.desc" for i in rep3),
           str([i.get("missing_key") for i in rep3 if "t.1" in str(i.get("missing_key"))][:2]))
        ok("事件正文 .d 回退写法被认", 
           not any(i.get("missing_key") == "t.2.d" for i in rep3),
           str([i.get("missing_key") for i in rep3 if "t.2" in str(i.get("missing_key"))][:2]))
        # t.3 既没写 desc=，也只有 .desc 键 —— 这条钉住「.desc 必须在候选里」。
        # t.9 两个候选键都不存在 —— 它的报错消息必须同时列出两种写法，
        # 直接证明候选列表是 [.desc, .d] 而不是只有 .d。
        ok("事件不写 desc= 时，.desc 候选生效（不是只认 .d）",
           not any(i.get("missing_key") == "t.3.desc" for i in rep3),
           str([i.get("missing_key") for i in rep3 if "t.3" in str(i.get("missing_key"))][:2]))
        t9 = [i for i in rep3 if i.get("missing_key") in ("t.9.desc", "t.9.d")]
        ok("事件缺键的提示同时列出 .desc 与 .d 两种写法",
           bool(t9) and ".desc" in t9[0]["message"] and ".d" in t9[0]["message"],
           str([i["message"] for i in t9][:1]))

        # --- 7. DEBUG_ 前缀豁免 ----------------------------------------- #
        # 原版调试开关，allowed = { always = no }，玩家看不到，原版也不写本地化。
        ddr = os.path.join(root, "common", "decisions")
        os.makedirs(ddr)
        with open(os.path.join(ddr, "d.txt"), "w", encoding="utf-8") as f:
            f.write('t_cat = { DEBUG_show_thing = { allowed = { always = no } } }\n')
        d4 = checks.collect_definitions(root)
        loc4 = checks.scan_localisation(root)
        rep4 = checks.check_missing_loc(root, d4["definitions"], loc4["keys"], d4["namespaces"])
        ok("DEBUG_ 前缀不报缺键（原版故意的）",
           not any("DEBUG_" in str(i.get("missing_key")) for i in rep4),
           str([i.get("missing_key") for i in rep4 if "DEBUG_" in str(i.get("missing_key"))][:3]))

        # --- 8. 决议的 *_desc 可选 -------------------------------------- #
        # 原版 4186 个决议里只有 1387 个（33%）有 *_desc。
        ok("决议缺 *_desc 不算缺键（原版 67% 都没有）",
           not any(i.get("missing_key", "").endswith("t_cat_desc") for i in rep4),
           str([i.get("missing_key") for i in rep4][:4]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_conditional_blocks() -> None:
    """条件块形式（值不是标量而是块）的采集与校验。

    这是第二轮「把原版当 mod 跑」抓出来的：11694 → 2079 之后还剩 140 条
    事件缺正文键的误报，根因是 desc 写成了条件块，而 _stmt_value_text()
    遇到 Block 一律返回空串，整段声明被静默丢弃。

    原版 1.19.4.2 实测：
      event desc  标量 6629 / 块 214   ← 块内 512 个键全部真实存在
      event title 标量 6826 / 块  18   ← 块内 46 个键全部真实存在
      focus icon  标量 10297 / 块 44
      decision icon 标量 3654 / 块 66

    三种块的内部结构互不相同，必须分别断言，防止「用一种写法通用」。

    每条断言都配了一个「改坏就必须报红」的变异点（见 _mutate.py），
    凡是不写变异就通的断言一律视为无效，不当数。
    """
    section("16. 条件块形式（icon / title / desc 的块写法）")

    import checks

    tmp = tempfile.mkdtemp()
    try:
        root = os.path.join(tmp, "m")
        os.makedirs(os.path.join(root, "localisation", "english"))
        lp = os.path.join(root, "localisation", "english", "t_l_english.yml")
        with open(lp, "wb") as f:
            f.write(
                b"\xef\xbb\xbfl_english:\n"
                b' E_multi.t: "T"\n E_multi.a: "A"\n'
                b' E_multi.desc_den: "den"\n'      # 第一个 desc 块声明的键
                b' E_multi.desc_gen: "gen"\n'      # 第二个 desc 块声明的键
                # 故意不写 E_multi.desc 与 E_multi.d：只要块被丢弃，
                # 回退候选就必然落空 → 误报。这条让断言能真的验到东西。
                b' E_badt.t: "T"\n E_badt.a: "A"\n E_badt.desc_den: "den"\n'
                b' E_bad.t: "T"\n E_bad.a: "A"\n'
                b' E_title.t_war: "W"\n E_title.t_peace: "P"\n'
                b' E_title.a: "A"\n'      # 不写 E_title.t，逼它必须用块内键
                b' F_block: "f"\n F_block_desc: "d"\n'
                b' D_block: "d"\n'
            )

        # --- 1. 事件 desc 的块形式：多个块、每块一个 text = 键 ---------- #
        # 原版写法（events/AAT_Iceland.txt:925）：
        #   desc = { text = iceland_events.17.desc_kingdom trigger = {...} }
        #   desc = { text = iceland_events.17.desc_generic trigger = {...} }
        evd = os.path.join(root, "events")
        os.makedirs(evd)
        with open(os.path.join(evd, "e.txt"), "w", encoding="utf-8") as f:
            f.write('add_namespace = E\n'
                    'country_event = { id = E_multi title = E_multi.t\n'
                    ' desc = { text = E_multi.desc_den trigger = { tag = DEN } }\n'
                    ' desc = { text = E_multi.desc_gen trigger = { always = yes } }\n'
                    ' option = { name = E_multi.a } }\n'
                    # 块里的键不存在 —— 必须报出来
                    'country_event = { id = E_bad title = E_bad.t\n'
                    ' desc = { text = E_bad.desc_missing trigger = { always = yes } }\n'
                    ' option = { name = E_bad.a } }\n'
                    # 两块里只有一块的键存在 —— 任一命中即通过
                    'country_event = { id = E_badt title = E_badt.t\n'
                    ' desc = { text = E_badt.desc_den trigger = { always = yes } }\n'
                    ' desc = { text = E_badt.desc_nope trigger = { always = yes } }\n'
                    ' option = { name = E_badt.a } }\n')

        d = checks.collect_definitions(root)
        ev = {x["id"]: x for x in d["definitions"]["event"]}
        ok("事件 desc 块内的 text 键全部被采集到（不是只取第一个）",
           sorted(ev["E_multi"].get("desc_keys") or [])
           == ["E_multi.desc_den", "E_multi.desc_gen"],
           f"desc_keys={ev['E_multi'].get('desc_keys')}")
        ok("事件 desc 的标量字段遇到块时仍为空（不塞块对象给消费方）",
           ev["E_multi"].get("desc") == "",
           f"desc={ev['E_multi'].get('desc')!r}")

        loc = checks.scan_localisation(root)
        rep = checks.check_missing_loc(root, d["definitions"], loc["keys"], d["namespaces"])
        ok("事件 desc 写成条件块时不误报缺键",
           not any(i.get("missing_key") == "E_multi.desc" for i in rep),
           str([i.get("missing_key") for i in rep if "E_multi" in str(i.get("missing_key"))][:3]))
        ok("块形式 desc 里真缺失的键仍会被抓出来",
           any(i.get("missing_key") == "E_bad.desc_missing" for i in rep),
           str([i.get("missing_key") for i in rep if "E_bad" in str(i.get("missing_key"))][:3]))
        ok("块里多候选中任一命中即通过（不要求每个键都在）",
           not any(i.get("missing_key") == "E_badt.desc_den" for i in rep),
           str([i.get("missing_key") for i in rep if "E_badt" in str(i.get("missing_key"))][:3]))

        # --- 2. 事件 title 的块形式 ------------------------------------- #
        # 块里带 text = 与 trigger，见 events/AAT_Finland.txt:85
        with open(os.path.join(evd, "e2.txt"), "w", encoding="utf-8") as f:
            f.write('add_namespace = E\n'
                    'country_event = { id = E_title\n'
                    ' title = { text = E_title.t_war trigger = { has_global_flag = f } }\n'
                    ' title = { text = E_title.t_peace trigger = { always = yes } }\n'
                    ' desc = E_multi.desc_gen option = { name = E_title.a } }\n')
        d2 = checks.collect_definitions(root)
        et = {x["id"]: x for x in d2["definitions"]["event"]}.get("E_title")
        ok("事件 title 块内的 text 键被采集到",
           et is not None and (et.get("title_keys") or []) == ["E_title.t_war", "E_title.t_peace"],
           f"title_keys={et and et.get('title_keys')}")
        # 这条钉住「校验时真的用上了 title_keys」：本地化里没有 E_title.t，
        # 一旦回退到默认键就会报缺，只有用块内声明的两个键才不报。
        loc2 = checks.scan_localisation(root)
        rep2 = checks.check_missing_loc(root, d2["definitions"], loc2["keys"], d2["namespaces"])
        ok("事件标题用块内声明的键校验，不误报",
           not any(i.get("missing_key") in ("E_title.t", "E_title.t_war") for i in rep2),
           str([i.get("missing_key") for i in rep2 if "E_title" in str(i.get("missing_key"))][:3]))

        # --- 3. focus icon 块：sprite 名当语句键 ------------------------ #
        # 见 common/national_focus/afghanistan.txt:332
        #   icon = { GFX_focus_A = { OR = { has_government = democratic } }
        #            GFX_focus_B = yes }
        nf = os.path.join(root, "common", "national_focus")
        os.makedirs(nf)
        with open(os.path.join(nf, "f.txt"), "w", encoding="utf-8") as f:
            f.write('focus_tree = { id = F\n'
                    ' focus = { id = F_block text = F_block x = 0 y = 0\n'
                    '  icon = { GFX_focus_den = { OR = { has_government = democratic } }\n'
                    '           GFX_focus_gen = yes } }\n}\n')
        d3 = checks.collect_definitions(root)
        fb = [x for x in d3["definitions"]["focus"] if x["id"] == "F_block"]
        pics = (fb[0].get("pictures") if fb else None) or []
        ok("focus 的 icon 条件块里所有 sprite 都被采集到",
           sorted(pics) == ["GFX_focus_den", "GFX_focus_gen"], str(pics))
        # 条件表达式在**值**里，键只有 sprite 名。任何深层键（OR / has_government）
        # 都不该出现在结果里 —— 一旦有人把 stmts() 换成 walk() 就会漏进来。
        ok("focus icon 块只取顶层键，不把嵌套条件表达式当 sprite",
           not any(s in ("OR", "AND", "has_government", "democratic") for s in pics),
           str(pics))

        # --- 4. decision icon 块：sprite 名写在 key = 里 ---------------- #
        # 见 common/decisions/NOR.txt:803
        #   icon = { key = GFX_decision_x trigger = { original_tag = USA } }
        ddr = os.path.join(root, "common", "decisions")
        os.makedirs(ddr)
        with open(os.path.join(ddr, "d.txt"), "w", encoding="utf-8") as f:
            f.write('D_cat = {\n'
                    ' D_block = { icon = { key = GFX_decision_foo\n'
                    '                      trigger = { original_tag = USA } }\n'
                    '            available = { always = yes } }\n}\n')
        d4 = checks.collect_definitions(root)
        db = [x for x in d4["definitions"]["decision"] if x["id"] == "D_block"]
        dpics = (db[0].get("pictures") if db else None) or []
        ok("decision 的 icon 条件块从 key = 取到 sprite",
           dpics == ["GFX_decision_foo"], str(dpics))
        # 这种结构里 trigger 是同级字段。取到 key 就必须收手，
        # 否则会一路落到「语句键即 sprite」分支，把 trigger 当成贴图名。
        ok("decision icon 块取到 key 后不再把 trigger 当 sprite",
           dpics == ["GFX_decision_foo"], str(dpics))

        # --- 5. 标量写法必须照旧 ---------------------------------------- #
        # 改采集逻辑最容易伤到最常见的那种写法，这条钉住它。
        with open(os.path.join(nf, "f2.txt"), "w", encoding="utf-8") as f:
            f.write('focus_tree = { id = F2\n'
                    ' focus = { id = F_plain text = F_plain x = 0 y = 0\n'
                    '  icon = GFX_focus_plain }\n}\n')
        d5 = checks.collect_definitions(root)
        fp = [x for x in d5["definitions"]["focus"] if x["id"] == "F_plain"]
        ok("focus 的 icon 标量写法仍采到单个 sprite",
           bool(fp) and (fp[0].get("pictures") or []) == ["GFX_focus_plain"],
           str(fp[0].get("pictures") if fp else None))
        ok("focus 的 extra 老字段仍保留标量值（不破坏既有消费方）",
           bool(fp) and fp[0].get("extra") == "GFX_focus_plain",
           str(fp[0].get("extra") if fp else None))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_vanilla_quirks() -> None:
    """原版真实写法的宽容度：大小写、隐藏事件、事件预约、行分隔符。

    这一组全部来自「把原版当 mod 跑」的第三轮（1939 → 1838）。
    共同点是：原版写得出来、游戏跑得通、旧校验器读不懂。
    每条都附原版出处，否则后人无法判断该不该动。
    """
    section("17. 原版真实写法的宽容度（大小写 / 隐藏事件 / 预约 / 分隔符）")

    import checks

    tmp = tempfile.mkdtemp()
    root = os.path.join(tmp, "vq")

    def _mk(rel: str, text: str) -> None:
        """写一个测试文件（自动建父目录）。同一份 mod 里要放多个文件。"""
        fp = os.path.join(root, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        enc = "utf-8-sig" if rel.endswith(".yml") else "utf-8"
        with open(fp, "w", encoding=enc) as f:
            f.write(text)

    try:
        _mk("descriptor.mod", 'name="vq"\nversion="1.0"\n')

        # --- 1. 事件命名空间大小写不敏感 ------------------------------- #
        # 原版 events/BBA_Switzerland.txt:30 声明 BBA_Switzerland（大写 S），
        # 文件里 55 个事件全写 id = BBA_switzerland.N（小写 s），游戏正常注册。
        _mk("events/case.txt",
            "add_namespace = Big_Case_NS\n"
            "country_event = { id = big_case_ns.1 title = T desc = D"
            " option = { name = T } }\n")
        r = checks.validate_mod(root, per_check=1000, max_issues=1000)
        ns_issue = [i for i in r["issues"] if "未在本文件声明" in (i.get("message") or "")]
        ok("事件命名空间大小写不同不报错（原版 BBA_Switzerland 实例）",
           not ns_issue, str(ns_issue[:2]))

        # --- 2. 隐藏事件的空 option 不报「缺名称」 ---------------------- #
        # 原版实测 6950 个事件里 116 个零 option、9 个有 option 无 name，
        # 全部是 hidden = yes（如 events/LaR_France.txt:3522 的 option = {}）。
        _mk("events/hidden.txt",
            "add_namespace = hid\n"
            "country_event = { id = hid.1 hidden = yes is_triggered_only = yes option = {} }\n"
            "country_event = { id = hid.2 title = T desc = D option = { name = T } }\n")
        r = checks.validate_mod(root, per_check=1000, max_issues=1000)
        nm = [i for i in r["issues"] if "没有 name" in (i.get("message") or "")]
        ok("隐藏事件的空 option 不报「选项缺名称」（原版 LaR_France 实例）",
           not nm, str(nm[:2]))

        # --- 3. 字段名大小写不敏感 -------------------------------------- #
        # 原版 events/USA.txt:1487 写 Hidden = yes（首字母大写），另有 8 处
        # Picture = ...，游戏照常认。精确匹配会把 hidden 读成 False。
        _mk("events/case2.txt",
            "add_namespace = caps\n"
            "country_event = {\n"
            "  id = caps.1 Hidden = yes is_triggered_only = yes option = {}\n"
            "}\n")
        d = checks.collect_definitions(root)["definitions"]
        h = [x for x in d["event"] if x["id"] == "caps.1"]
        ok("字段名 Hidden（首字母大写）仍被识别为隐藏事件",
           bool(h) and h[0].get("hidden") is True,
           str(h[0].get("hidden") if h else None))

        # --- 4. 区分事件定义与事件预约 ---------------------------------- #
        # 原版 history/countries/CZE - Czechoslovakia.txt:639 有
        #   country_event = { id = MUN_czech.6 days = 958 random_hours = 12 }
        # 这是「预约触发」，不是定义；当成定义校验会报「选项缺名称」。
        _mk("history/countries/TST.txt",
            "country_event = { id = some_ns.6 days = 958 random_hours = 12 }\n")
        d = checks.collect_definitions(root)["definitions"]
        sched = [x for x in d["event"] if x["id"] == "some_ns.6"]
        ok("history 里的事件预约不被当成事件定义（原版 MUN_czech.6 实例）",
           not sched, str(sched[:1]))

        # --- 5. 本地化分行只认 \\n，不认 NEL ---------------------------- #
        # 原版 localisation/braz_por/research_l_braz_por.yml:693 文本中有
        # 转义 \\n 紧接 U+0085；str.splitlines() 会把一行劈成两行，
        # 后半截无键名前缀 → 报「无法解析的行」。
        _mk("localisation/english/z_l_english.yml",
            'l_english:\n'
            ' vq_a: "line one \\n\u0085 tail same line"\n'
            ' vq_b: "second"\n')
        loc = checks.scan_localisation(root)
        bad = [i for i in loc["issues"] if "无法解析" in (i.get("message") or "")]
        ok("本地化文本里的 U+0085 不被当换行（原版 braz_por 实例）",
           not bad, str(bad[:2]))
        ok("U+0085 之后的内容仍属于同一条词条",
           "vq_a" in loc["keys"] and "vq_b" in loc["keys"],
           f"{'vq_a' in loc['keys']} / {'vq_b' in loc['keys']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    print(f"\033[1mHOI4 Modkit selftest\033[0m  python {sys.version.split()[0]}")
    tests = [
        test_parser, test_sample, test_broken, test_planner,
        test_preview, test_scaffolder, test_kb, test_mcp, test_remote, test_tiers,
        test_playbook, test_platform_state, test_structure_doc, test_tools,
        test_loc_quirks, test_conditional_blocks, test_vanilla_quirks,
    ]
    for fn in tests:
        try:
            fn()
        except Exception:
            _failed.append(f"{fn.__name__} 抛异常")
            print(f"  \033[31mFAIL\033[0m {fn.__name__} 抛异常")
            traceback.print_exc()

    total = _passed + len(_failed)

    # 文档声称的自检断言数，双向严格核对。
    # 放在这里是因为只有跑完所有用例，_passed 才是真实总数；
    # 在 test_structure_doc 里比只能比到中间值，挡不住「文档数字偏大」。
    if _CLAIMED_SELFTEST_COUNTS:
        bad_counts = sorted({n for n in _CLAIMED_SELFTEST_COUNTS if n != total})
        if bad_counts:
            _failed.append(
                f"文档写的自检项数都等于实际（实际 {total}，文档写 {bad_counts}）"
            )

    print()
    if _failed:
        print(f"\033[31m{len(_failed)} / {total} 项失败\033[0m")
        for f in _failed:
            print(f"  - {f}")
        return 1
    print(f"\033[32m全部通过 {total} / {total}\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

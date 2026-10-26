#!/usr/bin/env python3
"""新建一个可运行的 HOI4 Mod 骨架（1.19.3）。

生成：
  descriptor.mod、同级 <名字>.mod、README.md
  localisation/{english,simp_chinese}（UTF-8 BOM）
  common/ideas/、events/
  可选：common/national_focus/ 一棵国策树（--focus）

生成后自动跑一次静态校验（hoi4_lint.py，若同目录存在）。

用法：
  python new_mod.py D:/mods/MyMod --name "My Mod" --prefix MY --tag LUX
  python new_mod.py D:/mods/MyMod --focus --game "E:/Steam/steamapps/common/Hearts of Iron IV"
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
try:
    from _paths import find_game_dir
except Exception:  # 单独拷贝本文件时退化
    find_game_dir = None


def w(path: Path, text: str, bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)


def build(args) -> Path:
    prefix = args.prefix
    ns = prefix.lower()
    tag = args.tag
    root = Path(args.dir).resolve()
    name = args.name or root.name

    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(f"目录已存在且非空：{root}（加 --force 覆盖）")

    w(root / "descriptor.mod", f'''name="{name}"
supported_version="1.19.*"
tags={{
	"Gameplay"
}}
''')
    w(root.parent / f"{root.name}.mod", f'''name="{name}"
supported_version="1.19.*"
tags={{
	"Gameplay"
}}
path="{root.as_posix()}"
''')
    if any(ord(c) > 127 for c in str(root)):
        print("[warn] 目标路径含非 ASCII 字符：启动器对 path 兼容性差，建议换到纯 ASCII 路径或用 install_mod.py 复制安装。")

    focus_block = ""
    focus_loc_en = ""
    focus_loc_zh = ""
    if args.focus:
        focus_block = f'''
	focus = {{
		id = {prefix}_first_focus
		icon = GFX_focus_generic_industry_investment
		x = 0
		y = 0
		cost = 10
		search_filters = {{ FOCUS_FILTER_INDUSTRY }}
		completion_reward = {{
			add_ideas = {prefix}_idea_one
			country_event = {{ id = {ns}.1 days = 1 }}
		}}
	}}
'''
        focus_loc_en = f" {prefix}_first_focus:0 \"First Focus\"\n {prefix}_first_focus_desc:0 \"Description of the first focus.\"\n"
        focus_loc_zh = f" {prefix}_first_focus:0 \"第一个国策\"\n {prefix}_first_focus_desc:0 \"第一个国策的描述。\"\n"

    w(root / "common/ideas" / f"{prefix}_ideas.txt", f'''# {prefix}_ideas.txt —— 国家精神（Idea）
# 文件放 common/ideas/ 下任意 *.txt；分类 country 定义在 common/idea_tags/00_idea.txt。
ideas = {{
	country = {{
		{prefix}_idea_one = {{
			allowed = {{ original_tag = {tag} }}
			allowed_civil_war = {{ always = yes }}
			removal_cost = -1
			modifier = {{
				stability_factor = 0.02
			}}
		}}
	}}
}}
''')

    w(root / "events" / f"{prefix}_events.txt", f'''# {prefix}_events.txt —— 事件
# namespace 必须先 add_namespace；事件 id 为 <namespace>.<数字>。
add_namespace = {ns}

country_event = {{
	id = {ns}.1
	title = {ns}.1.t
	desc = {ns}.1.d
	picture = GFX_report_event_generic_rally2
	is_triggered_only = yes
	option = {{
		name = {ns}.1.a
		add_political_power = 25
	}}
}}
''')

    if args.focus:
        w(root / "common/national_focus" / f"{prefix}_focus.txt", f'''# {prefix}_focus.txt —— 国策树
# 注意：1.19 每个国家同一时间只有一棵激活国策树（country 块打分，取最高分）。
# 本树给 {tag} +10 分；若 {tag} 已有专属树，需要覆盖原树或改用 load_focus_tree，
# 否则可能被原版树压掉/顶掉。详见技能 references/cheatsheet.md §4。
focus_tree = {{
	id = {prefix}_tree

	country = {{
		factor = 0
		modifier = {{
			add = 10
			original_tag = {tag}
		}}
	}}

	initial_show_position = {{ x = 0 y = 0 }}
	default = no
{focus_block}}}
''')

    w(root / "localisation/english" / f"{prefix}_l_english.yml", f'''l_english:
 {prefix}_idea_one:0 "National Spirit"
 {prefix}_idea_one_desc:0 "A national spirit added by this mod."
 {ns}.1.t:0 "A New Beginning"
 {ns}.1.d:0 "This event was added by the mod skeleton. Replace this text."
 {ns}.1.a:0 "Proceed."
{focus_loc_en}''', bom=True)

    w(root / "localisation/simp_chinese" / f"{prefix}_l_simp_chinese.yml", f'''l_simp_chinese:
 {prefix}_idea_one:0 "国家精神"
 {prefix}_idea_one_desc:0 "本 Mod 添加的国家精神。"
 {ns}.1.t:0 "新的开始"
 {ns}.1.d:0 "这个事件由 Mod 骨架生成，请替换文本。"
 {ns}.1.a:0 "继续。"
{focus_loc_zh}''', bom=True)

    w(root / "README.md", f'''# {name}

由 `hoi4-modding` 技能骨架生成（HOI4 1.19.3）。

- 目标国家：`{tag}`
- ID 前缀：`{prefix}`，事件命名空间：`{ns}`
- 已生成：理念 1 个、事件 1 个{("、国策树 1 棵" if args.focus else "")}、中英本地化

## 安装 / 测试

```bash
python scripts/hoi4_lint.py "{root.as_posix()}"
python scripts/install_mod.py "{root.as_posix()}" --yes --enable
```

再启动游戏 → 新开 `{tag}` 档 → 控制台 `event {ns}.1` 验证事件。
{("> 注意：若 `" + tag + "` 已有专属国策树，本树可能不生效；见技能 references/cheatsheet.md §4。") if args.focus else ""}
''')

    return root


def lint(root: Path, game: Path) -> None:
    try:
        sys.path.insert(0, str(HERE))
        import hoi4_lint  # noqa: E402
    except Exception as exc:  # noqa: BLE001
        print(f"[skip] 未找到 hoi4_lint.py，跳过校验：{exc}")
        return
    vanilla = None
    if game.exists():
        try:
            vanilla = hoi4_lint.load_vanilla_index(game)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 原版索引构建失败，仅做离线校验：{exc}")
    report = hoi4_lint.Linter(root, game, vanilla).run()
    data = report.summary()
    print(f"[lint] {root.name}: errors={data['errors']} warnings={data['warnings']}")
    for issue in data["issues"][:20]:
        print(f"  {issue['severity']:<7} {issue['code']:<28} {issue['path']}:{issue['line']} {issue['message']}")


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="新建 HOI4 Mod 骨架")
    ap.add_argument("dir", help="Mod 目录（不存在则创建）")
    ap.add_argument("--name", default="", help="显示名（默认用目录名）")
    ap.add_argument("--prefix", default="", help="ID 前缀，2-5 个大写字母（默认取名字首字母）")
    ap.add_argument("--tag", default="LUX", help="目标国家 tag（默认 LUX，它没有专属国策树）")
    ap.add_argument("--focus", action="store_true", help="同时生成一棵国策树")
    ap.add_argument("--force", action="store_true", help="目录非空时覆盖")
    ap.add_argument(
        "--game",
        default=str(
            (find_game_dir() if find_game_dir else None)
            or os.environ.get("HOI4_GAME")
            or r"E:\Steam\steamapps\common\Hearts of Iron IV"
        ),
    )
    ap.add_argument("--no-lint", action="store_true", help="生成后不跑校验")
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[A-Z]{3}", args.tag):
        raise SystemExit("--tag 必须是 3 个大写字母，如 LUX / GER / SWE")
    if not args.prefix:
        base = args.name or Path(args.dir).name
        args.prefix = "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", base)).upper()[:5] or "NS"
        if len(args.prefix) < 2:
            args.prefix = (args.prefix + "X")[:2]
    if not re.fullmatch(r"[A-Z][A-Z0-9]{1,4}", args.prefix):
        raise SystemExit("--prefix 必须是 2-5 个字母/数字、以字母开头，如 MY / HHO / NS1")

    root = build(args)
    print(f"[ok] 已生成 {root}")
    print(f"     事件：event {args.prefix.lower()}.1；理念：{args.prefix}_idea_one")
    if not args.no_lint:
        lint(root, Path(args.game))
    print("\n下一步：")
    print(f"  1) 改内容：{root / 'common'}")
    print(f"  2) 补本地化：{root / 'localisation'}")
    print(f"  3) 校验：python {HERE / 'hoi4_lint.py'} \"{root}\"")
    print(f"  4) 安装：python {HERE / 'install_mod.py'} \"{root}\" --yes --enable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

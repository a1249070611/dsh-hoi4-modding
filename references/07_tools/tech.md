---
title: "tech：科技树 folder / 页签 / 小图标 / 标签可用性"
domain: 07_tools
scope: technology_folders 注册、页面/页签/网格/科技是否接上，technology_tags 的 has_country_flag 修正，科技小图标 sprite 尺寸
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py tech audit
  - tools/cli.py tech available
  - tools/cli.py tech sprites
  - tools/tech_tree_audit.py / tech_folder_available.py / item_sprite_check.py
---

# `tech`：科技树相关三件套

```bash
python tools/cli.py tech audit <mod>        # folder / 页面 / 页签 / 网格 / 科技 是否闭合
python tools/cli.py tech available <mod> --check            # 只报告要改的行
python tools/cli.py tech available <mod> --apply --yes      # 改（先备份）
python tools/cli.py tech available <mod> --revert --yes     # 从备份恢复
python tools/cli.py tech sprites <mod>      # 科技小图标 sprite / 模板尺寸
```

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## `tech audit`：科技树挂载

对着这三处比：

- `common/technology_tags/**.txt`：`technology_folders = { ... }` 注册的 folder；
- `common/technologies/**.txt`：每个 tech 的 `folder = { name = X }`；
- `interface/countrytechtreeview.gui`：`containerWindowType`（页面）、`buttonType`（页签）、`techtree_*_item` 模板、网格。

会报：folder 没注册进 `technology_folders`、folder 找不到页面、找不到页签、找不到 item 模板、找不到网格、folder 里没有科技、孤儿 folder（注册了但没有任何科技）。

- rule ID：`legacy.tech.audit`（旧工具输出逐行转换，message 里是具体 folder 与问题）。
- 退出码：`0` 全部闭合、`1` 发现问题、`2` 找不到 Mod。

**典型症状**：科技树页面有方框但拉不出线、点不开 → 先看这里报的「无页签 / 无网格」。

## `tech available`：`has_country_flag` → `original_tag`

`technology_folders` 里用 `has_country_flag = GER` 这种写法在部分场景不生效，应写成 `original_tag = GER`（或反过来按你的设计）。

```bash
python tools/cli.py tech available <mod> --check          # 列出将改的 (flag, tag) 行
python tools/cli.py tech available <mod> --apply --yes    # 写回（自动备份）
python tools/cli.py tech available <mod> --revert --yes   # 恢复上一份备份
```

- 不带 `--check/--apply/--revert` 视为用法错误（退出 `2`）。
- `--apply`/`--revert` 没有 `--yes`（也没有 `--dry-run`）时直接 **退出 `3`**，不会写文件。
- `--dry-run` 等价于 `--check`。
- 备份位置：`%LOCALAPPDATA%\hoi4mod\cache\backups\techfolder\<mod名>\<时间戳>\<原路径>`（旧版本留在 Mod 内的 `.dsh_techfolder_backup` 只读兜底）。
- 写回保留原文件 BOM；会打印 `命中 N 处 flag，未知 M 处`（未知 = 形如 `has_country_flag = some_flag` 但不是国家 tag）。

## `tech sprites`：小图标与模板尺寸

检查科技小框（`small_item`）用的 `GFX_*` sprite 与模板 `size`：

- `small_item` 缺 sprite / sprite 指向的贴图不存在 → error；
- 模板尺寸与贴图差超过 32px → 提示；
- `small_item` 模板宽 > 100 → 提示换 72×72 的 `tech_doctrine_*_item_bg.dds`。
- rule ID：`legacy.tech.sprites`。

## `--json`

三个命令结构一致：

```json
{"ok": false, "exit_code": 1, "command": "tech audit",
 "problems": [{"code": "legacy.tech.audit", "severity": "error",
               "message": "folder my_folder：无页签（countrytechtreeview.gui 里没有对应 buttonType）"}],
 "summary": {"mod": "...", "exit": 1, "lines": 12, "log": ["..."], "errors": 1, "warnings": 0}}
```

旧工具驱动的子命令统一用 `legacy.<group>.<action>` 作为 code，severity 由输出关键字（`[!]`/错误/失败/不存在/未找到/not found…）判定；稳定细粒度规则见 `lint` 与 `loc audit`。

## 已知限制

- `tech audit` 只做结构闭合，不校验 `available`/`path` 的语义（那要靠 `lint` 的 scope 规则与游戏实测）。
- `tech available` 只改 `technology_tags/**.txt` 里的 `has_country_flag`，不动其它文件。
- 科技树 GUI 的连线段（`gridboxtype` 的 `position`）不校验像素重叠，需要在游戏里看。

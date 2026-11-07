---
title: "init / parse / errorlog / reference / paths：其余子命令"
domain: 07_tools
scope: 生成 Mod 骨架、解析 PDX 脚本、error.log 分类、生成速查表、打印路径探测结果
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py init / parse / errorlog / reference build / paths
  - tools/new_mod.py / pdx_parser.py / errorlog_triage.py / build_reference.py / _paths.py
---

# 其余子命令

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## `init`：生成可加载的最小 Mod

```bash
python tools/cli.py init <目录> --tag LUX --name "Luxembourg Expanded" --prefix lx
python tools/cli.py init <目录> --tag LUX --focus      # 额外生成一个国策树骨架
```

生成：`descriptor.mod`（`supported_version="1.19.*"`）、同级 `<dir>.mod`（`path=` 指向生成目录）、`common/ideas/<PREFIX>_ideas.txt`（1 个理念）、`events/<prefix>_events.txt`（namespace + 1 个事件）、`localisation/english|simp_chinese` 各 1 个 yml（带 BOM）、`README.md`；可选 `common/national_focus/<prefix>_focus.txt`。

- `--tag` 必须是 3 个大写字母（`[A-Z]{3}`）；`--prefix` 自动推导 `[A-Z][A-Z0-9]{1,4}`。
- 生成后自动跑一次 lint（没有游戏则跳过并提示）。
- `--force` 覆盖已存在目录；`--dry-run` **不支持**（会直接退出 `3`，避免生成一半）。
- 退出码：`0` 成功、`2` 参数/目录问题、`3` 被拒。

## `parse`：PDX 脚本解析（调试用）

```bash
python tools/cli.py parse common/ideas/00_ideas.txt        # 打印顶层条目数/错误行/前 40 个 key
python tools/cli.py parse <file> --tree                    # 额外输出前 3 层结构
python tools/cli.py parse <file> --json                    # 结构化
```

- 文件不存在 → `parse.missing`，退出 `2`；读失败 `parse.io`；语法问题 `parse.error`（仍输出可解析部分）。
- JSON：`{"ok": bool, "exit_code": 0|1|2, "command": "parse", "problems": [...], "summary": {"files": [{"path": ..., "entries": N, "errors": [...], "top_keys": [...]}]}}`。
- 这是调工具时的调试入口，不是通用转换器；批量转换用 `hoi4-toolkit` 里的外部工具。

## `errorlog`：error.log 分类排错

```bash
python tools/cli.py errorlog                                  # 默认读玩家目录 logs/error.log
python tools/cli.py errorlog "D:/logs/error.log"
python tools/cli.py errorlog --keyword tech                   # 只看含关键字的行
python tools/cli.py errorlog --show 10 --json
```

- 分类：科技树-网格 / 科技树-连线 / 科技树-坐标 / 科技树-其它 / 贴图缺失 / scope 错误 / 未知 effect/trigger/modifier / 括号 token / 动态 token(OOS) / 本地化缺失。
- 输出：日志行数/大小、首末行、各类计数与样本；`tech_total == 0` 时给判语「页面有方框但无连线 → 查 `technology_folders` 是否用 `has_country_flag`」。
- **退出码按新约定**：默认 `0`；只有解析到 error 级别以外的问题时才变化（旧脚本里的 `return 0` 行为保留在 `scripts/errorlog_triage.py` 直调时）。
- 这是「先分类再手工修」的入口，具体修法见 `06_workflow/debugging.md`。

## `reference build`：生成 effects/triggers/modifiers/console 速查

```bash
python tools/cli.py reference build --game "<游戏目录>"
python tools/cli.py reference build --game "..." --out "<输出目录>"
```

从游戏 `documentation/*.md` 解析，生成 `effects.json`、`triggers.json`、`modifiers.json`、`console.json` + 4 个 `CHEATSHEET_*.md` + `index.md`，并打印各条目数（1.19.4 实测：effects 553 / triggers 596 / modifiers 764 / console 385 commands + 44 tweakables）。

- 默认输出到技能包 `skills/hoi4-modding/reference/`；开发时建议 `--out` 到临时目录。
- `--dry-run` 不支持（会重写 reference/）→ 退出 `3`。
- 缺 `documentation/` 目录时退出 `2` 并提示。

## `paths`：打印路径探测结果

```bash
python tools/cli.py paths
python tools/cli.py paths --json
```

输出 `_paths.explain()`：game、game_probes（探测过程）、user_dir、launcher_settings、steam_libraries、cache_dir、version、mod_dir。排「为什么工具找不到游戏/Mod」时比 `doctor` 更直接。

- 退出码：`0` 找到游戏、`1` 没找到（其它字段照常打印）、`2` 用法错误。

## 统一的 `--json` 约定

这五个命令都遵循 `{ok, exit_code, command, problems[], summary{}}`，`summary` 里至少 `errors`/`warnings`（`paths` 例外，直接输出探测字典）。细节见 [cli-conventions.md](cli-conventions.md)。

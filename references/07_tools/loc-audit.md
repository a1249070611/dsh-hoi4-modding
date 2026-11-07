---
title: "loc audit：本地化引用 vs 定义"
domain: 07_tools
scope: 找出「脚本引用了但没定义」「定义了但没人用」「重复/BOM/编码/语言缺失」的 loc key
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py loc audit
  - tools/loc_audit.py
  - 实测：hist_tech_trees、BlackICE、TNO
---

# `loc audit`：本地化引用 vs 定义

检查两件事：脚本里**引用**的 loc key 在 `localisation/**/*.yml` 里有没有定义；定义本身有没有 BOM / 编码 / 重复 / 空值 / 大小写问题。

```bash
python tools/cli.py loc audit <mod>                # 默认同时对照原版（可继承的 key 不算缺失）
python tools/cli.py loc audit <mod> --no-game      # 只查 Mod 自己（离线/无游戏）
python tools/cli.py loc audit <mod> --no-bom       # 不报 BOM（少数工具链会加 BOM）
python tools/cli.py loc audit <mod> --json=loc.json
```

退出码：`0` 无问题、`1` 有 error/warning、`2` 找不到 Mod、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 扫什么

- **引用**：`common/`、`events/`、`history/`、`interface/`、`gfx/`（`.txt/.gui/.gfx`）里这些属性值：
  `title`、`desc`、`text`、`tooltip`、`localization_key`、`custom_effect_tooltip`、`custom_trigger_tooltip`、
  `effect_tooltip`、`trigger_tooltip`、`selectable_tooltip`、`mapmode_tooltip`、`description`、`button_text`。
  **`name` 不算**（`.gfx` 里 `name` 是 sprite 名，误报会淹掉真问题）。
- **定义**：`localisation/**/*.yml`（`*_l_english.yml`、`*_l_simp_chinese.yml` …），按 `LANG_RE` 取语言。
- 容忍动态写法：`$VAR$`、`[ROOT.GetName]`、`\n`、含 `$`/`%`/`[`/`]` 的值跳过不判缺失。

## rule ID

| rule | 级别 | 含义 / 怎么修 |
|---|---|---|
| `loc.missing` | error | 脚本引用、Mod 与原版都没有定义。补 `.yml`，或改脚本里的 key |
| `loc.encoding_bad` | error | 文件不是 UTF-8（常见于 GBK 手写 yml）。用 UTF-8 重存 |
| `loc.bom_missing` | warning | HOI4 的 yml **需要** UTF-8 BOM。用带 BOM 的编辑器重存 |
| `loc.duplicate` | warning | 同一 key 在多个文件/多行重复定义，后者覆盖前者 |
| `loc.empty_value` | warning | `KEY:0 ""` 空字符串 |
| `loc.case_mismatch` | warning | 只有大小写不同（例如 `GER_focus` vs `ger_focus`） |
| `loc.lang_missing` | info | 某语言缺 N 个 key（**每种语言一条**，不逐 key 刷屏）。Mod 只做英文时属正常 |
| `loc.inherited` | info | Mod 没定义，但原版有，可继承，不用管 |
| `loc.no_game` | info | 没找到游戏目录，无法判断可否继承 |

## 读数建议

- 先看 `summary.missing`（真缺失）与 `summary.errors`，再看 `inherited`。
- `loc.missing` 里如果 key 是大写开头且看着像 `GFX_`/`idea_` 之类，多半是 `.gui` 里把 sprite 名写进了 `text =`，改回 `spriteType` 即可。
- 中文 Mod 常见：英文 yml 有、`simp_chinese` 没有 → 只有 `loc.lang_missing` 一条 info，不是 bug。

## `--json` 关键字段

```json
{"ok": false, "exit_code": 1, "command": "loc audit",
 "problems": [{"code": "loc.missing", "severity": "error", "path": "interface/x.gui",
               "line": 5354, "message": "...", "extra": {"key": "BABALKBLLALBLAL"}}],
 "summary": {"mod": "...", "script_refs": 458, "dynamic_refs": 12, "loc_files": 18,
             "keys_defined": 3200, "languages": ["english", "simp_chinese"],
             "missing": 2, "inherited": 80, "duplicates": 4, "lang_missing_keys": 0,
             "lang_missing_by_language": {"simp_chinese": 0},
             "omitted_by_code": {}, "omitted_total": 0}}
```

## 已知限制

- 不做插值展开：`[ROOT.GetNameDef]` 里的类名不校验，只保证不会误报。
- 只认常见 loc 属性名；自造 GUI 里把 key 塞进非标准字段时查不到。
- 原版对照依赖游戏目录（`--game`/自动探测），拿不到时 `loc.inherited` 变成 `loc.missing`（用 `--no-game` 可避免误解）。

---
title: "lint：静态校验"
domain: 07_tools
scope: 用一条命令查出脚本语法、编码、本地化、GFX 引用、ID 冲突、mod 结构问题
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py lint
  - tools/hoi4_lint.py
  - py tests/py/test_cli.py
---

# `lint`：静态校验

一次扫描 Mod 根目录，把「进游戏才会报错」的问题提前查出来。这是最常用的命令，改完任何内容都值得跑一次。

```bash
python tools/cli.py lint <mod>                 # 人读
python tools/cli.py lint <mod> --json          # 机器读
python tools/cli.py lint <mod> --no-vanilla    # 不建/不读原版索引（更快，跨 Mod 引用查不全）
python tools/cli.py lint <mod> --refresh-cache # 强制重建原版索引（换游戏版本后跑一次）
python tools/cli.py lint                       # 不带路径：从当前目录/--mod 猜 Mod
```

退出码：`0` 无问题、`1` 有 error/warning、`2` 找不到 Mod 或游戏、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 检查内容

- **结构**：`descriptor.mod` 是否存在/可解析、`name`/`version`/`tags`、同级 `<dir>.mod` 与 `path=` 是否对得上。
- **语法/编码**：括号与 token（`syntax.parse`）、脚本文件 BOM（`enc.bom_script`）、读取失败（`io.read`）。
- **本地化**：脚本里引用的 key 是否有定义（`loc.missing*` 一族）、同文件重复 key、BOM、语言文件格式。
- **GFX**：`gfx.*` 引用是否闭合、图标路径是否放在约定目录、`GFX_` 前缀、portrait/idea/decision/category 图标缺失。
- **ID 冲突**：自定义 ID 与原版重复、覆盖原版（`id.overrides_vanilla` 是要自觉确认的提示）。
- **原版索引**：把 `<game>/common|events|localisation|gfx` 建成索引，用来判断「这个 key/贴图是不是原版就有」。

## 常用 rule ID

| rule | 级别 | 怎么修 |
|---|---|---|
| `syntax.parse` | error | 按报的行号补 `}` 或 `=`，注意文件被截断 |
| `loc.missing_focus` / `loc.missing_focus_text` | error | 国策 `id` 与 `id_desc` 补到 `localisation/*_l_<lang>.yml` |
| `loc.missing_event_title` / `loc.missing_event_desc` | error | 事件 `title`/`desc` 的 key 补定义 |
| `loc.missing_idea` / `loc.missing_idea_desc` | error | 理念名与描述 key |
| `loc.missing_tech` | error | 科技 `name` key（科技树的 key 常写成小写，注意大小写一致） |
| `loc.duplicate_key` | warning | 同一 yml 里删掉重复行（后一条会覆盖前一条） |
| `gfx.missing` / `gfx.texture_missing` | error | `texturefile` 指向的 `.dds` 不存在或大小写不匹配 |
| `id.duplicate` | error | 同一 ID 定义两次，改名或删一个 |
| `id.overrides_vanilla` | warning | 有意覆盖原版就留着，无意则改名 |
| `mod.sibling_mod_missing` | warning | 同级 `<dir>.mod` 缺 `path=`（见下） |
| `mod.path_relative` | warning | `.mod` 里 `path=` 是相对路径：装进玩家 `mod/` 后才生效，仓库内直接跑会提示 |

## `mod.sibling_mod_missing` / `mod.path_*` 的正确写法

开发时通常在仓库里放一个 `.mod` 方便启动器识别：

```text
path = "C:/Users/you/Documents/Paradox Interactive/Hearts of Iron IV/mod/MyMod"
```

- 绝对路径且目录存在 → 不报。
- 绝对路径不存在 → `mod.path_not_found`（error）。
- 相对路径 → 若按 `.mod` 所在目录能解析则通过；否则降级成 `mod.path_relative` **warning**（提示「装进玩家 mod/ 目录后才生效」）。
- `path` 指向的位置和 `.mod` 所在目录不一致 → `mod.path_mismatch`。

## `--json` 关键字段

```json
{
  "ok": false,
  "exit_code": 1,
  "command": "lint",
  "problems": [{"code": "loc.missing_focus", "severity": "error",
                "path": "common/national_focus/my.txt", "line": 42, "message": "..."}],
  "summary": {"mod": "...", "errors": 1, "warnings": 3, "script_files": 271,
              "vanilla_index": true, "omitted_by_code": {}, "omitted_total": 0}
}
```

## 已知限制

- 只做静态检查：运行时 scope/trigger 合法性、GUI 实际渲染、贴图颜色都查不出来（见 `06_workflow/debugging.md`）。
- 原版索引较慢（首次几十秒，之后走 `%LOCALAPPDATA%\hoi4mod\cache`）；`--no-vanilla` 可跳过。
- 大型 total-conversion Mod 会有上万条 warning（多为 `gfx.dds_not_multiple_4`），看 `summary.errors` 与 rule 分布，不要逐条读。

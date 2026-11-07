---
title: "工具链总览"
domain: 07_tools
scope: hoi4mod 有哪些子命令、怎么装、怎么读输出
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - 本技能 tools/cli.py
  - .tmp/audit/skill-audit.md（旧脚本层审计）
---

# 工具链总览

所有工具都在一个入口：

```bash
python $SKILL/tools/cli.py <subcommand> [args...]
```

旧脚本名（`scripts/hoi4_lint.py`、`scripts/new_mod.py` …）仍然可用，行为等价，内部转调同一套实现。
**新代码、新文档、CI 一律用 `hoi4mod` 入口**。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 命令一览

| 子命令 | 做什么 | 需要游戏 |
|---|---|---|
| `doctor` | 环境体检：游戏路径、版本、用户目录、Python/Pillow、缓存可写 | 否（有则更好） |
| `lint [mod]` | 静态校验：语法、编码/BOM、本地化、GFX 引用、ID 冲突、`.mod` 结构 | 建议 |
| `loc audit [mod]` | 本地化 key 引用 vs 定义：缺失、重复、BOM、语言缺失 | 否 |
| `gfx audit [mod]` | `.gfx` sprite 与 DDS 贴图审计：闭合、头合法性、未使用 | 否 |
| `map audit [mod]` | map / states / strategicregions 一致性 | 否 |
| `model chain-check [mod]` | `.mesh` → `pdxmesh` → `entity` → `animation` 闭环 | 否 |
| `font audit [mod]` | 字体中文映射体检（哪个 `font =` 名没有中文分片） | 建议 |
| `font list` | 列出被映射到中文分片的字体名 | 建议 |
| `tech audit [mod]` | 科技树 folder / 页面 / 页签 / 网格一致性 | 建议 |
| `tech available [mod]` | 把 `technology_tags` 里的 `has_country_flag` 修为 `original_tag`（`--check`/`--apply`/`--revert`） | 是 |
| `tech sprites [mod]` | 科技小图标 sprite 与模板尺寸核对 | 否 |
| `tank probe` | 坦克设计器窗口/槽位实测 | 是 |
| `tank layout` | 生成 16 / 18 槽设计器布局（不写游戏目录） | 否 |
| `dds make\|solid\|check` | DDS 生成 / 纯色 / 头检查（需要 Pillow） | 否 |
| `icon import <in> <out>` | PNG → 科技图标 DDS | 否 |
| `errorlog [log]` | error.log 分类排错 | 否 |
| `install [mod]` | 安装到 `<USER_DIR>/mod` 并在 playset 启用（`--yes` / `--dry-run`） | 是 |
| `uninstall [mod]` | 卸载 | 是 |
| `reference build` | 从 `documentation/*.md` 生成 effects/triggers/modifiers/console 速查 | 是 |
| `parse <file>` | PDX 脚本解析，输出结构化结果（调试用） | 否 |
| `init <dir>` | 从模板生成一个可加载的最小 mod | 否 |
| `self-test` | 离线自检（15 个用例，不需要游戏，CI 用） | 否 |

`python $SKILL/tools/cli.py --help` 打印上面这张总表（`--help` 是全局的）；每个子命令的参数以 **本文档各篇** 为准：

| 文档 | 覆盖命令 |
|---|---|
| [lint.md](lint.md) | `lint` |
| [loc-audit.md](loc-audit.md) | `loc audit` |
| [gfx-audit.md](gfx-audit.md) | `gfx audit` |
| [map-audit.md](map-audit.md) | `map audit` |
| [model-chain.md](model-chain.md) | `model chain-check` |
| [tech.md](tech.md) | `tech audit` / `tech available` / `tech sprites` |
| [font.md](font.md) | `font audit` / `font list` |
| [tank.md](tank.md) | `tank probe` / `tank layout` |
| [dds.md](dds.md) | `dds make|solid|check` / `icon import` |
| [install.md](install.md) | `install` / `uninstall` |
| [doctor.md](doctor.md) | `doctor` |
| [self-test.md](self-test.md) | `self-test` |
| [misc.md](misc.md) | `init` / `parse` / `errorlog` / `reference build` / `paths` |

## 读输出

- 人读模式：一行一个问题，`级别 规则ID 文件:行号 说明`。
- `--json`：结构化输出，字段与退出码见 [cli-conventions.md](cli-conventions.md)。
- 退出码：`0` 无问题 / `1` 发现问题 / `2` 用法或环境错误 / `3` 写操作被拒。

## 缓存

首次运行会索引原版数据（几十 MB 目录），索引写在 `%LOCALAPPDATA%\hoi4mod\cache`（Linux/macOS 为
`~/.cache/hoi4mod`），可用 `--cache-dir` 指定。**不要在技能目录里生成缓存**，也不要把它提交进仓库。

## 常见用法组合

```bash
# 改完内容，提交前
python $SKILL/tools/cli.py lint <mod> --json
python $SKILL/tools/cli.py loc audit <mod>
python $SKILL/tools/cli.py gfx audit <mod>

# 进游戏前先预演安装
python $SKILL/tools/cli.py install <mod> --dry-run

# 出问题了
python $SKILL/tools/cli.py errorlog --user-dir "$HOI4_USER_DIR"
```

工具查不出来的问题（运行时才暴露的），走 `06_workflow/debugging.md` 的手工 triage 流程。

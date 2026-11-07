---
title: "CLI 约定：退出码、JSON、dry-run"
domain: 07_tools
scope: 所有 hoi4mod 子命令共用的契约，写脚本/CI 时读这篇
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py
  - tools/_io.py
  - tools/_result.py
---

# CLI 约定

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 退出码

| 码 | 含义 | 什么时候用 |
|---|---|---|
| `0` | 无问题 | 检查类命令没发现问题；写操作成功 |
| `1` | **发现问题** | 检查类命令找到了 error/warning（这是可预期的结果，不是崩溃） |
| `2` | 用法或环境错误 | 参数错、找不到 mod、找不到游戏、缺依赖 |
| `3` | 写操作被拒 | 需要 `--yes` 才能写的操作被拒绝，或目标被占用 |

`0` 与 `1` 的区别很重要：CI 里应当把 `1` 当作"检查失败"而不是"脚本挂了"，这样报告才有意义。

## `--json`

```bash
python $SKILL/tools/cli.py lint <mod> --json            # 到 stdout
python $SKILL/tools/cli.py lint <mod> --json=out.json   # 到文件（stdout 只留人读摘要）
```

固定结构（五键，脚本里按这个读，别猜字段）：

```json
{
  "ok": false,
  "exit_code": 1,
  "command": "lint",
  "problems": [
    {
      "code": "loc.missing_focus",
      "severity": "error",
      "path": "common/national_focus/my.txt",
      "line": 42,
      "message": "国策 `my_focus` 的 loc key 没有定义",
      "extra": {"key": "my_focus"}
    }
  ],
  "summary": { "errors": 1, "warnings": 3, "script_files": 271, "mod": "...",
               "omitted_by_code": {}, "omitted_total": 0, "log": [] }
}
```

- `problems` 永远是数组（空数组表示干净），不要在脚本里判断字段是否存在。
- `code` 是稳定标识（`域.问题`，如 `loc.missing`、`gfx.texture_missing`、`model.entity_no_mesh`），会随版本增加但不会改名；**按 `code` 做白名单**比按 `message` 可靠。
- `severity` 只有 `error` / `warning` / `info`；退出码只由前两种决定（`info` 不影响 `ok`）。
- `path` 是相对 Mod 根的 POSIX 路径，跨平台一致；`line` 为 0 表示不适用。
- `extra` 是 rule 专属字段（如 `key`/`entity`/`mesh`），可能为空对象。
- **大 Mod 截断**：同一 `code` 默认最多保留 200 条明细，其余计数进 `summary.omitted_by_code` 与 `omitted_total`；退出码仍按全量计算。要全量明细加 `--verbose`。
- 旧脚本驱动的子命令（`tech audit`、`tech sprites`、`tank layout`、`install`、`init`、`reference build`）detail 里是 `legacy.<group>.<action>` 这类 code，`message` 是原工具的逐行输出；`summary.log` 保留完整的原始输出行。

## `--dry-run` 与 `--yes`

- `install` / `uninstall` / `tech available --apply|--revert` 这类写操作：**没有 `--yes` 也没有 `--dry-run` 时直接退出 `3`**，什么都不写。
- `--dry-run` 打印「将要做什么」，退出码仍按真实检查结果给（计划可行 → `0`）。
- `init` / `icon import` / `reference build` 没有 dry-run 实现：给 `--dry-run` 会以 `3` 拒绝，去掉才会执行。
- agent 场景推荐：先 `--dry-run` 看路径对不对，再 `--yes` 执行。

## 输出与编码

- 所有输出 UTF-8；Windows 控制台不是 UTF-8 时工具会自己 reconfigure，不会因 GBK 崩。
- 需要给机器读就加 `--json`，不要解析人读格式（列宽会变）。
- `--quiet` 只输出问题行；`--verbose` 输出扫描过程；`--no-color` 关闭颜色（CI 默认无颜色）。

## 路径与环境

- 游戏目录：`--game` > `HOI4_GAME` > `launcher-settings.json` > Steam 库探测 > 常见路径。
- 用户目录：`--user-dir` > `HOI4_USER_DIR` > `Documents/Paradox Interactive/Hearts of Iron IV`。
- mod 目录：直接传路径；也可以传 `.mod` 文件所在目录，工具会读 `path=` 字段。
- 缓存：`--cache-dir` > `%LOCALAPPDATA%\hoi4mod\cache`（Linux/macOS `~/.cache/hoi4mod`）。

## 组合与管道

```bash
# 只看结构/语法，不加载 6.9 MB 原版索引（快）
python $SKILL/tools/cli.py lint <mod> --no-vanilla
# 原版索引过期时强制重建
python $SKILL/tools/cli.py lint <mod> --refresh-cache --json=report.json
# 全套审计（互不依赖，可并行）
python $SKILL/tools/cli.py loc audit <mod> --json=loc.json
python $SKILL/tools/cli.py gfx audit <mod> --no-unused --json=gfx.json
# CI
python $SKILL/tools/cli.py self-test || exit 2
python $SKILL/tools/cli.py lint <mod> --json=report.json; test $? -le 1
```

退出码语义见上面；各命令的具体参数见 `07_tools/` 下对应的单篇文档，`--help` 只打印全局总表（不提供逐子命令 help）。

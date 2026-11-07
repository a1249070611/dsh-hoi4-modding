---
title: "doctor：环境体检"
domain: 07_tools
scope: 一条命令看清游戏路径、版本、用户目录、Mod 目录、Python/Pillow、缓存是否可写
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py doctor
  - tools/doctor.py
  - tools/_paths.py
---

# `doctor`：环境体检

新机器、换游戏目录、工具行为异常时先跑这个。它不改任何东西。

```bash
python tools/cli.py doctor
python tools/cli.py doctor --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"
python tools/cli.py doctor --user-dir "<玩家目录>" --mod <mod>
python tools/cli.py doctor --json
```

退出码：`0` 没有 error（warning 不影响 0？——有 error 才 1，见下）/ `1` 有 error / `2` 用法错误 / `3` 不适用。

> 实际判定：`doctor` 把缺失游戏/用户目录当 **warning**（离线可用），只有 Python 过旧、缓存不可写、指定 Mod 不存在这类才是 **error** → 退出 `1`。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 检查项

| 项 | 正常 | 异常 code |
|---|---|---|
| Python 版本 | ≥3.10 | `doctor.python_old`（error） |
| stdout 编码 | 能 reconfigure UTF-8 | 输出在 `doctor.stdout_encoding`（info，记录实际值） |
| 游戏目录 | 找到且含 `hoi4.exe` + `interface/` | `doctor.no_game`（warning）、`doctor.game_layout`（warning，目录像但不完整） |
| 游戏版本 | 读 `hoi4_rev.txt` 或 launcher-settings | 记录在 `game_version` |
| 中文分片数 | 从 `interface/*.gfx` 统计到字体名 | 记录在 `zh_fonts`（本机 41） |
| 玩家目录 | 存在 | `doctor.no_user_dir`（warning） |
| Mod 目录 | 给了 `--mod` 或能猜到时校验 | `doctor.mod_missing`（error）、`doctor.mod_no_descriptor`（warning） |
| 缓存目录 | 可创建、可写 | `doctor.cache_unwritable`（error） |
| 旧缓存 | 发现旧版 `scripts/.cache/vanilla_index.json` | `doctor.legacy_cache`（info，提示可删/已迁移） |
| Pillow | 可 import | `doctor.no_pillow`（info，DDS/图标功能受限） |

## 怎么读游戏路径探测

`summary.game_probes` 是探测过程，按顺序：

```text
[miss] HOI4_GAME 环境变量
[miss] launcher-settings.json
[hit]  Steam libraryfolders.vdf -> C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV
```

顺序：`--game` → `HOI4_GAME` → `launcher-settings.json` 的 `gamePath` → Steam `libraryfolders.vdf` → 各盘常见路径。**没有任何硬编码盘符**。

## `--json` 示例

```json
{"ok": true, "exit_code": 0, "command": "doctor",
 "summary": {"tools_version": "2.0.0", "python": "3.14.8",
             "platform": "Windows-11", "stdout_encoding": "utf-8",
             "game": "<GAME_DIR>",
             "game_probes": ["[miss] HOI4_GAME", "[hit] steam libraryfolders.vdf -> ..."],
             "game_version": "1.19.4.2", "zh_fonts": 41,
             "user_dir": "<USER_DIR>", "user_dir_exists": true,
             "mod_dir": null, "cache_dir": "<CACHE_DIR>",
             "cache_writable": true, "pillow": "13.0.0", "errors": 0, "warnings": 0}}
```

## 常见处理

- **找不到游戏**：设 `HOI4_GAME=<GAME_DIR>`，或用 `--game <GAME_DIR>`。
- **缓存不可写**：`--cache-dir <可写目录>`；公司电脑常见 `%LOCALAPPDATA%` 被重定向。
- **Pillow 缺失**：`pip install pillow`（只有 DDS/图标命令需要）。
- **旧缓存很大**：`scripts/.cache/vanilla_index.json`（约 6.9 MB）可以删，新缓存已迁到 `%LOCALAPPDATA%\hoi4mod\cache`。

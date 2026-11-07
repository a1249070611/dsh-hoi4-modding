---
title: "install / uninstall：装进玩家 mod 目录"
domain: 07_tools
scope: 把仓库里的 Mod 装到 <user_dir>/mod、写 playset、或反向卸载；含 --dry-run 预演
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py install / uninstall
  - tools/install_mod.py
---

# `install` / `uninstall`：装进玩家 mod 目录

仓库里的 Mod 要进游戏，得放到 `Documents/Paradox Interactive/Hearts of Iron IV/mod/` 并由启动器/playset 选中。这个命令做拷贝 + 写 `.mod` + 可选写 `dlc_load.json`。

```bash
python tools/cli.py install <mod> --dry-run       # 只看计划，不写任何东西
python tools/cli.py install <mod> --yes           # 真的安装（拷目录 + 写 .mod）
python tools/cli.py install <mod> --link --yes    # 不拷贝，.mod 的 path 直接指向仓库
python tools/cli.py install <mod> --yes --enable  # 同时写 dlc_load.json（自动备份）
python tools/cli.py install <mod> --yes --force   # 目标已存在时覆盖
python tools/cli.py uninstall <mod> --yes         # 删 <user_dir>/mod/<name> 与 .mod，并从 playset 移除
```

退出码：`0` 成功 / `1` 检查有问题 / `2` 目标已存在（没给 `--force`）或找不到 Mod / **`3` 没给 `--yes` 也没有 `--dry-run`**（写操作被拒，什么都不会发生）。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 参数

| 参数 | 作用 |
|---|---|
| `--user-dir PATH` | 玩家目录，默认 `HOI4_USER_DIR` 或 `Documents/Paradox Interactive/Hearts of Iron IV` |
| `--link` | 不拷贝：只写 `.mod`，`path` 指向仓库目录（开发期最方便，改了立刻生效） |
| `--enable` | 追加到 `dlc_load.json` 的 `enabled_mods`（写前备份 `.json.bak`） |
| `--dry-run` | 打印源/目标/描述文件/是否启用，不写文件 |
| `--yes` | 确认写操作 |
| `--force` | 覆盖已存在的目标 |
| `--uninstall` | 等价于 `uninstall` 子命令 |

## 它具体做什么

1. 校验目标 Mod：`descriptor.mod` 存在、`name` 可读；目标目录 = `<user_dir>/mod/<name>`。
2. 拷贝时忽略 `__pycache__`、`*.pyc`、`tests/`、`_scratch/`（不把开发垃圾带进游戏）。
3. 写 `<user_dir>/mod/<name>.mod`：描述文件内容 + 一行 `path="<绝对路径>"`。
4. `--enable` 时读 `dlc_load.json`，把 `mod/<name>.mod` 追加进 `enabled_mods`（已存在则不重复）。
5. 被占用/无权限时：`3`（PermissionError）或提示关闭游戏后重试。

## 常见问题

- **启动器里看不到 Mod**：确认 `.mod` 在 `<user_dir>/mod/` 下且 `path=` 指向真实存在的目录；`--link` 模式下仓库路径不能含中文/被移动。
- **装了两个同名**：`--force` 覆盖前先看 `--dry-run` 的目标路径。
- **改了仓库但游戏里没变**：用的是拷贝模式；改 `--link` 或重新 `install --yes --force`。
- **卸载没删干净**：`uninstall` 只删 `<name>` 目录/`.mod` 与 playset 条目；`dlc_load.json` 被手改过时按名字移除。

## `--json`

```json
{"ok": true, "exit_code": 0, "command": "install",
 "problems": [],
 "summary": {"mod": "...", "dry_run": false, "exit": 0, "lines": 6, "log": ["源：...", "目标：...", "启用：是"]}}
```

被拒时：

```json
{"ok": false, "exit_code": 3, "command": "install",
 "problems": [{"code": "write.refused", "severity": "error",
               "message": "安装/卸载会写入玩家目录…需要 --yes 确认，或 --dry-run 只预演"}],
 "summary": {"errors": 1, "warnings": 0}}
```

## 已知限制

- 不调用启动器/Steam，不校验 playset 的加载顺序（`dlc_load.json` 只追加）。
- 不处理 Workshop 上传（那是另一套流程）。
- `--enable` 只动 `dlc_load.json`，不动 `launcher-settings.json`。

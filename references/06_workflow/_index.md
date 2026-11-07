---
title: 工作流（Workflow）：建 mod / 发布 / 兼容 / 调试 / 校验 / 迁移
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-11-06
---

# 06_workflow — 建 mod / 发布 / 兼容 / 调试 / 校验 / 迁移

## 一句话定位

**把「写完能跑」变成「装得上、不冲突、能联机、升级不炸」。** 本目录只管流程与工程约束，不重复讲语法（→ `../01_script/`）、内容系统（→ `../02_content/`）、军事/地图（→ `../03_military/`、`../04_world/`）、界面/本地化/字体（→ `../05_presentation/`）。

## 文档清单

| 文档 | 一句话摘要 |
|---|---|
| [setup.md](setup.md) | 从零建一个能被启动器识别的 mod：目录、两个 descriptor、`path`、`supported_version`、本地 vs 创意工坊；含 **ASCII 路径陷阱** |
| [publishing.md](publishing.md) | 发布到创意工坊的完整清单：封面、标签、`remote_file_id`、更新流程、发布前自检 |
| [compatibility.md](compatibility.md) | 覆盖式 vs 补丁式、加载顺序与 `dependencies`、`replace_path`、多 mod 冲突判定、校验和与联机 |
| [debugging.md](debugging.md) | `-debug_mode`、控制台命令、`error.log` 定位法、增量排查与崩溃二分 |
| [validation.md](validation.md) | **通用校验方法论**：语法 / 引用 / 语义 / 运行 / 门禁五层，含 auto-check 脚本的设计契约（分项 PASS/FAIL、`--json`、非零退出） |
| [performance.md](performance.md) | 脚本性能：用 `timer` 量化、周期扫描 vs 动作驱动、常见性能陷阱 |
| [migration.md](migration.md) | 旧 mod 升级到 1.19 的检查清单（含 1.19 移除/新增的实证清单） |

## 资料权威顺序（查任何字段前先看这里）

1. **游戏自带 `documentation/*.md`**（effects / triggers / modifiers / console commands …）—— 字段名与签名的第一手来源。
2. **原版文件里的真实用例**（`grep -rn` 至少找到两处用法一致）—— 「文档没写但引擎认」和「文档写了但引擎不认」都以它为准。
3. **官方 wiki 与 patch notes** —— 结构说明与版本变更。
4. **社区教程/视频** —— 只当线索，不当结论。

冲突时以「**游戏文件 + 实测**」为准。官方 `documentation/` 滞后于引擎是常态：新 trigger/effect 往往先上线、后补文档，所以在文档里搜不到 **≠** 写法非法。

## 本领域最重要的 5 条结论

1. **一个 mod = 两个描述文件**：`mod/你的mod.mod`（唯一写 `path` 的地方，文件名决定加载顺序）+ `<mod 文件夹>/descriptor.mod`（跟随分发，不写 `path`）。搞混这两个是本领域第一大错误来源。
2. **`path` 必须是纯 ASCII、用 `/`**。开发目录含中文（中文用户名、中文项目名）是常见雷区：路径非法时启动器可能仍显示 mod，但进游戏毫无效果。见 [setup.md](setup.md) §6。
3. **同名文件整体替换，不存在「逐行合并」**。所以「最小侵入」的做法是：**新增文件 + 用 `on_actions`/事件/决议在运行时注入**，而不是复制原版文件改一行。原版一更新，复制式改法就会把你锁死在旧内容上。
4. **加载顺序 = 原版 → DLC → 用户目录 → mod（按 `.mod` 文件名）**；`dependencies` 才能改这个顺序，`replace_path` **不改顺序**、只卸载已索引的文件夹，而且**必须两个 `.mod` 都写**。
5. **`error.log` 里 95% 以上是原版自带的噪声**。所以调试的第一步不是「修第一个报错」，而是**分类过滤，只找与你 ID 前缀/文件路径相关的行**。详见 [debugging.md](debugging.md) 与 [validation.md](validation.md) §4。

## 本领域最常见的坑（都源自 1.19.x 实测）

| 坑 | 症状 | 去哪看 |
|---|---|---|
| `path` 含非 ASCII | 启动器能显示 mod，但进游戏毫无效果 | [setup.md](setup.md) §6 |
| `path` 用了 `\` | 同上（反斜杠被当转义） | [setup.md](setup.md) §3 |
| `supported_version="1.*"` | `error.log: Invalid supported_version` | [compatibility.md](compatibility.md) |
| `.mod` 写 `thumbnail=` | `Unexpected token: thumbnail` | [publishing.md](publishing.md) |
| 复制原版文件改一行 | 下次原版更新后行为错乱/被覆盖 | [compatibility.md](compatibility.md) |
| `replace_path` 只写一个 `.mod` | 配置了但不生效 | [compatibility.md](compatibility.md) |
| 用 `-debug` 而不是 `-debug_mode` | 调试模式没开 | [debugging.md](debugging.md) |
| 改 `history/states`、`map` 后热加载 | 看不到变化 | [debugging.md](debugging.md) |
| 以为 error.log 清空才是「修好了」 | 白费力气 | [debugging.md](debugging.md) |
| 大版本后没重读 Modding patch notes | 关键字被移除（如 `add_temporary_buff_to_units`） | [migration.md](migration.md) |

## 与其他目录的接口

- **写代码前**：`../01_script/`（scope/effect/trigger 语义）—— 本目录不重复。
- **写内容时**：`../02_content/`（国策/事件/决议/理念的结构）—— 本目录只讲「文件放哪、怎么被加载」。
- **做界面/本地化**：`../05_presentation/` —— `.yml` 的 BOM、字体、GFX 定义细节由该目录负责；本目录只强调「本地化不参与校验和」这一工程结论。
- **要工具**：`../07_tools/` 是工具索引，实际实现是插件根目录的 `scripts/*.py`（`hoi4_lint.py`、`tech_tree_audit.py`、`errorlog_triage.py` …）。
- **要门禁**：本目录的 [validation.md](validation.md) 给出「一次跑完全部分项检查」的脚本契约。
- **要看真实项目怎么踩坑**：`../90_case-studies/`（案例是实战记录，不是默认做法）。

---
title: "SOL-006 Mod 安装到玩家目录"
id: SOL-006
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/install_mod.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-006 Mod 安装到玩家目录

## 它想解决什么

游戏只扫描 `Documents/Paradox Interactive/Hearts of Iron IV/mod/`。你在开发目录里写的 mod，**启动器根本看不到**，除非"安装"过去。

新手最常见的困惑："我按教程建了 mod 目录，为什么启动器里没有？"

## 思路

上游 `install_mod.py` 解决这个问题，两种安装方式：

| 方式 | 做法 | 适用 |
|---|---|---|
| 复制 | 把开发目录整个复制到玩家 mod 目录 | 简单，但每次改动要重新复制 |
| `.mod` 指向开发目录 | 只写一个 `.mod` 文件，`path` 指向开发目录 | 开发期推荐，改完直接生效 |

还可选写入 `dlc_load.json` 自动启用。

关键设计点：
- `--dry-run` 预览，不写盘
- 必须 `--yes` 才真正写（防误操作）
- `uninstall` 对应卸载

## 为什么没被采用

本插件选择**不做写操作**，理由是不碰用户的游戏目录更安全。`06_workflow/setup.md` 里写了手工步骤。

但这个决定的代价是：**每次新建 mod 都要手工复制/建 .mod**，而且容易把 `path` 写错（写成相对路径、或指向了 mod 目录而非其父目录）。

## 如果要用，怎么验证

1. 读上游 `install_mod.py`，确认它生成的 `.mod` 里 `path` 的写法
2. 用 `--dry-run` 跑一次，检查计划写入的路径
3. 实际安装一个测试 mod，打开启动器确认能看到

验证标准：启动器列表里出现该 mod，启用后进游戏能加载。

## 备注

**`path` 的基准目录是最大的坑**：`path` 应指向 mod 目录的**父级**，而不是 mod 目录本身。写错的话启动器能看到 mod 但加载失败。

上游 `install_mod.py` 的注释里明确提到了这一点。如果要补实现，这个细节必须原样保留。

顺带：本插件 `kiant_hoi4_validate_mod` 目前会检查 `.mod` 的路径合法性，但没有安装功能。

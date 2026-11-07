---
title: 发布（创意工坊 / Paradox Mods）工程清单
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - https://hoi4.paradoxwikis.com/Mod_structure
  - https://hoi4.paradoxwikis.com/Modding
  - https://bcssov.github.io/IronyModManager/faq.html
  - mod
---

# 发布工程清单

> 本文是「发布前必须满足的工程条件」清单：规格来自 wiki 与已发布 mod 的真实结构。基线 **1.19.x**。

## 1. 发布前 8 项硬检查（任何一项不过就别发）

| # | 检查 | 怎么查 | 不过的后果 |
|---|---|---|---|
| 1 | `descriptor.mod` 在 mod 根目录 | `ls <mod 目录>/descriptor.mod` | 创意工坊上传后订阅者无法加载 |
| 2 | `descriptor.mod` **无 BOM** | 十六进制看开头是否 `EF BB BF` | 启动器解析异常 |
| 3 | 封面 `thumbnail.png` 存在且 **< 1 MB** | `ls -l thumbnail.png` | 上传被拒（Paradox Mods 明确 1MB 限制） |
| 4 | `.mod` 用 `picture="thumbnail.png"`（**不是** `thumbnail=`） | grep | 实测报 `Unexpected token: thumbnail` |
| 5 | `supported_version="1.19.*"` | grep | `Invalid supported_version`（实测 7 例） |
| 6 | `name` 全局唯一（不与已装 mod 撞名） | 比对 `mod/*.mod` 的 `name=` | 只有先加载的那个生效 |
| 7 | 本地化齐全（en + simp_chinese，UTF-8 **BOM**） | 跑 lint / 人工查 | 游戏里显示 key 原文 |
| 8 | `version` 递增（语义化） | 人工 | 更新玩家看不出变化 |

## 2. 上传的是什么、不传什么

- **上传**：`descriptor.mod` + mod 本体所有文件。
- **不传**：`用户目录/mod/xxx.mod`（那份含 `path` 的，是**本机专属**的）。
- 上传后启动器会回填 `remote_file_id` 到你的本地 `.mod` —— **看到它出现就说明绑定成功**，之后更新走同一个 ID。

## 3. 更新流程（避免「更新变成新 mod」）

```
1. 改本体文件
2. 启动器 → 播放集里点 Update mod（不要用 Steam 客户端上传）
3. 确认 remote_file_id 未变
4. 大版本后：先读 patch notes 的 Modding 段（见 migration.md），再改 supported_version
5. 写更新说明（玩家最关心：旧存档能不能继续）
```

## 4. 三条真实踩过的错误（发布前一定要避开）

1. **`thumbnail=` 字段** → `error.log` 报 `Unexpected token: thumbnail`（`mod/ugc_3243611664.mod:9`）。
2. **`supported_version="1.*"`** → 7 个已发布 mod 各报一条 `Invalid supported_version`（`logs/error.log:1-8`）。社区里这种写法非常常见 —— 说明很多作者从旧教程抄的。
3. **同名/双份描述文件**：用户目录 `mod/` 下同时存在 `2067895531`（目录）与 `2067895531.mod`、`ugc_2067895531.mod`，以及 `BlackIce_Tech_Tree` 与 `ugc_*` 双份。wiki 说这会导致「只有一个生效」「更新失败」。发布者视角的教训：**订阅自己的 mod 是万恶之源**（wiki 原文说几乎总是没有理由订阅自己的 mod）。

## 5. 版本兼容承诺怎么写（给玩家看的）

建议在创意工坊描述里固定写三行：

```
Supported game version: 1.19.*
Save-game compatible: yes（从 0.x 到 0.y 可以继续；1.19 大版本不保证）
Load order: 建议放在 xxx 之后（dependencies 已声明则不用手动排）
```

理由：`supported_version` 决定启动器的「过时」标记；`dependencies` 决定加载顺序（**不是**由玩家在启动器里拖动决定，见 [compatibility.md](compatibility.md)）。

## 6. 不能确认的部分（写明，不要编）

- ❌ 创意工坊**标签合法列表**（wiki 指向上传页，本轮无法登录 Steam 抓取）→ 上传时从上拉框里复制。
- ❌ 上传界面的字段限制（描述长度、变更日志、许可协议）。
- ❌ 封面最小分辨率（wiki 只给「建议 1:1、<1MB」）→ 可从本机已下载 mod 的 `thumbnail.png` 反推经验值。
- ❌ Paradox Mods 与 Steam 双发布的差异（wiki 只提到 1MB 限制与 `remote_file_id` 通用）。

## 常见错误 / 自检清单

- [ ] 上传的是 `descriptor.mod` 而不是带 `path` 的 `mod/xxx.mod`？
- [ ] 封面 < 1MB、叫 `thumbnail.png`、字段是 `picture=`？
- [ ] `supported_version` 是 `1.19.*`？
- [ ] `name` 没和任何已装 mod 冲突？
- [ ] `remote_file_id` 已在更新后保持不变？
- [ ] 大版本更新前读过 patch notes 的 Modding 段？
- [ ] 描述里写清了「支持的版本 / 存档兼容性 / 加载顺序」？

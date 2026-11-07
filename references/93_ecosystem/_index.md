---
title: "生态调研：同类开源工具怎么做"
domain: 93_ecosystem
verified_on: 2026-11-06
---

# 93 生态调研

这一域研究**同类工具的实现方式**，目的是对照出本库的盲区，而不是照搬。

和 `90_case-studies/` 的分工：那边是"某个 mod 怎么做的"（内容层面），
这边是"某个**工具**怎么做的"（工程层面）。

## 本域 5 条最重要结论

1. **hagane-studio 有 1291 个 Go 文件，其中 529 个是测试（41%）。**
   `toolapi` 层代码 16485 行配测试 13818 行。**对外接口测得最狠**——
   因为接口就是承诺，承诺不稳其他都是空的。

2. **它能在读→改→写过程中保住原作者所有注释和缩进。**
   方法：每个 token 自带 `Trivia`（前导注释 + 行尾注释 + 原始空白）。
   本库的 `cw.py` 遇到 `#` 直接丢弃，**这是明确的能力缺口**。

3. **它给每次写操作返回 `mutation_receipt`，里面有一段 `reporting_rule`
   专门告诉 AI"哪些话不能说"。** 这是全仓库最值得学的设计——直接冲着
   "AI 谎报成功"去的。`write_status=committed` 和 `verification_status=not_run`
   被刻意分开，因为"写进去了"不等于"写对了"。

4. **科技树的格子尺寸和排列方向是从 `.gui` 里读出来的，不是猜的。**
   `gridboxType` 的 `slotSize` 给尺寸（默认 70×70），`format=left` 表示列优先。
   本库解算 `relative_position_id` 只得到数据层坐标，要还原视觉位置还得叠这一层。

5. **它自己手写了 839 行 DDS 编解码**（解码未压缩 32bpp + BCn，还能编码回 DXT5），
   因为 Pillow 对 DDS 支持太差。本库的 `kiant-hoi4-dds.py` 只解头部，不解像素。

## 篇目

| 篇 | 讲什么 |
|---|---|
| `hagane-studio.md` | 总览：硬数据、五层架构、项目存储、定位差异 |
| `hagane-studio-deep-notes.md` | **逐模块精读笔记**：artifact 构建、snapshot 指纹、51 条引用规格、诊断三段式、阶段缓存、双轨字段范式 |
| `hagane-studio-paradox.md` | 解析器：trivia 机制、三类错误恢复、Python 兼容层、三层测试 |
| `hagane-studio-mutation-receipt.md` | 写操作回执：防 AI 谎报的完整机制与判定表 |
| `hagane-studio-guirender.md` | 界面重建：全量索引、DDS 编解码、gridbox 几何、170 模块组织 |
| `hagane-studio-toolapi.md` | 149 个工具的组织、五个横切中间件、id/key 分离、安全设计 |

## 对本库的直接价值

### 已经落地的（2026-11-06，2.9.3）

| 事项 | 结果 |
|---|---|
| **lint 加回执** | 输出末尾加 `--- 回执 ---` 段：`checked_scope` / `verification: syntax_only` / `not_checked`（本地化、贴图、游戏内行为）/ `reporting_rule`（禁止仅凭此宣称完成）。4 条断言钉住 |
| **自检加原版全量解析** | `HOI4_VANILLA_DIR` 控制，无游戏时显式 SKIP。**实测 4410 个原版 .txt 零失败** |
| **大小写敏感结论修正** | 原版 `countrytechtreeview.gui` 同一文件混用 `slotsize` 与 `format = "LEFT"`，成为「键名不区分大小写」的第二条独立证据 |

### 可以马上做但还没做的

| 事项 | 成本 | 收益 |
|---|---|---|
| 改报告措辞（禁"已修复/完成"） | 很小 | 使用者能准确判断风险 |
| lint 结果写成 `_LINT_REPORT.log` 放进 mod 目录 | 小 | 跑完能回看，而不是只在终端一闪 |

### 中期的

| 事项 | 成本 | 收益 |
|---|---|---|
| `.gui` 布局几何读取（约 80 行） | 中 | 科技树/国策树能画准 |
| DDS 解码（仅未压缩，约 100 行） | 中 | 能显示游戏原图 |
| 引用规格表从 2 条扩到 51 条（照抄 `crossRefSpecs`） | 中 | 覆盖 idea/event/trait/tech/character 等 |
| `id` 与 `key` 分离 | 中 | 将来支持编辑的基础 |

### 长期 / 不必追的

| 事项 | 结论 |
|---|---|
| token 级 trivia + 无损写回 | 只在要做"编辑已有 mod"时才需要；我们是"从零生成"，可以不做 |
| 170 个界面模块 | 广度路线，与我们的深度路线不同；不追 |
| 149 个工具全覆盖 | 同上；我们覆盖高频路径 + 通用兜底更划算 |

## 常见误判提醒

| 想法 | 实际 |
|---|---|
| "它只是个可视化编辑器，技术含量不高" | 20 万行代码、41% 测试、手写 DDS 编解码 |
| "Go 项目应该有很多依赖" | 只有 5 个，HTTP/JSON/存储全手写 |
| "它从零设计的新项目" | 大量 `pyXxx` 函数证明是从 Python 版迁移，为字节级对齐而复刻 Python 浮点格式化 |
| "可视化工具不需要考虑 AI" | 它的 `reporting_rule` 是专门给 AI 看的 |

## 出处与时效

- 仓库地址：https://github.com/hagane-works/hagane-studio
- 许可证：GPL-3.0-only（**引用其代码需同样开源**；本库只是研究其设计，不复制代码）
- 本文基于 commit `main @ 2026-11-01`，仓库创建于 2026-10-30，仍在活跃开发
- 所有数字均为本地源码实测，非转载

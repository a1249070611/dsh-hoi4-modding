---
title: "生态调研：同类开源工具怎么做"
domain: 93_ecosystem
verified_on: 2026-11-06
---

# 93 生态调研

这一域研究**同类工具的实现方式**，目的是对照出本库的盲区，而不是照搬。

和 `90_case-studies/` 的分工：那边是"某个 mod 怎么做的"（内容层面），
这边是"某个**工具**怎么做的"（工程层面）。

## 本域 7 条最重要结论

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

6. **CWTools 的 script_documentation 与本库 kb 逐条对账：effects 553 完全一致**；
   它独有 loc 命令表（~80 个 Get*）与数据链（links）知识，我们有 6 万+ 实例符号
   它没有。`kb.py` 已扩 `DOC_KINDS` 补齐五类官方文档（+433 符号，
   console_command 一项 375:2 反超）。见 `cwtools-analysis.md`。

7. **AI 辅助 modding 在 2026 年已是显学**（RHoiScribe 的 MCP 服务器、UC 扩展的
   200+ MCP 工具、一批 skill pack），但没有一个项目同时做「机器校验 +
   原版实证知识库 + 错题本」。见 `github-ecosystem.md`。

## 篇目

| 篇 | 讲什么 |
|---|---|
| `hagane-studio.md` | 总览：硬数据、五层架构、项目存储、定位差异 |
| `hagane-studio-deep-notes.md` | **逐模块精读笔记**：artifact 构建、snapshot 指纹、51 条引用规格、诊断三段式、阶段缓存、双轨字段范式 |
| `hagane-studio-paradox.md` | 解析器：trivia 机制、三类错误恢复、Python 兼容层、三层测试 |
| `hagane-studio-mutation-receipt.md` | 写操作回执：防 AI 谎报的完整机制与判定表 |
| `hagane-studio-guirender.md` | 界面重建：全量索引、DDS 编解码、gridbox 几何、170 模块组织 |
| `hagane-studio-toolapi.md` | 149 个工具的组织、五个横切中间件、id/key 分离、安全设计 |
| `cwtools-analysis.md` | **CWTools 工程解剖**（2026-11-07）：F# LSP + `.cwt` 规则 DSL、script_documentation 逐维对账、loc 命令表/数据链知识、引擎校验四段式 |
| `github-ecosystem.md` | **GitHub hoi4 生态图谱**（2026-11-07）：2788 仓库按 IDE 插件/AI agent 工具/解析库/独立工具分类，fork 关系图与行动结论 |
| `hearts-of-modding-analysis.md` | **hearts-of-modding 解剖**（Rust LSP）：57 诊断码全表、LayeredValue 分层 VFS、实证校准法、地图交叉七连、scope 校验三件套 |
| `uc-hoi4-modding-tools-analysis.md` | **UC HOI4 Modding Tools 解剖**：仓库无源码只发二进制、236 个 MCP 工具核实、单表生成工具/一键接入 UX 可抄、广度路线的天花板 |
| `hoi4modutils-analysis.md` | **hoi4modutilities + fork 对比**：零容错解析器（反例教材）、fork 的 focus tree 语义校验（前置/互斥/环/坐标/可达）、地图安全措施（事务回滚/ID 上限）、`#!event:` 依赖协议 |
| `parser-libraries.md` | **解析库调研**（2026-11-07）：jomini 双子星（同一作者 Rust+WASM）、官方语法陷阱清单对 cw.py 反向测验（三处跨游戏写法缺口当日修复）、陈旧项处置 |
| `ai-agent-tools.md` | **AI agent 工具调研**（2026-11-07）：RHoiScribe 深读（37 工具/45 条约束/66 TOML）、Fostanico 置信分级与 baseline 去重、低星快评、三个最高优先差距 |
| `standalone-tools-analysis.md` | **独立工具调研**（2026-11-07）：收录/借鉴/舍弃三档处置——MD focus 工具规则码、khoeos 标记保护、Irony 对象级冲突算法、hoi4treesnap 预览升级路线、舍弃清单理由在案 |
| `md-repo-analysis.md` | **MD 官方仓解剖**（2026-11-07）：.gui 编写层专题——字段级统计（极简字段集/定位三轨/100%% 混用）、同名覆盖 1101 窗口的「保名三改」模式、legacy_lazy_load 性能惯例、5 条可吸收校验规则 |
| `kr-repo-analysis.md` | **KR 官方仓解剖**（2026-11-07）：与工坊 md5 级一致（工坊深读即权威）、57 条 replace_path 清单、portraits 三层池、64 个 0 字节 .gfx 空文件清除技法、GFX 尺寸规格实测、素材包与发版工作流处置 |

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

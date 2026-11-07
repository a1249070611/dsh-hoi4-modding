---
title: AI Agent 工具调研：RHoiScribe 深读与同赛道全景
domain: 93_ecosystem
scope: tooling
verified_on: 8 个仓库逐一克隆核录（全部一年内活跃）
verified_at: 2026-11-07
source: czxieddan/RHoiScribe（27★，AGPL-3.0，Rust）源码精读 + Fostanico/hoi4-ai-modding-skills 等 7 个同类
---

# AI Agent 工具调研：RHoiScribe 深读与同赛道全景

> 2026 年「AI 辅助 HOI4 modding」赛道集中出现了一批工具。逐一核录后：
> **没有第二个项目同时做「机器校验 + 原版实证知识库 + 错题本」**，但
> RHoiScribe 在「agent 行为协议」上、Fostanico 在「置信分级/去重」上
> 各有一块我们该抄的拼图。

## 1. RHoiScribe：我们最直接的镜像（深读）

37 个 MCP 工具 + 6 个结构化 prompt（约 45 条约束）+ 66 个知识 TOML
（`include_str!` 编译进二进制，运行时零网络）+ CWTools CWT 规则按固定
rev 编译内嵌（用的还是 MillenniumDawn fork）。AGPL-3.0（引用其**代码**
需同许可；本文只研究设计，不复制代码）。

### 1.1 五类问题的防护设计（提示词资产，`src/prompts/mod.rs`）

| 我们共同面对的问题 | 它的做法 |
|---|---|
| 重复搜索 | 硬约束「先用本地知识资源再网搜」；SKILL.md 要求先 read-resource 再依赖记忆 |
| 过时假设 | 优先级链「用户请求 > 工作区实测约定 > 内置资源 > 官方默认」；CWT 规则钉 git rev 并暴露 revision 元数据；知识条目带 source_refs |
| 不安全路径 | 写文件强制 `dry_run` + `output_root` 必填；编辑限定 workspace 树内；稀疏项目先 setup（dry_run）再写 |
| loc 编码 | 生成工具内置 BOM 强制 + 文件名后缀归一；repair 统一规则（localisation/** 必须 BOM，其余 txt 无） |
| 看着对不加载 | CWT schema 诊断 + validate_hoi4_project 红黄绿 + **收尾硬约束「改过文件必须 validate 才算完成」**；写作前先 scan_unique_identifiers 查重（create/reference 双意图） |

### 1.2 逐能力对照（结论：互补大于重叠）

| 能力 | RHoiScribe | 本插件 |
|---|---|---|
| 解析/校验 | cwtools 规则引擎（schema 级） | 自研宽容解析 + 8 校验器 |
| **诊断解释** | **explain_hoi4_diagnostic 专用工具** | ❌ 空档 |
| 知识库 | 66 TOML 手精选 | ✅ 运行时索引，6 万+ 实例符号 |
| **错题本** | ❌（审计日志 ≠ 错误回灌） | ✅ 独家 |
| agent 规范 | 45 条约束（最强项） | 有，写法可升级 |
| 真实启动游戏/预检 | 有 | 无 |
| 偏好持久化（global/mod 两级） | 有 | 无 |
| 环境发现（Steam/launcher-settings） | 有 | 有（find_game_dir） |

### 1.3 值得照抄（按性价比）

1. **两段式写盘协议**：dry_run 默认 + output_root 必填 + approved 才落盘
   ——我们的写盘工具（scaffold/fix_localisation）可加同一协议；
2. **explain 工具**：诊断码 → 含义/成因/修法/相关工具——我们的 issues 加
   稳定 code 字段后，explain 可由错题本直接驱动；
3. **收尾硬约束**：「改过文件必须 validate」写进 agents/kiant-hoi4-modder.md
   （第二铁律的强化措辞）；
4. **优先级链 + 显式 surface assumptions** 写进 agent 规范；
5. 骨架生成器 → 命名块编辑器的分工（防整文件重生成）；纯对话片段走内存
   虚拟路径校验（不落盘）。

## 2. Fostanico/hoi4-ai-modding-skills（12★，活跃）

三技能按任务分道（content-builder / pdx-modding / review-debug），每技能
SKILL.md 写明互相路由边界。**Mod Doctor** 最扎实：

- **confirmed（静态实见）vs lead（需运行时证据）两级置信**——可直接用于
  我们校验器输出的分级文案；
- **稳定指纹（code+归一化文件+消息）baseline 对比**：只报新增问题，
  行号漂移不算新债；**带过期日的抑制策略文件**（过期自动失效并报
  EXPIRED_SUPPRESSION）——错题本「已知问题不再重复报」机制的正解；
- 「车道路由」：按症状选最便宜的只读车道，「小改不跑全量校验」——
  AI 配额比例原则，可写进我们的 agent 规范；
- 解读边界明言「孤儿定义可能是公开 API；静态引用 ≠ 运行时证明」。

## 3. 低星快评（独家点提取）

| 仓库 | 独家价值 | 处置 |
|---|---|---|
| RohrReich/hoi4-claude-modding-template | script_docs.py 直读游戏 `documentation/`（与本插件 DOC_KINDS 同思路——已实现） | 收录其「版本精确权威」提法 |
| postigodev/hoi4-agent-skill | `examples/broken-cases/`（带失败机理的反例回归用例）+ `evals/trigger-evals.json` | 收录：反例集可进错题本冷启动 |
| npc-han/hoi4-skills | 「CTD/error.log/静默失败」三失败模式判定表 + 中文社区 MIO 译文语料 | 借鉴判定表 |
| cyberlieflife/hoi4-modding | 原版数据速查表 + 改前备份规则 | 借鉴 |
| bjafl/hoi4-claude-skill | description eval 调优方法论（技能触发准确率优化） | 借鉴方法论，主体不收录（玩法问答错位） |
| frostbite4575/hoi4-scenario-generator | 存档编辑领域，8 个月未更新 | **舍弃**（领域错位 + 不活跃） |

## 4. 行动结论

**三个最高优先差距**（对照后的真空白）：

1. **诊断 code 字段**：issues 加稳定 code（如 `LOC_MISSING_KEY`），是
   explain 工具、baseline 去重、SARIF 导出的共同地基；
2. **两段式写盘**：dry_run + approved 协议覆盖 scaffold/fix_localisation；
3. **agent 规范补三条**：优先级链、车道路由（配额比例）、收尾 validate 硬约束。

**同赛道格局**：RHoiScribe（协议强/知识薄）、UC（工具多/不可审计）、
本插件（校验+知识+错题本，独家）；三者互证「AI 辅助 modding 的难点不在
生成，在**验证与回灌**」——错题本路线持续加码。

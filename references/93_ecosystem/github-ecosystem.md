---
title: GitHub 生态调研：hoi4 相关 2788 个仓库的分类图谱
domain: 93_ecosystem
scope: tooling
verified_on: GitHub Search API（q=hoi4，total 2788，按 star 取头部 ~120 个逐一核录）
verified_at: 2026-11-07
source: github.com 检索（gh api search/repositories），星数/语言/活跃度均为当日实测
---

# GitHub 生态调研：hoi4 相关仓库图谱（2026-11）

> 检索方法：`search/repositories?q=hoi4` 共 2788 个结果；star 头部逐个核录，
> 长尾（≤6★）以 mod/翻译仓库为主仅归类不逐个展开。每条注明对本插件的意义。
> ⚠️ 星数与活跃度随时变化，引用时以实时检索为准；**星数不等于质量**——
> 生态位比热度重要（见 A 类四个插件的装机量与星数倒挂）。

## A. IDE 插件 / 语言服务（本插件最近的同类）

| 项目 | 星/装机 | 技术 | 一句话定位 |
|---|---|---|---|
| [cwtools/cwtools](https://github.com/cwtools/cwtools) | — | F# | Paradox 语言服务事实标准，`.cwt` 规则 DSL；详见 [cwtools-analysis.md](cwtools-analysis.md) |
| [herbix/hoi4modutilities](https://github.com/herbix/hoi4modutilities) | 114 | TS | VS Code 工具集（预览/校验/树可视化） |
| [TheCascadian/HOI4ModernUtils](https://github.com/TheCascadian/HOI4ModernUtils) | 130 装机 | TS | **上者的 fork**，重做世界地图编辑器（省份画笔/建州/重编号，WebGL2） |
| [emberglazee/hearts-of-modding](https://github.com/emberglazee/hearts-of-modding) | 509 装机 | Rust LSP | CWTools 启发的独立重写：补全/校验/definition.csv 校验 |
| [OlanderIAO/HOI4-Modding-Tools-Extension-for-VSC](https://github.com/OlanderIAO/HOI4-Modding-Tools-Extension-for-VSC) | 26 / **2861 装机** | TS+MCP | 全家桶可视化编辑器 + 装备/战斗分析器 + **200+ MCP 工具**；市场名 UC-ModdingUtilities.hoi4-modding-tools |
| MillenniumDawn/cwtools-vscode | 3 | Rust | **已非 fork——"CWTools MD Edition"完全重写**（扩展 + Rust 引擎 + 独立 `cwtools` CLI，2026-11-07 仍在活跃推送），值得盯其 CLI 形态 |
| LiefLife/HOI4-Code-Studio | 5 | Rust+Vue3 | Tauri 桌面版 HOI4 代码 IDE（2026-02 后低活跃，观察） |
| zhangxiaoyu66666/hoi4skill | 37 | Rust | **中文优先的 mod 创作工具，哲学与本插件逐字同源**：「AI 不直接手写未经验证的游戏代码，所有 effect/trigger/modifier/sprite/tag/technology/scope 引用必须来自本机索引，查不到就报错并生成修复上下文」——Rust CLI + Skill 包形态，`validate --strict-code-index` / `semantic-repair-search` 值得对照 |

**派生关系**：`herbix → TheCascadian`（fork，已 diverged：ahead 90/behind 108）；`cwtools → MD`（原 fork 已成独立重写）、`→ hearts-of-modding`（思想重写）。星数与装机量倒挂（UC 26★/2861 装机）说明 **modder 群体在市场里选工具，不看 GitHub**。

**A 类深读后的补充结论（2026-11-07，四篇解剖已归档）**：herbix 上游实为「预览器+索引器」而非语言服务（无补全/悬停/跳转）；四家中只有 CWTools 与 hearts-of-modding 做了 scope 层校验，且两家都默认关闭或实验性——**scope 链校验是全生态的未竟之地**，我们的 push_scope/links 知识（cwtools-analysis.md §5）进入门槛最低。

## B. AI Agent 工具（与我们同赛道，2026 年集中出现）

| 项目 | 星 | 说明 |
|---|---|---|
| [czxieddan/RHoiScribe](https://github.com/czxieddan/RHoiScribe) | 27 | **Rust 本地 MCP 服务器 + SKILL**；自述要解决的痛点与本插件逐条同源（重复搜索/过时假设/不安全路径/loc 编码/"看着对进游戏不加载"）——最直接的同类，值得解剖对照 |
| Fostanico/hoi4-ai-modding-skills | 12 | Agent skills + Mod Doctor 诊断/回归 |
| cyberlieflife/hoi4-modding | 4 | Claude Code/Codex 的 skill pack |
| npc-han/hoi4-skills | 1 | 钢4 MOD 技能体系（中文） |
| 其余 hoi4-agent-skill / hoi4-claude-skill 等 | ≤1 | 零星模板 |

**判断**：AI 辅助 HOI4 modding 在 2026 年已是显学，但**没有一个项目同时做
「机器校验 + 原版实证知识库 + 错题本」**——有的偏 skill 提示词，有的偏文件
操作。本插件的差异化位置仍然成立，但校验器对齐（CWTools 全家桶文档、
loc 命令校验）要加快，护城河在知识不在接口。

## C. 解析库 / 格式工具（可借鉴的实现）

`rakaly/jomini`（Rust，99★，高性能 parser）、`nickbabcock/jomini`（TS，96★）、
`QAston/clausewitz-antlr-grammar`（ANTLR 语法，规则文件形态）、
`grgrzybek/hoi4-db`（Java）、`MattMcFarland/hoi4-txt-parser`（JS）。
→ 我们的自写宽容解析器在「坏文件不崩」上与各家取舍一致；jomini 的性能
手法（零拷贝/位并行）值得将来性能轮参考。

## D. 独立工具

| 项目 | 星 | 价值 |
|---|---|---|
| bcssov/IronyModManager | 529 | 模组管理器（多 Paradox 游戏）；冲突合并思路 |
| crschnick/pdx_unlimiter | 446 | 存档工具箱（快照/编辑/回放） |
| ScottyThePilot/hoi4_province_editor | 40（归档） | 地图编辑器（Rust） |
| malashin/hoi4treesnap | 35 | 国策树截图渲染——预览工具的图像输出参照 |
| Yard1/HoI4ModdingPythonScripts | 36 | Yard1 的 Python 脚本集（他也是 CWTools 图表框架作者） |
| Flaxbeard/hoi4-parliament-diagram + scripted-graphs | 40/30 | scripted GUI 图表生成器（TNO 经济视图署名的框架出处） |
| textGamex/HOI_Error_Tools | 5 | C# 钢4 代码分析（中文界面） |
| Magolor/hoi4dev | 6 | Python mod 开发辅助 |
| khoeos/paradox-translation-toolkit | 30 | Paradox 本地化管理（TS） |
| NicolasGrosjean/Translate_helper | 33 | Java 翻译辅助 |
| MillenniumDawn/focus-tree-creation-tool | 23 | 国策树生成器（Python） |
| jordsta95/hoi4-national-focus-maker / decision-maker | 21/— | Web 版生成器（PHP/JS） |

## E. 大型 mod 官方仓库 / 素材

`MillenniumDawn/Millennium-Dawn`（157★）、`Kaiserreich/Kaiserreich-HOI4`
（60★）、`Globvs/Ultimate-HOI4-GFX`（239★，400+ 国策图标素材）、
`Economic-Crisis/Public-releases`、翻译类（KR 韩化 26★ 等）。
→ 官方仓库直接进我们 kb 的索引源（`sources.json` 加一条 mod 路径即可）。

## F. 剔除项（检索噪声）

`hoi4d/*` 系列（HOI4D 是计算机视觉 4D 数据集，与游戏无关）、
`hookey`/DLC unlocker 类（灰产工具，不纳入知识库）、纯存档分享仓库。

## 对本插件的三个行动结论

1. **校验对齐 CWTools 的文档全家桶**（已做：`DOC_KINDS` 扩展，+433 符号）；
   loc 命令表与 links 表待第二轮。
2. **观察 RHoiScribe 与 UC 的 MCP 工具面**：他们的「200+ 工具」走广度路线
   （编辑器操作暴露成 MCP）；我们的 20 个工具走深度路线（校验/知识）。
   差异成立，但 RHoiScribe 的「防重复搜索/防过时假设」提示词设计值得读。
3. **生态关系写进文档**：fork/启发关系图已在本文件 A 类，后续版本调研
   直接增补，不再从头检索。

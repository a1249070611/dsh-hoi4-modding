---
title: 工程解剖：CWTools（Paradox Language Services）
domain: 93_ecosystem
scope: tooling
verified_on: cwtools-vscode 0.10.31 + cwtools-hoi4-config master（2026-09-18）
verified_at: 2026-11-07
source: 用户提供的 tboby.cwtools-vscode-0.10.31.vsix 逐文件解包 + cwtools/cwtools 引擎源码树 + cwtools-hoi4-config 配置仓库
---

# 工程解剖：CWTools（Paradox Language Services）

> CWTools 是 Paradox 脚本语言服务的事实标准（VS Code 市场"Paradox Language
> Services"），本插件在「解析器 + 校验器 + 知识库」上与它同构而形态不同
> （MCP 服务 vs 编辑器 LSP）。本文记录其架构与知识组织，全部结论有出处；
> 两条MIT 许可（引擎 © 2018 tboby，配置仓库同），可借鉴可引用。

## 1. 架构：薄客户端 + F# 语言服务器 + 独立配置仓库

```
vsix 0.10.31（202 MB，706 文件）
├─ bin/client/*.js          VS Code 薄壳：LSP 客户端 + webview 图面板
└─ bin/server/{win,linux,osx}-x64/
   └─ CWTools Server.dll    F# 编译的 .NET LSP 服务器（真正的引擎）
      CWTools.dll 2.2MB     解析/规则/校验核心（MIT）

游戏知识不在包里！运行时从 github.com/cwtools/cwtools-hoi4-config（2MB，
Python 仓库实为 .cwt 数据）按游戏拉取——引擎与知识分离，版本各自演进。
```

对照本插件：MCP stdio 服务器（纯 Python）+ 知识库（运行时索引原版）。
**同一条「引擎小、知识外置」的路线**；差别在他们的知识是手工维护 + 上游
script_docs 双轨，我们的知识是全自动索引 + 实例符号。

## 2. `.cwt` 规则 DSL：声明式的作用域知识

规则文件长这样（`Config/scopes.cwt`）：

```text
## scope = country
## push_scope = state
alias[trigger:capital_scope] = { alias_name[trigger] = alias_match_left[trigger] }
```

要点：

- **`## scope =` / `## push_scope =` 注释即元数据**——把「这个 trigger 在
  country 里可用、进入后 scope 变成 state」声明在条目旁，引擎据此做作用域
  流转校验。我们的 kb 在 `extra` 里存了 `Supported Scopes`，但**没有
  push_scope（作用域流转）维度**——做 scope 链校验（如
  `[State.Owner.Capital.GetTag]` 是否合法）时的差一块拼图。
- **DLC 条件配置拆文件**：`effects.cwt`（113KB 主文件）+ `effects_bba/gtd/
  nsb/aat/ncns/toa/taog/goe.cwt`（每款 DLC 一个），按玩家启用情况叠加——
  比单文件 + 内部条件干净。
- alias 类型系统：`alias[trigger:X]` / `alias_name[trigger]` /
  `alias_match_left[effect]` 等类型标注让规则可被类型检查。

## 3. 知识对账：与本插件 kb 逐维比对（2026-11-07 实测）

CWTools 的 `script_documentation.json`（767KB，源自游戏控制台 `script_docs`
命令）与本插件对原版 `documentation/*.md` 的索引：

| 维度 | CWTools | 本插件（对账前） | 结论 |
|---|---|---|---|
| effects | 553 | 553 | **逐条一致**（同源） |
| triggers | 598 | 596 | 他们多 2 条=手维护 .cwt 增量 |
| modifiers | 764 | 722 | 他们多 42 条=手维护 .cwt（temp_modifiers + DLC 项） |
| math functions | 30 | **0（已补齐 → 30）** | 原版 `script_math_functions.md` 一直都在，本插件此前只收三个文档名，其余静默漏收 |
| loc objects | 15 | **0（已补齐 → 15）** | 同上 |
| loc formatters | 9 | **0（已补齐 → 8）** | 他们多 1 条 = `<scripted_loc>` 占位 |
| console commands | **2** | **0（已补齐 → 375）** | 反超：他们漏了这个维度 |
| collection input/operator | 6/7 | 0/4 | 部分条目含 NAME 占位符，非干净标识符 |
| **实例符号**（sprite/focus/event/idea/character/gui…） | 0 | **6 万+** | 他们的知识止于文档层；实例层是我们独有的差异化 |

本次整合动作：`kb.py` 的 `_extract_engine_docs` 从「三个文件名白名单」扩为
`DOC_KINDS` 全表（strict/loose/token 三种名称口径；strict 保 553/596/722
三个基准数字不漂），重建索引后新增 433 个符号，`kiant_hoi4_kb_symbol
name=Ace` 可直接回答 loc_object 问题。

## 4. 引擎校验体系（源码树定位）

`cwtools/cwtools` 引擎的校验模块分工：

```
CWTools/Rules/RulesParser.fs        .cwt 规则 DSL 的解析器
CWTools/Rules/RulesLoader.fs        规则加载/合并（主配置 + DLC 叠加）
CWTools/Rules/RuleValidationService.fs  按规则校验节点
CWTools/Rules/FieldValidators.fs    字段级校验器
CWTools/Game/RulesManager.fs        每游戏规则装配
CWTools/Game/ValidationManager.fs   校验总调度
CWTools/Validation/LocalisationValidation.fs   本地化校验
CWTools/Validation/LocalisationString.fs       loc 字符串内的命令/颜色码校验
```

可借鉴的分层：**规则解析 → 规则装配 → 节点校验 → 字段校验** 四段式；
本地化字符串单独一个校验器（命令/颜色码），与我们 `scan_localisation`
的分层一致。

## 5. 值得后续吸收的三件（按性价比排序）

1. **loc 命令清单进校验**：`Config/localisation.cwt` 维护了 ~80 个 `Get*`
   命令及适用 scope（GetDateText/GetNameDef/GetTokenKey/…/GetBopTrendTexticon），
   MIT 可直接引用（注出处）。我们已有 loc_objects（15 个对象），补上命令表
   就能做「`[Root.GetXxx]` 这个命令存在吗」的校验——错题本里
   「loc 里写错命令名显示原样文字」一类问题可以机器判定。
2. **links.cwt 的数据链知识**：`owner = { output_scope = country,
   input_scopes = { state unit_leader … } }`——事件目标链每跳的输入/输出
   scope 全表。做 scope 链校验的权威数据源，同样是手维护 + script_docs 双轨。
3. **DLC 条件配置的组织法**：如果我们以后维护手写规则（例如补那 42 个
   modifier），按 DLC 拆文件叠加，不要塞进单一文件。

## 5.5 客户端命令与事件类型图（vsix 实测补全）

客户端 15 条命令暴露了它的功能面：`outputerrors`（报错输出）、
`genlocall`（**批量生成本地化骨架**——我们 scaffold 的 loc 部分同类能力）、
`reloadrulesconfig` / `debugrules`（.cwt 热重载与调试）、`cacheVanilla`
（原版缓存）、`pretriggerAllFiles`（全量预触发校验）、`startcustomgame`
（带 mod 启动游戏）、`showGraph` 系六条（**事件/链条图面板**：从 JSON
建图、导出图片、控深度）。事件校验配置 `events.cwt` 用类型图描述：
5 种事件 subtype（country/state/news/unit_leader/operative_leader_event，
与本插件 `EVENT_KINDS` 一一对应）各带 `push_scope`，外加
`subtype[hidden]`/`only_if_not = hidden` 的可见性子类型——事件断链、
hidden 事件的选项检查等规则由此驱动。

`effects.cwt` 的类型系统（手维护 280 个 effect 富签名 + 其余 script_docs
生成兜底的双轨制）：值类型词表含 enum/int/scope/bool/variable_field/
value_set/localisation/single_alias_right[bindable_loc] 等，574 个
`## cardinality` 注解标可选性，同一 effect 可多签名重载
（如 `set_capital` 两种写法）。**这是四个插件里最深的字段级类型系统**，
我们 kb 的 name+scopes 是它的子集；全量对齐不划算，但 `cardinality`
（可选/必填）值得进未来手写规则的 schema。

## 6. 设置面（客户端侧）给我们的启示

`cwtools.errors.vanilla`（原版也报错，默认关）、`cwtools.errors.ignore`/
`ignorefiles`（README.txt 等credits 文件白名单）、`localisation.languages`
多语选择——「白名单放行非代码文件」「原版语料开关」这两个设计本插件的
校验器降级逻辑里都有对应物（`info` 分级 / loc 覆盖率子模组判定），互相印证。

## 7. 相关项目关系图（2026-11 实测）

```
cwtools/cwtools (F# 引擎, MIT) ──┬── cwtools-vscode（官方编辑器壳）
                                 ├── MillenniumDawn/cwtools-vscode（MD 团队 fork，Rust）
                                 └── 启发 → emberglaze/hearts-of-modding（Rust 独立重写）
cwtools-hoi4-config (.cwt 数据)  ← 运行时拉取，游戏知识唯一真源
```

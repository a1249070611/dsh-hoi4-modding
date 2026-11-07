---
title: 工程解剖：hoi4modutilities 与 HOI4ModernUtils（fork 对比）
domain: 93_ecosystem
scope: tooling
verified_on: herbix/hoi4modutilities 0.18.1（约 2 万行 TS）+ TheCascadian/HOI4ModernUtils 0.4.14（diverged fork：ahead 90 / behind 108）
verified_at: 2026-11-07
source: 双仓库源码逐模块精读（fork 部分经 GitHub API 取关键文件）
---

# 工程解剖：hoi4modutilities 与 HOI4ModernUtils（fork 对比）

> 两者关系早已不是「原版 + 地图编辑器」：fork ahead 90 / behind 108，
> 靠 changelog 手挑 "Ported from upstream" 双向漂移。

## 1. 先纠偏：上游不是语言服务器

全库无 CompletionItem/Hover/Definition Provider，package.json 仅 5 个命令
（src/constants.ts:19-25）。它是「**预览器 + 索引器**」：7 个 webview 预览
（focustree/gfx/technology/worldmap/event/gui/mio）按文件类型路由
（previewmanager.ts:38-46）。

## 2. 解析器：带 token 坐标的自写递归下降（但零容错）

- token 四类正则 + y-sticky 驱动（src/hoiformat/hoiparser.ts:37-42）；
- AST **保留每个 name/operator/value 的 Token 起止位置**——webview 点击
  跳回源文件的基础；
- `name{...}` 归一为 `name=`（:213）、支持尾逗号/分号/valueAttachment；
- **坏 token 直接 throw，整个文件作废**（:63）——mod 作者最常见的漏括号
  场景下预览全挂。**校验器必须做带错误恢复的部分解析，不能学它**
  （这正是本插件 cw.py 宽容设计 + 累积诊断的立论证据，反向验证）。

## 3. 数据加载：mod → DLC zip → 原版，replace_paths 感知

解析 .mod 描述符取 replace_paths；文件顺序 = mod 工作区 → replace_path
命中的目录跳过 → DLC zip（adm-zip）→ 原版 installPath（自定义
`hoi4installpath` scheme，src/util/fileloader.ts:44-120）。5 类索引
（gfx/sharedfocus/localisation/event/gui）分「globalIndex=原版+DLC 落盘
缓存、按 mtime 失效（indexbase.ts:17-60）」与「workspaceIndex=mod 文档事件
防抖增量（indexmanager.ts:99-112）」两层。

**可抄**：globalIndex 落盘缓存 + mtime 失效——我们 kb 已有（SQLite 即缓存），
确认覆盖 DLC zip 内文件即可。

## 4. 校验清单（数据源=原版文件，非硬编码清单）

- **focus tree**（上游）：重复 id、缺 id、shared focus 解析失败、
  `relative_position_id` 自引用/成环（validateRelativePositionId，:561）；
- **fork 补成正式诊断**（validation.ts:24）：前置缺失/自引/重复、互斥缺失/
  自引、前置环、**坐标重叠、不可达节点** → 发布进 VS Code Problems 面板
  （diagnostics.ts:17,100），纯函数无 IO——**"校验即纯函数"与我们
  validators 的形态一致**；
- **world map 57 处 warnings**：definition.csv id 重复、**颜色冲突**、
  def 有行但图上无像素、图有色但 def 缺行（provincemap.ts:172-241）、
  adjacencies 引用不存在省份、state/strategicregion/supplyarea 结构缺失、
  省份最小尺寸 8 像素（provincebmp.ts:192）；
- 语义层是硬编码知识：**scope 转移表约百条**（scope.ts:150-260，带
  condition/effect 标志与 from/to scope 类型）、generalConditions 白名单、
  标签 `ABC`→country / `ABC_`→character / `mio:` `sp:` 前缀规则（:21-48）。

## 5. fork 的地图编辑器增量与安全措施

- WebGL2 可选渲染器：每省顶点缓冲 + 每帧只更颜色 buffer、3 个 draw call
  处理经度 wrap（webgl2renderer.ts:177-302）；README 自承是 microbenchmark
  非实测帧时，且非逐像素一致、默认关闭——**重实现渲染必须有保真对照基线**；
- 编辑工具：笔刷/油漆桶/套索/传送魔杖 + 四叉树/像素哈希暂存；
- **危险操作安全措施（最值得学的一节）**：
  - **多文件写事务**：`applyEntriesWithRollback`（transactionjournal.ts:16）
    先 capture 全部旧内容，逐条 apply，失败按逆序回滚，回滚再失败抛
    "rollback incomplete"（70 行，可直接移植到 MCP 写工具）；
  - **ID 上限守卫**：maxProvinceId = provinces.bmp 像素数/8（maplimits.ts:13-24）；
  - reindex 是纯文本替换器，只映射正整数、未映射 id 直接抛错；
    ⚠️ 但块级重写时对未知数字「删除」而非报错（reindex.ts:62-90）——
    **比报错更危险**，文档自己要求人工复查外部引用；
  - 危险动作强制确认 UI + 写前 git 提交要求；undo 只管会话内，恢复靠版本控制；
  - `scanAndLogErrors` 全量扫描出时间戳报告（worldmaperrorscan.ts:23）。

## 6. 依赖协议：`#!event:` 头注释

`scanreferences` 对 event 文件 BFS 遍历 immediate/options 子事件链
（dependency.ts:64-110），把所需 event/localisation 文件以
`#!event:path` 头注释写回（:115-125），loader 按它加载——**自造的机器可读
依赖声明**，与 RT56 的 `#!gfx:` 协议同思路（见 mod-maintenance-engineering.md
§4），可作为我们增量校验的输入信号。

## 7. 对本插件的可吸收点（按成本排序）

| 点 | 成本 | 说明 |
|---|---|---|
| focus tree 语义校验（前置/互斥/环/坐标/可达） | **低** | 纯图算法，**校验器矩阵最值钱的缺口**；我们 preview 已解算 relative_position_id，数据现成 |
| province id ≤ 像素/8 上限 | 一行 | 直接抄进（将来的）地图校验 |
| 地图文本侧一致性（def↔adjacency↔state 三方对账、颜色冲突） | 低 | bmp 像素级中等成本，可先做 def/图两档 |
| `#!event:` / `#!gfx:` 头注释协议进 kb | 低 | 机器可读依赖，增量校验的输入信号 |
| scope 转移表（~百条）抄进知识库 | 低 | 先做「scope 类型不匹配」静态检查 |
| 事务化多文件写 + 逆序回滚 | 低 | 与 UC 的 dry_run+备份互补，写工具族的地基 |
| globalIndex 落盘缓存 + mtime 失效 | 低 | 确认 DLC zip 覆盖即可 |
| WebGL 渲染 / GUI widget 重建 / DDS 像素解码 / 国家合并工具 | 不值 | GUI 重建 542 行 schema 对齐游戏版本，维护无底洞 |

## 8. 坏味道

- 解析器零容错（见 §2，反例教材）；
- scope 表按 1.15 手工维护，白名单漏项即静默漏检（硬编码知识的通病，
  与 hearts-of-modding 同病）；
- fork 双向漂移、性能数字是 microbenchmark 非实测；
- 上游校验全藏 webview 里、无 Problems 面板（"校验即副作用"模式，
  **MCP 天然就是 Problems 面板**——我们的形态优势）；
- addmapitem 直接改内存 statesCount（addmapitem.ts:38），磁盘/内存可能不一致。

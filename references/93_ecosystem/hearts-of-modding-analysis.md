---
title: 工程解剖：hearts-of-modding（Rust LSP）
domain: 93_ecosystem
scope: tooling
verified_on: emberglazee/hearts-of-modding v0.32.1（main @ 2026-11-05）
verified_at: 2026-11-07
source: 仓库源码逐模块精读（约 5.9 万行 Rust，646 个测试）
---

# 工程解剖：hearts-of-modding（Rust LSP）

> 自述「灵感来自 CWTools」的独立重写。市场装机 509。**价值最高的部分不是
> 功能（大体与 CWTools 重合），而是它把校验规则的「实证校准」做成了流程**。

## 1. 架构：Rust LSP + 分层 VFS + 40 个注册表

- **索引**：约 40 个 `DashMap<InternedStr, LayeredValue<V>>` 注册表
  （`server/src/data/scanner_data.rs:79-100`），键全部 interning 省内存。
- **LayeredValue 分层覆盖**（:81-88）：entry[0]=vanilla，末位=活动 mod——
  每个键保留全部层，删除 mod 文件只删该层、底层自动复活
  （`incremental_scanner.rs:2028`）。文件叠加用 `FileOverlay`
  （相对路径→最高优先级文件胜出，`file_overlay.rs:25`）。
- **VFS 根栈**：gamePath（最低）→ 依赖 mod（解析 Paradox mod registry +
  descriptor 的 dependencies/replace_path，`lsp/handler.rs:264-330`）→
  工作区。我们 kb 的多源叠加是「源级」，它做到了「文件级」，两层都活着。
- 增量：did_change 从 AST 即时更新、did_save 全量重扫（:831/867）。

## 2. 诊断码体系：HOM0001–9001 共 57 码（`validation/advanced_validation.rs`）

按数据源分四类，这个分法可以直接抄进我们的文档：

| 类 | 数据源 | 代表 |
|---|---|---|
| 语法/环境 | 纯解析 | 双赋值、游离 `}`、**loc 双 BOM（专测 LLM 生成文件的高频雷）**、**非 ASCII 文件名破坏 MP 校验和**、events 子目录不加载 |
| 未知实体 | 扫描的原版+mod 实例 | unknown tag/trait/ideology/sprite/building/terrain/province/idea/focus filter… |
| 上限 | 常量或原版文件 | 角色技能 9 上限（characters.rs:20）、focus cost 引擎上限（focus_cost.rs:55）、**建筑 max_level 读原版 common/buildings** |
| 交叉一致性 | 原版文件互查 | **HOM2001–2009 地图七连**：VP 省不在 state 省表、海省入 state、两 state 争省、coastal_only 建筑在内陆省、空 state、state 引用不存在的省、两战略区争省 |

事件检查 HOM3008–3023 全套（namespace/ID/重复/选项缺名/缺 title+desc/缺
ai_chance/图片 sprite/断链引用），决议 HOM5006–5009——与我们 validators.py
的覆盖高度重叠，可逐条 diff 找盲区。

## 3. 实证校准法（最值得学的工作流）

- `allowed = ` 原版使用 6315 次 → 8516 条误报 → 把「透明列表」拆出来单独
  处理（CHANGELOG v0.32.0）；
- 决议「双 cost」告警先扫 4125 个原版决议再定阈值：仅 cost>0 时告警
  （decisions.rs:341-360）；
- scope 校准循环仍在进行（v0.32.1 刚修 history/countries 初始 scope），
  所以 scope 校验**默认关闭**（config.rs:52）——「测不准就 opt-in」是诚实设计。

**这正是我们变异测试+原版自检（self_check 体检原版）的同款哲学**，
他们的补充是把「误报率数字」写进 CHANGELOG 作为规则上线依据。

## 4. Scope Validation（实验性，独立实现未复用 CWTools）

三件套：

1. `hoi4_data.json`（1.27MB 编译期嵌入）：596 triggers / **583 effects**
   （比原版文档 553 多 30 条，wiki 抓取补充）/ 722 modifiers——与我们对账
   数字呼应；schema 每实体含 `scopes.usage / pushes_scope /
   stack_behaviour(transparent|push|passthrough) / parameters{value_type}`；
2. `ScopeStack::resolve_entry_scope`（scope.rs:828）：透明块 → 特例 →
   push_scope → 硬编码关键字 → event_targets/链式指针 → 目录推断初始 scope
   （30+ 分支，initial_scope_for_uri:525）；
3. `rules/v2_scope.rs` 只查「已知且非全局」实体，带 5+ 个硬编码逃生特判。

**局限（README:83 与 AGENTS.md:199 自认）**：wiki 文档缺口 34%，参数表只能
additive 不能过滤；**没有全局「未知 trigger/effect」检查**——
`has_stabillity` 这类结构键拼错静默通过（我们 kb_symbol 可查的存在性校验
反而更强）。逃生舱是补丁摞补丁（v2_scope.rs:80-105）。

## 5. definition.csv / adjacencies.csv 校验

- definition.csv 解析出省份实体库供交叉引用与悬停（地形/海岸/类型），
  对 CSV 本身几乎无诊断（不做重复 ID/RGB 冲突）——**这是它的空白**；
- adjacencies.csv：列数/整数校验、三省 ID 须存在于 definition.csv、
  `type=sea` 且 through≤0 提示、rule 列须在 adjacency_rules.txt
  （backend.rs:2961-3200）。

## 6. 对本插件的可吸收点（按成本排序）

| 点 | 成本 | 说明 |
|---|---|---|
| loc 双 BOM / 非 ASCII 文件名检查 | 极低 | 我们 loc 检查补两条规则即可（AI 产出高频雷） |
| 地图交叉七连（HOM2001-2009） | 低 | 纯集合运算，补齐校验矩阵缺的地图维度 |
| loc 缺键降噪启发式（大小写/空格/版本后缀 `:0`-`:5`） | 低 | 我们的 missing_loc 已有类似，可逐条对照查漏 |
| 结构化诊断：稳定 code + fix payload | 低 | 我们的 issues 加 `code` 字段，agent 可自动修复 |
| 实证校准流程写入文档 | 低 | 校验器调阈值时照做，数字进 changelog |
| LayeredValue 文件级叠加 | 中 | kb 多源升级为文件级（replace 语义正确的关键） |
| hoi4_data.json 的 schema + 生成脚本 | 中 | `pushes_scope/stack_behaviour/value_type` 是 scope 链校验的拼图（与 CWTools push_scope 互补） |

## 7. 坏味道

- 无全局未知键检查（与 README 宣传不符）；UNKNOWN_TRIGGER 常量被复用作
  country tag/ability/sound 的码（country_tags.rs:128），语义漂移；
- 部分诊断无 code、部分用临时字符串；backend.rs 3864 行巨石；
- wiki 抓取链路脆弱（参考文档目录整个 gitignore），游戏版本更新需重跑
  Python 管线 + 重编译——数据驱动的 CWTools 路线在「跟版本」上更省。

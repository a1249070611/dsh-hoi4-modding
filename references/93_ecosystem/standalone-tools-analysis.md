---
title: 独立工具调研：收录 / 借鉴 / 舍弃三档处置
domain: 93_ecosystem
scope: tooling
verified_on: 9 个仓库逐一核录（2026-11-07）
verified_at: 2026-11-07
source: 源码精读（Irony 冲突模块 3888 行、MD focus 工具、khoeos 全仓、hoi4treesnap、Yard1 脚本全集、HOI_Error_Tools 规则表）
---

# 独立工具调研：收录 / 借鉴 / 舍弃

> 按任务纪律执行三档处置：**收录**（规则/数据进知识库与文档）、
> **借鉴**（设计思想记录，代码不引入）、**舍弃**（验证后确认无用或不兼容，
> 理由写明）。年份久 ≠ 舍弃——规则有独占价值的停更项目照样摘录
> （HOI_Error_Tools 2023 年停更，规则表全部收录）。

## 1. 收录

### 1.1 MillenniumDawn/focus-tree-creation-tool（23★，活跃）

- **校验规则码对照表**：broken_prereq / prereq_cycle / mutex / duplicate_name /
  gfx_missing / loc_missing / loc_missing_desc / relative_position_unresolved /
  empty_effects——与我们即将做的 focus 语义校验直接对照补差；其
  position_collision 白名单允许「不同树共享坐标」（`validate.py:225-240`）；
- **两段式导入**（drawio.py:1-11）：先 snap 到网格预览，用户确认后才真正
  build Focus 对象并消耗 ID——与 RHoiScribe 的 dry_run 协议异曲同工；
- **ExportPlan 冻结模式**（export_plan.py:14-21）：把「渲染+写盘」所需输入
  冻结成不可变 plan 再执行——预览/生成工具的工程范式；
- **899 行 parse→render→parse 等价性测试**（test_focus_tree_roundtrip.py）
  ——我们解析器回归测试的直接模板。

### 1.2 khoeos/paradox-translation-toolkit（30★，活跃）

- **标记保护正则**（parser/src/markup.ts:5）：单条 TOKEN_PATTERN 覆盖全部
  Paradox loc 标记（`$变量$`、`[命令]`、`£图标£`、`§颜色`、`@scope!`、
  `#格式;`/`#!`、`\n`）；机翻流程 mask→`{N}`占位→MT→restore，**恢复时
  残留/缺失占位符一律返回 null 拒收**——机翻安全门的参考实现；
- **serializer 不破坏格式**（serializer.ts:5-58）：BOM 保留、行尾风格保留、
  `KEY:0` 版本号、引号转义、尾注释保留——与 fix_localisation 同诉求；
- **跨 mod 覆盖图**（converter/src/coverage.ts:92-99）：按 .mod
  `dependencies=` 把汉化补丁的 key 归属到目标 mod，「补丁已覆盖的 key
  永不重复覆盖」；
- 字节预算 + 截断诊断（mod-keys.ts:27-56）防巨型 loc 拖垮扫描。

### 1.3 HOI_Error_Tools 规则表（5★，2023 停更；只摘规则不引代码）

20 条错误码里，我们错题本/校验器大概率缺的 **state/地图交叉项**：
ProvinceNotExistsInStateFile（province 在 state 的 provinces 列表但不在
definition.csv）、VictoryPointsFormatIsInvalid、StateCategoryNotExists、
EmptyProvincesNode、建筑/战略资源类型不存在、ResourcesNodeNotOnly
（资源应集中一个块）、跨文件重复 state id。
⚠️ 本体是 CWTools 的薄包装（CWToolsParser.cs），C# 部分无引用价值。

## 2. 借鉴（设计思想）

### 2.1 hoi4treesnap（35★，2022 停更）→ kiant_hoi4_preview 的升级路线图

1. **零自研布局**：直接吃 mod 作者写的 X/Y，只做负坐标归一——我们 preview
   同款哲学，别替作者排树；
2. **连线方向位掩码**：按子节点 X 相对父节点分左/正/右三支，每条边累计
   方向位得 11 种转角精灵；**实线=AND 前置、虚线=OR 前置**（`len(前置)>1
   → 虚线`）——这是游戏内视觉语义，我们的预览连线应遵循；
3. 互斥线只画同 Y 行、从左往右、中间有其他 focus 时跳过；宽度按 X 差分档；
4. 多边交汇处转角只画一次（drawnCoords 去重）；
5. **游戏级还原**：解析 nationalfocusview.gui 取容器坐标 + 游戏贴图多帧
   切片 + mod 路径逐级回退找贴图——README 自述「连改过的 GUI 也能还原」。
   这 5 条把 preview 从示意图升级为「伪游戏截图」。

### 2.2 IronyModManager（529★）→ list_overrides 的对象级升级

- **对象级索引**：每个顶层块 = IDefinition（TypeAndId = 定义类型+ID），
  冲突 = 同一 TypeAndId 出现在 ≥2 mod——**我们 list_overrides 是文件级，
  对象粒度才能报出「两个 mod 改了同一个 focus」**；
- 内容 SHA 去重：冲突方内容全同则不算冲突；同 TypeAndId 缓存防反复报；
- **依赖豁免**：冲突方在 descriptor `dependencies=` 里声明了对另一方的
  依赖 → 视为有意覆盖不报（我们报 override 时的降噪规则）；
- `existsInLastFile` 标注「该定义是否存在于最高优先 mod」（生效 vs 被压掉）；
- 空文件语义：mod 用空文件压制原文件 → 生成虚拟定义参与判定；
- 可合并类型：provider 声明 MergeType，冲突直接合并而非报冲突；
- IndexedDefinitions 多键并发索引 + Trie + LiteDatabase 持久化，10 万级秒查。

### 2.3 Yard1/HoI4ModdingPythonScripts（36★，2021 停更）——6 项思路入库

花括号深度定位 loc 键（深度 2 取 id、1-2 取 title/desc）、剥引号再数花括号
防字符串干扰、goals_shine 缺条目补全（gfx 校验器可加）、从 focus/idea 文件
反推缺失 spriteType、**tech 树→transfer_technology 生成时「互斥科技会被
无脑授予」的坑**（知识库条目）、definition.csv→分省着色图。

## 3. 舍弃（理由在案）

| 仓库 | 处置 | 理由 |
|---|---|---|
| pdx_unlimiter（446★，活跃） | 舍弃 | 面向玩家的存档管理/savescum，不面向 mod 开发；「快照+恢复」思想我们已有备份机制覆盖 |
| jordsta95 两个 Web 生成器（2018 停更 7 年） | 舍弃 | jQuery/PHP 表单，功能被 MD 工具与我们 scaffolder 完全覆盖 |
| HOI_Error_Tools 代码本体 | 舍弃（规则已摘） | CWTools 薄包装 + 3 年停更 |
| hoi4treesnap 代码本体 | 舍弃（算法已摘） | Go 独立 exe，以读真游戏文件为前提，不适合并进 Python MCP |
| Yard1 3 个一次性脚本 | 仅存档 | DH 部长转换/人力倍率/美国选举生成器，无通用价值 |

---
title: 工程解剖：Millennium Dawn 官方仓库（.gui 编写层专题）
domain: 93_ecosystem
scope: tooling
verified_on: MillenniumDawn/Millennium-Dawn HEAD=9b020ff（65,421 文件）+ 工坊 2.0.3 对照（本机 2777392649）
verified_at: 2026-11-07
source: interface 全量 465 文件清单级盘点 + 8 个最大/覆盖文件逐段精读 + 字段级 grep 统计（原版 132 gui 做基线对照）
---

# 工程解剖：Millennium Dawn 官方仓库（.gui 编写层专题）

> MD 是工坊界面代码量最大的 mod（interface 7998 个容器窗口 ≈ 原版 2037 的
> 4 倍；**同名覆盖原版窗口 1101 个 = 67% 的原版 UI 表面**，另有自建 1476 个
> ——两数据来自本插件独立统计，与仓库精读互证）。本篇回答：
> 大规模 .gui 怎么写、怎么覆盖原版、仓库怎么组织。

## 1. 仓库 vs 工坊版：仓库领先，属开发中 2.x

- 目录级：仓库 interface 465 文件（303 gui + 160 gfx）vs 工坊 445（288+155）；
  仓库独有 21 个（3 个 gdp_graph 拆分图表、5 个 *_profiles.gfx、UKR 系）；
  抽样 12 个同名文件：topbar/techtree/popup/unitview **完全一致**，
  economyview 仓库多 2100 行（新税制面板）——差异性质＝版本演进，
  **工坊是发布快照、仓库是活的开发树**（docs/ 503 文件的 Astro 文档站、
  .github/ 25 个 CI 文件、tools/ 437 个 Python 工具都在仓库侧）。
- `.gitignore` 明确排除 `*.psd`——PSD 源文件本地有、仓库无，发布链只走成品。

## 2. 组织结构

- 顶层：gfx（60,724 文件！其中 gfx/interface 34,055 张图）、common、events、
  history、interface、localisation、map、music、portraits、sound、tutorial、
  descriptions、resources（参考素材）、tools、docs、.github、.claude；
- 命名**三轨并存**：`MD_` 前缀（24 个顶层 .gui）、小写国别 `cze_/pol_`、
  国名 `Iran_/ENG_/GER_`；gfx 侧 `MD_` 与 `mdult_` 两套；还有一个
  `!MD_research_slots.gui`——**`!` 前缀魔法保证加载序最先**；
- .claude/ 内 10 个专职 agent + 24 个 skills + rules（含
  「改 GUI window_name/按钮名/sprite 名前必须 grep 三处引用」的明文规则）、
  validation_config.json 38KB 豁免清单、AGENTS.md 定 KISS/BLUF/每 PR 一条
  Changelog——**AI 工程化程度与 BICE 并列生态第一梯队**。

## 3. .gui 编写层（字段级 grep 全量统计）

### 3.1 元素频率（工坊实测）

containerWindowType 7,984 / iconType 6,600 / buttonType 2,562 /
instantTextboxType 1,956 / background 1,170 / gridboxType 304 /
checkboxType 41 / editBoxType 36 / scrollbarType 25。
**全库 0 次使用**：cornerStyle、iconSpriteType、clone、fontName、anchor——
规范里存在的字段，大规模实践证明可用极简字段集（写新面板不必碰它们）。

### 3.2 定位三轨混用（错位问题的根源地）

1. **绝对坐标** `position={x,y}` 19,959 处；负值 = 窗口藏屏外（配合
   scripted_gui 显隐，见 scripted-gui.md §13.2）；
2. **元素内 `Orientation`**：大写 1,833 vs 小写 467 **随机混用**——引擎不
   敏感（与原版自身混用互证），但团队规范应统一；
3. **窗口级 `origo`**（80 处，与 Orientation 配套）：居中可拖窗模板
   `Orientation=center + origo=center + moveable=yes`（gdp_graph_gdp.gui:7-9）；
4. 级联：窗口 `orientation=lower_left`、子容器 `center_up`，子元素坐标
   相对父级锚点（chi_scripted_gui.gui:61-92）；
5. **屏高百分比**：`100%%` 798 处 vs `100%` 3,215 处混用（引擎都认，历史
   包袱）；高级用法 `size={width=2300 height=975 min={width=100%% height=100%%}}`
   （countrytechtreeview.gui:54-57）。

### 3.3 惯例与技巧

- **每窗必带 `background={name="Background" quadTextureSprite=...}`**；
  同名 "Background" 是惯例（62 处/文件）；甚至有**同名双 background 叠放**
  做分层（MD_countrymissilesview.gui:30-37，可运行，属技巧非错误）；
- `alwaystransparent=yes` 4,025 处——图标/文本默认加（性能惯例）；
- `fixedsize=yes` 1,167→1,387（仓库新增趋势）；`context_aware_text` 13 处；
- 滑入动画窗：`show_position/show_animation_type=decelerated/
  hide_animation_type/animation_time`（MD_countrymissilesview.gui:22-25）；
- 按钮 `scale/rotation`（892/198 次）、`frame=` 882 次切多帧 sprite、
  `shortcut="shift+m"` 键盘快捷键；
- **@变量系统化**：新文件头部定义 @COMMITTEE_Y 等布局常量（11 文件 308 处）；
- 文本字体用原版家族（hoi_36header/18mbs/16mbs/20b/33、nsb_hoi_24header）。

### 3.4 .gfx 注册体系

spriteType 47,411 定义 / texturefile 49,813；**legacy_lazy_load 15,179 处
——子图形懒加载是性能标配**，仅 goals 主图显式 `legacy_lazy_load=no` 预载；
noOfFrames 1,786（subuniticons 单行紧凑 sprite sheet）；
corneredTileSpriteType 86；progressbartype 76（textureFile1/2 +
effectfile=gfx/FX/progress.lua + steps 三件套）；bitmapfonts 仅 1 块
（core.gfx:842，实为 textcolors 色表）。
**goals_shine.gfx 单文件 10.7MB**：给每个国策图标自动生成 shine 动画，
头部注明 `#Vanilla DO NOT DELETE`——由 tools/assets/gfx_entry_generator_gui.py
（311KB GUI 工具）批量生成，**生成物入库 + 工具同仓**。

### 3.5 覆盖原版窗口的模式（44 gui + 44 gfx 同名覆盖）

同名文件 = 整体替换原版。topbar.gui 全 diff 结论：**结构、窗口名、元素名
全部保留**（引擎按 name 查找，改名即崩），改动只有三类——
①换 sprite 引用（指向新合成的顶栏背景）；
②在既有窗体内**插入新元素**（定位参考原版邻居坐标）；
③注释掉不再用的块而保留代码。
另 überhaupt 新窗体走 `MD_` 前缀独立文件 + scripted_gui 的 window_name
绑定（gui-basics.md 的「新增 vs 覆盖」二分法在万行级得到验证）。

## 4. 工具链（本仓特有）

- `tools/linting/check_common_mistakes.py` **4,662 行自研 linter**
  （上百个 _check_* 规则；只覆盖 common/events，**不覆盖 .gui**——
  .gui 质量靠人工 + 引擎，正是我们 gui 校验的空白区互证）；
- publishing/publish_workshop.py（创意工坊自动发布）、analysis/tick_audit.py
  82KB、gfx_entry_generator_gui.py、report_lib/ 验证报告框架。

## 5. 本插件可吸收的校验规则（5 条，按价值排序）

1. **同名覆盖保名集合**：覆盖原版窗口的同名文件，必须包含原版同名窗口的
   全部 name 集合——可内置原版 132 个 .gui 的顶层窗口名清单做 diff 告警
   （「改名即崩」的机器判定）；
2. **sprite 引用闭合性**：.gui 内 quadTextureSprite/spriteType 引用必须能
   在 interface/*.gfx 解析——查「.gfx 定义存在性」而非拼写（三处一致的
   冻结错字 coprs 是合法但危险的特例）；
3. **background 缺失提示**：每 containerWindowType 至少一个 background
   （info 级）；
4. **`100%` vs `100%%` 同文件混用告警**（两者都合法，混用即混乱种子）；
5. **动画参数合理性**：animation_time=1（毫秒级=瞬切）疑笔误，可报
   warn（MD 实测有此 bug）。

## 6. 坏味道

- animation_time=1 与 300 混用（missilesview:185/4551）——疑笔误上线；
- **冻结拼写错误 `coprs`**：topbar.gui:10 / topbar.gfx:313 / dds 文件名
  三处一致，改名需三方同步，无人敢动——「三处一致所以没错」是错觉，
  错字也会自我冻结（对照：我们 sprites 校验器查存在性时，这类要靠
  `typo-watchlist` 类人工清单兜底）；
- **墓碑文件**：Air_Technologies.gfx 仅 50 字节且语法未闭合
  （`spriteTypes = {` 后无 `}`），靠内容为空撑过引擎——空壳文件的
  语法错误是隐性地雷；
- 命名三轨 + `!` 魔法前缀：新贡献者难辨约定；100% 混用同源。

## 7. 覆盖度声明

interface 两侧共 908 文件**清单级**全过（大小/类型/字段 grep 全量）；
8 个最大/覆盖文件**逐段精读**（含 topbar 全 diff、economyview 2100 行 diff）；
popupwindow/unitview/goals_shine 仅结构级。未覆盖：common/scripted_guis
56 文件内容（上一轮 §13 已覆盖架构层）、gfx 二进制。

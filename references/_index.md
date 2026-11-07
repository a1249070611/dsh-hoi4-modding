---
title: "HOI4 Modding 参考库总索引"
domain: 00_start
scope: 路由——"我要做 X，该读哪一篇"
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - 本机知识库 knowledge/（52 篇，2026-10-26 校验）
  - .tmp/audit/game-survey.md（1.19.4.2 原版文件域盘点）
  - .tmp/audit/skill-audit.md（旧插件内容审计）
---

# HOI4 Modding 参考库总索引

这套参考库是**自包含**的：不依赖任何本机路径、外部笔记或记忆，换一台机器也能直接读。
所有路径都用占位符：`<GAME_DIR>` 游戏安装根、`<USER_DIR>` 用户数据目录（存档/mod/日志）、`<PROJECT_DIR>` 你的 mod 工程、`$SKILL` 本技能目录。

## 0. 三层读取

1. 本文件（总索引）——先查「任务 → 文档」路由表，直接跳到某一篇。
2. 域目录下的 `_index.md`——该域的文档清单、5 条最重要结论、常见坑、与相邻域的边界。
3. 单篇文档——具体字段、语法、实例路径。

**读之前先确认三件事**：游戏装在哪（`<GAME_DIR>`）、当前游戏版本（`<GAME_DIR>/launcher-settings.json` 的 `rawVersion`）、目标国家是否已有专属国策树（`<GAME_DIR>/common/national_focus/`）。

## 1. 任务 → 文档路由表

| 我要做的事 | 先读 |
|---|---|
| 从零建一个 mod（目录、descriptor、启动） | `00_start/mod-structure.md` → `00_start/environment.md` |
| 搞清 mod 怎么覆盖原版（replace_path / 同名文件 / 同 ID） | `00_start/load-order-and-override.md` |
| 查某个 effect / trigger / modifier 的官方定义 | `01_script/effects-triggers.md`（字段清单直接查游戏内 `documentation/`） |
| 写国策树（焦点、连线、AI 权重） | `02_content/focus-trees.md` |
| 国策树在界面上连线重叠/错位/不显示 | `90_case-studies/tech-tree-gridbox.md` |
| 写事件（country_event / news_event / 触发链） | `02_content/events.md` |
| 写决议、任务、连续决议 | `02_content/decisions.md` |
| 写国家精神 / 设计商 / 法律（ideas） | `02_content/ideas.md` |
| 写角色（领袖、元帅、顾问、科学家） | `02_content/characters.md` |
| 写国家历史（政治、科技、编制、建筑初始值） | `02_content/history-countries.md` |
| 写科技与科技树（含 folder / 前置 / 图标） | `02_content/technologies.md` |
| 写 MIO（军工组织） | `02_content/mio.md` |
| 写特殊项目（核、火箭、特种装备） | `02_content/special-projects.md` |
| 写情报机构与行动 | `02_content/intelligence.md` |
| 写外交、战争目标、和平会议 | `02_content/diplomacy-wargoals.md` |
| 写权力平衡（BoP） | `02_content/balance-of-power.md` |
| 写占领与抵抗 | `02_content/occupation-resistance.md` |
| 作用域（scope）怎么写、怎么切 | `01_script/scopes.md` |
| effect / trigger 写法与常用清单 | `01_script/effects-triggers.md` |
| 变量、临时变量、数组、数学运算 | `01_script/variables.md`、`01_script/math-operators.md`、`01_script/dynamic-variables.md` |
| 复用逻辑（scripted_effects / scripted_triggers） | `01_script/scripted-effects-triggers.md` |
| 集合（collection）与遍历 | `01_script/collections.md` |
| 定时/事件钩子（on_actions） | `01_script/on-actions.md` |
| 控制台命令（调试用） | `01_script/console-commands.md` |
| 科技树重排（动态挂载子科技、改界面布局） | `90_case-studies/tech-tree-gridbox.md` → `02_content/technologies.md` |
| 写装备与装备原型（陆海空） | `03_military/equipment.md`、`03_military/units.md` |
| 写师编制模板 | `03_military/division-templates.md` |
| 陆战数值与战斗修正 | `03_military/land-combat.md` |
| 空军（编制、任务、空域） | `03_military/air.md` |
| 海军（舰船、任务、海域） | `03_military/navy.md` |
| 学说（陆海空） | `03_military/doctrines.md` |
| 州（state）、人口、建筑槽 | `04_world/states.md` |
| 战略区域 | `04_world/strategic-regions.md` |
| 建筑定义与建造 | `04_world/buildings.md` |
| 资源与资源在州里的写法 | `04_world/resources.md` |
| 补给（节点、hub、铁路） | `04_world/supply.md` |
| 地形与地形修正 | `04_world/terrain.md` |
| 地图文件结构（definition.csv、default.map、province） | `04_world/map-structure.md` |
| 写 GUI 窗口（.gui） | `05_presentation/gui-basics.md` |
| scripted GUI（脚本驱动界面、按钮回调） | `05_presentation/scripted-gui.md` |
| 顶栏按钮 / 顶部栏入口 | `05_presentation/scripted-gui.md`（`parent_window_token = top_bar`） |
| 高级界面（tooltip、动态文本、列表复用） | `05_presentation/advanced-interface.md` |
| GFX / sprite / 贴图引用 | `05_presentation/gfx-sprites.md` |
| DDS 贴图格式、尺寸、压缩、生成 | `05_presentation/dds.md` |
| 本地化（.yml、key、颜色、动态文本） | `05_presentation/localisation.md` |
| **做汉化子模组 / 覆盖别人的内容** | `05_presentation/localisation.md` §13（四层工作流） |
| 中文字体（`????` 乱码根因） | `05_presentation/fonts-cjk.md` |
| 人物肖像与国旗 | `05_presentation/portraits-flags.md` |
| 3D 模型接入（.mesh/.anim/pdxmesh/entity） | `05_presentation/models-3d.md` |
| 音效与音乐 | `05_presentation/audio.md` |
| **做音乐/电台 mod** | `05_presentation/audio.md` §6.3（两层结构，缺层静默） |
| **大型 mod 的自测 / 静态检查 / CI / 协作公约** | `93_ecosystem/mod-maintenance-engineering.md` |
| 工程初始化与目录约定 | `06_workflow/setup.md` |
| 调试与 error.log 排错 | `06_workflow/debugging.md` |
| 校验与门禁（提交前跑什么） | `06_workflow/validation.md` |
| 性能优化（后期卡顿） | `06_workflow/performance.md` |
| 兼容性（多个 mod 共存、覆盖冲突） | `06_workflow/compatibility.md` |
| 版本迁移（1.18 → 1.19 之类） | `06_workflow/migration.md` |
| 发布到创意工坊 | `06_workflow/publishing.md` |
| 工具怎么用（lint / loc / gfx / map / model） | `07_tools/` 各篇 |
| 找真实案例参考写法 | `90_case-studies/` |
| **遇到问题、有报错、功能不对** | **`91_error-book/` 先查——按症状找标准答案** |
| **错题本里没有、想找思路** | **`92_solutions/` 思路池** |
| **想看看同类开源工具（如可视化编辑器）怎么实现的** | `93_ecosystem/` 工程解剖 |

> **别用眼睛翻这两本，用工具查。**
> `kiant_hoi4_error_book query="你看到的现象"` → 命中就 `action=get id=EB-00X` 拿标准方案；
> 没命中再 `kiant_hoi4_solutions query="关键词"`。
> 工具按症状做加权检索，比通读快得多；而且它会拒掉「字面碎片」式的假命中，不会把不相干的条目推给你。

## 2. 域目录一览

| 目录 | 主题 | 篇数 | 什么时候进 |
|---|---|---|---|
| `00_start/` | 环境、目录结构、加载与覆盖 | 4 | 项目刚开始 / 搞不清 mod 怎么生效 |
| `01_script/` | 脚本语言：scope、effect、trigger、变量、集合 | 10 | 写任何逻辑 |
| `02_content/` | 内容系统：国策、事件、决议、理念、角色、科技、MIO、特殊项目、外交、BoP、占领 | 14 | 写"内容" |
| `03_military/` | 陆海空、装备、编制、学说 | 8 | 军事相关 |
| `04_world/` | 州、战略区域、建筑、资源、补给、地形、地图 | 8 | 地图/经济相关 |
| `05_presentation/` | GUI、scripted GUI、GFX、DDS、本地化、字体、肖像、3D、音频 | 11 | 一切"看得见"的东西 |
| `06_workflow/` | 初始化、调试、校验、性能、兼容、迁移、发布 | 8 | 工程流程 |
| `07_tools/` | `hoi4mod` 命令行工具逐个用法（上游 CLI，命令名与本插件不符） | 15 | 想跑工具时 |
| `08_fileformats/` | **每种文件格式怎么解析、引擎容忍什么** | 3 | **读不懂/改不动某个文件时** |
| `09_assets/` | **图片/模型/动画/音频的资源管线、替换、兼容性** | 2 | 换素材、修贴图、模型不动 |
| `10_internals/` | **引擎底层行为：加载顺序、缓存、渲染、性能** | 1 | 想知道"为什么引擎这么干" |
| `90_case-studies/` | 真实 mod 的实战记录（**不是默认做法**） | 6 | 需要"别人怎么做的"具体样例 |
| `91_error-book/` | 错题本：已实证踩坑，症状 → 根因 → 标准方案 | 24 | **出问题第一个进这里** |
| `92_solutions/` | 方案库：未验证思路，按状态分级 | 15 | 错题本没有时找方向 |
| `93_ecosystem/` | **同类开源工具的工程解剖（hagane-studio）** | 6 | 想知道"别人家的工具怎么做的" |

域目录里的 `_index.md` 有该域的**5 条最重要结论**和**常见坑**，比读单篇更快。

### 91 / 92 两个目录怎么分工

这是本库唯一一处「同一个问题有两个入口」的地方，规则要记清：

| | `91_error-book/` | `92_solutions/` |
|---|---|---|
| 内容性质 | **已实证**的标准答案 | **未验证**的思路 |
| 可信度 | 高，可直接照做 | 低，必须自己验证 |
| 每条都有 | 症状、错误做法、根因、方案、验证 | 思路、为什么没采用、怎么验证 |
| 什么时候用 | 遇到具体问题 | 错题本没有时找方向 |
| 怎么进 | 按症状查速查表 | 按状态列扫一遍 |

**顺序永远是：先查 91，再查 92。** 反过来会浪费时间去试错题本里已经写明不行的方案。

## 3. 权威性分层（很重要）

写 mod 时如果两处说法冲突，按这个顺序取信：

1. **游戏内 `documentation/*.md`**（effects / triggers / modifiers / console_commands / dynamic_variables）——字段级权威，`01_script/effects-triggers.md` 说明怎么用。
2. **游戏内 `common/**/_documentation.md`**（31 处域级文档，raids / special_projects / MIO / ai_strategy 等最全）。
3. **`<GAME_DIR>` 里的原版实例文件**——没有专门文档的域（national_focus / ideas / technologies / units / history / interface / gfx / map / game_rules / defines）只能读实例。
4. **本参考库的域文档**——对上面三者的整理与实测补充。
5. **`91_error-book/`**——实证过的具体解法。层级低于域文档（因为它针对具体场景），但**排查时优先于域文档**：域文档讲怎么写对，错题本讲怎么修错。
6. **`90_case-studies/`**——单个项目的做法，不能当通用规则。
7. **`92_solutions/`**——未验证的思路。**最后才信，必须自己验证。**

版本声明：本库字段以 `1.19.x` 为准；本机实测多数在 `1.19.3.0`，并用 `1.19.4.2` 复核过文件位置。跨版本使用前先看 `06_workflow/migration.md`。

## 4. 工具入口

统一走 `hoi4mod`（`$SKILL/tools/cli.py`），不要记一堆脚本名：

```
python $SKILL/tools/cli.py doctor              # 环境体检
python $SKILL/tools/cli.py lint <mod>          # 静态校验
python $SKILL/tools/cli.py loc audit <mod>     # 本地化 key 审计
python $SKILL/tools/cli.py gfx audit <mod>     # 贴图/sprite 审计
python $SKILL/tools/cli.py map audit <mod>     # 地图引用审计
python $SKILL/tools/cli.py model chain-check <mod>
python $SKILL/tools/cli.py install <mod>       # 装到 <USER_DIR>/mod
python $SKILL/tools/cli.py self-test           # 离线自检
```

退出码：`0` 没问题 / `1` 发现问题 / `2` 用法或环境错误 / `3` 写操作被拒绝。所有子命令支持 `--json`。

## 5. 与其他资料的关系

- 通用**方法论**（第一性原则、角色分工、门禁设计）在 `dsh-hoi4-agent-preset`，本库不重复。
- 具体项目的**事实**（路径、生成器、门禁清单）写在你项目自己的 `AGENTS.md`，本库不写。
- 本库只负责：**领域知识 + 可执行工具**。

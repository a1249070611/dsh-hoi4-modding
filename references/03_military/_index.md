---
title: 军事系统知识库索引（Military）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/units
  - common/units/equipment
  - common/doctrines
  - common/terrain/00_terrain.txt
  - common/combat_tactics.txt
  - common/defines/00_defines.lua
  - common/unit_tags/00_categories.txt
---

# 03 军事系统（Military）— 索引

一句话定位：**HOI4 的军事系统 = 一组「数据表 + 一组 defines 常量 + 少量硬编码算法」**。你能用脚本改的是数据表（营、装备、学说、战术、地形），你能用 defines 调的是常量（伤害骰、宽度、惩罚），你改不了的是战斗解算流程本身。

## 文档清单

| 文档 | 一句话摘要 |
|---|---|
| [units.md](units.md) | `common/units/*.txt` 的营/支援连（sub_units）定义：字段、类别、地形加成、新增营的完整步骤 |
| [equipment.md](equipment.md) | `common/units/equipment/`（注意不是 `common/equipment`）的 archetype / 变体 / upgrades / modules / equipment_groups |
| [division-templates.md](division-templates.md) | 师编制：regiments/support/regimental_support 网格、OOB `units = {}`、AI 模板、师属性来源 |
| [land-combat.md](land-combat.md) | 陆战：宽度、伤害骰、战术（combat_tactics）、地形修正、dice/defines 全表 |
| [navy.md](navy.md) | 海军：船体 archetype、模块、船种 sub_unit、海战 defines、任务系统边界 |
| [air.md](air.md) | 空军：airframe archetype、机翼大小、任务白名单 `allow_mission_type`、空战 defines |
| [doctrines.md](doctrines.md) | 1.19 全新学说系统：folder / grand doctrine / track / subdoctrine / mastery / reward |

## 该领域 5 条最重要的结论

1. **装备分两层：archetype（原型，不可生产）+ 变体（真正生产的东西）**。`common/units/equipment/infantry.txt` 里 `infantry_equipment` 是 archetype（`is_archetype = yes`、`is_buildable = no`），`infantry_equipment_1..N` 才是变体。变体只写「与父级不同的数值」，其余继承。见 [equipment.md](equipment.md)。
2. **1.19 的学说不是树，是「文件夹 + 大教义 + 轨道 + 子教义 + 精通度」**。旧教程里的 `common/doctrines/land/*.txt`（`path = { ... }`、`xp_cost` 线性树）已不存在；现在文件在 `common/doctrines/{folders,grand_doctrines,tracks,subdoctrines}/`，四个文件夹 `land/naval/air/special_forces`（后者需 DLC）。这正是本库「旧教程失效」最集中的地方，见 [doctrines.md](doctrines.md)。
3. **战斗宽度已重写为「绝对方格 + 地形宽度」**：`common/terrain/00_terrain.txt` 里每种地形写 `combat_width = 50~70`（绝对值，不再是百分比）；营自身仍有 `combat_width`（步兵 2、支援连 0）；`NDefines.NMilitary.ENGAGEMENT_WIDTH_PER_WIDTH = 2.0` 决定交战上限。别再按「20/40 宽」写攻略，见 [land-combat.md](land-combat.md)。
4. **1.19 新增「团级支援」（regimental support）**：师编制里除了 `regiments` / `support` 还有第三层 `regimental_support = { field_guns = { x=.. y=.. } }`（原版只给 CZE 用了），对应 defines `MAX_REGIMENTAL_SUPPORT_WIDTH/HEIGHT` 与 `REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS`；子单元用 `divisional = no` + `category_regimental_support_battalions` 声明。见 [division-templates.md](division-templates.md) 与 [units.md](units.md)。
5. **同一个数值改在不同层，效果完全不同**：装备 stat（`soft_attack` 等）影响「每件装备」→ 师攻击力；子单元 stat 影响「营」→ 师的底子；`common/defines/00_defines.lua` 的 `LAND_COMBAT_*_DAMAGE_MODIFIER` 影响「所有战斗折算」。改平衡前先确定层级，否则会做出「改了没感觉」或「一改全崩」。见 [land-combat.md](land-combat.md)。

## 目录与读取方式速查

| 想改什么 | 改哪个文件 |
|---|---|
| 新增/修改营、支援连 | `common/units/<任意文件名>.txt`（顶层 `sub_units = { ... }`） |
| 新增/修改装备 | `common/units/equipment/<任意文件名>.txt`（顶层 `equipments = { ... }`） |
| 装备模块 | `common/units/equipment/modules/00_{tank,ship,plane}_modules.txt`（`equipment_modules = { ... }`） |
| 装备升级（引擎/装甲/火炮等级） | `common/units/equipment/upgrades/{land,naval,air}_upgrades.txt` |
| 装备分组（MIO / 加成） | `common/equipment_groups/*.txt` |
| 学说 | `common/doctrines/{folders,grand_doctrines,tracks,subdoctrines}/` |
| 战斗战术 | `common/combat_tactics.txt` |
| 地形战斗修正 | `common/terrain/00_terrain.txt`（注意不是 `map/terrain.txt`） |
| 常量（伤害/宽度/惩罚） | `common/defines/00_defines.lua` |
| 师编成与初始部队 | `history/units/<TAG>_<year>.txt`（`division_template` + `units`） |
| AI 模板 | `common/ai_templates/*.txt` |

## 本领域通用机制（必读）

- **加载**：`common/` 下所有 `.txt` 在启动时读取一次；**没有热重载**，改完必须重启游戏。
- **覆盖语义**：同名文件整体替换（按 mod 加载顺序，后加载覆盖先加载）；不同文件里同 ID 定义、后加载者覆盖。因此「改原版装备」有两种做法：整文件复制替换（易被原版更新破坏）或新增文件重定义同 ID（**推荐**，但必须完整复制该定义的字段，因为同 ID 覆盖是整条替换而不是字段合并）。
- **校验和**：任何 `common/` 改动都会改变 checksum，多人联机双方必须一致。
- **必须配本地化**：营/装备/学说/战术名都是 loc key，缺 key 会在界面显示 key 原文。命名建议 `NAMESPACE_` 前缀。
- **调试**：启动加 `-debug_mode`；出问题先看 `logs/error.log`，按你新增的 ID 名去搜索（常见为未知 modifier、未知 type、括号不平衡、引用了不存在的 category/module）。

## 常见坑（本领域高发）

1. **路径记错**：装备在 `common/units/equipment/`，**没有** `common/equipment/` 目录（1.19.x 实测）。写 `common/equipment/` 会静默不加载。
2. **忘了设计师 GUI**：新增坦克底盘/飞机机体后，装备能生产但**设计师界面里看不到**。`plane_airframes.txt` 第 3 行原版注释明确要求同时在 `interface/equipmentdesigner/planes/plane_blueprints_generic.gui` 里加条目；坦克在 `interface/equipmentdesigner/tanks/tank_chassis_<archetype>.gui`。
3. **把 subtype `type` 当装备 `type`**：子单元的 `type = { infantry support }` 是「营的类型集合」，装备的 `type = infantry/armor/...` 是「装备大类」，两者取值域不同。
4. **改 archetype 数值以为改的是变体**：变体若写了同名字段就覆盖 archetype；你想改「所有步枪」就改 archetype，想改「1936 型步枪」就改 `infantry_equipment_1`。
5. **学说效果写 `add_equipment_bonus` effect**：原版文档明确说不要用 effect 版（换学说后加成不会移除），要在学说里写 `equipment_bonus = { ... }` 数据块。

## 与其他目录的边界

- 国策/事件/科技如何给装备加成、如何解锁营：见 [../02_content/technologies.md](../02_content/technologies.md)、[../02_content/focus-trees.md](../02_content/focus-trees.md)。
- 装备的 `can_be_produced` 里用的 trigger 语法：见 [../01_script/effects-triggers.md](../01_script/effects-triggers.md)。
- 装备图标（GFX/DDS）、设计师界面布局：见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)、[../05_presentation/gui-basics.md](../05_presentation/gui-basics.md)。
- MIO（军工组织）与装备组的结合：见 [../02_content/mio.md](../02_content/mio.md)。

## 域文件规模、官方文档与实例文件位置（1.19.x 实测）

数据为 1.19.4.2 安装树统计（口径同 `.tmp/audit/game-survey.md`）。

| 子域 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 营 / 单位的全部内容 | `common/units/` | 297 文件（296 `.txt`，约 11.4 万行） | 仅 `equipment/_documentation.md`（125 行） |
| 装备（原型/变体/模块/升级） | `common/units/equipment/` | 51 `.txt` | ✅ 125 行 |
| 学说（四层 + 5 份 doc） | `common/doctrines/` | 27 文件 / 9,025 行 | ✅ ×5 |
| 科技（解锁装备/营的唯一入口） | `common/technologies/` | 13 文件 | ❌ |
| 师编制 AI | `common/ai_templates/` | 16 文件 | ✅ |
| 装备 AI | `common/ai_equipment/` | 23 文件 | ✅ |
| 海军 AI | `common/ai_navy/` | 26 文件 | ✅ |
| 装备分组 | `common/equipment_groups/` | 2 文件 | ✅ |
| 营类别标签 | `common/unit_tags/00_categories.txt` | 51 行 / 49 类 | ❌ |
| 陆战战术池 | `common/combat_tactics.txt` | 1,181 行（单文件域） | ❌ |
| 将领 / 技能 / 勋章 | `common/unit_leader/`(13)、`common/abilities/`(6)、`common/unit_medals/`(1)、`common/aces/`(1) | — | ❌ |
| 全局数值 | `common/defines/00_defines.lua` | 4,728 行 | ❌ |

结论：官方 `_documentation.md` 只集中在**装备（含模块/升级）、学说（5 份）、三类 AI（ai_templates / ai_equipment / ai_navy）与 equipment_groups**。其余（units 顶层、technologies、unit_tags、combat_tactics、defines、unit_leader）全靠原版样本反推——这也是本目录各篇标注"实测/推测"的原因。

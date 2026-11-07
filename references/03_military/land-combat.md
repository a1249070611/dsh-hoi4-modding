---
title: 陆战（Land Combat）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/combat_tactics.txt
  - common/terrain/00_terrain.txt
  - common/units/artillery_brigade.txt
  - common/units/infantry.txt
  - common/defines/00_defines.lua
  - common/doctrines/grand_doctrines/land_grand_doctrines.txt
  - documentation/triggers_documentation.md
---

# 陆战（Land Combat）

**一句话**：陆战 = **宽度 → 谁参战** → **战术掷骰** → **伤害骰 + 修正** → **装备/人力损失**。你能改的是「宽度数据」「战术表」「地形表」「defines 常量」，改不了这段流程的顺序。

---

## 1. 哪些可改、哪些硬编码

| 层 | 可改？ | 在哪 |
|---|---|---|
| 战斗宽度（地形） | ✅ | `common/terrain/00_terrain.txt` 的 `combat_width` / `combat_support_width` |
| 战斗宽度（营） | ✅ | `common/units/*.txt` 的 `combat_width`（步兵 2、线列炮 3、支援连 0） |
| 交战上限 | ✅ | `NDefines.NMilitary.ENGAGEMENT_WIDTH_PER_WIDTH = 2.0` |
| 战术表 / 新战术 | ✅ | `common/combat_tactics.txt`（自定义 tactic 名**必须** `tactic_` 开头，见文件第 3 行注释） |
| 地形修正 | ✅ | `common/terrain/00_terrain.txt` 的 `units = { attack = -0.15 }`、`movement_cost` |
| 伤害/骰子常量 | ✅ | `common/defines/00_defines.lua` 的 `LAND_COMBAT_*` |
| 装甲穿透/硬度 | ✅ | 装备 stat（`armor_value`/`ap_attack`/`hardness`）见 [equipment.md](equipment.md) |
| 学说加成（含解锁战术） | ✅ | `common/doctrines/` 的 `enable_tactic`、`category_*` 加成 |
| 战斗解算顺序 / 骰子公式结构 | ❌ | 引擎硬编码，只能通过 defines 调系数 |

---

## 2. 战斗宽度（1.19 最容易被旧攻略误导的地方）

### 2.1 地形给出「绝对宽度」

`common/terrain/00_terrain.txt`（1.19 新路径，旧教程写 `map/terrain.txt`）：

```pdx
# common/terrain/00_terrain.txt 第 29-53 行
forest = {
	color = { 89 199 85 }
	movement_cost = 1.5
	combat_width = 60          # ★绝对值（不是 -20% 这种百分比）
	combat_support_width = 30
	ai_terrain_importance_factor = 5.0
	match_value = 5
	sound_type = forest
	buildings_max_level = { bunker = 4 coastal_bunker = 6 }
	units = { attack = -0.15 }
	supply_flow_penalty_factor = 0.08
	truck_attrition_factor = 0.2
}
```

实测各地形宽度（同一文件）：

| 地形 | `combat_width` | `combat_support_width` | `units.attack` | `movement_cost` |
|---|---|---|---|---|
| plains | 70 | 35 | 无 | 1.0 |
| forest | 60 | 30 | -15% | 1.5 |
| hills | 70 | 35 | -25% | 1.5 |
| mountain | 50 | 25 | -50% | 2.0（`attrition = 0.3`） |
| ocean / lakes | 1.0 移动成本，`naval_terrain = yes` | — | — | 1.0 |

### 2.2 营宽度与超宽惩罚

- 营宽度：`infantry` = 2、`artillery_brigade` = 3、支援连 = 0（见 [units.md](units.md)）。师宽度 = Σ 线列营宽度。
- 超宽：`COMBAT_OVER_WIDTH_PENALTY = -1`（每超 1%）、`COMBAT_OVER_WIDTH_PENALTY_MAX = -0.33`。
- 交战上限：`ENGAGEMENT_WIDTH_PER_WIDTH = 2.0`（我方 1 宽允许交战的敌方宽度）。
- 堆叠惩罚：`COMBAT_STACKING_START = 5`、`COMBAT_STACKING_EXTRA = 3`、`COMBAT_STACKING_PENALTY = -0.02`。
- 多方向进攻：`MULTIPLE_COMBATS_PENALTY = -0.5`（防御方被多面进攻的惩罚）。

> 结论：**不要再用「20/40 宽」的说法**。当前模型是「地形给一个绝对宽度（50~70），师按营的 combat_width 填进去」。做 mod 时该调 `combat_width`（地形或营）还是 `ENGAGEMENT_WIDTH_PER_WIDTH`，取决于你想改「某地形更难展开」还是「全局交战规则」。

---

## 3. 战术（combat_tactics）

### 3.1 文件结构与阶段

`common/combat_tactics.txt`（1181 行）先声明阶段：

```pdx
# 第 6-12 行
phases = { # phase = no is the standard phase
	close_combat
	tactical_withdrawal
	seize_bridge
	hold_bridge
	street_fighting
}
```
然后是几十个 `tactic_*` 定义。

### 3.2 tactic 字段（原版第 14-102、187-262 行）

```pdx
tactic_encirclement = {
	is_attacker = yes               # 谁可以选择这个战术
	trigger = {                     # ★combatant + country 的合并 scope
		is_attacker = yes
		phase = no                  # 当前阶段
		frontage_full = yes
		has_reserves = yes
		OR = {
			skill_advantage > 0
			has_trait = panzer_leader
			has_trait = trickster
		}
	}

	active = yes                    # yes = 默认可用；no = 需被学说/国策 enable_tactic 解锁

	base = {                        # 权重（加权随机抽取）
		factor = 4
		modifier = {
			add = 4
			OR = { has_trait = panzer_expert has_trait = combined_arms_expert }
		}
	}

	picture = encircle             # 战术图标（GFX 名）
	countered_by = tactic_tactical_withdrawal   # 被哪个战术克制

	combat_width = 0.5             # 战术对宽度的修正（这里 +50%）
	attacker = 0.25                # 攻击方伤害加成
	defender = 0.05                # 防御方伤害加成
}

tactic_delay = {
	is_attacker = no
	trigger = { is_attacker = no phase = no }
	active = no                    # ★默认不可用，需学说/国策解锁
	base = { factor = 4 }
	picture = delay
	countered_by = tactic_shock
	attacker_movement_speed = -0.25
	attacker = -0.25
	defender = -0.15
}
```

- `phase = close_combat` / `tactical_withdrawal` / `seize_bridge` / `hold_bridge` / `street_fighting` 可让战术**切换阶段**（第 99 行 `tactic_assault` 就是切到 close_combat）。
- `trigger` 里可用：`terrain`、`is_fighting_in_terrain = urban`、`has_artillery_ratio > 0.1`、`skill_advantage > 0`、`frontage_full`、`has_reserves`、`has_trait`、`phase` 等（都在本文件里能找到用例）。
- 战术相关 defines：`TACTIC_SWAP_FREQUENCEY = 12`（小时换一次战术）、`RECON_SKILL_IMPACT = 5`、`COUNTRY/ARMY_GENERAL/FIELD_MARSHAL_PREFERRED_TACTIC_WEIGHT_FACTOR`、`PREFERRED_TACTIC_COMMAND_POWER_COST = 20`。

### 3.3 战术怎么被解锁

学说里 `enable_tactic`（`common/doctrines/_documentation.md` 与 `grand_doctrines/land_grand_doctrines.txt`）：

```pdx
# common/doctrines/grand_doctrines/land_grand_doctrines.txt 第 31-37 行
new_mobile_warfare = {
	...
	enable_tactic = tactic_unexpected_thrust
	milestones = { { ... enable_tactic = tactic_delay ... } }
}
```

> 自建战术名**必须**以 `tactic_` 开头，否则与科技/学说的 `enable_tactic` 匹配不上（文件第 3 行原版注释明确写了这点）。

---

## 4. 伤害计算与 defines

### 4.1 核心 defines（`common/defines/00_defines.lua`，NMilitary 段）

| define | 值 | 作用 |
|---|---|---|
| `LAND_COMBAT_STR_DICE_SIZE` | 2 | 地面打地面的 strength 骰数 |
| `LAND_COMBAT_ORG_DICE_SIZE` | 4 | 组织度骰数 |
| `LAND_COMBAT_STR_ARMOR_ON_SOFT_DICE_SIZE` | 2 | 装甲压制软目标时额外骰 |
| `LAND_COMBAT_ORG_ARMOR_ON_SOFT_DICE_SIZE` | 6 | 同上（组织度） |
| `LAND_COMBAT_STR_DAMAGE_MODIFIER` | 0.060 | ★全局 strength 伤害系数 |
| `LAND_COMBAT_ORG_DAMAGE_MODIFIER` | 0.053 | ★全局组织度伤害系数 |
| `LAND_COMBAT_STR_ARMOR_DEFLECTION_FACTOR` | 0.5 | 装甲压制时的伤害减免 |
| `LAND_COMBAT_ORG_ARMOR_DEFLECTION_FACTOR` | 0.5 | 同上 |
| `LAND_AIR_COMBAT_STR/ORG_DAMAGE_MODIFIER` | 0.035 | 空军对地伤害系数 |
| `LAND_AIR_COMBAT_MAX_PLANES_PER_ENEMY_WIDTH` | 3 | 每点敌方宽度可进多少架 CAS/TAC |
| `BASE_CHANCE_TO_AVOID_HIT` | 90 | 有防御值时闪避率(%) |
| `CHANCE_TO_AVOID_HIT_AT_NO_DEF` | 60 | 防御耗尽后的闪避率(%) |
| `ENCIRCLED_PENALTY` | -0.3 | 被包围惩罚 |
| `RIVER_CROSSING_PENALTY` / `_LARGE` | -0.3 / -0.6 | 渡河惩罚（小/大） |
| `BASE_FORT_PENALTY` | -0.15 | 基础要塞惩罚 |
| `DIG_IN_FACTOR` | 0.02 | 每级堑壕的加成 |
| `UNIT_DIGIN_CAP` | 5 | 最多挖 5 级 |
| `BASE_NIGHT_ATTACK_PENALTY` | -0.5 | 夜战惩罚 |
| `COMBAT_SUPPLY_LACK_*` | -0.15 ~ -0.65 | 缺补给时四种情形的战斗惩罚 |
| `ENEMY_AIR_SUPERIORITY_IMPACT` | -0.35 | 敌方空优对防御的影响 |
| `ATTRITION_DAMAGE_ORG` / `ATTRITION_EQUIPMENT_LOSS_CHANCE` | 0.08 / 0.005 | 损耗 |
| `EQUIPMENT_COMBAT_LOSS_FACTOR` | 0.70 | 战斗中装备损失比例（其余返还） |
| `COMBAT_MOVEMENT_SPEED` | 0.33 | 战斗中移动速度削减 |
| `COMBAT_MINIMUM_TIME` | 4 | 最短战斗时长(小时) |

### 4.2 装甲/穿透

- 装备 `armor_value` vs 敌方 `ap_attack`：`ap_attack` 不足则无法穿透，伤害大幅衰减（具体曲线在引擎，`LAND_COMBAT_*_ARMOR_DEFLECTION_FACTOR` 控制减免）。
- `hardness` 决定被 `hard_attack` 还是 `soft_attack` 命中比例。
- 来源：`common/units/equipment/infantry.txt`（`hardness = 0`）、`tank_chassis.txt`（`hardness = 0.8~0.9`）。

---

## 5. 最小可跑示例：改一个数值（三种典型）

### 例 A：让森林更窄（地形层）

```pdx
# 路径：<mod>/common/terrain/00_terrain.txt
# ⚠️ 这是整文件替换！必须复制原版全文再改，否则所有地形定义消失。
categories = {
	forest = {
		color = { 89 199 85 }
		movement_cost = 1.5
		combat_width = 45            # 原版 60 → 45
		combat_support_width = 22    # 原版 30 → 22
		ai_terrain_importance_factor = 5.0
		match_value = 5
		sound_type = forest
		buildings_max_level = { bunker = 4 coastal_bunker = 6 }
		units = { attack = -0.15 }
		supply_flow_penalty_factor = 0.08
		truck_attrition_factor = 0.2
	}
	# ……其余地形必须原样保留
}
```

### 例 B：新增一个「弹性迟滞」防御战术（战术层）

```pdx
# 路径：<mod>/common/combat_tactics.txt
# ⚠️ 同样是整文件替换；更稳的做法是放到独立文件（战术文件是平铺 tactic_* 定义，可新增文件）。
tactic_HHO_flexible_delay = {          # 名字以 tactic_ 开头
	is_attacker = no
	trigger = {
		is_attacker = no
		phase = no
		OR = {
			is_fighting_in_terrain = forest   # COMBATANT scope，原版 tactic_assault 第 91 行有用例
			is_fighting_in_terrain = hills
		}
	}
	active = no                          # 需要被 enable_tactic 解锁
	base = { factor = 3 }
	picture = delay
	countered_by = tactic_shock
	attacker_movement_speed = -0.3
	attacker = -0.2
	defender = -0.1
}
```
再在学说里 `enable_tactic = tactic_HHO_flexible_delay`（见 [doctrines.md](doctrines.md)）。
> 两个地形 trigger 的 scope 不同：`is_fighting_in_terrain` 是 **COMBATANT**（"check what terrain is in combat"，`triggers_documentation.md` 第 5561 行），适合战术 trigger；`has_terrain` 是 **COUNTRY**（"Checks if a country has any province of the specified terrain type"，第 4941 行），适合国策/事件。**别在战术里用 `has_terrain`**（语义会变成「国家有该地形省份」）。

### 例 C：全局加快战斗节奏（defines 层）

```lua
-- 路径：<mod>/common/defines/00_defines.lua
-- ⚠️ 整文件替换；必须复制原版全文。也可以只改自己 mod 的 define（同名表项覆盖）。
NDefines.NMilitary.LAND_COMBAT_ORG_DAMAGE_MODIFIER = 0.065   -- 原版 0.053
```

**风险**：A 改地形会影响补给/移动/AI 全盘；B 需要验证 trigger 合法；C 会影响所有国家的所有战斗（含 AI 对 AI），且改动 checksum。

---

## 6. 从「营」到「师面板」的换算链（排错用）

```
营基础值（common/units/*.txt）
  + 装备贡献（common/units/equipment/*.txt 的 stat × 装备数）
  → 师 base
  × (1 + 支援连 battalion_mult)
  × (1 + 学说/国策/理念/将领 trait 的 category 加成)
  × (1 + 地形/天气/补给/战术 修正)
  = 实际战斗值
```
- 学说/国策加成写法见 [doctrines.md](doctrines.md) 与 [../02_content/focus-trees.md](../02_content/focus-trees.md)。
- modifier 全表在 `documentation/modifiers_documentation.md`（按 scope 分组，搜 `army_` / `division_`）。

---

## 7. 1.19 与旧教程的差异（实测）

1. **地形定义搬到 `common/terrain/00_terrain.txt`**（旧版在 `map/terrain.txt`）；`combat_width` 从「百分比修正」变成「绝对值 50~70」，并新增 `combat_support_width`、`supply_flow_penalty_factor`、`truck_attrition_factor`。
2. **学说系统整体重写**（见 [doctrines.md](doctrines.md)），旧教程里「战术由 4 条陆军学说树解锁」的路径名/AI 权重字段已不适用。
3. **新增团级支援**（`regimental_support`、`category_regimental_support_battalions`），影响师的组成与战斗数值来源。
4. **新增一堆 defines**：`ENGAGEMENT_WIDTH_PER_WIDTH`、`MAX_REGIMENTAL_SUPPORT_*`、`REGIMENTAL_SUPPORT_SLOT_COST_MULTIPLIER`，以及 `TACTIC_*` 权重类。
5. 战术表里有新的「城市战」阶段战术（`tactic_urban_defense`、`tactic_sf_storm` 等），并带 `phase = street_fighting`。

---

## 8. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 陆战战术池 | `common/combat_tactics.txt` | 1 文件 / 1,181 行（18,634 B，单文件域） | ❌ |
| 地形（宽度与修正来源） | `common/terrain/00_terrain.txt`（类别定义）、`map/terrain/`（图形集 64 文件） | 356 行 | ❌ |
| 战术可用性 trigger | `documentation/triggers_documentation.md` | 180,523 B | ✅ |
| 战斗数值 | `common/defines/00_defines.lua` | 4,728 行 | ❌ |
| 营的固有属性 | `common/units/` 顶层 | 45 文件 | ❌（仅 equipment 子目录有 doc） |
| 学说加成 | `common/doctrines/` | 27 文件 / 5 份 `_documentation.md` | ✅ |

### 8.1 增援（reinforcement）——旧教程极少提的机制

宽度决定"能同时接战多少"，增援决定"打残之后能不能补上"，两者合起来才是真实战斗力。关键 defines（`00_defines.lua`）：

| define | 默认值 | 含义 |
|---|---|---|
| `REINFORCE_CHANCE` | 0.02 | 后排队列加入战斗的基础概率（第 1020 行） |
| `SPEED_REINFORCEMENT_BONUS` | 0.01 | 速度高于步兵基准时每 100% 的加成（上限 200%） |
| `ARMY_INITIATIVE_REINFORCE_FACTOR` | 0.25 | 主动性对增援概率的缩放 |
| `REINFORCEMENT_REQUEST_MAX_WAITING_DAYS` / `..._DAYS_FREQUENCY` | 14 / 7 | 装备补给请求的等待天数与重请求频率 |
| `REINFORCEMENT_DIVISION_PRIORITY_COUNT` | 3 | 师模板补给优先级档数（Reserves / Normal / Elite） |

- 补给优先级按**师模板**设（游戏内模板面板），不是按单支部队；默认档 = 1（Normal）。
- 想让精锐优先补员，用模板优先级与相关 modifier；**不要**直接改 `REINFORCE_CHANCE`——它全局作用于所有国家与 AI，还会改 checksum。
- 增援的"接战位置"由宽度决定：宽度算错的师，增援再快也只能在后排排队（见 §2）。

## 9. 常见错误 / 自检清单

- [ ] 改地形时确认改的是 `common/terrain/00_terrain.txt`，不是 `map/terrain.bmp`（后者是图像）。
- [ ] 地形定义是**整文件替换**语义：只写一个地形会丢其它地形。
- [ ] 自定义战术名以 `tactic_` 开头，且 `enable_tactic` 引用的是同一个名字。
- [ ] `base = { factor = ... }` 是权重不是伤害；伤害在 `attacker`/`defender` 字段。
- [ ] `trigger` 里用的字段先在 `documentation/triggers_documentation.md` 或原版 `combat_tactics.txt` 找到 ≥1 个用例。
- [ ] 改 `LAND_COMBAT_*` defines 会让 checksum 变化，多人联机必须同步。
- [ ] 改了装备/营数值后，注意师的宽度与消耗会一起变。
- [ ] 出错在 `logs/error.log` 搜战术名 / 地形名；未知字段通常会报 "unknown" 或静默忽略。

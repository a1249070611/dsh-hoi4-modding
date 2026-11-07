---
title: 海军（Navy）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/units/equipment/ship_hull_light.txt
  - common/units/equipment/ship_hull_carrier.txt
  - common/units/equipment/ship_hull_heavy.txt
  - common/units/equipment/modules/00_ship_modules.txt
  - common/units/battleship.txt
  - common/units/destroyer.txt
  - common/units/submarine.txt
  - common/units/equipment/upgrades/naval_upgrades.txt
  - common/defines/00_defines.lua
  - common/buildings/00_buildings.txt
  - common/ai_navy/_documentation.md
  - common/ideas/navy_spirits.txt
---

# 海军（Navy）

**一句话**：海军 = **船体（hull archetype + 变体）** + **模块（modules）** + **船种（sub_unit）** 三层；海战算法硬编码，但几乎全部系数都能在 `common/defines/00_defines.lua` 的 `COMBAT_*` / `NAVAL_*` 段里调。

> 旧教程（1.9 之前）把「船」直接写在 `common/units/equipment/ship_hull_*.txt` 里、数值一层；1.19 是三层结构（hull → modules → sub_unit），且必须挂在海军设计师 GUI 上。详见第 7 节。

---

## 1. 三层结构

```
ship_hull_light/ cruiser/ heavy/ carrier/ submarine   ← ① 船体 archetype（common/units/equipment/ship_hull_*.txt）
        ↓ 挂 module_slots + modules
ship_light_battery_1 / ship_engine_... / ship_anti_air  ← ② 模块（modules/00_ship_modules.txt）
        ↓ 组成
destroyer / light_cruiser / heavy_cruiser / battleship / carrier / submarine  ← ③ 船种 sub_unit（common/units/*.txt）
        ↓ 实例化
task force / fleet（舰队编组，由界面与 AI 管理，无脚本文件）
```

原版可参考：
- 船体：`common/units/equipment/ship_hull_light.txt`（驱逐/轻巡共用轻船体）、`ship_hull_cruiser.txt`、`ship_hull_heavy.txt`、`ship_hull_carrier.txt`、`ship_hull_submarine.txt`
- 模块：`common/units/equipment/modules/00_ship_modules.txt`（3176 行，`equipment_modules = { limit = { has_dlc = "Man the Guns" } ... }`）
- 船种：`common/units/battleship.txt`、`battlecruiser.txt`、`carrier.txt`、`destroyer.txt`、`heavy_cruiser.txt`、`light_cruiser.txt`、`submarine.txt`、`repair_ships.txt`、`support_ships.txt`
- 升级项：`common/units/equipment/upgrades/naval_upgrades.txt`
- 设计师 GUI：`interface/equipmentdesigner/ships/ship_hull_{light,cruiser,heavy,carrier,submarine,super_heavy}.gui`

---

## 2. 船体 archetype（以轻船体为例）

```pdx
# common/units/equipment/ship_hull_light.txt 第 3-143 行（节选）
ship_hull_light = {
	year = 1922

	can_be_produced = {
		if = {
			limit = { has_dlc = "Arms Against Tyranny" }
			NOT = { has_idea = BUL_army_restrictions_aat }
		}
		else = {
			NOT = { has_idea = BUL_army_restrictions }
		}
	}

	is_archetype = yes
	is_buildable = no
	type = screen_ship
	interface_category = interface_category_screen_ships
	alias = destroyer            # ★给 AI/替换逻辑的别名
	priority = 2000

	upgrades = {
		ship_torpedo_upgrade
		destroyer_engine_upgrade
		ship_ASW_upgrade
		ship_anti_air_upgrade
	}

	module_slots = {
		fixed_ship_battery_slot = {
			required = yes
			allowed_module_categories = { ship_light_battery dp_light_battery }
		}
		fixed_ship_anti_air_slot = {
			required = no
			allowed_module_categories = { ship_anti_air }
		}
		fixed_ship_fire_control_system_slot = {
			required = no
			allowed_module_categories = { ship_fire_control_system ship_sonar }
		}
		fixed_ship_radar_slot = {
			required = no
			allowed_module_categories = { ship_radar ship_sonar }
		}
		fixed_ship_torpedo_slot = {
			required = no
			allowed_module_categories = { ship_torpedo }
		}
		fixed_ship_engine_slot = {
			required = yes
			allowed_module_categories = { light_ship_engine }
		}
		mid_1_custom_slot = {
			required = no
			allowed_module_categories = {
				ship_torpedo ship_mine_warfare ship_mine_layer
				ship_anti_air ship_depth_charge ship_seaplane_tender
			}
		}
		rear_1_custom_slot = { ... }
	}

	module_count_limit = { category = ship_radar count < 2 }
	module_count_limit = { category = ship_sonar count < 2 }

	default_modules = {
		fixed_ship_battery_slot = empty
		fixed_ship_anti_air_slot = empty
		fixed_ship_fire_control_system_slot = empty
		fixed_ship_radar_slot = empty
		fixed_ship_engine_slot = light_ship_engine_1
		fixed_ship_torpedo_slot = empty
		mid_1_custom_slot = empty
		rear_1_custom_slot = empty
	}

	lg_armor_piercing = 0
	lg_attack = 0
	hg_armor_piercing = 0
	hg_attack = 0
	torpedo_attack = 0
	sub_attack = 1
	anti_air_attack = 0
	armor_value = 0
	surface_detection = 20
	sub_detection = 2.5
	surface_visibility = 10
	naval_speed = 32
	reliability = 0.80
	naval_range = 2000
	max_strength = 25
	fuel_consumption = 0
	build_cost_ic = 400
	resources = { steel = 2 }
	manpower = 250
	naval_dominance_factor = 20
	naval_weather_penalty_factor = 1
}
```

变体（`ship_hull_light_1`、`_2`…）只写差异，并用 `module_slots = inherit` 或逐槽 `inherit`：

```pdx
# 第 145-219 行（节选）
ship_hull_light_1 = {
	abbreviation = "hdb"
	year = 1922
	archetype = ship_hull_light
	priority = 2000
	module_slots = inherit
	naval_dominance_factor = 24
}

ship_hull_light_2 = {
	abbreviation = "hdc"
	year = 1936
	archetype = ship_hull_light
	parent = ship_hull_light_1
	module_slots = {
		fixed_ship_battery_slot = inherit
		...
		mid_1_custom_slot = {
			required = no
			allowed_module_categories = { ... ship_light_battery dp_light_battery ... }
		}
	}
	default_modules = {
		mid_1_custom_slot = empty
		rear_1_custom_slot = empty
		fixed_ship_engine_slot = light_ship_engine_2
	}
	reliability = 0.85
	naval_range = 2500
	max_strength = 40
	build_cost_ic = 500
	sub_detection = 3
	manpower = 300
	naval_dominance_factor = 30
}
```

**关键 stat 含义**：
- `lg_attack` / `lg_armor_piercing`：轻炮（对屏护舰）
- `hg_attack` / `hg_armor_piercing`：重炮（对主力舰）
- `torpedo_attack`：鱼雷；`sub_attack`：反潜
- `anti_air_attack`：防空
- `armor_value`、`max_strength`、`naval_speed`、`naval_range`、`reliability`
- `surface_detection` / `sub_detection` / `surface_visibility`：探测与隐蔽
- `naval_dominance_factor`：对海权贡献
- `naval_weather_penalty_factor`：天气惩罚系数（文件注释明确：基础值必须为 1）

---

## 3. 模块（ship modules）

`common/units/equipment/modules/00_ship_modules.txt`：

```pdx
# 第 75-139 行（节选）
equipment_modules = {
	limit = { has_dlc = "Man the Guns" }

	ship_light_battery_1 = {
		abbreviation = "saa"
		category = ship_light_battery
		sfx = sfx_ui_sd_module_turret

		add_stats = {
			lg_attack = 1
			build_cost_ic = 90
		}
		multiply_stats = {
			naval_speed = -0.01
		}
		add_average_stats = {            # ★对平均值加成（不是总和）
			lg_armor_piercing = 1
		}

		can_convert_from = {             # 老船改装
			module_category = ship_light_battery
			convert_cost_ic = 60
		}

		critical_parts = { damaged_light_guns }
	}

	ship_light_battery_2 = {
		parent = ship_light_battery_1
		...
	}
}
```

要点：
- 模块可用 `parent` 继承，`add_stats`/`multiply_stats`/`add_average_stats` 三种叠加方式。
- `can_convert_from` 决定改装成本；`critical_parts` 决定被暴击时打在哪个部件。
- 舰船 `module_slots` 的 `allowed_module_categories` 决定能装哪些模块类别；`fixed_` 前缀的槽在设计师里归组显示（语法见 `common/units/equipment/_documentation.md` 第 47-111 行）。
- 航母特殊：`ship_hull_carrier.txt` 用 `fixed_ship_deck_slot_1/2` + `ship_deck_space` 系模块，并且有 `carrier_size = 4/6/8/10` 表示载机量（见文件第 693、787、834、881 行）。

---

## 4. 船种 sub_unit（真正下水的单位）

```pdx
# common/units/battleship.txt 全文
sub_units = {
	battleship = {
		sprite = battleship
		map_icon_category = ship
		priority = 9
		active = yes
		type = { capital_ship }
		need_equipment = { ship_hull_heavy = 1 }        # 一艘 = 1 个船体
		need_equipment_modules = {                       # 必须含某模块之一
			any = {
				ship_armor_bb_1 = 1
				ship_armor_bb_2 = 1
				ship_armor_bb_3 = 1
				ship_armor_shbb = 1
			}
		}
		max_organisation = 50
		supply_consumption = 0.56
		critical_parts = { rudder_jammed destroyed_ammo_storage broken_propeller on_fire }
		critical_part_damage_chance_mult = 1
		hit_profile_mult = 1.0
	}
}
```

- `need_equipment`：每艘船消耗的装备（船体 ID）。
- `need_equipment_modules`：限制该船种必须安装哪些模块（这里是「主力舰装甲」）。
- `max_organisation`：舰船组织度；`supply_consumption`：油耗/补给。
- `critical_parts`：被暴击时的部件池；`hit_profile_mult`：被命中倾向。
- 其它船种同理：`destroyer.txt`、`light_cruiser.txt`、`heavy_cruiser.txt`、`carrier.txt`、`submarine.txt`。

---

## 5. 海战数值（defines 层）

`common/defines/00_defines.lua` 的海军段关键项（行号见注释）：

| define | 值 | 作用 |
|---|---|---|
| `COMBAT_BASE_HIT_CHANCE` | 0.1 | 基础命中率 |
| `COMBAT_EVASION_TO_HIT_CHANCE` | 0.007 | 闪避对命中的影响系数 |
| `COMBAT_EVASION_TO_HIT_CHANCE_TORPEDO_MULT` | 10.0 | 鱼雷受闪避影响更大 |
| `COMBAT_LOW_ORG_HIT_CHANCE_PENALTY` | -0.5 | 低组织度命中惩罚 |
| `COMBAT_TORPEDO_CRITICAL_CHANCE` | 0.1 | 鱼雷暴击率 |
| `COMBAT_TORPEDO_CRITICAL_DAMAGE_MULT` | 2.0 | 鱼雷暴击伤害倍率 |
| `COMBAT_DAMAGE_TO_STR_FACTOR` | 0.6 | 伤害→strength 换算 |
| `COMBAT_DAMAGE_TO_ORG_FACTOR` | 1.0 | 伤害→组织度换算 |
| `COMBAT_BASE_CRITICAL_CHANCE` | 0.05 | 基础暴击率 |
| `COMBAT_CRITICAL_DAMAGE_MULT` | 5.0 | 暴击伤害倍率 |
| `COMBAT_ARMOR_PIERCING_CRITICAL_BONUS` | 1.0 | 穿甲带来的暴击加成 |
| `COMBAT_MIN_DURATION` | 8 | 最短海战时长(小时) |
| `COMBAT_MAX_GROUPS` | 1 | 火力交换组数(平衡项) |
| `COMBAT_DAMAGE_SCALE_CARRIER` | 5 | 航母战伤害放大 |
| `CARRIER_HOURS_DELAY_AFTER_EACH_COMBAT` | 3 | 舰载机出击间隔 |
| `POSITIONING_PENALTY_FOR_SHIPS_JOINED_COMBAT_AFTER_IT_STARTS` | 0.01 | 后加入战斗的站位惩罚 |
| `CAPITAL_SHIP_COMBAT_RETREAT_MULT` | 0.5 | 主力舰撤退阈值系数 |
| `NAVAL_COMBAT_EXTERNAL_PLANES_JOIN_RATIO` | 0.05 | 外部陆基飞机参战比例 |

**任务的边界**：海军任务（巡逻/打击舰队/护航/布雷/扫雷/登陆支援…）**没有数据文件**，由引擎定义；装备/模块只能通过 `allow_mission_type` 影响空军任务，海军任务不可脚本新增。可脚本化的是：舰队编成（AI 策略 `common/ai_navy/`）、海军总部（`naval_headquarters` 建筑）、海权 modifier。

---

## 6. 最小可跑示例：新增一档驱逐船体（带新模块）

**① 新模块**（给「改进型轻炮」）：

```pdx
# 路径：<mod>/common/units/equipment/modules/HHO_ship_modules.txt
equipment_modules = {
	HHO_ship_light_battery_5 = {
		abbreviation = "sae"
		category = ship_light_battery
		sfx = sfx_ui_sd_module_turret

		add_stats = {
			lg_attack = 3.5
			build_cost_ic = 210
		}
		multiply_stats = {
			naval_speed = -0.03
		}
		can_convert_from = {
			module_category = ship_light_battery
			convert_cost_ic = 110
		}
		critical_parts = { damaged_light_guns }
	}
}
```

**② 新船体变体**（继承轻船体，改数值与槽位）：

```pdx
# 路径：<mod>/common/units/equipment/ship_hull_light_HHO.txt
equipments = {
	HHO_ship_hull_light_5 = {
		abbreviation = "hdh"
		year = 1944
		archetype = ship_hull_light
		parent = ship_hull_light_4        # 用已存在的上一级变体做父级（原版有 _1.._N）
		priority = 2000
		module_slots = inherit            # 全继承，简单安全

		reliability = 0.9
		naval_range = 3200
		max_strength = 60
		build_cost_ic = 640
		sub_detection = 5
		surface_detection = 28
		manpower = 340
		naval_dominance_factor = 38
		resources = { steel = 3 }
	}
}
```

> 想让它能装新模块，需要把 `module_slots` 里某个槽的 `allowed_module_categories` 覆盖为含 `ship_light_battery` 的列表（`module_slots = inherit` 会完全继承父级槽位；原版 `ship_hull_light_2` 就是重写了 `mid_1_custom_slot` 才多出轻炮选项）。

**③ 设计师 GUI**：`interface/equipmentdesigner/ships/ship_hull_light.gui` 里按 `equipment_designer_<hull>` 容器组织；新手体需要参照它新增容器与 `GFX_TC_*` 贴图（见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)）。
> ⚠️ 本机文件显示：每个 hull 只有一个通用 gui（`ship_hull_light.gui`），不像飞机那样按国家分文件；但 `interface/equipmentdesigner/ships/` 下没有 `_ger/_sov` 变体，说明舰体 GUI 是通用的。以本机文件为准。

**④ 科技解锁**：`enable_equipments = { HHO_ship_hull_light_5 }`（见 [equipment.md](equipment.md) 第 10 节）。

**⑤ 与国策/事件联动**：
- 科技解锁船体/模块：`enable_equipments` / `enable_equipment_modules`（见 [../02_content/technologies.md](../02_content/technologies.md)）。
- 国策给海军加成：`add_equipment_bonus = { bonus = { screen_ship = { naval_speed = 0.05 } } }`（见 [../02_content/focus-trees.md](../02_content/focus-trees.md)）。
- 事件赠送舰船：`create_ship`（COUNTRY scope，`documentation/effects_documentation.md` 第 3257-3276 行）：

```pdx
FRA = {
	create_ship = {
		type = ship_hull_submarine_1
		equipment_variant = "S Class"    # 原版文档示例写法
		creator = ENG                    # 可选，默认当前国家
		name = "My ship name"            # 可选
		amount = 5
	}
}
```

---

## 7. 1.19 与旧教程的差异（实测）

1. **船体、模块、船种三层分离**。旧教程常写 `ship_hull_light = { naval_speed = 32 ... }` 就把所有东西定义完；现在这只是第一层，还要模块和 GUI。
2. **新字段**：`alias`、`naval_dominance_factor`、`naval_weather_penalty_factor`、`critical_parts`、`critical_part_damage_chance_mult`、`hit_profile_mult`、`add_average_stats`、`can_convert_from`、`carrier_size`。旧教程全无。
3. **航母细分**：`carrier_size = 4/6/8/10`，并新增 `mega carrier`（`common/units/air.txt` 有 `mega_carrier_air_wing_size`）、`submarine_carrier_air_wing_size`。
4. **新增建筑 `naval_headquarters` / `naval_supply_hub` / `naval_facility`**（`common/buildings/00_buildings.txt` 第 126、357、377 行），会影响海军作战半径/补给。
5. **模块可用 `limit = { has_dlc = "Man the Guns" }` 门控**——没 DLC 时整块模块不加载，别假设玩家都有。

---

## 8. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 船体 archetype | `common/units/equipment/ship_hull_{light,cruiser,heavy,carrier,submarine}.txt` | 5 文件 | ✅ `common/units/equipment/_documentation.md`（125 行） |
| 舰船模块 | `common/units/equipment/modules/00_ship_modules.txt` | 3,176 行 | 同上 |
| 海军升级项 | `common/units/equipment/upgrades/naval_upgrades.txt` | 112 行 | 同上 |
| 船种 sub_unit | `common/units/` 顶层 9 个海军文件（battleship / battlecruiser / carrier / destroyer / light_cruiser / heavy_cruiser / submarine / repair_ships / support_ships） | 共 45 文件 | ❌ |
| 海军 AI（舰队/目标/任务分配） | `common/ai_navy/` | 26 文件（24 `.txt`；`fleet/` 8、`goals/` 8、`taskforce/` 9） | ✅ `_documentation.md` |
| 海军精神 | `common/ideas/navy_spirits.txt` | 1 文件 / 16,990 B | ❌ |
| 设计师 GUI | `interface/equipmentdesigner/ships/` | 6 文件 | ❌ |
| 海军数值 / 经验上限 | `common/defines/00_defines.lua`（`MAX_NAVY_EXPERIENCE = 500`） | 4,728 行 | ❌ |
| 海军区（战略区） | `map/strategicregions/` | 304 文件 | ❌ |

- **海军任务（mission）与空军一样是硬编码枚举**：没有"任务定义文件"；能脚本化的是任务可用条件与 `common/ai_navy/` 的舰队目标。想做新玩法只能组合现有任务 + 改 AI 目标。
- `common/ai_navy/` 是唯一有官方文档的海军 AI 入口（fleet / goals / taskforce 三层），调舰队行为先从它入手，别动 `COMBAT_*` defines。

## 9. 常见错误 / 自检清单

- [ ] 文件在 `common/units/equipment/`（hull）与 `common/units/`（船种），别搞反。
- [ ] 船体 `type` 用 `capital_ship / screen_ship / carrier / submarine / convoy` 等，与 sub_unit 的 `type` 匹配。
- [ ] 新增船体已挂到 `interface/equipmentdesigner/ships/*.gui`，否则设计师里看不到。
- [ ] 模块的 `category` 必须出现在某个 `module_slots` 的 `allowed_module_categories` 里，否则永远装不上。
- [ ] `need_equipment_modules` 里引用的模块 ID 真实存在（否则该船种无法设计出来）。
- [ ] 有 loc key（船体/模块/船种都要）。
- [ ] 改 `COMBAT_*` defines 会全面影响海战与 checksum。
- [ ] 海军任务不可脚本新增；想做「新任务」只能通过 UI/mission 相关系统，确认后再做。
- [ ] 出错在 `logs/error.log` 搜船体/模块 ID。

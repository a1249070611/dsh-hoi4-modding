---
title: 装备系统（Equipment）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/units/equipment/_documentation.md
  - common/units/equipment/infantry.txt
  - common/units/equipment/tank_chassis.txt
  - common/units/equipment/x_tank_chassis.txt
  - common/units/equipment/ship_hull_light.txt
  - common/units/equipment/plane_airframes.txt
  - common/units/equipment/modules/00_tank_modules.txt
  - common/units/equipment/upgrades/land_upgrades.txt
  - common/equipment_groups/_documentation.md
  - common/technologies/infantry.txt
  - common/equipment_groups/_documentation.md
  - common/technologies
---

# 装备系统（Equipment）

**一句话**：`common/units/equipment/` 里的 `equipments = { ... }` 定义「工厂生产出来的东西」的数值、材料、可生产条件、升级项与可插模块；师/舰/机的实际战力是这些数值按编制汇总出来的。

> ⚠️ **路径高频坑**：1.19.x 实测**没有** `common/equipment/` 目录。装备全部在 `common/units/equipment/*.txt`。写成 `common/equipment/xxx.txt` 不会报错、也不加载，表现为「我的装备在游戏里根本不存在」。

---

## 1. 目录地图

```
common/units/equipment/
├── _documentation.md              # ★官方语法文档（125 行），改装备前必读
├── infantry.txt                   # 步兵装备（archetype + 变体）
├── artillery.txt / anti_tank.txt / anti_air.txt / support.txt / motorized.txt / mechanized.txt
├── tank_chassis.txt               # ★坦克底盘 archetype（1.19 真正生效的坦克定义）
├── tank_light.txt / tank_medium.txt / tank_heavy.txt / tank_modern.txt
│                                  # ★注意：这些文件 1.19 里已整段注释掉（历史遗留），别照着改
├── x_tank_chassis.txt             # ★duplicate_archetypes：由底盘派生 AA/TD/SPG/喷火等
├── plane_airframes.txt            # ★飞机机体 archetype
├── x_plane_airframes.txt          # ★由机体派生战斗机/CAS/海轰/运输机等
├── single_engine_airframe.txt / twin_engine_airframe.txt
│                                  # ★实测：这两个文件 1.19 已 100% 注释掉（无有效定义）
├── quad_engine_airframe.txt       # 仅剩 transport_plane_equipment 有效（其余注释）
├── ship_hull_{light,cruiser,heavy,carrier,submarine}.txt   # ★舰体 archetype
├── modules/00_{tank,plane,ship}_modules.txt                # ★模块（equipment_modules）
├── upgrades/{land,naval,air}_upgrades.txt                  # ★升级项（upgrades）
└── convoys.txt / trains.txt / floating_harbor.txt / repair_ships.txt / railway_gun.txt / ...
```

配套目录：
- `common/equipment_groups/*.txt`：装备分组（MIO、装备加成用）。
- `common/units/unit_modifiers/unit_modifiers.txt`：兵种加成 modifier 白名单（见 [units.md](units.md)）。

---

## 2. 核心概念：archetype（原型）vs 变体（variant）

以 `common/units/equipment/infantry.txt` 为例（原版第 5-75 行节选）：

```pdx
equipments = {

	infantry_equipment = {                  # ← archetype
		year = 1936
		is_archetype = yes
		is_buildable = no                    # 原型本身不可生产
		type = infantry
		group_by = archetype
		interface_category = interface_category_land
		picture = archetype_infantry_equipment
		active = yes

		reliability = 0.9
		maximum_speed = 4
		defense = 20
		breakthrough = 2
		hardness = 0
		armor_value = 0
		soft_attack = 3
		hard_attack = 0.5
		ap_attack = 1
		air_attack = 0

		lend_lease_cost = 1
		build_cost_ic = 0.43
		resources = { steel = 2 }
	}

	infantry_equipment_0 = {               # ← 变体：只写「与父级不同」的字段
		year = 1918
		archetype = infantry_equipment
		active = yes
		priority = 05
		visual_level = 0
	}

	infantry_equipment_1 = {               # ← 1936 型，父级是 _0
		year = 1936
		archetype = infantry_equipment
		parent = infantry_equipment_0
		priority = 10
		visual_level = 1
		defense = 22
		breakthrough = 3
		soft_attack = 6
		hard_attack = 1
		ap_attack = 4
		build_cost_ic = 0.50
	}
}
```

**继承规则（实测归纳）**：变体没写的属性从 `parent` 链继承，最终回落到 archetype；写了就覆盖。所以「改所有步枪」改 archetype，「改 1936 步枪」改 `infantry_equipment_1`。

关键字段含义：
- `is_buildable = no`：原型不能生产（只能派生变体）。
- `group_by = archetype`：装备列表按原型分组显示。
- `interface_category`：决定它出现在生产界面的哪个页签。实测取值：`interface_category_land`、`interface_category_armor`、`interface_category_air`、`interface_category_capital_ships`、`interface_category_screen_ships`、`interface_category_other_ships`。
- `priority` / `visual_level`：同类排序与图标等级。
- `alias` / `substitute`：给 AI/替换逻辑用的等价物（`ship_hull_light.txt` 有 `alias = destroyer`；`plane_airframes.txt` 有 `substitute = cv_small_plane_airframe`）。
- `max_military_factories` / `max_dockyard_factories`：限制可分配给该类装备的工厂数。
- `can_be_produced = { <trigger> }` / `can_be_lend_leased = { <trigger> }`：可生产/可租借的条件（country scope）。
- `ai_type`：覆盖 AI 用 `type` 关联生产配比的行为（如 `ai_type = cv_cas`）。
- `resources = { steel = 2 }`：每单位消耗的战略资源；`build_cost_ic`：每单位 IC 成本。
- `manpower`：**海军装备**每单位占用的人力（`ship_hull_light.txt` 有 `manpower = 250`）。
- `lend_lease_cost`、`fuel_consumption`、`reliability`、`maximum_speed` 等。

### 2.1 各兵种装备 stat 名对照（都在原版文件里 grep 得到）

| 类别 | 常见 stat | 原版出处 |
|---|---|---|
| 陆军通用 | `soft_attack` `hard_attack` `ap_attack` `air_attack` `defense` `breakthrough` `armor_value` `hardness` `reliability` `maximum_speed` `build_cost_ic` | `infantry.txt`、`artillery.txt` |
| 坦克 | 同上 + `fuel_consumption`；底盘有 `module_slots` | `tank_chassis.txt` |
| 飞机 | `air_attack` `air_defence` `air_agility` `air_range` `maximum_speed` `naval_strike_attack` `naval_strike_targetting` `air_superiority` `surface_detection` `sub_detection` | `plane_airframes.txt`、`x_plane_airframes.txt` |
| 舰船 | `lg_attack` `lg_armor_piercing` `hg_attack` `hg_armor_piercing` `torpedo_attack` `sub_attack` `anti_air_attack` `armor_value` `surface_detection` `sub_detection` `surface_visibility` `naval_speed` `naval_range` `max_strength` `naval_dominance_factor` `naval_weather_penalty_factor` | `ship_hull_light.txt` |

> 想确认某个 stat 名是否有效：先在 `common/units/equipment/` 里 grep 到 2 个以上真实用例，再写进自己的文件。

---

## 3. `upgrades`（装备升级项）

定义在 `common/units/equipment/upgrades/{land,naval,air}_upgrades.txt`，顶层是 `upgrades = { ... }`。装备用 `upgrades = { tank_reliability_upgrade ... }` 引用。

原版 `common/units/equipment/upgrades/land_upgrades.txt`（第 3-41 行节选）：

```pdx
upgrades = {
	tank_nsb_engine_upgrade = {
		abbreviation = "eng"
		max_level = 20
		cost = land                 # 升级点类型：land / air / naval（花费由 defines 控制）

		linear_cost = {
			cost_by_level = 1
			cost_by_level_for_licensed_equipment = 5
		}

		level_requirements = {      # 某等级需要某科技
			5  = { has_tech = engine_tech_1 }
			10 = { has_tech = engine_tech_2 }
			15 = { has_tech = engine_tech_3 }
			18 = { has_tech = engine_tech_4 }
		}

		resource_cost_thresholds = { # 高等级追加资源成本（总值，非累加）
			10 = { }
		}

		reliability = -0.015
		add_stats = {
			fuel_consumption = 0.05
			build_cost_ic = 0.1
			maximum_speed = 0.1
		}
	}

	# 老式（5 级）升级项仍大量存在：
	tank_gun_upgrade = {
		max_level = 5
		cost = land
		soft_attack = 0.03
		hard_attack = 0.1
		ap_attack = 0.05
		maximum_speed = -0.02
		reliability = -0.05
		build_cost_ic = 0.05
	}
}
```

要点：
- 老式升级项直接把 stat 名写在升级项里（每级乘算/加算），新式（`*_nsb_*`）用 `add_stats` 明确加算。
- `level_requirements` 让「装备升级」与科技树挂钩，是 1.11+ 的机制。
- `cost = land/air/naval` 决定消耗哪条经验值，具体换算在 defines。

---

## 4. `equipment_modules`（模块，1.11+ 设计师系统）

模块定义在 `common/units/equipment/modules/00_tank_modules.txt`、`00_plane_modules.txt`、`00_ship_modules.txt`。顶层块名是 **`equipment_modules`**，可用 `limit = { }` 做 DLC 门控：

```pdx
# common/units/equipment/modules/00_tank_modules.txt 第 58-78 行
equipment_modules = {
	limit = {
		has_dlc = "No Step Back"
	}

	tank_gasoline_engine = {
		abbreviation = "gas"
		category = tank_engine_type      # 属于哪个模块类别（被 module_slots 的 allowed_module_categories 匹配）
		sfx = sfx_ui_sd_module_engine

		add_stats = {                    # 直接加算
			build_cost_ic = 1
			fuel_consumption = 2
			maximum_speed = 0.5
		}
		multiply_stats = {               # 乘算
			maximum_speed = 0.15
		}
	}
}
```

装备侧用 `module_slots` 声明槽位（完整语法见 `common/units/equipment/_documentation.md` 第 47-111 行）：

```pdx
# common/units/equipment/tank_chassis.txt 第 36-111 行（节选）
module_slots = {
	turret_type_slot = {                 # 固定槽建议 fixed_ 前缀；必须放在最前（原版注释：炮依赖炮塔）
		required = yes
		allowed_module_categories = { tank_light_turret_type }
	}
	main_armament_slot = {
		required = yes
		allowed_module_categories = { tank_small_main_armament tank_flamethrower }
	}
	engine_type_slot = {
		required = yes
		allowed_module_categories = { tank_engine_type }
	}
	special_type_slot_1 = {
		required = no
		allowed_module_categories = { tank_special_module tank_radio_module tank_secondary_turret }
	}
}
module_count_limit = { module = sloped_armor count < 2 }
module_count_limit = { category = tank_radio_module count < 2 }

# 继承写法（船/飞机变体常用）：
#   module_slots = inherit
#   fixed_ship_radar_slot = inherit
default_modules = {                 # 默认变体插什么
	fixed_ship_engine_slot = light_ship_engine_1
	mid_1_custom_slot = empty
}
```

模块还能给**任务白名单**：`00_plane_modules.txt` 里大量 `allow_mission_type = { naval_patrol }`，即「装了该模块的机型解锁该任务」。见 [air.md](air.md)。

---

## 5. `duplicate_archetypes`（1.19 派生装备的关键机制）

`x_tank_chassis.txt`、`x_plane_airframes.txt` 的顶层块是 **`duplicate_archetypes`**：以某个 archetype 为模板批量派生变体，并对派生结果做属性改写。

```pdx
# common/units/equipment/x_tank_chassis.txt 第 1-24 行（节选）
# This file must be evaluated after the file(s) defining the archetypes being duplicated.
duplicate_archetypes = {

	light_tank_aa_chassis = {
		archetype = light_tank_chassis
		type = { armor anti_air }
		for_each = {
			variant_name = { find_and_replace = { "chassis" "equipment" } }
			hardness = { set = 0.5 }
		}
	}

	light_tank_destroyer_chassis = {
		archetype = light_tank_chassis
		type = { armor anti_tank }
		for_each = {
			variant_name = { find_and_replace = { "chassis" "equipment" } }
		}
	}
}
```

```pdx
# common/units/equipment/x_plane_airframes.txt 第 1-20 行（节选）
duplicate_archetypes = {
	small_plane_cas_airframe = {
		archetype = small_plane_airframe
		type = cas
		picture = archetype_CAS_equipment
		variant_name = {
			small_plane_cas_airframe_1 = CAS_equipment_1
			small_plane_cas_airframe_2 = CAS_equipment_2
		}
		air_map_icon_frame = 2
		interface_overview_category_index = 0
		substitute = cv_small_plane_cas_airframe
	}
}
```

要点：
- 文件顶部注释明确：**必须在被复制的 archetype 定义之后求值**（加载顺序），所以文件名用 `x_` 前缀排在后面。
- `alias`、`type`、`variant_name`、`derived_variant_name` 这几个属性**不会**被复制，必须显式指定。
- ⚠️ `for_each` 内可用的算子（`find_and_replace`、`set` 等）是本机 `script_math_functions.md` + 原版用例归纳；更复杂的算子请查 `documentation/script_math_functions.md`。

---

## 6. `equipment_groups`（装备分组）

`common/equipment_groups/` 把多个装备类型聚成一组，供 MIO、加成、界面使用。官方文档 `common/equipment_groups/_documentation.md` 给的结构：

```pdx
useless_junk = {
	description = "Useless Junk"        # 可选，loc key
	equipment_type = {
		light_tank_chassis_0            # 可以是 type / archetype / category
		light_tank_chassis_1
		some_existing_group             # 也可以嵌套别的分组
	}
}

equipment_bonus = {
	useless_junk = {
		instant = yes
		build_cost_ic = -0.05
	}
}
```

原版实例：`common/equipment_groups/mio_equipment_groups.txt`（`mio_cat_eq_all_light_tank`、`mio_cat_eq_all_medium_tank`… 供 `common/military_industrial_organization/` 使用）。MIO 部分见 [../02_content/mio.md](../02_content/mio.md)。

---

## 7. 新增装备 vs 修改原版装备

| 做法 | 写法 | 优点 | 缺点 |
|---|---|---|---|
| A. 新增 archetype/变体 | 新文件 `common/units/equipment/hho_equipment.txt` 定义新 ID | 干净、不与原版冲突、易维护 | 需要在科技里 `enable_equipments`，需要设计师 GUI（若是底盘/机体），需要本地化与图标 |
| B. 同 ID 重定义原版装备 | 自己文件里把 `infantry_equipment_1 = { ... }` **整条**写全 | 改动立刻全局生效 | 同 ID 覆盖是**整条替换**，不是字段合并；原版更新会失效；影响 checksum 与多人 |
| C. 改 archetype 加 `equipment_bonus` | 国策/理念里 `add_equipment_bonus` 或学说里 `equipment_bonus` | 不动数据文件 | 只影响加成，不是「改基础值」 |

**推荐 A 或 C**；B 只在做总 overhaul 时用。

---

## 8. 最小可跑示例 1：新增一档步枪（变体）

```pdx
# 路径：<mod>/common/units/equipment/hho_infantry.txt
equipments = {

	HHO_rifle_1944 = {
		year = 1944
		archetype = infantry_equipment       # 必须是已存在的 archetype
		parent = infantry_equipment_3        # 继承上一个变体，少写字段
		priority = 10
		visual_level = 4

		defense = 42
		breakthrough = 6
		soft_attack = 14
		hard_attack = 3
		ap_attack = 12
		air_attack = 0
		build_cost_ic = 0.62
		reliability = 0.95
		resources = {
			steel = 3
		}
	}
}
```

科技里解锁（原版字段证据：`common/technologies/infantry.txt` 第 16-46 行）：

```pdx
# 路径：<mod>/common/technologies/hho_tech.txt
technologies = {
	HHO_infantry_weapons_1944 = {
		enable_equipments = { HHO_rifle_1944 }
		research_cost = 2
		start_year = 1944
		folder = { name = infantry_folder position = { x = 0 y = 200 } }
		path = { leads_to_tech = HHO_infantry_weapons_1945 research_cost_coeff = 1 }
	}
}
```

本地化（`localisation/simp_chinese/hho_equipment_l_simp_chinese.yml`，UTF-8 BOM）：
装备名 loc key = 装备 ID；同时原版通常还有 `_desc`。

```yml
l_simp_chinese:
 HHO_rifle_1944: "HHO-44 型步枪"
 HHO_rifle_1944_desc: "采用新型弹药与冲压工艺的制式步枪。"
```

---

## 9. 最小可跑示例 2：新增一个坦克底盘（1.19 正确做法）

1）**定义 archetype**（新文件，别改原版）：

```pdx
# 路径：<mod>/common/units/equipment/hho_tank_chassis.txt
equipments = {

	HHO_main_battle_chassis = {
		year = 1943
		is_archetype = yes
		is_buildable = no
		type = armor
		group_by = archetype
		interface_category = interface_category_armor
		picture = archetype_medium_tank_equipment
		priority = 2000

		module_slots = {
			turret_type_slot = {
				required = yes
				allowed_module_categories = { tank_medium_turret_type tank_light_turret_type }
			}
			main_armament_slot = {
				required = yes
				allowed_module_categories = { tank_small_main_armament tank_flamethrower }
			}
			suspension_type_slot = {
				required = yes
				allowed_module_categories = { tank_suspension_type }
			}
			armor_type_slot = {
				required = yes
				allowed_module_categories = { tank_armor_type }
			}
			engine_type_slot = {
				required = yes
				allowed_module_categories = { tank_engine_type }
			}
			special_type_slot_1 = {
				required = no
				allowed_module_categories = { tank_special_module tank_radio_module }
			}
		}

		maximum_speed = 9
		reliability = 0.85
		defense = 4
		breakthrough = 30
		hardness = 0.9
		armor_value = 20
		soft_attack = 16
		hard_attack = 12
		ap_attack = 20
		air_attack = 0
		lend_lease_cost = 12
		build_cost_ic = 14
		resources = {
			steel = 3
			tungsten = 1
		}
		fuel_consumption = 2.6
	}
}
```

2）**派生出具体变体**（如自行反坦克型），用 `duplicate_archetypes`：

```pdx
# 路径：<mod>/common/units/equipment/hho_tank_variants.txt
duplicate_archetypes = {
	HHO_tank_destroyer_chassis = {
		archetype = HHO_main_battle_chassis
		type = { armor anti_tank }
		for_each = {
			variant_name = { find_and_replace = { "chassis" "equipment" } }
		}
	}
}
```

3）**注册到设计师 GUI**（关键，不做的话生产界面里看不到）：

```pdx
# 路径：<mod>/interface/equipmentdesigner/tanks/tank_chassis_HHO_main_battle_chassis.gui
# 结构照抄原版 interface/equipmentdesigner/tanks/tank_chassis_light_tank.gui：
# 容器名 = equipment_designer_<archetype 名>，内部每个 module slot 一个同名子容器 + @highlight。
guiTypes = {
	containerWindowType = {
		name = "equipment_designer_HHO_main_battle_chassis"
		position = { x = 0 y = 0 }
		size = { width = 508 height = 248 }

		iconType = {
			name = "equipment_image_overlay"
			spriteType = "GFX_TC_HHO_main_battle_chassis"
			position = { x = 0 y = 0 }
		}
	}
}
```
> `GFX_TC_*` sprite 需要在 `interface/*.gfx` 里注册一张 508×248 的 DDS（见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)）。⚠️ 原版每个底盘按国家有多个 gui 文件（`_ger`/`_sov`/…），本机未见官方文档说明「只做一个通用的是否足够」，按最保险做法：至少提供通用版，再按国家追加。

4）**科技解锁** + 本地化（变体名的 loc key 由 `variant_name` 推导；原版变体名规则见 `x_plane_airframes.txt` 顶部注释）。

---

## 10. 与国策 / 事件 / 科技的联动

- 科技解锁：`enable_equipments = { <equipment id> }`、`enable_equipment_modules = { <module id> }`（原版 `common/technologies/infantry.txt` 第 18-26 行）。
- 国策/理念给装备加成：`add_equipment_bonus`（country scope，见 `documentation/effects_documentation.md` 第 1174 行）；**学说里不要用 effect 版**，要写 `equipment_bonus = { ... }` 数据块（见 [doctrines.md](doctrines.md)）。
- 租借/生产条件：`can_be_produced` 里可以写 `has_dlc`、`has_idea`、`has_tech` 等任意 trigger（原版 `tank_chassis.txt` 的保加利亚限制就是 `has_idea`）。
- 具体国策语法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)，科技全字段见 [../02_content/technologies.md](../02_content/technologies.md)。

---

## 11. 1.19 与旧教程的差异（实测）

1. **`common/equipment/` 不存在** → 只有 `common/units/equipment/`。
2. **坦克不再由 `tank_light.txt` 等文件定义**：这些文件在 1.19 被整段 `#` 注释，真正的定义是 `tank_chassis.txt`（archetype）+ `x_tank_chassis.txt`（`duplicate_archetypes` 派生）+ `modules/`。照 1.9~1.10 教程写 `light_tank_equipment = { ... }` 会得到「重复/无效定义」。
3. **飞机同理**：`plane_airframes.txt` + `x_plane_airframes.txt`。旧教程的 `fighter_equipment_1 = { ... }` 现在由 `duplicate_archetypes` 生成（其实体仍在 `x_plane_airframes.txt` 里可直接改，但要知道它在哪）。
4. **`upgrades` 两代并存**：老式 5 级升级项（`tank_gun_upgrade`）与新式 20 级 NSB 升级项（`tank_nsb_engine_upgrade` + `level_requirements`）。
5. **`duplicate_archetypes`、`module_slots`、`equipment_modules`、`equipment_groups`、`interface_overview_category_index`、`substitute`** 都是旧教程没有的字段。
6. **资源多了 `coal`**（`common/resources/00_resources.txt`，第 7 项），装备 `resources` 块里可以写 `coal = 1`。见 [../04_world/resources.md](../04_world/resources.md)。

---

## 12. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 装备定义（原型 + 变体） | `common/units/equipment/` | 51 个 `.txt`（顶层 45 + `modules/` 3 + `upgrades/` 3） | ✅ `_documentation.md`（125 行，`equipments` 全字段） |
| 坦克模块 | `common/units/equipment/modules/00_tank_modules.txt` | 2,291 行 | 同上 |
| 舰船模块 / 飞机模块 | `modules/00_ship_modules.txt`、`modules/00_plane_modules.txt` | 3,176 / 2,517 行 | 同上 |
| 升级项（陆/海/空） | `upgrades/{land,naval,air}_upgrades.txt` | 162 / 112 / 109 行 | 同上 |
| 装备分组 | `common/equipment_groups/` | 1 `.txt`（298 行）+ `_documentation.md` | ✅ `_documentation.md` |
| 原型 → 变体派生 | `tank_chassis.txt` → `x_tank_chassis.txt` 等（`duplicate_archetypes`） | 见 §5 | 同上 |
| 科技解锁入口 | `common/technologies/`（infantry / armor / artillery / support / air_techs / naval / MTG_naval …） | 13 文件 | ❌ |
| 设计师 GUI | `interface/equipmentdesigner/` | 270 文件（tanks 253 / planes 8 / ships 6） | ❌ |
| 装备 AI | `common/ai_equipment/` | 23 文件 | ✅ `_documentation.md` |

- **`common/units/equipment/_documentation.md` 是装备域唯一官方语法文档**：`module_slots`、`module_count_limit`、`default_modules`、`is_frame`、`ai_type`、`can_be_lend_leased` 都在里面，写模块槽前先读它。
- **原型文件里既有槽位也有基础数值**：`module_slots` 写 archetype 侧，变体常态是 `module_slots = inherit`（见 §4、§9）。想改"所有同类装备"改 archetype，改"某一档"改变体。
- **1.19.4 改过 `tank_chassis.txt` / `00_tank_modules.txt` / `sam_missile.txt`**：整文件覆盖时必须按现网内容抄全；`replace_path` 覆盖 `units/` 的 mod 还要重跑数值对表。

## 13. 常见错误 / 自检清单

- [ ] 文件在 `common/units/equipment/`，顶层块是 `equipments = { }`（模块文件是 `equipment_modules`，派生文件是 `duplicate_archetypes`）。
- [ ] 变体写了 `archetype = <已存在 archetype>`；`parent` 指向的是**变体**而不是 archetype。
- [ ] archetype 与变体的 `type` 一致（变体一般继承，不要乱写）。
- [ ] `interface_category` 用了合法值，否则生产界面不显示。
- [ ] 新增底盘/机体已在 `interface/equipmentdesigner/.../*.gui` 注册容器（原版 `plane_airframes.txt` 第 3 行注释明确要求）。
- [ ] 科技里有 `enable_equipments` / `enable_equipment_modules` / `enable_subunits`，否则永远是灰的。
- [ ] 有 loc key（装备名、`_desc`；底盘/机体的 loc key 命名与 `variant_name` 规则一致）。
- [ ] `resources` 里只写 `common/resources/00_resources.txt` 里存在的资源名。
- [ ] 用了 `duplicate_archetypes` 的文件名要让它在 archetype 之后加载（原版用 `x_` 前缀）。
- [ ] 同 ID 覆盖原版时是「整条替换」——必须把所有字段抄全。
- [ ] 改完重启；`logs/error.log` 搜装备 ID / 模块名。

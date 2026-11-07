---
title: 空军（Air）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/units/equipment/plane_airframes.txt
  - common/units/equipment/x_plane_airframes.txt
  - common/units/equipment/quad_engine_airframe.txt
  - common/units/air.txt
  - common/units/equipment/modules/00_plane_modules.txt
  - common/units/equipment/upgrades/air_upgrades.txt
  - common/defines/00_defines.lua
  - interface/equipmentdesigner/planes/plane_blueprints_generic.gui
  - common/ideas/air_spirits.txt
  - common/ai_equipment/_documentation.md
---

# 空军（Air）

**一句话**：空军 = **机体（airframe archetype）** + **机种变体（x_plane_airframes 派生）** + **机翼（sub_unit，100/10/3 架一队）**；可改的是数值、任务白名单、机翼大小、空战系数，**任务逻辑本身是硬编码的**。

---

## 1. 三层结构

```
small_plane_airframe / medium_plane_airframe / large_plane_airframe / ...
        （common/units/equipment/plane_airframes.txt，archetype）
                 ↓ duplicate_archetypes 派生
small_plane_cas_airframe / cv_small_plane_airframe / ... + 各等级变体
        （common/units/equipment/x_plane_airframes.txt 才是实体定义所在）
                 ↓ 再加机型
fighter / cv_fighter / cas / nav_bomber / strat_bomber / air_transport ...
        （common/units/air.txt，sub_unit，定义机翼大小）
```

原版参考：
- 机体 archetype：`common/units/equipment/plane_airframes.txt`（3213 行，`small_plane_airframe` 在文件最开头）
- 派生与实体：`common/units/equipment/x_plane_airframes.txt`（1743 行，`fighter_equipment_0`、`CAS_equipment_1`、`cv_fighter_equipment_0`…）
- 运输机/重型：`common/units/equipment/quad_engine_airframe.txt`、`twin_engine_airframe.txt`、`single_engine_airframe.txt`（部分内容已注释）
- 机种与机翼大小：`common/units/air.txt`（286 行）
- 模块：`common/units/equipment/modules/00_plane_modules.txt`
- 设计师 GUI：`interface/equipmentdesigner/planes/plane_blueprints_generic.gui`（796 行）

---

## 2. 机体 archetype（节选）

```pdx
# common/units/equipment/plane_airframes.txt 第 1-57 行
equipments = {

	#to make sure that an airframe appears in the air designer make sure to add it in
	#interface/equipmentdesigner/planes/plane_blueprints_generic.gui, otherwise it will not show up
	small_plane_airframe = {
		year = 1933

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
		is_convertable = yes
		picture = archetype_fighter_equipment
		is_buildable = no
		type = fighter                      # 默认机种
		type_override = fixed_main_weapon_slot
		allowed_types = {                   # ★同一机体能改成哪些机种
			fighter
			interceptor
			cas
			naval_bomber
			suicide
		}
		allow_mission_type = training       # ★任务白名单
		group_by = archetype
		sprite = light_plane
		air_map_icon_frame = 1
		interface_category = interface_category_air
		substitute = cv_small_plane_airframe
		interface_overview_category_index = 1

		air_superiority = 1
		reliability = 0.8
		naval_strike_attack = 1
		naval_strike_targetting = 1
		lend_lease_cost = 8
		manpower = 20
		fuel_consumption = 0.05
		build_cost_ic = 4
		resources = {
			aluminium = 2
			rubber = 1
		}

		module_slots = {
			fixed_main_weapon_slot = {
				required = yes
				allowed_module_categories = {
					fighter_weapon
					cas_weapon
					nav_bomber_weapon
					kamikaze_bomber_weapon
				}
			}
			fixed_auxiliary_weapon_slot_1 = { ... }
			engine_type_slot = {
				required = yes
				allowed_module_categories = { plane_engine_type twin_plane_engine_type }
			}
			special_type_slot_1 = { ... }
			special_type_slot_2 = { ... }
		}
	}
}
```

> **原版注释就是坑位提示**：第 3 行明确说「要让它出现在空军设计师里，必须在 `plane_blueprints_generic.gui` 里加条目」。这是改飞机最容易漏的一步。

---

## 3. 机种变体（真正可生产的东西）

```pdx
# common/units/equipment/x_plane_airframes.txt 第 167-205 行（早期陆基战斗机）
fighter_equipment_0 = {
	year = 1933
	archetype = small_plane_airframe
	priority = 5

	allow_mission_type = {
		air_superiority
		interception
	}

	air_range = 570
	maximum_speed = 330
	air_agility = 45
	air_attack = 9
	air_defence = 8
	naval_strike_attack = 1
	naval_strike_targetting = 10

	upgrades = {
		plane_gun_upgrade
		plane_range_upgrade
		plane_engine_upgrade
		plane_reliability_upgrade
	}

	air_superiority = 1
	reliability = 0.8

	# Air vs Navy - low damage / high hit chance / easy to hurt
	naval_strike_attack = 1
	naval_strike_targetting = 10
	surface_detection = 10   # For airwing of 100 planes
	sub_detection = 2.5

	lend_lease_cost = 8
}
```

```pdx
# 第 577-619 行（CAS）
CAS_equipment_1 = {
	year = 1936
	archetype = small_plane_cas_airframe
	priority = 40

	allow_mission_type = {
		cas                # ★对地支援任务名就是 cas
		naval_bomber
		port_strike
		attack_logistics
	}

	air_range = 700
	maximum_speed = 390
	air_agility = 35
	air_attack = 6
	air_defence = 14
	air_ground_attack = 8     # ★对地攻击（CAS 核心 stat）
	naval_strike_attack = 3
	...
}
```

```pdx
# common/units/equipment/quad_engine_airframe.txt 第 185-224 行（运输机）
transport_plane_equipment = {
	year = 1933
	allow_mission_type = {
		paradrop
		air_supply
	}
	is_archetype = yes
	is_convertable = yes
	type = air_transport
	...
	interface_overview_category_index = 6
}
```

### 3.1 任务白名单实测取值

在 `common/units/equipment/` 里 grep 到的 `allow_mission_type` token（**这些才是脚本能写的任务名**）：

`air_superiority`、`interception`、`naval_patrol`、`cas`、`naval_bomber`、`port_strike`、`attack_logistics`、`naval_mines_planting`、`naval_mines_sweeping`、`naval_kamikaze`、`recon`、`training`、`paradrop`、`air_supply`

> `training` 在机体 archetype 上（`allow_mission_type = training`），用于训练机。
> ⚠️ **战略轰炸（strategic bombing）没有出现在任何装备的 `allow_mission_type` 白名单里**，推测是按装备 `type = strategic_bomber` 默认授予；本机未见官方说明，做 mod 时若要限制/授予战略轰炸，先在本机实验或查 `documentation/` 与 wiki 再动手。

### 3.2 机翼大小（`common/units/air.txt`）

```pdx
# 第 4-48 行
fighter = {
	sprite = light_plane
	type = fighter
	need = { small_plane_airframe = 1 }
	categories = { category_fighter }
	land_air_wing_size = 100
	mega_carrier_air_wing_size = 10
}
cv_fighter = {
	need = { cv_small_plane_airframe = 1 }
	categories = { category_fighter category_carrier_fighter }
	carrier_air_wing_size = 10
	submarine_carrier_air_wing_size = 3    # 1.19：潜艇航母
	land_air_wing_size = 100
	mega_carrier_air_wing_size = 10        # 1.19：超级航母
}
```

- 陆基机翼 **100 架**，航母 **10 架**，潜艇航母 **3 架**，超级航母 **10 架**。
- 同一机体可以被覆盖成不同机种（`allowed_types`），所以「一个机体 5 种用途」是正常设计。

---

## 4. 空战与对地数值（defines 层）

`common/defines/00_defines.lua` 关键项：

| define | 值 | 作用 |
|---|---|---|
| `COMBAT_DAMAGE_STATS_MULTILPIER` | 0.2 | 空战伤害总系数（原版拼写就是 MULTILPIER） |
| `COMBAT_BETTER_AGILITY_DAMAGE_REDUCTION` | 0.45 | 机动优势减伤 |
| `COMBAT_BETTER_SPEED_DAMAGE_INCREASE` | 0.65 | 速度优势增伤 |
| `COMBAT_MAX_WINGS_AT_ONCE` | 10000 | 单场空战最大机翼数 |
| `COMBAT_MULTIPLANE_CAP` | 3.0 | 每架飞机可被多少架同时攻击 |
| `COMBAT_DAMAGE_SCALE` | 1 | 击落倍率 |
| `HOURS_DELAY_AFTER_EACH_COMBAT` | 4 | 空战间隔 |
| `AIR_COMBAT_FINAL_DAMAGE_SCALE` | 0.015 | 单次空战最大损失比例 |
| `LAND_AIR_COMBAT_STR_DAMAGE_MODIFIER` | 0.035 | 飞机对地强度伤害 |
| `LAND_AIR_COMBAT_ORG_DAMAGE_MODIFIER` | 0.035 | 飞机对地组织度伤害 |
| `LAND_AIR_COMBAT_MAX_PLANES_PER_ENEMY_WIDTH` | 3 | 每点敌方宽度可投入的 CAS/TAC |
| `AIR_SUPPORT_BASE` | 0.25 | CAS 对地支援基础系数 |
| `ENEMY_AIR_SUPERIORITY_IMPACT` | -0.35 | 敌方空优对地面防御的影响 |
| `ENEMY_AIR_SUPERIORITY_SPEED_IMPACT` | -0.3 | 敌方空优对移动速度的影响 |
| `ANTI_AIR_TARGETTING_TO_CHANCE` / `ANTI_AIR_ATTACK_TO_AMOUNT` | 0.07 / 0.005 | 地面防空对飞机的命中 |
| `AIR_WING_XP_AIR_VS_AIR_COMBAT_GAIN` | 0.8 | 空战经验获取 |
| `GROUND_ATTACK_...`（见文件） | — | 对地任务相关（推荐 grep `GROUND_ATTACK` 查看完整表） |

---

## 5. 最小可跑示例：新增一档「喷气战斗机」

**① 变体定义**（不改原版文件）：

```pdx
# 路径：<mod>/common/units/equipment/HHO_planes.txt
# ⚠️ 必须保证在原版 fighter_equipment_* 之后加载：用 x_/zz_ 前缀文件名最稳
equipments = {

	HHO_jet_fighter_1 = {
		year = 1944
		archetype = small_plane_airframe      # 复用原版机体
		priority = 200
		air_map_icon_frame = 1

		allow_mission_type = {
			air_superiority
			interception
		}

		air_range = 900
		maximum_speed = 760
		air_agility = 70
		air_attack = 36
		air_defence = 24
		air_ground_attack = 4
		naval_strike_attack = 2
		naval_strike_targetting = 10
		air_superiority = 1.25        # 制空值（空优贡献）
		reliability = 0.75

		build_cost_ic = 60
		resources = {
			aluminium = 4
			rubber = 2
		}
		lend_lease_cost = 12
		manpower = 30
		fuel_consumption = 0.6

		upgrades = {
			plane_gun_upgrade
			plane_range_upgrade
			plane_engine_upgrade
			plane_reliability_upgrade
		}
	}
}
```

**② 科技解锁**（`common/technologies/`）：

```pdx
technologies = {
	HHO_jet_fighter_tech = {
		enable_equipments = { HHO_jet_fighter_1 }
		research_cost = 2.5
		start_year = 1944
		folder = { name = air_techs_folder position = { x = 0 y = 200 } }
		path = { leads_to_tech = HHO_jet_fighter_tech2 research_cost_coeff = 1 }
	}
}
```

**③ 设计师注册**（必须）：

```pdx
# 路径：<mod>/interface/equipmentdesigner/planes/plane_blueprints_generic.gui
# 在 guiTypes = { ... } 里追加（容器名 = equipment_designer_<装备ID>）：
guiTypes = {
	containerWindowType = {
		name = "equipment_designer_HHO_jet_fighter_1"
		position = { x = 0 y = 0 }
		size = { width = 508 height = 248 }

		iconType = {
			name = "equipment_image_overlay"
			spriteType = "GFX_TC_HHO_jet_fighter_1"
			position = { x = 0 y = 0 }
		}
	}
}
```

**④ 本地化**：`HHO_jet_fighter_1: "HHO 喷气战斗机"`（+ `_desc`），放 `localisation/simp_chinese/`。

**⑤ 与国策/事件联动**：
- 科技解锁机体：`enable_equipments = { HHO_jet_fighter_1 }`（见 [../02_content/technologies.md](../02_content/technologies.md)）。
- 国策/理念给空军加成：`add_equipment_bonus = { bonus = { fighter = { air_attack = 0.05 } } }`（见 [../02_content/focus-trees.md](../02_content/focus-trees.md)）。
- 事件送飞机、设空优目标：先在 `documentation/effects_documentation.md` 检索确认 effect 名再写。

---

## 6. 1.19 与旧教程的差异（实测）

1. **机体/变体分层 + `duplicate_archetypes`**：旧教程写 `fighter_equipment_1 = { ... }` 的「一整块数值」；现在它在 `x_plane_airframes.txt` 里由 `duplicate_archetypes` 派生，机体字段在 `plane_airframes.txt`。
2. **`allow_mission_type` 白名单**：旧版飞机任务靠 `type` 隐式决定，现在每个变体显式列任务（token 见 3.1）。
3. **`allowed_types` / `type_override` / `substitute` / `interface_overview_category_index` / `air_map_icon_frame` / `air_superiority` / `air_ground_attack` / `naval_strike_targetting`** 等字段是旧教程没有的。
4. **1.19 新增超级航母与潜艇航母机翼大小**（`mega_carrier_air_wing_size`、`submarine_carrier_air_wing_size`）。
5. **设计师 GUI 变成硬性依赖**：原版自己都在 `plane_airframes.txt` 第 3 行写了这个要求。

---

## 7. 官方文档与实例文件位置（含系统入口，1.19.x）

路径相对 `<GAME_DIR>`（游戏安装根）。规模为 1.19.4.2 安装树实测（与 `.tmp/audit/game-survey.md` 同批采集），"官方文档"一栏指该路径下是否有 `_documentation.md`。

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 机种（air sub_unit：机翼与任务白名单） | `common/units/air.txt` | 1 文件 / 286 行 | ❌ |
| 机体 archetype | `common/units/equipment/plane_airframes.txt` | 1 文件 / 3,213 行 | ✅ 目录级 `common/units/equipment/_documentation.md`（125 行） |
| 机体派生/变体 | `x_plane_airframes.txt`、`single_engine_airframe.txt`、`twin_engine_airframe.txt`、`quad_engine_airframe.txt`（271 行） | 5 个 airframe 文件 | 同上 |
| 空军模块 | `common/units/equipment/modules/00_plane_modules.txt` | 2,517 行 | 同上 |
| 空军升级项 | `common/units/equipment/upgrades/air_upgrades.txt` | 109 行 | 同上 |
| 设计师界面容器 | `interface/equipmentdesigner/planes/` | 8 文件 | ❌ |
| 空军装备 AI | `common/ai_equipment/` | 23 文件（22 `.txt`） | ✅ `_documentation.md` |
| 空军精神 | `common/ideas/air_spirits.txt` | 1 文件 / 6,502 B | ❌ |
| 空战数值 | `common/defines/00_defines.lua` | 4,728 行 | ❌ |

- **任务类型（mission）不是数据文件**：没有 `common/air_missions/` 之类的目录，任务清单是硬编码枚举；脚本能表达的只有每个变体的 `allow_mission_type` 白名单（见 §3.1）与机翼尺寸字段。想"新增任务"只能动 UI/硬编码，不要在 `common/` 里找目录。
- **空军经验**：`MAX_AIR_EXPERIENCE = 500`（defines 第 893 行）；经验用于设计器解锁与精神，精神文件与陆军同构（见 [doctrines.md](doctrines.md) §7.1「军方经验与陆/海/空精神」）。
- **机体 / 模块 / 升级同目录**：改 `plane_airframes.txt` 影响同 archetype 的所有变体；改 `x_plane_airframes.txt` 只影响派生变体。这是本域最高频的误改。

## 8. 常见错误 / 自检清单

- [ ] 机体文件：`common/units/equipment/plane_airframes.txt`；变体实体：`x_plane_airframes.txt`；机种：`common/units/air.txt`。
- [ ] 新机体/新变体已经在 `interface/equipmentdesigner/planes/plane_blueprints_generic.gui` 注册（否则设计师里看不到）。
- [ ] `allow_mission_type` 里的 token 是第 3.1 节列表中的拼写（`cas` 不是 `close_air_support`）。
- [ ] 机翼大小字段用对：陆基 `land_air_wing_size`，航母 `carrier_air_wing_size`，潜艇航母 `submarine_carrier_air_wing_size`，超级航母 `mega_carrier_air_wing_size`。
- [ ] 科技有 `enable_equipments`；有 loc key 与图标。
- [ ] 用 `duplicate_archetypes` 时注意加载顺序（`x_` 前缀）。
- [ ] 改 `COMBAT_*` 空战 defines 影响全局与 checksum。
- [ ] 出错看 `logs/error.log`，搜装备 ID / 机体名。

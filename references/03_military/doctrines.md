---
title: 学说（Doctrines）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/doctrines/_documentation.md
  - common/doctrines/folders/_documentation.md
  - common/doctrines/grand_doctrines/_documentation.md
  - common/doctrines/tracks/_documentation.md
  - common/doctrines/subdoctrines/_documentation.md
  - common/doctrines/folders/doctrine_folders.txt
  - common/doctrines/grand_doctrines/land_grand_doctrines.txt
  - common/doctrines/tracks/land_doctrine_tracks.txt
  - common/doctrines/subdoctrines/land/armor_subdoctrines.txt
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/ideas/army_spirits.txt
  - common/defines/00_defines.lua
---

# 学说（Doctrines）

> **这是 1.19 与旧教程差异最大的一块。** 旧教程里的「陆军四条学说树、`path = { ... }` 逐级点、`xp_cost` 线性」已经整体被替换为一套**文件夹 + 大教义 + 轨道 + 子教义 + 精通度 + 奖励**系统。本文件完全基于本机 `common/doctrines/` 的 5 份 `_documentation.md` 与原版文件写成。

**一句话**：玩家先选一个 **Grand Doctrine（大教义，互斥根）** → 解锁若干 **Track（轨道）** → 在每条轨道里选一个 **Subdoctrine（子教义）** → 靠 **Mastery（精通度，由对应兵种的人力贡献累积）** 自动解锁 **Reward（奖励）** → 走完轨道拿 **Milestone（里程碑）**。

---

## 1. 目录结构（1.19.x 实测）

```
common/doctrines/
├── _documentation.md                      # 概念 + effect/trigger/modifier 清单
├── folders/
│   ├── _documentation.md
│   └── doctrine_folders.txt               # land / naval / air / special_forces
├── grand_doctrines/
│   ├── _documentation.md
│   ├── land_grand_doctrines.txt           # new_mobile_warfare / superior_firepower / grand_battleplan / mass_assault
│   ├── sea_grand_doctrines.txt            # new_fleet_in_being / new_convoy_raiding / new_base_strike
│   ├── air_grand_doctrines.txt            # new_strategic_destruction / new_battlefield_support / new_operational_integrity
│   └── special_forces_grand_doctrines.txt # special_forces_quantity / special_forces_quality（需 DLC）
├── tracks/
│   ├── _documentation.md
│   ├── land_doctrine_tracks.txt           # infantry / combat_support / armor / operations
│   ├── sea_doctrine_tracks.txt
│   ├── air_doctrine_track.txt
│   └── special_forces_tracks.txt
└── subdoctrines/
    ├── _documentation.md
    ├── land/     # armor_subdoctrines.txt / combat_support_subdoctrines.txt / infantry_subdoctrines.txt / operations_subdoctrines.txt
    ├── sea/  air/  special_forces/
```

原版四大学说文件夹（`common/doctrines/folders/doctrine_folders.txt`）：`land`、`naval`、`air`、`special_forces`。
**注意脚本名是 `naval` 不是 `sea`**：`sea_grand_doctrines.txt` / `sea_doctrine_tracks.txt` 是文件名，但 `folder = naval`（见该文件第 2 行）。

---

## 2. 四层对象与字段

### 2.1 Folder（文件夹）

```pdx
# common/doctrines/folders/doctrine_folders.txt 第 1-12 行
land = {
	allowed = { always = yes }         # 不满足则整个文件夹不可用
	name = "land_doctrine_folder"      # loc key
	ledger = army                      # army / navy / air / all / hidden（情报 ledger 里显示在哪）
	ledger_gfx = GFX_land_doctrine_folder_icon
	tab_gfx = GFX_landdoctrine_tab_large
	color_frame = 1
	sound = ui_doctrine_tab_land
}
```

`special_forces` 额外有 DLC 门控：

```pdx
special_forces = {
	allowed = {
		OR = {
			has_dlc = "No Compromise, No Surrender"
			has_dlc = "Arms Against Tyranny"
		}
	}
	...
}
```

> 你可以自定义一个新 folder（名字任意），但对新玩家来说自定义 folder 需要额外的 UI/图标资源；最小改动建议挂到现有 4 个 folder 下。

### 2.2 Grand Doctrine（大教义）

```pdx
# 结构见 common/doctrines/grand_doctrines/_documentation.md；
# 实例见 land_grand_doctrines.txt 第 1-37 行
new_mobile_warfare = {
	folder = land
	name = GRAND_DOCTRINE_MOBILE_WARFARE
	description = GRAND_DOCTRINE_MOBILE_WARFARE_DESC
	icon = GFX_doctrine_mobile_warfare_medium
	available = { always = yes }        # 可选条件
	# visible = { ... }                 # 可选：是否显示

	xp_cost = 100
	xp_type = army                      # army / navy / air

	ai_will_do = {
		base = 1
		modifier = { factor = 0 is_major = no }
	}

	tracks = {                          # 解锁哪些轨道
		infantry
		combat_support
		armor
		operations
	}
	max_track_rows = 2                  # 可选，默认不限
	max_track_columns = 2               # 可选，默认不限

	# ↓ 激活时的效果（见第 3 节）
	planning_speed = 0.20
	army_speed_factor = 0.10
	enable_tactic = tactic_unexpected_thrust

	milestones = {                      # ★数量与 tracks 顺序一一对应
		{ org_loss_when_moving = -0.15 land_reinforce_rate = 0.02 enable_tactic = tactic_delay }
		{ planning_speed = 0.1 org_loss_at_low_org_factor = -0.1 enable_tactic = tactic_overwhelming_fire }
		{ additional_brigade_column_size = 1 enable_tactic = tactic_blitz }
		{ ... }
	}
}
```

### 2.3 Track（轨道）

```pdx
# common/doctrines/tracks/land_doctrine_tracks.txt 第 1-45 行
infantry = {
	name = DOCTRINE_TRACK_INFANTRY
	background = "GFX_grand_battleplan_bg"
	icon = "GFX_doctrine_milestone_infantry_land"
	icon_frame = "GFX_doctrine_decor_land"

	mastery = {                         # ★精通度怎么积累
		multiplier = 1.0
		categories = { category_all_infantry }   # 哪些营的伤亡/人力贡献精通
		# sub_units = { ... }             # 也可按具体营
		# equipment = { ... }             # 也可按装备类别
	}
}

combat_support = {
	name = DOCTRINE_TRACK_COMBAT_SUPPORT
	background = "GFX_sup_firepower_bg"
	icon = "GFX_doctrine_milestone_artillery_land"
	mastery = {
		multiplier = 8.0
		categories = { category_line_artillery category_artillery category_support_battalions }
	}
}
```

Track 还支持 `background_offset`、`frame`、`active = { <trigger> }`（轨道内子教义可选的额外条件）。

### 2.4 Subdoctrine（子教义）

```pdx
# common/doctrines/subdoctrines/land/armor_subdoctrines.txt 第 1-50 行（节选）
armored_spearhead = {
	track = armor                        # 也能写列表 { infantry armor }
	# allow_in_multiple_tracks = yes     # 可选：允许同时挂在多条轨道
	name = SUBDOCTRINE_ARMORED_SPEARHEAD
	description = SUBDOCTRINE_ARMORED_SPEARHEAD_DESC
	icon = GFX_doctrine_armored_spearhead_medium

	xp_cost = 100
	xp_type = army

	available = { always = yes }
	visible = { has_dlc = "La Resistance" }

	ai_will_do = {
		base = 1
		modifier = { factor = 25 original_tag = GER }
		modifier = { factor = 0.5 is_major = no }
	}

	# ↓ 激活效果（见第 3 节）
	enable_tactic = tactic_breakthrough

	rewards = {                          # ★奖励：按精通度依次自动解锁
		force_concentration = {          # 命名键 = 本地化前缀（见下）
			category_tanks = {
				max_organisation = 2
				default_morale = 0.05
			}
		}
		armored_breakthrough_exploits = {
			category_all_armor = { breakthrough = 0.1 }
		}
		local_reserves = {
			armored_car = { default_morale = 0.1 max_organisation = 7 }
			category_self_propelled_anti_air_regimental_support = {
				max_organisation = 5
				air_attack = 0.05
			}
		}
	}

	# 可选：覆盖轨道的精通度条件
	# mastery = { multiplier = 5.0 sub_units = { bicycle_battalion } }

	# 可选：同文件夹内互斥（不同轨道不能同时选）
	# xor = { other_subdoctrine_a other_subdoctrine_b }
}
```

`subdoctrines/_documentation.md` 明确：**奖励的 loc key 是 `<sub_doctrine_key>_<reward_key>(_desc)`**，因为 reward 不是真正的数据库对象。

---

## 3. 四层通用的「激活效果」语法

`grand_doctrines/_documentation.md` 的 "Scripting Activation Effects" 适用于 Grand / Milestone / Subdoctrine / Reward：

```pdx
# ① 直接写国家 modifier（推荐，等同于 modifiers 块）
planning_speed = 0.4
army_speed_factor = 0.10

# ② 显式 modifiers 块（等价写法）
modifiers = {
	planning_speed = 0.4
	army_speed_factor = 0.10
}

# ③ 解锁战术
enable_tactic = tactic_unexpected_thrust

# ④ 按营类别/具体营加成（这才是「师属性加成」的正规写法）
category_tanks = {
	max_organisation = 1
}
armored_car = {
	max_organisation = 2
}

# ⑤ 装备加成（★官方文档明确：不要用 add_equipment_bonus effect，
#    因为换学说时 effect 加成不会移除）
equipment_bonus = {
	capital_ship = {
		naval_range = 0.10
		instant = yes
	}
}

# ⑥ 任意 scripted effect
effect = {
	add_tech_bonus = {
		bonus = 0.5
		uses = 1
		category = cat_light_armor
		name = [GRAND_DOCTRINE_NAME_LOC_KEY]
	}
}
```

配套的 **effect / trigger / modifier**（`common/doctrines/_documentation.md` 第 13-63 行）：

- Effects：`set_grand_doctrine`、`set_sub_doctrine`、`add_mastery`、`add_daily_mastery`、`add_mastery_bonus`（都在 `documentation/effects_documentation.md` 里，scope=COUNTRY；`add_mastery` 支持 `folder/grand_doctrine/sub_doctrine/track/index` 过滤）。
- Triggers：`has_completed_subdoctrine`、`has_doctrine`、`has_completed_track`、`has_subdoctrine_in_track`、`has_mastery`、`has_mastery_level`（在 `documentation/triggers_documentation.md`）。
- Modifiers（自动生成本地化，不用手写 loc）：
  - `<folder>_doctrine_cost_factor`（如 `land_doctrine_cost_factor = -0.15`）
  - `<folder>_track_mastery_gain_factor`（如 `land_track_mastery_gain_factor = 0.15`）
  - `<grand_doctrine>_mastery_gain_factor`、`<subdoctrine>_mastery_gain_factor`、`<track>_track_mastery_gain_factor`

---

## 4. 最小可跑示例：新增一条子教义 + 一个大教义

### 4.1 新增子教义（挂到原版 `infantry` 轨道）

```pdx
# 路径：<mod>/common/doctrines/subdoctrines/land/HHO_land_subdoctrines.txt
HHO_people_defense = {
	track = infantry
	name = HHO_SUBDOCTRINE_PEOPLE_DEFENSE
	description = HHO_SUBDOCTRINE_PEOPLE_DEFENSE_DESC
	icon = GFX_doctrine_armored_spearhead_medium    # 复用原版图标（自绘图标见 05_presentation）

	xp_cost = 100
	xp_type = army

	available = { always = yes }
	visible = { always = yes }

	ai_will_do = {
		base = 1
		modifier = { factor = 0.5 is_major = no }
	}

	enable_tactic = tactic_guerrilla_tactics

	rewards = {
		HHO_local_militia = {
			category_all_infantry = {
				defence = 0.05
				max_organisation = 2
			}
		}
		HHO_fortified_line = {
			category_all_infantry = { entrenchment = 0.5 }
			category_army = { org_loss_when_moving = -0.1 }
		}
		HHO_national_redoubt = {
			# 走 scripted effect 路线：任何合法 effect 都可以
			effect = {
				add_stability = 0.05
				add_war_support = 0.05
			}
		}
	}
}
```

> 奖励块里能写的东西 = 第 3 节列的「激活效果」：国家 modifier、`modifiers = { }`、`enable_tactic`、兵种/单位 stat 加成、`equipment_bonus`、`effect = { <任意 effect> }`。所有 modifier / effect 名请查 `documentation/modifiers_documentation.md` 与 `documentation/effects_documentation.md`。

**本地化**（reward 的 key 规则）：

```yml
l_simp_chinese:
 HHO_SUBDOCTRINE_PEOPLE_DEFENSE:0 "人民防御"
 HHO_SUBDOCTRINE_PEOPLE_DEFENSE_DESC:0 "以国土纵深与民兵体系拖垮侵略者。"
 HHO_people_defense_HHO_local_militia:0 "地方民兵"
 HHO_people_defense_HHO_local_militia_desc:0 "步兵防御与组织度提升。"
 HHO_people_defense_HHO_fortified_line:0 "筑垒防线"
 HHO_people_defense_HHO_fortified_line_desc:0 "堑壕加成提升。"
```

### 4.2 新增大教义（复用原版轨道）

```pdx
# 路径：<mod>/common/doctrines/grand_doctrines/HHO_land_grand_doctrines.txt
HHO_people_war = {
	folder = land
	name = HHO_GRAND_DOCTRINE_PEOPLE_WAR
	description = HHO_GRAND_DOCTRINE_PEOPLE_WAR_DESC
	icon = GFX_doctrine_mobile_warfare_medium

	available = { always = yes }

	xp_cost = 120
	xp_type = army

	ai_will_do = {
		base = 1
		modifier = { factor = 0.2 is_major = yes }
	}

	tracks = {
		infantry
		combat_support
	}

	planning_speed = 0.10
	army_speed_factor = 0.05
	enable_tactic = tactic_delay

	milestones = {
		{
			# 第 1 个轨道（infantry）的里程碑
			land_reinforce_rate = 0.02
			effect = { add_stability = 0.03 }
		}
		{
			# 第 2 个轨道（combat_support）的里程碑
			org_loss_at_low_org_factor = -0.1
			enable_tactic = tactic_overwhelming_fire
		}
	}
}
```

**这条大教义会成为 `land` 文件夹里的第 5 个互斥根**；因为复用了原版 `infantry` / `combat_support` 轨道，轨道定义不用重写。子教义 `HHO_people_defense` 会自动出现在这条大教义的 `infantry` 轨道里（只要 `track = infantry`）。

**本地化**：

```yml
l_simp_chinese:
 HHO_GRAND_DOCTRINE_PEOPLE_WAR:0 "人民战争"
 HHO_GRAND_DOCTRINE_PEOPLE_WAR_DESC:0 "以广土众民对抗工业强权。"
```

### 4.3 用国策/事件强制设置学说（联动 content）

```pdx
# 国策 completion_reward 里（country scope）
completion_reward = {
	set_grand_doctrine = HHO_people_war
}
# 或给精通度
completion_reward = {
	add_mastery = {
		amount = 100
		folder = land
		track = infantry
	}
}
```
国策写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)；effect 全表见 [../01_script/effects-triggers.md](../01_script/effects-triggers.md)。

---

## 5. 图标与界面

- Grand/Subdoctrine 的 `icon`、Track 的 `background` / `icon` / `icon_frame` 都是 **GFX sprite 名**（`GFX_` 前缀），必须在 `interface/*.gfx` 里注册真实 DDS 贴图，否则界面空白。
- `frame`/`background` 建议直接复用原版 `GFX_grand_battleplan_bg`、`GFX_sup_firepower_bg`、`GFX_mob_warfare_bg`、`GFX_tac_operation_bg`、`GFX_doctrine_decor_land` 等（原版 track 文件里就是这么用的）。
- 贴图规范见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)。

---

## 6. 1.19 与旧教程的差异（重点）

1. **旧版是「4 条陆军学说树，每级一个 tech 式节点」**；1.19 是「大教义 + 轨道 + 子教义 + 精通度」，`common/doctrines/land/*.txt` 这种老目录**不存在**。本机 `common/doctrines/` 下只有 `folders/ grand_doctrines/ tracks/ subdoctrines/` 四个子目录 + 5 个 `_documentation.md`。
2. **旧字段 `path = { ... }` 用于逐级推进**——现在 `path` 属于 `common/technologies/`，学说里没有它。
3. **新概念**：`xp_type`（army/navy/air 经验）、`track`、`mastery`、`rewards`、`milestones`、`xor`、`allow_in_multiple_tracks`、`max_track_rows/columns`。
4. **新 modifier**：`*_doctrine_cost_factor`、`*_track_mastery_gain_factor`、`*_mastery_gain_factor`。
5. **新 effect/trigger**：`set_grand_doctrine`、`set_sub_doctrine`、`add_mastery`、`add_mastery_bonus`、`has_doctrine`、`has_mastery_level` 等。
6. **第 4 个文件夹 `special_forces` 需要 DLC**（`No Compromise, No Surrender` 或 `Arms Against Tyranny`）。

---

## 7. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 大教义 | `common/doctrines/grand_doctrines/` | 4 `.txt`（air/land/sea/special_forces）+ `_documentation.md` | ✅ |
| 子教义 | `common/doctrines/subdoctrines/` | 13 `.txt`（air 4 / land 4 / sea 4 / special_forces 1）+ `_documentation.md` | ✅ |
| 轨道（track） | `common/doctrines/tracks/` | 4 `.txt` + `_documentation.md` | ✅ |
| 文件夹（folder） | `common/doctrines/folders/` | 1 `.txt`（`doctrine_folders.txt`）+ `_documentation.md` | ✅ |
| 根级说明 | `common/doctrines/_documentation.md` | 1,899 B | ✅ |
| 精神（XP 的另一去处） | `common/ideas/{army,air,navy}_spirits.txt` | 26,824 / 6,502 / 16,990 B | ❌ |
| 经验上限 | `common/defines/00_defines.lua` | `MAX_{ARMY,NAVY,AIR}_EXPERIENCE = 500`（891-893 行） | ❌ |

合计 27 文件（22 `.txt` + 5 `_documentation.md`）/ 9,025 行——**`common/` 下官方文档密度最高的子域**，字段疑问先读 doc 再试。

### 7.1 军方经验与陆/海/空精神

- 教义节点用 `xp_type = army|navy|air` 标明消耗哪一军经验；三军经验各自存储、上限均 500（defines 891-893 行），"经验花在教义还是精神"是真实取舍。
- **精神不在 `common/doctrines/`，而在 ideas**：`common/ideas/army_spirits.txt` 顶层是 `ideas = { academy_spirit = { ... } army_spirit = { ... } }` 两级块：

```
ideas = {
	academy_spirit = {
		bold_attack_spirit = {
			ledger = army
			available = { has_military_academy = yes }
			modifier = { custom_modifier_tooltip = bold_attack_spirit_tt }
			...
		}
	}
	army_spirit = {
		elevated_engineering_corps_spirit = {
			ledger = army
			modifier = { unit_engineer_design_cost_factor = -1 dig_in_speed_factor = 0.1 railway_gun_bombardment_factor = 0.25 }
			...
		}
	}
}
```

- `academy_spirit` 需 `available = { has_military_academy = yes }`（军校）才可选；`army_spirit` 是常规精神。
- 原版每条都写 `ledger = army`（海军/空军用 `navy`/`air`），它决定该精神出现在哪个军种界面——漏写就"定义了但看不见"。
- 自定义精神 = 在对应块加条目（文件 26 KB，**整文件替换**）+ 写 loc key（`<id>`、`<id>_tt`）+ 需要时给 `has_idea`。

## 8. 常见错误 / 自检清单

- [ ] 文件在 4 个子目录之一，**不要**再建 `common/doctrines/land/`。
- [ ] `folder = land/naval/air/special_forces`（是 `naval` 不是 `sea`）。
- [ ] `track` 引用的轨道 ID 在 `tracks/` 里存在；`tracks = { }` 里的 ID 也一样。
- [ ] `milestones` 的**数量与顺序**与 `tracks` 一致（原版注释明确）。
- [ ] 奖励块里只写合法 modifier / `effect = { }` / `equipment_bonus`；reward 的 loc key 按 `<subdoctrine>_<reward>_desc` 生成。
- [ ] 学说里给装备加成用 `equipment_bonus` 数据块，**不要**用 `add_equipment_bonus` effect（换学说不会移除）。
- [ ] 所有 `icon`/`background`/`frame` 的 `GFX_` 名真实存在。
- [ ] `available` / `visible` 里的 trigger 合法（查 `documentation/triggers_documentation.md`）。
- [ ] 想改「学说成本/精通速度」用 modifier（`*_doctrine_cost_factor` 等），不要改 defines。
- [ ] 出错在 `logs/error.log` 搜学说 ID；缺 loc 会显示 key。

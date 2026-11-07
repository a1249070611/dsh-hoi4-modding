---
title: 特殊项目（Special Projects）
domain: 02_content
scope: country / special_project
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/special_projects/special_projects_documentation.md
  - common/special_projects/projects/documentation.md
  - common/special_projects/projects/nuclear_projects.txt
  - common/special_projects/prototype_rewards/generic_land_prototype_rewards.txt
  - common/special_projects/specialization/documentation.md
  - common/buildings/00_buildings.txt
  - history/countries/GER - Germany.txt
  - documentation/effects_documentation.md
---

# 特殊项目（Special Projects）

特殊项目 = 在**设施（facility）**里、由**科学家**推进的「原型研发」，产出装备型号/模块/建筑/科技等奖励。
1.19.4.2 的原版权威说明（设计草案 + 三篇子系统规范 + 真实数据）都在 `common/special_projects/` 下。

## 1. 文件放哪 / 命名 / 原版参考

| 内容 | 路径 | 原版参考 |
|---|---|---|
| 专精（specialization） | `common/special_projects/specialization/specializations.txt` | `documentation.md`（同目录） |
| 项目（project） | `common/special_projects/projects/*.txt` | `nuclear_projects.txt`、`land_projects.txt`、`air_projects.txt`、`naval_projects.txt`、`rocket_projects.txt`、`radar_projects.txt` |
| 项目标签 | `common/special_projects/project_tags/tags.txt` | `project_tags = { sp_tag_tank ... }` |
| 通用原型奖励 | `common/special_projects/prototype_rewards/generic_*.txt` | `generic_land_prototype_rewards.txt` |
| 设施建筑 | `common/buildings/00_buildings.txt` | `nuclear_facility:501`、`air_facility:535`、`land_facility:559`（`specialization = { specialization_x }`） |
| 科学家特质 | `common/scientist_traits/00_traits.txt` | 语法见 [characters.md](characters.md) 的 scientist 段 |
| 科学家角色 | `common/characters/*.txt` | `scientist = { ... }` 块 |

**顶层结构**：每个项目文件直接是 `<project_token> = { ... }`（无包裹层）。
**本地化**：`<tag>_<token>` 优先，否则 `<token>`；描述 `<token>_desc`（`projects/documentation.md:65-96`）。
**DLC**：多数核项目写 `allowed = { has_dlc = "Gotterdammerung" }`（`nuclear_projects.txt:282-284、426-428、719-721、822-824`）；
没有该 DLC 时系统仍在，但项目池几乎为空。

**官方文档位置（1.19.4.2 实测，4 篇，合计 34 KB）**：

| 文件 | 行数 | 讲什么 |
|---|---|---|
| `common/special_projects/special_projects_documentation.md` | 701 | **设计草案**（含 `# UP TO DEBATE` 自注），讲概念、专精/设施设计意图，字段与实现有出入 |
| `common/special_projects/projects/documentation.md` | 283 | **项目字段的真实规范**（生命周期、`breakthrough_cost`、`narrative`、`project_output` 三个 effect 块）——以它为准 |
| `common/special_projects/prototype_rewards/documentation.md` | 134 | 原型奖励字段（`threshold`/`weight`/`allowed`/`option`） |
| `common/special_projects/specialization/documentation.md` | 48 | 专精字段 + 与 `common/buildings` 设施建筑的一一对应 |

目录规模：17 个文件、14,805 行。1.19.4 的两批脚本改动清单里没有 `common/special_projects/`，本域字段未动。

## 2. 项目生命周期（`projects/documentation.md:6-20`）

1. **Establishing phase**（建立阶段）：开始/重启项目时走一遍；中途取消则从头开始。
2. **Initial research phase**（初始研究）：只走一次；中途取消会记住进度。
3. **Prototyping phase**（原型迭代）：反复迭代，进度到 100% 即项目完成；`complexity` 决定每次迭代获得的进度。

## 3. 结构（带注释；以真实文件为准）

```pdx
HHO_project_token = {
	specialization = specialization_land        # 必填，决定在哪个设施里研发
	icon = GFX_sp_nuclear_reactor               # 可选，回退 GFX_<token>
	blueprint_image = GFX_generic_tank_blueprint_background  # 可选，覆盖专精默认蓝图背景
	facility_model = facility_type_entity       # 可选，覆盖设施模型

	project_tags = sp_tag_tank                  # 可选，见 common/special_projects/project_tags/tags.txt

	allowed = { }                               # 可选，**国家作用域**，开局建项目池（只宜用 tag/original_tag/has_dlc）
	visible = { }                               # 可选，项目作用域，FROM = 国家
	available = {                               # 可选，项目作用域，FROM = 国家（真实文件里 FROM 才是国家）
		FROM = { has_tech = atomic_research }
	}

	resource_cost = {                           # 可选，研究期间持续消耗资源（油不可用）
		resources = { steel = 6 tungsten = 3 }
	}

	prototype_time = sp_time.prototype.long     # 每次迭代耗时（原版用 script constant；也可写数字）
	complexity = sp_complexity.large            # 每次迭代进度（原版用 script constant；也可写数字）

	breakthrough_cost = {                       # 可选，启动需要的突破点（projects/documentation.md:53-63）
		specialization_land = 2
	}

	# ---- 完成时产出 ----
	project_output = {
		# ⚠️ 设计草案 special_projects_documentation.md:107-117 写的是裸 effects = { ... }，别照抄。
		# 真实规范在 projects/documentation.md:198-281，共 3 个 effect 包装块（nuclear_projects.txt:21-64 是实例）：
		#   country_effects（country 作用域，FROM = project）
		#   facility_state_effects（state 作用域，可用 var:facility_province_id）
		#   scientist_effects（character 作用域）—— 脚本直接完成项目时可能没有科学家，该块会被跳过
		country_effects = {
			custom_override_tooltip = {
				tooltip = {
					localization_key = SP_UNLOCK_BUILDING_ICON_DESC
					BUILDING = nuclear_reactor
				}
				set_technology = { nuclear_reactor = 1 popup = no }
			}
		}
		facility_state_effects = {
			set_building_level = { type = nuclear_reactor level = 1 }
		}
		# scientist_effects = { retire = yes }

		# 也可以直接给装备/单位加成（与理念同构，见 projects/documentation.md:266-281）
		# equipment_bonus = { armor = { reliability = 0.1 } instant = yes }   # instant = yes 才作用于已有型号
		# sub_unit_bonus = { cavalry = { soft_attack = 0.05 } }
		# enable_equipments = { anti_tank_equipment_3 }
		# enable_equipment_modules = { tank_medium_howitzer_2 }
		# enable_subunits = { limit = { has_dlc = "..." } infantry }
	}

	# ---- 迭代奖励 ----
	generic_prototype_rewards = {               # 引用通用奖励 token（可复用）
		sp_nuclear_scientist_xp_generic_reward
	}
	unique_prototype_rewards = {                # 本项目专属奖励（token = { ... }）
		HHO_reward_armor_breakthrough = {
			narrative = {
				name = HHO_reward_armor_breakthrough
				desc = HHO_reward_armor_breakthrough_desc
			}
			icon = GFX_sp_nuclear_reactor
			fire_only_once = yes
			threshold = { min = 35 max = 75 }
			weight = { base = 2 }

			option = {
				token = HHO_reward_armor_breakthrough_option
				iteration_output = {
					country_effects = {
						add_stability = 0.01
					}
				}
			}
		}
	}

	special_project_parent = { earlier_project } # 可选，前置项目（全部完成后才出现）
	ai_will_do = { factor = 1 }                  # 可选
}
```

### 专精（specialization）

```pdx
HHO_specialization_token = {
	icon = GFX_specialization_land
	blueprint_image = GFX_blueprint
	program_background = GFX_blueprint
	color = { 24 43 23 }        # <b, r, g>
}
```

- **必须与建筑对齐**：`common/buildings/00_buildings.txt` 里要有建筑带 `specialization = { <token> }`（`specialization/documentation.md:5-7`）。
- 本地化：`<tag>_<token>` → `<token>`。

### 突破点（breakthrough）

- 国家通过 `add_breakthrough_progress = { specialization = specialization_land value = 1.0 }` 积累（`effects_documentation.md:807-828`）。
- 历史文件里就写了（`history/countries/GER - Germany.txt:19-32`：land 1.0 / naval 0.8 / air 0.3）。
- 也支持 `specialization = all`（`effects_documentation.md:823-828`）。
- 原版常量 `sp_breakthrough_progress.medium` 可直接当 value（同文档 830-834）。

## 4. 脚本里怎么访问特殊项目

| 类型 | 写法 | 证据 |
|---|---|---|
| effect：直接完成 | `complete_special_project = sp:my_project`（COUNTRY 作用域） | `effects_documentation.md:2896-2923` |
| effect：直接完成（带选项） | `complete_special_project = { project = sp:my_project scientist = xxx state = 123 iteration_output = { my_reward } }` | 同上 |
| effect：加进度（项目作用域） | `sp:my_project = { add_project_progress_ratio = 0.1 }` | `effects_documentation.md:1909-1922` |
| effect：加突破点 | `add_breakthrough_progress = { specialization = specialization_land value = 1 }` | `effects_documentation.md:807` |
| 作用域前缀 | `sp:<token>`，变量用 `var:<name>` | `effects_documentation.md:2906-2908` |
| trigger：项目是否已完成 | `is_special_project_completed = sp:sp_nuclear_bomb` | 原版用例 `common/raids/categories/raid_categories.txt:25` |

## 5. 最小可跑完整示例

文件：`common/special_projects/specialization/specializations.txt` 追加（若原版没有对应专精）——
示例直接用原版 `specialization_land`，所以**这一节可以跳过**。

文件：`common/special_projects/projects/HHO_steel_projects.txt`

```pdx
HHO_advanced_steel_plating = {
	specialization = specialization_land
	icon = GFX_sp_nuclear_reactor
	complexity = sp_complexity.large
	prototype_time = sp_time.prototype.long

	project_tags = sp_tag_tank

	allowed = {
		original_tag = SWE
	}
	available = {
		FROM = { has_tech = infantry_weapons1 }
	}

	resource_cost = {
		resources = { steel = 5 tungsten = 2 }
	}

	breakthrough_cost = {
		specialization_land = 1
	}

	project_output = {
		country_effects = {
			add_ideas = HHO_steel_alloys_idea
			add_stability = 0.01
		}
		facility_state_effects = {
			set_building_level = {
				type = land_facility
				level = 1
			}
		}
	}

	generic_prototype_rewards = {
		sp_land_generic_reward_scientist_xp_1
	}

	unique_prototype_rewards = {
		HHO_reward_steel_breakthrough = {
			narrative = {
				name = HHO_reward_steel_breakthrough
				desc = HHO_reward_steel_breakthrough_desc
			}
			icon = GFX_sp_nuclear_reactor
			fire_only_once = yes
			threshold = { min = 30 max = 90 }
			weight = { base = 2 }
			option = {
				token = HHO_reward_steel_breakthrough_option
				iteration_output = {
					country_effects = {
						add_political_power = 10
					}
				}
			}
		}
	}

	ai_will_do = {
		factor = 2
	}
}
```

> `sp_land_generic_reward_scientist_xp_1` 是原版通用奖励 token（`prototype_rewards/generic_land_prototype_rewards.txt:7`），
> 可以直接引用，不必自己写。自己写的 unique reward 若只想要效果、不想让玩家选，`option` 至少写一个。

**原型奖励字段速查（`prototype_rewards/documentation.md`，1.19.4.2 实测）**：

| 字段 | 语义 |
|---|---|
| `narrative` / `icon` | 可选；本地化与图标都支持 `TAG_` 前缀回退（`<tag>_<token>` → `<token>`；缺省图标 `GFX_PLACEHOLDER_sp_project_picture`） |
| `fire_only_once` | 可选，默认 `no` |
| `threshold = { min = A max = B }` | 可选，**区间语义是 (min, max]**：`min` 含、`max` 不含；不写 = 任何时候都可被选中 |
| `weight` | 可选，可写成 scriptable 表达式（同 `ai_will_do`）：`ROOT` = project、`FROM` = 国家，另可读 `var:facility_state`、`var:facility_province_id`、`var:scientist`；不写时取 define `NProject::ITERATION_REWARD_DEFAULT_WEIGHT` |
| `allowed` | 可选，国家作用域触发器，默认 `true` |
| `option` | **至少 1 个**；`token` 必填且同一奖励内唯一；`default = yes` 最多一个（一个都不写则第一个是超时默认项）；`option.iteration_output` 与 `project_output` 同构 |
| `prototype_reward = { token = xxx ... }` | 顶层第二种写法，等价于匿名 `token = { ... }`（`prototype_rewards/documentation.md:118-133`） |

### 需要的本地化（`localisation/english/HHO_sp_l_english.yml`）

```yml
l_english:
 HHO_advanced_steel_plating:0 "Advanced Steel Plating"
 HHO_advanced_steel_plating_desc:0 "A metallurgical programme to produce armour-grade plating."
 HHO_reward_steel_breakthrough:0 "Breakthrough: Hardened Plating"
 HHO_reward_steel_breakthrough_desc:0 "The lab reports a promising alloy."
 HHO_reward_steel_breakthrough_option:0 "Excellent."
 specialization_land:0 "Land Research"
```

（`specialization_land` 原版已有中文/英文名，这里不必重复定义；**新专精才需要**。）

## 6. 科学家与设施：怎么让它真的能跑

1. **设施**：原版已有 `land_facility`（`00_buildings.txt:559`）带 `specialization = { specialization_land }`。
   玩家在州里建造该建筑后即可在「特殊项目」界面开工。
2. **科学家**：在 `common/characters/` 给国家一个 `scientist = { ... }` 角色，并在 history 里 `recruit_character`；
   或通过 `recruit_character` effect 在国策/事件里给（见 [characters.md](characters.md)）。
3. **突破点**：新国家没有突破点就用 `add_breakthrough_progress` 送一点（history 或国策）。
4. **项目池**：`allowed` 为 true 的国家会在开局时获得项目实例；`allowed` 里只宜用 `tag`/`original_tag`/`has_dlc`（文档明确限制）。

## 7. 新增 vs 覆盖

- **推荐**：新文件 `common/special_projects/projects/HHO_*.txt`，新 token；奖励也新 token。
- 引用原版通用奖励 = 安全复用（不需要覆盖）。
- 想改原版项目 → 同 token 覆盖整块（会丢字段）；风险与理念/科技一致。

## 8. 1.19 相关注意

- **文档与实现不一致**：`special_projects_documentation.md` 是设计草案（大量 `# UP TO DEBATE`），
  真实语法以 `projects/documentation.md`（规范）+ `projects/nuclear_projects.txt` 等实例为准 —— 例如完成效果用
  `country_effects` / `facility_state_effects` / `scientist_effects` 三个块，而不是草案里的裸 `effects`。
  **这是本目录最重要的一条 1.19 事实**。
- `complexity` / `prototype_time` 原版用 script constant：`sp_complexity.large`、`sp_time.prototype.long`（`nuclear_projects.txt:4,19`）；
  奖励里用 `constant:sp_scientist_xp_gain.low`（`prototype_rewards/generic_land_prototype_rewards.txt:48`）—— 两种写法都在用。
- 系统整体与 **Gotterdammerung** DLC 强绑定（项目 `allowed` 里的 `has_dlc`）。
- `common/special_projects/project_tags/tags.txt` 只有 15 个原版标签（`sp_tag_tank`…），**新增标签需改这个文件**（或另建文件追加）。
- **1.19.4 未改本域**：两批脚本改动清单里没有 `common/special_projects/`，四篇官方文档也一字未动；可直接沿用本文的字段与行号。

## 9. 常见错误 / 自检清单

- [ ] 项目文件顶层是 `<token> = { ... }`，没有包裹。
- [ ] `specialization` 指向的专精存在，且 `common/buildings` 里有建筑带同名的 `specialization = { ... }`。
- [ ] `visible`/`available` 里的国家条件写成 `FROM = { ... }`（项目作用域下的国家是 FROM）。
- [ ] `allowed` 只用 `tag`/`original_tag`/`has_dlc`（文档限制）。
- [ ] `project_output` 用 `country_effects` / `facility_state_effects`（别照抄设计文档的 `effects`）。
- [ ] `generic_prototype_rewards` 里引用的 token 真实存在（在 `prototype_rewards/` 里 grep）。
- [ ] `unique_prototype_rewards` 每个奖励有 `threshold`、至少一个 `option`，`option.token` 有本地化。
- [ ] `resource_cost.resources` 不用 `oil`（文档明确禁止）。
- [ ] 项目名/描述/奖励名都有本地化；`sp:` 前缀写法正确。

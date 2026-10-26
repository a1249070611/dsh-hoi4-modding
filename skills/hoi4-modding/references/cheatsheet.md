# HOI4 1.19.3 速查手册（代码可直接抄）

> 所有片段都在 1.19.3 原版文件的用法基础上核对过；`NS_` / `ns.` 换成你自己的前缀。
> 详细字段解释见知识库对应章节（`../knowledge/...` 或本机知识库路径）。

## 1. Mod 骨架与描述文件

```
MyMod/
├─ descriptor.mod
├─ localisation/english/MyMod_l_english.yml            # UTF-8 BOM
├─ localisation/simp_chinese/MyMod_l_simp_chinese.yml  # UTF-8 BOM
├─ common/ideas/MyMod_ideas.txt
├─ events/MyMod_events.txt
├─ interface/MyMod_icons.gfx        # 2D sprite 定义
└─ gfx/interface/icons/*.dds        # 贴图本体
```

`descriptor.mod`（Mod 目录内）：

```pdx
name="My Mod"
supported_version="1.19.*"
tags={ "Gameplay" "Historical" }
picture="thumbnail.png"
```

同级 `MyMod.mod`（玩家 `mod/` 目录里，启动器入口；`install_mod.py` 会生成）：

```pdx
name="My Mod"
supported_version="1.19.*"
tags={ "Gameplay" "Historical" }
path="C:/Users/you/Documents/Paradox Interactive/Hearts of Iron IV/mod/MyMod"
```

- `path` 用正斜杠、**纯 ASCII**；不要写 `thumbnail=`（正确是 `picture=`）。
- `supported_version` 只接受 `1.19.*` / `1.19.3.0` 这类形式。

## 2. 本地化（最常出错）

```yml
l_english:
 NS_idea_one:0 "Idea One"
 NS_idea_one_desc:0 "Description."
 ns.1.t:0 "Event Title"
 ns.1.d:0 "Event description."
 ns.1.a:0 "Option A."
```

```yml
l_simp_chinese:
 NS_idea_one:0 "理念一"
 NS_idea_one_desc:0 "描述。"
 ns.1.t:0 "事件标题"
 ns.1.d:0 "事件描述。"
 ns.1.a:0 "选项 A。"
```

规则：

- 文件必须 **UTF-8 with BOM**；目录 `english`/`simp_chinese` 与首行 `l_english:`/`l_simp_chinese:` 一致。
- 缩进 1 个空格；key 后 `:0` 或 `:`；值必须双引号；`\n` 换行。
- 颜色 `§Y黄色§!`、变量 `$VAR$`、图标 `£icon`、动态文本 `[ROOT.GetName]`。
- key 约定：国策/理念/决议/科技/角色 = 各自 ID；国策/理念/决议/科技描述 = `<id>_desc`；
  事件 = `<namespace>.<n>.t/.d`，选项自己起名（如 `.a`）；决议类别 = `<category_id>`。
- 中文出现"方框"是字体没有中文覆盖，不是文本问题（见知识库 `05_presentation/chinese_fonts.md`）。

## 3. 国家精神（Idea）

文件：`common/ideas/NS_ideas.txt`

```pdx
ideas = {
	country = {                          # 原版分类，定义在 common/idea_tags/00_idea.txt
		NS_steel_boom = {
			allowed = { original_tag = LUX }
			allowed_civil_war = { always = yes }
			removal_cost = -1              # -1 = 不可移除
			picture = can_wartime_prices_and_trade_board   # 引擎找 GFX_idea_<token>
			modifier = {
				industrial_capacity_factory = 0.05
				stability_factor = 0.02
			}
			on_add = { add_political_power = 10 }      # 可选
			on_remove = { add_stability = -0.02 }      # 可选
		}
	}
}
```

本地化：`NS_steel_boom` + `NS_steel_boom_desc`。
授予：`add_ideas = NS_steel_boom`（国策/事件/决议/on_startup）。
自定义分类：在 `common/idea_tags/NS_idea_tags.txt` 写 `idea_categories = { NS_category = { ... } }`，否则整块可能被忽略。

## 4. 国策树（Focus）

**先判断目标国家有没有专属树**：有（SWE/GER/SOV…）→ 只能覆盖原树或用 `load_focus_tree`；没有（LUX/IRE/BHU…用 `generic_focus`）→ 新建树 + 打分接管。

文件：`common/national_focus/NS_focus.txt`

```pdx
focus_tree = {
	id = NS_luxembourg_tree

	country = {                    # 打分：LUX 原版 generic_focus 是 0 分，+10 即接管
		factor = 0
		modifier = {
			add = 10
			original_tag = LUX
		}
	}

	initial_show_position = { x = 0 y = 0 }
	continuous_focus_position = { x = 20 y = 1000 }
	default = no

	focus = {
		id = NS_rebuild_the_ironworks
		icon = GFX_focus_generic_industry_investment   # 必须是已存在 sprite
		x = 0
		y = 0
		cost = 10                       # 天数 = cost × 7
		search_filters = { FOCUS_FILTER_INDUSTRY }
		ai_will_do = { base = 10 }
		completion_reward = {
			add_ideas = NS_steel_boom
			country_event = { id = ns.1 days = 1 }
		}
	}

	focus = {
		id = NS_benelux_cooperation
		icon = GFX_focus_generic_treaty
		prerequisite = { focus = NS_rebuild_the_ironworks }
		mutually_exclusive = { focus = NS_armed_neutrality }   # 互斥两边都要写
		x = -1
		y = 1
		cost = 10
		completion_reward = { add_stability = 0.05 }
	}

	focus = {
		id = NS_armed_neutrality
		icon = GFX_focus_generic_home_defense
		prerequisite = { focus = NS_rebuild_the_ironworks }
		mutually_exclusive = { focus = NS_benelux_cooperation }
		x = 1
		y = 1
		cost = 10
		completion_reward = { add_war_support = 0.05 }
	}
}
```

- 本地化：每个国策 `<id>` + `<id>_desc`。
- `prerequisite`：同一块里多个 `focus =` 是 AND；多个 `prerequisite = {}` 块是 OR。
- `icon` 的可用态需要额外的 `GFX_..._shine` sprite，命名必须是原 sprite 名 + `_shine`。
- `bypass` / `available` / `visible` / `allow_branch` 的语义见知识库 `02_content/focus_trees.md`。

## 5. 事件（Event）

文件：`events/NS_events.txt`

```pdx
add_namespace = ns

# 由国策/决议触发
country_event = {
	id = ns.1
	title = ns.1.t
	desc = ns.1.d
	picture = GFX_report_event_generic_rally2
	is_triggered_only = yes
	fire_only_once = yes

	immediate = { set_country_flag = NS_chain_started }

	option = {
		name = ns.1.a
		ai_chance = { base = 10 }
		add_political_power = 25
		country_event = { id = ns.2 days = 5 }
	}
	option = {
		name = ns.1.b
		ai_chance = { base = 1 }
		add_stability = 0.03
	}
}

# MTTH 型
country_event = {
	id = ns.2
	title = ns.2.t
	desc = ns.2.d
	picture = GFX_report_event_generic_research_lab
	trigger = { tag = LUX has_idea = NS_steel_boom }
	mean_time_to_happen = {
		days = 180
		modifier = { factor = 2 has_war = yes }
	}
	option = { name = ns.2.a add_research_slot = 1 }
}
```

- 触发别的事件：`country_event = { id = ns.2 days = 5 }`、`news_event = { id = news.1 hours = 12 }`。
- 隐藏事件：`hidden = yes`（不弹窗只执行效果）；新闻事件：`news_event = { ... major = yes }`。
- MTTH 型建议加 `fire_only_once = yes`，否则可能反复触发。

## 6. 决议（Decision）

文件：`common/decisions/NS_decisions.txt`（顶层每个块 = 一个类别，**不要** `decisions = {}` 外层）

```pdx
NS_home_front = {
	icon = GFX_decision_generic_civil_support     # 类别图标
	priority = 100

	NS_emergency_public_works = {
		icon = GFX_decision_generic_construction
		allowed = { original_tag = LUX }
		visible = { has_political_power > 0 }
		available = { has_political_power >= 50 }
		cost = 50
		fire_only_once = yes
		complete_effect = {
			add_stability = 0.05
			add_ideas = NS_steel_boom
		}
	}

	# 任务型：N 天后自动执行 remove_effect
	NS_winter_readiness_drill = {
		icon = GFX_decision_generic_military
		allowed = { original_tag = LUX }
		visible = { always = yes }
		available = { has_political_power >= 25 }
		cost = 25
		days_remove = 30
		modifier = { army_org_factor = 0.05 }
		remove_effect = { country_event = { id = ns.3 } }
	}
}
```

- 本地化：类别 `<category_id>`；决议 `<decision_id>` + `<decision_id>_desc`。
- `allowed` 每局判一次（性能友好）；`visible`/`available` 每次 UI 刷新都判。
- `icon` 不带 `GFX_` 前缀时找 `GFX_decision_<name>`（类别找 `GFX_decision_category_<name>`）。
- targeted 决议：`targets = { ... }` + `target_root_trigger` + `target_trigger`，详见知识库。

## 7. 角色（Character）

文件：`common/characters/NS_characters.txt`

```pdx
characters = {
	NS_erik_weber = {
		name = NS_erik_weber                    # 本地化 key
		portraits = {
			civilian = {
				large = GFX_Portrait_Europe_Generic_1
				small = GFX_Portrait_Europe_Generic_1_small
			}
		}
		advisor = {
			slot = political_advisor
			idea_token = NS_erik_weber_advisor    # 顾问理念 key（需本地化）
			cost = 150
			allowed = { original_tag = LUX }
			visible = { has_completed_focus = NS_rebuild_the_ironworks }
			traits = { NS_trait_industrialist }
		}
	}
}
```

领袖特质：`common/country_leader/NS_traits.txt`：

```pdx
leader_traits = {
	NS_trait_industrialist = {
		random = no
		industrial_capacity_factory = 0.05
	}
}
```

- 领袖：`country_leader = { ideology = <子意识形态> traits = { ... } expire = "1965.1.1.1" }`。
- 将领：`corps_commander = { skill = 3 attack_skill = 2 ... }`；科学家：`scientist = { ... }`。
- 本地化：角色名、顾问理念、特质各一条。

## 8. 科技（Technology）

文件：`common/technologies/NS_tech.txt`

```pdx
technologies = {
	@1936 = 2
	@1938 = 4

	NS_steel_alloys = {
		enable_equipments = { infantry_equipment_1 }
		research_cost = 1.5
		start_year = 1936
		folder = {
			name = infantry_folder          # folder 定义在 common/technology_tags/00_technology.txt
			position = { x = 12 y = @1936 }
		}
		path = { leads_to_tech = NS_steel_alloys_2 research_cost_coeff = 1 }
		dependencies = { infantry_weapons1 = 1 }   # 真正的前置
		categories = { infantry_weapons }
		on_research_complete = { add_ideas = NS_steel_boom }
	}
}
```

- 本地化：`NS_steel_alloys` + `NS_steel_alloys_desc`。
- 新 folder 必须在 `technology_folders = { }` 里声明；改原版科技树节点要覆盖原版科技块。

## 9. 州、资源、建筑

文件：`history/states/900-NS_land.txt`（ID 必须未被占用；原版 state id 到 1081）

```pdx
state = {
	id = 900
	name = "STATE_900"
	manpower = 250000
	state_category = town

	resources = { steel = 12 }

	history = {
		owner = LUX
		add_core_of = LUX
		victory_points = { 12345 5 }
		buildings = {
			infrastructure = 3
			industrial_complex = 2
			air_base = 1
		}
	}

	provinces = { 12345 12346 }     # 必须已存在于 map/definition.csv
	local_supplies = 0.0
}
```

改已有州/加建筑用 effect（别改历史）：

```pdx
on_startup = {
	effect = {
		900 = {
			add_extra_state_shared_building_slots = 2
			add_building_construction = { type = industrial_complex level = 1 instant_build = yes }
		}
	}
}
```

## 10. 动态变量与动态修正

```pdx
# common/dynamic_modifiers/NS_modifiers.txt
NS_growth_modifier = {
	icon = GFX_idea_generic_economic_crisis
	enable = { always = yes }
	remove_trigger = { check_variable = { NS_growth = 0 } }
	industrial_capacity_factory = NS_growth      # 值直接写变量名
}

# 施加（国家 scope）
set_variable = { NS_growth = 0.05 }
add_dynamic_modifier = { modifier = NS_growth_modifier }

# 修改并立刻刷新（否则每天才更新）
add_to_variable = { NS_growth = 0.05 }
clamp_variable = { var = NS_growth min = 0 max = 0.30 }
force_update_dynamic_modifier = yes
```

## 11. scripted GUI 面板（4 文件闭环）

1）`common/scripted_guis/NS_dashboard.txt`

```pdx
scripted_gui = {
	NS_dashboard_ui = {
		context_type = decision_category
		window_name = "NS_dashboard_window"
		visible = { has_country_flag = NS_dashboard_open }
		effects = {
			NS_dashboard_boost_click = {
				add_political_power = 10
				add_to_variable = { NS_boost_count = 1 }
			}
		}
		triggers = {
			NS_dashboard_boost_click_enabled = { check_variable = { NS_boost_count < 5 } }
		}
	}
}
```

2）`interface/NS_dashboard.gui`

```pdx
guiTypes = {
	containerWindowType = {
		name = "NS_dashboard_window"
		position = { x = 0 y = 0 }
		size = { width = 100% height = 170 }
		background = { name = "bg" quadTextureSprite = "GFX_decision_category_generic" }
		instantTextBoxType = {
			name = "NS_dashboard_title"
			position = { x = 90 y = 10 }
			font = "hoi_24header"
			text = "NS_dashboard_title"
			format = left
			maxWidth = 340
		}
		buttonType = {
			name = "NS_dashboard_boost"
			position = { x = 90 y = 96 }
			quadTextureSprite = "GFX_button_261x34"
			buttonText = "NS_dashboard_boost"
			buttonFont = "hoi_16mbs"
			clicksound = click_default
		}
	}
}
```

3）`common/decisions/NS_decisions.txt` 的类别里挂载：

```pdx
NS_dashboard_category = {
	icon = GFX_decision_generic_civil_support
	scripted_gui = NS_dashboard_ui
	NS_dashboard_dummy = {
		icon = GFX_decision_generic_construction
		available = { always = no }
		complete_effect = { }
	}
}
```

4）本地化：窗口标题/文本/按钮 key（`NS_dashboard_title` 等）。

- `effects` 键名规则：`<元素名>_click`（可加 `_right`/`_alt` 等组合）。
- 原版 17 个实例全部用 `context_type = decision_category`，这是最稳挂载方式。

## 12. MIO 与特殊项目

**MIO**：`common/military_industrial_organization/organizations/NS_mio.txt`（直接顶层块）

```pdx
NS_arms_works = {
	icon = GFX_idea_generic_tank_manufacturer_1
	allowed = { original_tag = LUX }             # 开局为真即自动创建实例
	equipment_type = { mio_cat_eq_all_light_tank }
	research_categories = { mio_cat_tech_light_armor_and_modules }
	research_bonus = 0.15
	task_capacity = 3

	initial_trait = {
		name = NS_mio_initial_trait
		equipment_bonus = { reliability = 0.05 }
		production_bonus = { production_cost_factor = -0.05 }
	}

	trait = {
		token = NS_mio_trait_quality
		name = NS_mio_trait_quality
		position = { x = 0 y = 0 }
		equipment_bonus = { soft_attack = 0.05 }
	}
}
```

**特殊项目**：`common/special_projects/projects/NS_projects.txt`（需 Gotterdammerung）

```pdx
NS_arctic_track = {
	specialization = specialization_land          # 对应 land_facility
	icon = GFX_idea_generic_tank_manufacturer_1
	complexity = sp_complexity.small
	project_tags = sp_tag_tank
	allowed = { has_dlc = "Gotterdammerung" original_tag = LUX }
	available = { FROM = { has_tech = tech_engineers } }
	resource_cost = { resources = { steel = 2 tungsten = 1 } }
	prototype_time = sp_time.prototype.short
	project_output = {
		country_effects = {
			army_experience = 50
			add_political_power = 50
		}
	}
}
```

## 13. 贴图、DDS 与 GFX

1）画图（PNG）→ 转 DDS：

```bash
python "$S/dds_helper.py" make icon.png gfx/interface/ideas/NS_icon.dds --width 60 --height 68
python "$S/dds_helper.py" check gfx/interface/ideas/NS_icon.dds
```

2）`interface/NS_icons.gfx` 注册（2D sprite **必须**在 `interface/`）：

```pdx
spriteTypes = {
	spriteType = {
		name = "GFX_idea_NS_icon"
		texturefile = "gfx/interface/ideas/NS_icon.dds"
	}
}
```

3）脚本引用 `icon = GFX_idea_NS_icon` / `picture = NS_icon`。

常用尺寸与格式：focus 100×88（`GFX_...` + `_shine`）、idea 60×68、decision 32×33、decision category 40×51、portrait 156×210、flag 82×52 TGA。DDS 默认 raw32（未压缩、无 mipmap），与原版 UI 同构。

## 14. 调试

启动：`hoi4.exe -gdpr-compliant -debug_mode`（本机 `launcher-settings.json` 已有该启动项）。
控制台：`~`/`^`；`event ns.1`、`focus.autocomplete`、`debug_events`、`tag LUX`、`pp 500`、`observe`、`annex`、`dump_checksum`。

日志：`C:\Users\<你>\Documents\Paradox Interactive\Hearts of Iron IV\logs\error.log`
格式：`[时间][游戏日期][文件:行]: 消息`；**只 grep 自己的文件名/ID**（原版噪声占 95%+）。

对照表：

| 关键字 | 原因 | 修法 |
|---|---|---|
| `Invalid Scope, supported: Country, provided: None` | scope 错 | 查 `Supported Scopes`；用 `GER = { }` 切 |
| `Unknown effect-type` / `Unknown trigger-type` | 拼错/版本没有 | 查 `reference/effects.json` / `triggers.json` |
| `Unknown modifier` | 修正名拼错 | 查 `reference/modifiers.json` |
| `Unexpected token` | 括号/引号/字段错 | 跑 lint；`.mod` 用 `picture=` |
| `Tried to get dynamic token` | 动态 key 未注册 | 改普通 key 或 `synchronized_dynamic_tokens` |
| 图标空白/黑块 | GFX 未注册/贴图缺失/DDS 头错 | `dds_helper.py check`；sprite 放 `interface/` |
| 中文方框 | 字体无中文 override | 换有中文覆盖的字体 |

## 15. 1.19 与旧教程差异（写前必看）

- **国策树**：`country` 块是打分，每国只加载一棵（最高分）；`default = yes` 只影响全 0 分时。
- **学说**：`common/doctrines/` 重写为 folder → grand_doctrines → tracks → subdoctrines → mastery/reward；旧「四条树 + path」作废。
- **地形**：定义在 `common/terrain/00_terrain.txt`（不是 `map/terrain.txt`）；`combat_width` 是绝对值。
- **装备**：没有 `common/equipment/`，在 `common/units/equipment/`；坦克/飞机由底盘/机体 + `duplicate_archetypes` 派生，新底盘要注册 `interface/equipmentdesigner/` GUI。
- **补给区**：`map/supplyareas/` 基本自动生成，不要按旧教程每区一文件。
- **理念**：支持 `on_add`/`on_remove`（旧教程说没有是错的）。
- **文档滞后**：官方 `documentation/*.md` 不是全集（`unit_modifiers`、`is_fighting_in_strategic_region`、`is_deployed` 等未收录），冲突以游戏文件为准。
- **路径**：`.mod` 的 `path` 建议纯 ASCII；`-debug_mode` 不是 `-debug`。

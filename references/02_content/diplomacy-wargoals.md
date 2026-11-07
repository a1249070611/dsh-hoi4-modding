---
title: 外交：宣战目标 / 阵营 / 和平会议 / 附庸 / 脚本外交行动
domain: 02_content
scope: country / global
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/wargoals/00_invasion.txt
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/factions/_documentation.md
  - common/factions/templates/axis.txt
  - common/peace_conference/ai_peace/_documentation.md
  - common/peace_conference/cost_modifiers/_documentation.md
  - common/autonomous_states/puppet.txt
  - common/scripted_diplomatic_actions/scripted_diplomatic_actions.txt
  - common/scripted_effects/DEN_scripted_effects.txt
---

# 外交：宣战目标 / 阵营 / 和平会议 / 附庸 / 脚本外交行动

## 1. 五个子系统与文件位置

| 子系统 | 目录 | 作用 |
|---|---|---|
| 宣战目标类型（wargoal） | `common/wargoals/*.txt` | 定义 `take_state` / `take_state_focus` 等目标的成本、期限、威胁度 |
| 阵营（factions） | `common/factions/{templates,goals,rules,upgrades,member_upgrades,icons}` | 1.19 阵营系统：模板 + 目标 + 规则 + 升级 |
| 和平会议 | `common/peace_conference/{ai_peace,categories,cost_modifiers}` | 和平会议 AI 偏好与行动成本修正 |
| 自治/附庸 | `common/autonomous_states/*.txt` | 自治等级（傀儡/自治领/…）及其修正 |
| 脚本外交行动 | `common/scripted_diplomatic_actions/scripted_diplomatic_actions.txt` | 自定义外交按钮（送礼、结盟请求…） |

原版必读：

- `common/wargoals/00_invasion.txt:1-55` —— `wargoal_types = { take_state = { allowed/available/take_states/generate_base_cost/generate_per_state_cost/take_states_limit/take_states_cost/expire/threat } }`。
- `common/scripted_effects/DEN_scripted_effects.txt:3525-3530` —— `create_wargoal` 的真实调用（含 `generator`）。
- `common/factions/_documentation.md`（390 行）—— **1.19 阵营系统权威说明**：goals / rules / templates / 效果与触发器清单。
- `common/factions/templates/axis.txt:1-29` —— 阵营模板实例。
- `common/peace_conference/ai_peace/_documentation.md` 与 `cost_modifiers/_documentation.md` —— 和平会议脚本化。
- `common/autonomous_states/puppet.txt:1-30` —— 自治等级结构。
- `common/scripted_diplomatic_actions/scripted_diplomatic_actions.txt:1-42` —— 脚本外交行动完整模板（注释形式）。

**官方文档位置（1.19.4.2 实测，2026-11-06）**：

| 子系统 | 规模 | 官方文档 |
|---|---|---|
| 宣战目标 | `common/wargoals/` 1 个 txt / 240 行 | **无**（只能读 `00_invasion.txt` 头部注释） |
| 阵营 | `common/factions/` 29 txt + 1 md / 19,894 行 | `_documentation.md` **390 行**（本域唯一系统级文档） |
| 和平会议 | `common/peace_conference/` 35 txt + 2 md / 5,390 行 | `ai_peace/_documentation.md` 41 行、`cost_modifiers/_documentation.md` 42 行 |
| 自治/附庸 | `common/autonomous_states/` 21 文件 / 1,756 行 | **无**（读 `puppet.txt` 实例与各等级文件头注释） |
| 脚本外交行动 | 1 个 txt / 105 行 | **无**（文件开头 42 行注释就是全部文档） |

1.19.4 的改动（相对 1.19.3）：10-28 批改 `common/factions/` 2 个文件、`common/peace_conference/` 若干文件；
10-29 批没有本域文件。阵营/和会的字段结构未变，只是数值与个别条目调整。

## 2. 宣战目标（wargoal）

### 2.1 定义目标类型（`common/wargoals/`）

```pdx
wargoal_types = {
	HHO_industry_seizure = {
		# PREV = 原始目标国家；ROOT = 目标拥有者（发起国）
		allowed = { }            # 该目标能否被使用（国家作用域）
		available = { }          # 当前是否可用

		take_states = { }        # 直接指定要拿的州（可选）
		generate_base_cost = 200 # 生成目标的基cost
		generate_per_state_cost = 50
		take_states_limit = 5
		take_states_cost = -20
		expire = 730             # 目标失效天数
		threat = 2               # 生成后增加的世界紧张度
	}
}
```

（字段含义直接对齐 `00_invasion.txt` 的 `take_state` / `take_state_focus` 两个原版块。）

### 2.2 在内容里发宣战目标（effect）

```pdx
create_wargoal = {
	type = take_state_focus   # 必须是 common/wargoals 里定义的类型
	target = FROM
	generator = { 138 }       # 目标州 ID 列表（原版写法；DEN_scripted_effects.txt:3525-3529）
}
remove_wargoal = { target = FROM type = take_state_focus }   # documentation/effects_documentation.md:6336
```

用法建议：写在国策 `completion_reward`、事件 `option`、或 `scripted_effect` 里。

## 3. 阵营（1.19 新系统）

> **关键变化**：`create_faction` 已被文档标注 **deprecated**（`documentation/effects_documentation.md:3105`），
> 推荐 `create_faction_from_template`。原版 `history/countries/GER - Germany.txt:871-872` 用的是模板写法。

### 3.1 模板（`common/factions/templates/*.txt`）

```pdx
faction_template_hho_nordic = {
	name = HHO_nordic_faction_name        # 本地化 key
	icon = GFX_faction_logo_axis          # 阵营 logo（原版 icon 可复用）
	manifest = faction_manifest_conquest_of_territory  # 主目标（faction goal token）

	goals = {                             # 初始目标（goal token 或内联定义）
		faction_goal_military_infrastructure
		faction_goal_secure_european_continent
	}

	default_rules = {                     # 默认规则（rule token 或内联定义）
		joining_rule_same_continent_only
		change_leader_rule_manpower
	}

	visible = { }                         # 可选：是否出现在「创建阵营」列表
	available = { }                       # 可选：是否可选
	can_leader_join_other_factions = yes  # 可选（_documentation.md:251-254）
}
```

### 3.2 目标与规则（`common/factions/goals`、`common/factions/rules`）

`_documentation.md:6-137` 给出 goal 全字段：`name`、`description`、`category`（`short_term`/`medium_term`/`long_term`）、
`visible`/`available`/`completed`、`group`、`auto_complete`、`ai_will_do`、`complete_effect`、`cancel`、`cancel_effect`、
`select_effect`、`remove_effect`，以及持续型目标的 `progress` / `ratio_progress`（用 scripted collection 算比例）。

`_documentation.md:140-228` 给出 rule 字段：`type`（`joining_rule`/`war_declaration_rule`/`call_to_war_rule`/`member_rules`/
`change_leader_rules`/`peace_conference_rules`）、`visible`/`available`/`can_remove`/`trigger`/`modifier`/`peace_action_modifiers`/`ai_will_do`。
规则组：`group_id = { default_rule = xxx rules = { ... } }`。

### 3.3 脚本接口（`_documentation.md:270-300`）

**effect**：`create_faction_from_template`、`dismantle_faction`、`set_faction_leader`、`set_faction_spymaster`、`set_faction_name`、
`add_to_faction`、`remove_from_faction`、`leave_faction`、`set_faction_rule`、`set_faction_manifest`、`add_faction_goal`、
`remove_faction_goal`、`add_faction_initiative`、`add_faction_power_projection`、`add_faction_influence_score`、`add_faction_influence_ratio`

**trigger**：`faction_manifest_fulfillment`、`has_faction_template`、`faction_power_projection`、`faction_influence_score`、
`faction_influence_ratio`、`faction_influence_rank`、`has_faction_goal`、`has_completed_faction_goal`

```pdx
HHO_join_nordic_bloc = {
	create_faction_from_template = faction_template_hho_nordic
	add_to_faction = NOR
	add_to_faction = DEN
	add_faction_initiative = 25
}
```

## 4. 和平会议

- **AI 偏好**：`common/peace_conference/ai_peace/*.txt`，结构见 `ai_peace/_documentation.md:18-40`：
  `peace_ai_desires = { 任意名字 = { peace_action_type = force_government enable = { ... } ai_desire = 100 } }`。
- **成本修正**：`common/peace_conference/cost_modifiers/*.txt`，`peace_action_modifiers = { xxx = { category = is_core peace_action_type = ... enable = { ... } cost_multiplier = 0.65 } }`。
- **作用域链**（两份文档一致）：`ROOT` = 谈判国（赢家）、`FROM` = 接受方（战后拥有者）、`FROM.FROM` = 让出方（战前拥有者）、`FROM.FROM.FROM` = 州。
- **脚本触发会议**（限两国/有限范围）：

```pdx
SOV = {
	start_peace_conference = {
		tag = FIN              # 主要战败国
		score_factor = 0.2     # 0-1，给赢家的会议分数比例；0 = 白和
		winner_scope = FACTION # ALL / FACTION / LIMITED_FACTION / LIMITED
		loser_scope = FACTION
		message = FIN_agree_peace  # 可选弹出消息本地化
	}
}
```

（`documentation/effects_documentation.md:8063-8082`。）
和平会议期间请用 `pc_xxx` 前缀的专用触发器（文档明确：外交关系/州归属在会议中不会实时更新）。

## 5. 附庸 / 自治（`common/autonomous_states/`）

```pdx
autonomy_state = {
	id = HHO_associated_state
	default = no                 # 是否默认自治等级
	is_puppet = yes              # 是否算「傀儡」

	min_freedom_level = 0.4      # 进入该等级所需的自由点数
	manpower_influence = 0.9     # 人力贡献系数

	rule = {
		desc = "RULE_DESC_IS_A_SUBJECT"
		can_not_declare_war = yes
		can_decline_call_to_war = no
	}

	modifier = {
		autonomy_manpower_share = 0.9
		can_master_build_for_us = 1
		peace_score_ratio_transferred_to_overlord = 0.1
		research_sharing_per_country_bonus_factor = -0.5
	}
}
```

（原版样板 `common/autonomous_states/puppet.txt:1-30`，注意那里还有 `faction_influence_contribution_factor` 等 1.19 新修正。）

设置：

```pdx
set_autonomy = {
	target = ENG
	autonomy_state = autonomy_puppet
	freedom_level = 0.5
	end_wars = yes
	end_civil_wars = yes
}
```

（`documentation/effects_documentation.md:6586-6600`。）触发器用 `compare_autonomy_state`（`common/technology_sharing/00_tech_sharing_groups.txt:13` 有真实用例）。

## 6. 脚本外交行动（`common/scripted_diplomatic_actions/`）

原版文件**整段被注释**（模板形式，`:1-42`），把注释去掉就是可用骨架：

```pdx
scripted_diplomatic_actions = {
	HHO_trade_offer = {
		# root = 发起国；THIS = 目标国
		allowed = { has_political_power > 25 }
		visible = { always = yes }
		selectable = { has_war = no }

		requires_acceptance = yes
		cost = 25                     # 政治点数
		command_power = 0
		cost_string = HHO_trade_offer_cost   # 可选：自定义代价显示
		show_acceptance_on_action_button = yes
		icon = 1

		on_sent_effect = { }
		complete_effect = { add_opinion_modifier = { target = FROM modifier = HHO_trade_deal } }
		reject_effect = { }
	}
}
```

## 7. 最小可跑完整示例（一条「北欧外交线」）

文件：`common/factions/templates/HHO_factions.txt`

```pdx
faction_template_hho_nordic = {
	name = HHO_nordic_faction_name
	icon = GFX_faction_logo_axis
	manifest = faction_manifest_conquest_of_territory
	goals = {
		faction_goal_military_infrastructure
	}
	default_rules = {
		joining_rule_same_continent_only
	}
}
```

文件：`common/scripted_effects/HHO_diplomacy_effects.txt`

```pdx
HHO_form_nordic_faction = {
	create_faction_from_template = faction_template_hho_nordic
	add_to_faction = SWE
	add_faction_initiative = 25
}

HHO_claim_swedish_iron = {
	create_wargoal = {
		type = take_state_focus
		target = FROM
		generator = { 91 }
	}
}
```

文件：`common/scripted_diplomatic_actions/HHO_diplomatic_actions.txt`

```pdx
scripted_diplomatic_actions = {
	HHO_trade_offer = {
		allowed = { has_political_power > 25 }
		visible = { always = yes }
		selectable = { has_war = no }
		requires_acceptance = yes
		cost = 25
		command_power = 0
		on_sent_effect = { }
		complete_effect = {
			add_opinion_modifier = {
				target = FROM
				modifier = HHO_trade_deal
			}
		}
		reject_effect = { }
	}
}
```

文件：`common/peace_conference/cost_modifiers/HHO_pc_modifiers.txt`

```pdx
peace_action_modifiers = {
	HHO_nordic_brothers = {
		category = is_core
		peace_action_type = puppet
		enable = {
			ROOT = { has_government = democratic }
			ROOT.FROM.FROM.FROM = { is_core_of = SWE }
		}
		cost_multiplier = 0.65
	}
}
```

### 需要的本地化（`localisation/english/HHO_diplomacy_l_english.yml`）

```yml
l_english:
 HHO_nordic_faction_name:0 "Nordic Union"
 HHO_trade_offer:0 "Offer Trade Agreement"
 HHO_trade_offer_cost:0 "25 Political Power"
 HHO_trade_deal:0 "Trade Agreement"
 HHO_claim_swedish_iron:0 "Claim the Iron Fields"
 HHO_industry_seizure:0 "Seize Industry"
```

> `HHO_industry_seizure` 是 wargoal 类型 id，**也要一条本地化**（原版类型如 `take_state_focus` 都在 yml 里有对应条目）。

> `HHO_trade_deal` 是 opinion modifier token：除了本地化，还要在 `common/opinion_modifiers/` 里定义它（`opinion = { value = 25 months = 24 }` 一类结构），
> 否则 `add_opinion_modifier` 静默无效。格式请直接照抄 `common/opinion_modifiers/` 里任一原版条目。

## 8. 新增 vs 覆盖

- `common/wargoals/`：新增文件 + 新增类型（`HHO_industry_seizure`），别覆盖 `00_invasion.txt`。
- `common/factions/`：新增模板/目标/规则文件；**1.19 的新系统文件普遍是「新文件」而不是覆盖**（原版也按内容包分文件：`axis.txt`、`allies.txt`…）。
- `common/autonomous_states/`：新增自治等级文件，别改 `puppet.txt`。
- `common/peace_conference/`：新增 cost_modifiers/ai_peace 文件。

## 9. 1.19 相关注意

- **阵营系统是 1.19 前后最大改动**：`create_faction` deprecated，出现 `create_faction_from_template`、faction goals/rules/upgrades、
  `faction_initiative`/`faction_power_projection`/`faction_influence_*`（`common/factions/_documentation.md`）。
  文档还提到 "Deeper Factions DLC"（`effects_documentation.md:3106`）——DLC 名称请以 `dlc/*.dlc` 与启动器为准。
- 自治等级的 `rule` 块里包含 `contributes_operatives`、`can_create_collaboration_government` 等情报/合作政府相关开关（`puppet.txt:17-18`）。
- 和平会议触发器统一 `pc_` 前缀（`ai_peace/_documentation.md:26-34`），这是会议内唯一可靠的判定方式。
- ⚠️ `declare_war_on` / `add_war_goal` 这类旧教程函数名未在 1.19.4.2 的 effect 文档中确认；用 `create_wargoal`。

## 10. 常见错误 / 自检清单

- [ ] `wargoal_types` 定义了新类型，`create_wargoal.type` 与之匹配。
- [ ] `create_wargoal` 里的 `generator` 州 ID 属于目标国家（否则目标无效）。
- [ ] 阵营相关：模板 `manifest`/`goals`/`default_rules` 引用的 token 都存在（`common/factions/goals|rules` 里 grep）。
- [ ] 用 `create_faction_from_template` 而不是 `create_faction`。
- [ ] 和平会议文件放在 `ai_peace/` 或 `cost_modifiers/` 对应子目录（放错目录=不加载）。
- [ ] 自治等级 `id` 唯一，且 `is_puppet`/`default` 只有一个 `default = yes`（每个「树」一个默认等级）。
- [ ] 脚本外交行动文件外层有 `scripted_diplomatic_actions = { ... }`（原版模板如此）。
- [ ] 所有新 key（阵营名、行动名、cost_string、opinion modifier）都有本地化。
- [ ] `start_peace_conference` 的目标必须**正在交战**，否则无效。

---
title: 情报与行动 / 突袭（Intelligence, Operations & Raids）
domain: 02_content
scope: country / operation
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources: [common/operations/_documentation.md, common/operation_phases/_documentation.md, common/operation_tokens/_documentation.md, common/intelligence_agency_upgrades/_documentation.md, common/intelligence_agencies/00_intelligence_agencies.txt, common/raids/_documentation.md, common/raids/categories/raid_categories.txt, common/raids/air_raids.txt, documentation/effects_documentation.md, documentation/triggers_documentation.md]
---

# 情报与行动 / 突袭

1.19.4.2 的「情报」由 4 组数据文件 + 1 组突袭文件构成，**每一组都有自己的 `_documentation.md`**，是本文的主要依据。

## 1. 文件放哪 / 命名 / 原版参考

| 内容 | 目录 | 原版参考 |
|---|---|---|
| 情报机构（名字/logo） | `common/intelligence_agencies/00_intelligence_agencies.txt` | 第 5-30 行 |
| 机构升级（部门分支） | `common/intelligence_agency_upgrades/intelligence_agency_upgrades.txt` | `_documentation.md` + 正文 |
| 行动（operation） | `common/operations/*.txt` | `_documentation.md`（297 行）、`00_operations.txt`、`LaR_historical_operations.txt` |
| 行动阶段（phase） | `common/operation_phases/*.txt` | `_documentation.md`（52 行）、`00_operation_phases.txt` |
| 行动 token | `common/operation_tokens/00_OperationTokens.txt` | `_documentation.md`（29 行） |
| 突袭类别 | `common/raids/categories/raid_categories.txt` | 第 1-40 行 |
| 突袭类型 | `common/raids/*.txt` | `_documentation.md`（623 行）、`air_raids.txt`、`nuclear_raids.txt` |

DLC 门控：

- 行动/机构升级 → **La Résistance**（原版文件前缀 `LaR_`、`lar_`）。
- 突袭 → 多数要求 **Gotterdammerung**（`common/raids/air_raids.txt:42`、`categories/raid_categories.txt:4`），
  部分要求 `No Compromise, No Surrender` 或 `Thunder at Our Gates`（`raid_categories.txt:36-40`）。

**官方文档位置（1.19.4.2 实测，2026-11-06）**：

| 内容 | 规模 | 官方文档 |
|---|---|---|
| 情报机构 | `intelligence_agencies/` 1 txt / 905 行 | **无**（读 `00_intelligence_agencies.txt:5-30` 实例） |
| 机构升级 | `intelligence_agency_upgrades/` 1 txt / 563 行 | `_documentation.md` **67 行** |
| 行动 | `operations/` 7 文件 | `_documentation.md` 297 行 |
| 行动阶段 | `operation_phases/` 17 文件 | `_documentation.md` 52 行 |
| 行动 token | `operation_tokens/` 2 文件 | `_documentation.md` 29 行 |
| 突袭 | `raids/` 9 txt + 1 md / 11,829 行 | `_documentation.md` 623 行（本域最大的一篇） |

1.19.4 的改动：10-28 批改 `common/raids/` 5-8 个文件（含 `air_raids.txt` 等数值与字段）、`intelligence_agencies` 数值；
没有新增或改名的官方文档。突袭字段仍以 623 行的 `_documentation.md` 为准。

## 2. 行动（Operation）

### 2.1 结构（`common/operations/_documentation.md:12-269`）

```pdx
operation_test = {                      # 唯一 ID
	icon = GFX_operation_test_icon
	name = "Operation: ..."             # [[scripted localization]]，可写裸文本或 loc key
	desc = "..."                        # 同上
	priority = 15                       # 列表排序，越大越靠前
	days = 15                           # 行动总时长（天）
	danger_level = 5                    # 被目标察觉的危险度（默认 0）
	operatives = 2                      # 需要派出的特工数
	network_strength = 100              # 目标国所需情报网强度 0-100

	# 阶段：可写多个 phases 块，按时间均分；每块里是「候选阶段 → 权重」
	phases = {
		phase_test = { base = 10 }
		phase_1 = {
			base = 90
			modifier = { factor = 0 }
			modifier = { add = 10 }
		}
	}
	phases = {
		phase_1 = { base = 100 }
	}

	# 以下全部可选
	ai_will_do = { factor = 11 }
	allowed = { original_tag = GER }        # ROOT = 发起国；决定是否对玩家可见
	available = { always = no }             # ROOT, FROM
	awarded_tokens = { token_airforce token_army }  # 仅用于 tooltip 展示
	cost_modifiers = { trait_grease_machine trait_smooth_operator }  # 受哪些特工特质影响成本
	operation_target = { targets = { ENG } }         # 不写 = 所有国家可选
	selection_target = { targets = { ROOT } }        # 写后 UI 允许选省份/战略区
	target_type = strategic_region                    # province（默认）/ strategic_region
	equipment = { medium_tank_equipment = 20 infantry_equipment = 5000 }
	required_tokens = { token_airforce token_army }    # 需要先取得这些 token
	requirements = { }                                 # 除装备外的启动条件；运行中不满足会取消
	return_on_complete = yes                           # 完成时退还装备

	on_start = { }                          # 行动开始时（OPERATION 作用域）
	outcome_potential = { }                 # 仅用于描述「可能结果」的文本生成
	outcome_extra_chance = 50               # 发生「额外糟糕结果」的概率
	outcome_modifiers = { trait_perfectionist trait_planner }
	outcome_execute = { }                   # 行动完成时执行一次
	outcome_extra_execute = { }             # 发生额外结果时执行
}
```

作用域：`operation` 作用域内 **ROOT = 发起国、FROM = 目标国**；
有 `selection_target` 时 **FROM.FROM = 目标州**（`_documentation.md:195-199,230-233`）。

### 2.2 阶段（`common/operation_phases/`）

```pdx
phase_test = {
	name = "Run Forest Run"          # [[scripted localization]]
	desc = "..."
	icon = "GFX_report_event_hitler_handshake"
	picture = "GFX_report_event_hitler_handshake"
	outcome = "..."                  # 结果文本（拼进最终结局字符串）
	map_icon = "GFX_..."             # 可选
	outcome_extra = "..."            # 发生风险事件时的替代文本
	requirements = {                 # 每周检查；不满足则该阶段无效（ROOT/FROM = 国家）
		has_full_control_of_state = 119
		NOT = { original_tag = GER }
	}
	return_on_complete = no          # 完成时是否退还该阶段装备成本
	equipment = { infantry_equipment = 5000 }  # 可按行动里的倍率缩放；支持 civilian_factories
}
```

### 2.3 token（`common/operation_tokens/`）

```pdx
token_test = {
	name = ""
	desc = ""
	icon = ""
	targeted_modifier = targeted_modifier_id1   # 可多条；关系修正
	intel_source = navy                         # army / navy / civilian / airforce
	intel_gain = 1.0                            # 每个 token 只支持一个来源
}
```

规则：**同一对国家对之间只能有一个 token，不叠加**（`_documentation.md:3`）。

### 2.4 机构升级（`common/intelligence_agency_upgrades/`）

> 下面是**伪代码骨架**：`<分支名>` / `<upgrade_name>` / `<GFX entry>` 都要换成真实 token。

```text
<分支名> = {
	<upgrade_name> = {              # 名称全分支唯一
		picture = <GFX entry>
		frame = <GFX entry>         # 不带 _available/_completed/_unavailable 后缀
		sound = <Sound entry>       # 可选，默认 click_default
		ai_will_do = { factor = 2 }
		modifiers_during_progress = { civilian_factory_use = 15 }
		visible = { original_tag = GER }
		available = { has_done_agency_upgrade = upgrade_form_department }
		level = {
			modifier = { intelligence_agency_defense = 1.5 }
			complete_effect = { add_political_power = 200 }
		}
		level = {
			modifier = { intelligence_agency_defense = 1.25 }
		}
	}
}
```

注意：**没有 description 字段**，描述靠本地化 key `<upgrade_name>_desc`（`_documentation.md:9`）。

### 2.5 机构名字/logo（`common/intelligence_agencies/`）

```pdx
intelligence_agency = {
	picture = GFX_intelligence_agency_logo_usa
	names = { "Office of Strategic Services" }   # 可用本地化 key 或裸文本，随机选一个
	default = { tag = USA }                      # 默认给谁
	available = { original_tag = USA }           # logo 是否出现在可选列表
}
```

## 3. 突袭（Raids）

### 3.1 类别（`common/raids/categories/raid_categories.txt`）

```pdx
categories = {
	HHO_land_raids = {
		visible = { has_dlc = "Gotterdammerung" }
		intel_source = army                       # air/naval/army/civilian
		available = { has_tech = paratroopers }   # 可选
		free_targeting = no                       # yes = 允许任意省份（如核突袭）
		faction_influence_score_on_success = 100  # 1.19 阵营系统联动
	}
}
```

### 3.2 突袭类型（`common/raids/*.txt`，`types = { ... }`）

关键字段（完整清单见 `common/raids/_documentation.md:17-185`）：

| 字段 | 说明 |
|---|---|
| `category` | 上面定义的类别 token |
| `command_power` / `cost` | 指挥点数分配成本 |
| `days_to_prepare` / `preparation_time` | 准备天数 |
| `days_re_enable` | 对同一目标再次发动的冷却（0 = 无冷却） |
| `fire_only_once` | 只能执行一次 |
| `max_distance` | 起点到目标的最大距离（1.19 新字段，`_documentation.md:80`） |
| `allowed` / `visible` / `show_target` / `available` / `launchable` | 五层触发（性能敏感，注释明确要求写简单） |
| `target_types` | `province = any / id / { id列表 }`，`building = { type = ... }`，`state = { ... }` |
| `starting_point` | `types = { air_base naval_base rocket_site carrier submarine }`、`building_types`、`allow_faction_buildings` |
| `unit_requirements` | `battalion_types` 或 `equipment { type/modules/amount }`（可写多个块，满足其一即可） |
| `essential_equipment` / `additional_equipment` | 创建/执行时消耗的装备（走库存） |
| `unit_model` | `entity` / `default_entity` / `equipment = air_transport` / `start_offset` / `scale` |
| `unit_animations` | 1.19 新字段：随进度切换动画状态（`_documentation.md:55-64`） |
| `ai_will_do` / `ai_min_success_chance` | AI 权重与最低成功率 |
| `arrow = { type = line }` | 地图箭头类型：line/ballistic/air/naval/land |

突袭的完整可跑范例请直接读 `common/raids/air_raids.txt:12-60`（`facility_strike`：`category`、`command_power`、
`days_to_prepare`、`allowed`/`visible`/`show_target`/`available`、`ai_will_do` 一应俱全）。
新建 raid 时**逐字段替换**最稳，尤其别漏 `unit_model` / `target_icon` / `launch_sound` 这些表现字段。

⚠️ 突袭的**表现字段**（`unit_model` / `unit_icon` / `target_icon` / `equipment_icon` / `launch_sound`）没有「可选即安全」的默认值，
新建 raid 前请以 `common/raids/air_raids.txt` 的完整条目为模板逐字段替换。

### 3.3 脚本访问

| 类型 | 写法 | 证据 |
|---|---|---|
| effect：记录突袭历史 | `add_raid_history_entry` | `effects_documentation.md:1948` |
| effect：突袭伤害单位/加经验 | `raid_damage_units`、`raid_add_unit_experience` | `effects_documentation.md:5216,5233` |
| effect：降低项目进度 | `raid_reduce_project_progress_ratio` | `effects_documentation.md:5273` |
| trigger：特殊项目是否完成（常用于解锁核突袭） | `is_special_project_completed = sp:sp_nuclear_bomb` | `common/raids/categories/raid_categories.txt:25` |
| effect：加行动 token | `add_operation_token = { tag = GER token = some_token_id }` | `effects_documentation.md:1822-1833` |
| trigger：是否有 token | `has_operation_token` | `triggers_documentation.md:4516` |

## 4. 最小可跑完整示例（行动 + 阶段 + token）

**① `common/operation_phases/HHO_phases.txt`**

```pdx
HHO_phase_infiltrate = {
	name = HHO_phase_infiltrate
	desc = HHO_phase_infiltrate_desc
	icon = "GFX_report_event_hitler_handshake"
	picture = "GFX_report_event_hitler_handshake"
	outcome = HHO_phase_infiltrate_outcome
	requirements = {
		has_full_control_of_state = 64
	}
	equipment = {
		infantry_equipment = 200
	}
}

HHO_phase_extract = {
	name = HHO_phase_extract
	desc = HHO_phase_extract_desc
	icon = "GFX_report_event_hitler_handshake"
	picture = "GFX_report_event_hitler_handshake"
	outcome = HHO_phase_extract_outcome
	outcome_extra = HHO_phase_extract_outcome_extra
	return_on_complete = yes
	equipment = {
		infantry_equipment = 100
	}
}
```

**② `common/operation_tokens/HHO_tokens.txt`**

```pdx
HHO_steel_blueprints_token = {
	name = HHO_steel_blueprints_token
	desc = HHO_steel_blueprints_token_desc
	icon = GFX_operation_test_icon
	intel_source = civilian
	intel_gain = 0.5
}
```

**③ `common/operations/HHO_operations.txt`**

```pdx
HHO_steal_steel_blueprints = {
	icon = GFX_operation_test_icon
	name = HHO_steal_steel_blueprints
	desc = HHO_steal_steel_blueprints_desc
	priority = 15

	days = 30
	danger_level = 5
	operatives = 1
	network_strength = 50

	allowed = { always = yes }
	available = {
		FROM = { has_war = no }
	}

	phases = {
		HHO_phase_infiltrate = { base = 100 }
	}
	phases = {
		HHO_phase_extract = { base = 100 }
	}

	awarded_tokens = { HHO_steel_blueprints_token }

	equipment = {
		infantry_equipment = 300
	}
	return_on_complete = no

	on_start = {
		ROOT = { add_command_power = -10 }
	}

	outcome_execute = {
		ROOT = { add_operation_token = { tag = FROM token = HHO_steel_blueprints_token } }
		ROOT = { add_stability = 0.01 }
	}

	ai_will_do = {
		factor = 5
	}
}
```

### 需要的本地化（`localisation/english/HHO_intel_l_english.yml`）

```yml
l_english:
 HHO_steal_steel_blueprints:0 "Steal Steel Blueprints"
 HHO_steal_steel_blueprints_desc:0 "Our agents can copy the alloy recipes of a rival."
 HHO_steel_blueprints_token:0 "Steel Blueprints"
 HHO_steel_blueprints_token_desc:0 "Copied technical documents on alloy treatment."
 HHO_phase_infiltrate:0 "Infiltrate the Ministry"
 HHO_phase_infiltrate_desc:0 "Get an agent inside the ministry building."
 HHO_phase_infiltrate_outcome:0 "Our agent walked out with the files."
 HHO_phase_extract:0 "Extract the Agent"
 HHO_phase_extract_desc:0 "Bring our agent home before the alarm."
 HHO_phase_extract_outcome:0 "The agent crossed the border safely."
 HHO_phase_extract_outcome_extra:0 "The agent never checked in."
```

> `icon = GFX_operation_test_icon` 只是文档示例名；真实项目请用原版已有 sprite（`common/operations/00_operations.txt` 里能看到原版用的图标名）。

## 5. 新增 vs 覆盖

- `common/operations/`、`operation_phases/`、`operation_tokens/`、`intelligence_agency_upgrades/`：**新增文件 + 新 ID**。
- `common/raids/categories/raid_categories.txt`：只有一个文件且是 `categories = { }` 包裹；新增类别需要**改这个原版文件**或自己新建一个同样有 `categories = { }` 的文件（后者更安全，引擎会逐个文件读）。
- 突袭类型文件：新增 `common/raids/HHO_raids.txt` + `types = { }`。

## 6. 1.19 相关注意

- **1.19 的突袭系统新增了 `max_distance`、`unit_animations`、`ai_min_success_chance`、`days_re_enable` 等字段**（`common/raids/_documentation.md:55-88`），旧教程里的突袭写法缺这些也能跑，但表现/平衡会差。
- 突袭类别里的 `faction_influence_score_on_success` 是 1.19 阵营系统的挂钩（`raid_categories.txt:6`）。
- `is_special_project_completed = sp:<token>` 是「特殊项目 → 突袭解锁」的标准触发（`raid_categories.txt:25`）。
- 行动文档里仍有「待迁移到 on_actions」的注释（`_documentation.md:268-269`），说明部分 on_action 钩子尚未迁移，别依赖。
- ⚠️ 行动/突袭的图标与实体资源名大量是占位示例（`_documentation.md` 里的 `GFX_operation_test_icon` 等），真实可用的 sprite 必须自己 grep `interface/`。

## 7. 常见错误 / 自检清单

- [ ] 行动文件顶层是 `<token> = { ... }`（无包裹）；阶段/ token/升级同理。
- [ ] `phases` 里引用的 phase token 都在 `common/operation_phases/` 定义。
- [ ] `awarded_tokens` / `required_tokens` 的 token 都真实存在，并已本地化。
- [ ] `equipment` 里写的装备类型存在（`civilian_factories` 是特殊允许项）。
- [ ] `operation_target`/`selection_target`/`target_type` 搭配合理（有 `selection_target` 才会有目标州作用域 `FROM.FROM`）。
- [ ] 机构升级没有 `description` 字段（写了也不生效），描述用 `<upgrade_name>_desc`。
- [ ] 突袭：`category` 存在；`target_types`/`starting_point`/`unit_requirements` 至少各有一条；表现字段齐全。
- [ ] 突袭触发器保持轻量（文档反复强调性能）。
- [ ] 所有 "[[scripted localization]]" 位置可以用裸文本，但推荐 loc key，便于中英双语。

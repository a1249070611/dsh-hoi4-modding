---
title: 军工组织（Military Industrial Organization, MIO）
domain: 02_content
scope: country / industrial_org
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/military_industrial_organization/organizations/_documentation.md
  - common/military_industrial_organization/policies/_documentation.md
  - common/military_industrial_organization/organizations/00_generic_organization.txt
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
---

# 军工组织（MIO）

MIO 是「设计公司」的替代品：一棵可解锁的**特质树**，加成同时作用于**装备型号**（`equipment_bonus`）和**生产线**（`production_bonus`）。
1.19.4.2 的完整权威说明在 `common/military_industrial_organization/organizations/_documentation.md`（575 行）、`.../policies/_documentation.md`（91 行）与 `.../ai_bonus_weights/_documentation.md`（38 行）。
本域共 63 个文件、44,406 行（`organizations/` 55 个 `.txt`、`policies/`、`ai_bonus_weights/`），是 BBA（Arms Against Tyranny）之后才有的系统。

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 组织 | `common/military_industrial_organization/organizations/*.txt`（原版 `TAG_organization.txt` + `00_generic_organization.txt`） |
| 政策 | `common/military_industrial_organization/policies/*.txt`（`_land_policies.txt`、`_air_policies.txt`、`_navy_policies.txt`、`_general_policies.txt`） |
| AI 权重 | `common/military_industrial_organization/ai_bonus_weights/ai_bonus_weights.txt` |
| 顶层结构 | 组织文件直接一个 `<token> = { ... }`（**没有外层包裹**） |
| 本地化 | `<tag>_<token>` 优先，否则 `<token>`；特质同理 `<tag>_<mio>_<trait>` → `<mio>_<trait>` → `<trait>`（见文档注释） |
| 图标 | `icon = GFX_xxx`；缺省回退 `GFX_TAG_<token>` → `GFX_<token>` → `GFX_idea_unknown` |
| 校验和 | 影响 |

原版必读：

- `organizations/_documentation.md:14-197` —— 组织全部字段（逐行注释，**先读这个**）。
- `organizations/_documentation.md:199-235` —— `include` 复用已有 MIO + `add_trait`/`remove_trait`/`override_trait`。
- `organizations/_documentation.md:239-384+` —— 各装备类型可用的 `equipment_bonus` 数值键清单（坦克/舰船/飞机/步兵装备）。
- `organizations/00_generic_organization.txt:13-75` —— 真实组织开头（`icon` + 复杂的 `allowed` DLC 排除）。
- `policies/_documentation.md:8-89` —— 政策全部字段。

**`equipment_bonus` 可用键按装备类型分节（`organizations/_documentation.md`，1.19.4.2 实测行号）**：
Tanks `:252`、Ships `:280`、Planes `:320`、Materiel `:354`；步兵相关 `:364`（infantry）、`:383`（support）、`:393`（artillery）、`:410`（anti-air）、`:427`（anti-tank）、`:445`（rocket artillery）、`:464`（motorized）、`:478`（motorized rocket）、`:497`（mechanized）、`:515`（amphibious mechanized）、`:534`（armored car）、`:554`（train）、`:565`（railway gun）。
写之前先跳到对应小节确认键名——不同装备类型能写的 stat 不一样，写错键不报错但无效。
1.19.4 的两批脚本改动清单里都没有 MIO 目录，本域字段与数值在 1.19.4 未动，可直接沿用本文结论。

## 2. 结构（带注释）

```pdx
MY_MIO_token = {
	name = loc_key                  # 可选；不写就用 token 作 key
	icon = GFX_idea_generic_tank_manufacturer_1
	background = GFX_xxx            # 可选，详情页背景

	allowed = { original_tag = SWE } # 必填；开局时为所有国家求值，true 则该国获得实例
	visible = { }                    # 可选，MIO 作用域，FROM = 国家
	available = { }                  # 可选，显示但灰

	equipment_type = { infantry_equipment armor }  # 该 MIO 能匹配的装备类型/分类/组
	research_categories = { infantry_weapons }     # 能匹配的科技类别（决定设计团队加成）

	# 可选 on-action（MIO 作用域，FROM = 国家）
	on_design_team_assigned_to_tech = { }
	on_design_team_assigned_to_variant = { }
	on_industrial_manufacturer_assigned = { }
	on_tech_research_cancelled = { }
	on_tech_research_completed = { }
	on_industrial_manufacturer_unassigned = { }

	research_bonus = 0.2            # 默认值取 define DESIGN_TEAM_RESEARCH_BONUS
	task_capacity = 3               # 默认取 define DEFAULT_INITIAL_TASK_CAPACITY

	ai_will_do = { factor = 1 }     # MIO 作用域；与 ai_bonus_weights 相乘

	tree_header_text = {            # 特质树上方的一行说明（可重复）
		text = MY_flavor_loc
		x = 1                       # 横向格坐标（可用小数对齐两格之间）
	}

	initial_trait = {               # 开局即生效的初始特质（只能用下面 5 个参数）
		name = MY_MIO_initial
		equipment_bonus = { reliability = 0.1 }
		production_bonus = { production_cost_factor = -0.05 }
		organization_modifier = { military_industrial_organization_funds_gain = 0.2 }
		limit_to_equipment_type = { infantry_equipment }
	}

	trait = {
		token = MY_trait_one        # 必填，全 MIO 内唯一
		name = MY_trait_one_loc     # 可选
		icon = GFX_idea_generic_tank_manufacturer_1
		special_trait_background = yes   # 可选，金色背景
		position = { x = 0 y = 0 }

		# 前置（三选一或组合）
		parent = { traits = { MY_trait_zero } num_parents_needed = 1 }
		# any_parent = { MY_trait_zero }     # = parent + num_parents_needed 1
		# all_parents = { A B }               # = 需要全部前置
		# relative_position_id = MY_trait_zero # 位置相对某个特质

		mutually_exclusive = { MY_trait_two }   # 互斥（两边都要写）

		visible = { }
		available = { }
		on_complete = { }            # 解锁时（MIO 作用域）

		limit_to_equipment_type = { armor }   # 限定只对某类装备生效（可在 MIO 范围内进一步收窄）

		equipment_bonus = {          # 作用于「已分配给型号」时
			reliability = 0.2
			soft_attack = 0.1
		}
		production_bonus = {         # 作用于「已分配给产线」时
			production_cost_factor = -0.1
			production_capacity_factor = 0.1
		}
		organization_modifier = {    # 只作用于 MIO 自身
			military_industrial_organization_research_bonus = 0.1
			military_industrial_organization_task_capacity = 2
			military_industrial_organization_funds_gain = 0.5
			military_industrial_organization_size_up_requirement = -0.2
			military_industrial_organization_design_team_assign_cost = -0.33
			military_industrial_organization_design_team_change_cost = -0.5
			military_industrial_organization_industrial_manufacturer_assign_cost = -0.66
		}
		ai_will_do = { factor = 1 }
	}
}
```

### 复用现成组织（`include`）

```pdx
MY_variant_of_generic_tank = {
	include = generic_tank_organization   # 复制它的全部内容
	icon = GFX_idea_generic_tank_manufacturer_1
	research_bonus = 0.3                  # 覆盖其中一部分
	delete_included_values = { name on_design_team_assigned_to_variant }  # 清空不需要的
	add_trait = { token = MY_extra_trait position = { x = 3 y = 0 } }
	remove_trait = { some_trait }
	override_trait = {
		token = some_trait
		equipment_bonus = { reliability = 0.3 }
		delete_included_values = { relative_position_id }
	}
}
```

⚠️ 原版文档提到：`include` 的两半若分处两个文件，热重载需要「两个文件都保存」才生效（`_documentation.md:232`）。
这在**开发者调试环境**下成立；普通玩家 mod 环境仍按「改完重启」处理。

### 政策（`policies/`）

```pdx
MY_policy_token = {
	name = loc_key                  # 可选，回退规则同 MIO
	icon = GFX_xxx
	cost = 10                       # 默认 define DEFAULT_INITIAL_POLICY_ATTACH_COST
	cooldown = 60                   # 默认 define DEFAULT_INITIAL_ATTACH_POLICY_COOLDOWN

	allowed = { }                   # 必填；开局对每个 MIO 求值，false 则永远不考虑
	visible = { }                   # 可选
	available = { }                 # 可选

	equipment_bonus = {             # 这里要写「装备组/类别/原型/型号」
		infantry_equipment = { reliability = 0.2 soft_attack = 0.1 }
		same_as_mio = { }           # 应用到该 MIO 所有部门的装备
	}
	production_bonus = {
		infantry_equipment = { production_cost_factor = -0.1 }
	}
	organization_modifier = { }

	on_add = { }                    # MIO 作用域
	on_remove = { }
	ai_will_do = { }
}
```

## 3. 脚本里怎么访问 MIO

| 类型 | 写法 | 证据 |
|---|---|---|
| effect：给钱（会触发升级） | `add_mio_funds = 200`（INDUSTRIAL_ORG 作用域） | `effects_documentation.md:1590-1605` |
| effect：给资金增益系数 | `add_mio_funds_gain_factor = 0.1` | `effects_documentation.md:1607` |
| effect：解锁提示（只显示，不解锁） | `unlock_military_industrial_organization_tooltip = mio:my_mio_token` | `effects_documentation.md:8475-8486` |
| effect：迭代所有 MIO | `every_military_industrial_organization = { limit = { } add_mio_funds = 100 }` | `effects_documentation.md:3937-3947` |
| effect：改政策成本/冷却 | `set_mio_policy_cost` / `set_mio_policy_cooldown` | `effects_documentation.md:7303,7325` |
| trigger：是否有特质 | `has_mio_trait = mio_trait` | `triggers_documentation.md:4364` |
| trigger：规模/政策/装备类型 | `has_mio_size`、`has_mio_policy`、`has_mio_policy_active`、`has_mio_equipment_type`、`has_mio_research_category`、`has_mio_number_of_completed_traits`、`has_mio_flag` | `triggers_documentation.md:4261-4348` |

作用域前缀：MIO 用 `mio:<token>`（`unlock_military_industrial_organization_tooltip = mio:my_mio_token`）。
变量里存 MIO 用 `var:xxx`（例如 `var:my_mio_var = { add_mio_funds = 200 }`）。

## 4. 最小可跑完整示例

文件：`common/military_industrial_organization/organizations/HHO_steel_works.txt`

```pdx
HHO_steel_works = {
	name = HHO_steel_works
	icon = GFX_idea_generic_tank_manufacturer_1

	allowed = {
		original_tag = SWE
	}

	visible = { always = yes }
	available = { always = yes }

	equipment_type = { infantry_equipment armor }
	research_categories = { infantry_weapons }

	research_bonus = 0.15
	task_capacity = 3

	initial_trait = {
		name = HHO_steel_works_initial
		equipment_bonus = {
			reliability = 0.05
		}
		production_bonus = {
			production_cost_factor = -0.03
		}
		organization_modifier = {
			military_industrial_organization_funds_gain = 0.1
		}
	}

	trait = {
		token = HHO_swedish_quality
		name = HHO_swedish_quality
		icon = GFX_idea_generic_tank_manufacturer_1
		position = { x = 0 y = 0 }
		limit_to_equipment_type = { infantry_equipment }
		equipment_bonus = {
			reliability = 0.1
			soft_attack = 0.05
		}
		production_bonus = {
			production_capacity_factor = 0.05
		}
	}

	trait = {
		token = HHO_cheap_steel
		name = HHO_cheap_steel
		icon = GFX_idea_generic_tank_manufacturer_1
		any_parent = { HHO_swedish_quality }
		position = { x = 1 y = 0 }
		production_bonus = {
			production_cost_factor = -0.1
		}
		mutually_exclusive = { HHO_premium_steel }
	}

	trait = {
		token = HHO_premium_steel
		name = HHO_premium_steel
		icon = GFX_idea_generic_tank_manufacturer_1
		any_parent = { HHO_swedish_quality }
		position = { x = 1 y = 1 }
		equipment_bonus = {
			reliability = 0.15
			breakthrough = 0.05
		}
		mutually_exclusive = { HHO_cheap_steel }
	}
}
```

> 注意：**树里的根特质不能写 `parent`**（原版文档：不是第一个才需要 parent）。上面 `HHO_swedish_quality` 就是根特质，没有 parent。

文件：`common/military_industrial_organization/policies/HHO_steel_policies.txt`

```pdx
HHO_export_focus_policy = {
	name = HHO_export_focus_policy
	icon = GFX_idea_generic_tank_manufacturer_1
	cost = 10
	cooldown = 60

	allowed = {
		original_tag = SWE
	}
	visible = { always = yes }
	available = { always = yes }

	production_bonus = {
		same_as_mio = {
			production_cost_factor = -0.05
		}
	}
	organization_modifier = {
		military_industrial_organization_funds_gain = 0.2
	}
}
```

### 需要的本地化（`localisation/english/HHO_mio_l_english.yml`）

```yml
l_english:
 HHO_steel_works:0 "Holandia Steel Works"
 HHO_steel_works_initial:0 "Steel Heritage"
 HHO_swedish_quality:0 "Swedish Quality"
 HHO_swedish_quality_desc:0 "Better inspection, fewer defects."
 HHO_cheap_steel:0 "Cheap Steel"
 HHO_cheap_steel_desc:0 "Cut costs, accept some waste."
 HHO_premium_steel:0 "Premium Steel"
 HHO_premium_steel_desc:0 "Spare no expense on quality."
 HHO_export_focus_policy:0 "Export Focus"
 HHO_export_focus_policy_desc:0 "Prioritise foreign orders."
```

## 5. 新增 vs 覆盖

- **推荐**：新文件 + 新 token（`HHO_steel_works`）。
- 「改原版 MIO 的一个数值」：`include = 原版token` + 覆盖字段（`_documentation.md:199-233` 的正规做法），比整块抄安全。
- 同名文件整体替换原版 `TAG_organization.txt` → 禁止（几千行）。

## 6. 1.19 相关注意

- MIO 是 **Arms Against Tyranny（`dlc/dlc038_arms_against_tyranny`）** 时代的系统；原版国家对无 DLC 情况用 `allowed` 里的 `has_dlc` 组合做降级（`00_generic_organization.txt:17-75` 是范例）。
- `equipment_type` 的可选值来自 **script enum**（`common/script_enums.txt` 的 `script_enum_equipment_bonus_type`），
  文档明确写「cf. script enum script_enum_equipment_bonus_type」。写错 = 该类型永不匹配。
- 各装备类型**能用的数值键不同**：坦克 `soft_attack/armor_value/breakthrough/reliability/...`；
  舰船 `lg_attack/torpedo_attack/naval_speed/...`；飞机 `air_attack/air_agility/air_defence/...`；
  步兵装备 `reliability/soft_attack/hard_attack/ap_attack/build_cost_ic/...`（完整清单在 `_documentation.md:252-384+`）。
- `organization_modifier` 只有 7 个 `military_industrial_organization_*` 键（`_documentation.md:171-179`），别塞普通国家修正。

## 7. 常见错误 / 自检清单

- [ ] 文件顶层直接是 `<mio_token> = { ... }`（没有包裹层）。
- [ ] `allowed` 必填，并且每个国家只在该块为 true 时拿到实例。
- [ ] `equipment_type` 用的是 archetype/category/equipment group 名，不是装备文件名。
- [ ] `research_categories` 与 `common/technologies` 的 `categories` 一致，否则设计团队加成吃不到。
- [ ] 特质树的根特质**不写** parent；非根特质至少有一个 `parent`/`any_parent`/`all_parents`。
- [ ] 互斥特质**两边都写** `mutually_exclusive`。
- [ ] `position` 不重复（同一个坐标两个特质会让 UI 重叠）。
- [ ] `equipment_bonus` 里每个键在该装备类型下合法（见 §6 清单）。
- [ ] 组织的 `name`/每个 trait 都有本地化（按 TAG_ 回退规则命名最方便）。
- [ ] 政策 `equipment_bonus` 必须写「装备类型 → 数值」两层，不能像特质那样只写数值。

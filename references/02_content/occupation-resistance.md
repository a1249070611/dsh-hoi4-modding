---
title: 占领、抵抗与顺从（Occupation, Resistance & Compliance）
domain: 02_content
scope: state / country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/occupation_laws/occupation_laws.txt
  - common/resistance_activity/resistance_activity.txt
  - common/resistance_compliance_modifiers/resistance_modifiers.txt
  - common/resistance_compliance_modifiers/compliance_modifiers.txt
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
---

# 占领、抵抗与顺从

三组数据文件共同决定「占领区怎么反抗、你用什么法律压」：

| 内容 | 文件 | 作用 |
|---|---|---|
| 占领法 | `common/occupation_laws/occupation_laws.txt` | 玩家可切换的占领政策，决定抵抗目标/顺从/驻军需求 |
| 抵抗活动 | `common/resistance_activity/resistance_activity.txt` | 抵抗组织会做的「事件」（破坏工厂、罢工…） |
| 抵抗/顺从阈值修正 | `common/resistance_compliance_modifiers/{resistance_modifiers,compliance_modifiers}.txt` | 抵抗/顺从到某个百分比时获得的修正 |

这些文件都把**完整模板写在文件开头的注释里**，是 1.19.4.2 最省事的抄写源。

**官方文档位置（1.19.4.2 实测，2026-11-06）**：本域**三组文件都没有** `_documentation.md`（`common/occupation_laws/`、
`common/resistance_activity/` 下都没有 .md），占位量级 —— `occupation_laws.txt` 1 个文件 / 1,113 行、
`resistance_activity.txt` 1 个文件 / 717 行、`resistance_compliance_modifiers/` 2 个文件。字段定义只能靠文件头注释
（`occupation_laws.txt:1-62`、`resistance_activity.txt:1-26`）+ `documentation/effects_documentation.md` /
`triggers_documentation.md` / `modifiers_documentation.md` 里对应的条目。

1.19.4 的改动：10-28 批改过 `common/occupation_laws/`（数值层面），抵抗活动文件未在改动清单中；没有新增或改名文档。

## 1. 占领法（`common/occupation_laws/occupation_laws.txt`）

文件头注释 `:1-62` 给出全部字段；真实法律从 `:63` 的 `missing_garrison_scaled_effect` 开始。结构：

```pdx
MY_occupation_law = {
	tooltip = "loc_key"            # 条目的 tooltip 描述（可选）
	icon = "GFX_icon:5"            # gfx 条目 + frame；省略则用 GFX_occupation_policy_icon_strip
	sound_effect = "sound_effect"  # 选择时播放

	visible = { always = yes }     # 作用域：占领国（不检查目标级）
	available = { always = yes }   # 作用域：THIS = 占领国，FROM = 被占领国

	fallback_law = law_id          # 当前法律失效时回退到哪条
	main_fallback_law = yes        # 全表只能有一条：人力/装备不足时用它兜底

	state_modifier = {             # 适用于该法律管辖的州
		resistance_target = 0.1
		compliance_gain = -0.045
	}
	suppressed_state_modifier = {   # 抵抗被完全压制（=0）时改用它
		required_garrison_factor = -1
		resistance_target = 0.4
	}

	gui_order = 1                  # UI 排序（默认按加载顺序）

	ai_will_do = {                 # 作用域：STATE；FROM = 占领国；FROM.FROM = 被占领国
		base = 100
		modifier = {
			steel > 10
			add = 100
		}
	}
}
```

要点（全部来自 `occupation_laws.txt:1-62` 注释）：

- `main_fallback_law` 全表**有且仅有一条**。
- AI 权重里可用临时变量：`ai_desire_resource`、`uncapped_resistance_target`、`resistance_target_without_law`、
  `garrison_min_support_ratio`、`garrison_equipment_support_ratio`、`garrison_manpower_support_ratio`。
- 当这条法律不再 `visible`/`available` 时，会回退到 `fallback_law`（没有则回退到主 fallback）。

真实范例：`missing_garrison_scaled_effect:63`、`no_garrison:81`（含 `missing_garrison_law = yes`，这是较新的兜底法律标记）。

### 脚本设置占领法

```pdx
GER = { set_occupation_law = foreign_civilian_oversight }       # 设默认法律
GER = { POL = { set_occupation_law = default_law } }           # 取消对某国的覆写
GER = { 123 = { set_occupation_law = military_governor_occupation } } # 针对某个州
ITA = { set_occupation_law_where_available = colonial_police } # 在所有可用层级上设置
```

（`documentation/effects_documentation.md:7434-7463`；`default_law` 是特殊 token，用于「清除覆写/回到默认」。）

触发器：`occupation_law = <law_id>`（`triggers_documentation.md:6918`）。

## 2. 抵抗活动（`common/resistance_activity/resistance_activity.txt`）

文件头注释 `:1-26` 即模板；真实条目从 `:28` 的 `sabotage_arms_factory` 起。

```pdx
HHO_sabotage_steel_mill = {
	available = {                       # 能否发生（STATE 作用域）
		non_damaged_building_level = {
			building = steel_mill
			level > 0
		}
	}

	weight = {                          # 权重（可用变量控制触发概率）
		base = 1
		modifier = {
			occupation_law = harsh_quotas_occupation
			add = -0.25
		}
	}

	max_amount = 3                      # 同一时间最多几条
	duration = 10                       # 持续天数

	effect = {                          # 实际效果
		damage_building = {
			type = steel_mill
			damage = 0.5
		}
	}

	state_modifier = { }                # 生效期间的州修正
	alert_text = HHO_sabotage_alert     # 可选：地图上的警报文本
}
```

（结构逐字来自 `resistance_activity.txt:1-26`；`damage_building` 的语法见 `documentation/effects_documentation.md:3374`。）

强制开启抵抗：

```pdx
123 = { start_resistance = POL }      # STATE 作用域，参数为核心国家
123 = { start_resistance = yes }      # 对当前占有者？
# 若该州本不可能有抵抗（例如已是核心），配合 force_enable_resistance（effects_documentation.md:4346）
```

（`documentation/effects_documentation.md:8084-8094`。）

## 3. 抵抗/顺从阈值修正

文件头注释（`resistance_modifiers.txt:1-30`）说明四种 type：

| type | 作用域 |
|---|---|
| `state_resistance_modifier` | 州级；`FROM`/`ROOT` = 占领国，`FROM.FROM` = 被占领国 |
| `core_resistance_modifier` | 国家级；`ROOT` = 占领国，`FROM` = 被占领国 |
| `state_compliance_modifier` | 同 state 级 |
| `core_compliance_modifier` | 同 core 级（注意注释里拼成 `core_compliancemodifier`，以 `compliance_modifiers.txt` 实际用法 `core_compliance_modifier` 为准） |

```pdx
HHO_compliance_30 = {
	type = core_compliance_modifier
	icon = "GFX_occupation_compliance_modifier_strip:2"
	small_icon = "GFX_occupation_compliance_modifier_small_strip:2"
	threshold = 30                 # 达到该百分比启用
	margin = 2                     # 低于 threshold - margin 才关闭（防抖）
	state_modifier = {
		required_garrison_factor = -0.25
		recruitable_population = 0.005
	}
}
```

原版例子：`compliance_modifiers.txt:4-45`（`compliance_15/25/40/60`）。

动态修正（只在需要时由脚本添加）：

```pdx
# 注释里的 dynamic = yes 表示默认不挂到州上，只能由脚本添加/移除
HHO_dynamic_resistance = {
	type = state_resistance_modifier
	dynamic = yes
	threshold = 20
	margin = 2
	state_modifier = {
		resistance_growth = 0.1
	}
}
```

```pdx
123 = { add_state_resistance_compliance_modifier = HHO_dynamic_resistance }
123 = { remove_state_resistance_compliance_modifier = HHO_dynamic_resistance }
```

（`documentation/effects_documentation.md:2210,6260`。）

## 4. 最小可跑完整示例

**① 追加到新文件 `common/occupation_laws/HHO_laws.txt`**

```pdx
HHO_steel_administration = {
	tooltip = HHO_steel_admin_tt
	icon = 3                       # 复用原版占领法图标条帧号
	sound_effect = "Martial_Law_Interface_No_Garrison"

	visible = {
		has_war = yes
	}
	available = {
		has_political_power > 0
	}

	state_modifier = {
		resistance_target = 0.15
		compliance_gain = -0.05
		required_garrison_factor = 0.2
	}
	suppressed_state_modifier = {
		resistance_target = 0.05
		required_garrison_factor = -0.5
	}

	gui_order = 50

	ai_will_do = {
		base = 50
	}
}
```

**② 追加到新文件 `common/resistance_activity/HHO_resistance.txt`**

```pdx
HHO_sabotage_steel_mill = {
	available = {
		non_damaged_building_level = {
			building = steel_mill
			level > 0
		}
	}
	weight = {
		base = 1
		modifier = {
			occupation_law = HHO_steel_administration
			add = 1
		}
	}
	duration = 7
	effect = {
		damage_building = {
			type = steel_mill
			damage = 0.3
		}
	}
}
```

**③ 追加到新文件 `common/resistance_compliance_modifiers/HHO_compliance.txt`**

```pdx
HHO_compliance_20 = {
	type = core_compliance_modifier
	threshold = 20
	margin = 2
	state_modifier = {
		required_garrison_factor = -0.1
	}
}
```

### 需要的本地化（`localisation/english/HHO_occupation_l_english.yml`）

```yml
l_english:
 HHO_steel_administration:0 "Steel Administration"
 HHO_steel_admin_tt:0 "We govern the steel districts directly, at the cost of local resentment."
 HHO_sabotage_steel_mill:0 "Steel Mill Sabotage"
 HHO_compliance_20:0 "Local Cooperation"
```

> `HHO_steel_admin_tt` 只是 `tooltip` 字段用的 key；法律名本身也需一条（`HHO_steel_administration`）。
> 结论：**占领法/抵抗活动/阈值修正的 id 都是本地化 key**（原版注释明确 "id is used for localization"）。

## 5. 新增 vs 覆盖

- 占据法/抵抗活动/阈值修正都**支持多文件追加**（引擎读取目录下每个文件），因此：
  **新建 `HHO_*.txt` 即可**，不要改 `occupation_laws.txt`（1113 行）或 `resistance_activity.txt`（717 行）。
- 同名文件整体替换：禁止。

## 6. 1.19 相关注意

- `missing_garrison_law = yes` 与 `missing_garrison_scaled_effect`（`occupation_laws.txt:63-65`）是「驻军不足时的缩放兜底法」，属较新机制。
- `suppressed_state_modifier`（抵抗压制为 0 时的替代修正）是 1.19 常用写法，旧教程常漏。
- `fallback_law` 链要小心形成环（A→B→A），原版注释只要求「必须有 main fallback」，没说会检测环。
- 抵抗/顺从修正的 `dynamic = yes` 让修正只在脚本添加时生效（注释 `:27-30`）。

## 7. 常见错误 / 自检清单

- [ ] 新法律的 `id` 与所有相关 id（`fallback_law`、`resistance_activity` 的 `occupation_law` 引用）一致。
- [ ] 全表**只有一个** `main_fallback_law = yes`（原版注释要求 "there must be exactly one"）。
- [ ] `state_modifier` 里的键（`resistance_target`、`compliance_gain`、`required_garrison_factor`…）在 `modifiers_documentation.md` 中存在。
- [ ] 抵抗活动的 `effect`/`state_modifier` 作用域是 STATE。
- [ ] 阈值修正的 `threshold` + `margin` 与 `state_modifier` 搭配合理（margin 太小会频繁开关）。
- [ ] 每个 id 都有本地化；`tooltip`/`alert_text` 指向的 key 存在。
- [ ] `occupation_law = <id>` 触发器写的是 id，不是「名字」。
- [ ] 脚本给州加动态修正前，确认它是 `dynamic = yes`（否则会重复添加）。

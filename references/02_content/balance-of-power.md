---
title: 权力平衡（Balance of Power）
domain: 02_content
scope: country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/bop/_test.txt
  - common/bop/FIN.txt
  - common/decisions/_documentation.md
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - localisation/english/aat_bop_l_english.yml
---

# 权力平衡（Balance of Power）

权力平衡是「一根滑条 + 两侧立场 + 若干区间」的系统：滑条数值落在哪个 `range`，就吃哪个 `modifier`。
它通常和**决议分类**绑定，在决议界面里显示成一根条形图。

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/bop/*.txt`（1.19 简写为 `bop`；原版文件 `FIN.txt`、`ITA.txt`、`SWE.txt`、`DEN.txt`、`CZE.txt`、`ETH.txt`、`BRA.txt`、`PRC.txt`、`SWI.txt`） |
| 顶层结构 | 直接 `<bop_id> = { ... }`（无包裹层） |
| 关联决议 | `decision_category = <common/decisions 里的分类 ID>` |
| 本地化 | bop id、每个 side id、`decision_category` 的 id 都需要本地化。证据 `localisation/english/aat_bop_l_english.yml:44-46`（`FIN_power_balance`、`FIN_bad_side`、`FIN_good_side`）；`aat_decisions_l_english.yml:537` 用 `$FIN_power_balance$` 复用 |
| 校验和 | 影响 |

原版必读：

- `common/bop/_test.txt:1-39` —— **最小完整模板**（1 个中立 range + 两个 side，各带一个 range）。抄它最快。
- `common/bop/FIN.txt` —— 真实复杂案例：`initial_value`、`left_side`/`right_side`、4 个 range、`on_activate` 里 `set_power_balance_gfx` + `swap_ideas`（换国家精神）。
- 芬兰的决策：`decision_category = FIN_balance_of_power_category`（`FIN.txt:5`），分类名在 `aat_decisions_l_english.yml:537`。

**官方文档位置（1.19.4.2 实测，2026-11-06）**：`common/bop/` **没有** `_documentation.md`——
本域是「无文档、全靠实例」的典型：10 个 txt、3,738 行，唯一「规范」是 `_test.txt:1-39` 的最小模板 +
`FIN.txt` 的复杂实例；脚本接口（`add_power_balance_value` / `add_power_balance_modifier` / `set_power_balance` /
`is_power_balance_side_active`）散在 `documentation/effects_documentation.md` 与 `triggers_documentation.md` 里。
BOP 系统随 **Arms Against Tyranny** 引入（原版文案与 `aat_*` 本地化前缀可证），1.19.4 的两批脚本改动清单里没有
`common/bop/`，字段与数值都未动。

## 2. 结构（带注释）

```pdx
MY_balance_id = {
	initial_value = 0.25            # 开局值（-1 ~ 1 之间，0 = 中间）
	left_side = MY_left_side         # 左端立场 side id
	right_side = MY_right_side       # 右端立场 side id
	decision_category = MY_bop_category   # 可选：把滑条挂到某个决议分类

	# ===== 中立区间（不属于任何 side 的中间段）=====
	range = {
		id = MY_mid_range
		min = -0.1
		max = 0.1
		modifier = {                 # 该区间的国家修正
			war_support_weekly = 0.5
		}
		on_activate = { }            # 进入区间时（可选）
		on_deactivate = { }          # 离开区间时（可选）
	}

	# ===== 左 side =====
	side = {
		id = MY_left_side
		icon = GFX_idea_generic_agrarian_society   # 侧边图标（原版 _test.txt:17）
		range = {
			id = MY_left_range
			min = -1
			max = -0.1
			modifier = {
				war_support_weekly = 0.1
			}
		}
	}

	# ===== 右 side =====
	side = {
		id = MY_right_side
		icon = GFX_idea_generic_degauss_ship_hulls
		range = {
			id = MY_right_range
			min = 0.1
			max = 1
			modifier = {
				war_support_weekly = 0.9
			}
		}
	}
}
```

### 进/出区间时做剧情（原版 FIN 写法）

```pdx
range = {
	id = FIN_medium_trust_range
	min = -0.10
	max = 0.10
	modifier = { }
	on_activate = {
		# 换图形（领导人相关图标可以脚本化拼接）
		set_power_balance_gfx = {
			id = FIN_power_balance
			side = FIN_bad_side
			gfx = "GFX_bop_FIN_[GetLeaderBopIcon]_bad_side"
		}
		# 换国家精神（原版用 swap_ideas 避免闪烁）
		swap_ideas = {
			remove_idea = FIN_sisu_1
			add_idea = FIN_sisu_3
		}
		set_variable = { FIN_motion_of_no_confidence_dec_cost = 250 }
	}
	on_deactivate = { }
}
```

（`common/bop/FIN.txt:8-95`，注意 `gfx = "GFX_bop_...[GetLeaderBopIcon]..."` 里的方括号是**脚本化本地化/动态 GFX 名**，是 1.19 的写法。）

## 3. 脚本接口（effects / triggers）

| 类型 | 写法 | 证据 |
|---|---|---|
| 加减当前值 | `add_power_balance_value = { id = MY_balance_id value = 0.42 tooltip_side = MY_left_side }` | `effects_documentation.md:1893-1907` |
| 挂一个**静态修正** | `add_power_balance_modifier = { id = MY_balance_id modifier = static_modifier_id }` | `effects_documentation.md:1878-1891` |
| 直接设置 | `set_power_balance` / `set_power_balance_gfx` | `effects_documentation.md:7571,7589` |
| 判断当前是否在某侧 | `is_power_balance_side_active` | `triggers_documentation.md:6130` |

`add_power_balance_modifier` 的 `modifier` 必须是**静态修正库**里的 ID（原版 `common/modifiers/` 与 `common/event_modifiers.txt`；
文档原文："this must be defined in the static modifier database"）。

## 4. 最小可跑完整示例

**① `common/bop/HHO_bop.txt`**

```pdx
HHO_public_trust = {
	initial_value = 0.0
	left_side = HHO_low_trust
	right_side = HHO_high_trust
	decision_category = HHO_trust_category

	range = {
		id = HHO_mid_trust
		min = -0.2
		max = 0.2
		modifier = {
			stability_factor = 0.02
		}
	}

	side = {
		id = HHO_low_trust
		icon = GFX_idea_generic_agrarian_society
		range = {
			id = HHO_low_trust_range
			min = -1
			max = -0.2
			modifier = {
				stability_factor = -0.1
				political_power_factor = -0.1
			}
			on_activate = {
				set_power_balance_gfx = {
					id = HHO_public_trust
					side = HHO_low_trust
					gfx = "GFX_idea_generic_agrarian_society"
				}
			}
		}
	}

	side = {
		id = HHO_high_trust
		icon = GFX_idea_generic_degauss_ship_hulls
		range = {
			id = HHO_high_trust_range
			min = 0.2
			max = 1
			modifier = {
				stability_factor = 0.1
				war_support_factor = 0.05
			}
		}
	}
}
```

**② `common/decisions/HHO_trust_decisions.txt`**（把滑条挂进决议界面）

```pdx
HHO_trust_category = {

	HHO_trust_boost = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		visible = { always = yes }
		available = { has_political_power > 25 }
		cost = 25
		complete_effect = {
			add_power_balance_value = {
				id = HHO_public_trust
				value = 0.15
				tooltip_side = HHO_high_trust
			}
		}
		ai_will_do = { factor = 5 }
	}
}
```

### 需要的本地化（`localisation/english/HHO_bop_l_english.yml`）

```yml
l_english:
 HHO_public_trust:0 "Public Trust"
 HHO_low_trust:0 "§RLow Public Trust§!"
 HHO_high_trust:0 "§GHigh Public Trust§!"
 HHO_trust_category:0 "$HHO_public_trust$"
 HHO_trust_boost:0 "Address the Nation"
 HHO_trust_boost_desc:0 "A speech from the Prime Minister will raise public trust."
```

> 注意 `HHO_trust_category:0` 用 `$HHO_public_trust$` 复用同名文本，这是原版做法（`aat_decisions_l_english.yml:537` 的 `$FIN_power_balance$`）。

## 5. 新增 vs 覆盖

- **推荐**：新建 `common/bop/HHO_bop.txt` + 新 bop id + 新决议分类。
- 想给原版国家加一条 bop：`decision_category` 必须指向**该国已有的分类**（会复用原版决议界面），但你的 bop 文件仍是新文件。
- `common/bop/_test.txt` 是原版的测试文件（`_test_balance`），**不要改它**，但可以照抄。

## 6. 1.19 相关注意

- 目录名是 `common/bop/`（不是 `common/balance_of_power/`）。写错目录会被忽略。
- `set_power_balance_gfx` 的 `gfx` 支持 `"GFX_bop_FIN_[GetLeaderBopIcon]_bad_side"` 这种**动态拼接**（`FIN.txt:18`），
  也就是 1.19 支持在 GFX 名里放 loc 数据绑定；不加方括号也能正常引用静态 sprite。
- 原版只有 9 个 bop 国家（BRA/CZE/DEN/ETH/FIN/ITA/PRC/SWE/SWI），说明这是「大国/剧情国专属」系统。
- ⚠️ `has_power_balance_value` 之类的比较 trigger 未在 1.19.4.2 的 `triggers_documentation.md` 中确认；判断某侧时用 `is_power_balance_side_active`。

## 7. 常见错误 / 自检清单

- [ ] 文件在 `common/bop/`，顶层直接 `<bop_id> = { ... }`。
- [ ] `left_side` / `right_side` 的 id 与两个 `side = { id = ... }` 完全一致。
- [ ] 所有 range 的 `min`/`max` 覆盖 -1~1，且**互不重叠**；中立 range 不放 side 里。
- [ ] `modifier` 里的键在 `modifiers_documentation.md` 中存在。
- [ ] `decision_category` 指向的决议分类存在（否则滑条不显示）。
- [ ] bop id / side id / 分类 id 都有本地化（否则界面空白）。
- [ ] `add_power_balance_modifier.modifier` 用的是静态修正 ID。
- [ ] `on_activate`/`on_deactivate` 里别写重 effect（每次过区间都跑）。

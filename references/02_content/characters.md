---
title: 角色系统（Characters：领袖 / 顾问 / 将领 / 科学家）
domain: 02_content
scope: country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/characters/_documentation.md
  - common/characters/GER.txt
  - common/country_leader/00_traits.txt
  - common/unit_leader/00_traits.txt
  - common/scientist_traits/_documentation.md
  - documentation/effects_documentation.md
---

# 角色系统（Characters）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/characters/`（原版平铺，一个 tag 一个文件：`GER.txt`、`SWE.txt`、`SOV.txt`…） |
| 顶层结构 | `characters = { <角色 token> = { ... } }`（`common/characters/_documentation.md:3-8`） |
| 角色 token | 全局唯一，惯例 `TAG_名_姓`（`GER_otto_strasser`），建议 mod 用 `HHO_` 前缀 |
| 读取时机 | 启动建库；改文件需重启 |
| 覆盖语义 | 同 token 后者覆盖（可用于换肖像/加角色）；同名文件整体替换 |
| 本地化 | 角色名 = 角色 token（`name = GER_adolf_hitler` 就是让引擎读 key `GER_adolf_hitler`）；特质 = 特质 token |

原版必读：

- `common/characters/_documentation.md`（48 行）——**官方 1.19 说明**：`characters` 根、`can_be_captured`、`scientist` 角色。
- `common/characters/GER.txt:15-28` —— 国家领袖（`country_leader`）。
- `common/characters/GER.txt:121-143` —— 元帅（`field_marshal`，含 `visible`）。
- `common/characters/GER.txt:263-284` —— 理论家顾问（`advisor` + `slot = theorist` + `idea_token` + `ledger`）。
- `common/characters/GER.txt:1384-1392` —— 海军将领（`navy_leader` 的 skill 体系与 `legacy_id`）。
- `common/characters/GER.txt:62-78` —— 政治顾问 + `visible` 条件（靠国策解锁）。

**官方文档位置（1.19.4.2 实测）**：本域唯一域级官方文档是 `common/characters/_documentation.md`（48 行，只覆盖 `characters` 根、`can_be_captured`、`scientist` 三件事）；领袖特质、将领特质、科学家特质的库各在自己的目录里，其中只有 `common/scientist_traits/_documentation.md` 有官方说明，`common/country_leader/`、`common/unit_leader/` **没有** `_documentation.md`（靠 `00_traits.txt` 实例 + `documentation/effects_documentation.md` 的 `recruit_character` 等条目）。
目录规模：233 个文件（232 个 `.txt` + 1 个 `.md`）、165,061 行，`has_dlc` 出现 1,789 次——这是原版里 DLC 门控最密集的域，抄实例时别漏 DLC 条件。
1.19.4 改动：10-28 批改 `common/characters/` 20 个文件、`common/country_leader/` 4 个文件；新增「生涯档案自定义」相关本地化与 `interface/career_profile/*.gui`（不改变角色定义字段）。

## 2. 结构（带注释）

```pdx
characters = {

	MY_character_token = {
		name = MY_character_token          # 本地化 key（通常与 token 相同）
		gender = female                    # 可选（GER.txt:38）

		portraits = {                      # 肖像：分 civilian / army 两套
			civilian = {                   # 顾问/领袖用 civilian
				large = GFX_portrait_XXX
				small = GFX_portrait_XXX_small
			}
			army = {                       # 将领用 army
				large = GFX_portrait_XXX
				small = GFX_idea_XXX        # 原版常有小图用 idea 图标的情况（GER.txt:126）
			}
		}

		can_be_captured = no               # 可选，默认 yes（_documentation.md:17-25）

		# ===== 角色一：国家领袖 =====
		country_leader = {
			ideology = nazism             # 必须是 common/ideologies 里存在的意识形态
			traits = { MY_leader_trait }  # 领袖特质（common/country_leader/00_traits.txt）
			expire = "1965.1.1.1"         # 可选，到期时间
			id = -1                       # 原版惯例写 -1
		}

		# ===== 角色二：顾问（占一个 advisor 槽）=====
		advisor = {
			slot = political_advisor      # political_advisor / theorist / high_command / army_chief / navy_chief / air_chief
			idea_token = MY_advisor_idea  # 生效时作为理念 token（可省略/与角色 token 相同）
			ledger = army                 # 可选：army / navy / air / political ...
			cost = 150                    # 可选：雇佣政治点数
			allowed = { original_tag = SWE }
			visible = { has_completed_focus = HHO_rebuild_the_steelworks }  # 未满足=不显示
			available = { }               # 未满足=显示但灰
			traits = { MY_advisor_trait }
		}

		# ===== 角色三：陆军将领 =====
		field_marshal = {                 # 元帅；军长用 corps_commander
			traits = { old_guard thorough_planner }
			skill = 4
			attack_skill = 3
			defense_skill = 4
			planning_skill = 3
			logistics_skill = 3
			visible = { }                  # 可选，满足才出现（GER.txt:136-141）
		}

		corps_commander = {               # 军长（可带军衔/技能）
			traits = { infantry_leader }
			skill = 3
			attack_skill = 3
			defense_skill = 2
			planning_skill = 2
			logistics_skill = 2
		}

		navy_leader = {
			traits = { navy_career_officer seawolf }
			skill = 5
			attack_skill = 5
			defense_skill = 3
			maneuvering_skill = 3
			coordination_skill = 5
			legacy_id = 26                 # 原版内部 id（GER.txt:1391），新角色不必写
		}

		# ===== 角色四：科学家（特殊项目用，1.15+ 新增，文档见下）=====
		scientist = {
			desc = MY_scientist_desc
			traits = { MY_scientist_trait }
			skills = {
				specialization_land = 2    # 按专精覆盖等级（默认 1）
			}
			visible = { }                  # 国家/角色作用域触发器
		}
	}
}
```

> `scientist` 块完全来自 `common/characters/_documentation.md:27-46`（1.19.4.2 原版文档），
> 特质库在 `common/scientist_traits/00_traits.txt`，写法见 `common/scientist_traits/_documentation.md`：
> `modifier = { special_project_prototype_speed_factor = 0.5 }`、`specialization = { specialization_land }`、`available = { ... }`。

## 3. 角色怎么「出现」：招募与授予

角色定义在 `common/characters/` 只是**建库**，还要「招募/授予角色」才会进游戏：

```pdx
# ① 国家历史里招募（原版标准做法，history/countries/GER - Germany.txt:886-904）
recruit_character = GER_konrad_adenauer

# ② 运行时招募（effect，documentation/effects_documentation.md:5696-5707）
recruit_character = HHO_my_advisor

# ③ 动态加一个顾问角色（甚至是原版角色，用于「换人」）
add_advisor_role = {
	character = HHO_my_advisor
	advisor = {
		slot = political_advisor
		cost = 150
		idea_token = HHO_my_advisor_idea
		traits = { MY_advisor_trait }
		allowed = { original_tag = SWE }
	}
	activate = yes        # 直接雇佣（否则只是出现在可选列表）
}

# ④ 动态加元帅角色（effects_documentation.md:1367-1384）
add_field_marshal_role = {
	character = HHO_my_general
	traits = { old_guard }
	skill = 4
	attack_skill = 2
	defense_skill = 3
	planning_skill = 3
	logistics_skill = 5
}

# ⑤ 让角色成为执政党领袖/国家领袖（effects_documentation.md:5149-5170）
promote_character = HHO_my_leader
promote_character = {
	character = HHO_my_leader
	ideology = conservatism
}

# ⑥ 退役/降级/换国籍（events/Germany.txt:70-85 用过 demote_leader + set_nationality）
retire_character = HHO_my_advisor
demote_leader = yes                 # 在角色作用域内（THIS = CHARACTER）
set_nationality = GER
retire_country_leader = GER
```

### 特质的定义位置

| 类型 | 目录 | 根块 |
|---|---|---|
| 领袖特质 | `common/country_leader/00_traits.txt` | `leader_traits = { <trait> = { ... } }`（第 44 行起，含 `random = no`、修正、`ai_will_do`、`sprite`） |
| 将领特质 | `common/unit_leader/00_traits.txt`（另有 `_skills.txt`、`NSB_traits.txt` 等） | 相关 `_traits` 块 |
| 科学家特质 | `common/scientist_traits/00_traits.txt` | `_documentation.md` 给出完整语法 |

```pdx
# common/country_leader/00_traits.txt 风格（第 46-55 行）
leader_traits = {
	HHO_steel_magnate = {
		random = no
		political_power_factor = 0.05
		industrial_capacity_factory = 0.05
		ai_will_do = { factor = 1 }
	}
}
```

## 4. 最小可跑完整示例

文件：`common/characters/HHO_characters.txt`

```pdx
characters = {

	# --- 政治顾问：用原版已存在的瑞典肖像 sprite（interface/_leader_portraits.gfx:6847）---
	HHO_lars_ekstrom = {
		name = HHO_lars_ekstrom
		portraits = {
			civilian = {
				large = GFX_portrait_SWE_per_albin_hansson
			}
		}
		advisor = {
			slot = political_advisor
			idea_token = HHO_lars_ekstrom
			ledger = political
			cost = 150
			allowed = { original_tag = SWE }
			visible = {
				has_completed_focus = HHO_rebuild_the_steelworks
			}
			available = {
				has_political_power > 150
			}
			traits = { HHO_steel_magnate }
		}
	}

	# --- 军长：需要肖像（army 套）---
	HHO_ingvar_berg = {
		name = HHO_ingvar_berg
		portraits = {
			army = {
				large = GFX_portrait_SWE_sven_olov_lindholm
			}
		}
		corps_commander = {
			traits = { infantry_leader }
			skill = 3
			attack_skill = 3
			defense_skill = 2
			planning_skill = 2
			logistics_skill = 2
		}
	}

	# --- 国家领袖（替换/备用）---
	HHO_gustaf_adolf_reformer = {
		name = HHO_gustaf_adolf_reformer
		portraits = {
			civilian = {
				large = GFX_portrait_SWE_per_albin_hansson
			}
		}
		country_leader = {
			ideology = conservatism
			traits = { HHO_steel_magnate }
			expire = "1965.1.1.1"
			id = -1
		}
	}

	# --- 科学家（特殊项目用）---
	HHO_elin_strid = {
		name = HHO_elin_strid
		portraits = {
			civilian = {
				large = GFX_portrait_SWE_lise_meitner
			}
		}
		scientist = {
			desc = HHO_elin_strid_desc
			traits = { HHO_scientist_metallurgy }
			skills = {
				specialization_land = 2
			}
		}
	}
}
```

### 需要的本地化（`localisation/english/HHO_characters_l_english.yml`）

```yml
l_english:
 HHO_lars_ekstrom:0 "Lars Ekström"
 HHO_ingvar_berg:0 "Ingvar Berg"
 HHO_gustaf_adolf_reformer:0 "Gustaf Adolf"
 HHO_elin_strid:0 "Elin Strid"
 HHO_elin_strid_desc:0 "A metallurgist with an interest in armour plating."
 HHO_steel_magnate:0 "Steel Magnate"
 HHO_steel_magnate_desc:0 "Industry listens when he speaks."
 HHO_scientist_metallurgy:0 "Metallurgist"
 HHO_scientist_metallurgy_desc:0 "Specialises in metallurgy."
```

> 肖像 sprite 可以直接复用原版已存在的（本机 `interface/_leader_portraits.gfx:6847-6892` 有 `GFX_portrait_SWE_per_albin_hansson`、
> `GFX_portrait_SWE_sven_olov_lindholm` 等；`interface/_scientists_portraits.gfx:411` 有 `GFX_portrait_SWE_lise_meitner`）。
> 自绘肖像的尺寸/风格规范见 [05_presentation/portraits-flags.md](../05_presentation/portraits-flags.md)。

## 5. 新增 vs 覆盖

- **推荐**：新文件 `common/characters/HHO_characters.txt`，新 token；历史里 `recruit_character`。
- 「给原版国家补一个顾问」：新 token + 在 `history/countries/<TAG> - <Name>.txt` 里 `recruit_character`（但那要覆盖历史文件，见 [history-countries.md](history-countries.md) 的风险说明）。
  更安全：用国策/事件里的 `add_advisor_role = { ... }` 动态加。
- 覆盖原版角色（换肖像/加特质）：在新文件里重定义同 token 的完整块 —— 但会丢掉未写的字段，必须整块抄。

## 6. 1.19 相关注意

- `scientist` 角色是特殊项目系统的配套（1.15+；本机 `common/characters/_documentation.md` 明确列出），
  老教程里顾问 `slot = theorist` 的「理论家」现在与「科学家」是两套东西（`common/characters/GER.txt:4060` 有 "Old Theorist role -> Now Scientist" 注释）。
- `can_be_captured = no`：新字段（`_documentation.md:17-25`），有 `country_leader` 角色的角色永远不可被俘。
- 领袖 `id = -1` + `expire` 是 1.19 原版常规写法（`GER.txt:22-27`）。
- `legacy_id`（`navy_leader`）是原版内部 id，模组新增将领不需要写。

## 7. 常见错误 / 自检清单

- [ ] 文件外层是 `characters = { ... }`。
- [ ] 角色 token 有本地化；`name = <token>` 指向的 key 存在。
- [ ] `advisor.slot` 只用 `political_advisor` / `theorist` / `high_command` / `army_chief` / `navy_chief` / `air_chief`（原版用例见 §1）。
- [ ] 用到的 trait 已在对应 DB 定义（`common/country_leader/`、`common/unit_leader/`、`common/scientist_traits/`），且每个 trait 有本地化。
- [ ] 肖像 `GFX_portrait_*` 真实存在；`army` 套用于将领、`civilian` 套用于顾问/领袖。
- [ ] 角色「没出现」时先查：是否被招募（`recruit_character`）、`visible`/`available` 是否满足、`allowed` 是否放行。
- [ ] `ideology = xxx` 必须是 `common/ideologies/` 里存在的意识形态 token（写错=领袖不生效）。
- [ ] `promote_character` 在角色有多个领袖角色时必须给 `ideology`（文档明确要求）。
- [ ] 替换原版角色时整块复制，只改需要的行。

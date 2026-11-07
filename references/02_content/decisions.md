---
title: 决议与任务（Decisions & Missions）
domain: 02_content
scope: country / state
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/decisions/_documentation.md
  - common/decisions/AST.txt
  - common/decisions/AFG.txt
  - common/decisions/BRA.txt
  - common/decisions/GER.txt
  - localisation/english/TAOG_decisions_l_english.yml
---

# 决议与任务（Decisions & Missions）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/decisions/`（原版平铺，文件名多为 `TAG.txt` 或 `TAG_decisions.txt`） |
| 顶层结构 | **每个顶层块就是一个「决议分类」**；**不要**写 `decisions = { ... }` 这种包裹层（我对整个 `common/decisions/` 用 grep 搜「以 `decisions =` 开头的行」，零命中，1.19.4.2） |
| 读取时机 | 启动建触发器；`allowed` 每局只检查一次，`visible`/`available` 每帧刷新 UI 时检查（见 §2 引用） |
| 覆盖语义 | 同 ID 后者覆盖；同名文件整体替换 |
| 本地化 | 分类：`<cat_id>`、`<cat_id>_desc`、`<cat_id>_name`（targeted 分类的提示语）；决议：`<decision_id>`、`<decision_id>_desc`。证据 `localisation/english/TAOG_decisions_l_english.yml:655-669` |

原版必读：

- `common/decisions/_documentation.md`（46 行）——**最重要**，定义 `allowed/visible/available/target_root_trigger/target_trigger/state_trigger` 各自的检查频率与作用域。
- `common/decisions/AST.txt:1-42` —— 最小分类 + 带 `days_remove`/`modifier`/`remove_effect` 的决议。
- `common/decisions/AST.txt:2775-2830` —— `highlight_states` 的状态高亮写法。
- `common/decisions/AFG.txt:479-500,748,1723` —— `targets = { 州ID... }`、`target_trigger`、`custom_cost_text` 的真实组合。
- `common/decisions/GER.txt:90-110` —— 「任务型」决议（`days_mission_timeout`、`is_good`、`fire_only_once`）。

**官方文档位置（1.19.4.2 实测）**：`common/decisions/_documentation.md` 是本域**唯一**的域级官方文档（46 行，只讲触发器检查频率与作用域，不讲字段全集）；字段写法靠 vanilla 实例。
目录规模：`common/decisions/*.txt` 89 个 + `common/decisions/categories/*.txt` 57 个（**分类可以放在 `categories/` 子目录**，原版就这么分），全域 147 个文件、345,066 行。
1.19.4 只做内容改动：10-28 批改 39 个决议文件、10-29 批再改 13 个；`formable_nation_decisions.txt` 里新增了一批可成立国家（TAJ、samanid_empire、USA_CSA 等，配套 `common/countries/cosmetic.txt`）。

## 2. 检查频率与作用域（`common/decisions/_documentation.md` 摘要）

| 触发器 | 检查频率 | 作用域 | 用途 |
|---|---|---|---|
| `allowed` | **每局一次**（读档时） | THIS = 国家 | 过滤「这个国家永远不会看到」的决议（性能关键） |
| `visible` | 每次 UI 刷新（每帧级） | THIS = 国家；targeted 时 FROM = 目标国家/州 | 决定是否出现在列表（可以灰） |
| `available` | 每次 UI 刷新 | 同上 | 决定「现在能不能点」 |
| `target_root_trigger` | 每天一次（24 个整点之一） | THIS = 国家 | targeted 决议的「预筛选」，只写发起国自身条件 |
| `target_trigger` | 每天一次，对每个国家/州 | THIS = 国家，FROM = 目标 | 决定这条 targeted 决议命中哪些目标（每个命中生成一条） |
| `state_trigger` | — | — | `yes`/`no`/`any`/`any_owned_state`/`any_controlled_state`/`continent_key`；不写 `targets` 时用它来限定州范围 |

> 原文要点：`target_root_trigger` 与 `target_trigger` 都应该是 `visible` 的**子集**，目的是把「每帧 × 全世界国家」的开销降到「每天一次」。targeted 决议滥用 `state_trigger = any` 是经典卡顿来源（文档明确 "To be avoided whenever possible"）。

## 3. 结构（带注释）

```pdx
# ===== 顶层：一个分类 =====
MY_category = {                      # 分类 ID；本地化 MY_category / _desc / _name

	MY_decision_one = {              # 决议 ID

		icon = GFX_decision_eng_install_government   # sprite（decisions.gfx 里有定义）
		# 也可写成 icon = eng_blackshirt_march（原版 AST.txt:4 的旧式写法）

		# ---- 三个触发器 ----
		allowed = { original_tag = SWE }          # 每局一次
		visible = { has_political_power > 0 }     # 每帧
		available = { has_political_power > 50 }  # 每帧

		# ---- 代价 ----
		cost = 50                       # 政治点数（默认货币是 PP）
		# cost_cooldown = 30            # ⚠️ 本机未确认，别写
		custom_cost_text = MY_cost_tt    # 自定义代价显示（本地化 key），与实际扣费无关
		# days_remove = 25             # 激活后 N 天自动移除
		# days_re_enable = 70          # 移除后 N 天才能再点
		# fire_only_once = yes         # 只能点一次（AST.txt:56 等 50+ 处）
		# days_mission_timeout = 180   # 「任务」型：N 天内完不成会失败（GER.txt:107）
		# is_good = no                 # 任务型：失败是否算「坏事」（GER.txt:108）
		# activation = { ... }         # 任务型：自动激活条件（AST.txt:58-60）

		# ---- 持续效果 ----
		modifier = {                     # 决议「进行中」生效的国家修正（AST.txt:31-33）
			civilian_factory_use = 1
		}
		# state_modifier = { ... }       # ⚠️ 州级持续修正在 1.19 未在本机决议文件中确认

		cancel_trigger = { ... }         # 进行中被取消的条件（AST.txt:27-29）
		ai_will_do = { factor = 10 }     # AI 权重（AST.txt:35-37）

		# ---- 效果 ----
		complete_effect = {              # 点击成功时
			add_stability = 0.02
			country_event = { id = hho.2 days = 2 }
		}
		remove_effect = {                # 被移除/到期时
			add_ideas = HHO_free_trade_steel
		}
	}

	# ---------- targeted（针对国家/州）决议 ----------
	MY_targeted_decision = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		targets = { NOR DEN FIN }        # 目标国家列表（AFG.txt:479 用州 ID 列表）
		target_root_trigger = {          # 每天一次，仅发起国条件
			has_war = no
		}
		target_trigger = {               # 每天一次，FROM = 目标国家
			NOT = { is_in_faction_with = ROOT }
			has_opinion = { target = ROOT value < 50 }
		}
		visible = {
			has_political_power > 100
			NOT = { is_in_faction_with = FROM }
		}
		available = { has_political_power > 100 }
		cost = 100
		complete_effect = {
			FROM = { add_opinion_modifier = { target = ROOT modifier = HHO_trade_deal } }
			add_political_power = -10
		}
	}

	# ---------- 州级 targeted（高亮地图） ----------
	MY_state_decision = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		state_trigger = any_owned_state   # 只对「本国拥有的州」逐个跑 target_trigger
		target_trigger = {
			free_building_slots = { building = industrial_complex size > 0 }
		}
		highlight_states = {              # 让地图上的目标州闪光（AST.txt:2790-2796）
			highlight_state_targets = {
				state = 634
			}
		}
		visible = { has_political_power > 75 }
		available = { has_political_power > 75 }
		cost = 75
		complete_effect = {
			add_extra_state_shared_building_slots = 1   # THIS = 州（targeted 决议里 THIS 会变成目标）
		}
	}
}
```

> **作用域提醒**：targeted 决议的 `complete_effect` 里，`THIS` 是**目标**（州或国家），发起国要用 `ROOT`。普通决议里 `THIS` 才是发起国。这是 1.19 里最常写错的一点。

## 4. 最小可跑完整示例（决策 + 任务）

文件：`common/decisions/HHO_decisions.txt`

```pdx
HHO_steel_policy_category = {

	HHO_steel_export_drive = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		visible = {
			has_completed_focus = HHO_rebuild_the_steelworks
		}
		available = {
			has_political_power > 50
			NOT = { has_idea = HHO_free_trade_steel }
		}
		cost = 50
		fire_only_once = yes
		ai_will_do = { factor = 20 }
		complete_effect = {
			add_ideas = HHO_free_trade_steel
			add_political_power = -10
			country_event = { id = hho.2 days = 1 }
		}
	}

	HHO_steel_austerity = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		visible = { has_completed_focus = HHO_rebuild_the_steelworks }
		available = {
			has_political_power > 50
			NOT = { has_idea = HHO_autarkic_steel }
			NOT = { has_idea = HHO_free_trade_steel }
		}
		cost = 50
		fire_only_once = yes
		remove_effect = {
			add_stability = -0.02
		}
		complete_effect = {
			add_ideas = HHO_autarkic_steel
			add_stability = 0.05
		}
	}

	# 州级 targeted：给本国一个空建筑槽的州加槽
	HHO_build_steel_district = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		state_trigger = any_owned_state
		target_trigger = {
			free_building_slots = {
				building = industrial_complex
				size > 0
			}
		}
		visible = {
			has_political_power > 75
			has_completed_focus = HHO_rebuild_the_steelworks
		}
		available = { has_political_power > 75 }
		cost = 75
		days_re_enable = 90
		ai_will_do = { factor = 10 }
		complete_effect = {
			add_extra_state_shared_building_slots = 1
		}
	}

	# 「任务」型：180 天内完成，否则失败
	HHO_steel_quota_mission = {
		icon = GFX_decision_eng_install_government
		allowed = { original_tag = SWE }
		visible = { has_completed_focus = HHO_rebuild_the_steelworks }
		available = { has_war = no }
		cost = 25
		days_mission_timeout = 180
		is_good = yes
		fire_only_once = yes
		ai_will_do = { factor = 5 }
		complete_effect = {
			add_stability = 0.03
		}
		remove_effect = {
			add_stability = -0.03
		}
	}
}
```

若要让任务在满足条件时自动开启，用 effect `activate_mission = HHO_steel_quota_mission`（`documentation/effects_documentation.md:661-669`），
原版在 `history/countries/GER - Germany.txt:883` 就用了 `activate_mission = GER_mefo_bills_mission`。

### 需要的本地化（`localisation/english/HHO_decisions_l_english.yml`）

```yml
l_english:
 HHO_steel_policy_category:0 "Steel Policy"
 HHO_steel_policy_category_desc:0 "Decisions about where Swedish steel goes."
 HHO_steel_export_drive:0 "Steel Export Drive"
 HHO_steel_export_drive_desc:0 "Open long-term export contracts."
 HHO_steel_austerity:0 "Steel Austerity"
 HHO_steel_austerity_desc:0 "Keep the ore at home."
 HHO_build_steel_district:0 "Build a Steel District"
 HHO_build_steel_district_desc:0 "Add a building slot to a state."
 HHO_steel_quota_mission:0 "Meet the Steel Quota"
 HHO_steel_quota_mission_desc:0 "Produce enough steel within 180 days."
```

## 5. 新增 vs 覆盖

- **推荐**：新建 `common/decisions/HHO_decisions.txt`，新分类 + 新 ID；`allowed` 限 `original_tag = SWE`。
- 想加「原版分类里的新决议」：在自己的新文件里**重开**一次同名分类块是危险操作（同名分类后加载者可能整体覆盖原分类）。安全做法：
  要么新建分类，要么在**完全一致**的分类 ID 下补决议并接受「整块替换」的风险（一定要在 README 写明）。
- 同名文件替换 `common/decisions/GER.txt`（22,869 行）→ 禁止。

## 6. 1.19 相关注意

- **没有 `decisions = { }` 包裹层**：1.19.4.2 原版所有决议文件的顶层都是分类块。网上旧教程的 `decisions = { category = { decision = {} } }` 写法在这里找不到对应实现，别抄。
- `icon` 两种写法并存：`icon = eng_blackshirt_march`（无前缀，AST.txt:4）与 `icon = GFX_decision_eng_install_government`（有前缀，AST.txt:2777）。
- 分类可以有 `_name` 本地化，用于 targeted 决议的「选择目标」提示（`TAOG_decisions_l_english.yml:657`，`AST_union_control_1_cat_name`）。
- 权力平衡系统会通过 `decision_category = <你的分类>` 把 bop 数值挂到决策界面上（见 [balance-of-power.md](balance-of-power.md)）。

## 6.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Decision_modding）

**AI 默认永不选择决议**——不写 `ai_will_do = { ... }` 的话 AI 一辈子不碰它（MTTH 格式：`base` + `modifier` 的 add/factor）。这是「我写的决议 AI 从来不用」的头号原因。

**任务的 `available` 默认恒为 true**——不写的话任务一出现就瞬间完成。任务（`days_mission_timeout` 型）的可见性用 `activation = { ... }`（每日检查），`visible` 对任务无效。

**`allowed` 只在开局和读档时检查一次**——运行时不会变 true（国家/DLC 限制放这里，别放 `visible`）。

**自定义消耗不实际扣任何东西**——`custom_cost_trigger` 只负责显示与判定，政治点/指挥点要自己在 `complete_effect`（建议 `hidden_effect` 包住）里手动扣。AI 也不会为它攒资源，除非设 `ai_hint_pp_cost`（须为常量）。

**targeted decision 的 FROM 语义与直觉相反**：ROOT = 执行国，**FROM = 决议目标**。三个目标来源任一出现即为 targeted：`targets`（显式列表，可加 `targets_dynamic = yes`）、`target_array`、`target_trigger`——注意**只写了 `target_root_trigger` 也会使决议变成 targeted**（它每日只查 ROOT，性能比 target_trigger 好）。`fire_only_once` 对 targeted 是**每个目标各一次**。开战预警用 `war_with_target_on_complete/remove/timeout = yes`（普通决议的 `war_with_on_*` 对 targeted 无效）。

**任务的兄弟属性**：`days_mission_timeout = -1` 表示永不因超时移除；`remove_trigger` 满足时提前触发 `remove_effect`；`cancel_if_not_visible = yes` 在不可见时取消计时器（不执行 remove_effect，回滚放 `cancel_effect`）。

**随机种子陷阱**：决议默认 `fixed_random_seed = yes`——`random_list` 每次执行结果相同；需要真随机时显式设 `fixed_random_seed = no`。

## 7. 常见错误 / 自检清单

- [ ] 文件顶层直接是 `<category_id> = { ... }`，没有多包一层的 `decisions = { ... }` 壳。
- [ ] 想让 AI 用它？每条决议都有 `ai_will_do`；任务型还要写 `available`（默认恒 true，不写就瞬间完成）。
- [ ] 每条决议的 `allowed` 限定了国家（否则所有国家都能看到，UI 会很乱，且性能差）。
- [ ] targeted 决议同时写了 `target_root_trigger`（发起国）与 `target_trigger`（目标）；`visible` 能覆盖二者。
- [ ] targeted 决议的 `complete_effect` 里用 `ROOT` 指发起国、`THIS` 指目标。
- [ ] `state_trigger` 用 `any_owned_state` / `any_controlled_state`，不要随手 `any`。
- [ ] `icon` 是真实 sprite（`interface/decisions.gfx` 或自建 `.gfx`）。
- [ ] `custom_cost_text` 指向的本地化 key 存在（且与真实 `cost` 一致，否则玩家觉得被骗）。
- [ ] 任务型：`days_mission_timeout` + `is_good` + `remove_effect` 三件套齐全，否则失败时什么都不发生。
- [ ] 分类与决议各两条本地化（`<id>`、`<id>_desc`），分类再加 `_name`。
- [ ] `visible`/`available` 里不要把「永远不可能满足」的条件写进 `available`（原版文档明确警告，例如要求一个已被锁死的国策）。

---
title: 理念 / 国家精神 / 法律（Ideas）
domain: 02_content
scope: country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/ideas/GER.txt
  - common/ideas/_economic.txt
  - common/idea_tags/00_idea.txt
  - localisation/english/ideas_l_english.yml
  - interface/ideas.gfx
---

# 理念 / 国家精神 / 法律（Ideas）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/ideas/`（原版平铺：`GER.txt`、`_economic.txt`、`_event.txt`、`army_spirits.txt`、`SOV.txt`…） |
| 顶层结构 | `ideas = { <分类> = { <理念> = { ... } } }`（`common/ideas/GER.txt:1-3`、`_economic.txt:1-3`） |
| 分类来自哪 | 分类与「槽位」在 `common/idea_tags/00_idea.txt` 的 `idea_categories = { ... }` 里定义（`country`、`economy`、`government`、`hidden_ideas`…） |
| 读取时机 | 启动建库；改文件需重启 |
| 覆盖语义 | 同 ID 后者覆盖（可用新文件覆盖单条原版理念）；同名文件整体替换 |
| 本地化 | `<idea_id>` + `<idea_id>_desc`（证据 `localisation/english/ideas_l_english.yml:12-13` 的 `sour_loser` / `sour_loser_desc`） |
| 图标 | `picture = xxx` → 引擎找 sprite `GFX_idea_xxx`（证据 `interface/ideas.gfx:134-135`：`can_wartime_prices_and_trade_board` → `GFX_idea_can_wartime_prices_and_trade_board`） |

原版必读：

- `common/ideas/GER.txt:1-90` —— `country` 分类、`allowed`/`allowed_civil_war`/`removal_cost`/`modifier`/`rule`/`research_bonus`/`picture` 全套。
- `common/ideas/_economic.txt:1-141` —— 法律型分类（`law = yes`、`use_list_view = yes`）、`allowed_to_remove`、`cancel_if_invalid`、`default = yes`、`on_add`。
- `common/idea_tags/00_idea.txt:1-40` —— 分类与槽位（`slot = mobilization_laws`、`character_slot = political_advisor`、`ledger = civilian`、`cost = 150`）。
- `localisation/english/ideas_l_english.yml` —— 最标准的理念本地化样板。

**官方文档位置（1.19.4.2 实测）**：`common/ideas/` **没有** `_documentation.md`（213 个 `.txt`，0 个 `.md`），是 all-content 域里体量最大、文档最少的之一（151,368 行）。字段事实来源只有两个：
`common/ideas/GER.txt` / `_economic.txt` 等 vanilla 实例；`common/idea_tags/00_idea.txt` 的 `idea_categories`（分类、槽位、`cost` 的定义处）。
1.19.4 改动集中在内容：10-28 批改 24 个理念文件、10-29 批新增 `common/ideas/indonesia.txt`（TAOG 配套）。若你覆盖原版理念 ID，换小版本后需重新 diff 文件。

## 2. 结构（带注释）

```pdx
ideas = {

	# ===== 分类 A：国家精神（无槽位限制，可无限叠加）=====
	country = {                         # 分类 ID 必须已在 common/idea_tags 定义
		MY_spirit_one = {               # 理念 ID

			allowed = {                 # 该理念「属于谁」（自动添加/校验时用）
				original_tag = SWE
			}
			allowed_civil_war = {       # 内战双方是否都保留（GER.txt:10-12）
				always = yes
			}
			allowed_to_remove = {       # 是否可以手动移除（不写=不可移除）
				has_war = no
			}
			removal_cost = -1           # -1 = 不可移除（GER.txt:14）；>0 = 移除消耗 PP

			picture = can_wartime_prices_and_trade_board   # → GFX_idea_can_wartime_prices_and_trade_board
			# 民族精神图标也可用 generic_air_bonus / autarkic_economy 等已存在 sprite

			modifier = {                # 修正，键名必须在 modifiers_documentation.md 里
				industrial_capacity_factory = 0.1
				stability_factor = 0.05
			}

			research_bonus = {          # 研究加速（归类目名，GER.txt:87-90）
				industry = 0.10
			}

			rule = {                    # 特殊规则（GER.txt:19-21）
				can_create_factions = yes
			}

			on_add = {                  # 添加时执行（国家作用域，_economic.txt:122）
				add_political_power = 10
			}
			on_remove = {               # 移除时执行（_economic.txt:1177）
				add_stability = -0.02
			}
		}
	}

	# ===== 分类 B：法律（占槽位，同一槽位同时只能有一个）=====
	economy = {                         # 注意：分类参数（law/use_list_view）写在这里
		law = yes
		use_list_view = yes

		MY_economy_law = {
			allowed = { always = no }   # 一般由事件/国策授予，不是任意国家可点
			allowed_to_remove = {
				has_war = yes
			}
			removal_cost = -1
			modifier = {
				consumer_goods_expected_value = 0.1
				production_speed_industrial_complex_factor = 0.1
			}
			default = yes               # 该分类的默认法律（_economic.txt:118）
			cancel_if_invalid = no
		}
	}
}
```

> 分类级参数（`law`、`use_list_view`、`slot`、`cost`、`ledger`）真正定义在 `common/idea_tags/00_idea.txt`；
> `common/ideas/` 里再写一次 `law = yes` 是原版习惯写法（`_economic.txt:4-5`），照抄即可。

### 如何给国家加/移除理念（effect）

```pdx
add_ideas = HHO_steel_boom            # 单条
add_ideas = { HHO_steel_boom HHO_trade_deal }  # 多条（GER history 里大量使用）
remove_ideas = HHO_steel_boom
swap_ideas = {                        # 原子替换（不会触发 remove/add 的中间态工具提示）
	remove_idea = HHO_free_trade_steel
	add_idea = HHO_autarkic_steel
}
has_idea = HHO_steel_boom             # trigger
```

`swap_ideas` 的原版用例：`common/bop/FIN.txt:31-35`、`:349-353`。

## 3. 最小可跑完整示例

文件：`common/ideas/HHO_ideas.txt`

```pdx
ideas = {

	country = {
		HHO_steel_boom = {
			allowed = {
				original_tag = SWE
			}
			allowed_civil_war = {
				always = yes
			}
			removal_cost = -1
			picture = autarkic_economy
			modifier = {
				industrial_capacity_factory = 0.10
				production_speed_industrial_complex_factor = 0.10
				stability_factor = 0.05
			}
			research_bonus = {
				industry = 0.05
			}
			on_add = {
				add_political_power = 10
			}
			on_remove = {
				add_stability = -0.02
			}
		}

		HHO_free_trade_steel = {
			allowed = { original_tag = SWE }
			removal_cost = 50
			allowed_to_remove = {
				has_war = yes
			}
			picture = can_wartime_prices_and_trade_board
			modifier = {
				trade_opinion_factor = 0.15
				industrial_capacity_factory = 0.05
			}
		}

		HHO_autarkic_steel = {
			allowed = { original_tag = SWE }
			removal_cost = 50
			allowed_to_remove = {
				has_war = yes
			}
			picture = can_wartime_prices_and_trade_board
			modifier = {
				consumer_goods_expected_value = 0.05
				industrial_capacity_factory = 0.10
				stability_factor = -0.02
			}
			rule = {
				can_create_factions = no
			}
		}
	}

	# 一个「事件给的临时精神」示例（带时限的写法是配合 timed effect / 决议，不是理念本身）
	country = {
		HHO_nordic_council = {
			allowed = { original_tag = SWE }
			removal_cost = -1
			picture = generic_air_bonus
			modifier = {
				research_speed_factor = 0.03
			}
		}

		# 被 technologies.md / special-projects.md 的 on_research_complete 授予
		HHO_steel_alloys_idea = {
			allowed = { original_tag = SWE }
			removal_cost = -1
			picture = autarkic_economy
			modifier = {
				industrial_capacity_factory = 0.03
			}
			on_add = {
				army_experience = 5
			}
		}
	}

	economy = {
		law = yes
		use_list_view = yes

		HHO_steel_economy = {
			allowed = { always = no }
			removal_cost = -1
			modifier = {
				consumer_goods_expected_value = 0.05
				production_speed_industrial_complex_factor = 0.15
			}
			cancel_if_invalid = no
		}
	}
}
```

### 需要的本地化（`localisation/english/HHO_ideas_l_english.yml`）

```yml
l_english:
 HHO_steel_boom:0 "Steel Boom"
 HHO_steel_boom_desc:0 "Our mills run day and night, and the treasury swells with ore money."
 HHO_free_trade_steel:0 "Free Trade in Steel"
 HHO_free_trade_steel_desc:0 "Long-term export contracts bind us to foreign buyers."
 HHO_autarkic_steel:0 "Autarkic Steel"
 HHO_autarkic_steel_desc:0 "The ore stays home. We accept higher prices for strategic independence."
 HHO_nordic_council:0 "Nordic Defense Council"
 HHO_nordic_council_desc:0 "A permanent framework of Nordic military cooperation."
 HHO_steel_alloys_idea:0 "Steel Alloys Programme"
 HHO_steel_alloys_idea_desc:0 "A national programme of metallurgical research."
 HHO_steel_economy:0 "Steel Economy"
 HHO_steel_economy_desc:0 "Everything is subordinated to steel output."
```

## 4. 与国策/事件的联动（标准模式）

| 需求 | 写法 |
|---|---|
| 国策给精神 | `completion_reward = { add_ideas = HHO_steel_boom }`（原版 `germany.txt:143` 给 `civilian_economy`） |
| 国策移除精神 | `completion_reward = { remove_ideas = sour_loser }` |
| 精神不可移除 | `removal_cost = -1`（**绝大多数国家精神都是这个**） |
| 精神可花钱撤 | `removal_cost = 50` + `allowed_to_remove = { ... }` |
| 精神只在某条件下现形 | `allowed = { ... }`（不满足时 `add_ideas` 也会失败/被清掉） |
| 理念内显示 tooltip | 在国策里用 `show_ideas_tooltip = <idea_id>`（原版 `germany.txt:176`） |

## 5. 新增 vs 覆盖

- **推荐**：新文件 `common/ideas/HHO_ideas.txt` + 新 ID。
- 想改原版理念数值：在新文件里**重定义该 idea ID**（后者覆盖），只写需要变的字段？**不行** —— 覆盖是整个 idea 块替换，未写的字段会丢。
  必须把该 idea 的完整定义抄过去（并且要在 README 注明「跟随原版 XX 版本」）。
- 同名文件替换 `common/ideas/_economic.txt`（1 814 行）→ 禁止。

## 6. 1.19 相关注意

- `on_add` / `on_remove` 确实存在且被原版大量使用（`common/ideas/_economic.txt:122/241/405/627/831/1177/1279/1380/1520/1758`），
  网上老教程说「理念没有 on_add」已经过时。
- `allowed_civil_war` 用于内战双方共享精神（`GER.txt:10-12`）。
- `rule = { ... }`（如 `can_create_factions = yes`）是 1.19 常见写法（`GER.txt:19-21`）。
- ⚠️ `equipment_bonus` 写在理念里在本机 1.19 理念文件中**未见用例**（只在科技/MIO/特殊项目里见过）；需要装备加成优先用科技/项目，别赌。

## 6.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Idea_modding）

**`on_add` / `on_remove` 开局不执行**：只有游戏开始后通过效果添加/移除才触发；写在 `history/countries/` 或选国界面 `effect = {}` 里的开局理念，这些块被忽略，需要的效果要手动复制一份。

**`picture` 会被自动加前缀**：`picture = XYZ` 实际查找的是 `GFX_idea_XYZ`。误写成 `picture = GFX_XYZ` 会去找 `GFX_idea_GFX_XYZ`——找不到 sprite 显示问号图标；texturefile 路径错则 idea **在政治界面隐形但仍然生效**（更难排查）。不写 `picture` 时默认找 `GFX_idea_<idea名>`。

**modifier 里不能用变量**——可变数值要用 dynamic modifiers（`common/dynamic_modifiers/`）。另外 `research_bonus` / `equipment_bonus` / `rule` / `targeted_modifier` 是 idea 的**独立顶层属性**，写进 `modifier = {}` 是错误用法（不生效）。

**idea 无法原地修改，只能 swap**：`swap_ideas = { remove_idea = old add_idea = new }`。数值演进用多个 idea + swap；同本地化键时表现为"升级"。

**`allowed_civil_war` 默认恒 false**——不写的话内战时精神双方都消失；`always = yes` 让双方保留。逐方评估可写条件。

**加载顺序坑**：文件按 Unicode 顺序加载（大写 < 下划线 < 小写）。理念文件名大写开头（如 `GER.txt`）会先于 `00_economy.txt` 之外的小写法律文件加载，若理念引用 `economy_cost_factor` 之类修正时法律还没加载 → error.log 报错。修法：理念文件用小写开头命名。

**cost 的默认值**：添加默认 150 政治点（`idea_tags` 里的 `cost` 决定），`removal_cost = -1` 表示不可手动移除，默认 0；`level = N` 实现跨级补差价（征兵法模式）。

**GUI 槽位上限**：政治界面每行最多 7 个槽位，超出要改 `countrypoliticsview.gui`；新增类别还要同步 `GFX_idea_categories` sprite 的帧数。

## 7. 常见错误 / 自检清单

- [ ] 文件外层有 `ideas = { ... }`，分类名是 `common/idea_tags/00_idea.txt` 里已存在的（`country`/`economy`/`government`/`hidden_ideas`…）。
- [ ] 新写一个分类前先在 `common/idea_tags/` 里定义它，否则整个块被忽略（error.log 有 unknown category）。
- [ ] 每个 idea 有 `<id>` 与 `<id>_desc`。
- [ ] `modifier` 里每个键都能在 `documentation/modifiers_documentation.md` 里 grep 到（拼错=静默忽略）。
- [ ] 国家精神用 `removal_cost = -1`；法律/顾问类才用正数。
- [ ] `picture` token 对应的 `GFX_idea_<token>` 存在。
- [ ] 用 `add_ideas` 授予前确认 `allowed` 能让该国家通过，否则加了会被自动移除。
- [ ] 移除逻辑优先用 `swap_ideas`，避免 UI 上出现「-X 然后又 +Y」的闪烁。
- [ ] 不要在理念里写 `available`/`visible`（那是决议/国策的字段），理念用 `allowed`。

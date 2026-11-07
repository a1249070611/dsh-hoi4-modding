---
title: 国家定义与初始设置（Country Tags / Countries / History / Bookmarks）
domain: 02_content
scope: country / global
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/country_tags/00_countries.txt
  - common/countries/Germany.txt
  - history/countries/GER - Germany.txt
  - common/bookmarks/the_gathering_storm.txt
  - documentation/effects_documentation.md
---

# 国家定义与初始设置

一个可玩国家由 **4 处文件**共同决定，缺一处就「不存在/不可玩/没内容」：

```text
① common/country_tags/00_countries.txt     ← 注册 tag，指向国家定义文件
② common/countries/<Name>.txt              ← 国家「着色/文化」属性（很短，6 行左右）
③ history/countries/<TAG> - <Name>.txt     ← 开局状态：首都、政治、科技、理念、OOB、角色
④ common/bookmarks/*.txt                   ← 书签（选国家界面）里的条目
   配合 history/units/<TAG>_1936.txt        ← 初始军队（OOB）
```

## 1. 文件放哪 / 命名 / 原版参考

| 文件 | 位置 | 原版参考 | 说明 |
|---|---|---|---|
| tag 注册 | `common/country_tags/00_countries.txt` | 第 1-14 行 | 一行一个：`GER = "countries/Germany.txt"` |
| 国家属性 | `common/countries/*.txt` | `Germany.txt`（6 行）、`United Kingdom.txt`（6 行） | 只有 `graphical_culture`、`graphical_culture_2d`、`color` 等 |
| 国家历史 | `history/countries/TAG - Name.txt` | `GER - Germany.txt`（1,867 行） | 开局设置，支持日期块 |
| 军队 | `history/units/*.txt` | `history/units/GER_1936.txt` | `set_oob = "GER_1936"` 引用 |
| 书签 | `common/bookmarks/*.txt` | `the_gathering_storm.txt`、`blitzkrieg.txt` | `bookmarks = { bookmark = { ... } }` |

**命名约定（实测）**：本机 `history/countries/` 共 **364** 个文件，其中 363 个严格采用 `TAG - Name.txt`，
唯一例外是 `KLT -Kalat.txt`（原文如此，空格写错也能被识别）。**照抄 `TAG - Name.txt` 最稳**。

**官方文档位置（1.19.4.2 实测）**：本域**完全没有官方文档**——`history/` 整棵树、`common/country_tags/`、`common/countries/`、`common/bookmarks/` 下都没有 `.md`（`documentation/` 的 11 篇大文档只讲 effect/trigger/modifier 等脚本本体）。所以唯一事实来源是原版实例：
`common/country_tags/00_countries.txt`（384 行）、`common/countries/*.txt`（442 个文件，每个 6 行左右）、`history/countries/*.txt`（364 个文件）、`history/units/*.txt`（609 个文件）、`common/bookmarks/{the_gathering_storm,blitzkrieg}.txt`。`set_politics`、`recruit_character`、`set_technology` 等 history 里用的 effect 查 `documentation/effects_documentation.md`。
1.19.4 改动：10-28 批改 35 个 `history/countries/` 文件、13 个 `history/states/` 文件；新增一批可成立国家（TAJ、samanid_empire、USA_CSA、CHI_warlord_PRC 等）的旗帜 + `common/countries/cosmetic.txt` + `common/names/00_names.txt` 条目。写「新国家」时这些是现成的复制源。

## 2. 结构（带注释）

### ① tag 注册

```pdx
# common/country_tags/00_countries.txt
GER = "countries/Germany.txt"      # 三位大写字母 tag（大小写敏感，国际化标准）
SWE = "countries/Sweden.txt"
HHO = "countries/HHO_Holandia.txt" # mod 新增：右边是相对 common/ 的路径
```

### ② 国家属性（`common/countries/HHO_Holandia.txt`）

```pdx
#use_legacy_ai_pp_spend = yes         # 可选（原版 Germany.txt:1 被注释掉）
graphical_culture = western_european_gfx      # 3D 模型/单位外观组
graphical_culture_2d = western_european_2d    # 2D 界面风格组
color = { 106 119 89 }               # 地图颜色 RGB（0-255）
```

### ③ 国家历史（`history/countries/HHO - Holandia.txt`）

```pdx
capital = 64                          # 首都州 ID

# ---- 军队（OOB）----（GER.txt:4-17 用 if/else 按 DLC 选不同 OOB）
set_oob = "HHO_1936"

# ---- 特殊项目初始突破点（GER.txt:19-32）----
add_breakthrough_progress = {
	specialization = specialization_land
	value = 1.0
}

# ---- 学说（1.19：common/doctrines 的 grand doctrine id，GER.txt:34-36）----
set_grand_doctrine = new_mobile_warfare

# ---- 已研究科技 ----
set_technology = {
	infantry_weapons = 1
	infantry_weapons1 = 1
}

# ---- 数值 ----
set_research_slots = 4                # 研究槽（GER.txt:425）
set_convoys = 200                     # 运输船（GER.txt:426）
set_stability = 0.7                   # 稳定度 0-1（GER.txt:431-434）
set_war_support = 0.3                 # 战争支持度 0-1（GER.txt:436）

# ---- 政治 ----
set_politics = {                      # GER.txt:856-861
	ruling_party = conservatism        # 意识形态 token（common/ideologies）
	last_election = "1933.3.5"
	election_frequency = 48            # 月
	elections_allowed = no
}
set_popularities = {                  # GER.txt:862-867，总和 100
	democratic = 35
	fascism = 40
	communism = 10
	neutrality = 15
}

# ---- 阵营（1.19 新写法，GER.txt:871-872）----
create_faction_from_template = faction_template_axis
add_to_faction = GER

# ---- 理念（法律 + 国家精神，GER.txt:875-880）----
add_ideas = {
	limited_exports
	limited_conscription
	HHO_steel_boom
}

# ---- 角色招募（GER.txt:886-904）----
recruit_character = HHO_lars_ekstrom

# ---- 变量初始化（GER.txt:421）----
set_variable = { HHO_steel_counter = 0 }

# ---- 日期块：只对某个开局日期生效（GER.txt:440 起的 1939.1.1 = { ... }）----
1939.1.1 = {
	add_political_power = 1000
	set_research_slots = 5
	add_ideas = { war_economy }
}
```

### ④ 书签（`common/bookmarks/HHO_bookmark.txt`）

```pdx
bookmarks = {
	bookmark = {
		name = "HHO_BOOKMARK_NAME"        # 本地化
		desc = "HHO_BOOKMARK_DESC"
		date = 1936.1.1.12               # 开局时间（含小时）
		picture = "GFX_select_date_1936" # 选日期背景图
		default_country = "GER"          # 默认选中
		default = yes                    # 是否默认书签
		filters = { new_content continent }

		"HHO" = {                        # 书签里列出的可玩国家
			history = "HHO_HISTORY_DESC" # 该国家在书签里的简介
			ideology = conservatism
			version = base_game          # 按版本区分条目（可选）
			available = { always = yes } # 可选
			ideas = { HHO_steel_boom }   # 可选：显示用的初始理念
			focuses = { HHO_rebuild_the_steelworks } # 可选：显示用的国策进度
		}
	}
}
```

原版完整字段见 `common/bookmarks/the_gathering_storm.txt:1-55`（含 `required_dlc`、`sort_unplayed_first`、`apply_filter_to_majors` 等注释说明）。

## 3. 最小可跑完整示例（新增可玩国家 HHO）

> 建议别新造国家，先用原版国家（如 SWE）做内容；确实要新国家时按下面 4 步。

**① `common/country_tags/00_countries.txt`**（新文件，如 `common/country_tags/HHO_tags.txt`，避免覆盖原文件）

```pdx
HHO = "countries/HHO_Holandia.txt"
```

**② `common/countries/HHO_Holandia.txt`**

```pdx
graphical_culture = western_european_gfx
graphical_culture_2d = western_european_2d
color = { 106 119 89 }
```

**③ `history/countries/HHO - Holandia.txt`**

```pdx
capital = 64

set_oob = "HHO_1936"

set_technology = {
	infantry_weapons = 1
	infantry_weapons1 = 1
}

set_research_slots = 3
set_stability = 0.6
set_war_support = 0.2

set_politics = {
	ruling_party = conservatism
	last_election = "1932.5.1"
	election_frequency = 48
	elections_allowed = yes
}
set_popularities = {
	democratic = 55
	fascism = 20
	communism = 15
	neutrality = 10
}

add_ideas = {
	HHO_steel_boom
}

recruit_character = HHO_gustaf_adolf_reformer
recruit_character = HHO_lars_ekstrom

set_variable = { HHO_steel_counter = 0 }
```

**④ `history/units/HHO_1936.txt`**（OOB：初始军队，格式与原版 `history/units/GER_1936.txt` 一致）

```pdx
# 最小 OOB：一个步兵团 + 一个首都守备（具体语法见 03_military/division-templates.md）
division_template = {
	name = "Holandia Infantry"
	regiments = {
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
	}
	support = { }
}
units = {
	division = {
		name = "1. Holandia Division"
		location = 64
		division_template = "Holandia Infantry"
		start_experience_factor = 0.1
	}
}
```

⚠️ OOB 的 `division_template` / `units` 语法请以 `history/units/GER_1936.txt` 为准（本文件只是骨架示范，直接照抄更安全）。

**⑤ `common/bookmarks/HHO_bookmark.txt`**（若想加独立书签）

```pdx
bookmarks = {
	bookmark = {
		name = "HHO_BOOKMARK_NAME"
		desc = "HHO_BOOKMARK_DESC"
		date = 1936.1.1.12
		picture = "GFX_select_date_1936"
		default_country = "HHO"
		default = no
		filters = { new_content }

		"HHO" = {
			history = "HHO_HISTORY_DESC"
			ideology = conservatism
		}
	}
}
```

### 需要的本地化（`localisation/english/HHO_country_l_english.yml`）

```yml
l_english:
 HHO:0 "Holandia"
 HHO_DEF:0 "Holandia"
 HHO_ADJ:0 "Holandian"
 HHO_BOOKMARK_NAME:0 "A New Beginning"
 HHO_BOOKMARK_DESC:0 "A small nation with steel ambitions."
 HHO_HISTORY_DESC:0 "Holandia sits on iron and dreams of industry."
```

> 国家名三件套 `TAG`、`TAG_DEF`、`TAG_ADJ` 是 HOI4 的固定约定（可只写 `TAG` 时游戏会用 tag 原样，但界面会难看）。
> 这三个 key 的规则是本地化层约定，**必须全部存在**才不会出现 "HHO" 这样的原始字符串。

## 4. 新增 vs 覆盖（本系统风险最高）

| 做法 | 结果 | 评价 |
|---|---|---|
| 新建 `common/country_tags/HHO_tags.txt` + 新国家全部文件 | 完全隔离 | **推荐** |
| 覆盖 `common/country_tags/00_countries.txt` | 整个 tag 表被替换（数百行） | 禁止；用新文件追加 |
| 覆盖 `history/countries/GER - Germany.txt` | 德国整段 1848 行开局设置被替换 | 极不推荐 |
| 给原版国家「补一行」 | 无法追加：历史的加载是整文件替换 | 改用事件/on_actions 在开局注入（见 [01_script/on-actions.md](../01_script/on-actions.md)） |

**推荐模式（mod 加内容给原版国家）**：
不要在 history 里改，改用 `common/on_actions/` 的 `on_startup`（或 `on_daily` 首次触发）执行一次 effect 初始化：

```pdx
on_actions = {
	on_startup = {
		effect = {
			if = {
				limit = {
					NOT = { has_country_flag = HHO_initialized }
				}
				set_country_flag = HHO_initialized
				if = {
					limit = { original_tag = SWE }
					SWE = { add_ideas = HHO_steel_boom }
				}
			}
		}
	}
}
```

（`common/on_actions/00_on_actions.txt:1-40` 就是这种 `on_actions = { on_startup = { effect = { ... } } }` 结构；on_actions 的完整机制见 [01_script/on-actions.md](../01_script/on-actions.md)。）

## 5. 1.19 相关注意

- **阵营创建已换代**：`create_faction` 在文档中被标 deprecated（`documentation/effects_documentation.md:3105`），
  history 里用 `create_faction_from_template = faction_template_axis`（`GER - Germany.txt:871`）+ `add_to_faction = GER`。
- **初始学说**用 `set_grand_doctrine = <id>`（`GER - Germany.txt:34-36`），不再是科技。
- **特殊项目**的初始突破点用 `add_breakthrough_progress = { specialization = ... value = ... }`（`GER - Germany.txt:19-32`）。
- **开局任务**可用 `activate_mission = <decision_id>`（`GER - Germany.txt:883`）。
- 日期块（`1939.1.1 = { ... }`）是「同文件内多开局日期」的正规做法（`GER - Germany.txt:440`），
  比给每个开局写一个历史文件更省事。

## 6. 常见错误 / 自检清单

- [ ] `common/country_tags/` 里注册了 tag，且路径大小写与真实文件一致（Linux 服务器上大小写敏感！）。
- [ ] `history/countries/` 文件名是 `TAG - Name.txt`（`TAG` 与注册的一致）。
- [ ] `common/countries/` 里的国家文件有 `color`，否则地图上颜色异常。
- [ ] `set_politics` 的 `ruling_party` 是 `common/ideologies/` 里的意识形态 token。
- [ ] `set_popularities` 之和 = 100。
- [ ] `capital` 是**州 ID**（不是省份 ID），且该州属于你。
- [ ] `set_oob` 引用的 `history/units/<name>.txt` 存在。
- [ ] `add_ideas` / `recruit_character` 引用的 ID 都已定义（理念在 `common/ideas/`，角色在 `common/characters/`）。
- [ ] 书签里列出的国家有 `TAG`/`TAG_DEF`/`TAG_ADJ` 本地化，否则选国界面显示原始 tag。
- [ ] 新国家的国策树能拿到（树头 `country = { ... }` 命中你的 tag，见 [focus-trees.md](focus-trees.md)）。
- [ ] 在 mod 里改了原版国家的开局内容时，用 `on_actions` 注入而不是覆盖 history 文件。

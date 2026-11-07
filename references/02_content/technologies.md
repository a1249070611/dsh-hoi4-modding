---
title: 科技树与科技文件夹（Technologies）
domain: 02_content
scope: country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/technologies/infantry.txt
  - common/technologies/support.txt
  - common/technologies/NSB_armor.txt
  - common/technology_sharing/00_tech_sharing_groups.txt
  - common/technology_tags
  - documentation/effects_documentation.md
---

# 科技树与科技文件夹（Technologies）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/technologies/`（原版按领域分文件：`infantry.txt`、`support.txt`、`armor.txt`、`industry.txt`、`electronic_mechanical_engineering.txt`、`air_techs.txt`、`naval.txt`、`NSB_armor.txt`…） |
| 顶层结构 | `technologies = { <tech_id> = { ... } }`（`common/technologies/infantry.txt:1,16`） |
| tech ID | 全局唯一；原版无前缀，mod 用 `HHO_` |
| 读取时机 | 启动建库；改文件需重启 |
| 覆盖语义 | 同 ID 后者覆盖（覆盖整块！）；同名文件整体替换 |
| 校验和 | 影响 |
| 本地化 | `<tech_id>` + `<tech_id>_desc`（科技界面里的名字与说明） |

> 学说（doctrine）**不在** `common/technologies/` 里，1.19 独立在 `common/doctrines/`（`grand_doctrines/`、`subdoctrines/`、`tracks/`，见 `common/doctrines/_documentation.md`）。
> 军事侧细节见 [03_military/doctrines.md](../03_military/doctrines.md)。

原版必读：

- `common/technologies/infantry.txt:1-85` —— 文件头 `@年份` 常量 + 最小的两个科技（`enable_equipments`、`enable_equipment_modules`、`enable_subunits`、`path`、`folder`、`categories`、`ai_will_do`）。
- `common/technologies/support.txt:1146-1180` —— `dependencies`（真正的科技前置）、`enable_subunits` 里带 `limit`、`path` 多条分支、`@field_hospital_x` 常量当坐标。
- `common/technologies/NSB_armor.txt:63-97` —— `on_research_complete_limit` + `on_research_complete` 的配对用法。
- `common/technology_sharing/00_tech_sharing_groups.txt:1-45` —— 科技共享组（英联邦/共产国际/轴心）。

**官方文档位置（1.19.4.2 实测）**：`common/technologies/`（13 个 `.txt`、27,065 行）、`common/technology_tags/`、`common/technology_sharing/` **都没有** `_documentation.md`。科技块的字段只能从 `infantry.txt` 头部注释与实例反推；`enable_equipments` / `enable_equipment_modules` / `enable_subunits` 的 token 目标见 `common/units/`（其下有 `equipment/_documentation.md`），效果类条目查 `documentation/effects_documentation.md`（`add_tech_bonus`、`set_technology`…）。
1.19.4 改动：10-28 批改 5 个科技文件（`infantry`、`support`、`artillery`、`MTG_naval`、`electronic_mechanical_engineering`），并配套改 `common/units/equipment/{tank_chassis,00_tank_modules,sam_missile}.txt` 与 `common/units/` 下 6 个兵种文件——纯数值平衡，`technologies` 的字段结构未变。

## 2. 结构（带注释）

```pdx
technologies = {

	# 常用写法：把「年份 → 科技树纵向坐标」做成常量（infantry.txt:3-14）
	@1936 = 2
	@1938 = 4
	@1940 = 8

	HHO_steel_alloys = {                    # 科技 ID

		# ---- 解锁内容（四类）----
		enable_equipments = {               # 解锁装备（装备 archetype/type 名）
			infantry_equipment_1
		}
		enable_equipment_modules = {        # 解锁装备模块（坦克炮塔/引擎等）
			tank_heavy_machine_gun
		}
		enable_subunits = {                 # 解锁营/支援连
			infantry
		}
		enable_subunits = {                 # 支持带 limit（support.txt:1151-1154）
			limit = { has_dlc = "Thunder at Our Gates" }
			hq_field_hospital
		}

		# ---- 研究成本与年份 ----
		research_cost = 1.5                 # 相对成本系数（不是绝对天数）
		start_year = 1936                   # 早于该年研究有惩罚（引擎按年份差算）

		# ---- 科技树 GUI 中的位置 ----
		folder = {
			name = infantry_folder          # 文件夹名（原版：infantry_folder / support_folder / ...）
			position = { x = 0 y = @1936 }  # x=列，y=行（用年份常量或整数）
		}

		# ---- 树上的连线（可多条 = 分支）----
		path = {
			leads_to_tech = HHO_steel_alloys_2
			research_cost_coeff = 1
		}

		# ---- 真正的前置要求（与 path 的视觉连线独立）----
		dependencies = {
			infantry_weapons1 = 1           # 需要前置科技等级
		}

		# ---- 研究类别（供 research_bonus / 科技共享匹配）----
		categories = {
			infantry_weapons
		}

		# ---- 完成时效果 ----
		on_research_complete_limit = {       # 可选：不满足则该科技不显示完成效果（NSB_armor.txt:73-77）
			NOT = { has_template_containing_unit = light_armor }
		}
		on_research_complete = {
			add_ideas = HHO_steel_alloys_idea
		}

		# ---- AI ----
		ai_will_do = {
			base = 2
			modifier = {
				factor = 3
				has_war = yes
			}
		}
	}
}
```

### 科技共享组（`common/technology_sharing/`）

```pdx
technology_sharing_group = {
	id = HHO_nordic_research
	name = HHO_nordic_research_name          # 本地化
	desc = HHO_nordic_research_desc
	picture = GFX_technology_sharing_default
	research_sharing_per_country_bonus = 0.1 # 每多一个成员国给的研究加速
	available = {                            # 哪些国家自动进组
		is_in_faction_with = SWE
	}
}
```

（原版三组见 `common/technology_sharing/00_tech_sharing_groups.txt:1-45`；除 `available` 外还有 `research_sharing_per_country_bonus`。）

## 3. 最小可跑完整示例

文件：`common/technologies/HHO_steel_tech.txt`

```pdx
technologies = {

	@1936 = 2
	@1938 = 4

	HHO_steel_alloys = {
		enable_equipments = {
			infantry_equipment_1
		}
		research_cost = 1.5
		start_year = 1936
		folder = {
			name = infantry_folder
			position = { x = 12 y = @1936 }
		}
		path = {
			leads_to_tech = HHO_steel_alloys_2
			research_cost_coeff = 1
		}
		dependencies = {
			infantry_weapons1 = 1
		}
		categories = {
			infantry_weapons
		}
		ai_will_do = {
			base = 2
			modifier = {
				factor = 2
				has_war = yes
			}
		}
	}

	HHO_steel_alloys_2 = {
		research_cost = 2.0
		start_year = 1938
		folder = {
			name = infantry_folder
			position = { x = 12 y = @1938 }
		}
		dependencies = {
			HHO_steel_alloys = 1
		}
		categories = {
			infantry_weapons
		}
		on_research_complete = {
			add_ideas = HHO_steel_alloys_idea
		}
		on_research_complete_limit = {
			has_war = yes
		}
		ai_will_do = {
			base = 1
		}
	}
}
```

> 说明：`HHO_steel_alloys` 用 `enable_equipments = { infantry_equipment_1 }` 只是**示例**（原版那个装备早已被 `infantry_weapons1` 解锁）。
> 真做新科技时，解锁对象应该是**你自己的新装备/新模块/新营**，否则只会重复解锁。新装备定义见 [03_military/equipment.md](../03_military/equipment.md)。

### 需要的本地化（`localisation/english/HHO_tech_l_english.yml`）

```yml
l_english:
 HHO_steel_alloys:0 "Improved Steel Alloys"
 HHO_steel_alloys_desc:0 "Better alloys mean lighter, tougher equipment."
 HHO_steel_alloys_2:0 "Advanced Steel Alloys"
 HHO_steel_alloys_2_desc:0 "Our metallurgists can now mass-produce high-grade steel."
 HHO_nordic_research:0 "Nordic Research Council"
 HHO_nordic_research_desc:0 "Shared research programmes across the Nordic states."
```

## 4. 科技怎么被别的系统用

| 需求 | 写法 | 证据 |
|---|---|---|
| 国策给科技 | `completion_reward = { set_technology = { HHO_steel_alloys = 1 } }` | `history/countries/GER - Germany.txt:41-55` |
| 事件给科技 | 同上（`set_technology` 是 effect） | 同上 |
| 国策给研究加速 | `completion_reward = { add_tech_bonus = { name = ... bonus = 0.5 uses = 1 category = infantry_weapons } }` | ⚠️ 参数名请以 `documentation/effects_documentation.md` 的 `add_tech_bonus` 词条为准 |
| 是否研究过 | `has_tech = HHO_steel_alloys`（trigger） | `common/scientist_traits/_documentation.md:38-40` |
| 理念给某类加速 | `research_bonus = { infantry_weapons = 0.1 }` 写在 idea 里（**类别名取 `categories`**） | `common/ideas/GER.txt:87-90` |

## 5. 新增 vs 覆盖

- **推荐**：新文件 + 新 tech ID；挂到**已存在的 folder 名**（`infantry_folder` 等）以免动 GUI。
- 想在原版树里插节点：需要让某个原版科技 `leads_to_tech` 指向你的科技。`path` 是单向声明，**只能通过覆盖那个原版科技整块**来加线。
  替代方案：自己新科技用 `dependencies` 约束、用 `folder.position` 摆在末尾，不连线（玩家仍可研究，只是视觉上孤立）。
- 若确实要自建 folder：`name` 用新的字符串即可，`position` 决定列位置；⚠️ 新增 folder 在科技界面里的列标题/图标是否自动生成未在本机实测，稳妥做法是复用原版 folder。

## 6. 1.19 相关注意

- `enable_subunits` / `enable_equipments` **支持 `limit = { ... }`**（`support.txt:1148-1154`、`special_projects_documentation.md` 同风格），
  这是做「DLC 专属解锁」的正规方式，别再用「拆成两个科技 + 事件补偿」。
- `on_research_complete` 常与 `on_research_complete_limit` 配对（`NSB_armor.txt:73-84`）。
- 学说科技在 `common/doctrines/`，其 UI 在学说页而非科技页；把学说混进 `common/technologies/` 在 1.19 是错的。
- 特殊项目也给「装备解锁」类奖励（`enable_equipments`），见 [special-projects.md](special-projects.md)。

## 7. 常见错误 / 自检清单

- [ ] 文件外层 `technologies = { ... }`；每个科技块有唯一 `id`。
- [ ] `folder.name` 与原版一致（或你确定要新建），`position` 的 x/y 不与同 folder 其他科技完全重叠。
- [ ] `dependencies` 里的前置科技存在且等级写对（否则永远不可研究）。
- [ ] `path.leads_to_tech` 指向的科技存在（指向不存在 = 断线，error.log 会报）。
- [ ] `enable_equipments` / `enable_subunits` / `enable_equipment_modules` 里的 token 真实存在（写错=解锁空气）。
- [ ] `categories` 与你要吃的 `research_bonus` 类别一致。
- [ ] `<tech_id>` 与 `<tech_id>_desc` 两条本地化都在。
- [ ] `on_research_complete` 里调用的 effect 合法（常犯：`add_ideas` 写到不存在的理念）。
- [ ] 改了原版科技整块覆盖时，`enable_*`、`path`、`dependencies` 全部抄回去，不要只写想改的字段。

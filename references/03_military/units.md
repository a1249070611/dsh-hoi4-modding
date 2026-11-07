---
title: 单位与营（Units / Sub-units）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/units/infantry.txt
  - common/units/artillery.txt
  - common/units/artillery_brigade.txt
  - common/units/engineer.txt
  - common/units/fire_support.txt
  - common/units/air.txt
  - common/units/battleship.txt
  - common/units/unit_modifiers/unit_modifiers.txt
  - common/defines/00_defines.lua
  - common/unit_tags/00_categories.txt
  - common/units/names_divisions
---

# 单位与营（Units / Sub-units）

**一句话**：`common/units/*.txt` 定义「师里能放的最小格子」——步兵营、炮兵营、坦克营、各种支援连、以及海空军的最小单位（船种/机种）。它不含数值平衡的主体（那在装备里），它定义的是**编制、人力、组织度、速度、地形修正、消耗哪类装备**。

> 先分清三个词组，后面全靠它们：
> - **sub_unit（子单元/营）**：`common/units/*.txt` 里 `sub_units = { ... }` 的键，例如 `infantry`、`artillery_brigade`、`engineer`、`battleship`、`fighter`。
> - **equipment（装备）**：`common/units/equipment/*.txt`，例如 `infantry_equipment`、`artillery_equipment`。见 [equipment.md](equipment.md)。
> - **division_template（师编制）**：把营摆到 `x/y` 网格里，见 [division-templates.md](division-templates.md)。

---

## 1. 文件放哪 / 命名 / 加载

| 项 | 事实（本地实测） |
|---|---|
| 目录 | `common/units/*.txt`，一个文件一个或多个 `sub_units = { ... }` 顶层块 |
| 文件名 | 无约定；原版按兵种拆成 `infantry.txt`、`artillery.txt`、`engineer.txt`…（`common/units/` 下约 50 个 .txt） |
| 子目录 | 营定义只读顶层 `.txt`；`common/units/names/`、`common/units/names_divisions/`、`common/units/unit_modifiers/` 是**专用子目录**（部队命名、番号名、modifier 注册），不要混放 |
| 加载 | 启动时一次性读取，**无热重载** |
| 覆盖 | 不同文件同名 sub_unit ID → 后加载覆盖；同名文件 → 整文件替换 |
| 校验和 | 改动会影响 checksum |

原版可参考的真实文件（写新营前先看同类）：
- 步兵/骑兵/自行车/摩托化：`common/units/infantry.txt`、`cavalry.txt`、`bus.txt`
- 线列炮兵：`common/units/artillery_brigade.txt`（注意：`artillery_brigade` 是**线列**，`combat_width = 3`）
- 支援连：`common/units/artillery.txt`（`artillery` 是**师属支援炮兵**，`combat_width = 0`）、`engineer.txt`、`recon.txt`、`signal.txt`、`logistics.txt`、`field_hospital.txt`、`maintenance.txt`、`military_police.txt`
- 团级支援（1.19 新）：`common/units/fire_support.txt`、`tank_destroyer_brigade.txt`、`sp_anti-air_brigade.txt`
- 海/空最小单位：`common/units/battleship.txt`、`destroyer.txt`、`submarine.txt`、`air.txt`
- 特殊：`common/units/hq_support.txt`（HQ 模板）、`railway_gun.txt`、`helicopter_brigade.txt`

---

## 2. sub_unit 字段全表（都在原版文件里能对上）

以 `common/units/infantry.txt` 的 `infantry`（第 6-54 行）为例：

```pdx
sub_units = {
	infantry = {
		abbreviation = "INF"        # 编制界面缩略名（3 字母）
		sprite = infantry           # 地图/编制上的 3D 模型 sprite 名（不含 GFX_ 前缀）
		map_icon_category = infantry # 地图图标大类：land 用 infantry/armored/other；sea 用 ship/transport/uboat
		priority = 600              # 编制界面排序
		ai_priority = 200
		active = no                 # no = 需要科技/解锁后才可用

		type = { infantry }         # ★营的类型集合，供 trigger/加成匹配（见下）
		group = infantry            # 编制界面分组：infantry / mobile / armor / support / combat_support ...
		categories = {              # ★类别，加成与筛选的主要依据
			category_front_line
			category_light_infantry
			category_all_infantry
			category_army
			category_infantry_and_bicycle
		}

		combat_width = 2            # ★占用的战斗宽度（1.19 下与地形 combat_width 配合）

		max_strength = 25           # 满编 strength（1000 人 ≈ ?，见下注）
		max_organisation = 60       # 组织度
		default_morale = 0.3
		manpower = 1000             # 该营占用的人力
		training_time = 90
		suppression = 1.5
		weight = 0.5                # 运输/海运重量
		supply_consumption = 0.06   # 补给消耗

		need = {                    # ★每个营需要多少装备（按比例消耗）
			infantry_equipment = 100
		}
	}
}
```

### 2.1 关键字段逐个说清

- **`type`**：营的「兵种类型」集合（可多个）。补给/统计/AI 用它分类。取值典型：`infantry`、`cavalry`、`motorized`、`mechanized`、`armor`、`artillery`、`anti_air`、`anti_tank`、`support`、`capital_ship`、`screen_ship`、`submarine`、`carrier`、`fighter`、`cas`…（海空文件里 `type = { capital_ship }` / `type = fighter`）。
- **`categories`**：真正的「加成挂载点」。国策/学说/理念里的 `category_all_infantry = { ... }`、`category_tanks = { ... }` 就是按这个匹配的（见 `common/doctrines/subdoctrines/land/armor_subdoctrines.txt` 的 `category_tanks = { max_organisation = 1 }`）。**新营不写 categories，学说和国策就加成不到它。**
- **`group`**：编制界面里的行分组（`infantry`、`combat_support`、`support`、`mobile`、`armor`）。支援连一般是 `group = support`。
- **`need`**：每营消耗装备的「满编数量」。师的装备需求 = 各营 `need` 求和；装备不足时按比例掉 strength。
- **`essential`**：哪些装备「缺了就直接不能训练/作战」（`engineer.txt` 的 `essential = { support_equipment }`）。
- **`max_strength`**：营的血量（strength）上限。支援连常见 0.2~2，步兵 25。
- **`max_organisation = 0`**：炮兵类支援连常为 0（组织度由线列营提供）。
- **`affects_speed = no`**：该营不拖慢师速度（支援连常见）。
- **`is_artillery_brigade = yes`**：标记为炮兵，影响战斗时的炮击阶段/战术选择（`has_artillery_ratio` trigger 依赖它）。
- **`battalion_mult`**：给「同师内其它营」的乘算加成（工程师给步兵加堑壕）：

```pdx
# common/units/engineer.txt 第 38-42 行
battalion_mult = {
	category = category_light_infantry
	entrenchment = 0.20
	add = yes          # 不写 add = yes 时按乘算处理
}
```

- **`same_support_type = engineer`**：同类型支援连不能重复编入（工程连与先锋连互斥，见 `engineer.txt`）。
- **`regimental = no` / `divisional = no`**：编制层级标记。1.19 里支援连写 `regimental = no`；新增的**团级支援**单位写 `divisional = no` 且 categories 含 `category_regimental_support_battalions`、并用 `allowed_battalion_groups = { infantry mobile combat_support }` 限定能配给哪些营（`common/units/fire_support.txt` 第 19-27 行）。⚠️ 这两个标记的确切语义本机无官方文档说明，以上为对原版用例的归纳。
- **地形块**：直接以地形名为键，写 `attack` / `defence` / `movement`：

```pdx
# common/units/engineer.txt 第 49-72 行
forest = { defence = 0.25 movement = 0.05 }
hills = { defence = 0.1 }
jungle = { defence = 0.25 }
marsh = { defence = 0.25 movement = 0.2 }
fort = { attack = 0.1 defence = 0.25 }
river = { defence = 0.25 movement = 0.25 }
amphibious = { attack = 0.15 }
```
地形名必须与 `common/terrain/00_terrain.txt` 的 `categories` 键一致（`plains`/`forest`/`hills`/`mountain`/`urban`/`desert`/`marsh`/`jungle`/`ocean`/`lakes` 等），另加 `fort`、`river`、`amphibious` 这类虚拟地形。见 [terrain.md](../04_world/terrain.md)。

### 2.2 海/空 sub_unit 特殊字段

```pdx
# common/units/battleship.txt（全文 27 行）
sub_units = {
	battleship = {
		sprite = battleship
		map_icon_category = ship
		active = yes
		type = { capital_ship }
		need_equipment = { ship_hull_heavy = 1 }        # ★海军用 need_equipment（一艘=1 个船体）
		need_equipment_modules = {                       # ★必须装某类模块之一
			any = {
				ship_armor_bb_1 = 1
				ship_armor_bb_2 = 1
				ship_armor_bb_3 = 1
				ship_armor_shbb = 1
			}
		}
		max_organisation = 50
		supply_consumption = 0.56
		critical_parts = { rudder_jammed destroyed_ammo_storage broken_propeller on_fire }
		critical_part_damage_chance_mult = 1
		hit_profile_mult = 1.0
	}
}
```

```pdx
# common/units/air.txt 第 4-25 行（空军用 need + 机翼大小）
fighter = {
	sprite = light_plane
	type = fighter
	need = { small_plane_airframe = 1 }
	categories = { category_fighter }
	land_air_wing_size = 100
	mega_carrier_air_wing_size = 10
}
cv_fighter = {
	need = { cv_small_plane_airframe = 1 }
	carrier_air_wing_size = 10          # 航母舰载机中队 10 架
	submarine_carrier_air_wing_size = 3 # 1.19 有潜艇航母
	land_air_wing_size = 100
	mega_carrier_air_wing_size = 10     # 1.19 有超级航母（mega carrier）
}
```
海空的具体玩法见 [navy.md](navy.md)、[air.md](air.md)。

### 2.3 `unit_modifiers` 注册表（容易漏）

`common/units/unit_modifiers/unit_modifiers.txt` 是**白名单**：只有列进去的 `modifier_army_sub_unit_<兵种或类别>_attack_factor / defence_factor / speed_factor / max_org_factor …` 才会在陆战里生效。文件开头原版注释直接写明这一点。你新增一个营/类别后，若想让它吃到「对某兵种的加成」modifier，需要在这里登记对应 modifier 名。

---

## 3. 最小可跑示例：新增一个「海军陆战突击工兵营」

目标：新增 `HHO_assault_pioneer`（团级支援单位），只在有 `HHO_assault_engineering` 科技后可用。

**第 1 步 建文件** `common/units/hho_units.txt`：

```pdx
# 路径：<mod>/common/units/hho_units.txt
sub_units = {

	HHO_assault_pioneer = {
		abbreviation = "HAP"
		sprite = infantry
		map_icon_category = infantry

		priority = 0
		ai_priority = 0
		active = no

		type = {
			infantry
			support
		}

		group = support
		allowed_battalion_groups = { infantry mobile }

		categories = {
			category_support_battalions
			category_regimental_support_battalions
			category_army
		}

		divisional = no
		combat_width = 0

		need = {
			infantry_equipment = 20
			support_equipment = 20
		}
		essential = { support_equipment }

		manpower = 200
		training_time = 120
		max_organisation = 25
		default_morale = 0.2
		max_strength = 0.8
		weight = 0.1
		supply_consumption = 0.03

		# 支援连对自身战斗数值的削减（原版惯例：负数）
		defense = -0.2
		breakthrough = -0.2
		soft_attack = -0.4

		can_be_parachuted = yes

		forest = { attack = 0.05 defence = 0.15 movement = 0.1 }
		hills  = { attack = 0.05 defence = 0.1 }
		jungle = { attack = 0.05 defence = 0.1 }
		marsh  = { attack = 0.05 defence = 0.1 movement = 0.1 }
		river  = { attack = 0.05 defence = 0.1 movement = 0.2 }
		urban  = { attack = 0.15 defence = 0.05 }
		fort   = { attack = 0.2 defence = 0.1 }

		same_support_type = engineer
	}
}
```

**第 2 步 解锁**（`active = no` 必须被科技或效果打开）。原版用科技的 **`enable_subunits`** 字段：

```pdx
# 原版证据：common/technologies/support.txt 第 675-683 行
tech_military_police = {
	enable_subunits = {
		military_police
	}
	enable_subunits = {
		limit = { has_dlc = "Thunder at Our Gates" }
		hq_military_police
	}
	research_cost = 1.25
	path = { leads_to_tech = tech_military_police2 research_cost_coeff = 1 }
}
```

所以你的科技写：

```pdx
# 路径：<mod>/common/technologies/hho_tech.txt
technologies = {
	HHO_assault_engineering = {
		enable_subunits = { HHO_assault_pioneer }
		research_cost = 2
		start_year = 1936
		folder = { name = industry_folder position = { x = 0 y = 0 } }  # 科技树坐标写法见 ../02_content/technologies.md
		path = { leads_to_tech = HHO_assault_engineering2 research_cost_coeff = 1 }
	}
}
```

> 科技节点完整字段（`folder`/`position`/`prerequisite`/`on_research_complete`/`enable_equipments` 等）见 [../02_content/technologies.md](../02_content/technologies.md)，本节只讲与营解锁相关的 `enable_subunits`。

**第 3 步 本地化**（`localisation/simp_chinese/hho_units_l_simp_chinese.yml`，UTF-8 BOM）：

```yml
l_simp_chinese:
 HHO_assault_pioneer: "海军陆战突击工兵营"
```

**第 4 步 用起来**：
- 在师编制里加 `regimental_support = { HHO_assault_pioneer = { x = 0 y = 0 } }`（见 [division-templates.md](division-templates.md)）
- 让 AI 会用：在 `common/ai_templates/<你的文件>.txt` 的 `target_template` 里加 `regimental_support = { HHO_assault_pioneer = 1 }`
- 让国策给加成：`HHO_focus = { completion_reward = { if = { limit = { } army_experience = 5 } } }`，或给营加成用 `category_...`（见 [../02_content/focus-trees.md](../02_content/focus-trees.md)）。

---

## 4. 想改数值？层级判断三步

1. **改「一个营的固有属性」**（组织度、人力、宽、地形修正）→ 改 `common/units/*.txt` 里那个 sub_unit。
2. **改「装备提供的攻击/防御/硬度」** → 改 `common/units/equipment/*.txt`（见 [equipment.md](equipment.md)）。师面板上的 attack/defence 主要由装备 stat 汇总而来。
3. **改「全局折算系数」** → 改 `common/defines/00_defines.lua`（见 [land-combat.md](land-combat.md)）。

> 风险提示：直接覆盖原版 sub_unit（复制整条定义到自己的文件）会让原版后续平衡更新失效且难以维护；**新增 ID + 用国策/科技/效果替换**更安全。

---

## 5. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 营（sub_unit）定义 | `common/units/` 顶层 | 45 `.txt`（`sub_units = { }`） | ❌ |
| **营类别注册表** | `common/unit_tags/00_categories.txt` | 51 行 / 49 个 `category_*` | ❌ |
| 装备（营的 `need` 引用目标） | `common/units/equipment/` | 51 `.txt` | ✅ `_documentation.md`（125 行） |
| 师名册组 | `common/units/names_divisions/` | 100 文件 | ❌ |
| 舰名 / 铁路炮名 / 代号 | `names_ships/`(65)、`names_railway_guns/`(11)、`codenames_operatives/`(14) | — | ❌ |
| 单位修正器 | `common/units/unit_modifiers/unit_modifiers.txt` | 97 行 | ❌ |
| 关键部件 | `common/units/critical_parts/` | 1 文件 | ❌ |
| 初始 OOB（引用营） | `history/units/` | 609 文件 | ❌ |

目录合计 297 文件（296 `.txt` + 1 `_documentation.md`），行数约 11.4 万。

**`common/unit_tags/00_categories.txt` 是本域最常被忽略的入口**——文件只做一件事：声明全部合法 `category_*` 标签（`sub_unit_categories = { ... }`，49 个）。营写了未注册的 category 会连锁失效：

1. `logs/error.log` 报未知 category（或静默不生效）；
2. `common/doctrines/` 里按 `target = { category_xxx }` 的加成永远匹配不到；
3. 师模板 `support` / `regimental_support` 列的校验不通过。

所以"新增一个营"的正确顺序是：先找已有 category → 不够才在 `00_categories.txt` 里注册新标签（该文件只有这一处列表，**整文件替换**）→ 写营 → 写本地化 → 最后在 `history/units/` 或科技里让它可被解锁。

## 6. 常见错误 / 自检清单

- [ ] 文件在 `common/units/` 顶层，顶层块是 `sub_units = { ... }`（不是 `units` / `sub_unit`）。
- [ ] 新营写了 `categories`，否则学说/国策加成不到。
- [ ] `need` 里的装备 ID 真实存在（在 `common/units/equipment/*.txt` 里 grep 得到）。
- [ ] `active = no` 的营确实被科技/效果解锁（否则永远灰着）。
- [ ] 地形块的名字都在 `common/terrain/00_terrain.txt` 的 `categories` 里。
- [ ] 有本地化 key（`abbreviation` 是界面缩略名，不是 loc key；营名 loc key = sub_unit ID）。
- [ ] 支援连与线列营不要混：支援连 `combat_width = 0`，线列营 > 0。
- [ ] 新增类别/兵种后检查 `common/units/unit_modifiers/unit_modifiers.txt` 是否要登记。
- [ ] 出错时在 `logs/error.log` 中搜你的 ID；常见是未知 category、缺 loc、括号不平衡。
- [ ] 改完必须重启游戏（无热重载）。

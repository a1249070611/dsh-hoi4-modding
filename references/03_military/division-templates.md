---
title: 师编制与 AI 模板（Division Templates）
domain: 03_military
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - history/units/GER_1936.txt
  - history/units/CZE_1936.txt
  - common/ai_templates/_documentation.md
  - common/ai_templates/generic.txt
  - common/defines/00_defines.lua
  - documentation/effects_documentation.md
  - common/unit_tags/00_categories.txt
  - common/units/names_divisions
---

# 师编制与 AI 模板（Division Templates）

**一句话**：`division_template` 把「营」摆进一个 **5 列 × 5 行**的网格（外加 1 列支援连、5 列团级支援），`units = { ... }` 再把模板实例化成地图上的师；AI 通过 `common/ai_templates/` 决定要往什么编成方向升级。

---

## 1. 文件在哪

| 内容 | 路径 | 说明 |
|---|---|---|
| 初始师编制 + 初始部队 | `history/units/<TAG>_<year>.txt` | 一个文件里先若干 `division_template = { ... }`，再一个 `units = { ... }`；原版还有 `_nsb`、`_bba`、`_aat` 等 DLC 变体文件 |
| AI 目标编成 | `common/ai_templates/*.txt` | 角色的「目标模板」，AI 会自己复制现有模板并向目标靠拢 |
| 编成的运行时修改 | scripted effects | `add_units_to_division_template`、`set_division_template_cap`、`set_division_template_lock`（见 `documentation/effects_documentation.md`） |
| 网格上限与成本 | `common/defines/00_defines.lua`（NMilitary 段） | 见下表 |

原版参考文件：
- `history/units/GER_1936.txt`（第 1-99 行是 5 个 `division_template`，第 101 行起 `units`）
- `history/units/CZE_1936.txt`（第 52-70 行，**1.19 唯一使用 `regimental_support` 的原版编制**）
- `common/ai_templates/generic.txt`、`templates_GER.txt`、`_documentation.md`（更新日期 2024-08，比网上教程新）

---

## 2. division_template 结构

```pdx
# 路径：history/units/GER_1936.txt 第 1-22 行（原文）
division_template = {
	name = "Infanterie-Division"

	division_names_group = GER_Inf_01     # 番号名组（common/units/names_divisions/）

	regiments = {                         # ★线列营：x = 列(0~4)，y = 行(0~4)
		infantry = { x = 0 y = 0 }
		infantry = { x = 0 y = 1 }
		infantry = { x = 0 y = 2 }
		infantry = { x = 1 y = 0 }
		infantry = { x = 1 y = 1 }
		infantry = { x = 1 y = 2 }
		infantry = { x = 2 y = 0 }
		infantry = { x = 2 y = 1 }
		infantry = { x = 2 y = 2 }
	}

	support = {                           # ★支援连：只在 x = 0 这一列，y = 0~4
		engineer = { x = 0 y = 0 }
		artillery = { x = 0 y = 1 }
	}
}
```

**网格规则（1.19 实测，来自 `common/defines/00_defines.lua` 第 860-873 行）**：

| define | 值 | 含义 |
|---|---|---|
| `MAX_DIVISION_BRIGADE_WIDTH` | 5 | 线列最多 5 列（x = 0~4） |
| `MAX_DIVISION_BRIGADE_HEIGHT` | 5 | 线列最多 5 行（y = 0~4） |
| `MIN_DIVISION_BRIGADE_HEIGHT` | 4 | 至少 4 行 |
| `MAX_DIVISION_SUPPORT_WIDTH` | 1 | 支援连只有 1 列 |
| `MAX_DIVISION_SUPPORT_HEIGHT` | 5 | 支援连最多 5 个 |
| `MAX_REGIMENTAL_SUPPORT_WIDTH` | 5 | **团级支援**最多 5 列（1.19 新） |
| `MAX_REGIMENTAL_SUPPORT_HEIGHT` | 1 | 团级支援 1 行 |
| `REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS` | `{ 3 }` | 每团级支援位下方需要 3 个营才可放置（注释原文："how many battalions are required in the regiment to be able to place a support in that row"） |
| `BASE_DIVISION_BRIGADE_GROUP_COST` | 20 | 解锁一个团槽的陆军经验成本 |
| `BASE_DIVISION_BRIGADE_CHANGE_COST` | 5 | 改动一列的成本 |
| `BASE_DIVISION_SUPPORT_SLOT_COST` | 10 | 解锁支援槽成本 |
| `REGIMENTAL_SUPPORT_SLOT_COST_MULTIPLIER` | 0.5 | 团级支援槽成本系数 |

这里 `x` 是**列（团/regiment）**，`y` 是**行（营/battalion）**。一个 x 列 = 一个团，最多 5 个营；师最大 5×5 = 25 个线列营。

### 2.1 ★1.19 新增第三层：`regimental_support`

```pdx
# 路径：history/units/CZE_1936.txt 第 52-70 行（原文）
division_template = {
	name = "Rychlá divize"
	division_names_group = CZE_ARM_01
	regiments = {
		light_armor = { x = 0 y = 0 }
		light_armor = { x = 0 y = 1 }
		cavalry = { x = 1 y = 0 }
		cavalry = { x = 1 y = 1 }
		cavalry = { x = 1 y = 2 }
	}

	regimental_support = { #Various field pieces operated by the division at the regeniment level
		field_guns = { x = 1 y = 0 }
	}

	support = {
		recon = { x = 0 y = 0 }
	}
}
```

- 这是 1.19「Operation Postern」新增的编制层级：团级支援占用 `x` 列（对应某个团），只允许 `y = 0`。
- 能放什么由子单元的 `allowed_battalion_groups` + `category_regimental_support_battalions` + `divisional = no` 决定（见 [units.md](units.md) 第 2.1 节）。
- 原版用它的营：`field_guns`（CZE 编制）、`fire_support`、`mot_fire_support`、`tank_destroyer_regimental_support` 系列、`self_propelled_anti_air_regimental_support` 系列。
- **旧教程完全没有这一层**，老 mod 的编制可以直接沿用（不写就不占位），但想要「团属火力」必须用 1.19 语法。

---

## 3. 师属性从哪来（这是最容易搞错的地方）

师面板上的数值不是存在 `division_template` 里的，而是**运行时汇总**：

```
师属性 ≈ Σ(每个营的 sub_unit 基础值 + 该营装备的 equipment stat × 数量)
        × (1 + Σ 支援连 battalion_mult 加成)
        × (1 + 学说/国策/理念/将领/traits 的 category 加成)
        × (1 + 地形/天气/补给/经验修正)
```

对应关系：
- **营底盘**：`max_organisation`、`max_strength`、`manpower`、`combat_width`、`supply_consumption`、地形修正 → `common/units/*.txt`（见 [units.md](units.md)）。
- **装备数值**：`soft_attack`/`hard_attack`/`defense`/`breakthrough`/`armor_value`/`hardness`/`ap_attack` → `common/units/equipment/*.txt`（见 [equipment.md](equipment.md)）。师的攻击/防御基本是各营装备 stat 的加总。
- **编制界面里显示的绿色/红色差值**（designer 里"modified"概念）：来自上面第 3、4 行的乘算修正，即「基础值 vs 加成后值」。哪来的加成可以在 `common/modifiers/` 与 `documentation/modifiers_documentation.md` 里查（modifier 全表）。
- **团级支援**只作用于它所在的那个团（不作用于全师）；`battalion_mult` 有 `add = yes` 时是加算，否则乘算。

> 排错思路：如果改了一个营的属性但游戏里没变，先确认改的是**这个师实际使用的营**（而不是支援连版本）、再确认没有别的 mod 用同 ID 覆盖。

---

## 4. `units` 块（初始部队实例化）

```pdx
# 路径：history/units/GER_1936.txt 第 101-124 行（节选）
units = {
	division = {
		division_name = {
			is_name_ordered = yes
			name_order = 25
		}
		location = 6334                  # 省 ID（必须是该省的 owner/controller，否则会重新部署）
		division_template = "Infanterie-Division"   # ★按 name 字符串引用模板
		start_experience_factor = 0.3
		# start_equipment_factor = 0.7   # 原版 CZE_1936.txt 第 80 行有：初始装备比例
	}
	division = { ... }
}
```

要点：
- `division_template` 引用的是模板的 **`name` 字符串**（不是文件名、不是 ID），所以模板名必须唯一。
- 同一个模板可以被多个 `division` 实例引用。
- 新国家历史文件通常放在 `history/countries/<TAG>.txt` 里通过 `load_oob = "TAG_1936"` 载入 OOB（见 [../02_content/history-countries.md](../02_content/history-countries.md)）。
- `start_experience_factor` ∈ [0,1]；`start_equipment_factor` 同理。

---

## 5. 运行时改编制（script 能做的事）

`documentation/effects_documentation.md` 里有三个关键 effect（COUNTRY scope）：

```pdx
# 给某模板加营（第 2433-2453 行原文结构）
add_units_to_division_template = {
	template_name = "Infanterie-Division"   # 对具体师操作时可省略
	regiments = {
		infantry = 0                        # 数字 = 目标 x 列，自动放到该列第一个空位
		cavalry = 2                         # 放到 x = 2 列
	}
	support = {
		military_police = 0
	}
	regimental_support = {
		military_police = 0                 # 1.19：团级支援也支持
	}
}

set_division_template_cap = {
	division_template = "Infanterie-Division"
	division_cap = 30
}

set_division_template_lock = {
	division_template = "Infanterie-Division"
	is_locked = yes
}
```

典型用法：国策解锁「装甲师扩编」→ `set_division_template_cap` 提高上限；国策给模板加一个坦克营 → `add_units_to_division_template`。国策写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)。

---

## 6. AI 模板（`common/ai_templates/`）

官方文档 `common/ai_templates/_documentation.md`（2024-08 更新）说得很清楚，这里只摘要点：

- **role-level 条目**：`role = infantry/armor/...`，用 `blocked_for` / `available_for` 限定国家。
- **target_template**：写「想要多少营/支援连」，AI 会挑最接近的现有模板复制并改造：

```pdx
# 结构来自 common/ai_templates/_documentation.md 与 generic.txt
infantry_generic = {
	blocked_for = { GER JAP }
	role = infantry

	upgrade_prio = {
		base = 2
		modifier = { factor = 3 has_tech = basic_medium_tank }
	}

	infantry_1 = {
		upgrade_prio = { base = 1 }
		target_template = {
			support = {
				engineer = 1
				anti_air = 1
				artillery = 1
			}
			regiments = {
				infantry = 6
			}
		}
		replace_at_match = 0.9
		replace_with = infantry_2
		target_min_match = 0.9
	}

	infantry_2 = {
		target_template = {
			support = { engineer = 1 recon = 1 field_hospital = 1 anti_air = 1 anti_tank = 1 }
			regiments = { infantry = 9 artillery_brigade = 2 }
		}
	}
}
```

- **1.19 新**：`target_template` 里可以写 `regimental_support = { anti_tank_battery = 1 }`（`common/ai_templates/generic.txt` 已用）。
- 调试：控制台 `imgui show ai_templates` / `imgui show ai_division_production`（文档明确给出）。
- `enable` / `can_upgrade_in_field` / `replace_at_match` / `target_min_match` 都是 trigger 化的门控。

---

## 7. 最小可跑示例：给 SWE 加一个「北极装甲旅」模板与初始部队

```pdx
# 路径：<mod>/history/units/SWE_1936.txt（会整文件替换原版同名文件！）
# ★更安全做法：在 <mod>/history/units/SWE_1936_hho.txt 里只写新增模板，
#   但原版 SWE 的 OOB 也要能引用到——实践中通常整文件复制原版再加内容。
division_template = {
	name = "HHO_Arctic_Armored_Brigade"
	division_names_group = SWE_ARM_01        # 原版组名见 common/units/names_divisions/SWE_names_divisions.txt 第 179 行

	regiments = {
		light_armor = { x = 0 y = 0 }
		light_armor = { x = 0 y = 1 }
		motorized = { x = 1 y = 0 }
		motorized = { x = 1 y = 1 }
		motorized = { x = 1 y = 2 }
	}

	regimental_support = {
		HHO_assault_pioneer = { x = 1 y = 0 }   # 见 units.md 的示例营
	}

	support = {
		engineer = { x = 0 y = 0 }
		recon = { x = 0 y = 1 }
	}
}

units = {
	division = {
		division_name = { is_name_ordered = yes name_order = 1 }
		location = 9636                 # 用真实存在的省 ID（这里只是示例，落点要按地图核对）
		division_template = "HHO_Arctic_Armored_Brigade"
		start_experience_factor = 0.2
		start_equipment_factor = 0.6
	}
}
```

配套本地化：模板名是**直接显示的字符串**（不是 loc key），所以 `name = "..."` 里写的是显示名；番号名组 `division_names_group` 必须在 `common/units/names_divisions/` 里存在（原版 SWE 有 `SWE_ARM_01`，见 `SWE_names_divisions.txt` 第 179 行）。

> ⚠️ `history/units/` 是「同名文件整体替换」：自己新建 `SWE_1936_hho.txt` **不会**替换原版 `SWE_1936.txt`，两者都会加载（模板会叠加，`units` 也会叠加），可能产生重复师。要替原版 OOB 必须整文件替换或用 `load_oob` 换成自己的 OOB 文件。

---

## 8. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 师模板定义 | `history/units/` 的 `division_template = { }` | 609 文件 | ❌ |
| 初始部队（OOB） | `history/units/` 的 `units = { }` | 同上 | ❌ |
| 营引用 | `common/units/` 顶层 | 45 文件 | ❌ |
| 营类别注册表（support / regimental 列校验） | `common/unit_tags/00_categories.txt` | 51 行 / 49 个 `category_*` | ❌ |
| 师名册组（`division_names_group`） | `common/units/names_divisions/` | 100 文件 | ❌ |
| AI 模板 | `common/ai_templates/` | 16 文件（15 `.txt`） | ✅ `_documentation.md` |
| 增援优先级 / 槽位常量 | `common/defines/00_defines.lua`（`REINFORCEMENT_DIVISION_PRIORITY_COUNT`、`REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS`） | 4,728 行 | ❌ |
| 运行时改编制 | `documentation/effects_documentation.md`（`set_division_template_*`、`load_oob`） | 222,533 B | ✅ |

- **模板校验取决于 `unit_tags/00_categories.txt`**：`support` 列要求营带 `category_support_battalions`，`regimental_support` 列要求 `divisional = no` + `category_regimental_support_battalions` 且数量达标。类别标签没在该文件注册，模板会静默拒收（见 [units.md](units.md) §5）。
- **AI 想用新编制必须写 `common/ai_templates/` 的 `target_template`**，该目录有官方 `_documentation.md`，字段疑问先查它。
- 1.19.4 改过 `ai_templates/{SOV,USA}` 与 `history/units/` 若干文件：整文件替换原版 OOB 前先 diff。

## 9. 常见错误 / 自检清单

- [ ] `division_template` 的 `name` 唯一，否则引用歧义。
- [ ] `x` ≤ 4、`y` ≤ 4；支援连只有 `x = 0`；团级支援 `y = 0`。
- [ ] `regiments` / `support` / `regimental_support` 里的营 ID 在 `common/units/` 存在且已被解锁（`active`）。
- [ ] `regimental_support` 的单位满足 `divisional = no` + `category_regimental_support_battalions`，且该列有 ≥3 个营（`REGIMENTAL_SUPPORT_REQUIRED_BATTALIONS`）。
- [ ] `units` 里的 `location` 省 ID 存在且属于该国控制，否则开局师会被重新部署。
- [ ] `division_template = "..."` 写的是模板 name，字面量要完全一致（含空格）。
- [ ] `division_names_group` 在 `common/units/names_divisions/` 里存在。
- [ ] AI 想用新编成必须在 `common/ai_templates/` 里写 `target_template`，否则 AI 永远不造。
- [ ] 改模板上限/锁定用 `set_division_template_cap` / `set_division_template_lock`，不要直接改 defines（会影响所有国家）。
- [ ] 出错先看 `logs/error.log`，搜模板名 / 营 ID。

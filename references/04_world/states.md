---
title: 州系统（States）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - history/states/1-France.txt
  - history/states/10-Poland.txt
  - history/states/1032 - Yanan.txt
  - history/states/1022 - Interior Borneo.txt
  - common/state_category
  - map/definition.csv
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/strategic_locations/documentation.md
---

# 州系统（States）

**一句话**：州（state）是「人力、建筑槽、资源、胜利点、归属」的最小行政单位；一个州 = `history/states/<id>-<name>.txt` 一个文件 + 若干省（province）+ 一个 `state_category`（决定槽位）。

**本机现状**：`history/states/` 有 **1081 个文件**，state id `1`~`1081`，**无重复**；下一个可用 ID 是 `1082`。

---

## 1. 文件位置与命名

| 项 | 事实 |
|---|---|
| 目录 | `history/states/*.txt`，一个文件一个 `state = { ... }` |
| 文件名 | 约定 `<id>-<英文名>.txt`（如 `1-France.txt`、`1032 - Yanan.txt`）；**文件名不参与解析**，`id` 字段才重要 |
| 子目录 | 不读子目录 |
| 加载 | 启动时读取；无热重载 |
| 覆盖 | 同名文件整体替换；不同文件同 `id` → 后加载覆盖（⚠️ 会导致该州建筑/归属被整体替换） |
| 校验和 | 改动影响 checksum |

---

## 2. 顶层字段（全部来自原版文件）

```pdx
# 路径：history/states/1-France.txt（全文 29 行）
state = {
	id = 1
	name = "STATE_1"                  # ★loc key（原版 state_names_l_english.yml 第 2 行 = "Corsica"）
	manpower = 322900                 # 州人力池

	state_category = town             # ★决定建筑槽位（见第 3 节）

	history = {                       # ★初始归属/建筑/胜利点，可写日期块
		owner = FRA
		victory_points = { 3838 1 }   # { 省ID 点数 }，可多行
		buildings = {
			infrastructure = 2        # 州级建筑：直接写 数量
			industrial_complex = 1
			air_base = 1
			3838 = {                  # ★省级建筑：以省 ID 为键
				naval_base = 3
			}
		}
		add_core_of = COR             # 加核心（可多行）
		add_core_of = FRA
	}

	provinces = {                     # ★该州包含的省 ID
		3838 9851 11804
	}

	local_supplies = 0.0              # ★本地补给（见 supply.md）
}
```

### 2.1 字段逐个说明

| 字段 | 类型 | 说明 | 原版证据 |
|---|---|---|---|
| `id` | int | 州 ID，全局唯一 | 所有州文件 |
| `name` | string | loc key，惯例 `STATE_<id>` | `state_names_l_english.yml` 第 2/188 行 |
| `manpower` | int | 州人力（影响可招募人口） | `10-Poland.txt` 第 4 行 `3089000` |
| `state_category` | token | 州类别，决定槽位 | `common/state_category/*.txt`（13 种） |
| `history` | block | 初始状态（可含日期块） | 见 2.2 |
| `provinces` | int list | 省 ID 列表 | `1-France.txt` 第 24 行 |
| `local_supplies` | float | 本地补给值 | `1000-East Azerbaijan.txt` 第 28 行 `4.0` |
| `resources` | block | 州资源产量 | `1000-East Azerbaijan.txt` 第 6-8 行 |
| `buildings_max_level_factor` | float | 建筑等级上限系数 | `1032 - Yanan.txt` 第 5 行 `= 1` |
| `impassable` | yes/no | 不可通行州（山脉/丛林隔离区） | `1022 - Interior Borneo.txt` 第 7 行 |
| `force_link_ownership_to` | int | 强制归属跟随某个州 | 同上第 8 行 `= 334` |
| `impassable_ignored_links` | int list | 不可通行州仍需连通的邻州 | 同上第 9 行 |

### 2.2 `history` 块里能写什么

- `owner = TAG`：所有者；`controller = TAG`：控制者（不写默认等于 owner）。
- `add_core_of = TAG`：加核心（可多行）。
- `add_claim_by = TAG`：加声索（原版 `106-Macedonia.txt` 第 22 行 `add_claim_by = BUL`）。
- `buildings = { ... }`：见第 4 节。
- `victory_points = { <province> <value> }`：可多行（`10-Poland.txt` 第 10-15 行）。
- **日期块**：`1936.1.1 = { ... }`、`1938.10.25 = { ... }`，里面可以写 effect：

```pdx
# history/states/1032 - Yanan.txt 第 14-22、48-55 行
history = {
	owner = PRC
	add_core_of = PRC
	add_core_of = CHI

	1936.1.1 = {
		IF = {
			limit = { has_dlc = "No Compromise, No Surrender" }
			transfer_state_to = XIC
			add_core_of = XIC
		}
	}

	1938.10.25 = {
		owner = PRC
		controller = PRC
		add_victory_points = {
			province = 8049
			value = 2
		}
	}
}
```

> 日期块里可以写**任何 state/country 作用域的 effect**（`transfer_state_to`、`add_victory_points`、`set_state_category`…），这是做「历史上州易手」的标准做法。

---

## 3. `state_category` 与建筑槽位

`common/state_category/*.txt`（1.19.x 共 13 个文件，每个文件一个类别）：

| 类别 | `local_building_slots` | 典型用途 |
|---|---|---|
| `wasteland` | 0 | 荒地 |
| `enclave` | 0 | 飞地（如 Gibraltar、西柏林式） |
| `tiny_island` | 0 | 极小岛 |
| `small_island` | 1 | 小岛 |
| `pastoral` | 1 | 牧区 |
| `rural` | 2 | 农村 |
| `large_island` | 3 | 大岛 |
| `town` | 4 | 城镇 |
| `large_town` | 5 | 大镇 |
| `city` | 6 | 城市 |
| `large_city` | 8 | 大城市 |
| `metropolis` | 10 | 都会 |
| `megalopolis` | 12 | 巨型都市 |

```pdx
# common/state_category/town.txt 全文
state_categories={
	town = {
		local_building_slots = 4
		color = { 200 200 0 }
	}
}
```

- `local_building_slots` 是**共享槽位数**（`shares_slots = yes` 的建筑共用这些槽，见 [buildings.md](buildings.md)）。
- 国策可以通过 `add_extra_state_shared_building_slots` 临时加槽（见第 6 节）。
- 也可以给单个州用 `buildings_max_level_factor` 调整上限系数（原版 `1032 - Yanan.txt`）。

---

## 4. 建筑在州文件里怎么写

`buildings` 块支持两种层级（`common/buildings/00_buildings.txt` 顶部注释说明：设置了 `province_max` 的是省级建筑）：

```pdx
buildings = {
	# ① 州级建筑：直接写等级
	infrastructure = 4
	arms_factory = 6
	industrial_complex = 2
	anti_air_building = 2
	air_base = 5

	# ② 省级建筑：以省 ID 为键
	11374 = {
		naval_base = 10
		naval_headquarters = {
			level = 1
			allowed = { has_dlc = "No Compromise, No Surrender" }
		}
	}

	# ③ 地标建筑（1.19，需 DLC）：也是省级，且可以带 allowed/level
	6103 = {
		landmark_big_ben = {
			allowed = { has_dlc = "Gotterdammerung" }
			level = 1
		}
	}
}
```
（原版证据：`history/states/126-Greater London Area.txt` 第 12-38 行）

- 州级 vs 省级由 `common/buildings/00_buildings.txt` 里该建筑是否有 `level_cap { province_max = N }` 决定。
- 建筑种类与成本见 [buildings.md](buildings.md)。

---

## 5. 新建一个州的完整步骤

> 目标：新增 state `1082`，包含 2 个省（`13414`、`13415`），归 `SWE`。

### 步骤 1：先有省

新省必须先存在（见 [04_world/map-structure.md](map-structure.md) 第 7 节：改 `provinces.bmp` + `definition.csv` + `terrain.bmp` + 战略区）。**没有省就没有州。**

### 步骤 2：写州文件

```pdx
# 路径：<mod>/history/states/1082-HHO_New_State.txt
state = {
	id = 1082
	name = "STATE_1082"
	manpower = 150000

	state_category = rural

	resources = {
		steel = 4
	}

	history = {
		owner = SWE
		add_core_of = SWE

		victory_points = {
			13414 5
		}

		buildings = {
			infrastructure = 2
			arms_factory = 1
			air_base = 1
		}
	}

	provinces = {
		13414 13415
	}

	local_supplies = 2.0
}
```

### 步骤 3：本地化（必需）

```yml
# localisation/simp_chinese/HHO_states_l_simp_chinese.yml（UTF-8 BOM）
l_simp_chinese:
 STATE_1082: "HHO 新州"
```
原版证据：`localisation/english/state_names_l_english.yml` 第 2 行 `STATE_1: "Corsica"`。

> 省名说明：1.19.x 原版 `localisation/english/province_names_l_english.yml` 只有 18 行（全是 `europe`/`asia` 这类大洲名），**没有 `PROV<id>` 这类省名 key**——HOI4 界面主要显示**州名**与**胜利点名**，省本身没有独立显示名。若需要给省命名，可用 effect `set_province_name`（`documentation/effects_documentation.md` 第 7623 行，`set_province_name = { id = <province id> name = <string> }`）⚠️ 其显示位置本机未验证。

### 步骤 4：把新省从战略区/补给区补上

- 把 `13414 13415` 加进某 `map/strategicregions/*.txt` 的 `provinces = { ... }`（否则补给/海军区域异常）。
- 补给区当前由引擎自动划分（见 [supply.md](supply.md)），一般不用手改。

### 步骤 5：初始部队/建筑如果想放在新州

- 初始部队：`history/units/<TAG>_<year>.txt` 的 `units = { division = { location = 13414 ... } }`（见 [../03_military/division-templates.md](../03_military/division-templates.md)）。
- 初始建筑：直接写在州文件 `history.buildings` 里。

### 步骤 6：验证

- 重启游戏；点开新省看名称/地形/归属/建筑。
- `logs/error.log` 搜 `1082` / `13414`（常见：province 不属于任何 state、state id 重复、loc 缺失）。

---

## 6. 国策 / 事件如何引用州

`documentation/effects_documentation.md` 里与州相关的 effect（都已确认存在）：

| effect | Scope | 用途 | 文档行 |
|---|---|---|---|
| `add_state_core` | COUNTRY | 给州加核心 | 2191 |
| `add_extra_state_shared_building_slots` | STATE | 加共享建筑槽 | 1267 |
| `add_building_construction` | STATE | 直接开工建造 | 839 |
| `build_railway` | any | 修铁路（可指定路径） | 2535 |
| `set_state_category` | STATE | 改州类别（改槽位数） | 7681 |
| `set_state_province_controller` | STATE | 改省内控制者 | 7759 |
| `transfer_state_to` | STATE | 转移州给某国 | 8332 |
| `add_victory_points` | any | 加胜利点 | 2455 |

**国策里的典型用法**（原版 `common/national_focus/argentina.txt` 第 157-172 行）：

```pdx
completion_reward = {
	random_core_state = {
		limit = {
			free_building_slots = {          # STATE scope trigger，见 triggers_documentation.md 第 2901 行
				building = arms_factory
				size > 0
				include_locked = yes
			}
			is_owned_and_controlled_by = ROOT
		}
		add_extra_state_shared_building_slots = 1
		add_building_construction = {
			type = arms_factory
			level = 1
			instant_build = yes
		}
	}
}
```

更多国策写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)；事件里改州见 [../02_content/events.md](../02_content/events.md)。

---

## 7. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 州定义 | `history/states/` | 1,081 文件（`<id>-<name>.txt`，也存在 `1032 - Yanan.txt` 这类带空格命名） | ❌（`history/` 全目录无 doc） |
| 州分类与槽位 | `common/state_category/` | 13 文件 | ❌ |
| 省注册表（校验 `provinces`） | `map/definition.csv` | 13,414 行 | ❌ |
| 省建筑等级修正（特殊地点） | `common/strategic_locations/` | 17 行 + `documentation.md` | ✅ |
| 州内建筑 | `common/buildings/00_buildings.txt` | 787 行 | ❌ |
| 州资源 | `common/resources/00_resources.txt` | 43 行 | ✅（4 行） |
| 脚本读写州 | `documentation/{effects,triggers}_documentation.md` | 222,533 / 180,523 B | ✅ |

**id 规则**：state id 与省 id、战略区 id 是三套独立编号；当前最大 state id = **1081**（实有 1,081 个州文件），新建从 **1082** 起。文件名里的序号只是给人读的，**引擎只认文件内容里的 `id` 字段**——所以带空格的 `1032 - Yanan.txt` 能正常加载；但 mod 里建议统一 `<id>-<name>.txt` 以便脚本处理。

- 新州同时要在 `map/definition.csv` 里有对应的省（`provinces` 列表），否则州里出现"幽灵省"。
- 只改 `history/states/` 不需要动 `map/`；新增省则两边都要改（见 [map-structure.md](map-structure.md)）。

## 8. 常见错误 / 自检清单

- [ ] `id` 唯一（当前最大 1081，新建从 1082 起）。
- [ ] `name` 有对应 loc key（`STATE_<id>`）。
- [ ] `state_category` 是 `common/state_category/` 里存在的类别（大小写敏感）。
- [ ] `provinces` 里的省在 `definition.csv` 存在，且**没有被其它州重复引用**。
- [ ] `provinces` 至少一个（空州会报错）。
- [ ] 省级建筑写在 `province_id = { ... }` 里，且该省属于本州。
- [ ] `victory_points` 的省属于本州。
- [ ] `owner` 的 TAG 在 `common/country_tags/` 存在。
- [ ] 新省已加入战略区。
- [ ] `impassable = yes` 的州不要放建筑/胜利点（原版也不放）。
- [ ] 改完重启；`logs/error.log` 搜 state id。
- [ ] 只有 `history/states` 的改动不需要动 `map/`；新增省则两边都要改。

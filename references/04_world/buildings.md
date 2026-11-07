---
title: 建筑（Buildings）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/buildings/00_buildings.txt
  - common/buildings/01_landmark_buildings.txt
  - common/state_category
  - history/states/126-Greater London Area.txt
  - interface/countrystateview.gfx
  - localisation/english/buildings_l_english.yml
  - documentation/triggers_documentation.md
  - common/strategic_locations/documentation.md
  - common/state_category
---

# 建筑（Buildings）

**一句话**：`common/buildings/` 定义「建筑类型」（成本、产量、上限、修正、图标），`history/states/` 决定「哪里有、几级」。建筑分**州级**与**省级**两种，槽位由 `state_category.local_building_slots` + `shares_slots` 共同决定。

---

## 1. 文件与加载

| 项 | 事实 |
|---|---|
| 目录 | `common/buildings/00_buildings.txt`（787 行，39 个建筑）+ `01_landmark_buildings.txt`（659 行，22 个地标） |
| 顶层块 | `buildings = { ... }` |
| 加载 | 启动时；无热重载 |
| 覆盖 | 同名文件整体替换；不同文件同建筑 ID → 后加载覆盖 |
| 本地化 | key = 建筑 ID（如 `arms_factory: "Military Factory"`，见 `localisation/english/buildings_l_english.yml` 第 5 行），另有 `_desc` |
| 图标 | `icon_frame = N` 取 `interface/countrystateview.gfx` 里 `GFX_buildings_strip`（`gfx/interface/buildings/building_icon_strip.dds`，**noOfFrames = 31**）的第 N 帧 |

> ⚠️ 1.19.x 原版 39 个建筑已把 31 帧用满（`icon_frame` 最大 31）。新增建筑时要**复用现有帧**，或替换 `building_icon_strip.dds` 并改 `noOfFrames`（会与其它 UI 冲突，风险高）。

---

## 2. 建筑列表（`common/buildings/00_buildings.txt`，按行号）

| 行 | 建筑 | 类别 |
|---|---|---|
| 34 | `infrastructure` | 州级基础（`infrastructure = yes`，上限 `state_max = 5`） |
| 55 | `arms_factory` | 军工（`military_production = 1`） |
| 70 | `industrial_complex` | 民用（`general_production = 1`） |
| 84 | `air_base` | 空军基地（`air_base = yes`） |
| 98 | `supply_node` | **补给枢纽**（`supply_node = yes`，`province_max = 1`） |
| 115 | `rail_way` | 铁路（`per_level_extra_cost = 130`，`province_max = 1`） |
| 126 | `naval_facility` | 海军特殊项目设施（`specialization = { specialization_naval }`） |
| 151 | `naval_base` | 海军基地（`is_port = yes`，`only_costal = yes`，`province_max = 10`） |
| 170 | `bunker` | 陆上要塞（`land_fort = 1`） |
| 185 | `coastal_bunker` | 海岸要塞（`naval_fort = 1`） |
| 201 | `stronghold_network` | 要塞网（Gotterdammerung DLC） |
| 226 | `dockyard` | 船厂（`naval_production = 1`，`only_costal = yes`） |
| 244 | `anti_air_building` | 州防空（`air_defence = 1`） |
| 259 | `synthetic_refinery` | 合成炼油厂（`local_resources_rubber = 1`） |
| 283 | `fuel_silo` | 油库 |
| 303 | `radar_station` | 雷达站 |
| 318 | `mega_gun_emplacement` | 巨炮阵地 |
| 339 | `rocket_site` | 火箭基地 |
| 357 | `naval_supply_hub` | 海军补给枢纽 |
| 377 | `naval_headquarters` | 海军总部 |
| 403 | `nuclear_reactor` | 核反应堆 |
| 434 | `nuclear_reactor_heavy_water` | 重水反应堆 |
| 464 | `commercial_nuclear_reactor` | 商用核反应堆 |
| 501 | `nuclear_facility` | 核特殊项目设施 |
| 535 | `air_facility` | 空军特殊项目设施 |
| 559 | `land_facility` | 陆军特殊项目设施 |
| 583 | `dam` / 611 `dam_mountain` / 639 `cataract_dam_mountain` | 水坝（发电） |
| 667 | `canal_kiel` / 690 `canal_panama` | 运河 |
| 715 | `energy_infrastructure` | **电力基础设施（1.19 新）** |
| 734 | `industrial_infrastructure` | 工业基础设施 |
| 755-782 | `nuclear_reactor_spawn` / `special_project_facility_spawn` / `rocket_site_spawn` / `naval_base_spawn` / `dam_spawn` / `locks_spawn` | **spawn 占位建筑**（只用于地图模型定位，不显示/不可造） |

地标建筑（`01_landmark_buildings.txt`）：`landmark_big_ben`、`landmark_colosseum`、`landmark_eiffel_tower`、`landmark_kremlin`、`landmark_statue_of_liberty`、`landmark_taj_mahal`、`landmark_forbidden_city`、`landmark_hagia_sophia`、`landmark_great_wall_section` 等 22 个。

---

## 3. 字段全表（以原版真实建筑为例）

```pdx
# common/buildings/00_buildings.txt 第 55-68 行
arms_factory = {
	show_on_map = 6                  # 地图模型显示规则：省级建筑=每省数量，州级建筑=每州数量
	base_cost = 7200                 # 基础建造 IC 成本
	base_cost_conversion = 4000      # 转换（民用→军用）成本
	military_production = 1          # 每个等级提供的军工产能
	disabled_in_dmz = yes            # 非军事区禁止建造
	icon_frame = 2
	value = 8                        # 建造队列 AI 权重 / 价值
	infrastructure_construction_effect = yes   # 受基建影响建造速度
	level_cap = {
		shares_slots = yes           # ★占用州共享槽
		state_max = 20               # 每州最多 20 级
	}
}
```

| 字段 | 含义 | 例 |
|---|---|---|
| `show_on_map` / `show_on_map_meshes` | 地图模型密度 | `infrastructure show_on_map` 无；`naval_base show_on_map = 1 show_on_map_meshes = 3` |
| `base_cost` / `per_level_extra_cost` | 基础成本 / 每级递增 | `naval_base base_cost = 5000 per_level_extra_cost = 1000` |
| `base_cost_conversion` / `per_controlled_building_extra_cost` | 转换成本 / 控制数量加成成本 | `naval_facility per_controlled_building_extra_cost = 6000` |
| `military_production` / `general_production` / `naval_production` | 每级产能 | 见上表 |
| `infrastructure` / `air_base` / `supply_node` / `is_port` / `anti_air` / `land_fort` / `naval_fort` / `refinery` | 功能类型标记（决定系统怎么用它） | 见上表 |
| `level_cap { state_max / province_max / shares_slots }` | ★上限与是否共享槽 | `province_max = N` 同时意味着「这是省级建筑」 |
| `only_costal` | 只能建在沿海省 | `naval_base`、`dockyard`、`coastal_bunker` |
| `disabled_in_dmz` | 非军事区不可建 | `arms_factory`、`bunker`、`supply_node` |
| `damage_factor` | 被战略轰炸的受损系数 | `air_base damage_factor = 0.5`；`naval_facility damage_factor = 0`（不可被常规轰炸） |
| `infrastructure_construction_effect` | 建造速度受基建影响 | 绝大多数建筑都有 |
| `allied_build` / `always_shown` / `only_display_if_exists` / `hide_if_missing_tech` | 可见性/盟友可建 | `air_base allied_build = yes` |
| `tags = { ... }` | 分类标签 | `naval_building_tag`、`facility`、`supply_building` |
| `country_modifiers { enable_for_controllers { ... } modifiers { ... } }` | ★给国家的修正（可限定控制者） | `infrastructure max_fuel_building = 1.5`；地标 `landmark_big_ben` 限 ENG |
| `state_modifiers { ... }` | 给州的修正 | `stronghold_network` 的 `local_supplies_for_controller = 0.1` |
| `spawn_point` | 地图模型挂点 | `naval_base spawn_point = naval_base_spawn` |
| `specialization` | 特殊项目设施专精 | `naval_facility specialization = { specialization_naval }` |
| `need_supply` / `need_detection` / `detecting_intel_type` | 特殊项目设施需求 | `naval_facility` |
| `repair_speed_factor` / `missing_tech_loc` / `disable_grow_animation` | 修复速度 / 缺科技提示 / 关闭生长动画 | 地标用 `@landmark_repair_speed_factor = 0.15` |
| `local_resources_<resource> = N` | 给州加资源产出 | `synthetic_refinery local_resources_rubber = 1` |
| `affects_energy` | 影响电力 | `infrastructure affects_energy = yes` |
| `dlc_allowed = { has_dlc = ... }` | DLC 门控 | 地标 `has_dlc = Gotterdammerung`；`stronghold_network` 同 |
| `is_buildable = no` | 不可建造（只能由脚本放置） | 地标 |
| `special_icon` / `drawn_at_distance` | 地标专用图标 / 远距离也绘制 | 地标 |

---

## 4. 槽位规则（新手最容易算错）

1. **州槽位** = `state_category.local_building_slots`（见 [states.md](states.md) 第 3 节表格）。
2. **共享槽**：`level_cap { shares_slots = yes }` 的建筑（军工厂/民用厂/船厂/合成炼油厂/要塞网…）**共用**这些槽位——一个军工厂占 1 槽，民用厂也占 1 槽。
3. **非共享建筑**：有独立上限（如 `air_base state_max = 10`、`infrastructure state_max = 5`、`anti_air_building state_max = 5`）**不占**共享槽。
4. **省级建筑**：有 `province_max` 的建筑（`naval_base`、`bunker`、`coastal_bunker`、`supply_node`、`rail_way`…）按省单独计算。
5. **额外槽**：聚焦/事件用 `add_extra_state_shared_building_slots`（STATE scope，`documentation/effects_documentation.md` 第 1267 行）临时加槽。
6. **查询空槽**：trigger `free_building_slots = { building = <type> size > 0 include_locked = yes }`（STATE scope，`documentation/triggers_documentation.md` 第 2901 行）。

```pdx
# 原版国策里的标准「找有槽的州建厂」写法
# common/national_focus/argentina.txt 第 157-172 行
random_core_state = {
	limit = {
		free_building_slots = {
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
```

---

## 5. 地标建筑（Landmark，1.19）

```pdx
# common/buildings/01_landmark_buildings.txt 第 36-63 行（大本钟）
landmark_big_ben = {
	dlc_allowed = { has_dlc = Gotterdammerung }
	show_on_map = 1
	base_cost = 20000
	damage_factor = 0                  # 不可被常规战略轰炸
	icon_frame = 22
	value = 5

	is_buildable = no                  # 不可建造，只能脚本/历史放置
	disable_grow_animation = yes
	spawn_point = landmark_spawn
	repair_speed_factor = @landmark_repair_speed_factor   # 文件顶部 @ = 0.15
	only_display_if_exists = yes
	special_icon = GFX_big_ben_icon_small
	level_cap = { province_max = 1 }
	always_shown = yes
	drawn_at_distance = yes
	show_modifier = yes
	country_modifiers = {
		enable_for_controllers = { ENG }     # ★只有 ENG 控制时生效
		modifiers = {
			political_power_factor = 0.03
		}
	}
}
```

放置方式（省级，带 DLC 门控）：

```pdx
# history/states/126-Greater London Area.txt 第 31-38 行
6103 = {
	landmark_big_ben = {
		allowed = { has_dlc = "Gotterdammerung" }
		level = 1
	}
}
```

---

## 6. 最小可跑示例：新增一个「HHO 国家研究院」建筑

```pdx
# 路径：<mod>/common/buildings/HHO_buildings.txt
buildings = {

	HHO_research_institute = {
		show_on_map = 1
		base_cost = 15000
		icon_frame = 13                  # 复用原版某帧（避免动 31 帧的 strip）
		value = 6
		infrastructure_construction_effect = yes
		disabled_in_dmz = yes

		level_cap = {
			shares_slots = yes           # 占州共享槽
			state_max = 2
		}

		state_modifiers = {
			local_building_slots_factor = 0.1     # 合法：原版 00_buildings.txt 顶部注释示例与多处使用
			local_supplies_for_controller = 0.05  # 合法：stronghold_network 的 state_modifiers 有用例
		}
	}
}
```

> 说明：`state_modifiers` 里只能写 **state scope** 的 modifier；`country_modifiers.modifiers` 里写 country scope。哪些 modifier 属于哪个 scope，以 `documentation/modifiers_documentation.md` 的分组标题为准（该文件按 `## Modifiers for scope STATE` 这类小节组织）。

- 本地化：`HHO_research_institute: "HHO 国家研究院"` + `_desc`。
- 在州里放一个：在 `history/states/<你的州>.txt` 的 `history.buildings` 加 `HHO_research_institute = 1`。
- 国策建它：`add_building_construction = { type = HHO_research_institute level = 1 instant_build = yes }`。
- 图标：复用 `icon_frame` 即可；要自制图标需处理 `GFX_buildings_strip`（见第 1 节 ⚠️）。

---

## 7. 通过国策 / 事件引用

| 需求 | effect | 文档行 |
|---|---|---|
| 直接建造 | `add_building_construction = { type = ... level = ... instant_build = yes }` | 839 |
| 加共享槽 | `add_extra_state_shared_building_slots = N` | 1267 |
| 修铁路 | `build_railway = { ... }` | 2535 |
| 破坏建筑 | `damage_building = { ... }` | 3374 |
| 查询空槽 | trigger `free_building_slots` | — |

写法示例见第 4 节；国策结构见 [../02_content/focus-trees.md](../02_content/focus-trees.md)。

---

## 8. 1.19 与旧教程的差异（实测）

1. **新增大量建筑**：`energy_infrastructure`（电力）、`industrial_infrastructure`、`dam` 家族、`stronghold_network`（Gotterdammerung）、`naval_headquarters`、`naval_supply_hub`、`naval_facility`/`land_facility`/`air_facility`/`nuclear_facility`（特殊项目设施）、各种 `*_spawn` 占位建筑。
2. **`level_cap` 取代旧字段**：旧教程常用 `state_max` / `province_max` 直接写在建筑顶层；现在都要包在 `level_cap = { ... }` 里（本机 39 个建筑全部如此）。
3. **`shares_slots` 显式化**：哪些建筑共用州槽现在是数据字段，不再靠硬编码。
4. **地标建筑系统**（`01_landmark_buildings.txt` + `special_icon` + `drawn_at_distance`）是较新内容，旧教程没有。
5. **`specialization` / `need_supply` / `need_detection`** 是特殊项目（Special Projects）系统的建筑字段。

---

## 9. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 建筑定义 | `common/buildings/00_buildings.txt` | 787 行 | ❌ |
| 地标建筑 | `common/buildings/01_landmark_buildings.txt` | 659 行 | ❌ |
| 州分类（决定槽位） | `common/state_category/` | 13 文件（city / enclave / large_city / large_island / large_town / megalopolis / metropolis / pastoral / rural / small_island / tiny_island / town / wasteland） | ❌ |
| **特殊地点（省建筑等级修正）** | `common/strategic_locations/` | `strategic_locations.txt` 17 行 + `documentation.md` 23 行 | ✅ `documentation.md`（唯一权威） |
| 州内建筑实例 | `history/states/*.txt` 的 `buildings = { }` | 1,081 文件 | ❌ |
| 建筑坐标（生成物） | `map/buildings.txt` | 生成，勿手写 | ❌ |
| 建筑图标条 | `interface/countrystateview.gfx` 的 `GFX_buildings_strip` | — | ❌ |

### 9.1 `strategic_locations`：给省建筑加/减上限（旧教程完全没有）

1.19 的 `strategic_locations` 不是"地标"，而是**省建筑等级的额外修正**：

```
# common/strategic_locations/strategic_locations.txt
natural_harbor = { naval_base = 2 }        # 该省海军基地 +2 上限
defensive_chokepoint = { bunker = 2 }      # 地堡 +2
defensible_coastline = { coastal_bunker = 2 }
favorable_approach = { air_base = 2 }
```

施加方式是 effect（官方 `documentation.md` 写的是 `strategic_location_building`，示例为 state scope 下 `strategic_location = { <名> = <省 id> }`）：

```
555 = {                        # state scope
	strategic_location = {
		natural_harbor = 3258   # province id
	}
}
```

用途：给历史港口/隘口"加建筑位"而不改 `state_category`；写 `-1`/`-2` 可削减上限。需求是"某地该多建几个港口/地堡"时，优先它而不是新分类。

## 10. 常见错误 / 自检清单

- [ ] 建筑 ID 唯一；有 `建筑ID` 与 `建筑ID_desc` 两条 loc。
- [ ] `level_cap` 写法正确（`state_max` / `province_max` / `shares_slots` 都在里面）。
- [ ] 省级建筑必须给 `province_max`，否则会被当成州级。
- [ ] `icon_frame` 在 1..31 内（`GFX_buildings_strip` 的帧数）。
- [ ] `state_modifiers` / `country_modifiers` 里的 modifier 名在 `documentation/modifiers_documentation.md` 中存在。
- [ ] DLC 内容写 `dlc_allowed = { has_dlc = ... }`。
- [ ] 州里放置省级建筑时用 `province_id = { ... }`，省必须属于该州。
- [ ] 只有省级建筑能在 `spawn_point` 指定的模型挂点显示。
- [ ] 改完重启；`logs/error.log` 搜建筑 ID。

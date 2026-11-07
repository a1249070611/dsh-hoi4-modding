---
title: 地形（Terrain）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/terrain/00_terrain.txt
  - map/terrain.bmp
  - map/default.map
  - map/definition.csv
  - common/weather.txt
  - map/seasons.txt
  - map/strategicregions/1-Southern England.txt
  - common/units/engineer.txt
  - common/weather.txt
---

# 地形（Terrain）

**一句话**：地形分两层——**类别（category，决定战斗宽度/移动/修正，在 `common/terrain/00_terrain.txt`）** 与 **图形地形（graphical terrain，把 `terrain.bmp` 的调色板索引映射到某个类别 + 贴图，也在同一个文件）**。1.19 把地形定义从旧版 `map/terrain.txt` 搬到了 `common/terrain/00_terrain.txt`。

---

## 1. 文件位置（1.19 变更）

| 内容 | 路径 | 说明 |
|---|---|---|
| 地形类别 + 图形地形映射 | `common/terrain/00_terrain.txt`（356 行） | ★核心 |
| 地形贴图/图集 | `map/terrain/*.dds` | `atlas0..2.dds`、`colormap_*`、`mud_*`、`snow_*`、`ice_*` 等 |
| 地形位图 | `map/terrain.bmp`（5632×2048，8-bit 索引色） | 每像素一个调色板索引 |
| 天气对地形的修正 | `common/weather.txt` | `terrain_modifiers` + `settings` |
| 季节（视觉） | `map/seasons.txt` | 季节日期范围 + HSV/色彩平衡 |
| 省的地形 | `map/definition.csv` 第 7 列 | ⚠️ 与 `terrain.bmp` 的关系见第 5 节 |

---

## 2. `categories`：地形类别（战斗/移动在这里）

`common/terrain/00_terrain.txt` 顶部是 `categories = { ... }`，1.19.x 共有 **14 个类别**：

`unknown`、`ocean`、`lakes`、`forest`、`hills`、`mountain`、`plains`、`urban`、`jungle`、`marsh`、`desert`、`water_fjords`、`water_shallow_sea`、`water_deep_ocean`

### 2.1 陆战地形字段（以 forest / mountain 为例）

```pdx
# common/terrain/00_terrain.txt 第 29-53 行
forest = {
	color = { 89 199 85 }              # 类别颜色（用于 UI/调试，不是位图索引）
	movement_cost = 1.5
	#combat_width = -0.20              # ← 旧写法的百分比被注释掉了
	combat_width = 60                  # ★1.19：绝对战斗宽度
	combat_support_width = 30          # ★1.19：支援宽度（团级支援/支援连使用）
	ai_terrain_importance_factor = 5.0
	match_value = 5
	sound_type = forest
	buildings_max_level = {
		bunker = 4
		coastal_bunker = 6
	}
	units = {
		attack = -0.15                 # 攻方在此地形的攻击修正
		#movement = -0.2
	}
	enemy_army_bonus_air_superiority_factor = -0.1
	supply_flow_penalty_factor = 0.08
	truck_attrition_factor = 0.2
}

# 第 80-105 行
mountain = {
	color = { 157 192 208 }
	movement_cost = 2.0
	attrition = 0.3
	combat_width = 50
	combat_support_width = 25
	ai_terrain_importance_factor = 10.0
	match_value = 10
	sound_type = desert
	buildings_max_level = { bunker = 4 coastal_bunker = 6 }
	units = { attack = -0.5 }
	enemy_army_bonus_air_superiority_factor = -0.10
	supply_flow_penalty_factor = 0.12
	truck_attrition_factor = 1.0
}
```

### 2.2 陆战地形数值总表（本机实测）

| 地形 | `combat_width` | `combat_support_width` | `movement_cost` | `units.attack` | 其它 |
|---|---|---|---|---|---|
| plains | 70 | 35 | 1.0 | 无 | `ai_terrain_importance_factor 0.1` |
| forest | 60 | 30 | 1.5 | -0.15 | `supply_flow_penalty_factor 0.08` |
| hills | 70 | 35 | 1.5 | -0.25 | |
| mountain | 50 | 25 | 2.0 | -0.50 | `attrition 0.3` |
| urban | 80 | 40 | 1.2 | -0.30 | `enemy_army_bonus_air_superiority_factor -0.50`，`supply_flow_penalty_factor -0.2` |
| jungle | 60 | 30 | 1.5 | -0.30 | `attrition 0.2` |
| marsh | 50 | 25 | 2.0 | -0.40 | `attrition 0.35`、`sickness_chance 1.0`、`truck_attrition_factor 4.0` |
| desert | 70 | 35 | 1.05 | 无 | `attrition 0.15`、`sickness_chance 1.0`、`truck_attrition_factor 0.5` |

### 2.3 海战地形字段

海战类别（`ocean`、`lakes`、`water_fjords`、`water_shallow_sea`、`water_deep_ocean`）用另一组字段：

```pdx
# 第 12-20 行（ocean）
ocean = {
	naval_terrain = yes
	color = { 40 83 176 }
	movement_cost = 1.0
	is_water = yes
	sound_type = sea
	naval_mine_hit_chance = -0.75
	minimum_seazone_dominance = 250
}

# 第 222-265 行（water_fjords，节选）
water_fjords = {
	naval_terrain = yes
	is_water = yes
	sound_type = sea
	destroyer = { units = { attack = -0.2 movement = -0.2 defence = -0.2 } navy_fuel_consumption_factor = 0.2 }
	heavy_cruiser = { units = { attack = -0.2 movement = -0.2 defence = -0.2 } navy_fuel_consumption_factor = 0.2 }
	carrier = { units = { attack = -0.2 movement = -0.2 defence = -0.2 } navy_fuel_consumption_factor = 0.2 }
	navy_visibility = -0.2
	positioning = -0.15
	minimum_seazone_dominance = 100
}

# 第 267-280 行（water_shallow_sea）
water_shallow_sea = {
	naval_terrain = yes
	is_water = yes
	submarine = { navy_visibility = 0.33 }
	positioning = -0.05
	naval_mine_hit_chance = -0.5
	minimum_seazone_dominance = 100
}

# 第 282-312 行（water_deep_ocean）
water_deep_ocean = {
	naval_terrain = yes
	is_water = yes
	destroyer = { units = { attack = -0.2 movement = -0.2 defence = -0.2 } }
	light_cruiser = { units = { attack = -0.1 movement = -0.1 defence = -0.1 } }
	submarine = { navy_visibility = -0.15 units = { movement = -0.25 } }
	naval_mine_hit_chance = -0.95
	minimum_seazone_dominance = 250
}
```

海战地形字段：`naval_terrain`、`is_water`、`naval_mine_hit_chance`、`minimum_seazone_dominance`、`navy_visibility`、`positioning`、按船种分的 `{ units = { attack/movement/defence } navy_fuel_consumption_factor }`。

---

## 3. 图形地形映射（`terrain.bmp` 调色板 → 类别）

同一文件下半部分是 `terrain = { ... }`（第 323-356 行，前文 [04_world/map-structure.md](map-structure.md) 第 5 节有全文）。

```pdx
terrain_0       = { type = plains   color = { 0 }  texture = 1 }
terrain_1       = { type = forest   color = { 1 }  texture = 4 }
desert_mountain = { type = hills    color = { 2 }  texture = 3 }
forest_13       = { type = urban    color = { 13 } texture = 10 spawn_city = yes }
snow_16         = { type = mountain color = { 16 } texture = 11 perm_snow = yes }
plains_17       = { type = plains   color = { 19 } texture = 0  perm_snow = yes }
```

- **键名**（`terrain_0`/`desert_mountain`/…）是任意标识，**真正起作用的是 `color = { N }`**：它等于 `terrain.bmp` 的**调色板索引**。
- `type` → `categories` 里的地形类别（决定战斗/移动）。
- `texture` → `map/terrain/atlas*.dds` 里的贴图编号。
- `spawn_city = yes`：自动生成城市模型；`perm_snow = yes`：永久积雪。

> 所以「某块地是什么地形」= `terrain.bmp` 该像素的**调色板索引** → 在 `terrain = {}` 里查 `color = { N }` → 得到 `type`。
> `terrain.bmp` 是 8-bit 索引色 PNG 时代最常见的坑：用图像软件编辑时必须**保留原调色板/索引**，否则颜色重排后整张地图的地形全变。

---

## 4. 天气与季节

### 4.1 `common/weather.txt`

```pdx
# common/weather.txt 第 1-43 行
terrain_modifiers = {
  no_phenomenon = { }
  mud = {
    terrain = { type = "mountain" value = -0.3 }
    terrain = { type = "plains"   value = 0.5 }
    terrain = { type = "marsh"    value = 0.9 }
    terrain = { type = "desert"   value = 0.1 }
    terrain = { type = "jungle"   value = 0.2 }
  }
  rain_light  = { terrain = { type = "jungle" value = 0.2 } }
  rain_heavy  = { terrain = { type = "jungle" value = 0.2 } }
  snow = {
  	terrain = { type = "mountain" value = 0.8 }
  	terrain = { type = "desert"   value = -1.0 }
    terrain = { type = "urban"    value = -0.4 }
  }
  blizzard = { ... }
  sandstorm = { terrain = { type = "desert" value = 0.8 } terrain = { type = "mountain" value = -1.0 } }

  temperature = {
    terrain = { type = "mountain" value = -7.0 }
    terrain = { type = "hills"    value = -3.0 }
    terrain = { type = "forest"   value = -1.0 }
    terrain = { type = "urban"    value = 3.0 }
    terrain = { type = "jungle"   value = 5.0 }
  }
}

settings = {
  temperature = {
    temperature_variation = 2.0
    max_temperature_change = 6.0
    temperature_neighbor_smoothing = 0.3
    weather_extreme_cold = { -100.0 -12.0 }
    weather_very_cold    = { -12.0 -4.0 }
    weather_very_hot     = { 20.0 28.0 }
    weather_extreme_hot  = { 28.0 100.0 }
  }
  mud = {
    water_gain_on_rain_light = 0.5
    water_gain_on_rain_heavy = 1.8
  }
  ...
}
```

- 文件头注释：`value` 在大多数元素里是**概率增量**，只有 `temperature` 里是**摄氏度增量**。
- 天气的**时段与基础概率**在**每个战略区**里配（`map/strategicregions/*.txt` 的 `weather.period`，见 [04_world/strategic-regions.md](strategic-regions.md)）。
- 天气对战斗的影响（mud/snow 减速等）由各自的 modifier 系统给出，查 `documentation/modifiers_documentation.md`。

### 4.2 `map/seasons.txt`

季节视觉（HSV/色彩平衡），1.19.x 有 `winter/spring/summer/autumn` + `tree_*` 8 个树周期。纯视觉，不影响战斗。

---

## 5. 省的地形到底由谁决定？（⚠️ 重要不确定点）

本机有两处数据，且**没有官方文档说明优先级**：

1. `map/definition.csv` 第 7 列（实测值：`ocean/plains/forest/mountain/hills/desert/jungle/urban/marsh/lakes/unknown`）
2. `map/terrain.bmp` 调色板索引 → `common/terrain/00_terrain.txt` 的 `terrain = {}`

**实测观察**：两处大体一致（`urban` 省都是城市省；`ocean` 省都是海）。原版同时维护两份数据，说明可能一处是「初始/权威」、一处是「图形」。

**安全做法**：
- 改地形时**两处一起改**（`definition.csv` 第 7 列 + `terrain.bmp` 索引）。
- 改完在游戏里点开该省 tooltip 看地形名与战斗修正，做最终验证。
- 若只改一处，记录你的实测结果并标注 ⚠️。

---

## 6. 最小可跑示例

### 例 A：改森林的战斗宽度（不动地图）

```pdx
# 路径：<mod>/common/terrain/00_terrain.txt
# ⚠️ 整文件替换语义：必须复制原版全文，只改目标字段
categories = {
	forest = {
		color = { 89 199 85 }
		movement_cost = 1.5
		combat_width = 45              # 原版 60
		combat_support_width = 22      # 原版 30
		ai_terrain_importance_factor = 5.0
		match_value = 5
		sound_type = forest
		buildings_max_level = { bunker = 4 coastal_bunker = 6 }
		units = { attack = -0.15 }
		enemy_army_bonus_air_superiority_factor = -0.1
		supply_flow_penalty_factor = 0.08
		truck_attrition_factor = 0.2
	}
	# ……其余 13 个类别 + 下方 terrain = {} 全部原样保留
}
```

### 例 B：新增一种图形地形（复用已有类别）

```pdx
# 路径：<mod>/common/terrain/00_terrain.txt（追加到 terrain = {} 里）
# 前提：terrain.bmp 的调色板第 40 号索引存在且未被占用（8-bit 最多 256 色）
terrain = {
	# ……原版 26 条全部保留
	HHO_volcanic = { type = mountain color = { 40 } texture = 11 }
}
```

- `type = mountain` 表示它沿用 mountain 的战斗/移动规则；
- 若想让火山有独立规则，需在 `categories` 里加 `HHO_volcanic = { ... }` 再引用；
- `terrain.bmp` 调色板必须真有第 40 号索引（用图像工具查看调色板）。

### 例 C：让「城市」地形更利于防守（改类别）

```pdx
categories = {
	urban = {
		color = { 120 120 120 }
		movement_cost = 1.2
		ai_terrain_importance_factor = 4.0
		combat_width = 60              # 原版 80
		combat_support_width = 30
		match_value = 4
		sound_type = plains
		buildings_max_level = { bunker = 5 coastal_bunker = 6 }
		units = { attack = -0.45 }     # 原版 -0.3
		enemy_army_bonus_air_superiority_factor = -0.50
		supply_flow_penalty_factor = -0.2
	}
}
```

---

## 7. 地形如何被其它系统引用

- **子单元的地形修正**：`common/units/engineer.txt` 等用 `forest = { defence = 0.25 }`、`mountain = { ... }` 这种块，键名必须与 `categories` 一致；另有虚拟地形 `fort` / `river` / `amphibious`。见 [../03_military/units.md](../03_military/units.md)。
- **战术的触发**：`is_fighting_in_terrain = urban`、`has_terrain = forest`（见 [../03_military/land-combat.md](../03_military/land-combat.md)）。
- **建筑上限**：`buildings_max_level = { bunker = N coastal_bunker = M }` 限制该地形上的要塞等级（`common/buildings/00_buildings.txt` 的 `bunker`/`coastal_bunker` 有 `province_max`）。
- **补给/卡车**：`supply_flow_penalty_factor`、`truck_attrition_factor` 影响补给流与卡车损耗（见 [supply.md](supply.md)）。
- **天气**：`common/weather.txt` 的 `terrain_modifiers` 按地形类型调天气概率。

### 7.1 国策 / 事件怎么用「地形」

国策与事件不能改地形数据，但可以**按地形做条件**与**按地形给加成**：

```pdx
# 在国策的 available / trigger 里判断地形（COUNTRY scope）
available = {
	has_terrain = mountain        # triggers_documentation.md 第 4941-4949 行：COUNTRY scope
}
```
> scope 注意：`has_terrain` 是 **COUNTRY**（「国家是否拥有该地形的省」），`is_fighting_in_terrain` 是 **COMBATANT**（「战斗发生在什么地形」，第 5561 行）。想在战术里判断地形用后者。

- 战斗中判断地形：`is_fighting_in_terrain`（`documentation/triggers_documentation.md` 第 5561 行）。
- 国策/事件结构见 [../02_content/focus-trees.md](../02_content/focus-trees.md)、[../02_content/events.md](../02_content/events.md)。
- 想「给某地形的部队加成」：用国策给 `army_...` modifier，或改子单元的地形块（见 [../03_military/units.md](../03_military/units.md)）。

---

## 8. 1.19 与旧教程的差异（实测）

1. **地形定义搬到 `common/terrain/00_terrain.txt`**（旧教程写 `map/terrain.txt`）。
2. **`combat_width` 从百分比（-0.20 之类）改成绝对值（50~80）**，旧写法在本机被 `#` 注释保留作参考（第 32、58、84 行等）。
3. **新增 `combat_support_width`**（支援宽度）、`supply_flow_penalty_factor`、`truck_attrition_factor`、`sickness_chance`、`ai_terrain_importance_factor`、`match_value`、`enemy_army_bonus_air_superiority_factor`。
4. **海战地形细分**：`water_fjords` / `water_shallow_sea` / `water_deep_ocean`，且按船种写修正。
5. **`climate.txt` 被注释掉**（`map/default.map`），由 `seasons.txt` + `common/weather.txt` + 战略区天气取代。

---

## 9. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 地形类别与修正 | `common/terrain/00_terrain.txt` | 356 行（`categories` + `terrain = { }` 图形映射） | ❌ |
| 图形地形集 | `map/terrain/` | 64 文件 | ❌ |
| 地形图 | `map/terrain.bmp` | 8-bit 索引色 | ❌ |
| 天气 | `common/weather.txt` | 162 行 | ❌ |
| 季节 | `map/seasons.txt` | 156 行 | ❌ |
| 天气单元坐标 | `map/weatherpositions.txt` | 生成 | ❌ |
| 大洲 | `map/continent.txt` | — | ❌ |
| 地形相关 trigger / modifier | `documentation/triggers_documentation.md`（`is_fighting_in_terrain`）、`modifiers_documentation.md` | 180,523 / 242,947 B | ✅ |

- **`common/terrain/` 与 `map/` 都无官方文档**：`categories` 里的 `combat_width`、`combat_support_width`、`movement_cost`、`sickness_chance` 等字段只能靠原版取值与实测，改完用 `-debug_mode` 复核。
- 官方文档覆盖的是"函数式语法"（trigger / effect / modifier），**不覆盖文件格式**——这是本目录多处标 ⚠️ 推测的原因。
- 地形改动一律整文件替换：`00_terrain.txt` 只有 1 个文件，丢一条 `terrain = { }` 映射就会让一类图形地形失效。

## 10. 常见错误 / 自检清单

- [ ] 改的是 `common/terrain/00_terrain.txt`，**不是** `map/terrain.txt`（后者不存在）。
- [ ] 整文件替换 → 必须保留原版全部 14 个类别 + 26 条 `terrain = {}` 映射。
- [ ] `terrain.bmp` 是 **8-bit 索引色**：编辑时保留调色板，不要转成 RGB。
- [ ] `terrain = {}` 里的 `color = { N }` 必须对应 `terrain.bmp` 真实存在的调色板索引。
- [ ] 子单元/战术里引用的地形名必须在 `categories` 里（含 `fort`/`river`/`amphibious` 虚拟地形）。
- [ ] 改 `combat_width` 会影响所有战斗，配合 [../03_military/land-combat.md](../03_military/land-combat.md) 一起看。
- [ ] `definition.csv` 第 7 列与 `terrain.bmp` 尽量同步修改（⚠️ 优先级无官方说明）。
- [ ] 改完重启；`logs/error.log` 搜地形名/`terrain`。

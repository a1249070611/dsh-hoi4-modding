---
title: 补给系统（Supply）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - map/supplyareas/1-SupplyArea.txt
  - map/supply_nodes.txt
  - map/railways.txt
  - common/buildings/00_buildings.txt
  - common/defines/00_defines.lua
  - history/states/1-France.txt
  - documentation/effects_documentation.md
  - map/buildings.txt
---

# 补给系统（Supply）

**一句话**：补给从**首都**出发，经**铁路**流到**补给枢纽（supply node）**，再靠卡车/马拉向部队分发；**补给区（supply_area）**是这条流的统计单位，**州**提供本地补给（人力/胜利点/基建）。1.19 下大部分补给区已由引擎自动划分，**旧教程的「每区一个 supplyareas 文件」改法失效**。

---

## 1. 补给相关的文件（1.19.x 实测）

| 文件 | 内容 | 备注 |
|---|---|---|
| `map/supplyareas/1-SupplyArea.txt` | **全文只有 1 个 `supply_area`** | 见下 |
| `map/supply_nodes.txt` | 727 行，`1 <province_id>` | 补给枢纽所在省 |
| `map/railways.txt` | `<level> <点数> <prov1> <prov2> ...` | 初始铁路 |
| `common/buildings/00_buildings.txt` | `supply_node`（第 98 行）、`rail_way`（115）、`naval_base`（151）、`naval_supply_hub`（357）、`infrastructure`（34） | 建筑定义 |
| `history/states/*.txt` | `local_supplies = <float>` | 州本地补给 |
| `common/defines/00_defines.lua` | `SUPPLY_*` / `CAPITAL_SUPPLY_*` / `RAILWAY_*` / `OUT_OF_SUPPLY_*` | 全部系数 |

### 1.1 ★1.19.x 的 `map/supplyareas/` 只剩 1 个文件

```
map/supplyareas/1-SupplyArea.txt（全文 8 行）
supply_area={
	id=1
	name="SUPPLYAREA_1"
	value=12
	states={
		5 85 763 807
	}
}
```

但本地化里有 `SUPPLYAREA_1` ~ `SUPPLYAREA_357`（`localisation/english/supply_area_names_l_english.yml`，357 条）。

> ⚠️ **结论（本地实测 + 推断）**：1.19.x 原版只显式定义 1 个补给区，其余 356 个由引擎按州/战略区自动生成。官方文档没有说明这一点，但「1 个文件 + 357 个 loc key」是硬证据。实践指导：
> - **改补给区**：优先改州文件（`local_supplies`）与补给枢纽/铁路，而不是找「补给区文件」。
> - **新增补给区**：目前没有可靠的脚本方式（旧教程的 `map/supplyareas/<id>.txt` 写法在原版里已不再出现）——如必须做，先做实验并在报告里标注 ⚠️。

---

## 2. 补给流模型（defines 证据）

`common/defines/00_defines.lua` 第 4267-4410 行（NSupply 段）：

| define | 值 | 含义 |
|---|---|---|
| `CAPITAL_SUPPLY_BASE` | 5.0 | 首都基础补给 |
| `CAPITAL_SUPPLY_CIVILIAN_FACTORIES` | 0.3 | 每座民用工厂给首都的补给 |
| `CAPITAL_SUPPLY_MILITARY_FACTORIES` | 0.6 | 每座军工厂 |
| `CAPITAL_SUPPLY_DOCKYARDS` | 0.4 | 每座船厂 |
| `CAPITAL_INITIAL_SUPPLY_FLOW` | 5.0 | 首都初始流量 |
| `NODE_INITIAL_SUPPLY_FLOW` | 2.8 | 补给枢纽初始流量 |
| `NAVAL_BASE_INITIAL_SUPPLY_FLOW` | 3.3 | 海军基地初始流量 |
| `FLOATING_HARBOR_INITIAL_SUPPLY_FLOW` | 2.6 | 浮动港 |
| `FLOATING_HARBOR_BASE_SUPPLY` | 15.0 | 浮动港基础补给 |
| `RAILWAY_BASE_FLOW` | 10.0 | 铁路基础流量 |
| `RAILWAY_FLOW_PER_LEVEL` | 5.0 | 每级铁路追加流量 |
| `RAILWAY_FLOW_PENALTY_PER_DAMAGED` | 5.0 | 每段受损铁路的流量惩罚 |
| `RAILWAY_MIN_FLOW` | 5.0 | 铁路流量下限 |
| `SUPPLY_FLOW_DROP_REDUCTION_AT_MAX_INFRA` | 0.30 | 满基建减少 30% 流量衰减 |
| `SUPPLY_FLOW_PENALTY_CROSSING_RIVERS` | 0.20 | 过河额外惩罚 |
| `SUPPLY_FLOW_DIST_LOGISTICS_FALLOFF_*` | 1.3 / 2.3 / 0.9 / 0.25 | 距离衰减曲线（sigmoid） |
| `SUPPLY_HUB_FULL_MOTORIZATION_BONUS` | 2.2 | 满摩托化的枢纽额外流量 |
| `SUPPLY_HUB_MOTORIZATION_TRUCK_COST` | 60.0 | 满摩托化所需卡车 |
| `SUPPLY_HUB_MOTORIZATION_MARGINAL_EFFECT_DECAY` | 1.6 | 摩托化边际收益衰减 |
| `INFRA_TO_SUPPLY` | 0.3 | 每级基建给本地补给 |
| `VP_TO_SUPPLY_BASE` | 0.2 | 胜利点基础补给 |
| `VP_TO_SUPPLY_BONUS_CONVERSION` | 0.05 | 胜利点等级折算 |
| `SUPPLY_BASE_MULT` | 0.2 | 补给基础值总乘数 |
| `SUPPLY_PORT_LEVEL_THROUGHPUT` | 3 | 每级海军基地的补给吞吐 |
| `NAVAL_SUPPLY_HUB_REDUCTION_FACTOR` | 0.0 | 海军补给枢纽对舰队需求的削减 |
| `SUPPLY_NEED_FACTOR` | 0.28（陆军段）/1（其它段） | 补给使用量乘数 |
| `SUPPLY_GRACE` | 72 | 部队自带 3 天补给 |
| `SUPPLY_PATH_MAX_DISTANCE` | 15 | 补给路径最大距离 |
| `SUPPLY_POINTS_PER_TRAIN` | 1.0 | 每列火车运的补给量 |

### 2.1 缺补给的惩罚

| define | 值 | 含义 |
|---|---|---|
| `SUPPLY_ORG_MAX_CAP` | 0.35 | 完全断补给时组织度上限系数 |
| `MAX_OUT_OF_SUPPLY_DAYS` | 30 | 30 天后达到最大惩罚 |
| `OUT_OF_SUPPLY_ATTRITION` | 0.20 | 最大损耗 |
| `OUT_OF_SUPPLY_SPEED` | -0.8 | 最大减速 |
| `OUT_OF_SUPPLY_MORALE` | -0.2 | 组织度恢复惩罚 |
| `COMBAT_SUPPLY_LACK_ATTACKER_ATTACK` | -0.25 | 缺补给进攻方攻击惩罚 |
| `COMBAT_SUPPLY_LACK_ATTACKER_DEFEND` | -0.65 | 缺补给进攻方防御惩罚 |
| `COMBAT_SUPPLY_LACK_DEFENDER_ATTACK` | -0.35 | 缺补给防御方攻击惩罚 |
| `COMBAT_SUPPLY_LACK_DEFENDER_DEFEND` | -0.15 | 缺补给防御方防御惩罚 |
| `NON_CORE_SUPPLY_SPEED` | -0.5 | 在非核心领土上的补给速度惩罚 |
| `MIN_SUPPLY_CONSUMPTION` | 0.05 | 最小补给消耗 |

### 2.2 本地补给的三个来源

州提供本地补给 = `state.local_supplies`（显式值）+ 人力折算（`AVAILABLE_MANPOWER_STATE_SUPPLY = 0.18`）× 人口 + 胜利点（`VP_TO_SUPPLY_BASE/CONVERSION`）+ 基建（`INFRA_TO_SUPPLY = 0.3`/级）。

原版州文件里的 `local_supplies` 差异很大：`1-France.txt` 是 `0.0`、`10-Poland.txt` 是 `7.0`、`1018 - South Kyushu.txt` 是 `10.0`。这是**手工调的平衡值**，不做地图大改时通常不用动。

### 2.3 空中补给

| define | 值 |
|---|---|
| `AIR_SUPPLY_CONVERSION_SCALE` | 0.01 |
| `AIR_SUPPLY_DROP_EXPIRATION_HOURS` | 168 |
| `MIN_PLANE_COUNT_AIR_SUPPLY` | 1 |

运输机任务 `air_supply` 的授权见 [../03_military/air.md](../03_military/air.md)（`common/units/equipment/quad_engine_airframe.txt` 第 190-191 行）。

### 2.4 摩托化（motorization）

- 补给枢纽可被摩托化，提高分发半径与流量：`SUPPLY_HUB_FULL_MOTORIZATION_BONUS = 2.2`、卡车成本 60。
- AI 触发阈值：`DIVISION_SUPPLY_RATIO_TO_MOTORIZE = 0.80`、`UPDATE_SUPPLY_MOTORIZATION_FREQUENCY_HOURS = 52`。
- 玩家侧靠「摩托化补给」开关（消耗卡车）。

---

## 3. 补给设施怎么放

### 3.1 补给枢纽（supply_node）

```pdx
# common/buildings/00_buildings.txt 第 98-113 行
supply_node = {
	show_on_map = 1
	base_cost = 20000
	disabled_in_dmz = yes
	icon_frame = 15
	centered = yes
	supply_node = yes
	damage_factor = 0.1
	allied_build = yes
	always_shown = yes
	infrastructure_construction_effect = yes
	level_cap = { province_max = 1 }      # ★省级建筑，每省 1 个
	tags = { supply_building }
}
```

放置方式（省级建筑，写在州的 `history.buildings` 里）：

```pdx
# 示例：在 state 1082 的 13414 省放一个补给枢纽
history = {
	buildings = {
		13414 = {
			supply_node = 1
		}
	}
}
```

> `map/supply_nodes.txt` 是**地图初始补给枢纽的位置数据**（727 行，首列恒为 1）。⚠️ 首列语义本机无文档，按实测记录；一般通过州建筑放置补给枢纽，而不是手改这个文件。

### 3.2 铁路

```pdx
# common/buildings/00_buildings.txt 第 115-124 行
rail_way = {
	base_cost = 170
	per_level_extra_cost = 130
	disabled_in_dmz = yes
	icon_frame = 16
	infrastructure_construction_effect = yes
	level_cap = { province_max = 1 }
}
```

- 初始铁路在 `map/railways.txt`：`<等级> <省数> <省1> <省2> ...`（如 `3 4 6521 11444 3312 6282`）。
- 脚本修铁路用 `build_railway`（`documentation/effects_documentation.md` 第 2535 行）：

```pdx
build_railway = {
	level = 1
	build_only_on_allied = yes
	# 可给路径权重函数（scope = 省控制者）
}
```

### 3.3 海军补给

- `naval_base`（每级吞吐 3）、`naval_supply_hub`、`FLOATING_HARBOR_*`。
- 舰队补给需求由海军基地/海军补给枢纽满足；`NAVAL_SUPPLY_HUB_REDUCTION_FACTOR = 0.0` 是削减系数。

---

## 4. 最小可跑示例：给新州配好补给

```pdx
# 路径：<mod>/history/states/1082-HHO_New_State.txt
state = {
	id = 1082
	name = "STATE_1082"
	manpower = 150000
	state_category = rural

	history = {
		owner = SWE
		add_core_of = SWE

		buildings = {
			infrastructure = 3          # 基建给本地补给 + 铁路流量衰减减免
			13414 = {
				supply_node = 1         # ★补给枢纽（省级）
			}
			13414 = {
				rail_way = 1            # 铁路（省级；实际是否连通要看 railways 拓扑）
			}
		}
	}

	provinces = { 13414 13415 }
	local_supplies = 3.0            # ★本地补给（手工平衡值）
}
```

> ⚠️ 同一 `province_id = { }` 块里可以同时写多个建筑；上面为可读性拆成两块——**重复的省键会按后者覆盖**，实际请写在一个块里：
> ```pdx
> 13414 = {
>     supply_node = 1
>     rail_way = 1
> }
> ```

配好后：
- 该省通铁路后，补给从首都/上级枢纽流入（`RAILWAY_BASE_FLOW = 10` + 每级 5）。
- 摩托化由玩家/AI 开关，受卡车数量限制。

---

## 5. 通过国策 / 事件改补给

| 需求 | 做法 |
|---|---|
| 修铁路 | `build_railway = { level = 1 }`（any scope） |
| 建补给枢纽 | `add_building_construction = { type = supply_node level = 1 instant_build = yes }`（STATE scope） |
| 加本地补给 | `add_state_modifier` 里的 `local_supplies_for_controller` 等（modifier 名查 `documentation/modifiers_documentation.md`） |
| 加基建 | `add_building_construction = { type = infrastructure level = 1 }` |
| 给部队短暂补给 | 空投（air supply 任务）或 `add_equipment` 类效果 |

国策/事件写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)。

---

## 6. 1.19 与旧教程的差异（实测）

1. **补给区文件几乎消失**：`map/supplyareas/` 只剩 `1-SupplyArea.txt`（1 个定义），本地化仍有 357 条 → 补给区基本自动生成。**旧教程「每个补给区一个 .txt」已不适用**（⚠️ 推断）。
2. **补给枢纽/铁路/摩托化**是 1.12+ 的内容，但 1.19 的数值与结构（`supply_nodes.txt` 727 行、`rail_way` 建筑、`build_railway` effect）与旧教程（补给靠「补给区 + 基建 + 港口」）完全不同。
3. **新增 `naval_supply_hub` / `floating_harbor`（装备）** 这类海军补给设施。
4. **`local_supplies` 字段**在州文件里是显式平衡值（1.12+），旧教程没有。

---

## 7. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 补给节点 | `map/supply_nodes.txt` | 727 行 | ❌ |
| 铁路 | `map/railways.txt` | 909 行 | ❌ |
| 补给区 | `map/supplyareas/1-SupplyArea.txt` | 1 文件 / 8 行 | ❌ |
| 补给相关建筑（hub / 节点 / 港口） | `common/buildings/00_buildings.txt`（`supply_node`、`rail_way`、`naval_supply_hub` 等） | 787 行 | ❌ |
| 州补给系数 | `history/states/*.txt` 顶层 `local_supplies = <值>` | 1,069 / 1,081 州文件含该字段 | ❌ |
| 补给数值 | `common/defines/00_defines.lua`（`SUPPLY_*`） | 4,728 行 | ❌ |
| 脚本建铁路/补给 | `documentation/effects_documentation.md`（`build_railway` 等） | 222,533 B | ✅ |

- **"补给 hub" 的实体是省建筑 `supply_node` + 铁路连通**：`map/supply_nodes.txt` 是引擎/工具产物，手改难验证；mod 里加补给应优先"州里放 `supply_node` 建筑 + `build_railway` 连通"，而不是手写节点坐标。
- `map/buildings.txt`、`map/railways.txt` 属于 `map/` 生成结构；任何 `map/` 改动都要 `replace_path` 整目录替换并全员一致（见 [../06_workflow/compatibility.md](../06_workflow/compatibility.md)）。

## 8. 常见错误 / 自检清单

- [ ] 补给枢纽用省级建筑 `supply_node` 放（`province_max = 1`），不是州级。
- [ ] 铁路要连通（`map/railways.txt` 或 `build_railway`），孤立枢纽没有流量。
- [ ] `local_supplies` 写在 `state = { }` 顶层（不是 history 里）。
- [ ] 新省加入战略区（否则区域补给/空投异常）。
- [ ] 不要手改 `map/supply_nodes.txt` 首列语义不明的数据；优先用州建筑。
- [ ] 改 `SUPPLY_*` defines 会让 checksum 变化且影响全局 AI，慎用。
- [ ] `infrastructure` 上限 5 级（`state_max = 5`）。
- [ ] 改完重启；`logs/error.log` 搜 `supply`。

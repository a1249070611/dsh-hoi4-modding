---
title: 战略区（Strategic Regions）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - map/strategicregions/1-Southern England.txt
  - map/strategicregions/23-Italy.txt
  - common/ai_areas/default.txt
  - localisation/english/strategic_region_names_l_english.yml
  - common/defines/00_defines.lua
  - map/supplyareas/1-SupplyArea.txt
---

# 战略区（Strategic Regions）

**一句话**：战略区是**跨州的作战/天气/海军区域**——空战、海战、天气、AI 战区划分都以它为单位；一个省必须属于某个战略区，否则会出现「无天气/无区域」的异常。

**本机现状**：`map/strategicregions/` 有 **304 个 .txt**，id `1`~`304` **连续无缺号**；下一个可用 ID = `305`。

---

## 1. 文件格式

一个文件一个 `strategic_region = { ... }`，文件名约定 `<id>-<英文名>.txt`：

```pdx
# map/strategicregions/1-Southern England.txt（节选）
strategic_region={
	id=1
	name="STRATEGICREGION_1"          # loc key（strategic_region_names_l_english.yml 第 2 行 = "Southern England"）
	provinces={
		221 271 296 322 364 507 540 3241 3287 3301 3353 3369 3422 3463
		3501 6103 6221 6237 6270 6301 6351 6378 6489 6526 7239 9239 9250
		9268 9297 9322 9458 9484 9562 11221 11253 11279 11333 11345 11374
		11406 11446 11471 13070
	}
	weather={
		period={
			between={ 0.0 30.0 }      # 一年内的日期区间（0.0~1.0 的比例？见下方说明）
			temperature={ -6.0 12.0 } # 温度范围
			no_phenomenon=0.500       # 各天气现象的权重
			rain_light=1.000
			rain_heavy=0.150
			snow=0.200
			blizzard=0.000
			arctic_water=0.000
			mud=0.300
			sandstorm=0.000
			min_snow_level=0.000
		}
		period={ between={ 0.1 27.1 } temperature={ -7.0 12.0 } ... }
		# ……原版共 12 个 period（大约按月划分）
	}
}
```

### 字段说明

| 字段 | 含义 |
|---|---|
| `id` | 战略区 ID（1~304 已被占用） |
| `name` | loc key，惯例 `STRATEGICREGION_<id>` |
| `provinces` | 该区包含的省 ID（空格分隔，可换行） |
| `weather.period` | 天气时段；每个 period 一组参数 |
| `between = { a b }` | 时段边界（原版取值 0.0~0.11 等，实际是**日期比例**；⚠️ 具体解释本机无官方文档，改前先在游戏内观察） |
| `temperature = { min max }` | 该时段温度范围 |
| `no_phenomenon` / `rain_light` / `rain_heavy` / `snow` / `blizzard` / `arctic_water` / `mud` / `sandstorm` | 各天气的**权重**（相对值，不需要和为 1） |
| `min_snow_level` | 积雪所需的最低「雪位」 |

> 原版有 12 个 period（0.0~0.11 附近各一个），大致对应 12 个月；最后一个 period 的 `between` 会跨年（如 `{ 0.11 30.11 }`）。

---

## 2. 战略区有什么用

1. **空军区域**：空优/空战、CAS 出动、战略轰炸的目标区域都按战略区计算。
2. **海军区域**：海区（如 `9-Baltic Sea.txt`、`36-Atlantic Ocean.txt`）就是战略区；舰队任务在战略区内执行。
3. **天气**：每个战略区独立配置天气时段与概率（见上）。
4. **AI 战区**：`common/ai_areas/default.txt` 把若干战略区聚成「AI 区域」（如 `scandinavia`、`suez`、`italy`），供 AI 战略与前线分配使用：

```pdx
# common/ai_areas/default.txt 第 3-24 行
areas = {
	suez = {
		strategic_regions = { 128 28 232 }
	}
	scandinavia = {
		strategic_regions = {
			11 191 10 192 276 12 13 277 278
		}
	}
}
```

5. **补给**：1.19 的补给区与战略区不是一一对应（补给区已自动生成，见 [supply.md](supply.md)），但新省仍必须加入战略区才能参与空/海/天气计算。

---

## 3. 新增/修改战略区的步骤

### 3.1 把省加进已有战略区（最常见）

```pdx
# 编辑 map/strategicregions/<对应区域>.txt
strategic_region={
	id=1
	name="STRATEGICREGION_1"
	provinces={
		221 271 ... 13070
		13414            # ← 新增的省
	}
	weather={ ... }      # 保持原样
}
```

> ⚠️ 战略区文件是**整体替换**语义（同名文件被 mod 替换）；因此要在 mod 里完整复制该文件再改，或使用 `replace_path`（见 [../06_workflow/compatibility.md](../06_workflow/compatibility.md)）。

### 3.2 新增一个战略区

```pdx
# 路径：<mod>/map/strategicregions/305-HHO_New_Region.txt
strategic_region={
	id=305
	name="STRATEGICREGION_305"
	provinces={
		13414 13415
	}
	weather={
		period={
			between={ 0.0 30.0 }
			temperature={ 2.0 18.0 }
			no_phenomenon=0.5
			rain_light=1.0
			rain_heavy=0.15
			snow=0.1
			blizzard=0.0
			arctic_water=0.0
			mud=0.3
			sandstorm=0.0
			min_snow_level=0.0
		}
		# 建议复制原版相邻区域的 12 个 period 作为模板
	}
}
```

配套：
- 本地化 `STRATEGICREGION_305: "HHO 新区域"`（原版 key 在 `localisation/english/strategic_region_names_l_english.yml`）。
- 如果想让 AI 把它当作战区，在 `common/ai_areas/default.txt` 的某个 `areas` 里加 `305`。
- 新省必须同时加入州（`history/states`）与战略区，否则补给/天气/海军区域异常。

---

## 4. 与海军区、补给区、州的关系（一次说清）

| 概念 | 文件 | 粒度 | 作用 |
|---|---|---|---|
| **州（state）** | `history/states/*.txt` | 省的分组 | 人力/资源/建筑/归属 |
| **战略区（strategic_region）** | `map/strategicregions/*.txt` | 省的分组 | 空战/海战/天气/AI 战区 |
| **补给区（supply_area）** | `map/supplyareas/1-SupplyArea.txt` | 州的分组 | 补给流（1.19 几乎全自动） |
| **AI 区域（ai area）** | `common/ai_areas/default.txt` | 战略区的分组 | AI 战略/前线 |

一个省可以属于：1 个州、1 个战略区、若干补给相关结构（补给枢纽/铁路）。

### 4.1 脚本能对战略区做什么

战略区是**静态地图数据**（形状/省列表不能由国策改），但引擎提供了 `STRATEGIC_REGION` 作用域与 effect：

- `add_region_efficiency`（STRATEGIC_REGION scope，`documentation/effects_documentation.md` 第 1978-1985 行）：给某国在该战略区加效率系数。
- `documentation/effects_documentation.md` 第 528-530 行显示 `STRATEGIC_REGION` scope **只有一个 effect**（`add_region_efficiency`），没有「改省列表/改天气」的 effect；官方文档也没有列出 `every_strategic_region` 之类的迭代器。
- 因此「国策让某区域变得更适合作战」只能通过：给国家/州的 modifier、加建筑（机场/港口/雷达）、或改控制权间接实现。国策写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)。

---

## 5. 1.19 与旧教程的差异（实测）

1. **补给区不再与战略区一一对应**：旧教程常说「每个战略区对应一个补给区文件」；1.19.x `map/supplyareas/` 只剩 1 个文件，补给区基本由引擎自动生成（⚠️ 详见 [supply.md](supply.md)）。
2. **天气系统内嵌在战略区文件里**（`weather.period`），旧教程有独立的 `climate.txt`——本机 `map/default.map` 里 `#climate = "climate.txt"` 已被注释掉。
3. **AI 区域独立成 `common/ai_areas/`**，旧教程少有提及。

---

## 6. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 战略区定义 | `map/strategicregions/` | 304 文件 / 50,530 行（`<id>-<name>.txt`，如 `133-Central Russia.txt`） | ❌（`map/` 全目录无 doc） |
| 战略区名本地化 | `localisation/*/strategic_region_names_l_*.yml` | `STRATEGICREGION_<id>` | — |
| AI 区域（与战略区不同） | `common/ai_areas/default.txt` | 1 文件 | ❌ |
| 天气/季节引用 | 战略区文件内 `weather = { period = { ... } }`；`map/seasons.txt`、`common/weather.txt` | 156 / 162 行 | ❌ |
| 补给区（已脱钩） | `map/supplyareas/1-SupplyArea.txt` | 1 文件 / 8 行 | ❌ |
| 唯一可用 effect | `documentation/effects_documentation.md`（`add_region_efficiency`） | 222,533 B | ✅ |

**id 规则**：strategic region id 与 state id、省 id 独立编号；1..304 已全部占用（304 个文件），新建从 **305** 起。与州一样，文件名序号只是注释，引擎取文件内 `id`。

- 每个省必须属于且仅属于一个战略区；缺失或重复会导致补给、海军、天气归属异常。可用脚本对 `definition.csv` 全量省 id 与所有战略区 `provinces` 的并集做比对。
- 改战略区是**整文件替换**语义：只写一个 `provinces` 块会丢掉 `weather`、`naval_terrain` 等其余内容。

## 7. 常见错误 / 自检清单

- [ ] `id` 唯一（1~304 已用，新从 305 起）。
- [ ] `name` 有 loc key（`STRATEGICREGION_<id>`）。
- [ ] `provinces` 里的省在 `definition.csv` 存在，且没有被两个战略区重复引用（⚠️ 重复会导致天气/区域归属异常）。
- [ ] 每个省都至少属于一个战略区（可用脚本核对：definition.csv 全部 id vs 所有战略区 provinces 的并集）。
- [ ] `weather` 的 period 完整（原版 12 个），只写 1 个会导致其它时段无天气。
- [ ] 改战略区等于整体替换文件，记得复制完整原文。
- [ ] 新区域如果想被 AI 使用，加入 `common/ai_areas/default.txt`。
- [ ] 改完重启；`logs/error.log` 搜战略区 id。

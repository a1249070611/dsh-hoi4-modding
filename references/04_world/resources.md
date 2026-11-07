---
title: 战略资源（Resources）
domain: 04_world
scope: country
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - common/resources/00_resources.txt
  - common/resources/_documentation.md
  - common/defines/00_defines.lua
  - history/states/1000-East Azerbaijan.txt
  - common/buildings/00_buildings.txt
  - documentation/effects_documentation.md
---

# 战略资源（Resources）

**一句话**：资源种类在 `common/resources/00_resources.txt`（1.19.x 共 **7 种**），产量写在 `history/states/*.txt` 的 `resources = { }` 里（或建筑的 `local_resources_<x>`），资源不足会让军工生产按缺口打折。

---

## 1. 资源定义文件

`common/resources/00_resources.txt`（全文 43 行，1.19.x 实测 **7 种资源，含 1.19 新增的 `coal`**）：

```pdx
resources = {

	oil = {
		icon_frame = 1
		cic = 0.125
		convoys = 0.1
	}

	aluminium = { icon_frame = 2  cic = 0.125  convoys = 0.1 }
	rubber    = { icon_frame = 3  cic = 0.125  convoys = 0.1 }
	tungsten  = { icon_frame = 4  cic = 0.125  convoys = 0.1 }
	steel     = { icon_frame = 5  cic = 0.125  convoys = 0.1 }
	chromium  = { icon_frame = 6  cic = 0.125  convoys = 0.1 }
	coal      = { icon_frame = 7  cic = 0.125  convoys = 0.1 }
}
```

| 字段 | 含义 |
|---|---|
| `icon_frame` | 资源图标在资源图标 strip 里的帧号（1~7） |
| `cic` | 每单位资源折算的「民用工厂等价值」（用于贸易/造价换算） |
| `convoys` | 每单位资源海运需要的运输船比例 |

配套说明 `common/resources/_documentation.md`（全文 4 行，很重要）：

> *"When adding new resources or changing the order, remember to update this define: `NAI::MIN_FACTORIES_TO_WANT_TO_IMPORT`. This define prevents the AI from considering importing certain resources if it has less than N factories available for trade."*

即：**改资源种类/顺序后必须同步改 defines 里的数组**：

```lua
-- common/defines/00_defines.lua 第 3584 行
MIN_FACTORIES_TO_WANT_TO_IMPORT = {  -- per strategic resource, array should be updated with new resources
	...
}
```

以及 `common/defines/00_defines.lua` 第 22-24 行的资源映射：

```lua
OIL_RESOURCE    = "oil",
FUEL_RESOURCE   = "oil",     -- 给国家燃油的资源
ENERGY_RESOURCE = "coal",    -- ★1.19：给国家电力的资源
```

---

## 2. 资源产量写在哪

### 2.1 州级（最主要）

```pdx
# history/states/1000-East Azerbaijan.txt 第 3-10 行
state = {
	id = 1000
	name = "STATE_1000"
	manpower = 715857
	resources = {
		steel = 6
	}
	state_category = town
	...
}
```

- 一个州可以写多种资源；数值是**基础产量**。
- 实际产量还要乘基建与补给线加成（见 2.3）。

### 2.2 建筑级（`local_resources_<resource>`）

`common/buildings/00_buildings.txt` 里建筑可以给所在州加资源：

```pdx
# 第 259-280 行（合成炼油厂）
synthetic_refinery = {
	base_cost = 14500
	icon_frame = 10
	#local_resources_oil = 1     # May use local_resources_ + any resource name
	local_resources_rubber = 1
	refinery = yes
	...
}
```

> 原版注释明确：`local_resources_ + 任意资源名` 都可用。

### 2.3 修正（defines + modifier）

| 来源 | 数值 | 出处 |
|---|---|---|
| 基建 | 每级未损坏基建 `+15%` 乘法加成 | `INFRASTRUCTURE_RESOURCE_BONUS = 0.15` |
| 铁路/海路连接首都 | `+20%` 乘法加成 | `SUPPLY_ROUTE_RESOURCE_BONUS = 0.2` |
| 资源短缺 | 每座缺料工厂 `-5%` 生产惩罚 | `PRODUCTION_RESOURCE_LACK_PENALTY = -0.05` |
| 装备最多依赖几种资源 | 3 | `MAX_EQUIPMENT_RESOURCES_NEED = 3` |

资源相关 modifier（如 `resource_..._factor`）请查 `documentation/modifiers_documentation.md`（按 scope 分组）。

---

## 3. 资源在游戏里怎么被消耗

- **装备生产**：装备的 `resources = { steel = 2 }` 表示每单位装备消耗 2 钢（见 [../03_military/equipment.md](../03_military/equipment.md)）。
- **电力（1.19 新）**：`coal` 通过 `ENERGY_RESOURCE = "coal"` 映射为电力，换算 `RESOURCE_TO_ENERGY_COEFFICIENT = 9.0`（1 单位煤 = 9 电力）。
- **燃油**：`FUEL_RESOURCE = "oil"`，油资源进国家油库；`infrastructure` 建筑有 `country_modifiers { modifiers { max_fuel_building = 1.5 } }`（每级 +1.5k 油上限）。
- **贸易/租借**：`cic` 决定资源价值；`convoys` 决定海运消耗；贸易优先级 defines：`RESOURCE_EXPORT_PRIORITY = 4`、`RESOURCE_IMPORT...`（第 1573-1576 行）。

---

## 4. 脚本修改资源：`add_resource`

`documentation/effects_documentation.md` 第 2056-2070 行（**STATE 与 COUNTRY 两个 scope 都支持**）：

```pdx
add_resource = {
	type = steel
	amount = 5
	state = 42            # 也可以从当前 scope 读（STATE scope 时可省）
	days = 60             # 可选：临时资源，60 天后移除
	show_state_in_tooltip = no
}
```

典型用法（国策/事件里永久加产）：

```pdx
# 国策 completion_reward（country scope 下对某州生效）
completion_reward = {
	42 = {
		add_resource = {
			type = steel
			amount = 5
		}
	}
}
```

国策/事件写法见 [../02_content/focus-trees.md](../02_content/focus-trees.md)、[../02_content/events.md](../02_content/events.md)。

---

## 5. 最小可跑示例 A：给一个州加资源（最常用）

```pdx
# 路径：<mod>/history/states/1082-HHO_New_State.txt（新建州见 states.md）
state = {
	id = 1082
	name = "STATE_1082"
	manpower = 150000
	state_category = rural

	resources = {
		steel = 4
		tungsten = 2
	}

	history = {
		owner = SWE
		add_core_of = SWE
	}

	provinces = { 13414 13415 }
	local_supplies = 2.0
}
```

## 6. 最小可跑示例 B：新增一种资源（⚠️ 高风险）

> ⚠️ **以下步骤是基于本机文件结构的推导，官方未提供「新增资源」的完整文档**。除非做大 overhaul，强烈建议复用 7 种现有资源。

1. `common/resources/00_resources.txt` 追加：

```pdx
resources = {
	oil = { ... }
	...
	coal = { icon_frame = 7 ... }

	HHO_rare_earth = {
		icon_frame = 8        # ⚠️ 需要资源图标 strip 有第 8 帧
		cic = 0.2
		convoys = 0.1
	}
}
```

2. **更新 defines 数组**：`NAI::MIN_FACTORIES_TO_WANT_TO_IMPORT` 增加一项，否则 AI 导入逻辑错位（`_documentation.md` 明确要求）。
3. **图标**：资源图标是 strip 帧（`icon_frame`），需要扩展对应 DDS/GFX；具体注册方式见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)。
4. **本地化**：`HHO_rare_earth: "稀土"`（原版 key 在 `localisation/*/resources_l_*.yml` 一类文件里）。
5. **在州/建筑/装备里引用**：`resources = { HHO_rare_earth = 3 }`、`local_resources_HHO_rare_earth = 1`。
6. **测试**：进游戏看生产界面资源条是否多一格、tooltip 是否正常、AI 是否崩。

**风险**：资源系统与贸易 AI、生产惩罚、能源/燃油映射都耦合，新资源很容易出现「有产量但 AI 不贸易」「图标错位」「存档不兼容」。

---

## 7. 1.19 与旧教程的差异（实测）

1. **资源从 6 种变 7 种**：新增 `coal`（`icon_frame = 7`），并通过 defines `ENERGY_RESOURCE = "coal"` 接入电力系统；旧教程只有 oil/aluminium/rubber/tungsten/steel/chromium。
2. **新增电力系统**：`RESOURCE_TO_ENERGY_COEFFICIENT = 9.0`、建筑 `affects_energy`、`energy_infrastructure` 建筑。
3. **`local_resources_<resource>`** 在建筑上是通用写法（原版注释写明），旧教程多只讲合成炼油厂。
4. **资源顺序敏感**：`MIN_FACTORIES_TO_WANT_TO_IMPORT` 是**按顺序的数组**，改顺序必须同步改 defines（`_documentation.md` 唯一一句就是这个警告）。

---

## 8. 官方文档与实例文件位置（含系统入口，1.19.x）

| 系统 / 入口 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 资源定义 | `common/resources/00_resources.txt` | 43 行 / 7 种资源 | ✅ `_documentation.md`（4 行，只有 AI 顺序警告） |
| 州内资源 | `history/states/*.txt` 顶层 `resources = { }` | 1,081 文件 | ❌ |
| 建筑产资源 | `common/buildings/00_buildings.txt` 的 `local_resources_<资源>` | 787 行 | ❌ |
| 装备耗资源 | `common/units/equipment/*.txt` 的 `resources = { }` | 51 文件 | ✅ 装备 `_documentation.md` |
| 资源/能源数值 | `common/defines/00_defines.lua`（`ENERGY_RESOURCE`、`RESOURCE_TO_ENERGY_COEFFICIENT`、`NAI::MIN_FACTORIES_TO_WANT_TO_IMPORT`） | 4,728 行 | ❌ |
| 资源图标 | `interface/*.gfx` 的资源 sprite + `icon_frame` | — | ❌ |

- 官方文档只有一句：**加资源或改顺序必须同步 `NAI::MIN_FACTORIES_TO_WANT_TO_IMPORT`**（按资源顺序的数组），否则贸易 AI 会错位。
- 州里写资源的位置是 `state = { }` **顶层**（不是 `history = { }`，也不是省块）；改州文件即整州替换，必须抄全其他字段。
- 改资源顺序 = 改图标条与 defines 数组，**最容易让旧存档/联机出问题**，非必要不动。

## 9. 常见错误 / 自检清单

- [ ] 资源名拼写与 `common/resources/00_resources.txt` 完全一致（小写英文）。
- [ ] 新增/改顺序后同步 `NAI::MIN_FACTORIES_TO_WANT_TO_IMPORT`。
- [ ] `state.resources` 写在 `state = { }` 顶层（不是 `history` 里）。
- [ ] 建筑加资源用 `local_resources_<resource>`，装备用 `resources = { ... }`。
- [ ] 装备依赖资源种类 ≤ `MAX_EQUIPMENT_RESOURCES_NEED`（3）。
- [ ] 用 `add_resource` 时确认 scope（STATE/COUNTRY 都行），临时资源加 `days`。
- [ ] 新资源必须有图标（`icon_frame`）与本地化，否则界面显示异常。
- [ ] 改完重启；`logs/error.log` 搜资源名。

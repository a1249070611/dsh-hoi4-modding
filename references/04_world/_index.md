---
title: 世界地图与州系统索引（World Map）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - map/default.map
  - map/definition.csv
  - map/provinces.bmp
  - common/terrain/00_terrain.txt
  - history/states
  - common/buildings/00_buildings.txt
  - common/resources/00_resources.txt
  - map/strategicregions
  - map/supplyareas
---

# 04 世界地图与州系统（World Map）— 索引

一句话定位：**地图 = `map/` 的一堆 BMP/CSV（几何与拓扑）+ `history/states/` 的州定义（人力/资源/建筑/归属）+ `common/` 的定义表（建筑/资源/地形）**。改数值在 `history/` 与 `common/`，改形状要动 BMP，两者都要注意「省 ID ↔ RGB 颜色」的唯一映射。

## 文档清单

| 文档 | 一句话摘要 |
|---|---|
| [04_world/map-structure.md](map-structure.md) | `map/` 每个文件的作用、BMP 尺寸/格式、`definition.csv` 列含义、改图完整流程 |
| [states.md](states.md) | `history/states/*.txt` 全字段、新建一个州的完整步骤、如何被国策/事件引用 |
| [buildings.md](buildings.md) | `common/buildings/` 字段、槽位规则、地标建筑、建筑上限 |
| [resources.md](resources.md) | `common/resources/00_resources.txt`（1.19 有 7 种含 coal）、州资源、资源修正 |
| [04_world/strategic-regions.md](strategic-regions.md) | `map/strategicregions/` 结构与天气、与补给区/海军区的关系 |
| [supply.md](supply.md) | 1.19 补给：补给区/补给枢纽/铁路/摩托化、defines、与 mod 的关系 |
| [terrain.md](terrain.md) | `common/terrain/00_terrain.txt`（1.19 新位置）、地形类别、terrain.bmp 调色板映射、天气 |

## 该领域 5 条最重要的结论

1. **`definition.csv` 是省 ID ↔ RGB 的注册表**：13,414 行（id `0`~`13413`），下一可用省 ID 是 `13414`。`provinces.bmp` 里每个像素的颜色必须能在 `definition.csv` 里找到；改图 = 同时改 BMP 和 CSV，且颜色必须唯一。
2. **BMP 有严格尺寸/位深**（本机实测）：`provinces.bmp` 5632×2048 **24-bit**；`heightmap.bmp`、`terrain.bmp`、`rivers.bmp`、`cities.bmp` 5632×2048 **8-bit 索引色**；`world_normal.bmp` 2816×1024（半分辨率）24-bit。尺寸/位深不对 = 地图直接加载失败，且不一定有可读报错。
3. **地形定义在 `common/terrain/00_terrain.txt`，不是 `map/terrain.txt`**（1.19 变更）。`terrain.bmp` 的**调色板索引**通过该文件的 `terrain = { terrain_0 = { type = plains color = { 0 } ... } }` 映射到地形类别；战斗宽度、移动成本、单位修正都在地形类别里。
4. **州是「人力/资源/建筑/归属」的唯一载体**：`history/states/` 现有 1081 个文件、state id `1`~`1081`（无重复），新建州从 `1082` 起。州必须写 `id`、`name`、`state_category`、`manpower`、`provinces`、`local_supplies`，`history` 里写 `owner`/`add_core_of`/`buildings`/`victory_points`。
5. **`map/supplyareas/` 在 1.19.x 只剩 1 个文件、1 个 `supply_area` 定义**（`1-SupplyArea.txt`，包含 state 5/85/763/807），而本地化里有 `SUPPLYAREA_1..357`。说明绝大多数补给区已由引擎按州/战略区自动生成，**旧教程「每个补给区一个文件」的改法不再适用**。⚠️ 此结论为本地文件观察 + 推断，官方文档未说明。

## 关键文件速查

| 想改什么 | 改哪里 |
|---|---|
| 省形状/边界 | `map/provinces.bmp` + `map/definition.csv` |
| 省地形（视觉） | `map/terrain.bmp` 的调色板索引 + `common/terrain/00_terrain.txt` |
| 省地形（战斗/移动规则） | `common/terrain/00_terrain.txt` 的 `categories` |
| 州人口/资源/建筑/归属 | `history/states/<id>-<name>.txt` |
| 建筑种类/成本/上限 | `common/buildings/00_buildings.txt`（+ `01_landmark_buildings.txt`） |
| 资源种类 | `common/resources/00_resources.txt` |
| 州分类（槽位数） | `common/state_category/*.txt` |
| 战略区（天气/海军区） | `map/strategicregions/<id>-<name>.txt` |
| 补给区/补给枢纽 | `map/supplyareas/1-SupplyArea.txt`、`map/supply_nodes.txt`、`map/railways.txt` |
| 海峡/运河 | `map/adjacencies.csv` + `map/adjacency_rules.txt` |
| 初始省份名称 | `localisation/*/state_names_l_*.yml` 等（`STATE_x` / `PROV_x` / `VICTORY_POINTS_x`） |

## 常见坑（本领域高发）

1. **颜色冲突**：`provinces.bmp` 里两个省用同一个 RGB → 只有一个省生效、另一个消失（`definition.csv` 里同色多行）；新省必须用未被占用的 RGB。
2. **改了 BMP 忘了 CSV**（或反之）→ 省不出现 / 出现随机 ID。
3. **地形改错文件**：改 `map/terrain.bmp` 只是改「画面上是什么地形」；实际战斗修正来自 `common/terrain/00_terrain.txt`，且 `definition.csv` 第 7 列也有 terrain 字段（⚠️ 二者优先级本机未找到官方说明，见 [terrain.md](terrain.md)）。
4. **州没写 `state_category`** → 槽位 0、建筑全锁。
5. **州 `provinces` 漏了某个省 / 省被两个州重复引用** → 加载报错或省归属错乱。
6. **新省没加入任何战略区** → 补给/海军/空战区域异常。
7. **`map/positions.txt` 本机是 0 字节** → 单位站位由游戏/nudge 处理，不要手写（⚠️ 观察结论）。
8. **地图改动无法热重载**，必须重启；且大地图改动会改变 checksum。

## 与其他目录的边界

- 用国策/事件改州（加核心、加建筑、改分类、转移归属）：见 [../02_content/focus-trees.md](../02_content/focus-trees.md)、[../01_script/effects-triggers.md](../01_script/effects-triggers.md)。
- 州/建筑/地标的图标与界面：见 [../05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)。
- `map/` 的发布与 `replace_path`（整目录替换）：见 [../06_workflow/compatibility.md](../06_workflow/compatibility.md)。

## 域文件规模、官方文档与实例文件位置（1.19.x 实测）

数据为 1.19.4.2 安装树统计（口径同 `.tmp/audit/game-survey.md`）。

| 子域 | 相对 `<GAME_DIR>` 路径 | 规模 | 官方文档 |
|---|---|---|---|
| 州定义 | `history/states/` | 1,081 文件 | ❌ |
| 建筑 | `common/buildings/` | 2 文件 / 1,446 行 | ❌ |
| 州分类（槽位） | `common/state_category/` | 13 文件 / 114 行 | ❌ |
| 资源 | `common/resources/` | `00_resources.txt` 43 行 | ✅ `_documentation.md`（4 行） |
| 省建筑等级修正（特殊地点） | `common/strategic_locations/` | 17 行 + `documentation.md` | ✅ |
| 地形 | `common/terrain/` | 1 文件 / 356 行 | ❌ |
| 地图文件 | `map/` | 顶层 22 文件 + `strategicregions/` 304 + `terrain/` 64 | ❌（`map/` 零文档） |
| 省注册表 | `map/definition.csv` | 13,414 行 | ❌ |
| 天气/季节 | `common/weather.txt`(162) / `map/seasons.txt`(156) | — | ❌ |

结论：世界地图层**只有 `resources` 与 `strategic_locations` 两处有官方文档**，且都很短（4 行 / 23 行）。`map/`、`history/`、`buildings/`、`terrain/`、`state_category/` 全部无 doc，本目录各篇因此以"原版样本 + 实测"为主要依据。

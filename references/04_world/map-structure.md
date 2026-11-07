---
title: 地图文件结构与改图流程（Map Structure）
domain: 04_world
scope: state
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - map/default.map
  - map/definition.csv
  - map/provinces.bmp
  - map/heightmap.bmp
  - map/terrain.bmp
  - map/rivers.bmp
  - map/cities.txt
  - map/adjacencies.csv
  - map/adjacency_rules.txt
  - map/continent.txt
  - map/seasons.txt
  - common/terrain/00_terrain.txt
  - common/defines/00_defines.lua
  - map/strategicregions
  - map/continent.txt
---

# 地图文件结构与改图流程（Map Structure）

**一句话**：`map/` 是「一张 5632×2048 的位图世界 + 一组索引/拓扑 CSV + 若干 3D 位置数据」。**只在既有省份内改数值不需要碰 `map/`**；只要新增/删除省份、海峡、地形，就必须动 BMP 与 CSV，并做完整的一致性检查。

---

## 1. `map/` 文件清单（本机 1.19.x 实测）

| 文件 | 大小/尺寸（实测） | 作用 | 手改？ |
|---|---|---|---|
| `default.map` | 504 B | 地图入口：声明每个数据文件叫什么 | ✅（几乎不用改） |
| `definition.csv` | 465 KB，13,414 行 | **省 ID ↔ RGB ↔ 类型/沿海/地形/大洲** 注册表 | ✅ 必须 |
| `provinces.bmp` | 5632×2048，**24-bit** | 每个像素的颜色 = 一个省 | ✅ 必须 |
| `heightmap.bmp` | 5632×2048，8-bit 索引 | 高度图（地形起伏/山脉） | ✅ 可选 |
| `terrain.bmp` | 5632×2048，8-bit 索引 | 地形**视觉/类别**（调色板索引 → 地形） | ✅ 可选 |
| `rivers.bmp` | 5632×2048，8-bit 索引 | 河流（调色板索引区分大小河） | ✅ 可选 |
| `world_normal.bmp` | 2816×1024，24-bit | 法线贴图（半分辨率） | ❌ 美术资源 |
| `trees.bmp` | 1650×600，8-bit 索引 | 树木分布/调色板（`default.map` 的 `tree_definition`） | ⚠️ 需专用工具 |
| `cities.bmp` + `cities.txt` | 5632×2048 8-bit + 2.2 KB | 城市区域（按调色板索引归类到 `city_group`） | ⚠️ 城市模型 |
| `continent.txt` | 93 B | 大洲列表（7 个） | ✅ |
| `adjacencies.csv` | 13 KB | 海峡/运河/跨海连接 | ✅ |
| `adjacency_rules.txt` | 6.1 KB | 通航规则（谁能过、如何被封锁） | ✅ |
| `positions.txt` | **0 B（本机）** | 单位/建筑在地图上的坐标 | ⚠️ 由 nudge 生成，勿手写 |
| `unitstacks.txt` | 10 MB | 部队堆叠标记的 3D 坐标（`<id>;<...>;x;y;z;...`） | ⚠️ 生成数据 |
| `buildings.txt` | 3.2 MB | 建筑模型在地图上的 3D 摆放（`<province>;<building>;x;y;z;rotation;<spawn province>`） | ⚠️ 生成数据 |
| `weatherpositions.txt` | 17 KB | 天气单元位置（`<id>;x;y;z;size`） | ⚠️ 生成数据 |
| `railways.txt` | 28 KB | 初始铁路（`<level> <点数> <prov1> <prov2> ...`） | ✅ |
| `supply_nodes.txt` | 727 行 | 补给枢纽所在省（本机首列恒为 `1`） | ✅（见 [supply.md](supply.md)） |
| `seasons.txt` | 2.9 KB | 季节的日期范围 + HSV/色彩平衡 | ✅ |
| `ambient_object.txt` | 2.6 KB | 环境特效（风、水的实体） | ⚠️ 美术 |
| `strategicregions/` | 304 个 .txt | 战略区（含天气） | ✅ |
| `supplyareas/` | **1 个 .txt** | 补给区（1.19.x 只剩 1 个定义） | ⚠️ 见 [supply.md](supply.md) |
| `terrain/` | 一堆 .dds | 地形贴图资源（视觉） | ❌ 美术 |

### 1.1 `default.map`

```
# map/default.map（全文，1.19.x）
definitions = "definition.csv"
provinces = "provinces.bmp"
positions = "positions.txt"
terrain = "terrain.bmp"
rivers = "rivers.bmp"
heightmap = "heightmap.bmp"
tree_definition = "trees.bmp"
continent = "continent.txt"
adjacency_rules = "adjacency_rules.txt"
adjacencies = "adjacencies.csv"
#climate = "climate.txt"
ambient_object = "ambient_object.txt"
seasons = "seasons.txt"

# Define which indices in trees.bmp palette which should count as trees for automatic terrain assignment
tree = { 3 4 7 10 }
```

- 改文件名（例如想让 mod 用自己的 bmp）→ 改这里，但**通常更推荐直接替换同名文件**。
- `tree = { 3 4 7 10 }`：`trees.bmp` 调色板里哪些索引算树，用于自动地形判定。

---

## 2. `definition.csv`：省注册表（核心）

**格式（分号分隔，8 列，无表头）**：

```
id;R;G;B;type;coastal;terrain;continent
0;0;0;0;land;false;unknown;0
1;230;81;119;lake;false;lakes;7
2;0;0;55;land;false;forest;1
3544;44;159;148;land;false;urban;1
3838;46;39;43;land;true;hills;1
12156;174;57;132;land;false;hills;6
```

| 列 | 示例 | 说明 |
|---|---|---|
| 1 `id` | `3544` | 省 ID（0 是占位行；本机最大 `13413`，下一可用 `13414`） |
| 2-4 `R;G;B` | `44;159;148` | `provinces.bmp` 中该省的颜色（**全表唯一**） |
| 5 `type` | `land` / `sea` / `lake` | 省类型 |
| 6 `coastal` | `false` / `true` | 是否沿海（能否建港口/海军基地） |
| 7 `terrain` | `plains` / `forest` / `hills` / `mountain` / `urban` / `desert` / `jungle` / `marsh` / `ocean` / `lakes` / `unknown` | 地形类别名（对应 `common/terrain/00_terrain.txt` 的 `categories`） |
| 8 `continent` | `1`~`7`，`0`=无 | 大洲（`continent.txt` 的 **1-based** 索引）。实测：Warsaw=1(europe)、Yanan=6(asia) |

**本机统计（脚本实测）**：

```
总行数 13414，id 0..13413
land 10155 / sea 3133 / lake 126
coastal=true 3181
地形分布：ocean 3133, plains 3031, forest 2364, mountain 1708, hills 1352,
          desert 815, jungle 477, urban 265, marsh 142, lakes 126, unknown 1
```

> ⚠️ **第 7 列 terrain 与 `terrain.bmp` 哪个最终决定游戏内地形**，本机没有官方文档说明。实测两处数据大体一致（`urban` 省都是城市省）。稳妥做法：**两处一起改**，改完在游戏里点开省份 tooltip 核对地形名。

---

## 3. 为什么颜色必须唯一

`provinces.bmp` 是「颜色 → 省」的编码图。游戏读取时按颜色查 `definition.csv`：
- 同一 RGB 出现在两行 `definition.csv` → 后读到的覆盖前面的，表现为「一个省消失/数据错乱」。
- BMP 里用了 `definition.csv` 没登记的颜色 → 该区域不属于任何省（通常表现为不可通行/黑洞）。

**新省取色流程**（用 Python 最快，避免肉眼撞色）：

```python
# 伪代码/可直接改路径运行：从 definition.csv 读已用颜色，生成一个未用颜色
import csv, random
used = set()
with open(r"<GAME_DIR>/map/definition.csv", encoding="utf-8") as f:
    for row in csv.reader(f, delimiter=";"):
        used.add((int(row[1]), int(row[2]), int(row[3])))
while True:
    c = (random.randint(1, 255), random.randint(1, 255), random.randint(1, 255))
    if c not in used:
        print(c); break
```

然后把该颜色刷到 `provinces.bmp` 的新区域，并在 `definition.csv` 追加一行（新 id = 13414）。

---

## 4. 各地图的格式要求（BMP）

| 文件 | 位深 | 要点 |
|---|---|---|
| `provinces.bmp` | 24-bit RGB | 每个像素一个省颜色；**不要**缩放/压缩，保持 5632×2048 |
| `heightmap.bmp` | 8-bit 索引（灰度） | 亮度=高度；海滨要有过渡否则出现断崖 |
| `terrain.bmp` | 8-bit 索引色 | 调色板索引 → `common/terrain/00_terrain.txt` 的 `terrain = { color = { N } }` |
| `rivers.bmp` | 8-bit 索引色 | 索引区分小/大河：`RIVER_SMALL_START_INDEX = 0`、`RIVER_SMALL_STOP_INDEX = 6`、`RIVER_LARGE_STOP_INDEX = 11`（`common/defines/00_defines.lua` 第 937-939 行） |
| `trees.bmp` | 8-bit 索引色 | `default.map` 的 `tree = { 3 4 7 10 }` 决定哪些索引算树 |

> **格式必须完全一致**：尺寸错、位深错、用 PNG 改名成 BMP，都会导致地图加载失败或渲染异常。保存时选「BMP / 索引色 / 不压缩」。

---

## 5. 地形映射（`terrain.bmp` ↔ `common/terrain/00_terrain.txt`）

```pdx
# common/terrain/00_terrain.txt 第 323-356 行
terrain = {
	terrain_0      = { type = plains   color = { 0 }  texture = 1 }
	terrain_1      = { type = forest   color = { 1 }  texture = 4 }
	desert_mountain= { type = hills    color = { 2 }  texture = 3 }
	desert         = { type = desert   color = { 3 }  texture = 9 }
	terrain_4      = { type = forest   color = { 4 }  texture = 5 }
	terrain_5      = { type = plains   color = { 5 }  texture = 0 }
	terrain_6      = { type = mountain color = { 6 }  texture = 11 }
	terrain_7      = { type = desert   color = { 7 }  texture = 12 }
	desert_hills   = { type = desert   color = { 8 }  texture = 14 }
	terrain_9      = { type = marsh    color = { 9 }  texture = 6 }
	terrain_10     = { type = mountain color = { 10 } texture = 13 }
	desert         = { type = mountain color = { 11 } texture = 11 }
	desert         = { type = desert   color = { 12 } texture = 8 }
	forest_13      = { type = urban    color = { 13 } texture = 10 spawn_city = yes }
	forest_14      = { type = lakes    color = { 14 } texture = 255 }
	ocean_15       = { type = ocean    color = { 15 } texture = 9 }
	snow_16        = { type = mountain color = { 16 } texture = 11 perm_snow = yes }
	plains_17      = { type = plains   color = { 19 } texture = 0  perm_snow = yes }
	hills_blend    = { type = hills    color = { 17 } texture = 2 }
	mountain_variation_sand  = { type = mountain color = { 18 } texture = 7 }
	mountain_variation_grass = { type = mountain color = { 20 } texture = 7 }
	jungle_18      = { type = jungle   color = { 21 } texture = 4 }
	jungle_blend_18= { type = jungle   color = { 22 } texture = 5 }
	jungle_blend_18= { type = mountain color = { 27 } texture = 7 }
	desert_mountain_tops     = { type = mountain color = { 31 } texture = 15 }
}
```

- `color = { N }` 就是 `terrain.bmp` 的**调色板索引**。
- `type` 指向 `categories` 里的地形类别（战斗/移动规则在那边）。
- `texture` 指向 `map/terrain/atlas*.dds` 里的贴图编号；`perm_snow = yes`、`spawn_city = yes` 是特殊标记。
- 详细地形机制见 [terrain.md](terrain.md)。

---

## 6. 拓扑与连接

### 6.1 `adjacencies.csv`（海峡/运河）

```
From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment
12251;10321;sea;8313;-1;-1;-1;-1;;Andaman
8857;2284;sea;7617;1560;1009;1556;1016;PANAMA_CANAL;Panama
```

- `Type`：实测有 `sea`（其余如 `land`/`impassable` 需按需验证）。
- `Through`：穿过的省（对 sea 型是海省）。
- `adjacency_rule_name`：引用 `adjacency_rules.txt` 里的规则名；空 = 无特殊规则。
- 坐标列 `-1` 表示自动。

### 6.2 `adjacency_rules.txt`（通航规则）

```pdx
# map/adjacency_rules.txt 第 14-60 行（苏伊士运河）
adjacency_rule = {
	name = "SUEZ_CANAL"

	contested = { army = no  navy = no  submarine = no  trade = no }
	enemy     = { army = no  navy = no  submarine = no  trade = no }
	friend    = { army = yes navy = yes submarine = yes trade = yes }
	neutral   = { army = yes navy = yes submarine = yes trade = yes }

	required_provinces = { 12049 1155 4073 9947 }   # 控制这些省才算控制运河

	is_disabled = {                                  # 被封锁的条件
		OR = {
			has_global_flag = SUEZ_CANAL_BLOCKED
			has_country_flag = SUEZ_CANAL_BLOCKED_FOR_COUNTRY
			has_country_flag = SUEZ_SANCTIONS_FLAG
		}
		tooltip = suez_blocked_tt
	}

	icon = 12049
	offset = { 1 0 -6 }
}
```

- 四类关系（contested/enemy/friend/neutral）各写 `army/navy/submarine/trade` 的 `yes/no`。
- 文件开头 1-10 行有完整优先级说明（谁先判定），改规则前必读。

---

## 7. 改图完整流程（新增一个省）

> 目标：在冰岛（state 100）旁边加一个新省 `13414`，归属 state 100。

1. **备份**：把 `map/` 相关文件复制到安全位置。
2. **画省**：在 `provinces.bmp` 上用唯一 RGB（如 `11;222;33`）刷出新区域。保持 5632×2048 / 24-bit（用 GIMP「导出为 BMP，高级选项：24 位 R8 G8 B8」）。
3. **注册**：`definition.csv` 追加一行：
   ```
   13414;11;222;33;land;true;plains;1
   ```
   （`coastal=true` 因为它临海；`continent=1` 欧洲）
4. **地形**：在 `terrain.bmp` 对应区域刷上想用的地形调色板索引（如 `terrain_0` → 索引 0 = plains）。
5. **高度**（可选）：`heightmap.bmp` 刷灰度。
6. **归属州**：编辑 `history/states/100-Iceland.txt`，把 `13414` 加入 `provinces = { ... }`。
7. **战略区**：在对应 `map/strategicregions/*.txt` 的 `provinces = { ... }` 里加 `13414`（否则补给/海军区异常）。
8. **位置数据**：`map/positions.txt`、`unitstacks.txt`、`buildings.txt` 是生成数据；让游戏/nudge 重新生成，不要手写。
9. **本地化/命名**：状态名 loc key `STATE_<state_id>`（`localisation/english/state_names_l_english.yml`）；胜利点名 `VICTORY_POINTS_<province>`（`victory_points_l_english.yml`，如 `VICTORY_POINTS_6521`）。⚠️ 省本身**没有** `PROV<id>` 显示名（本机 english 本地化里不存在此类 key）；需要省名用 `set_province_name` effect。
10. **重启游戏**，在 `logs/error.log` 搜 `13414`；进游戏点省份看名称/地形/归属是否正确。

> 若还要**新增州**（而不是塞进旧州），见 [states.md](states.md)。

### 7.1 新地图内容的运行时联动

地图本身是**静态数据**，国策/事件改不了「省形状」，但可以改州的归属/建筑/分类/胜利点：

- 加核心 / 转移归属 / 改分类：`add_state_core`、`transfer_state_to`、`set_state_category`（见 [states.md](states.md) 第 6 节，完整表在 `documentation/effects_documentation.md`）。
- 建建筑 / 加槽 / 修铁路：`add_building_construction`、`add_extra_state_shared_building_slots`、`build_railway`（见 [buildings.md](buildings.md)、[supply.md](supply.md)）。
- 触发条件里判断地形：`has_terrain`、`is_fighting_in_terrain`（见 [terrain.md](terrain.md)）。

国策/事件本身怎么写：见 [../02_content/focus-trees.md](../02_content/focus-trees.md)、[../02_content/events.md](../02_content/events.md)。

---

## 8. 改图的工程化注意事项

- **`map/` 是整体替换语义**：mod 只要改一张 BMP，就必须把整个 `map/` 目录纳入替换（`descriptor.mod` 的 `replace_path`，见 [../06_workflow/compatibility.md](../06_workflow/compatibility.md)），否则原版与 mod 的 BMP 会混用导致错位。
- **不可热重载**：改图后必须重启游戏。
- **checksum**：任何地图改动都会改变 checksum，多人联机必须全员一致。
- **不要用「改 PNG 再改名」**：位深/压缩都会变；必须用图像软件导出真正的 BMP。
- **生成数据别手改**：`positions.txt`（本机 0 B）、`unitstacks.txt`、`buildings.txt`、`weatherpositions.txt` 都是工具/游戏生成的结构，手改极易崩。

---

## 9. 1.19 与旧教程的差异（实测）

1. **`positions.txt` 为 0 字节**：旧教程常教「手写 positions.txt 放单位坐标」，本机原版文件是空的，推断由 nudge/启动重建（⚠️ 未找到官方说明）。改图时应走 nudge 流程而不是手写。
2. **地形定义移到 `common/terrain/00_terrain.txt`**（旧版是 `map/terrain.txt`），且 `combat_width` 改成绝对值。
3. **`map/supplyareas/` 只剩 1 个文件**（旧版是上百个文件），见 [supply.md](supply.md)。
4. **新增 `map/weatherpositions.txt`**（天气单元位置），旧教程没有。
5. **`default.map` 里 `climate = "climate.txt"` 被注释掉**（气候系统被季节/天气替代）。

---

## 10. 官方文档与实例文件位置（含系统入口，1.19.x）

`map/` 顶层 22 个文件，**整个目录零 `_documentation.md`**，格式只能靠原版样本与实测反推。

| 文件 / 目录 | 规模 | 作用 |
|---|---|---|
| `definition.csv` | 13,414 行（表头 + 13,413 省） | 省注册表：id / RGB / 地形 / 大洲 / 海岸等（见 §2） |
| `provinces.bmp` / `heightmap.bmp` / `world_normal.bmp` | 24-bit | 省着色、高度、法线（见 §4） |
| `terrain.bmp` / `rivers.bmp` / `trees.bmp` / `cities.bmp` | 8-bit 索引色 | 地形、河流、植被、城市灯光 |
| `strategicregions/` | 304 文件 / 50,530 行 | 战略区（`<id>-<name>.txt`，id 1..304） |
| `terrain/` | 64 文件 | 图形地形集 |
| `supplyareas/` | 1 文件 / 8 行 | 补给区（1.19 只剩 1 个，见 [supply.md](supply.md)） |
| `supply_nodes.txt` / `railways.txt` | 727 / 909 行 | 补给节点与铁路（生成/半生成，见 [supply.md](supply.md)） |
| `seasons.txt` / `weatherpositions.txt` | 156 行 / 生成 | 季节与天气单元（见 [terrain.md](terrain.md) §4） |
| `continent.txt` | — | 大洲定义（`definition.csv` 的大洲列按其次序） |
| `buildings.txt` / `positions.txt` / `unitstacks.txt` | 生成 | 建筑/单位/堆叠坐标，勿手写（见 §8） |
| `adjacencies.csv` / `adjacency_rules.txt` | — | 海峡与运河、通过规则（见 §6） |
| `default.map` | — | 地图尺寸与子文件绑定（`climate = "climate.txt"` 已被注释） |

**三套独立 ID 空间（跨文件一致性最易错）**：

- **省 id**：`definition.csv` 定义（1..13,413，无断号；新增从最大值 +1 起，**不要复用已删 id**）；
- **州 id**：`history/states/`（1..1081）；
- **战略区 id**：`map/strategicregions/`（1..304）。

state 文件与 strategic region 文件里写的 `provinces` 都是**省 id**；state id 只出现在州文件与 effect/trigger 里。三者混用是"加载报错但看不出原因"的常见根因（见 §10 自检）。

## 11. 常见错误 / 自检清单

- [ ] BMP 尺寸/位深与上表一致（provinces 24-bit，其余 8-bit 索引）。
- [ ] 新省 RGB 在 `definition.csv` 全表唯一，且所有 BMP 像素颜色都已登记。
- [ ] `definition.csv` 每行 8 列、分号分隔、无表头、无空行。
- [ ] 大洲列用 1~7（1=europe … 6=asia，`continent.txt` 顺序的 1-based）。
- [ ] 新省已加入某州 `provinces`，且**没有被两个州同时引用**。
- [ ] 新省已加入某战略区。
- [ ] 地形调色板索引在 `common/terrain/00_terrain.txt` 的 `terrain` 块里有映射。
- [ ] 河流像素索引落在 `RIVER_*_INDEX` 范围内。
- [ ] 改完重启，并在 `logs/error.log` 搜新省 ID。
- [ ] 记得改 checksum 相关说明（多人）。

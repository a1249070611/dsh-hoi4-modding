---
title: 3D 模型接入（四层链 / entity / pdxmesh / io_pdx_mesh 工具链）
domain: 05_presentation
scope: models
verified_on: 1.19.x
verified_at: 2026-11-04
sources:
  - gfx/entities/
  - gfx/models/units/
  - gfx/interface/equipmentdesigner/graphic_db/
  - https://github.com/ross-g/io_pdx_mesh
  - https://github.com/Grinsel/stnh_mesh_IO
  - https://github.com/Ireheart/hoi4-models
  - https://github.com/sid00123/KRMI-Collection
  - https://github.com/cwtools/cwtools-hoi4-config
  - https://github.com/amtep/tiger
  - https://github.com/DaanBroekhof/JoroDox
---

# 3D 模型接入

基线 **1.19.x**。路径相对 `<GAME_DIR>` / `<PROJECT_DIR>`。适用：给自定义坦克/底盘/飞机换 3D 模型、复用原版模型、修“模型不显示 / 贴图丢失 / 炮管不转”。

> **原则：先复用原版实体把玩法跑通，再考虑自制 mesh。**
> 本页只讲通用接入链；某个项目里“18 槽坦克设计器怎么排、某型坦克怎么建模”的实战记录属于案例区，不在本页。

## 1. 一句话

一辆车的 3D 显示 =
`graphic_db` 的 `models = { ENTITY }` → `gfx/entities/*.asset` 里的 `entity`（引用 `pdxmesh`）→
`gfx/entities/*.gfx` 里的 `pdxmesh`（引用 `.mesh` + `.anim` + 贴图）→ `gfx/models/units/.../*.mesh` + `*.dds`。

## 2. 四层文件（接入链的核心）

| 层 | 文件 | 关键字段 |
|---|---|---|
| 数据 | `gfx/interface/equipmentdesigner/graphic_db/*.txt` | `models = { GER_medium_armor_entity }`（可多个随机） |
| 实体 | `gfx/entities/units_tanks.asset` | `entity = { name = ... pdxmesh = ... }` + 动画状态 |
| mesh 声明 | `gfx/entities/tanks.gfx` | `pdxmesh = { name = ... file = "gfx/models/units/tanks/xxx.mesh" }` |
| 资源 | `gfx/models/units/tanks/` | `.mesh`（几何/骨骼）+ `.anim`（动画）+ `.dds`（贴图） |

断一层就整条链失效，逐层排查顺序就是这张表从上到下。

原版德国坦克实体（可直接复用，省掉建模）：

```
GER_iw_armor_entity           # 一号/二号这类轻装甲
GER_light_armor_entity
GER_medium_armor_entity       # 三号/四号/黑豹
GER_heavy_armor_entity        # 虎式/虎王
GER_super_heavy_armor_entity  # 鼠式
```

## 3. `entity` 定义示例（`.asset`）

```pdx
entity = {
	name = "GER_medium_armor_entity"
	pdxmesh = "GER_tank_medium_mesh"

	state = { name = "idle" animation = "idle_1" animation_blend_time = 0.4 }
	state = { name = "move" animation = "move_1" animation_blend_time = 0.4 }
	state = { name = "attack" animation = "attack_1" animation_blend_time = 0.2 }
	state = { name = "defend" animation = "defend_1" }
	state = { name = "support_attack" animation = "attack_1" }
	state = { name = "training" animation = "idle_1" }
	state = { name = "death" animation = "death_1" }

	# 特殊效果节点（必须是 mesh 里存在的空节点名，见 §5）
	# barrel / left_tracks / right_tracks / left_exhaust / right_exhaust
}
```

- `pdxmesh` 名字要与 `.gfx` 里注册的一致；`file` 路径相对 `gfx/models/`。
- 动画缺失会导致模型静止/报错；**最少要 `idle`**（生产界面/设计器一进就要有可播的状态）。
- 模型比例/朝向：原版坦克朝向 **+Z 车头**，单位约等于米；自制模型导出前先在 Maya/Blender 里
  统一 scale（10~14 之间常见）与原点（车体中心地面）。

## 4. 贴图规范

原版命名（同目录、同名后缀）：

```
GER_tank_medium_diffuse.dds     # RGB + alpha
GER_tank_medium_normal.dds      # 法线
GER_tank_medium_specular.dds    # 高光
GER_tank_medium_diffuse_desert.dds / _snow.dds   # 可选季节/地形变体
```

- 尺寸**没有硬性 2 的幂要求**，但建议 **1024/2048 的正方形或 2:1**；`.dds` 用 BC3/DXT5（带 alpha），
  纯 diffuse 可用 BC1/DXT1。格式细节见 [dds.md](dds.md)。
- 自制模型最容易踩：**法线（normal）没转成切线空间 / 绿通道反了**（看起来“塑料感”或凹凸反了）。
  HOI4 用 DXT5 存 normal（`ATI2/BC5` 也可），Y 通道按 DirectX 约定。
- 贴图走 `gfx/models/...`，**不是** `gfx/interface/`；2D 图标/界面贴图是完全另一套（见 §7）。

## 5. 特殊节点（特效/动画挂点，即 locator）

mesh 里需要存在这些同名 locator/空节点，引擎才能把特效挂在正确位置：

| 节点 | 用途 |
|---|---|
| `barrel` | 炮口火焰、炮管后坐 |
| `left_tracks` / `right_tracks` | 履带扬尘 |
| `left_exhaust` / `right_exhaust` | 排气烟 |

节点名与 entity 里引用的名称要一致，否则特效不出（日志通常有 `Failed to find locator` 类警告）。
locator 是**空节点**（无几何），跟着骨骼层级走；导出时不要把 locator 合并进车体网格。

## 6. 三条路线（按成本排序）

### 路线 A：复用原版实体（最快）

在 mod 的 `graphic_db` 里给自定义底盘指同阵营/同吨位实体：

```pdx
GER_armor_medium_tank_2 = {
	# ...
	graphic_db = {
		GFX_HTT_medium_tank_2_icon
		models = { GER_medium_armor_entity }
	}
}
```

优点：零建模，动画/特效/国家涂装全包；缺点：30 辆坦克只有 5 张模型脸。
建议按吨位/年份分配：一号/二号→`GER_iw_armor_entity`，三/四号→`GER_light_armor_entity`/`GER_medium_armor_entity`，
黑豹/虎→`GER_medium_armor_entity`/`GER_heavy_armor_entity`，鼠/E-100→`GER_super_heavy_armor_entity`。

### 路线 B：换贴图（伪新模型）

复制一套原版 `.mesh/.anim` 到 mod（保持路径/名称），只替换 `_diffuse/_normal/_specular.dds`。
游戏内表现为“新涂装/新迷彩”，适合战役改色、夏冬涂装、部队专属涂装。

### 路线 C：自制 mesh（成本最高）

1. 建模/绑定（Blender 或 Maya），命名层级、原点、朝向按导出器要求；
2. 工具：Paradox Clausewitz Maya Exporter（Maya 版）；社区标准是 Blender 插件
   `ross-g/io_pdx_mesh`（本机 Blender 4.5 扩展即此插件，`bl_ext.user_default.io_pdx_mesh`）；
3. 导出 `.mesh` + `.anim`，贴图转 `.dds`；
4. 在 `.gfx` 注册 `pdxmesh`，在 `.asset` 写 `entity`（含全部 `state`）；
5. `graphic_db` 里 `models = { 新 entity }`；
6. 进游戏用 `-debug_mode` 观察（模型比例/位置不对用 `nudge` 微调）。

> 自制模型常见失败：mesh 版本/头格式不对（导出器版本对不上目标版本）、缺 `pdxmesh` 注册、
> 动画名不存在、贴图路径大小写错（Linux/Proton 下大小写敏感）。

## 7. 2D 图标 ≠ 3D 模型

- 设计器右上角预览、科技卡图标是 **2D**（`gfx/interface/...` 下 DDS，经 `interface/*.gfx` 注册为 sprite）；
- 设计器中间/右下 3D 视图用 `models` 实体；
- “选择模型”按钮（`select3d_button` / `GFX_3d_view_placeholder`）走原版控件，不改 GUI 就能显示。

装备的 2D 图标 + 3D 模型混合写法：

```pdx
graphic_db = {
	GFX_HTT_medium_tank_2_icon
	models = { GER_medium_armor_entity }
}
```

`GFX_..._icon` 是 `interface/*.gfx` 里的 sprite；`models` 是 3D。sprite 侧规则见 [gfx-sprites.md](gfx-sprites.md)。

## 8. 工具链（GitHub 实测盘点）

| 仓库 | 数据 | 用途 | 判断 |
| --- | --- | --- | --- |
| `ross-g/io_pdx_mesh` | 128★ / 21 fork / GPL-3.0 / 389 commits，最后提交 2024-09-24 | Clausewitz `.mesh`/`.anim` 的 Blender、Maya 导入导出 | **事实标准**；本机 Blender 4.5 扩展即此插件（`bl_ext.user_default.io_pdx_mesh`） |
| `Grinsel/stnh_mesh_IO` | 0★，2026-06-25 | io_pdx_mesh 的 fork，面向新版 Blender | 若官方版不兼容新版 Blender 可评估替换 |
| `cwtools/cwtools-hoi4-config` | 隶属 `cwtools/cwtools`（154★） | VSCode CWTools 规则，含 `Config/gfx/model_entities.cwt` 的 pdxmesh/entity schema | 写 `.gfx`/`.asset` 时能查结构错误，可作本地校验补强 |
| `amtep/tiger` | Rust，CK3/VIC3/Imperator 成熟 | 静态校验器，含 `hoi4/data/gfx.rs` 的 pdxmesh/entity 校验 | **HOI4 支持未完成**，官方声明会产生数千误报，暂不可用 |
| `DaanBroekhof/JoroDox` | 22★，2023-07 | 老工具，`.mesh`→`.obj`/`.x`，主要面向 EU4/CK2 | 只适合逆向查看旧格式，不适合生产 |

**结论：GitHub 上没有“HOI4 3D 模型制作”的完整解决方案。** 生态核心只有 `io_pdx_mesh` 一个插件，
其余是模型搬运合集、静态校验配置、以及无关的 2D GFX 工具。教程主要在 Paradox wiki、官方论坛、Steam 指南与 YouTube。

### 坐标约定（io_pdx_mesh）

`blender_import_export.py` 的映射：**PDX -Z 车头、Y 向上 ↔ Blender -Y 车头、Z 向上**。
模型源文件若按 +X 车头建模，导出前必须旋转。

## 9. 现成模型资产（学习四层链路 / 二次利用，注意授权）

| 仓库 | 内容 | 用途 |
| --- | --- | --- |
| `Ireheart/hoi4-models` | 903 个文件，`gfx/entities/*.asset|*.gfx` + `gfx/models/units/...` 的 `.mesh`/`.dae`/`.obj`/`.dds` 全套 | **最接近完整示例**，可直接对照四层链路写法 |
| `sid00123/KRMI-Collection` | 1204 个文件：444 `.mesh`、663 `.dds`、23 `.asset`、12 `.gfx` | 步兵/单位模型集合，规模最大 |
| `CX13BVA/hoi4_smg_officer` | 2026-09，HQ 人物模型实验 | 人物模型参考 |
| `Julienn-Modelling/HOI4-models-gpl` | 仓库实际为空（仅 1 个目录项） | 不可用 |
| `4upik24/hoi4model` | 空仓库 | 不可用 |
| `Globvs/Ultimate-HOI4-GFX` | 239★，但全是 2D 国策图标/背景 | 与 3D 无关 |

## 10. 排错表

| 症状 | 原因 |
|---|---|
| 设计器 3D 区域空白/黑块 | `models` 引用的 entity 不存在，或 `.gfx` 未注册 `pdxmesh` |
| 模型全黑 | diffuse 丢失/路径错；normal 缺失一般不会全黑 |
| 模型贴图花/发光 | 贴图格式（DXT）与 alpha 通道错；normal 不是切线空间 |
| 炮管/履带特效错位 | mesh 缺 `barrel`/`left_tracks` 节点或命名不一致 |
| 模型骑在地上/浮空/过大 | 导出 scale、原点、朝向不对；用 `nudge` 验证 |
| 模型是国家专属涂装 | 原版实体按国家分配贴图；想统一就用通用实体或自制 |
| Proton/Linux 下贴图丢 | 路径大小写不一致 |

## 11. 检索方法与限制（复现用）

```bash
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=hoi4+models&sort=stars&per_page=10"
```

- 无 token 的 GitHub 搜索 API 限 **10 次/分钟**，超限返回 `API rate limit exceeded`，需间隔 10s+ 重试。
- 若本机走 HTTP(S)_PROXY 且代理无监听，搜索会 `ECONNREFUSED`；临时 `unset` 代理变量再试。
- `raw.githubusercontent.com` 直连可用；仓库页 HTML 也可用 `web_fetch` 读取，但体积大。

## 12. 验收清单

- [ ] `graphic_db` 的 `models = { }` 实体在 `.asset` 中能找到；
- [ ] `.asset` 引用的 `pdxmesh` 在 `.gfx` 注册，`.mesh` 文件存在；
- [ ] entity 至少有 `idle` / `move` / `attack` 三个 `state`；
- [ ] 贴图 `.dds` 齐全（diffuse 必须，normal/specular 建议），格式与尺寸合规（见 [dds.md](dds.md)）；
- [ ] 4 个 locator（`barrel`、左右履带、左右排气）与 entity 引用名一致；
- [ ] 进游戏设计器/生产界面能看到模型，`logs/error.log` 无贴图/entity 报错；
- [ ] 旧存档与新开档都检查（生产中的旧装备可能保留旧模型）。

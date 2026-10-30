# 坦克 3D 模型接入（HOI4 1.19.3 实战）

> 适用：给自定义坦克/底盘换 3D 模型、复用原版模型、修“模型不显示/贴图丢失/炮管不转”。
> 原则：**先复用原版实体把玩法跑通，再考虑自制 mesh**。

## 0. 一句话

一辆坦克的 3D 显示 = `graphic_db` 的 `models = { ENTITY }` → `gfx/entities/*.asset` 里的 `entity`（引用 `pdxmesh`）→
`gfx/entities/*.gfx` 里的 `pdxmesh`（引用 `.mesh` + `.anim` + 贴图）→ `gfx/models/units/tanks/*.mesh` + `*.dds`。

## 1. 四层文件

| 层 | 文件 | 关键字段 |
|---|---|---|
| 数据 | `gfx/interface/equipmentdesigner/graphic_db/*.txt` | `models = { GER_medium_armor_entity }`（可多个随机） |
| 实体 | `gfx/entities/units_tanks.asset` | `entity = { name = ... pdxmesh = ... }` + 动画状态 |
| mesh 声明 | `gfx/entities/tanks.gfx` | `pdxmesh = { name = ... file = "gfx/models/units/tanks/xxx.mesh" }` |
| 资源 | `gfx/models/units/tanks/` | `.mesh`（几何/骨骼）+ `.anim`（动画）+ `.dds`（贴图） |

原版德国坦克实体（可直接复用，省掉建模）：

```
GER_iw_armor_entity           # 一号/二号这类轻装甲
GER_light_armor_entity
GER_medium_armor_entity       # 三号/四号/黑豹
GER_heavy_armor_entity        # 虎式/虎王
GER_super_heavy_armor_entity  # 鼠式
```

## 2. entity 定义示例（`.asset`）

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

	# 特殊效果节点（必须是 mesh 里存在的空节点名）
	# barrel / left_tracks / right_tracks / left_exhaust / right_exhaust
}
```

- `pdxmesh` 名字要与 `.gfx` 里注册的一致；`file` 路径相对 `gfx/models/`。
- 动画缺失会导致模型静止/报错；最少要 `idle`。
- 模型比例/朝向：原版坦克朝向 **+Z / 车头方向**，单位约等于米；自制模型导出前先在 Maya/Blender 里
  统一 scale（10~14 之间常见）与原点（车体中心地面）。

## 3. 贴图规范

原版命名（同目录、同名后缀）：

```
GER_tank_medium_diffuse.dds     # RGB + alpha
GER_tank_medium_normal.dds      # 法线
GER_tank_medium_specular.dds    # 高光
GER_tank_medium_diffuse_desert.dds / _snow.dds   # 可选季节/地形变体
```

- 尺寸没有硬性 2 的幂要求，但建议 **1024/2048 的正方形或 2:1**；`.dds` 用 DXT5/BC3（带 alpha 用 DXT5，纯 diffuse 用 DXT1）。
- 自制模型最容易踩：**法线 (normal) 没转成切线空间/绿通道反了**（看起来“塑料感”或凹凸反了）。
  HOI4 用 DXT5 存 normal（`ATI2/BC5` 也可），Y 通道按 DirectX 约定。
- 贴图走了 `gfx/models/...`，**不是** `gfx/interface/`；2D 图标/界面贴图是另一套。

## 4. 特殊节点（特效/动画挂点）

mesh 里需要存在这些同名 locator/空节点，引擎才能把特效挂在正确位置：

| 节点 | 用途 |
|---|---|
| `barrel` | 炮口火焰、炮管后坐 |
| `left_tracks` / `right_tracks` | 履带扬尘 |
| `left_exhaust` / `right_exhaust` | 排气烟 |

节点名与 entity 里引用的名称要一致，否则特效不出（日志通常有 `Failed to find locator` 类警告）。

## 5. 三条路线

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

优点：零建模、动画/特效/国家涂装全包；缺点：30 辆坦克只有 5 张模型脸。
建议按吨位/年份分配：一号/二号→`GER_iw_armor_entity`，三/四号→`GER_light_armor_entity`/`GER_medium_armor_entity`，
黑豹/虎→`GER_medium_armor_entity`/`GER_heavy_armor_entity`，鼠/E-100→`GER_super_heavy_armor_entity`。

### 路线 B：换贴图（伪新模型）
复制一套原版 `.mesh/.anim` 到 mod（保持路径/名称），只替换 `_diffuse/_normal/_specular.dds`。
游戏内表现为“新涂装/新迷彩”，适合战役改色、夏冬涂装、部队专属涂装。

### 路线 C：自制 mesh（成本最高）
1. 建模/绑定（Maya 或 Blender），命名层级、原点、朝向按官方导出器要求；
2. 官方工具：Paradox Clausewitz Maya Exporter（Maya 版）；社区：Blender 的
   `io_scene_hoi4` / `Clausewitz-Maya-Exporter` 对应插件；
3. 导出 `.mesh` + `.anim`，贴图转 `.dds`；
4. 在 `.gfx` 注册 `pdxmesh`，在 `.asset` 写 `entity`（含全部 `state`）；
5. `graphic_db` 里 `models = { 新 entity }`；
6. 进游戏用 `debug` 模式观察（模型比例/位置不对用 `nudge` 微调）。

> 自制模型常见失败：mesh 版本/头格式不对（导出器版本对不上 1.19）、缺 `pdxmesh` 注册、
> 动画名不存在、贴图路径大小写错（Linux/Proton 下大小写敏感）。

## 6. 2D 图标 ≠ 3D 模型

- 设计器右上角预览、科技卡图标是 **2D**（`gfx/interface/...` 下 DDS，经 `interface/*.gfx` 注册）；
- 设计器中间/右下 3D 视图用 `models` 实体；
- “选择模型”按钮（`select3d_button` / `GFX_3d_view_placeholder`）走原版控件，不改 GUI 就能显示。

装备的 2D 图标池写法：

```pdx
graphic_db = {
	GFX_HTT_medium_tank_2_icon
	models = { GER_medium_armor_entity }
}
```

`GFX_..._icon` 是 `interface/*.gfx` 里的 sprite；`models` 是 3D。

## 7. 排错表

| 症状 | 原因 |
|---|---|
| 设计器 3D 区域空白/黑块 | `models` 引用的 entity 不存在，或 `.gfx` 未注册 pdxmesh |
| 模型全黑 | diffuse 丢失/路径错；normal 缺失一般不会全黑 |
| 模型贴图花/发光 | 贴图格式（DXT）与 alpha 通道错；normal 不是切线空间 |
| 炮管/履带特效错位 | mesh 缺 `barrel`/`left_tracks` 节点或命名不一致 |
| 模型骑在地上/浮空/过大 | 导出 scale、原点、朝向不对；用 nudge 验证 |
| 模型是国家专属涂装 | 原版实体按国家分配贴图；想统一就用通用实体或自制 |
| Proton/Linux 下贴图丢 | 路径大小写不一致 |

## 8. 验收清单

- [ ] `graphic_db` 的 `models = { }` 实体在 `.asset` 中能找到；
- [ ] `.asset` 引用的 `pdxmesh` 在 `.gfx` 注册，`.mesh` 文件存在；
- [ ] entity 至少有 `idle`/`move`/`attack` 三个 state；
- [ ] 贴图 `.dds` 齐全（diffuse 必须，normal/specular 建议）；
- [ ] 进游戏设计器/生产界面能看到模型，无 error.log 贴图/entity 报错；
- [ ] 旧存档与新开档都检查（生产中的旧装备可能保留旧模型）。

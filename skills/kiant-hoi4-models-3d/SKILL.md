---
name: kiant-hoi4-models-3d
description: HOI4 三维模型与实体：.mesh/.asset 关系、entity 定义、模型替换、贴图与材质、单位模型挂接、常见导入失败原因。工具链边界说明。
---

# 模型与实体

## 三层结构

```
.mesh  ← 二进制网格（Blender/Maya 用 Paradox 导出插件生成）
  ↑
.asset ← entity 定义，把 mesh + 材质 + 挂点 + 缩放串起来
  ↑
脚本   ← equipment / units / 事件 里引用 entity 名
```

改模型通常只动 `.asset` 与贴图；`.mesh` 是二进制，脚本层面改不了。

## entity 定义

`gfx/entities/*.asset`：

```
entity = {
	name = "GER_autobahn_truck_entity"
	pdxmesh = "gfx/models/units/truck/generic_truck.mesh"

	scale = 1.0

	attach = {
		id = "turret"
		parent = "GER_autobahn_truck_entity"
	}
}
```

要点：

- `name` 是全局唯一的实体名，脚本引用它
- `pdxmesh` 路径相对 mod 根目录，**正斜杠、带扩展名**
- 路径大小写敏感：Windows 上错大小写能跑，Steam Deck / Linux 上直接加载失败
- `attach` / `animation` 等挂点块必须与 mesh 里实际的骨骼/挂点同名，写错不会报错，只是不生效

## 单位模型怎么挂上去

装备原型（`common/units/equipment/*.txt`）通过 `archetype` 与模型挂钩，单位的视觉表现来自 `gfx/entities` 与 `gfx/models` 的组合。

这块不同大版本有差异，**不要凭记忆写**：

```
kiant_hoi4_kb_lookup kind=entity limit=3
kiant_hoi4_kb_search "archetype" source=vanilla
```

先看原版真实写法，再照抄结构。这是知识库存在的意义。

## 贴图

- 格式 DDS，单位模型常用 DXT5
- 尺寸建议 2 的幂
- 材质在 `.asset` 或材质文件里引用，路径同样相对 mod 根、正斜杠
- 缺贴图表现为纯白/粉黑，`error.log` 会有 texture 相关行

## 导入失败的常见原因

| 现象 | 原因 |
|---|---|
| 模型完全不显示 | `.mesh` 路径错、大小写错、或 entity 名未被任何脚本引用 |
| 显示但全白 | 贴图路径错、DDS 未压缩、或材质未绑定 |
| 模型朝向错误 | 导出时坐标系不对（Paradox 要求 Z 轴向上） |
| 缩放离谱 | `.asset` 里 `scale` 与原 mesh 尺寸不匹配 |
| 动画不播放 | 动画未包含在导出里，或 `animation` 块名与 mesh 内不一致 |
| 游戏崩溃 | 网格顶点数/骨骼数超出引擎限制，或 .mesh 版本与游戏不兼容 |

## 工具链边界（说清楚，避免浪费时间）

这个插件**不做**以下事情，别指望：

- 生成或编辑 `.mesh`（二进制，需要 Blender + Paradox 导出插件）
- 转换图片格式（用 ImageMagick / GIMP）
- 预览 3D 模型（离线预览只渲染 2D 数据，不渲染模型）

它能做的是：

- 校验 `.asset` 里引用的 mesh / 贴图文件**是否真的存在**（`assets` 校验器）
- 统计 entity 定义、查重名
- 从知识库取出原版真实 entity 写法供参照
- 定位 `error.log` 里模型相关的报错

## 工作流

1. `kiant_hoi4_kb_lookup kind=entity` 看原版怎么组织
2. 复制一份原版 `.asset` 改名，替换 `pdxmesh` 与贴图路径
3. 跑 `kiant_hoi4_validate_mod deep=true`，`assets` 校验器会告诉你哪个文件不存在
4. 进游戏 `-debug_mode`，看 `error.log` 是否有 mesh 加载失败
5. 只有第 3 步干净了，再去看视觉问题

先保证文件引用正确，再谈美术效果。反过来的话，你会在「是模型错了还是路径错了」之间反复横跳。

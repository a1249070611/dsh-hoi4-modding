---
name: kiant-hoi4-technology
description: HOI4 科技树编写：technologies 结构、folder 与坐标、start_year/research_cost、前置与依赖、装备解锁、科技分类、AI 权重，以及科技不显示/不可研究的排查。
---

# 科技树

## 文件与结构

`common/technologies/*.txt`，根键 `technologies = { ... }`。

两种写法都真实存在，先看你要改的模组用的是哪种：

**扁平式**（多数现代模组，tech 直接挂在 `technologies` 下，folder 写在 tech 内部）：

```
technologies = {

	GER_autobahn_1 = {
		start_year = 1936
		research_cost = 1.0
		folder = {
			name = GER_autobahn_folder
			position = { x = 0 y = 0 }
		}
		path = {
			leads_to_tech = GER_autobahn_2
			research_cost_coeff = 1
		}
		categories = {
			industry
		}
		ai_will_do = { factor = 1 }
	}
}
```

**分组式**（原版部分文件）：`technologies = { 分类 = { tech = { ... } } }`。

判断方法：看一个块里有没有 `start_year` / `research_cost`，有就是 tech，没有就是分组。

## 字段

| 字段 | 作用 |
|---|---|
| `start_year` | 最早可研究年份，早于它不会出现在科技树 |
| `research_cost` | 研究成本系数（相对值，不是天数） |
| `folder` | 所属树分组，`name` + `position {x y}` 决定格子位置 |
| `path` | 连线：`leads_to_tech`（后继）、`research_cost_coeff`（后续成本倍率） |
| `dependencies` | 硬前置：`tech_id = 1`，不满足无法研究 |
| `categories` | 科技分类，影响加成卡与 AI 倾向 |
| `enable_equipments` | 解锁装备原型 |
| `enable_equipment_modules` | 解锁装备模块 |
| `ai_will_do` | AI 研究倾向权重 |

`path` 和 `dependencies` 的区别最容易混：

- `path` 只画连线，**不阻止**研究（视觉上的树结构）
- `dependencies` 是真前置，数值是额外成本倍率

只写 `path` 不写 `dependencies`，玩家可以跳着研究——看起来像 bug，其实是你没写硬前置。

## folder 与分类

`folder.name` 决定科技树界面里的分组标题。用原版已有的名字（如 `infantry_folder`、`artillery_folder`）可以直接复用原版界面与本地化；自建 folder 需要自己提供本地化键。

`categories` 里的自定义分类必须在 `common/technology_tags` 里声明，否则引擎忽略、加成卡不会作用。不确定时先用原版已有分类（`industry`、`armor`、`infantry`、` artillery`、`naval`、`air`）。

## 本地化

每个 tech 需要两个键：

```
 GER_autobahn_1:0 "Reichsautobahn I"
 GER_autobahn_1_desc:0 "First trunk routes, 1936 standard."
```

缺主键 → 科技树里出现空白格子。缺 `_desc` → 悬停提示为空，不影响功能。

## 科技不显示 / 点不了

| 症状 | 原因 |
|---|---|
| 完全看不到 | `start_year` 晚于当前年份；或 `folder` 的 position 与别的科技重叠被盖住 |
| 灰的但能看见 | `dependencies` 未满足；或 `start_year` 已到但前置科技没研究 |
| 显示了但点不动，无提示 | 缺 `categories` 且被 AI/界面过滤；检查是否被 `enable_equipments` 影响 |
| 研究后装备没解锁 | `enable_equipments` 里的原型名拼错，或该原型未在 `common/units/equipment` 定义 |
| 树是乱的 | `position {x y}` 同一 folder 内重叠。x 步长 1，y 步长 2 的倍数比较安全 |

## 大改科技树的现实建议

改原版科技树（比如整体重排）几乎必然要覆盖原版文件，维护成本高：

1. 先从知识库取原版实现：`kiant_hoi4_kb_lookup kind=tech limit=3`，看真实结构
2. 用 `kiant_hoi4_kb_symbol` 查你想改的 tech 在哪些文件里被引用（装备、AI、事件都可能引用）
3. 新增科技优先「追加新文件」而不是改原版文件
4. 每加一个 tech 跑 `kiant_hoi4_validate_mod deep=true`，科技校验器会检查前置目标是否存在、本地化是否齐全

## 校验

科技校验器（`technology`）会报：

- 前置/后继目标找不到定义（拼错，或在未索引的 mod 里）
- 缺主本地化键（error）
- 缺 `_desc`（warn）

需要先 `kiant_hoi4_kb_build` 索引原版，才能确认「目标在原版里」而不误报。

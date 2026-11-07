---
name: kiant-hoi4-events-decisions
description: HOI4 事件与决议编写：namespace 规则、触发方式、MTTH 与随机权重、选项与 AI 概率、隐藏事件、决议分类与冷却、以及事件不触发的排查。
---

# 事件与决议

## 事件文件位置与 namespace

`events/<任意名>.txt`。文件顶部必须有：

```
add_namespace = mymod
```

之后事件 id 一律写成 `mymod.<数字>`：

```
country_event = {
	id = mymod.1
	title = mymod.1.t
	desc = mymod.1.d
	picture = GFX_report_event_generic_army
	is_triggered_only = yes

	option = {
		name = mymod.1.a
		add_political_power = 25
	}
}
```

**缺 `add_namespace` 的事件不会注册，且没有任何报错。** 这是第二大坑（第一是本地化 BOM）。

事件类型：`country_event`、`state_event`、`news_event`、`unit_leader_event`、`operative_leader_event`。

## 触发方式

| 写法 | 行为 |
|---|---|
| `is_triggered_only = yes` | 只在被 effect 调起时触发（`country_event = { id = mymod.1 }`） |
| `mean_time_to_happen = { months = 6 }` | 满足 `trigger` 后开始计时，平均 6 个月触发 |
| `fire_only_once = yes` | 全局只触发一次 |
| `hidden = yes` | 不弹窗，只执行 `immediate` |
| `major = yes` | 全屏大事件 |

MTTH 可以按条件调整：

```
mean_time_to_happen = {
	months = 12
	modifier = {
		factor = 0.5
		has_war = yes
	}
	modifier = {
		factor = 2
		has_stability > 0.6
	}
}
```

`factor < 1` 加速，`> 1` 减速。想让某条件下永不触发，别用 MTTH，改用 `trigger` 里的 `NOT`。

## 选项与 AI 选择

```
option = {
	name = mymod.1.a
	add_political_power = 50
	ai_chance = {
		factor = 80
		modifier = {
			factor = 0
			has_government = communism
		}
	}
}
```

多个 option 的 `ai_chance` 是相对权重，不是百分比。某个选项写 `factor = 0` 时 AI 永不选——但玩家仍可选，适合放"只有玩家会做的激进选项"。

## immediate 与 option 的选择

- `immediate` 在事件一出现就执行，**玩家还没看到界面**。适合设置 flag、记录状态。
- `option` 里的 effect 在玩家点击后执行。

想在选项里给不同效果，就把 effect 写进对应 option。

## 决议

`common/decisions/<任意名>.txt`。结构是两层：分类 → 决议。

```
GER_decisions = {
	icon = GFX_decision_generic_political_rally
	allowed = { always = yes }
	visible = { always = yes }
	available = { always = yes }

	GER_autobahn_program = {
		icon = GFX_decision_generic_political_rally
		cost = 150
		days_remove = 90
		available = {
			has_political_power > 100
		}
		complete_effect = {
			add_ideas = GER_autobahn
		}
		ai_will_do = { factor = 1 }
	}
}
```

分类 id 与决议 id 都要有本地化（各带 `_desc`）。

### 常用字段

| 字段 | 说明 |
|---|---|
| `cost` | 政治点数花费 |
| `days_remove` | 执行耗时，完成后移除 |
| `days_re_enable` | 完成后多久可再点 |
| `fire_only_once = yes` | 只能执行一次 |
| `remove_effect` | 执行完毕时的效果（配合 `days_remove`） |
| `complete_effect` | 立即完成时的效果（无 `days_remove` 时） |
| `is_good = yes` | 影响 AI 评估倾向 |
| `target_trigger` | 需要选目标时用（如选国家） |
| `on_map_mode` | 决议是否在地图上选点 |

`days_remove` 与 `complete_effect` 的配合最容易搞错：**有 `days_remove` 时，进度条走完执行 `remove_effect`**；`complete_effect` 用于无耗时决议。写反了就是"点了没效果"。

## 事件的本地化三件套

```
 mymod.1.t:0 "标题"
 mymod.1.d:0 "正文"
 mymod.1.a:0 "选项文字"
```

`title` / `desc` 不写时会回退到 `<id>.t` / `<id>.d`；option 不写 `name` 时回退到 `<id>.a`、`<id>.b`。但**显式写出来更可控**，尤其是选项顺序调整时。

## 事件不触发的排查

1. `add_namespace` 漏了 → 事件根本没注册（`kiant_hoi4_validate_mod` 会报命名空间未声明）
2. `trigger` 恒假 → 逐条拆开验证，特别注意用了 effect 语法
3. `is_triggered_only = yes` 但没有任何地方调它
4. 同名 id 被别的文件覆盖
5. MTTH 太长 + `trigger` 只在特定条件下成立 → 看起来"永不触发"
6. 缺本地化 → 事件触发了但显示为键名，容易被误判为没触发

用控制台直接测：

```
event mymod.1
```

能弹出来说明事件注册成功，问题在触发条件上。

## 设计建议

- 事件 id 按模块分段（`mymod.1-99` 政治、`100-199` 军事），后期好维护
- 每个事件至少给一个"什么都不做"的选项，除非刻意逼迫玩家
- `hidden = yes` 的机制事件记得 `fire_only_once`，否则可能反复触发
- 大量小事件优先用 `on_actions` 驱动，而不是几十个 MTTH 轮询

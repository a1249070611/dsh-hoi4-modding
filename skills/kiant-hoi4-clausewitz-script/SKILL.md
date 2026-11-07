---
name: kiant-hoi4-clausewitz-script
description: Clausewitz 脚本语言规则：语法结构、作用域链、trigger 与 effect 的区别、条件块、随机权重、变量与 flag、scripted_effects/triggers 复用。写 HOI4 逻辑时的语法依据。
---

# Clausewitz 脚本语法

## 基本形式

一切皆 `键 = 值`，块用花括号，**没有分号，没有逗号**（数组靠空格分隔）。

```
key = value
key = { ... }
key = "带空格的字符串"
```

注释用 `#`，到行尾。

```
# 这是注释
add_political_power = 50   # 行尾注释也合法
```

数值不带单位，布尔用 `yes` / `no`（不是 `true` / `false`）。字符串需要空格或特殊字符时才加引号，但涉及本地化键、文件路径时**一律加引号更安全**。

## 重复键是合法的

同名键可以出现多次，引擎按上下文决定取哪一个：

```
option = { ... }      # 事件有多个 option，靠重复键表达
option = { ... }
```

但有 id 语义的重复（两个 `focus` 用同一个 `id`）会被静默丢弃一个——这是"写了没效果"的头号原因。

## 作用域链

Trigger 和 effect 都运行在某个作用域里（country / state / character / division / province…），`common/` 下的内容大多以 country 开头。

| 记号 | 含义 |
|---|---|
| `ROOT` | 当前执行链的起点（通常是事件目标国） |
| `THIS` | 当前作用域 |
| `FROM` | 上一步的来源对象（如事件发起者） |
| `PREV` | 上一层作用域 |

切换作用域：

```
GER = { ... }                 # 切到德国
owner = { ... }               # 切到当前州的拥有者
every_country = { ... }       # 遍历
random_owned_state = { ... }
```

## Trigger 与 effect 的区别

- **Trigger** 返回布尔，只能出现在 `trigger` / `limit` / `available` / `visible` / `allowed` 这类判断位。
- **Effect** 改变游戏状态，只能出现在 `effect` / `immediate` / `completion_reward` / `complete_effect` 这类执行位。

放错位置不会报错，只是整块被忽略。这是最难查的一类 bug——**看到某个条件"永远不生效"，先确认它没被写进 effect 槽位**。

```
# 正确：trigger
available = {
	has_political_power > 100
	NOT = { has_war = yes }
}

# 正确：effect
completion_reward = {
	add_political_power = 50
}
```

## 条件组合

```
available = {
	AND = {
		tag = GER
		has_government = fascism
	}
	OR = {
		has_war = yes
		has_country_flag = emergency
	}
	NOT = { is_in_faction = yes }
}
```

`AND` 也可以省略——块内多个条件默认是"与"：

```
available = {
	tag = GER
	has_government = fascism
}
```

## 条件分支

```
if = {
	limit = { has_political_power > 100 }
	add_political_power = -50
}
else_if = {
	limit = { has_political_power > 50 }
	add_stability = 0.05
}
else = {
	add_stability = -0.05
}
```

`else` 不带 `limit`。

## 随机与权重

按权重二选一：

```
random_list = {
	70 = { add_political_power = 25 }
	30 = { add_stability = -0.05 }
}
```

带条件限制时用 `random`：

```
random = {
	chance = 25
	modifier = {
		add = 25
		has_idea = GER_rearmament
	}
	add_political_power = 50
}
```

国策/决议的 AI 权重用 `ai_will_do`：

```
ai_will_do = {
	factor = 1
	modifier = {
		factor = 2
		has_war = yes
	}
}
```

`factor = 0` 表示 AI 永不主动选。

## 变量与 flag

两者别混用：flag 是布尔标记，变量存数值。

```
# flag
set_country_flag = GER_rearmed
clr_country_flag = GER_rearmed
has_country_flag = GER_rearmed

# 变量
set_variable = { GER_progress = 3 }
add_to_variable = { GER_progress = 1 }
check_variable = { GER_progress > 2 }
```

变量名建议带 TAG 前缀，否则容易和别的 mod 撞。

## 复用：scripted_effects / scripted_triggers

`common/scripted_effects/` 里定义，之后任何地方直接当 effect 名调用：

```
# common/scripted_effects/mymod_effects.txt
GER_give_industry_boost = {
	add_ideas = GER_autobahn
	add_tech_progress = { tech = industry_1939 progress = 0.5 }
}
```

```
# 调用处
completion_reward = {
	GER_give_industry_boost = yes
}
```

`scripted_triggers` 同理，写在 `common/scripted_triggers/`，调用处当 trigger 用。

**注意**：`scripted_effect` / `scripted_trigger` 允许重名覆盖（这是特性，方便做兼容补丁），所以校验工具不会把它们报成重复。

## 常见静默失效清单

| 写法 | 结果 |
|---|---|
| trigger 写进 effect 槽 | 整块被忽略 |
| effect 写进 trigger 槽 | 视为恒假 |
| `has_government = Fascism`（大小写） | 恒假，枚举值全小写 |
| 拼错 effect 名（如 `add_politcal_power`） | 该行被忽略，其余照常执行 |
| `limit` 里用了 effect | 条件恒真 |
| 事件缺 `add_namespace` | 事件不注册，无提示 |
| 国策 `available` 里引用未定义 idea | 恒假 |

遇到"逻辑对但没反应"，先用 `kiant_hoi4_parse_script` 确认文件结构被正确解析，再看 `error.log` 有没有 `could not find` / `invalid`。

## 数值惯例

- 政治点数、陆军经验等整数资源：直接写整数
- 稳定度、战争支持度、各种 `factor`：写小数（`0.05` = 5%）
- 时间：`days = 30` / `months = 6` / `years = 1`
- 日期：字符串 `"1939.9.1"`

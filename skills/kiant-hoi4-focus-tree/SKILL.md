---
name: kiant-hoi4-focus-tree
description: HOI4 国策树编写：focus_tree 结构、坐标布局、前置与互斥、可用性条件、完成奖励、AI 权重、共享国策、以及国策不显示的排查。
---

# 国策树

## 文件位置

`common/national_focus/<任意名>.txt`。一个文件可以放多个 `focus_tree`，一棵树属于一个国家（或一组国家）。

## 骨架

```
focus_tree = {
	id = ger_my_tree
	country = {
		factor = 0
		modifier = {
			add = 10
			tag = GER
		}
	}
	default = no

	focus = {
		id = GER_autobahn
		icon = GFX_focus_generic_industry_2
		cost = 10
		x = 0
		y = 0
		completion_reward = {
			add_political_power = 50
		}
	}
}
```

### `country` 块决定谁拥有这棵树

`factor = 0` 加上 `modifier` 是标准写法：基础权重 0，满足条件才 +10 抢到。多个 mod 都定义了某国树时，权重高的胜出。

`default = no` 表示这棵树不是"无人认领时的兜底树"。做通用树（比如所有小国共用的那棵）时才有意义。

## 坐标系统

- `x` 横向，`y` 纵向，`y` 向下增大
- 同 `y` 上的国策左右排列，**同一行不能重叠**（重叠会导致图标互相压住，不报错）
- 间距惯例：横向步长 2（`x = 0, 2, 4`），纵向步长 1 或 2
- 树宽超过约 12 列，界面就会出现横向滚动

用 `relative_position_id` 可以相对某个国策定位，改结构时比绝对坐标省事：

```
focus = {
	id = GER_autobahn_2
	relative_position_id = GER_autobahn
	x = 0
	y = 1
	...
}
```

## 前置与互斥

```
focus = {
	id = GER_rearm
	prerequisite = { focus = GER_autobahn }
	prerequisite = { focus = GER_industry }     # 再来一行表示"或"
	mutually_exclusive = { focus = GER_purge }
	...
}
```

关键区别：

- **同一个 `prerequisite` 块里写多个 `focus`** → 需要全部满足（与）
- **写多个 `prerequisite` 块** → 满足任一即可（或）

这个语义很容易写反，写完用 `kiant_hoi4_parse_script` 打印出来核对结构。

## 条件

| 槽位 | 语义 |
|---|---|
| `available` | 不满足时国策灰显、不可点 |
| `bypass` | 满足时自动完成，跳过等待 |
| `cancel` | 满足时中断正在进行的国策 |
| `will_lead_to_war_with` | 目标国，用于界面提示 |

```
available = {
	has_political_power > 50
	NOT = { has_war_with = SOV }
}
bypass = {
	has_tech = industry_1939
}
```

`available` 恒假 = 国策永久灰掉。常见原因是里面写了 effect，或引用了不存在的 idea / flag。

## 完成奖励

```
completion_reward = {
	add_political_power = 50
	add_ideas = GER_autobahn
	if = {
		limit = { has_war = yes }
		add_war_support = 0.1
	}
}
```

想给玩家看效果提示但不想真生效，用 `custom_effect_tooltip = my_tooltip_key` 配合空 effect。

## AI 权重

```
ai_will_do = {
	factor = 1
	modifier = {
		factor = 3
		has_war = yes
	}
	modifier = {
		factor = 0
		has_government = communism
	}
}
```

`factor = 0` 是彻底禁止 AI 选。AI 不会评估 `completion_reward` 的价值，只按这里给的权重选——所以重要国策记得手动提权重，否则 AI 可能永远不走。

## 共享国策

多国共用的国策放 `shared_focus = { ... }`，然后在各国树里用 `focus = { id = 某共享id }` 引用：

```
shared_focus = {
	id = shared_industrial_effort
	icon = GFX_focus_generic_industry_2
	cost = 10
	completion_reward = { ... }
}
```

共享国策的 `id` 同样全局唯一。

## 国策不显示 / 点不了的排查

1. **树没被认领** —— `country` 块的 `factor` 为 0 且没命中 `modifier`，这棵树谁都不属于。检查 `tag` 是否拼对。
2. **id 重复** —— 与别的文件（包括原版、别的 mod）撞了。用 `kiant_hoi4_find_duplicate_ids`。
3. **图标 sprite 不存在** —— 国策显示为问号或空白。`error.log` 会有 `Could not find sprite GFX_...`。

   原版确实存在的通用图标（1.19.4.2 实测，逐个 grep 过 `interface/*.gfx`）：

   ```
   GFX_focus_generic_industry_1    _2    _3
   GFX_focus_generic_military_academy
   GFX_focus_generic_military_dictatorship
   GFX_focus_generic_army_attack
   GFX_focus_generic_navy_battleship2
   GFX_focus_generic_air_bases
   ```

   ⚠️ **没有** `GFX_focus_generic_political`、`GFX_focus_generic_research`、`GFX_focus_generic_diplomacy` 这些名字——很多教程在传，但原版里不存在。

   别背名单，查：

   ```
   kiant_hoi4_kb_symbol name=GFX_focus_generic_industry_2     # 在不在，在哪
   grep -r "GFX_focus_generic_" 游戏安装目录/interface/ | head
   ```

   每个国策通常还配一个 `同名_shine`（高亮层），原版成对出现；只写主体也能用，只是没有悬停高亮。
4. **缺本地化** —— 按钮显示键名。`GER_x` 和 `GER_x_desc` 两个都要有。
5. **坐标重叠** —— 被别的国策盖住，视觉上"消失"了。
6. **`available` 恒假** —— 灰显，鼠标悬停能看到未满足条件。

## 布局建议

做大体量树（50+ 国策）时的实用做法：

- 先画草图定主干（纵向 10–15 层），再挂支线
- 每条支线独立 `x` 区间，避免后期互相挤压
- 用 `relative_position_id` 而不是硬编码绝对坐标，改主干时支线自动跟随
- 每加 5–10 个国策跑一次 `kiant_hoi4_validate_mod`，别攒到最后

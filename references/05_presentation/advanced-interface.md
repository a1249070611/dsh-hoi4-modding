---
title: 进阶界面（map_modes / alerts / tooltip / scripted loc 联动）
domain: 05_presentation
scope: interface
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 进阶界面

## 1. 脚本化地图模式（Scripted map modes）

官方文档：**`common/map_modes/documentation.md`**（本机原版自带；`common/map_modes/` 下**只有**这一个文件，没有 `.txt` 实例——⚠️ 本机无原版用例，字段全部来自该文档）。

文件位置：`common/map_modes/*.txt`，最外层 `scripted_map_modes = { <名字> = { ... } }`。

```pdx
# mod 里：common/map_modes/NS_map_modes.txt
scripted_map_modes = {

	NS_dashboard_map_mode = {

		# 两层：top 与 bottom，渲染顺序 bottom -> top，结构完全一样
		top = {
			# type 决定“按什么边界渲染”，必须是以下之一：
			#   none            什么都不画
			#   country         按国家省份
			#   state           按州省份
			#   state_controller 按州省份 + 控制者（一个州被多国控制会分别回调）
			#   或硬编码层：game_map_mode_country / game_map_mode_states / game_map_mode_diplomacy /
			#              game_map_mode_players / game_map_mode_factions / game_map_mode_ideology
			#              （用硬编码层时其它层字段被忽略）
			type = country

			# 颜色：返回 true 才渲染；由脚本设置临时变量 red/green/blue/alpha
			color = {
				set_temp_variable = { red = 0.0 }
				set_temp_variable = { green = 1.0 }
				set_temp_variable = { blue = 0.0 }
				set_temp_variable = { alpha = 1.0 }

				# 只有父层写了 thickness = yes 时才需要
				set_temp_variable = { thickness = 10.0 }

				# 置 1 会脉冲闪烁
				set_temp_variable = { highlighted = 1.0 }
			}

			# 强烈建议写：限定参与渲染的 scope，写法同 targeted decision
			targets = {
				# target_array = NS_map_icon_array
				# targets / target_trigger ...
			}

			thickness = yes          # 是否带“边界厚度”
		}

		bottom = {
			type = none
		}

		# 地图上的文字（必须取以下之一）
		far_text = country       # none / country / state / faction / player
		near_text = state

		# 每天刷新；否则靠 force_update_map_mode effect 手动刷新
		update_daily = yes
	}
}
```

### 必须一并提供的本地化与图标（文档明确列出）

```yml
 MAPMODE_NS_DASHBOARD_MAP_MODE: "发展度"
 MAPMODE_NS_DASHBOARD_MAP_MODE_NAME: "发展度地图"
 MAPMODE_NS_DASHBOARD_MAP_MODE_DESCRIPTION: "按国家发展度着色。"
 ns_dashboard_map_mode_tooltip: "..."
 ns_dashboard_map_mode_tooltip_delayed: "..."
```

图标 sprite 名（写进 `interface/*.gfx`）：

```pdx
spriteType = { name = "GFX_mapmode_buttons_deselected_small_ns_dashboard_map_mode" texturefile = "gfx/interface/NS/mapmode_off.dds" }
spriteType = { name = "GFX_mapmode_buttons_selected_small_ns_dashboard_map_mode"   texturefile = "gfx/interface/NS/mapmode_on.dds" }
```

即：`MAPMODE_<大写名>` / `_NAME` / `_DESCRIPTION` 三组 loc + `GFX_mapmode_buttons_{deselected,selected}_small_<小写名>` 两个 sprite。名字对不上 → 地图模式按钮空白/不可用。

### 性能

- `targets` 不写 → 引擎会对**每个国家/州**回调 `color` 块。文档原话：「highly recommended for perfomance」。一个国家 200 州时，少写 `targets` 就是每帧几千次脚本求值。
- `update_daily = no` + 手动 `force_update_map_mode` 是更省的做法。

## 2. 警报（Alerts）

| 项 | 事实 |
|---|---|
| 定义 | `common/alerts.txt`（176 行）：`alerts = { alert_xxx = { category = HIGH/MEDIUM/LOW } }` |
| 数量分布（实测） | `LOW` 27、`HIGH` 24、`MEDIUM` 4 |
| 界面 | `interface/alerts.gui`（2 个容器：`global_alerticon_window` / `global_diplorequesticon_window`） |
| 贴图 | `interface/alerts.gfx`（`GFX_global_alert_icons`、`GFX_green_alert_glow`、`GFX_yellow_alert_glow`、`GFX_red_alert_glow` 等） |
| 触发 | 引擎按内置条件评估（如 `alert_low_supply`、`alert_naval_invasion`）；**脚本侧没有“新增一个 alert 定义并用 trigger 驱动”的公开入口** ⚠️ 未在本机找到，原版字段只有 `category` |

```pdx
# common/alerts.txt 节选
alerts = {
	alert_hostile_troops = { category = MEDIUM }
	alert_enemy_air_superiority = { category = HIGH }
	alert_low_supply = { category = MEDIUM }
	alert_very_low_supply = { category = HIGH }
}
```

**实用结论**：mod 能做的是**调整既有警报的优先级分组**（新增文件 + 同名 `alerts = { }` 追加/覆盖），做“全新警报类型”基本不可行（无文档、无原版先例）。想要“提醒玩家”，用**决议 + 事件 + scripted GUI 面板**替代。

## 3. 决议/分类图标（最常被漏的一步）

| 资源 | 位置 | 尺寸（实测） |
|---|---|---|
| 分类图标 | `gfx/interface/decisions/decision_category_*.dds` | 约 **40×51**（`decision_category_generic.dds` = 40×51） |
| 决策图标 | `gfx/interface/decisions/decisions_*.dds` | 约 **32×33**（多帧按钮则竖排，如 `_0.._3` 4 帧） |
| 注册 | `interface/decisions.gfx`（662 个 sprite；519 个 dds 文件） | — |

```pdx
# interface/NS_decisions.gfx
spriteTypes = {
	spriteType = {
		name = "GFX_decision_category_NS_dashboard"
		texturefile = "gfx/interface/decisions/decision_category_NS_dashboard.dds"
	}
	spriteType = {
		name = "GFX_decision_NS_do_nothing"
		texturefile = "gfx/interface/decisions/decisions_NS_do_nothing.dds"
	}
}
```

```pdx
NS_dashboard_category = {
	icon = GFX_decision_category_NS_dashboard     # 分类图标
	...
	NS_dashboard_do_nothing = {
		icon = GFX_decision_NS_do_nothing          # 决策图标
	}
}
```

原版两种 `icon` 写法都出现（`icon = GFX_decision_oil` 与 `icon = generic_tank`），**统一写全 `GFX_` 最安全**。

## 4. Tooltip 体系（四种，别混）

| 场景 | 写法 | 作用域/限制 |
|---|---|---|
| GUI 元素悬停 | `.gui` 里 `pdx_tooltip = KEY` | **`$var$` 不展开**；`[命名空间]` 需要该界面挂在 scripted GUI 上 |
| GUI 元素悬停（带引擎上下文） | `.gui` 里 `context_aware_tooltip = KEY` | 只在角色/特质等有上下文的元素上有效 |
| 效果/触发器的提示 | `custom_effect_tooltip = KEY` / `custom_trigger_tooltip = { tooltip = KEY ... }` | 支持 `[命名空间]` 与 bindable 变量 |
| 修正（modifier）提示 | 由引擎生成 | 自定义 modifier tooltip **不支持**脚本化本地化 |

带参数的效果提示（bindable，1.15+）：

```pdx
custom_effect_tooltip = {
	localization_key = NS_gain_tt
	AMOUNT = 25
	RESOURCE = "£pol_power"
}
```

```yml
 NS_gain_tt: "获得 §G$AMOUNT$§! $RESOURCE$"
```

## 5. 脚本化本地化 ↔ 界面联动

### 5.1 用 `defined_text` 让同一段文字随条件变化

`common/scripted_localisation/*.txt`：

```pdx
defined_text = {
	name = NS_GetDashboardSubtitle
	text = { trigger = { has_war = yes }        localization_key = NS_subtitle_war }
	text = { trigger = { has_war = no }         localization_key = NS_subtitle_peace }
	text = {                                    localization_key = NS_subtitle_default }
}
```

```yml
 NS_dashboard_subtitle: "[NS_GetDashboardSubtitle]"
```

原版范例文件：`common/scripted_localisation/00_scripted_localisation.txt`（文件头注释解释了 `defined_text/text/trigger/localization_key` 四层）。

### 5.2 让 scripted GUI 动态换图（`properties.image` + 脚本化本地化）

原版：`INS_revolution_scripted_gui.txt:8-10` + 对应 loc key 返回 sprite 名：

```pdx
properties = {
	lon_we_1_icon = { image = "[INS_GET_WAR_ESCALATION_LEVEL_1_COLOR]" frame = 1 }
}
```
→ `INS_GET_WAR_ESCALATION_LEVEL_1_COLOR` 是一个 `defined_text`，返回 `GFX_xxx` 形式的 sprite 名。

### 5.3 界面上的动态颜色

```yml
 NS_tt: "当前风险：§[NS_GetRiskColor][?NS_risk_value]§!"
```
`§[函数名]` 直接调用命名空间函数返回颜色代码（原版 13 处用例，见 [localisation.md](localisation.md) §3）。

## 6. 决策/事件图片与图标命名速查

| 内容 | sprite 名 | 文件位置 | 尺寸 |
|---|---|---|---|
| 国策图标 | `GFX_focus_<name>` | `gfx/interface/goals/focus_<name>.dds` | **100×88** |
| 理念/特质/顾问图标 | `GFX_idea_<name>` | `gfx/interface/ideas/idea_<name>.dds` | ~65×67（不统一，建议照抄同类） |
| 决议分类图标 | `GFX_decision_category_<name>` | `gfx/interface/decisions/decision_category_<name>.dds` | ~40×51 |
| 决议图标 | `GFX_decision_<name>` | `gfx/interface/decisions/decisions_<name>.dds` | ~32×33 |
| 事件图片 | `GFX_<name>` | `gfx/event_pictures/<name>.dds` | 见原版同类 |
| 国家旗帜 | 自动（无需 sprite） | `gfx/flags/TAG[_ideology].tga` | 82×52 |

> 国策/理念/决议图标**都必须显式注册 sprite**（原版 `interface/goals.gfx` 5794 个 `GFX_focus_*`、`interface/ideas_characters.gfx` 逐条注册、`interface/decisions.gfx` 662 条）；**没有按文件名自动生成的机制**（实测无 `GFX_focus_AFG_adopt_nufus` 以外的隐式规则，全部能在 `.gfx` 里 grep 到）。

## 7. 性能总表（表现层专属）

| 项 | 开销来源 | 建议 |
|---|---|---|
| scripted GUI 每 tick 刷新 | `properties`/`triggers`/`visible` 全部求值 | 写 `dirty = 变量`；面板多了直接掉帧 |
| `dynamic_lists` | 每次刷新重建条目 | 数组 ≤ 几十；条目容器别嵌套太深 |
| scripted map mode | 每 scope 回调 `color` | 必写 `targets`；`update_daily = no` |
| 大量 `frameAnimatedSpriteType` | 每帧重绘 + 显存 | 动画贴图 `loadType = "INGAME"`；不用时用 `visible` 隐藏 |
| `legacy_lazy_load = no` 滥用 | 启动即加载全部纹理 | 只给文本图标/首屏要用的 sprite 写 |
| 每 tick 触发的 tooltip 本地化 | `[ ]` 求值 | 面板级 `dirty` 一起管住 |

## 8. 常见错误 / 自检清单

- [ ] `scripted_map_modes` 放在 `common/map_modes/*.txt`（不是 `common/` 根），外壳名写对。
- [ ] map mode 的 loc 三键（`MAPMODE_*` / `_NAME` / `_DESCRIPTION`）与两个 `GFX_mapmode_buttons_*` sprite 齐全。
- [ ] map mode 写了 `targets`，否则卡。
- [ ] alerts 只改 `category`，别指望自定义新警报。
- [ ] 决议/国策/理念图标都注册了 sprite，且名字与 `icon =` 完全一致。
- [ ] `pdx_tooltip` 里不用 `$var$`；要动态文本用 `defined_text` 或 `custom_effect_tooltip`。
- [ ] `defined_text` 的 `trigger` 作用域是“调用处”，兜底 `text`（无 trigger）一定要写。
- [ ] 换图标尺寸时同步检查 UI 布局（原版各处的图标尺寸并不统一，硬套 64×64 会变形）。
- [ ] 以上全部改完必须重启游戏后再验证。

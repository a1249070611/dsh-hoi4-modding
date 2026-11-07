---
title: GUI 基础（interface/*.gui）
domain: 05_presentation
scope: interface
verified_on: 1.19.x
verified_at: 2026-10-26
---

# GUI 基础：`interface/*.gui`

## 1. 文件放哪、谁读它、能不能热重载

| 项 | 事实 |
|---|---|
| 位置 | `interface/*.gui`（原版 292 个文件；子目录合法，如 `interface/doctrines/`、`interface/career_profile/`） |
| 加载时机 | 启动时由引擎扫描 `interface/` 下所有 `.gui`；mod 只“新增文件”，不要复制原版整文件 |
| 同名文件 | **整体替换**：mod 里出现 `interface/backend.gui` 就完全顶掉原版同名文件（这就是“覆盖式”改界面的代价） |
| 热重载 | **不支持**。改完必须重启游戏（`-debug_mode` 下也只有部分资源可重载） |
| 报错位置 | `logs/error.log`：`Unexpected token` / `Unknown element type` / `could not find window` |
| 命名限制 | 元素 `name` 在同一 `guiTypes` 作用域内应唯一；`scripted_gui.window_name` 靠这个名字找容器 |

> 关键事实：**单独一个 `.gui` 不会让任何东西出现在屏幕上**。`.gui` 只定义“元素树”；显示时机、显示给谁、按钮行为由 `common/scripted_guis/*.txt`（或硬编码视图）决定。详见 [scripted-gui.md](scripted-gui.md)。

## 2. 顶层结构

```pdx
# mod 里：interface/NS_dashboard.gui
@NS_PANEL_W = 460          # 文件级常量，用 @NAME 引用；原版大量使用（backend.gui/sov_paranoia_*）
@NS_PANEL_H = 210

guiTypes = {

	containerWindowType = {
		name = "NS_dashboard_window"
		position = { x = 0 y = 0 }
		size = { width = 100% height = @NS_PANEL_H }
	}

}
```

- 最外层必须是 `guiTypes = { ... }`（原版 130 个文件里唯一入口写法）。
- `guiTypes` 里可以直接放任意元素类型；甚至可以直接放一个裸 `iconType` 而不包容器（见 `interface/abilitylist.gui:3`）。
- `@NAME = 值` 是**文件作用域文本替换**，可以用在 `position`/`size`/`maxWidth` 里（`sov_paranoia_system_scripted_gui.gui:1-16`）。
- 键名**大小写不敏感**：原版同时存在 `instantTextBoxType`(1026) 与 `instantTextboxType`(1722)、`buttonType` 与 `ButtonType`、`Orientation` 与 `orientation`、`maxWidth` 与 `maxwidth`。

## 3. 元素类型（1.19.x 原版实际出现过的全部）

| 类型 | 原版出现次数 | 用途 |
|---|---|---|
| `iconType` | 2962 | 显示一张 sprite（贴图） |
| `containerWindowType` | 1984 | 容器/无边框面板，**最常用** |
| `buttonType` | 1825 | 可点按钮（有 up/hover/down/disabled 帧） |
| `instantTextBoxType` | 1722+1026 | 单行/自动换行文本（可带 `pdx_tooltip`） |
| `guiButtonType` | 319 | 老式按钮，用 `quadTextureSprite` 指定按钮底图 |
| `gridBoxType` | 297 | 按网格排列子元素（`slotsize`/`max_slots_horizontal`） |
| `positionType` | 160 | 只声明一个命名位置，供引擎把动态元素（进度条、地图图标）塞进来 |
| `checkboxType`/`checkBoxType` | 131+24 | 复选/开关 |
| `editBoxType` | 84 | 输入框 |
| `windowType` | 55 | 顶层窗口（可拖拽 `moveable`、全屏 `fullScreen`），一般只用于整屏视图 |
| `OverlappingElementsBoxType` | 45 | 层叠排列子元素 |
| `dropDownBoxType` | 37 | 下拉框 |
| `scrollbarType`/`extendedScrollbarType` | 31+21 | 滚动条/滑条（`minValue`/`maxValue`/`stepSize`/`startValue`） |
| `textBoxType` | 22 | 多行文本块 |
| `listboxType`/`smoothListBoxType` | 14+14 | 列表 |
| `browserType` | 1 | 内嵌浏览器（仅多人界面） |

> 数数命令（原版目录里跑）：`grep -rhoE "^\s*[a-zA-Z_]+Type\s*=\s*\{" interface/*.gui | sed 's/[[:space:]]//g;s/={.*//' | sort | uniq -c | sort -rn`

## 4. 定位、尺寸、朝向（90% 的错位都出在这里）

```pdx
containerWindowType = {
	name = "my_panel"
	orientation = center_up            # 元素的“锚点/对齐基准”，默认 upper_left
	position = { x = -230 y = 80 }     # 相对父容器；配合 orientation 可以是负值/居中偏移
	size = { width = 460 height = 210 }  # 也支持 width = 100%（占父容器宽度百分比）
	clipping = no                      # no = 子元素允许画到容器外（原版常用，便于摆装饰）
	moveable = no                      # 仅 windowType 有意义
}
```

### `orientation` 合法值（原版实测词表）

| 值 | 次数 | 含义 |
|---|---|---|
| `upper_left` | 312 | 默认：坐标原点在左上 |
| `center` | 219 | 子元素坐标以容器中心为原点 |
| `upper_right` | 65 | 右上 |
| `center_up` | 54 | 水平居中、顶部对齐（做居中标题条最常用） |
| `lower_left` | 44 | 左下 |
| `center_right` / `center_down` / `center_left` | 43/28/17 | 右中 / 下中 / 左中 |
| `lower_right` | 17 | 右下 |
| `center_lower` | 7 | 同 `center_down`（旧写法） |
| `left` / `bottom_left` | 5/1 | 少见变体 |

**换算规则**：`orientation = center` 的容器里，子元素 `x = 0` 是水平中心；`center_up` 里 `x` 是**中心偏移**（所以原版写 `x = -280` 让宽度 600 的标题居中：`GER_inner_circle_scripted_gui.gui:45-53`）。**不要按屏幕绝对坐标思考，按父容器 + 锚点思考。**

### 尺寸/边距相关字段

| 字段 | 含义 | 原版例子 |
|---|---|---|
| `size = { width = .. height = .. }` 或 `{ x = .. y = .. }` | 容器/元素尺寸，支持百分比 | `backend.gui:9` |
| `borderSize = { x = .. y = .. }` | 九宫格边框（配 `corneredTileSpriteType` 缩放用） | `core.gfx:44` |
| `margin` / `background_margin` | 容器内边距 | `interface/*.gui` 203/11 次 |
| `slotsize` / `max_slots_horizontal` / `max_slots_vertical` | `gridBoxType` 的格子尺寸/列数/行数 | `interface/*.gui` |
| `maxWidth` / `maxHeight` / `fixedsize` | 文本换行宽度/高度上限、是否强制尺寸 | `usa_congress_scripted_gui.gui:47-59` |
| `scale` | 缩放 sprite（头像缩小常用 0.5） | `GER_inner_circle_scripted_gui.gui:186` |
| `rotation` | 弧度旋转（1.5708 = 90°） | `interface/*.gui` 51 次 |
| `centerposition = yes` | 按 sprite 中心而不是左上角定位 | `GER_inner_circle_scripted_gui.gui:100` |

## 5. 四种最常用控件

### 5.1 `iconType`（贴图）

```pdx
iconType = {
	name = "panel_bg"
	spriteType = "GFX_NS_dashboard_bg"     # 必须先在 interface/*.gfx 里注册同名 sprite
	position = { x = 0 y = 0 }
	alwaystransparent = yes               # 允许点击穿透（背景装饰用）
	# scale = 1.0
	# frame = 1                            # 多帧 sprite 取第 N 帧（frameAnimatedSpriteType/多帧 spriteType）
}
```

- `spriteType` 也可以是 `""`：原版用它做“占位、稍后由 scripted_gui 的 `properties` 填图”（`GER_inner_circle_scripted_gui.gui:183`）。

### 5.2 `instantTextBoxType`（文本）

```pdx
instantTextBoxType = {
	name = "title_text"
	position = { x = 18 y = 8 }
	font = "hoi_18mbs"                    # 中文界面下必须是带 l_simp_chinese override 的字体，见 fonts-cjk.md
	text = "NS_dashboard_title"           # 这里是**本地化 key**，不是字面文本
	format = center                       # left / center(centre) / right
	maxWidth = 430                        # 超过就换行
	maxHeight = 40
	fixedsize = yes                       # 固定尺寸（不随文本增长）
	pdx_tooltip = NS_dashboard_title_tt   # 悬停提示（也是 loc key）
	# context_aware_text = "..."          # 需要引擎上下文的文本（如角色姓名）
	# context_aware_tooltip = "..."       # 同上，tooltip
}
```

- `text` 支持 `[GetXxx]` 命名空间吗？**只有被 scripted GUI 挂载、且 `context_type` 有效时才可靠**（wiki “Custom interface elements” 条；本机 1.19.x 无 `bound_tooltip` 用例，`grep bound_tooltip interface/*.gui` = 0）。所以动态文本优先用**本地化 key + `[?TAG.var]`**，或 `defined_text` 脚本化本地化。
- `format` 原版取值统计：`left` 1084、`center` 1008、`centre` 259、`right` 196（`centre` 与 `center` 等价）。

### 5.3 `buttonType`（可点按钮）

```pdx
buttonType = {
	name = "boost_btn"                    # 名字是给 scripted_gui 绑定用的，见 scripted-gui.md
	position = { x = 18 y = 150 }
	quadTextureSprite = "GFX_button_261x34"  # 按钮底图；或 spriteType = "..."
	buttonText = "NS_dashboard_boost"        # 按钮文字（loc key）
	buttonFont = "hoi_16mbs"
	clicksound = click_default               # 音效名来自 sound/gui/gui_sound_effects.asset
	shortcut = "RETURN"                      # 键盘快捷键（可选）
	pdx_tooltip = NS_dashboard_boost_tt
}
```

- 按钮状态帧由 sprite 的 `noOfFrames`（一般 4 帧：normal/hover/pressed/disabled）+ `.shader` 决定。原版 `effectFile = "gfx/FX/buttonstate.lua"` 指向的 `.lua` 在 1.19.x **不存在**（`gfx/FX/` 里只有 45 个 `.shader`），属旧版残留字段——照抄无害，但别指望它产生效果（⚠️ 具体回退逻辑未在游戏内实测）。
- `clicksound` 原版常用值：`click_default`(758)、`click_checkbox`(347)、`click_close`(227)、`click_scroll`(81)、`click_ok`(51)。

### 5.4 `background`（背景块，属于容器内字段）

```pdx
background = {
	name = "bg"
	quadTextureSprite = "GFX_tiled_plain_bg2"   # 九宫格拉伸的 tile sprite
	alwaystransparent = yes
}
```

- 注意 `background` 是**容器内的保留字段**（1053 次），不是元素类型；用 `quadTextureSprite` 而不是 `spriteType`。
- `windowType` 上则用 `backGround=""`（`backend.gui:7`，大小写均可）。

## 6. tooltip 三兄弟

| 字段 | 用途 | 限制 |
|---|---|---|
| `pdx_tooltip = <loc_key>` | 普通悬停提示 | **内部 `$var$` 不展开**（wiki 明确说明），要用 `defined_text` 绕 |
| `pdx_tooltip_delayed = <loc_key>` | 延迟悬停提示（42 次） | 同上 |
| `context_aware_tooltip = <loc_key>` | 依赖引擎上下文的提示（角色/特质等，42 次） | 只在引擎提供上下文的元素上有效，递归继承 |
| `tooltip = <loc_key>` | 极少见（62 次），部分控件用 | 兼容性最差 |

原版范例：`GER_inner_circle_scripted_gui.gui:101/112/134` 用 `context_aware_tooltip` 显示角色信息；`sov_paranoia_system_scripted_gui.gui:54/63` 用 `pdx_tooltip`。

## 7. 完整可加载面板（照抄即用）

四个文件合起来才“真的出现在屏幕上”。这里先给 `.gui`（另外三个文件在 [scripted-gui.md](scripted-gui.md) §5）。

```pdx
# mod 里：interface/NS_dashboard.gui
@NS_BG_X = 0
@NS_BG_Y = 0

guiTypes = {

	containerWindowType = {
		name = "NS_dashboard_window"
		position = { x = 0 y = 0 }
		size = { width = 100% height = 170 }

		background = {
			name = "bg"
			quadTextureSprite = "GFX_decision_category_generic"
		}

		iconType = {
			name = "NS_dashboard_icon"
			spriteType = "GFX_decision_category_generic"
			orientation = center_left
			position = { x = 12 y = 50 }
			scale = 0.75
		}

		instantTextBoxType = {
			name = "NS_dashboard_title"
			position = { x = 90 y = 10 }
			font = "hoi_24header"
			text = "NS_dashboard_title"
			format = left
			maxWidth = 340
		}

		instantTextBoxType = {
			name = "NS_dashboard_value"
			position = { x = 90 y = 46 }
			font = "hoi_18mbs"
			text = "NS_dashboard_value_text"
			format = left
			maxWidth = 340
		}

		buttonType = {
			name = "NS_dashboard_boost"
			position = { x = 90 y = 96 }
			quadTextureSprite = "GFX_button_261x34"
			buttonText = "NS_dashboard_boost"
			buttonFont = "hoi_16mbs"
			clicksound = click_default
			pdx_tooltip = NS_dashboard_boost_tt
		}
	}
}
```

- `GFX_decision_category_generic`、`GFX_button_261x34` 都是原版已存在的 sprite（`interface/decisions.gfx:7`、`interface/core.gfx` 内按钮组），**复制即能显示**，不需要先做图。
- 容器高度 170、子元素 `y` 都落在容器内；`position = { x = 0 y = 0 }` + `size = { width = 100% }` 是原版 scripted GUI 面板的标准开头（`RAJ_famine.gui:16-17`、`usa_congress_scripted_gui.gui:8-10`）。

## 8. 常见 UI 组合套路

| 需求 | 做法 | 原版范例 |
|---|---|---|
| 顶部标题条 + 背景 | `containerWindowType` + `background` + `instantTextBoxType(format = center)` | `GER_inner_circle_scripted_gui.gui:22-53` |
| 头像 + 圆形边框 | 两层 `iconType`，头像 `alwaystransparent = yes`，边框 `centerposition = yes` | `GER_inner_circle_scripted_gui.gui:71-113` |
| 一排图标（顾问栏） | `containerWindowType` + 多个 `iconType` 手摆 x 间距 | `GER_inner_circle_scripted_gui.gui:402-476` |
| 仪表盘指针 | 两张同位置 `iconType`（底盘 + 指针），指针角度/裁剪靠 sprite 帧 | `sov_paranoia_system_scripted_gui.gui:33-44` |
| 数值文本带颜色 | 文本走 loc key，颜色写在 loc 里 `§Y...§!` | [localisation.md](localisation.md) |
| 进度条 | `progressbartype` sprite + 引擎按 `positionType` 插入 | `countryconstructionsview.gui:667`、`countryconstructionsview.gfx:182` |

## 9. 常见错误 / 自检清单

- [ ] 花括号平衡（`hoi4_lint.py` 或编辑器括号匹配）；`.gui` 里**不能**用 `#` 写行内注释以外的东西——`#` 后整行注释是安全的。
- [ ] `guiTypes = {` 在最外层，文件名 `.gui` 小写扩展名。
- [ ] 每个 `spriteType = "GFX_xxx"` 都能在 `interface/*.gfx` grep 到；`spriteType` 值**带 `GFX_` 前缀**（原版无例外）。
- [ ] `position/size` 用 `{ x = .. y = .. }` 或 `{ width = .. height = .. }`，不要混写成 `{ width = .. y = .. }`。
- [ ] 有 `background` 的容器，`quadTextureSprite` 指向的是 `corneredTileSpriteType`（九宫格）或普通 sprite，不能指向 `progressbartype`。
- [ ] 元素 `name` 不与同容器内其他元素重名（否则 `properties`/`effects` 绑到错的那个）。
- [ ] 中文界面下所有 `font =` 都来自 `core_chinese.gfx` 的 override 名单。
- [ ] 面板“看不见”时，先确认是 GUI 问题还是挂载问题：把 `visible = { always = yes }`、把分类 `visible` 改成 `always = yes`、再重启。
- [ ] 改 `.gui` 后必须重启游戏；不要指望控制台刷新。

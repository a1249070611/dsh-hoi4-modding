---
name: kiant-hoi4-ui-interface
description: HOI4 界面开发：.gui 结构、窗口与控件类型、定位与尺寸、dataSource 绑定、sprite 注册与九宫格、字体、覆盖原版界面的代价、nudge 编辑器用法。
---

# 界面（GUI）

## 两个文件系统，别混

| 文件 | 作用 |
|---|---|
| `interface/*.gfx` | 注册图片资源（sprite），让界面能引用 |
| `interface/*.gui` | 定义窗口布局：谁在谁里面、多大、放哪 |

图片没注册 → 界面能开但控件空白。`.gfx` 写对了 `.gui` 里才有东西可引。

## .gui 基本骨架

```
guiTypes = {
	containerWindowType = {
		name = "mymod_panel"
		position = { x = 100 y = 100 }
		size = { width = 400 height = 300 }
		moveable = yes
		background = {
			name = "bg"
			spriteType = "GFX_tiled_window"
		}

		instantTextBoxType = {
			name = "title"
			position = { x = 12 y = 10 }
			font = "hoi_16mbs"
			text = "MYMOD_TITLE"
			maxWidth = 360
			maxHeight = 24
		}
	}
}
```

常用控件类型：

| 类型 | 用途 |
|---|---|
| `containerWindowType` | 容器，可嵌套 |
| `windowType` | 顶层窗口 |
| `instantTextBoxType` | 静态文本 |
| `buttonType` | 按钮 |
| `iconType` | 图片 |
| `positionType` / `gridBoxType` | 定位与网格排布 |
| `scrollbarType` | 滚动条 |

## 定位与尺寸

- `position {x y}` 相对**父容器**左上角
- `size {width height}` 是控件尺寸，不是内容尺寸
- 文本控件还需要 `maxWidth` / `maxHeight`，否则长文本会溢出到别的控件上
- `orientation = UPPER_LEFT` 等决定锚点

界面错位 90% 是这三件事之一：父容器尺寸变了、`maxWidth` 没设、sprite 尺寸与控件尺寸不匹配。

## sprite 与九宫格

普通 sprite：

```
spriteTypes = {
	spriteType = {
		name = GFX_tiled_window
		texturefile = "gfx/interface/tiled_window.dds"
	}
}
```

可拉伸面板用 `corneredTileSpriteType`（九宫格），否则缩放时边角会被拉变形：

```
corneredTileSpriteType = {
	name = GFX_my_panel
	texturefile = "gfx/interface/panel.dds"
	size = { width = 64 height = 64 }
	borderSize = { left = 16 top = 16 right = 16 bottom = 16 }
}
```

字体用 `bitmapfont` 在 `.gfx` 里定义，`.gui` 里用 `font = "字体名"` 引用。自定义字体需要配套的 `.fnt` + 图集，这块兼容性差，非必要不用碰。

## 覆盖原版界面的代价

改原版某个窗口，只能复制原版 `.gui` 到 mod 同名路径再改——整文件替换。

后果：

- 游戏每次更新界面结构，你的副本就过期，轻则错位重则窗口不显示
- 别的 mod 也覆盖同一文件时，只有后加载的生效
- 你放弃了原版在该文件里的所有后续改动

**优先级：新建窗口 > 用 scripted GUI 注入 > 覆盖原版。** 只有在必须改原版布局时才走覆盖，并在 README 里注明覆盖了哪个文件。

## scripted GUI

想在原版界面上挂自己的按钮，用 `common/scripted_guis/`，避免覆盖 `.gui`：

```
scripted_gui = {
	mymod_button = {
		context_type = player_context
		window_name = "country_politics_view"
		effects = { ... }
		triggers = { ... }
	}
}
```

具体字段各版本有差异，用 `kiant_hoi4_kb_search "scripted_gui"` 找原版实例。

## nudge 编辑器

`-debug_mode` 启动，控制台输入 `nudge`，进入实时拖拽模式：

- 拖动控件，坐标实时更新
- 可以直接导出当前布局的坐标
- 手算坐标在复杂界面里不现实，这是唯一实用的方式

## 排查清单

| 症状 | 原因 |
|---|---|
| 窗口完全不出现 | `name` 与调用处不一致；或父窗口名写错 |
| 窗口出现了但空白 | sprite 未注册 / 路径错 |
| 控件重叠 | 父容器尺寸与子控件位置不匹配 |
| 文本被截断 | 缺 `maxWidth` / `maxHeight` |
| 点按钮没反应 | 按钮 `name` 与代码里引用不一致 |
| 整个界面崩 | `.gui` 括号不配对（校验器会报） |

`ui` 校验器会检查窗口名重复、sprite 引用是否存在、`.gui` 语法错误。跑 `kiant_hoi4_validate_mod deep=true`。

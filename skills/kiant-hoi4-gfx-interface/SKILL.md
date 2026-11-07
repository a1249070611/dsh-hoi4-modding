---
name: kiant-hoi4-gfx-interface
description: HOI4 图像与界面资源：DDS/TGA 规格、sprite 定义 .gfx、图标与立绘命名、sprite 前缀解析规则、.gui 界面修改、以及"问号图标/粉黑方块"的排查。
---

# GFX 与界面

## 图片格式

引擎读 `.dds` 和 `.tga`。DDS 用 DXT5（带 alpha）或 BC1（无 alpha），尺寸建议为 2 的幂（128/256/512），非 2 的幂多数情况能读但容易在缩放时出问题。

放在 `gfx/` 下，按用途分目录：

```
gfx/
├── interface/icons/         图标（国策、精神、决议）
├── interface/leaders/       领袖立绘
└── interface/goals/         国策大图
```

## sprite 定义

图片不会自动出现在界面里，必须在 `interface/*.gfx` 注册：

```
spriteTypes = {
	spriteType = {
		name = GFX_GER_autobahn
		texturefile = "gfx/interface/icons/GER_autobahn.dds"
	}
}
```

> 上面 `GFX_GER_autobahn` 只演示语法，**它不是原版真实存在的 sprite**。原版有哪些、长什么样，用 `kiant_hoi4_kb_symbol name=GFX_xxx` 查，别照抄示例名。

- `name` 全局唯一，**必须带 `GFX_` 前缀**（社区惯例，也是引擎查找的约定）
- `texturefile` 路径相对 mod 根目录，**正斜杠**，**带扩展名**
- 路径大小写敏感（Windows 上不报错，Steam Deck / Linux 上直接找不到）

动画帧：

```
frameAnimatedSpriteType = {
	name = GFX_loading_spinner
	texturefile = "gfx/interface/spinner.dds"
	noOfFrames = 8
	animationRate = 12
	looping = yes
}
```

`GFX_loading_spinner` 同样是虚构示例名。`noOfFrames` 必须与 DDS 里实际切出的横向帧数一致，写多了引擎会取到空白帧。

九宫格（可拉伸面板）：

```
corneredTileSpriteType = {
	name = GFX_my_panel
	texturefile = "gfx/interface/panel.dds"
	size = { width = 64 height = 64 }
	borderSize = { left = 16 top = 16 right = 16 bottom = 16 }
}
```

## 不同字段的前缀规则不同

这是最容易出错的地方——同样指一个图标，不同字段的前缀处理不一样：

| 字段 | 写法 | 实际查找的 sprite |
|---|---|---|
| 国策 `icon` | `icon = GFX_focus_generic_industry_2` | 原样，带 GFX_ |
| 事件 `picture` | `picture = GFX_report_event_generic_army` | 原样，带 GFX_ |
| 国家精神 `picture` | `picture = generic_build_infrastructure` | 引擎自动补成 `GFX_idea_generic_build_infrastructure` |
| 决议 `icon` | `icon = generic_political_rally` | 引擎自动补成 `GFX_decision_generic_political_rally` |

**别凭记忆，用原版验证**：到游戏安装目录的 `interface/` 里 grep 一下 sprite 真名。例：

```
grep -r "GFX_idea_generic_build_infrastructure" "游戏安装目录/interface/"
```

找到说明前缀规则如上；找不到就说明这个 sprite 在别的文件里，或者名字不同。

## 图标出问题的典型症状

| 症状 | 原因 |
|---|---|
| 问号图标 | sprite 没注册，或名字拼错 |
| 粉黑方块 | 图片文件存在但格式/尺寸不对，或路径指错 |
| 空白 | `texturefile` 路径大小写错误（Linux 会挂，Windows 可能没事） |
| 图标被裁切 | 图片尺寸与界面预期的宽高比不符 |

`error.log` 里的 `Could not find sprite GFX_xxx` 会直接告诉你是哪个名字找不到——先跑 `kiant_hoi4_analyze_error_log`。

## 界面文件 .gui

`interface/*.gui` 定义窗口布局。改原版界面需要**覆盖同名文件**（复制原版文件到 mod 的同名路径再改），这是高维护成本操作：

- 游戏每次大版本更新都可能改动 `.gui` 结构，你的覆盖文件会随之失效或错位
- 覆盖文件是整文件替换，原版在该文件里的所有内容都被你的版本取代

`nudge` 是官方 GUI 编辑器：`-debug_mode` 启动后在控制台输入 `nudge`，可以实时拖动界面元素并导出坐标。做界面调整几乎必须用它，靠手算坐标不现实。

## 制作流程建议

1. 先用占位图（纯色 512×512 PNG 转 DDS）把 sprite 和引用全部打通
2. 确认游戏里能正常显示后，再替换成正式美术
3. 每加一批 sprite 跑一次 `kiant_hoi4_validate_mod` + 进游戏看 `error.log`
4. 图片资源体积大，`.gitignore` 排除中间产物，只提交最终 DDS

## 工具链

- 图片转换：ImageMagick（`magick input.png -define dds:compression=dxt5 output.dds`）、GIMP 的 DDS 插件、Paint.NET
- 批量转换脚本放 `tools/` 目录，别手工一个个导

## 与本地化的联动

图标在文本中的内联引用用 `£icon_name`，此时 `icon_name` 是 sprite 名去掉 `GFX_` 前缀后的部分：

```
 GER_autobahn_desc:0 "提供 £political_power 与 £stability 加成。"
```

找不到对应 sprite 时，文本里会直接显示 `£political_power` 字样而不是图标。

## 中文字体覆盖（条件生效）

替换/新增中文字体时用**语言条件覆盖**，只在对应语言时生效（原版
`core_chinese.gfx` 同款手法，实测见 52 字体 mod）：

```pdx
bitmapfont_override = {
    name = "ToolTip_Font"
    fontfiles = { "gfx/fonts/garamond_16" "gfx/fonts/Arial_14" }   # 字形回退链
    languages = { "l_simp_chinese" }
}
```

- `.fnt + .dds` 成对出现、同名覆盖原版字体文件即可生效（无需改 .gui）。
- 地图字体独立一套 `mapfont_chn_0..7`（8 个 unicode 段），地图文字乱码先查它。
- 详见 `references/05_presentation/fonts-cjk.md`。

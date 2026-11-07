---
title: 贴图与 sprite（interface/*.gfx + DDS）
domain: 05_presentation
scope: gfx
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 贴图与 sprite：`interface/*.gfx`

## 1. 文件放哪（一个反直觉的事实）

| 项 | 事实（本机实测） |
|---|---|
| 2D sprite 定义 | **全部在 `interface/*.gfx`**：145 个文件、23521 个 `spriteType` |
| `gfx/interface/*.gfx` | **0 个文件**（原版从不用这个位置） |
| `gfx/*.gfx` | 36 个，全是 3D：`gfx/entities/`（坦克/飞机/船/建筑模型）、`gfx/models/`、`gfx/particles/` |
| 贴图本体 | `gfx/interface/`、`gfx/flags/`、`gfx/leaders/`、`gfx/texticons/`、`gfx/fonts/`、`gfx/interface/goals/` |
| 加载 | 启动时扫描；改完需重启；mod 新增文件即可 |
| 同名文件 | 整体替换（mod 里放 `interface/core.gfx` = 顶掉整个原版文件，**不要这样干**） |
| 报错 | `logs/error.log` 搜 `Failed to load texture` / `sprite` / `texturefile` |

> 社区教程常写 `gfx/interface/xxx.gfx`。原版 0 先例 —— 放 `interface/xxx.gfx` 最稳。若放 `gfx/` 下，只有 `gfx/` 的模型管线会扫到，2D sprite 可能根本不被加载（⚠️ 未在游戏内实测两种放法的差异）。

## 2. 顶层结构与元素类型

```pdx
# interface/NS_icons.gfx
spriteTypes = {

	spriteType = { ... }
	textSpriteType = { ... }
	frameAnimatedSpriteType = { ... }
	corneredTileSpriteType = { ... }
	progressbartype = { ... }
	maskedShieldType = { ... }
}
```

原版各类出现次数（`interface/*.gfx` 统计）：

| 类型 | 次数 | 用途 |
|---|---|---|
| `spriteType` | 23521 | 普通贴图（单图或多帧竖排图） |
| `textSpriteType` | 75 | 行内文本图标（`£name`），可多帧 |
| `frameAnimatedSpriteType` | 151 | 逐帧动画（帧数 × fps） |
| `corneredTileSpriteType` | 133 | 九宫格拉伸（`borderSize`），做可缩放面板底 |
| `progressbartype` | 103 | 进度条（底图 + 填充图） |
| `maskedShieldType` | ~90 | 旗帜叠在盾/旗框里（国家旗帜渲染核心） |
| `animationType`（`animation = {}` 子块） | — | 附加在 spriteType 上的特效动画（流光/旋转/脉冲） |

`spriteTypes = { }` 外壳不可省；键名大小写不敏感（`SpriteType` 与原版混用）。

## 3. `spriteType` 字段与常用开关

```pdx
spriteType = {
	name = "GFX_NS_my_icon"                  # 必须以 GFX_ 开头（原版 23521 个全部如此）
	texturefile = "gfx/interface/NS/my_icon.dds"   # 用 / 分隔；大小写敏感
	# noOfFrames = 4                          # 竖排多帧贴图（按钮 4 帧、图标 2 帧）
	# size = { x = 64 y = 64 }                # 覆盖默认尺寸（动画/图集需要）
	# alwaystransparent = yes                 # 允许点击穿透（装饰层）
	# loadType = "INGAME"                     # INGAME / FRONTEND：贴图在哪个阶段加载
	# transparencecheck = yes                 # 透明像素不参与点击检测
	# legacy_lazy_load = no                   # 立即加载（行内文本图标必须写！见 §8）
	# generate_mip_maps = yes                 # 生成 mipmap（地图/3D 场景贴图需要）
	# masking_texture = "gfx/interface/...dds"  # 用另一张图的 alpha 做遮罩
	# effectFile = "gfx/FX/buttonstate.lua"   # 旧版残留，见 §3.2
}
```

原版实例：
- 最简：`interface/abilitylist.gfx:3-7`
- 带 `loadType` + `transparencecheck` 的动画：`interface/countryconstructionsview.gfx:12-21`
- 带 `masking_texture` + `generate_mip_maps`：`interface/mapicons.gfx:819-825`（特工头像裁成圆形）

### 3.1 `loadType`

`"INGAME"`（游戏内才需要）与 `"FRONTEND"`（主菜单就需要）两值。原版 78 处全部是这两个。菜单类贴图写 `FRONTEND`，其余写 `INGAME` 可减少主菜单内存占用。

### 3.2 `effectFile` 是个坑（1.19.x 实测）

原版 3731 处 `effectFile = "gfx/FX/xxx.lua"`，但 **`gfx/FX/` 下只有 45 个 `.shader` + 13 个 `.fxh`，全游戏只有 8 个 `.lua`（都在 `common/defines/` 和 `script/`）**。也就是说 `.lua` 路径已不存在，引擎必然忽略或按名回退到同名 `.shader`。照抄原版无害，但**不要以为写了就有效果**（⚠️ 引擎内部回退规则未实测）。

## 4. `frameAnimatedSpriteType`（逐帧动画）

```pdx
# interface/NS_anim.gfx
frameAnimatedSpriteType = {
	name = "GFX_NS_burning_icon"
	texturefile = "gfx/interface/NS/burning_strip.dds"   # 竖排 N 帧，每帧宽=图宽，高=图高/N
	noOfFrames = 12
	animation_rate_fps = 24
	looping = yes
	play_on_show = yes
	pause_on_loop = 0.0
	loadType = "INGAME"
	transparencecheck = yes
	alwaystransparent = yes
}
```

原版范例：`interface/countryconstructionsview.gfx:12-21`（施工中 12 帧 24fps）、`interface/alerts.gfx:3-13`（警报辉光 2 帧 0.5fps）。
**贴图必须竖排**：帧高 = 单帧高 × `noOfFrames`。数值不是 2 的幂没关系（原版有 12 帧）。

## 5. `corneredTileSpriteType`（九宫格，做可拉伸面板底）

```pdx
corneredTileSpriteType = {
	name = "GFX_NS_panel_bg"
	textureFile = "gfx/interface/NS/panel_bg.dds"   # 例：96×96
	size = { x = 96 y = 96 }
	borderSize = { x = 32 y = 32 }                  # 四角各 32px 不拉伸，中间平铺/拉伸
	tilingCenter = yes                              # yes=中间平铺，no=中间拉伸
	alwaystransparent = yes
}
```

原版：`interface/core.gfx:40-48`（`GFX_tiled_generic_overlay_bg1_small`，96→`borderSize=144`）、`interface/countryarmyview.gfx:335-341`。
**用法**：在 `.gui` 里当 `background = { quadTextureSprite = "GFX_NS_panel_bg" }`，容器改多大都不会糊。

## 6. `progressbartype`（进度条）

```pdx
progressbartype = {
	name = "GFX_NS_progress"
	color = { 0.0 0.5 0.0 }         # 填充色（低值）
	colortwo = { 1.0 0.0 0.0 }      # 填充色（高值），底图之上按比例着色
	textureFile1 = "gfx/interface/NS/progress_full.dds"  # 填充层
	textureFile2 = "gfx/interface/NS/progress_bg.dds"    # 背景层
	size = { x = 60 y = 8 }
	horizontal = yes                # 省略则纵向
}
```

原版：`interface/abilitylist.gfx:25-32`（33×33 纵向）、`interface/countryconstructionsview.gfx:172-190`（60×8 横向）。
**GUI 里怎么用**：引擎把进度值画进一个 `positionType` 命名的位置，`.gui` 里写 `iconType { spriteType = "GFX_construction_progressbar" }` 不行——正确姿势是声明命名位置并由引擎绑定：

```pdx
positionType = {
	name = "NS_progress_position"
	position = { x = 20 y = 120 }
}
```
（原版范例：`interface/*.gui` 里的 `leader_xp_progressbar_position`；进度条自身的尺寸/颜色都来自 `.gfx` 定义。）

## 7. `maskedShieldType`（旗帜/盾徽遮罩，旗帜系统的核心）

```pdx
maskedShieldType = {
	name = "GFX_NS_shield"
	textureFile1 = "gfx/interface/shield_frame.dds"   # 外框/高光层
	textureFile2 = "gfx/interface/shield_mask.tga"    # 遮罩：白=显示旗帜，黑/透明=不显示
	effectFile = "gfx/FX/maskedflag.lua"
}
```

原版：`interface/general_stuff.gfx:253-310` 定义了 `GFX_flag_small`、`GFX_shield_small`、`GFX_shield_medium`、`GFX_flag_small2`、`GFX_shield_thin` 等全部旗帜框。
**机制**：`.tga/.dds` 遮罩的 alpha/亮度决定「国旗（`gfx/flags/TAG.tga`）画在哪几块区域」，所以**换旗帜框 = 换 `textureFile1` + 对应遮罩**，旗帜图本身不用动。

## 8. 行内文本图标（`£icon` 背后的 sprite）

```pdx
textSpriteType = {
	name = "GFX_my_text_icon"            # 本地化里写 £my_text_icon
	texturefile = "gfx/texticons/my_text_icon.dds"
	noOfFrames = 2                        # 多帧时用 £my_text_icon|1 取第 2 帧
	legacy_lazy_load = no                 # 多帧文本图标 + 游戏启动即显示，必须写
}
```

原版：`interface/texticons.gfx`（428 个 `spriteType`/45 个 `SpriteType`）、`interface/core.gfx:1826`（`GFX_red_cross_texticon` 用的是 `textSpriteType`）。
**规则**：`£name` → 找 `GFX_name`；带 `GFX_` 前缀的 loc 写法（`£GFX_topbar_convoys`）在原版也存在，说明两种写法兼容（⚠️ 精确匹配规则未实测）。

## 9. `animation` 子块（流光/旋转/脉冲特效）

挂在 `spriteType` 里，`interface/goals_shine.gfx` 给 **2954 个国策图标**都加了「扫光」：

```pdx
SpriteType = {
	name = "GFX_focus_xxx_shine"
	texturefile = "gfx/interface/goals/focus_xxx.dds"
	effectFile = "gfx/FX/buttonstate.lua"
	animation = {
		animationmaskfile = "gfx/interface/goals/focus_xxx.dds"   # 只在这个形状内显示特效
		animationtexturefile = "gfx/interface/goals/shine_overlay.dds"
		animationrotation = -90.0
		animationlooping = no
		animationtime = 0.75                 # 秒
		animationdelay = 0
		animationblendmode = "add"           # add / multiply / overlay
		animationtype = "scrolling"          # scrolling / rotating / pulsing
		animationrotationoffset = { x = 0.0 y = 0.0 }
		animationtexturescale = { x = 1.0 y = 1.0 }
	}
	legacy_lazy_load = no
}
```

原版节选：`interface/goals_shine.gfx:5-35`。这是「给图标加漂亮特效」最省事的模板——同一张底图 + `shine_overlay.dds` + 遮罩图即可。

## 10. DDS 贴图：统一见 [dds.md](dds.md)

DDS 的格式/压缩族/尺寸/mipmap/alpha/生成校验管线全部收在 [dds.md](dds.md)，本页不再重复。只记三条与本页（sprite 注册）直接相关的：

- 	exturefile / 	extureFile1 等字段用 **/** 分隔、相对游戏/mod 根目录、**大小写敏感**；扩展名必须与真实格式一致（图标 .dds、旗帜 .tga）。
- **贴图对了 ≠ 界面显示**：.gfx 里没注册同名 spriteType，界面照样不显示（icon = GFX_xxx 找不到 → 白块/占位）。
- 字体图集（gfx/fonts/chinese/*.dds）是 DXT5、4 页 × 2048×1200/页，**不要手改**：改了字形坐标和 .fnt 就对不上（见 [fonts-cjk.md](fonts-cjk.md)）。

## 11. 中文/字体相关贴图注意

- 字体图集（`gfx/fonts/chinese/*.dds`）是 **DXT5**，4 页 × 2048×1200/页，**不要手改**（改了字形与 `.fnt` 就对不上）。
- 详见 [fonts-cjk.md](fonts-cjk.md)。

## 12. 常见错误 / 自检清单

- [ ] `.gfx` 放在 `interface/`（不是 `gfx/interface/`）；最外层是 `spriteTypes = { }`。
- [ ] sprite 名以 `GFX_` 开头，全局唯一（撞名会被加载顺序覆盖）。
- [ ] `texturefile` 路径用 `/`，相对游戏/mod 根目录，扩展名与真实格式一致（图标 `.dds`、旗帜 `.tga`）。
- [ ] DXT 贴图宽高是 4 的倍数；UI 贴图不需要 mipmap。
- [ ] 动画贴图是**竖排**帧序列，`noOfFrames` 与图高匹配。
- [ ] 九宫格底图配 `borderSize`，否则缩放会糊或穿帮。
- [ ] 文本图标写了 `legacy_lazy_load = no`。
- [ ] `loadType` 写对（菜单用 `FRONTEND`，游戏内用 `INGAME`）。
- [ ] 写完用 `dds_helper.py check` 与原版同类文件对比头字段。
- [ ] 黑块先怀疑路径/格式，不要先怀疑引擎。

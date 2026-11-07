---
title: 中文字体与中文乱码排查
domain: 05_presentation
scope: font
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - gfx/fonts/
  - gfx/fonts/chinese/
  - interface/fonts.gfx
  - interface/core.gfx
  - interface/core_chinese.gfx
  - interface/chatfonts.gfx
  - interface/load_screen_font.gfx
  - interface/core_korean.gfx
  - localisation/simp_chinese/
  - localisation/languages.yml
---

# 中文字体与中文乱码

基线 **1.19.x**。路径均相对 `<GAME_DIR>`；示例写进 `<PROJECT_DIR>` 下同名路径。

## 1. 结论先行：`????` 的根因是「字体名/字重映射」，不是「`.fnt` 没有字形」

| 问题 | 答案 |
|---|---|
| `localisation/simp_chinese/` 存在吗？ | **存在**，208 个 yml（`localisation/english/` 207 个） |
| 游戏支持简体中文？ | **支持**，`localisation/languages.yml` 里 `l_simp_chinese: "中文"`，共 10 种语言 |
| 中文字体在哪？ | `gfx/fonts/chinese/`（**约 1.1 GB**，222 个 `.fnt`，每个字体 4 页 `.dds` + 4 个 `.fnt`） |
| 字体怎么注册？ | `interface/core_chinese.gfx` 里 **`bitmapfont_override` + `languages = { "l_simp_chinese" }`** |
| 能用 TTF 吗？ | **不能**。全游戏 `gfx/fonts` 只有 `.fnt` + `.dds`/`.tga` 位图字体；根目录 2 个 `.ttf` 属启动器/预览器（`assets/font.ttf`、`previewer_assets/…/previewer_arial.ttf`）与游戏 UI 无关 |
| 方框/`?` 的第一嫌疑 | **GUI 里用了没有中文 override 的字体名**（见 §4 黑名单） |
| 乱码/显示 key 名的第一嫌疑 | **yml 不是 UTF-8 with BOM**，或文件名没带 `_l_simp_chinese` |

一句话机制：**汉字不在「默认加载的那个字体文件」里，在 `bitmapfont_override` 为该字体名挂的 `gfx/fonts/chinese/<name>_Nof4` 分片上。**
控件写 `font = "hoi_14mbs"` → 这个名字没有任何 override 块给它挂中文分片 → 中文一律 `????`，**和装没装第三方字体 mod 无关**。

### 口径纠正（别再把这两件事混为一谈）

- ❌ 旧文档/旧 README 说「游戏全部 `.fnt` 自身 CJK 字形数为 0」——**这是错的**，属于把「拉丁基础字体」以偏概全。
- ✅ 实际分两类：
  - **拉丁基础字体**（`gfx/fonts/*.fnt`，59 个）：只有拉丁字母/标点。实测 `hoi_16mbs.fnt` 仅 `chars count=333`、最大 `char id=8222`，**确实没有汉字**。
  - **中文分片**（`gfx/fonts/chinese/*.fnt`，222 个）：**确实含汉字**。实测每套 4 页 `chars count` = **7677 / 7813 / 8002 / 7041**（合计 30533 个字形）。
- 两者不矛盾：默认字体表里没有汉字，是 `bitmapfont_override` 在简中语言下**把该字体名整表换成中文分片**，汉字才出现。
  所以根因永远是**名字有没有被 override 覆盖**，而不是「`.fnt` 里有没有字形」。

## 2. 字体文件结构

```text
<GAME_DIR>/gfx/fonts/
├─ garamond_12.fnt + garamond_12.dds + garamond_12.tga   # 拉丁字体（.dds 与 .tga 都可能被 .fnt 引用）
├─ hoi_18mbs.fnt + hoi_18mbs.dds
├─ ...（59 个顶层 .fnt）
└─ chinese/                                              # 中文专用位图字体（4 页拆分，222 个 .fnt）
   ├─ garamond_16_1of4.fnt + garamond_16_1of4.dds
   ├─ garamond_16_2of4.fnt + garamond_16_2of4.dds
   ├─ garamond_16_3of4.fnt + ...
   ├─ garamond_16_4of4.fnt + ...
   ├─ hoi_mapfont4_1of11 ... hoi_mapfont4_11of11      # 地图字体 11 页
   └─ ...
```

**为什么拆 4 页**：汉字字形太多，单张 2048×1200 图集装不下。实测一套四页字形数 **7677 + 7813 + 8002 + 7041 = 30533 个字形**，
且各套字体（`Arial12`、`cg_16b`…）四页的 `chars count` 完全一致——它们是**同一批字形集**，只是渲染风格不同。
字形数最多的字体按 11 页拆（`hoi_mapfont4_*of11`，地图文字）。

### `.fnt` 是 BMFont 文本格式

```text
info face="garamond_16_1of4" size=16 bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 padding=1,1,1,1 spacing=1,1
common lineHeight=16 base=19 scaleW=2048 scaleH=1200 pages=1 packed=0
page id=0 file="garamond_16_1of4.dds"
chars count=7677
char id=32 x=0 y=0 width=0 height=0 xoffset=0 yoffset=-2 xadvance=3 page=0 chnl=15
char id=33 x=2044 y=934 width=4 height=15 xoffset=1 yoffset=4 xadvance=5 page=0 chnl=15
```

- `char id=<Unicode 码位>` + 图集坐标 + 步进 → 每个字形的位图位置。
- `page file=` 指向图集；中文页用 `.dds`（DXT5），拉丁老字体有 `.tga`。
- **缺字 = 该字体名字形表里没有这个 `char id`** → 显示 `?` 或空白。

## 3. 字体注册（两步：定义 + 按语言覆盖）

### 3.1 定义字体（`interface/core.gfx` 的 `bitmapfonts`）

```pdx
bitmapfonts = {
	# 全局颜色表（§ 代码 → RGB），见 localisation.md
	textcolors = { Y = { 255 189 0 } R = { 255 50 50 } ... }

	bitmapfont = {
		name = "hoi_18mbs"
		path = "gfx/fonts/hoi_18mbs"         # 不带扩展名；引擎找 .fnt + 图集
		color = 0xffffffff
		# 也可以在这里写这个字体专属的 textcolors
	}
}
```

最小示例在 `interface/fonts.gfx`（18 行，全文就 2 个 `bitmapfont`）——说明**新增一个字体只要一个 `bitmapfont` 块 + 一对 `.fnt/.dds`**。

### 3.2 中文覆盖（`interface/core_chinese.gfx`）

```pdx
bitmapfonts = {

	bitmapfont_override = {
		name = "hoi_18mbs"                    # 要覆盖哪个已注册字体
		fontfiles = {
			"gfx/fonts/chinese/hoi_18mbs_1of4"
			"gfx/fonts/chinese/hoi_18mbs_2of4"
			"gfx/fonts/chinese/hoi_18mbs_3of4"
			"gfx/fonts/chinese/hoi_18mbs_4of4"
		}
		languages = { "l_simp_chinese" }      # 只在简体中文下生效
	}
	...
}
```

- 实测（1.19.x）：`core_chinese.gfx` **38 个 `bitmapfont_override` 块 / 37 个不同名字**；
  另 `interface/chatfonts.gfx`（`standard_font`、`chat_input_font`）与 `interface/load_screen_font.gfx`
  （`loadscreen_header`、`loadscreen_tip`）再补 4 个名字 → **简中共 41 个字体名有中文分片**。
- 韩语同机制：`interface/core_korean.gfx`（38 个 override，`l_korean`）。
- **`bitmapfont_override` 是 mod 给中文换字体的官方入口**：在自己的 `interface/NS_fonts.gfx` 里写同样的块，
  指向自己的字体文件即可（必须用**同一个 `name`** 才会覆盖）。

## 4. 中文字体清单（哪些字体名有汉字）

**有中文 override（41 个，安全）**：

```
ToolTip_Font  AnimatedMapText  Main_16  Main_14  Main_14_black  Main_14_bold  Main_14_eu  Main_14_grey
Arial12  garamond_14  cg_16b  hoi_arrow_font  tahoma_60
hoi4_typewriter16  hoi4_typewriter16_inverted  hoi4_typewriter22  hoi4_typewriter22_inverted
hoi_16mbs  hoi_18  hoi_18b  hoi_18mbs  hoi_20b  hoi_20bs  hoi_22chat  hoi_22tech
hoi_24header  hoi_30  hoi_30header  hoi_33  hoi_36header  nsb_hoi_24header  nsb_hoi_36header
vic_18  vic_18_black  vic_22  vic_36  vic_36_black
standard_font  chat_input_font  loadscreen_header  loadscreen_tip
```

**没有中文 override（危险，汉字必然缺失）**：
`garamond_12、garamond_16、garamond_16_bold、garamond_14_bold、garamond_24、hoi_20、hoi_14mbs、hoi_15mbs、hoi_12mbs、
hoi_16tooltip3、hoi_16typewriter、hoi_26mbs、hoi_22typewriter、standard_18、standard_22、vic_18_grey、vic_18s、vic_22s、
vic_36s、vic_22_bl、tahoma_20_bold、cw_3d_debug、newsfeed_body、newsfeed_title、null_font`

> ⚠️ 典型踩坑：`hoi_14mbs` / `hoi_15mbs` / `hoi_12mbs` —— **名字看着像 `hoi_16mbs`，但没有任何 override 挂给它们**，装什么字体 mod 都没用。

### 常用选择建议

| 场景 | 字体 |
|---|---|
| 普通正文 / tooltip | `hoi_16mbs` |
| 小号说明文字 | `hoi_18b`、`Main_14`、`ToolTip_Font` |
| 卡片标题、按钮 | `hoi_18mbs`、`hoi_20bs`、`hoi_22tech` |
| 分区标题 | `hoi_24header`、`hoi_30header` |
| 页面大标题 | `hoi_36header`、`nsb_hoi_36header` |

`hoi_20bs` 是科技卡（203×84）常用名，中文可用；`hoi_22tech` 是原版科技页大字，中文可用。
**别用 `garamond_16`（看着像“主字体”，其实没中文）。**

> 复现命令（在 `<GAME_DIR>` 下）：`grep -ho 'bitmapfont_override' interface/core_chinese.gfx | wc -l` → 38；
> 或直接跑 `python $SKILL/scripts/font_audit.py --list-supported --game "<GAME_DIR>"`。

## 5. 第三方字体 mod 到底改变了什么

以工坊 `2977114459`（官方中文 52 字体替换）为例：它替换 **19 个字体名**的 fnt/dds，
并**同时提供自己的 `interface/core_chinese.gfx`**。也就是说它改的是
「这些名字对应的字形**长得什么样**」，**不改变**「哪些名字有中文」这件事。

推论：

- 装了字体 mod，`hoi_14mbs` 依然没有中文（它不在任何一方的 override 名单里）；
- 两个字体 mod 同时开，`core_chinese.gfx` 是**同名文件整体替换**，只有一个生效，
  某些名字可能因此失去分片 → 表现为「装完字体 mod 反而更多问号」。

## 6. 中文乱码/方框根因表

| 现象 | 根因 | 验证 | 修法 |
|---|---|---|---|
| 汉字变 `?` | 当前字体名没有中文分片，或分片里确实没该字形 | 看该字体名的 override；`.fnt` 里 `grep 'char id=<码位>'` | 换 §4 名单里的名字；或补字形（§8） |
| 汉字变方框/空白 | GUI 用了**没有中文 override 的字体名** | 查 §4 黑名单 | 换字体名 |
| 文字显示 key 名（`NS_title`） | yml 没 BOM / 非 UTF-8 / 文件名没带 `_l_simp_chinese` / key 拼错 | 十六进制看开头；控制台 `loc_check` | 用 UTF-8 with BOM 重存 |
| 中文变乱码方块（“锟斤拷”式） | 文件被存成 GBK/ANSI | 十六进制看是否 `EF BB BF` 开头 | 转 UTF-8 with BOM |
| 只有部分界面方框 | 不同界面用了不同字体，个别字体没 override | 看该 GUI 的 `font =` | 统一换字体名 |
| 地图文字方框 | 地图字体（`tahoma_60` → `gfx/fonts/chinese/hoi_mapfont4_*of11`）缺失 | 看 `gfx/fonts/chinese/hoi_mapfont4_*` | 用原版地图字体，别覆盖 |
| 文字全部消失 | 自定义 `bitmapfont_override` 的 `fontfiles` 路径错/数量错（4 页少一页） | 看 `logs/error.log` | 4 个文件齐全、路径对 |
| 加了自己的字体后原版中文变方框 | 自己的 `.gfx` 用同名 `bitmapfont_override` 顶掉了原版项 | `grep name =` 对比 | 换个 `name`，别覆盖原版 |
| 大面积 key 名/问号，且整份文件都不对 | yml 的 `"..."` 里有**裸换行**（引号不闭合）→ 整份文件失效 | 见 §10 | `\n` 转义后重存 |

## 7. 排查顺序（`????` 专用，按这个顺序走，别乱猜）

1. 同一份 yml 里有没有**任意一个 key 能显示中文**？
   - 能 → 文件加载正常，问题在**字体名**，不是 key/编码。
   - 不能 → 先查 BOM 与根键（`l_simp_chinese:` 与目录名 `simp_chinese` 对应）。
2. 看该控件的 `font =`，对照 §4 名单。
3. 跑 `font_audit.py`，一次性扫全 Mod（§9）。
4. 才轮到怀疑本地化被别的 mod 覆盖、语言设置、`replace_path`。

## 8. 给 mod 加中文字体（三种方案，按代价排序）

### 方案 A：零成本——用原版已有的中文字体名（推荐）

在 `.gui` 里写 `font = "hoi_18mbs"` / `"hoi_16mbs"` / `"hoi_20b"` / `"hoi_24header"` / `"vic_18"`，什么都不用做就能显示汉字。
**缺点**：只能用原版允许的那几种字号/字重。

### 方案 B：`bitmapfont_override` 换一套自己的字形（要更好看 / 要补字）

```pdx
# mod 里：interface/NS_fonts.gfx

bitmapfonts = {

	bitmapfont_override = {
		name = "hoi_18mbs"                     # 必须复用已有 name 才会被界面引用到
		fontfiles = {
			"gfx/fonts/NS/ns_cn_1of2"          # 自己的 .fnt/.dds 对（不带扩展名）
			"gfx/fonts/NS/ns_cn_2of2"
		}
		languages = { "l_simp_chinese" }
	}
}
```

前置条件：你得有 **BMFont 格式的 `.fnt` + 对应图集 `.dds`**（DXT5 或未压缩均可，DDS 细节见 [dds.md](dds.md)）。
生成工具：`BMFont`(AngelCode)、`Hiero`、`BMGlyph` 等，导出设置选 **binary=否 / texture=DDS / 字符集=自己的中文子集**（只导出用到的字，否则图集巨大）。
⚠️ 这些工具是否为 HOI4 所需格式的最佳选择未在本机验证——判定标准是「生成的 `.fnt` 头字段与 `gfx/fonts/chinese/*.fnt` 同构 + 图集能被引擎读到」。

**不要**只复制 `.fnt` 改个名字：没有 `bitmapfont_override` 就不会进中文替换流程。

### 方案 C：整文件替换原版中文字体（不推荐）

把 `gfx/fonts/chinese/*.dds` + `*.fnt` 整套替换（mod 同名路径文件会整体顶掉原版）。
**代价**：`gfx/fonts/chinese/` 实测 **约 1.1 GB / 222 个 `.fnt`**；随游戏更新需要重新同步；Workshop 体积不可接受。
只在「整套换字体品牌」时才考虑。

### 授权与体积注意

- 中文字体文件（尤其商业字体）版权归字体厂商；随 mod 分发 `.fnt/.dds` 等于分发了该字体的位图——先确认许可（常见可自由分发：思源黑体/Noto Sans SC、文泉驿、霞鹜文楷等，各自有许可条款，注意保留版权声明）。
- 体积控制：**只导出用到的汉字子集**（几千字 4 页→1 页），并压成 DXT5。
- 不要把原版 `gfx/fonts/chinese/` 复制进 mod（既超体积又违反“只放需要改的部分”原则）。

## 9. 体检：`font_audit.py`

```bash
python $SKILL/scripts/font_audit.py "<PROJECT_DIR>"                        # 扫 mod
python $SKILL/scripts/font_audit.py "<PROJECT_DIR>" --game "<GAME_DIR>"    # 指定游戏目录（默认自动探测）
python $SKILL/scripts/font_audit.py --list-supported --game "<GAME_DIR>"   # 只看名单
python $SKILL/scripts/font_audit.py "<PROJECT_DIR>" --json font.json       # 机器可读
```

- 读游戏的 `interface/core_chinese.gfx` 取真实名单（取不到时用内置 37 个兜底），
  扫描 Mod 的 `interface/**/*.gui` 与 `gfx/**/*.gui` 里所有 `font = "..."`，列出**没有中文分片**的名字并给出行号。
- 退出码 **0 = 全部安全；1 = 发现无中文分片的字体**，可直接进 CI。
- 只扫 `.gui`：`common/` 下的脚本、`.txt`、`.yml` 里不写字体名。
- ⚠️ **已知局限**：脚本只读 `core_chinese.gfx`（37 个名字），不含 `chatfonts.gfx` / `load_screen_font.gfx` 里的
  `standard_font`、`chat_input_font`、`loadscreen_header`、`loadscreen_tip` —— 用了这 4 个名字会被**误报**，人工排除即可。

## 10. 顺带：本地化多行必须转义（症状很像字体问题）

`.yml` 的 `"..."` 内不能有裸换行，否则**整份文件**失效（表现为大面积 key 名/问号），
和字体问题是两种不同的病，但症状极像：

```python
def loc_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
```

```yaml
# ❌ 坏行：引号没闭合，整份 yml 作废
NS_TECH_TOOLTIP:0 "第一行
第二行"
```

`hoi4_lint.py` 会查 BOM / 根键 / 重复 key，但**不查裸换行**，需要自己保证。详见 [localisation.md](localisation.md)。

## 11. 中文 yml 的正确存档姿势

| 编辑器 | 操作 |
|---|---|
| Notepad++ | 编码 → 「UTF-8 BOM」 |
| VS Code | 右下角编码 → "Save with encoding" → "UTF-8 with BOM" |
| Sublime | File → Save with Encoding → UTF-8 with BOM |
| 脚本（Python） | `open(p, "w", encoding="utf-8-sig", newline="\n")` |

验证：文件开头 3 字节必须是 `EF BB BF`。

## 12. 常见错误 / 自检清单

- [ ] 中文界面下所有 `font =` 都落在 §4 的「有中文 override」名单里。
- [ ] 页面标题、卡片名、tooltip、按钮四种字号各抽查一处中文。
- [ ] yml 三件套：UTF-8 with BOM + 文件名 `_l_simp_chinese` + 首行 `l_simp_chinese:`。
- [ ] 中文多行描述已 `loc_escape`（用 `\n`），无裸换行；`hoi4_lint.py` 0 error。
- [ ] 自己写的 `bitmapfont_override`：`name` 是已存在的字体名；`fontfiles` 数量与页数一致；`languages` 写 `"l_simp_chinese"`。
- [ ] 不覆盖 `gfx/fonts/chinese/` 原版文件（除方案 C）。
- [ ] 字形真的存在：`.fnt` 里 `grep 'char id=<码位>'` 能搜到（例如「民」= U+6C11 → 十进制 27665）。
- [ ] 没有为了「让中文显示」去改 `core_chinese.gfx`（除非确实在自建字体）。
- [ ] 改字体后重启；`logs/error.log` 搜 `bitmapfont` / `font` / `Failed to load`。
- [ ] `font_audit.py` 退出码 0（或误报的 4 个名字已人工排除）。
- [ ] 用原版中文界面自查：如果**原版中文正常、你的新增界面方框** → 100% 是字体名问题，不是本地化问题。

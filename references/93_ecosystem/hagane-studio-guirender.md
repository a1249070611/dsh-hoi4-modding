---
title: "guirender：重建游戏界面的 170 个模块"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
verified_at: 2026-11-06
method: 通读 internal/hoi4/guirender/ 与 imgcodec/ 关键文件
---

# 界面重建：guirender

位置：`internal/hoi4/guirender/`，**170 个文件、约 1 MB**，其中大半是 `_test.go`。
目标：**不启动游戏，把 HOI4 的界面在浏览器里画出来。**

## 一、为什么这件事难

HOI4 的界面是 `.gui`（布局）+ `.gfx`（精灵注册）+ `.dds`（图片）+ `.yml`（文字）
四层叠加，而且：

- 坐标是嵌套累加的（父容器偏移 + 子元素偏移）
- 尺寸可以用 `-1`、`100%` 之类相对值
- 有 40+ 种控件类型，每种行为不同
- 文字要按本地化语言切换

## 二、它的解法：先建一张全量索引

`index.go`（1082 行）不按需读文件，而是**一次性把所有 `.gui` / `.gfx` / `.yml` / `.fnt`
解析进内存：

```go
func NewIndex(files map[string][]byte) (*Index, error)
```

索引里存了：

| 内容 | 来源 | 用途 |
|---|---|---|
| `windows` | `.gui` 的 `windowType` | 一个可显示的窗口 |
| `sprites` | `.gfx` 的 `spriteType` | 名字 → 贴图文件 |
| `localisation` | `.yml` | 键 → 文字 |
| `fonts` | `.fnt` | 位图字体度量 |

对外接口很克制：

```go
idx.Window(name)          // 拿一个窗口的 AST
idx.ListWindows()         // 列出所有窗口
idx.SpritePNG(name)       // ★ 直接解出 PNG 字节
idx.Source(file)          // 拿原始文件内容
```

**`SpritePNG` 是亮点**：传入精灵名，它自己顺着 `spriteType → texturefile → 实际文件`
找到图片、解码、转成 PNG 返回：

```go
func (idx *Index) SpritePNG(name string) ([]byte, int, int, bool) {
	record, ok := idx.spriteRecordFor(name)
	for _, texture := range record.TextureFiles {
		actual, body, found := idx.localTexture(texture)
		img, err := importassets.DecodeImage(body, actual)
		png.Encode(&out, img)
		return out.Bytes(), bounds.Dx(), bounds.Dy(), true
	}
}
```

**前端只要 `<img src="/api/sprite/GFX_xxx">` 就能显示游戏原图**，不用自己处理 DDS。

## 三、DDS 编解码：手写 839 行，不依赖库

`internal/hoi4/imgcodec/`：

| 文件 | 行数 | 干什么 |
|---|---:|---|
| `dds.go` | 118 | 头部解析 + `EncodeDXT5DDS` |
| `bc3.go` | 166 | BC3/DXT5 块编解码 |
| `decode_bcn.go` | 132 | 所有 BCn 格式解码 |
| `decode_uncompressed.go` | 96 | 32bpp / 24bpp 解码 |

**注意它同时具备编码能力**（`EncodeDXT5DDS`）——不只是读，还能把改过的图写成
DDS 塞回项目。本库的 `kiant-hoi4-dds.py` 只解头部（128 字节），不碰像素。

> 这解释了为什么它不需要 Pillow：DDS 是 HOI4 的主力格式，Pillow 对它支持很差
> （只能写未压缩 32bpp，读也只认几种）。自己写反而更可靠。
> **本库上一轮的实测结论（99% 是未压缩 32bpp、DXT5 只有 43 个）在这里得到印证**：
> 它优先实现 `decode_uncompressed`（96 行覆盖 99% 的实际情况），BCn 是补充。

## 四、科技树布局：从 `.gui` 里读出真实网格

这是最实用的一节。`geometry.go`（101 行）解决了一个我一直没搞清的问题：
**科技树的格子到底多大、往哪个方向排。**

### 4.1 它读什么

在 `countrytechtreeview` 这个窗口里，找到名为 `technology_folder` 的节点，
然后递归下降找两种控件：

```go
switch strings.ToLower(nodeType) {
case "gridboxtype":       // 网格容器 → 格子尺寸 + 排列方向
case "instanttextboxtype": // 年份标签 → 行列刻度
}
```

### 4.2 坐标是累加的

```go
walk = func(node map[string]any, parentX, parentY int) {
	position, _ := node["position"].(map[string]any)
	x, y := parentX, parentY
	if position != nil {
		x += numeric(position["x"])   // ★ 累加，不是取绝对值
		y += numeric(position["y"])
	}
	for _, child := range nodeChildren(node) {
		walk(child, x, y)             // 把累计坐标传给子节点
	}
}
```

### 4.3 格子尺寸来自 `slotSize`

```go
width, height := 70, 70        // 默认 70×70
if raw, ok := node["raw"].(map[string]any); ok {
	if slot, ok := raw["slotSize"].(map[string]any); ok {
		if v, ok := slot["width"].(int); ok { width = numeric(slot["width"]) }
		if v, ok := slot["height"].(int); ok { height = numeric(slot["height"]) }
	}
}
```

**默认值是 70×70**——这大概是 HOI4 科技树的实际格子尺寸。而且它先做类型检查
（`if _, isBool := slot["width"].(bool); !isBool`），因为 `.gui` 里 `width = -1` 或
布尔值都合法。

### 4.4 排列方向来自 `format`

```go
columnMajor := strings.ToLower(strings.TrimSpace(grids[0]["format"].(string))) == "left"
```

`format = left` 表示**列优先**（先往下排，排满一列往右走）。这决定了年份标签该按 x 排序还是按 y 排序：

```go
sort.SliceStable(years, func(i, j int) bool {
	if columnMajor { return numeric(years[i]["x"]) < numeric(years[j]["x"]) }
	return numeric(years[i]["y"]) < numeric(years[j]["y"])
})
```

### 4.5 年份标签靠命名规则识别

```go
var yearLabelRE = regexp.MustCompile(`(?i)_year\d+$`)

case "instanttextboxtype":
	if yearLabelRE.MatchString(name) {     // 名字以 _year1 / _year2 ... 结尾
		years = append(years, map[string]any{"name": name, "text": text, "x": x, "y": y})
	}
```

**这是原版 `.gui` 里的命名惯例**——年份刻度控件的名字都以 `_year` 加数字结尾。
不靠猜位置，靠名字识别。

### 4.6 输出

```json
{
  "folder": "infantry_folder",
  "grids": [
    {"name": "...", "originX": 120, "originY": 80,
     "slotWidth": 70, "slotHeight": 70, "format": "left"}
  ],
  "yearLabels": [
    {"name": "..._year1", "text": "1936", "x": 120, "y": 80}
  ]
}
```

前端拿这个画 canvas。

> **本库该怎么用**：我们 `01_clausewitz-syntax.md` 里用递归解算 `relative_position_id`
> 得到的是**国策在数据层的位置**（绝对格子坐标）。但要精确还原科技树的**视觉**位置，
> 还需要叠加这一层 gridbox 的 `originX/originY` 和 `slotWidth/slotHeight`。
> 两者结合才是完整答案。

## 五、170 个模块怎么组织的

按界面区域拆，一个文件一个区域：

```
airoverview.go        空军总览
armyoverview.go       陆军总览
armyhq.go             陆军总部
buildings.go          建筑
characters.go         人物
construction.go       生产建设
continuousfocus.go    持续国策
countries.go          国家列表
countryprofile.go     国家档案
countrystats.go       国家统计
decisions.go          决议
diplomacy.go          外交
divisions.go          师
doctrines.go          学说
equipment_design.go   装备设计
events.go             事件
faction.go            阵营
focustree.go          国策树
frontend.go           主菜单
...
```

**几乎每个 `.go` 都配一个 `_test.go`**（`airoverview_test.go`、`armyoverview_test.go`…）。
这是"每个界面区域都能单元测试"的组织方式——因为它们都是
**输入 AST/索引 → 输出 JSON** 的纯函数，不依赖浏览器。

**关键设计**：渲染逻辑在 Go 侧完成，输出结构化 JSON；前端只负责把 JSON 变成 DOM/SVG。
这样 90% 的逻辑可以纯后端测试。

## 六、这套架构的代价

诚实地说，170 个模块是**巨大的维护负担**：

- 游戏每次更新界面，可能十几个模块要跟着改
- 每个区域都要手写"这 40 个字段怎么显示"
- 覆盖率不均（README 自己承认"不同功能的导入、导出覆盖程度并不完全相同"）

**它的选择是"用广度换深度"**：覆盖广但每处不一定完整。
本库的选择是"用深度换广度"：覆盖窄但每处都写透。

两种都合理，取决于使用者要什么。

## 七、本库能直接学的三点

### 7.1 精灵名 → PNG 的解析链

```python
def resolve_sprite(name) -> bytes | None:
    gfx = parse_gfx()                     # spriteType → texturefile
    tex = gfx.get(name)
    if not tex: return None
    return decode_dds(Path(tex))          # 需要解码器
```

本库目前只解析 `.gfx` 拿到路径（`checks.py` 里有 sprite 引用检查），
但**不能显示图片**。要显示就得实现 DDS 解码——可以参考它的 96 行未压缩解码器。

### 7.2 gridbox 几何读取

```python
def folder_geometry(gui_ast, folder_name):
    """递归累加 position，找 gridboxType 的 slotSize 和 format"""
```

这个可以用本库的 `cw.py` 解析 `.gui` 后实现，约 80 行。

### 7.3 「一个区域一个模块 + 一个测试」的组织

本库的 `preview.py` 现在是一个大文件管所有（国策树、事件、决议、理念）。
如果要扩到 170 个区域，必须拆。**现在拆比以后拆便宜。**

## 八、差距清单

| 能力 | 本库 | hagane-studio |
|---|---|---|
| 解析 `.gui` 成 AST | 有（cw.py） | 有 |
| 解析 `.gfx` 拿精灵路径 | 有（checks.py） | 有 |
| **DDS 解码成像素** | ❌ | ✅ 839 行 |
| **DDS 编码（写回）** | ❌ | ✅ |
| **`.gui` 布局几何还原** | ❌ | ✅ 101 行 |
| 界面渲染模块数 | 4 个区域（preview.py） | 170 个 |
| 位图字体度量 | ❌ | ✅ bitmapfont.go |

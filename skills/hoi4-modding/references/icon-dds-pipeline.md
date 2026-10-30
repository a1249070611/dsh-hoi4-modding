# 科技/装备 2D 图标流水线：照片 → 173×77 DDS（实战）

> 适用：把坦克照片/矢量图做成 HOI4 科技卡图标、装备 2D 图标；处理白底/棋盘格/阴影、保护白色涂装、
> 解决“图标出框 / 偏左 / 白边 / 涂装被挖空”。
> 本文是 `hist_tech_trees`（30 辆德国坦克科技）全套照片图标的量产经验。

## 0. 关键结论（先看这 4 条）

1. **科技卡图标画布 173×77**；卡片背景 183×84，卡内 `Icon` 控件是 `position {x=74 y=50}` + `centerposition`，
   所以 **173 宽的图在 183 卡里左右各出 5px**：内容必须留安全边距，否则炮管/履带会被卡片边框裁掉。
2. 原版照片/渲染图多数是**白底或 8px 棋盘格（纯白+灰 130/192）**，必须去背景；透明 PNG 最省事，优先找。
3. **白色涂装/白色编号会被“去白底”算法一起挖掉**：保护规则 = 区域平均亮度 ≥235 **且** 相对位置偏上（relY<0.8）→ 保留。
4. 批量导入必须有 **别名表**：文件名 ≠ 科技中文名（如 `四号坦克F型.png` → `GER_pz4_f1`、`38(t)A型`、`35(t)`）。

## 1. 卡片几何：为什么图标要“右移”

```pdx
# countrytechtreeview.gui 的 item 模板（原版）
containerWindowType = { name = "techtree_GER_armor_item" size = { width = 183 height = 84 }
	iconType = { name = "Icon" position = { x = 74 y = 50 } centerposition = yes }
	instantTextBoxType = { name = "Name" position = { x = 6 y = -1 } }
	background = { spriteType = "GFX_technology_unavailable_item_bg" }  # 286×109
}
```

- 卡片可见内容区约 **183×84**；`Icon` 的中心在卡片 x=74，而卡片中心是 91.5 → 图标整体天然偏左 17.5px。
- 因此 **173×77 的图标内容**建议：
  - 水平：左边距 **20px**、右边距 **4px**（内容整体右移 8px，把炮管/车身放在视觉中心）；
  - 垂直：上下各留 **2px**，最大内容 **149×73**。
- 具体数值可按立绘方向微调（炮口朝左的图可反过来），但**右侧不能顶满**，否则车头/炮口出框。

## 2. 输入类型与去背景

| 输入 | 处理 |
|---|---|
| 透明 PNG/WebP（矢量导出） | 直接用 alpha，最省事；裁 bbox → 缩放 → 贴到安全区 |
| 纯白底 | 从边界 flood fill 去白（容差 ~12），保留内部白色（高光/白涂装） |
| 8px 棋盘格（白 + 灰 130/192） | 先识别两种背景色，按“边界连通 + 颜色接近任一背景色”泛洪；再做 1px 腐蚀+描边 |
| 阴影/渐变背景 | 难；优先找透明版，或 PS 手动抠图 |
| 白底带白色涂装 | 用第 3 条保护规则，否则涂装会被挖空 |

推荐流程：

```
1) 转 RGBA
2) 估计背景色：取四条边上的高频中性色（R≈G≈B），最多取 2 个峰
3) 从边界 flood fill：颜色接近任一背景色 → 透明
4) 保护：连通的“白色区域”若 平均亮度≥235 且 中心 relY<0.8 → 保留（白涂装/编号）
5) 其他内部洞（履带缝、观察窗）：用前景色填充或按最近深色覆盖
6) 腐蚀 1px（去掉白边），边缘轻微重着色
7) 预乘 alpha 下采样（避免灰边）
8) 裁 bbox → 按最大 149×73 等比缩放 → 贴到 173×77 画布的安全位置（左 20/右 4/上下 2）
9) 输出 PNG + DDS（dds_helper raw32 173×77）
10) 合成 183×84 卡片预览，检查不越框
```

## 3. 别名与匹配

批量导入时用**文件名模糊匹配** + 显式别名表：

```python
ALIASES = {
    "四号坦克F型": "GER_pz4_f1",      # 早期 F1（短管）与后期 F2 区分
    "38(t)A型":  "GER_pz38t_ad",
    "35(t)":     "GER_pz35t",
}
```

匹配顺序：`big_zh/big_en` 精确 → 小名（small_zh）精确 → 小名首词 → 唯一子串包含 → 别名表。
**不要用“任意包含”直接命中**：`四号坦克F型` 会同时匹配 F1/F2/G/H，必须最先用别名表消歧。

## 4. 输出与注册

```bash
python "$S/dds_helper.py" make GER_pz4_f1.png \
  gfx/interface/technologies/GER_armor/GER_pz4_f1.dds --width 173 --height 77
python "$S/dds_helper.py" check gfx/interface/technologies/GER_armor/GER_pz4_f1.dds
```

```pdx
# interface/NS_tech_icons.gfx
spriteTypes = {
	spriteType = { name = "GFX_GER_pz4_f1_medium" texturefile = "gfx/interface/technologies/GER_armor/GER_pz4_f1.dds" }
}
```

- 科技卡模板里图标 sprite 名按原版约定：`GFX_<tech>_medium`（`<tech>_small` 用于小框）；
- **每张图 173×77，raw32 未压缩**（原版 UI 同构；体积约 53KB/张，30 张 1.6MB，可接受）；
- 共享占位图标时只注册一张 sprite，多个科技共用。

## 5. 卡片预览自检（不越框）

```python
CARD = Image.open(GAME / "gfx/interface/techtree/technology_available_item_bg.dds").convert("RGBA")
card = CARD.resize((183, 84), Image.LANCZOS)
icon = Image.open("GER_pz4_f1.png").convert("RGBA")
card.alpha_composite(icon, (74 - icon.width // 2, 50 - icon.height // 2))
card.save("preview_card.png")
```

检查点：炮管/车头不出框；左右留白均衡（视觉重心略右）；与同排其他卡片的车体大小一致（缩放按“车长”统一，
不要按图片 bbox 高度统一，否则炮塔高低不一）。

## 6. 踩坑表

| 症状 | 原因 / 修法 |
|---|---|
| 图标左侧被裁 | 内容顶满 173 宽；加大 left margin（本项目用 20px） |
| 图标整体偏左 | 没考虑 Icon 控件中心 x=74；内容整体右移 8px |
| 白边/灰边 | 未腐蚀边缘；缩放前未预乘 alpha |
| 白色涂装/编号被挖空 | 缺少白涂装保护规则（亮度≥235 + relY<0.8） |
| 棋盘格残留 | 只按单色去背；需检测两种背景色并联合泛洪 |
| 各卡大小不一 | 缩放基准不一致（按车长/统一系数，而不是 bbox 高） |
| 导入后图标不显示 | sprite 没注册 / 路径大小写 / DDS 尺寸不对（必须 173×77 或模板要求尺寸） |
| 装备图标显示错位 | 装备 2D 图标尺寸不同（原版 81×37 等），不要拿科技卡 173×77 混用 |

## 7. 配套脚本

`scripts/tech_icon_import.py`（需 Pillow）：
- 单张/批量（目录或 JSON 映射）输入 → 去背（transparent / white / checker / auto）→ 安全区 173×77 →
  PNG + DDS（调用 `dds_helper.py`）；
- `--card-preview` 输出 183×84 合成卡，直接目检是否出框；
- `--alias alias.json` 传文件名→科技 id 映射，批量时用于消歧。

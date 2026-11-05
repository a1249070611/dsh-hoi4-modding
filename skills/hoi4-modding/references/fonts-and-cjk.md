# 中文字体与 `????` 的真正根因（HOI4 1.19.3 实测）

> 这一页推翻了很多教程里「装个字体 mod 就好」的说法。
> 实测对象：原版 1.19.3 + 23 个工坊 mod（含 3 个字体/汉化 mod）。

## 0. 一句话

**汉字不在 `.fnt` 里，在 `gfx/fonts/chinese/` 的分片里；只有被 `interface/core_chinese.gfx` 的
`bitmapfont_override` 覆盖过的字体名，才有中文分片。**

所以：控件写 `font = "hoi_14mbs"` → 这个字体名没有分片 → 中文一律 `????`。
和是否装了第三方字体 mod **无关**。

## 1. 机制

原版 `interface/core_chinese.gfx` 里有 **37 个 `bitmapfont_override` 块**，形状是：

```pdx
bitmapfont_override = {
    name = "hoi_16mbs"
    fontfiles = {
        "gfx/fonts/hoi_16mbs.fnt"
        "gfx/fonts/chinese/hoi_16mbs_0.fnt"
        "gfx/fonts/chinese/hoi_16mbs_1.fnt"
        "gfx/fonts/chinese/hoi_16mbs_2.fnt"
        "gfx/fonts/chinese/hoi_16mbs_3.fnt"
    }
    languages = { "l_simp_chinese" }
}
```

- 基础 `.fnt`（`gfx/fonts/hoi_16mbs.fnt`）**只含拉丁字形**；
- `gfx/fonts/chinese/hoi_16mbs_Nof4.fnt` 才含汉字（`hoi_16mbs` 四片合计 41,952 个 CJK 字形）；
- 切到 `l_simp_chinese` 时，引擎用 override 里的 `fontfiles` 整体替换该字体名的字形表。

实测数据：游戏全部 57 个 `.fnt` 文件，**自身 CJK 字形计数全部为 0**。
这就是「拉丁字母正常、汉字变问号」的完整解释。

## 2. 安全字体名单（1.19.3，37 个）

```
ToolTip_Font  AnimatedMapText
Main_14  Main_14_black  Main_14_bold  Main_14_eu  Main_14_grey  Main_16
Arial12  cg_16b  garamond_14
hoi4_typewriter16  hoi4_typewriter16_inverted  hoi4_typewriter22  hoi4_typewriter22_inverted
hoi_16mbs  hoi_18  hoi_18b  hoi_18mbs  hoi_20b  hoi_20bs
hoi_22chat  hoi_22tech  hoi_24header  hoi_30  hoi_30header  hoi_33  hoi_36header
hoi_arrow_font  nsb_hoi_24header  nsb_hoi_36header  tahoma_60
vic_18  vic_18_black  vic_22  vic_36  vic_36_black
```

**不在这个名单里的字体名，一律不要用来显示中文。** 典型踩坑：
`hoi_14mbs`、`hoi_15mbs`、`hoi_12mbs` —— 名字看着像，但没有分片。

### 常用选择建议

| 场景 | 字体 |
|---|---|
| 普通正文 / tooltip | `hoi_16mbs` |
| 小号说明文字 | `hoi_18b`、`Main_14`、`ToolTip_Font` |
| 卡片标题、按钮 | `hoi_18mbs`、`hoi_20bs`、`hoi_22tech` |
| 分区标题 | `hoi_24header`、`hoi_30header` |
| 页面大标题 | `hoi_36header`、`nsb_hoi_36header` |

`hoi_20bs` 是科技卡（203×84）的常用名，中文可用；
`hoi_22tech` 是原版科技页大字，中文可用。

## 3. 体检脚本

```bash
python scripts/font_audit.py "D:/mods/MyMod"
python scripts/font_audit.py "D:/mods/MyMod" --game "E:/Steam/steamapps/common/Hearts of Iron IV"
python scripts/font_audit.py "D:/mods/MyMod" --list-supported   # 只看名单
python scripts/font_audit.py "D:/mods/MyMod" --json font.json   # 机器可读
```

它读游戏的 `core_chinese.gfx` 取真实名单（取不到时用内置 38 个兜底），
扫描 Mod 的 `interface/**/*.gui` 与 `gfx/**/*.gui` 里所有 `font = "..."`，
列出**没有中文分片**的名字并给出行号。退出码 1 表示有问题，可直接进 CI。

> 只扫 `.gui`。`common/` 下的脚本、`.txt`、`.yml` 里不写字体名。

## 4. 自建字体（可选）

想让一个**新名字**（比如 `my_ui_font`）支持中文，需要：

1. 准备含 CJK 的 `.fnt` + 对应 `.dds` 图集（可用 BMFont / Hiero 生成）；
2. 在 `interface/NS_fonts.gfx` 写自己的 `bitmapfont_override`：

```pdx
bitmapfont_override = {
    name = "my_ui_font"
    fontfiles = {
        "gfx/fonts/my_ui_font.fnt"
        "gfx/fonts/chinese/my_ui_font_0.fnt"
    }
    languages = { "l_simp_chinese" }
}
```

3. 确认没有别的 mod 也覆盖同名 `interface/core_chinese.gfx`（同名文件整体替换，
   后加载的赢；两个字体 mod 同时启用时，只有一个的名单生效）。

**不要**只复制 `.fnt` 改个名字：没有 `bitmapfont_override` 就不会进中文替换流程。

## 5. 第三方字体 mod 的真实作用

以工坊 `2977114459`（官方中文 52 字体替换）为例：它替换 **19 个字体名**的 fnt/dds，
并**同时提供自己的 `interface/core_chinese.gfx`**。也就是说它改变的是
「这些名字对应的字形长得什么样」，不改变「哪些名字有中文」这件事。

推论：
- 装了字体 mod，`hoi_14mbs` 依然没有中文（它不在任何一方的 override 名单里）；
- 两个字体 mod 同时开，`core_chinese.gfx` 互相整体替换，**只有一个生效**，
  某些名字可能因此失去分片 → 表现为「装完字体 mod 反而更多问号」。

## 6. 排查顺序（`????` 专用）

1. 同一份 yml 里有没有**任意一个 key 能显示中文**？
   - 能 → 文件加载正常，问题在字体名，不是 key/编码。
   - 不能 → 先查 BOM 与根键（`l_simp_chinese:` 与目录 `simp_chinese` 对应）。
2. 看该控件的 `font =`，对照 §2 名单。
3. 跑 `font_audit.py`，一次性看全 Mod。
4. 才轮到怀疑本地化被别的 mod 覆盖、语言设置、`replace_path`。

## 7. 顺带：本地化多行必须转义

`.yml` 的 `"..."` 内不能有裸换行，否则**整份文件**失效（表现为大面积 key 名/问号），
和字体问题是两种不同的病，但症状很像：

```python
def loc_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
```

`hoi4_lint.py` 会查 BOM / 根键 / 重复 key，但**不查裸换行**，需要自己保证。

## 8. 验收清单

- [ ] `font_audit.py` 退出码 0；
- [ ] 页面标题、卡片名、tooltip、按钮四种字号各抽查一处中文；
- [ ] 没有为了「让中文显示」去改 `core_chinese.gfx`（除非确实在自建字体）；
- [ ] 中文多行描述已 `loc_escape`，`hoi4_lint.py` 0 error。
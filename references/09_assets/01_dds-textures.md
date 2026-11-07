---
title: "DDS 贴图：字节级实测与替换规则"
domain: 09_assets
verified_on: 1.19.4.2
verified_at: 2026-11-06
method: tools/kiant-hoi4-dds.py 对 gfx/ 全量 21898 个 DDS 解析头部，非文档抄录
---

# DDS 贴图

DDS 是全游戏**数量最多、体积最大**的文件类型：33007 个、4880 MB。
界面、国策图标、单位头像、地图纹理全是它。这篇讲清三件事：文件里到底存了什么、
原版实际用的是什么规格、自己换图时要注意什么。

## 一、文件结构：128 字节头 + 像素数据

```
偏移   长度  字段              说明
  0     4   magic            "DDS " 四个字符，不对就不是 DDS
  4     4   dwSize           固定 124（头本身除 magic 外的长度）
  8     4   dwFlags          标志位，决定哪些字段有效
 12     4   dwHeight         高
 16     4   dwWidth          宽
 20     4   dwPitchOrLinear  未压缩=每行字节数；压缩=总字节数
 24     4   dwDepth          卷深，2D 图恒为 0
 28     4   dwMipMapCount    mip 级数，0 表示只有 1 级
 ...
 76    32   DDS_PIXELFORMAT  像素格式（关键）
 76     4     dwSize         固定 32
 80     4     dwFlags        DDPF_FOURCC(0x4)=压缩 / DDPF_RGB(0x40)=未压缩
 84     4     dwFourCC       "DXT1"/"DXT3"/"DXT5"/"DX10"；未压缩时为 0
 88     4     dwRGBBitCount  每像素位数：32 / 24 / 8
 92     4     dwRBitMask     红色通道掩码
 96     4     dwGBitMask
100     4     dwBBitMask
104     4     dwABitMask      alpha 掩码，0 表示没有 alpha
108     4   dwCaps
112     4   dwCaps2         立方体贴图/体积纹理标志
```

**后面接什么**：`128 字节` 之后直接是像素数据。如果是 DX10 格式，中间还多一个
20 字节的扩展头（DXGI 格式枚举），之后的像素数据位置要相应后移。

用 `struct` 一次解出来：

```python
import struct
h = open(path, "rb").read(128)
assert h[:4] == b"DDS "
height, width = struct.unpack("<II", h[12:20])
mips = struct.unpack("<I", h[28:32])[0]
pf_size, pf_flags, fourcc, rgbbits, rmask, gmask, bmask, amask = \
    struct.unpack("<II4sIIIII", h[76:108])
```

## 二、原版实际在用什么（实测，不是猜）

`gfx/interface` 下 **16923 个 DDS** 的格式分布：

| 格式 | 数量 | 占比 |
|---|---:|---:|
| **未压缩 32bpp** | **16773** | **99%** |
| DXT1 | 63 | 0.4% |
| DXT5 | 43 | 0.3% |
| 未压缩 24bpp | 22 | 0.1% |
| DXT3 | 13 | 0.08% |
| DX10 | 8 | 0.05% |
| RXGB | 1 | 0.006% |

### 这张表推翻了两个流行说法

**说法一「mod 贴图必须用 DXT5」——错的。**
P 社自己 99% 用未压缩 32bpp。DXT5 全库只有 43 个。用 DXT5 的优势是体积小 4 倍，
但界面图标本来就小，省这点空间不值得引入压缩噪点——**图标边缘的锯齿就是 DXT 压缩造成的**。

**说法二「DDS 必须有 mipmap」——错的。**
`gfx/` 下 21898 个 DDS 有 **19331 个只有单级 mip**（88%）。这 19331 个里，
**14384 个**（65%）头部写的 `dwMipMapCount` 是 `0`，另外 **4947 个**写的是 `1`——
两种写法指的是同一件事（只有一级），引擎都认。mipmap 是给 3D 远距离
渲染用的，2D 界面图标在屏幕上永远是固定像素大小，生成 mip 纯属浪费体积。

什么时候**该**用 DXT：体积大的地图/天空盒/模型贴图（`gfx/models/`、`map/`），
那里压缩收益明显。界面图标用 32bpp。

## 三、尺寸规律：原版大多不是 2 的幂

按出现频次排的头部尺寸：

```
100x88   2783 个      ← 不是 2 的幂
65x67    1638 个      ← 连奇数都有
131x52   1324 个
60x68    1159 个
64x64     979 个      ← 唯一规矩的那个
508x248   791 个
```

**2 的幂不是硬要求。** 实测 `gfx/interface` 下 16923 个 DDS：

| 宽是 2 的幂 | 高是 2 的幂 | 数量 | 占比 |
|---|---|---:|---:|
| ❌ | ❌ | 15035 | **89%** |
| ✅ | ✅ | 1302 | 7% |
| ❌ | ✅ | 457 | 2.7% |
| ✅ | ❌ | 129 | 0.8% |

**93% 的图至少有一边不是 2 的幂**，P 社自己也大量用 `65x67`、`131x52` 这种尺寸。
这是又一个被教程误导的点——老式 GPU 要求纹理边长是 2 的幂，现代 GPU 不需要。

真正要守的是**一致性**：同一个图标在 `.gfx` 里注册成 `size = { x = 60 y = 68 }`，
图片实际是 60x68，两者必须对上。对不上不会报错，只是显示被拉伸或裁切。

## 四、体积校验：21898 个文件零例外

每个格式的理论像素字节数：

| 格式 | 公式 |
|---|---|
| 32bpp | `w × h × 4` |
| 24bpp | `w × h × 3` |
| DXT1 | `ceil(w/4) × ceil(h/4) × 8` |
| DXT3 / DXT5 / RXGB | `ceil(w/4) × ceil(h/4) × 16` |
| DX10 | 需读扩展头，无法从主头推算 |

**块压缩必须向上取整**，这点极易错。`72x21` 的 DXT5，块数是
`ceil(72/4) × ceil(21/4) = 18 × 6 = 108`，`108 × 16 = 1728` 字节。
如果用整除 `21 // 4 = 5`，会算成 1440，然后误判文件「体积偏大」。

> 这个坑我自己踩过：`tools/kiant-hoi4-dds.py` 第一版用 `w // 4`，对 `accept_decline_icon.dds`
> 报「⚠ 偏大」，看着像文件损坏，实际是公式写错。修正后拿 `gfx/` 全部
> **21898 个文件复核，零例外全部精确匹配**——这才叫验证过了。

有 mipmap 时逐级累加，每级尺寸减半（最小 1），**每级按自己的尺寸独立算块数**，
不能拿上一级的字节数除 4——宽高奇偶交替时块数不是整数倍，累加会漂。

## 五、引用链的实测规模：原版自己就有 491 处死引用

扫 `interface/` 下所有 `.gfx` / `.gui` 里的 `textureFile` 引用（大小写混用，实测两种写法都有）：

| 指标 | 数值 |
|---|---:|
| `textureFile` 引用总数 | 28916 处 |
| 扩展名 `.dds` | 25240 处（87%） |
| 扩展名 `.png` | 76 处 |
| 扩展名 `.tga` | 60 处 |
| **引用的文件按字面路径找不到** | **491 处（1.9%）** |

### 491 处死引用长什么样

| 类型 | 数量 | 例子 |
|---|---:|---|
| 文件名对不上 | 431 | 写 `gfx/aces/GER_ace_Erich_Hartmann.dds`，实物叫 `GER_Erich_Hartmann_ace.dds` |
| 扩展名对不上 | — | 引 `sort_button_83x29.tga`，实物是 `.dds` |
| 路径里双斜杠 | 60 | `gfx//interface//sort_button_83x29.tga` |

**双斜杠引擎能归一化**（折叠成单斜杠），所以这类不是错，是我正则没归一化导致的假阳性——
归一化后它们仍然「找不到」，是因为扩展名写错，不是路径写错。

**这些是原版 1.19.4.2 自己写错的**，游戏里表现为对应图标显示成占位图。
写校验器时要注意：**死引用率到 2% 是正常的**，别把阈值定成 0，否则原版都过不了。

### 大小写到底敏不敏感

**键名不敏感，已有两条独立证据：**

1. `.gfx` 里 `textureFile` 和 `texturefile` 两种写法**都存在于原版**
   （实测共 28916 处，大写开头占绝大多数）。
2. `interface/countrytechtreeview.gui` 里同一个控件，属性名写 `slotsize`（全小写），
   `format` 的值写成 `"LEFT"`（大写带引号）——**同一个文件内混用**，
   引擎照样正常工作。

如果不敏感，这在实现上意味着什么：引擎读属性时做大小写折叠（`EqualFold` 之类）。
hagane-studio 的 `internal/hoi4/guirender/index.go` 就是全用 `strings.EqualFold`
读属性名的（`ciScalar` / `ciPoint`，`ci` = case-insensitive）。

**但路径值里的文件名是否敏感，仍无法从文件层面证明**——Windows 文件系统本身不区分，
必须进游戏加一张大小写不符的贴图看是否加载才能确定。**这一条留作待验证。**

> 一个旁证：hagane-studio 在构建 ZIP 时做了**大小写折叠冲突检查**
> （`artifact.go` 里 `strings.ToLower(clean)` 后查重），理由是"解压到 Windows
> 会把 `Foo.txt` 和 `foo.txt` 合并成一个，静默丢文件"。
> **它防的是目标文件系统，不是引擎。** 这两个问题要分开看。

> 踩坑记录：我第一版统计用 `texturefile`（全小写）做正则，Python `re` 默认区分大小写，
> 于是漏掉了绝大多数引用，算出「6109 个孤儿贴图（36%）」。改成 `re.I` 后降到 3153（18%）。
> **规则不完整就会这样：大面积误报，数字看着骇人但全是假的。**
> 统计贴图前先拿一两个已知结果对一遍，别直接信总数。

## 六、换图的操作流程

```bash
# 1. 先看原文件规格，照着做
python tools/kiant-hoi4-dds.py info gfx/interface/goals/goal_generic_construct.dds
#    → 60x68  未压缩 32bpp  mips=1  alpha=有

# 2. 做一张同尺寸、带 alpha 的 PNG/TGA，转成 DDS
#    （Photoshop: NVIDIA Texture Tools / GIMP: DDS 插件 / 命令行: texconv）
#    格式选 A8R8G8B8（未压缩 32bpp），不要勾 mipmap

# 3. 校验结果
python tools/kiant-hoi4-dds.py check 新文件.dds --expect 60x68
```

**必须保持 alpha 通道**。图标、按钮、旗帜都是靠 alpha 抠出不规则形状的，
丢了 alpha 会变成一个实心方块。

## 七、兼容性陷阱

| 陷阱 | 后果 | 怎么避 |
|---|---|---|
| 尺寸与 `.gfx` 里的 `size` 不符 | 拉伸/裁切，不报错 | 改完对一遍 `size` |
| 丢了 alpha 通道 | 变实心方块 | 用 32bpp + `DDPF_ALPHAPIXELS` |
| 用了 DX10 格式 | 老版本可能不认 | 别用，选 DXT5 或 32bpp |
| 文件名大小写不符 | 找不到，显示占位图 | 见下方「大小写到底敏不敏感」 |
| 放在错误的 `gfx/` 子目录 | 只在特定界面生效 | 按原文件同路径放 |
| 勾了 mipmap | 体积翻 1.33 倍，无收益 | 2D 图标不要 mip |

## 八、自查

```bash
python tools/kiant-hoi4-dds.py scan gfx/                          # 整个目录的格式分布
python tools/kiant-hoi4-dds.py info a.dds b.dds                   # 逐个详查 + 体积校验
python tools/kiant-hoi4-dds.py check x.dds --expect 60x68         # 尺寸对不对
```

三个子命令都是零依赖，只用 Python 自带的 `struct`——
不需要 Pillow，不需要装任何东西。

---
title: "资源域总览：图片 / 模型 / 动画 / 音频"
domain: 09_assets
verified_on: 1.19.4.2
---

# 09 资源文件

这一域管的是「素材」——不能手写、只能用工具生成或替换的东西。
全库 **60366 个文件里 59000+ 是素材**，占体积 10 GB 中的 9.5 GB。

和 `08_fileformats/` 的分工：那边讲文本格式（能打开读、能改）；
这边讲二进制格式（只能靠工具解、靠实测摸清规律）。

## 本域 5 条最重要结论

1. **贴图占绝对多数**：`.dds` 33007 个 / 4880 MB + `.tga` 6889 个 / 173 MB。
   改了界面却「没变化」，九成是贴图这一环断了。

2. **`.dds` 99% 是未压缩 32bpp，88% 只有单级 mip（无 mipmap），93% 不是 2 的幂。**
   三条都和网上教程说的相反。`gfx/` 下 21898 个里 32bpp 占绝大多数，DXT5 只有 43 个。
   跟着原版做比跟着教程做可靠。

3. **`.anim` 和 `.asset` 是纯文本，不是二进制。** `.anim` 是 Clausewitz 文本
   （头 `@@t@pdXasset i21`），`.asset` 是索引表（`animation = { name file }` /
   `entity = { name pdxmesh }`）。这两种不用工具就能读。

4. **`.mesh` 是混合格式**：文本头 + 二进制顶点数据。文本头能读（能看出顶点数、
   材质名），顶点数据不能手改，要过 Blender 流程。

5. **`.fnt` 是 BMFont 文本 + 一张图集**。中文字体被切成 `1of4`~`4of4` **四个分片，
   按码位切分、互不重叠**（4 片合计 30530 个唯一字符，彼此只有 1 个重叠＝空格）。
   每片 7677 / 7813 / 8002 / 7041 个字。改字体必须四片一起换，只换一片会出现方框。

## 篇目

| 篇 | 讲什么 |
|---|---|
| `01_dds-textures.md` | DDS 字节级结构、原版真实规格、体积公式、换图流程 |

## 素材调用的四层链

改了图不生效，一定是这条链断了某一环。逐层往上查：

```
.gfx 文件（interface/*.gfx）
   spriteType = { name = "GFX_button_attack"  texturefile = "gfx/interface/button.dds" }
        │
        ├─ name 被谁引用？  → .gui 文件里的 buttonType、或国策的 icon = ...
        │
        └─ texturefile 指向的文件在不在？尺寸对不对？
```

**最常见的断点**：`.gfx` 里注册了名字但 `.gui` 用的名字拼错；或图片路径大小写不符
（Windows 不敏感，但引擎内部可能按字面匹配）。

## 常见坑

| 症状 | 原因 | 去哪 |
|---|---|---|
| 换图后显示成紫黑格 | 格式不被支持（DX10 在新旧版本间不兼容） | `01_dds-textures.md` §六 |
| 图标变实心方块 | 丢了 alpha 通道 | `01_dds-textures.md` §五 |
| 图片被拉伸/裁切 | 尺寸与 `.gfx` 的 `size` 不符 | `01_dds-textures.md` §三 |
| 中文显示成方框 | 只换了字号分片中的一片 | 本篇 §5 |
| 模型/动画不显示 | `.asset` 没注册，或 entity 名对不上 | 见 `08_fileformats/` |

## 工具

```bash
python tools/kiant-hoi4-dds.py info x.dds          # 头部详查 + 体积校验
python tools/kiant-hoi4-dds.py scan gfx/interface  # 整个目录的格式分布
python tools/kiant-hoi4-dds.py check x.dds --expect 60x68
```

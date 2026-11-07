---
title: DDS 贴图格式（BC1/3/5、尺寸、mipmap、Alpha、生成与校验）
domain: 05_presentation
scope: gfx
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - gfx/interface/
  - gfx/leaders/
  - gfx/flags/
  - gfx/fonts/chinese/
  - $SKILL/scripts/dds_helper.py
  - https://github.com/microsoft/DirectXTex/wiki/Texconv
---

# DDS 贴图格式

基线 **1.19.x**。`<GAME_DIR>` = 游戏根，`<PROJECT_DIR>` = mod 工程，`$SKILL` = 本技能目录。

> 本页是 DDS 的**唯一权威页**：格式、压缩族、尺寸、mipmap、Alpha、用途对照、生成/校验管线、排错。
> sprite 侧（`interface/*.gfx` 怎么注册这张图）见 [gfx-sprites.md](gfx-sprites.md)；
> 具体尺寸的肖像/旗帜规范见 [portraits-flags.md](portraits-flags.md)；
> 照片→科技卡图标的项目级量产流水线（去背、173×77 安全区）属于案例区，不在本页。

## 1. 一句话

HOI4（Clausewitz / D3D9 风格）读的是**标准 128 字节头 + 原始或块压缩像素**的 DDS。
**体积优化才用 BC 压缩；不确定时用未压缩 32bpp（原版 UI 图标的主流写法）。**

## 2. 文件结构

```text
偏移 0    : b"DDS "              # magic，4 字节
偏移 4    : DDS_HEADER           # 124 字节（dwSize=124 + 字段）
偏移 128  : 像素负载             # 未压缩 = width*height*4（BGRA）；BC = 块数据
```

- 头里 `ddspf`（DDS_PIXELFORMAT, 32 字节）决定像素怎么读：`DDPF_FOURCC(0x4)` = 块压缩，`DDPF_RGB(0x40)|DDPF_ALPHAPIXELS(0x1)` = 未压缩带 alpha。
- 未压缩 32bpp 的**内存字节序是 BGRA**（掩码 `R=0x00ff0000 G=0x0000ff00 B=0x000000ff A=0xff000000`）。
- **`DX10` 扩展头**（多 20 字节、`dxgiFormat` 字段）是 D3D11 风格，HOI4 不保证支持 → 导出时选「DXT5 / BC3」而不是「BC3_UNORM + DX10」。

## 3. 压缩族对照（HOI4 能读的）

| 叫法 | DDS 里 | 块大小 | 每像素 | 用途 | HOI4 |
|---|---|---|---|---|---|
| BC1 | `DXT1` | 8 字节/4×4 | 4 bpp（0.5 B/px） | **无 alpha 或 1-bit 硬 alpha** 的 diffuse/UI | ✅ |
| BC2 | `DXT3` | 16 字节/4×4 | 8 bpp | 4-bit **显式** alpha（硬边、渐变差） | ✅ |
| BC3 | `DXT5` | 16 字节/4×4 | 8 bpp | **插值 alpha，平滑**；字体图集 / normal 也在用 | ✅ 首选压缩格式 |
| BC4 | `ATI1`/`BC4U` | 8 字节/4×4 | 单通道 | 灰度/高度/单通道遮罩 | 一般用不到 |
| BC5 | `ATI2` | 16 字节/4×4 | 双通道 | **切线空间法线图**（比 DXT5 存 normal 更准） | ✅ 可，但不必须 |
| BC7 | `DX10`+`dxgiFormat=98` | 16 字节/4×4 | 8 bpp | D3D11 高质量压缩 | ❌ 别用 |
| BC6H | `DX10`+`dxgiFormat=95~97` | 16 字节/4×4 | HDR | HDR 光照贴图 | ❌ 别用 |

**结论**：给 HOI4 出压缩图，只用 **`DXT1` / `DXT5`（必要时 `ATI2`）**，且必须是 **D3D9 风格的 fourCC 头**，不能是 DX10 头。

体积参考（64×64）：未压缩 32bpp = **16512 字节**（128 + 16384）；`DXT5` = **4224 字节**（128 + 16×16×16）；`DXT1` = **2176 字节**。

## 4. 尺寸：2 的幂不是硬要求，4 的倍数才是（仅压缩图）

| 规则 | 内容 |
|---|---|
| BC 压缩 | **宽高必须是 4 的倍数**（按 4×4 块编码）。`65×67` 这种只能存**未压缩** |
| 2 的幂 | **不是硬性要求**（原版大量 100×88、156×210、65×67、60×9）。但 UI 缩放显示时非 2 的幂更容易轻微模糊 |
| 未压缩 raw32 | 任意尺寸都行（156×210 肖像就是 raw32） |
| 极端尺寸 | 单边别超 4096；字体图集是 2048×1200/页 |

## 5. mipmap：UI 一律不要，3D/地图才要

- **UI 图标不需要 mipmap**：原版 UI 图标实测 `dwMipMapCount = 0`。
- 需要 mipmap 的场景：3D 模型贴图、地图/场景贴图 —— 在 `.gfx` 的 sprite 定义里写 `generate_mip_maps = yes`（见 [gfx-sprites.md](gfx-sprites.md) §3），或导出时就带 mip 链。
- Pillow **不会**写 mipmap；需要在 DDS 里带 mip 链时用 `texconv`（`-m` 控制层数）。

## 6. Alpha 通道：谁需要、谁不需要

| 资源 | 需要 alpha？ | 说明 |
|---|---|---|
| UI 图标 | 需要 | 图标透明背景；Alpha 全 0 会显示成洋红/紫块 |
| 国策/理念/装备图标 | 需要 | 同上；原版是 32bpp ARGB |
| 领袖肖像 | 一般不需要（但通常带） | 矩形图，靠 GUI 裁切 |
| 旗帜 | 不需要（TGA 32bpp） | **旗帜是 `.tga`，不是 DDS**（82×52 / 41×26 / 10×7） |
| 字体图集 | 需要 | DXT5 的插值 alpha 存字形轮廓，所以字形边缘平滑 |
| 法线图 | 不需要 alpha | 用 `DXT5`/`ATI2` 存两个通道（Y 通道按 DirectX 约定，别反） |
| 进度条/九宫格底 | 看用途 | 半透明面板底需要真 alpha |

**DXT1 的 1-bit alpha** 只能「透/不透」，做不了柔和边缘；要软边必须 `DXT5` 或未压缩。

## 7. 游戏里常见用途（原版实测尺寸与格式）

| 用途 | 文件例（相对 `<GAME_DIR>`） | 尺寸 | 格式 |
|---|---|---|---|
| 通用 UI 图标 | `gfx/interface/observer_button.dds` | 64×64 | 未压缩 32bpp，无 mipmap（16512 B） |
| 国策图标 | `gfx/interface/goals/focus_AFG_*.dds` | 100×88 | 未压缩 32bpp |
| 理念/特质图标 | `gfx/interface/ideas/idea_GER_*.dds` | ~65×67（不统一） | 未压缩 32bpp |
| 领袖肖像 | `gfx/leaders/GER/*.dds` | 156×210 | 未压缩 32bpp（131168 B） |
| 旗帜（大/中/小） | `gfx/flags/*.tga`、`medium/`、`small/` | 82×52 / 41×26 / 10×7 | **TGA 32bpp** |
| 字体图集 | `gfx/fonts/chinese/garamond_16_1of4.dds` | 2048×1200/页 | **DXT5**（2457728 B） |
| 进度条 | `gfx/interface/construction_progressbar.dds` | 60×9 | 未压缩 32bpp（2288 B） |
| 九宫格底 | `gfx/interface/tiles/tiled_window_transparent.dds` | 95×95 | 未压缩 32bpp（36228 B） |

**关键结论：原版 UI 贴图绝大多数是 32 位未压缩 BGRA，不是压缩格式。**
所以「图标必须 DXT5」是错的——DXT5 只在优化体积时用（字体图集用了 DXT5，证明引擎也读 DXT5）。

## 8. 原版头字段实测（`observer_button.dds`，照这个抄）

| 字段 | 值 | 说明 |
|---|---|---|
| `dwSize` | 124 | 固定 |
| `dwFlags` | `0x00081007` | CAPS\|HEIGHT\|WIDTH\|PIXELFORMAT\|PITCH\|LINEARSIZE |
| `dwHeight` / `dwWidth` | 64 / 64 | |
| `dwPitchOrLinearSize` | 16384 | 原版把「**总字节数**」写这里（标准语义是每行字节数 256，两种读法引擎都接受） |
| `dwMipMapCount` | 0 | UI 贴图不需要 mipmap |
| `ddspf.dwSize` | 32 | |
| `ddspf.dwFlags` | `0x41` | RGB(0x40) \| ALPHAPIXELS(0x1) |
| `ddspf.dwFourCC` | 0 | 未压缩 |
| `ddspf.dwRGBBitCount` | 32 | |
| 掩码 | R=`0x00ff0000` G=`0x0000ff00` B=`0x000000ff` A=`0xff000000` | 内存字节序 = BGRA |
| `dwCaps` | `0x1000` | DDSCAPS_TEXTURE |

压缩图把 `dwFlags=0x4`（FOURCC）位保留、`ddspf.dwFlags=0x4`、`ddspf.dwFourCC='DXT1'/'DXT3'/'DXT5'`。

## 9. 生成管线（Pillow + `dds_helper.py`，已实测）

`$SKILL/scripts/dds_helper.py` 是零依赖（除 Pillow）生成/检查器，三个子命令：`make` / `solid` / `check`。

### 9.1 Pillow 能力实测

| 调用 | 结果 |
|---|---|
| `img.save("x.dds")`（默认） | ✅ 未压缩 32bpp，与原版 UI 图标同构（16512 字节 @64×64） |
| `img.save("x.dds", pixel_format="DXT1"/"DXT3"/"DXT5")` | ✅ 真压缩；`DXT5` 文件 4224 字节 @64×64，`fourCC='DXT5'` |
| `pixel_format="BC3"` | ⚠️ 写出 **DX10 扩展头**（`dxgiFormat=76`），HOI4 不推荐 |
| `pixel_format="BC5"` | ❌ `OSError: only RGB mode can be written as BC5` |
| mipmap | ❌ Pillow 不写 mipmap（UI 图标本来也不需要） |

### 9.2 常用命令

```bash
# 纯色占位图（画图前的临时素材）
python "$SKILL/scripts/dds_helper.py" solid out/icon_placeholder.dds --size 64 --color "#3a6ea5"

# PNG -> 未压缩 32bpp（最保险，与原版 UI 图标字节布局一致）
python "$SKILL/scripts/dds_helper.py" make my_icon.png out/GFX_NS_my_icon.dds --size 64

# 非方形图标（国策 100×88、理念 60×68、肖像 156×210）：用 --width/--height
python "$SKILL/scripts/dds_helper.py" make focus.png out/GFX_NS_focus.dds --width 100 --height 88
python "$SKILL/scripts/dds_helper.py" make portrait.png out/GFX_NS_portrait.dds --width 156 --height 210

# PNG -> DXT5（体积 1/4，与原版字体图集同格式；DXT 要求宽高都是 4 的倍数）
python "$SKILL/scripts/dds_helper.py" make my_icon.png out/GFX_NS_my_icon.dds --size 64 --format dxt5

# 检查任何 DDS（判断黑块/花屏根因）
python "$SKILL/scripts/dds_helper.py" check "<GAME_DIR>/gfx/interface/observer_button.dds"
```

`check` 输出示例（实测）：

```text
out/GFX_NS_my_icon.dds
  64x64  mips=0  dwFlags=0x81007  pitch/linear=16384
  未压缩: 32bpp  R=0x00ff0000 G=0x0000ff00 B=0x000000ff A=0xff000000
  caps=0x1000  实际字节=16512  未压缩理论字节=16512
```

### 9.3 脚本要点（自己实现时照这个写）

1. 尺寸对齐：仅 **DXT 压缩**要求 `w % 4 == 0 and h % 4 == 0`（否则花屏）；未压缩 raw32 不限。
2. **未压缩**：Pillow 没有 BGRA 编码器，用通道交换拿到 DDS 需要的字节序：
   ```python
   r, g, b, a = img.split()
   raw = Image.merge("RGBA", (b, g, r, a)).tobytes()
   ```
3. **压缩**：`img.save(tmp, format="DDS", pixel_format="DXT5")` 后**丢掉 Pillow 的 128 字节头、只取压缩块**，
   再写自己的 fourCC 头（`dwFlags=0x81007`、`dwPitchOrLinearSize` = 压缩数据总长、`dwMipMapCount=0`、`dwCaps=0x1000`）。
4. 头布局：`<7I`（magic 后 28 字节）+ 44 字节保留 + `ddspf` 32 字节 + 5 个 caps/reserved DWORD，共 128 字节。
5. 写完立刻 `check()` 打印头字段，与原版同类文件对照。

### 9.4 备选工具（Pillow 不满足时）

| 工具 | 命令要点 | 说明 |
|---|---|---|
| **texconv**（微软 DirectXTex） | `texconv -f BC3_UNORM -m 1 -srgbi -dx9 -o out in.png` | 最标准的 BC 压缩工具；**`-dx9`** 输出 DXT5 头（非 DX10）；`-m 1` 不生成 mipmap |
| NVIDIA `nvcompress` / `compressonator` | `nvcompress -bc3 in.png out.dds` | 老工具，仍有镜像 |
| GIMP + DDS 插件 / Paint.NET + DDS 插件 | 导出时选 “DXT5 / BC3, no mipmaps” | 手工改图最方便 |
| 程序化写入（纯 Python） | 只写头 + 手工填像素 | 只在没有 Pillow 时才值得 |

> 无论哪种工具，**验收标准只有一条**：把生成的文件和原版同样用途的文件对比头字段（`dds_helper.py check` 各跑一次），
> `dwFlags` / `ddspf` / 尺寸 / 字节数一致即可。

## 10. 校验管线（三层，从便宜到贵）

1. **头字段自检**：`dds_helper.py check <file>` —— 一眼看出尺寸/mips/格式/字节数，并对「非 4 倍数」「DX10 头」直接告警。
2. **与原版同类文件对照**：`check` 原版同用途文件（如 `gfx/interface/observer_button.dds`），字段应同构。
3. **进游戏看**：`-debug_mode` 下 `logs/error.log` 搜 `Failed to load texture` / `texturefile` / `sprite`。

CI 可只跑第 1+2 层（纯头解析，不需要游戏和显卡）。

## 11. 排错表（黑块 / 花屏 / 白块 / 洋红）

| 现象 | 根因 | 修法 |
|---|---|---|
| 纯黑方块 | 文件不是 DDS（把 PNG 改名）；或 DXT 尺寸非 4 的倍数；或 `texturefile` 路径错 → 引擎画占位 | 看头部 4 字节是否 `DDS `；`dds_helper.py check` |
| 花屏/条纹 | 用了 DX10 头或 BC7；或 DXT 数据长度与头部不符（手改过头） | 重新导出为标准 DXT5 或未压缩 |
| 洋红/紫块 | 缺 alpha 通道或 alpha 全 0 | 导出时保留 alpha |
| 白色方块（UI 有框没图） | 找不到 sprite：`spriteType` 名与 `icon = GFX_xxx` 不一致 | `grep -r 'name = "GFX_xxx"' interface/*.gfx` |
| 图标显示成别的图 | sprite 名重复定义，后者覆盖前者（加载顺序 mod 在后 → mod 赢） | 加 `NS_` 前缀避免撞名 |
| TGA 当 DDS 用 | `texturefile` 后缀与真实格式不符 | 旗帜就该是 `.tga`，图标就该是 `.dds` |
| 模型贴图发黑 / 塑料感 | 法线不是切线空间、Y 通道反；或 diffuse 路径错 | 见 [models-3d.md](models-3d.md) §4 |
| 图标缩放后糊 | 非 2 的幂又被缩放；或缺 mipmap（大图缩小场景） | 用原版同款尺寸；地图/3D 贴图开 `generate_mip_maps` |

## 12. 自检清单

- [ ] 文件头 4 字节是 `DDS `（不是改名的 PNG）。
- [ ] 尺寸与用途匹配（见 §7 / [portraits-flags.md](portraits-flags.md) 尺寸表）；压缩图宽高是 4 的倍数。
- [ ] 格式是 `DXT1`/`DXT5`（或未压缩 32bpp）；没有 DX10 头、没有 BC7/BC6H。
- [ ] UI 贴图 `dwMipMapCount = 0`；3D/地图贴图按需带 mip 或 `generate_mip_maps = yes`。
- [ ] 需要透明的地方 alpha 不是全 0，且边缘不是硬切（DXT1 只有 1-bit alpha）。
- [ ] 在 `interface/*.gfx` 注册了同名 sprite（否则贴图对但界面不显示，见 [gfx-sprites.md](gfx-sprites.md)）。
- [ ] `dds_helper.py check` 与原版同类文件头字段一致；`logs/error.log` 无贴图报错。

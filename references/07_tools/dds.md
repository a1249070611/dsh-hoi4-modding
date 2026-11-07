---
title: "dds 与 icon：DDS 生成 / 头检查，PNG 转科技图标"
domain: 07_tools
scope: 生成或检查 HOI4 用的 DDS，把 PNG 批量转成带边距的科技图标 DDS（含卡片预览）
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py dds make|solid|check
  - tools/cli.py icon import
  - tools/dds_helper.py / tech_icon_import.py
---

# `dds` 与 `icon`：贴图生成与检查

HOI4 只认真实 DDS（改了扩展名的 PNG 会花屏/黑块）。这两个命令覆盖「生成、检查、把美术给的 PNG 转成游戏图标」。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## `dds check`：头检查

```bash
python tools/cli.py dds check gfx/interface/techtree/my_icon.dds
python tools/cli.py dds check <目录>          # 目录：逐个文件
python tools/cli.py dds check <file> --json
```

打印：尺寸、mipmap 数、flags、pitch、压缩格式（DXT1/3/5、BC 系列、raw32）、文件实际字节数。会提示：

- 头不合法/截断（文件 <148 字节）→ `env.missing`（旧工具包装层的错误码）；
- 宽高不是 4 的倍数；
- `raw32` 与 DXT 的 pitch/字节数不匹配。

退出码：`0` 正常、`1` 有问题、`2` 文件不存在/参数错。

## `dds make`：PNG/JPG 转 DDS

```bash
python tools/cli.py dds make <src.png> <out.dds> --format raw32
python tools/cli.py dds make <src.png> <out.dds> --format dxt5 --size 128
python tools/cli.py dds make <src.png> <out.dds> --width 173 --height 77 --no-resize
```

- `--format`：`raw32`（默认，无损、体积大、图标最稳）、`dxt5`、`dxt1`、`dxt3`；
- `--size N` 等比缩放到 N×N；`--width/--height` 指定尺寸；`--no-resize` 保持原尺寸；
- 需要 Pillow（`doctor` 会报是否可用）；DXT 格式要求宽高是 4 的倍数，否则报错退出。

## `dds solid`：纯色占位

```bash
python tools/cli.py dds solid <out.dds> --color "#3a6ea5" --alpha 255
```

生成 raw32 纯色 DDS，用于补 `missing_*` 占位或做背景。

## `icon import`：PNG → 科技图标 DDS

```bash
python tools/cli.py icon import <输入.png或目录> <输出目录>
python tools/cli.py icon import icons/ out/ --mode auto --width 173 --height 77 --margin-left 20 --margin-right 4
python tools/cli.py icon import icons/ out/ --card-preview --card-bg "<game>/gfx/interface/techtree/technology_available_item_bg.dds"
python tools/cli.py icon import icons/ out/ --alias alias.json
```

- 背景处理 `--mode`：`auto`（默认，按 RGBA/边框判断）、`alpha`、`white`、`checker`、`none`；
- 尺寸：默认内容 173×77，左边距 20 / 右边距 4 / 上下 2，按 alpha bbox 裁剪后等比缩放居中；
- `--card-preview`：同时合成 183×84 的可用/不可用卡片预览（默认背景取原版 `technology_available_item_bg.dds`）；
- `--alias alias.json`：文件名（或中文名）→ 科技 id 的映射，输出按科技 id 命名，避免 `1.png` 这种名字；
- 输出 `raw32` DDS（与 `dds make --format raw32` 同一实现，不再起子进程）。

## 图标规格速查

| 用途 | 尺寸 | 说明 |
|---|---|---|
| 科技小图标（small_item） | 内容 173×77 内，模板画布 72×72 的建议换 `tech_doctrine_*_item_bg.dds` | `tech sprites` 会查 |
| 科技大图标 | 依页面模板 | 看 `countrytechtreeview.gui` 的 `techtree_*_item` |
| 理念/国策图标 | 依模板 | 用 `lint` 的 `gfx.missing_idea_picture` 兜底 |

## 常见错误

- **花屏/黑块**：PNG 改扩展名、尺寸非 4 倍数还用了 DXT。
- **图标偏小/被裁**：`--margin-*` 与模板尺寸不匹配；先用 `--card-preview` 看合成效果。
- **透明背景变黑**：源图没有 alpha，`--mode auto` 判成 `white`/`checker`；指定 `--mode alpha` 或先抠图。

## 已知限制

- 不做 BC7/ASTC 编码（Pillow 不支持），需要这些格式用外部工具。
- `icon import` 会同时在输出目录留一份同名 `.png`（便于核对），发布前可删。
- 所有输出走 UTF-8 路径；中文目录可用，但游戏内引用路径建议全 ASCII。

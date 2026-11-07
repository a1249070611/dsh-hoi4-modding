---
title: "gfx audit：sprite 与 DDS 贴图"
domain: 07_tools
scope: .gfx 里的 sprite 是否能闭合到真实 .dds，DDS 头是否合法，有没有未使用 sprite
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py gfx audit
  - tools/gfx_audit.py
  - tools/_dds.py
---

# `gfx audit`：sprite 与 DDS 贴图

扫 `interface/**/*.gfx` 的 sprite 定义，检查 `texturefile` 指向的贴图是否存在、DDS 头是否合法，以及 sprite 有没有人引用。

```bash
python tools/cli.py gfx audit <mod>                # 含未使用 sprite 检查
python tools/cli.py gfx audit <mod> --no-unused    # 只看闭合/合法性（大 Mod 更快、更安静）
python tools/cli.py gfx audit <mod> --json=gfx.json
```

退出码：`0` 无问题、`1` 有 error/warning、`2` 找不到 Mod、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 扫什么

- sprite 块：`spritetype`、`frameAnimatedSpriteType`、`corneredTileSpriteType`、`textSpritetype`（块名大小写不敏感，用词边界匹配避免 `frameAnimatedSpriteType` 被当成 `spriteType` 收两次）。
- 属性：`name`、`texturefile`（大小写不敏感，`gfx//interface//x.dds` 这种双斜杠会先折叠）。
- 贴图解析顺序：Mod 根目录 → 游戏根目录（含 `dlc/`、`integrated_dlc/` 的 `gfx/` 逻辑路径）。
- DDS 头：magic、128 字节头、宽高、mipmap、FourCC（DXT1/3/5、BC 系列、raw32）、文件实际大小。

## rule ID

| rule | 级别 | 含义 / 怎么修 |
|---|---|---|
| `gfx.texture_missing` | error | `texturefile` 指向的文件不存在。注意大小写与反斜杠 |
| `gfx.sprite_no_texture` | error | sprite 没有 `texturefile`（`spritetype` 必须有） |
| `gfx.dds_invalid` | error | 头不合法/文件截断/尺寸为 0。重新导出 |
| `gfx.duplicate_sprite` | warning | 同名 sprite 定义多次，后者覆盖前者 |
| `gfx.frames_bad` | warning | `noOfFrames` 与贴图宽高不匹配（横向帧） |
| `gfx.dds_not_multiple_4` | warning | 宽或高不是 4 的倍数，压缩格式可能花屏；`raw32` 一般可接受 |
| `gfx.dds_suspicious` | warning | 尺寸/字节数与预期差太多（常见于把 PNG 改名成 DDS） |
| `gfx.non_dds_texture` | info | 用了 `.tga`/`.png`。能读，但不符合发布习惯 |
| `gfx.unused_sprite` | info | 没有任何脚本/GUI 引用 `GFX_<name>`（社区 Mod 里很多，别全当 bug） |
| `gfx.no_gfx` | info | Mod 没有 interface/*.gfx |

## 典型修法

- **科技/理念图标空白**：`gfx.texture_missing` → 检查 `texturefile` 是否写成 `gfx/interface/...`（应为相对路径，不带 `gfx/`）和扩展名大小写。
- **贴图花屏/黑块**：`gfx.dds_invalid` / `gfx.dds_not_multiple_4` → 重新按游戏尺寸导出（图标 173×77 之类可以保留，属已知可接受）。
- **sprite 覆盖**：`gfx.duplicate_sprite` → 换名字或删重复块（Mod 覆盖原版是允许的，但同 Mod 内重名通常是复制粘贴遗留）。

## `--json` 关键字段

```json
{"ok": true, "exit_code": 0, "command": "gfx audit",
 "problems": [{"code": "gfx.dds_not_multiple_4", "severity": "warning",
               "path": "gfx/interface/techtree/x.dds", "line": 12, "message": "..."}],
 "summary": {"mod": "...", "gfx_files": 3, "sprites": 396, "textures_checked": 396,
             "texture_from_game": 18, "unused": 0, "dds_files": 343,
             "omitted_by_code": {}, "omitted_total": 0}}
```

## 已知限制

- 只扫 `interface/**/*.gfx`，`gfx/entities/*.gfx`（3D 模型声明）不在此命令范围。
- 不做像素级校验（内容是否全透明/颜色错需要在游戏里看）。
- `--no-unused` 关闭的只是 info 级未使用统计，不影响 error/warning。
- 大 Mod（5 万 sprite）会有几千条 warning；按 `summary.texture_from_game` 与 code 分布判断，不要逐条读。

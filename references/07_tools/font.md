---
title: "font：中文字体映射体检"
domain: 07_tools
scope: 找出「脚本用了某个 font 名，但这个名字没有映射到中文分片」的情况
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py font audit / font list
  - tools/font_audit.py
  - 实测：gfx/fonts/chinese/*.fnt（四页各 7677/7813/8002/7041 个字形）
---

# `font`：中文字体映射体检

中文显示成方框/问号，**根因不是 `.fnt` 没有汉字字形**（原版中文分片每页有 7000+ 个字形），而是脚本里用的字体名没被映射到中文分片。这个命令把「用了但没映射」的字体名找出来。

```bash
python tools/cli.py font audit <mod>              # 扫 Mod 里所有 font = "..." 引用
python tools/cli.py font audit <mod> --list-supported   # 顺便列出受支持的字体名
python tools/cli.py font list                     # 只列受支持的字体名（含来源）
```

退出码：`0` 全部受支持、`1` 有不支持的字体名、`2` 找不到 Mod、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 受支持的判定

1. `game/interface/*.gfx` 里所有 `bitmapfont_override = { name = ... }` 的 `name`（原版英文 UI 常用 `core.gfx`、`chatfonts.gfx`、`core_chinese.gfx`、`core_korean.gfx`、`load_screen_font.gfx`，共 40+ 个名字）；
2. 4 个标准 UI 名字：`standard_font`、`chat_input_font`、`loadscreen_header`、`loadscreen_tip`。

这个集合与 `--game` 相关：换游戏版本/语言包后重新跑一次。找不到游戏时回退到内置名单，并在输出里注明来源。

## 扫什么

`mod/interface/**/*.gui`、`mod/gfx/**/*.gui` 里的 `font = "名字"`（`FONT_RE`）。每个命中记 文件:行:字体名。

## 输出

```text
# hist_tech_trees
字体来源：chatfonts.gfx + core.gfx + core_chinese.gfx + core_korean.gfx + load_screen_font.gfx（另含 4 个标准 UI 字体名），共 41 个名字
引用 458 处，字体名 14 个，不支持 0 个
PASS
```

有问题时每个不支持的字体名一条 `font.unsupported`：

```json
{"ok": false, "exit_code": 1, "command": "font audit",
 "problems": [{"code": "font.unsupported", "severity": "error",
               "message": "字体 `hoi_14mbs` 没有被映射到中文分片（gfx/fonts/chinese/*.fnt 里有汉字字形，但名字没接上）"}],
 "summary": {"references": 458, "fonts": 14, "supported": 41, "unsupported": 1,
             "source": "chatfonts.gfx + core.gfx + ..."}}
```

## 怎么修

- 把该字体名加进 `interface/*.gfx` 的 `bitmapfont_override`，`fontname`/`path` 指向中文分片（`gfx/fonts/chinese/`）。
- 或者把脚本里的 `font = "xxx"` 换成已支持的等价字体（正文常用 `standard_font`，聊天用 `chat_input_font`）。
- 只改了 `.fnt` 字形但没改映射，游戏里仍是方框——这是最常见的误判，先看本命令。

## 已知限制

- 只扫 `.gui`，国策/事件的 `.txt` 里不写 font，不需要扫。
- 不校验 `.fnt` 内容与字形覆盖（只信原版分片存在）。
- 没有游戏目录时用内置名单，可能把原版新增字体误报为不支持；跑一次 `--game` 即可消除。

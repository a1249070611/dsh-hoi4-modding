---
name: kiant-hoi4-localisation
description: HOI4 本地化文件规则：UTF-8 BOM、语言头、键命名、颜色码与图标、动态文本、多语言、以及"游戏里显示键名/乱码"的完整排查路径。
---

# 本地化

## 格式是死的

```
l_english:
 GER_autobahn:0 "帝国高速公路"
 GER_autobahn_desc:0 "我们 rebuild 了国家的动脉。"
```

三条硬规则：

1. **文件必须 UTF-8 with BOM**。没有 BOM，整个文件被引擎无视，界面上显示 `GER_autobahn` 这样的键名。
2. 第一行必须是语言头 `l_english:`。中文是 `l_simp_chinese:`。
3. 每行是 ` KEY:0 "文本"`。冒号后的数字是版本号，写 `0` 即可；写成 `KEY:1` 在某些场景下会让旧存档继续用旧文本。

行首那个空格不是强制的，但社区惯例保留——某些旧版解析器对行首无空格会挑剔。

## 目录与命名

```
localisation/
├── english/
│   ├── mymod_l_english.yml
│   └── mymod_events_l_english.yml
└── simp_chinese/
    ├── mymod_l_simp_chinese.yml
    └── mymod_events_l_simp_chinese.yml
```

文件名建议 `<mod>_<模块>_l_<语言>.yml`。Paradox 会加载目录下所有 `.yml`，文件名本身不重要，但统一命名能让加载顺序可预测（**后加载的覆盖先加载的**，同目录按文件名字母序）。

## 键命名约定

| 内容 | 键 |
|---|---|
| 国策 | `<focus_id>` 和 `<focus_id>_desc` |
| 国家精神 | `<idea_id>` 和 `<idea_id>_desc` |
| 决议 | `<decision_id>` 和 `<decision_id>_desc` |
| 决议分类 | `<category_id>` 和 `<category_id>_desc` |
| 事件 | `<namespace>.<n>.t` / `.d` / `.a` / `.b` |
| 角色 | `<character_id>_name` |

键名**大小写敏感**，且全局唯一。两个 mod 用同一个键就是互相覆盖——所以一律加 TAG 前缀。

## 富文本

```
 GER_autobahn_desc:0 "§Y帝国高速公路§! 让我们的工业产能 §G+5%§!。"
```

- 颜色：`§Y`…`§!`，`§Y` 黄、`§G` 绿、`§R` 红、`§B` 蓝、`§W` 白、`§H` 高亮
- 换行：`\n`
- 图标：`£political_power` 插入政治点数图标，图标名对应 `gfx/interface/icons` 里的 sprite
- 变量：`[?GER_progress]` 取出变量值；`[Root.GetName]` 取作用域名字

```
 GER_report_desc:0 "我们在 [Root.GetName] 的进度是 [?GER_progress|0]%。"
```

`|0` 是小数位控制。

## 动态本地化（1.11+）

在 `common/scripted_localisation/` 里定义，可以随游戏状态变化：

```
defined_text = {
	name = GetOurLeaderTitle
	text = {
		trigger = { has_government = fascism }
		localisation_key = leader_title_fuhrer
	}
	text = {
		trigger = { has_government = democratic }
		localisation_key = leader_title_president
	}
}
```

调用处写 `[GetOurLeaderTitle]`。

## 排查：界面显示的是键名

按这个顺序查，命中率从高到低：

1. **没有 BOM** —— 用 `kiant_hoi4_scan_localisation`，它会直接报"缺少 UTF-8 BOM"。
2. **没有语言头** —— 第一行必须是 `l_english:`，不能是注释、不能是空行。
3. **游戏语言不是 english** —— 你在 `localisation/english/` 写了文本，但游戏跑的是简体中文。要么改游戏语言，要么同时提供 `l_simp_chinese:`。
4. **键名拼错或大小写不符** —— `GER_autobahn` 与 `GER_Autobahn` 是两个键。
5. **引号没闭合** —— 一行里少一个 `"`，该行及其后续都可能失效。
6. **文件不在 `localisation/<语言>/` 下** —— 放在 `localisation/` 根目录不生效。

## 排查：中文乱码

中文 Windows 下编辑器（记事本、旧版 VS Code 默认）常把文件存成 GBK/GB18030。Paradox 只认 UTF-8。

- 用 `kiant_hoi4_fix_localisation` 先 `dry_run=true` 看报告，确认有 `converted_from: gb18030` 再执行
- 手动方案：VS Code → 右下角编码 → "通过编码保存" → UTF-8 with BOM

## 中文模组实践

- 只写 `l_simp_chinese:` 时，把游戏语言切到简体中文；否则英文界面仍显示键名
- 稳妥做法：`english` 和 `simp_chinese` 两个目录都提供，英文目录放英文文本
- 中文不影响脚本逻辑，脚本文件（`.txt`）用 UTF-8 无 BOM 更安全（有 BOM 的 `.txt` 在部分版本会让首行解析失败）

## 校验

任何本地化改动后：

```
kiant_hoi4_validate_mod     # 会列出所有缺失的键，精确到引用位置
kiant_hoi4_scan_localisation # 只看编码/格式层问题
```

缺失键的报告会给到具体是哪个国策/事件缺哪个键，直接照补即可。

## 做汉化子模组（覆盖别人/原版的内容）

先判断目标文本在哪一层，别一上来就覆盖文件（2026-11 实测六汉化 mod 的四层
工作流全文见 `references/05_presentation/localisation.md` §13）：

1. **纯 loc**（90% 文本）：`simp_chinese/` 补键即可，英文缺键自动回落；
   覆盖个别键放 `simp_chinese/replace/`。
2. **common 硬编码字符串**（机构名/AI 条件/编制名/角色名）：必须同路径覆盖
   common 文件，diff 上游只改字符串——见 EB-023。
3. **字体**：能不自带就不自带；自带时用 `bitmapfont_override + languages` 条件覆盖。
4. **texticon**（文字烤进贴图）：逐张替换 DDS，成本最高，能推上游改就推。

收尾：descriptor 写 `tags = { "Translation" }` + 注明适配的上游版本号；
`kiant_hoi4_validate_mod` 回归。

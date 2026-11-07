---
title: 表现层知识库（GUI / GFX / DDS / 3D 模型 / 本地化 / 字体 / 音频）
domain: 05_presentation
scope: interface
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 05 · 表现层（Presentation）

一句话定位：**把游戏内容“画出来、写出来、放出声”的一切**——`interface/*.gui` 搭界面、`interface/*.gfx` 注册贴图、`common/scripted_guis` 让界面能点、`localisation/*.yml` 出文字、`gfx/fonts` 出字形、`sound/`+`music/` 出声音。

> 本目录全部结论基于本机 **1.19.x “Operation Postern”** 的真实文件（路径均相对游戏根目录 `<GAME_DIR>`）。
> 规则：游戏根目录只读；本文所有示例写进 **mod 目录**同名路径下（mod 内 `interface/`、`gfx/`、`localisation/`…）。

---

## 文档清单

| 文档 | 一句话摘要 | 关键产出 |
|---|---|---|
| [gui-basics.md](gui-basics.md) | `interface/*.gui` 语法、控件、定位/朝向/尺寸、完整可加载面板 | 一个 4 文件即可显示的自定义面板骨架 |
| [scripted-gui.md](scripted-gui.md) | `common/scripted_guis` 定义、effects/triggers/properties/dynamic_lists、刷新与性能、挂载点 | 「让面板真的出现并能点」的完整清单 |
| [gfx-sprites.md](gfx-sprites.md) | `interface/*.gfx`：spriteTypes、动画/圆角/进度条/遮罩旗帜、行内文本图标 | 可直接抄的 sprite 定义模板 |
| [dds.md](dds.md) | **DDS 贴图权威页**：BC1/3/5、尺寸与 2 的幂、mipmap、Alpha、用途尺寸表、生成与校验管线、黑块/花屏排错 | `dds_helper.py` 全用法（raw32/DXT5 已实测）+ 头字段对照表 |
| [models-3d.md](models-3d.md) | 3D 接入四层链（graphic_db → entity → pdxmesh → mesh/贴图）、locator、三条路线、GitHub 工具链盘点 | 可复用原版实体表 + 逐层排错链 |
| [portraits-flags.md](portraits-flags.md) | 肖像与旗帜目录、命名、尺寸、意识形态旗、角色引用 | 尺寸表 + `maskedShieldType` 旗帜机制 |
| [localisation.md](localisation.md) | yml 规范、`§颜色`、`£图标`、`$var$`、`[ROOT.GetName]`、formatter/loc objects | 可直接复制的 yml 模板 |
| [fonts-cjk.md](fonts-cjk.md) | 中文字体注册（`bitmapfont_override`）、字形覆盖、方框/乱码根因 | 本机实测的「哪些字体名没中文」清单 |
| [audio.md](audio.md) | `sound/*.asset`、`music/music.asset`、`soundeffect`/`category`、OGG/WAV 规范 | 新增音效/音乐的最小文件集 |
| [advanced-interface.md](advanced-interface.md) | map_modes、alerts、scripted localisation、文本图标与界面联动 | `scripted_map_modes` 全文要点 |

工具（均在 `$SKILL/scripts/`）：`dds_helper.py`（生成/检查 HOI4 DDS，用法见 [dds.md](dds.md)）、`font_audit.py`（字体中文分片体检，见 [fonts-cjk.md](fonts-cjk.md)）、`hoi4_lint.py`（语法/本地化静态校验）。

---

## 五条最重要的结论

1. **GUI 分两层，缺一层就不显示。** `interface/*.gui` 只描述“长什么样”（元素树，必须放在 `guiTypes = { }` 里），`common/scripted_guis/*.txt` 描述“谁、在哪个上下文里、显示哪个窗口、按钮点了执行什么”。**没有任何原版 `.gui` 能独立弹出来**：全部通过 scripted GUI 挂到决策分类（`context_type = decision_category` + 分类里写 `scripted_gui = xxx`）或硬编码视图上。
2. **2D 贴图定义全部在 `interface/*.gfx`，不在 `gfx/`。** 实测：原版 `interface/` 下 145 个 `.gfx`（23521 个 `spriteType`），`gfx/interface/` 下 **0 个** `.gfx`。`gfx/` 下的 36 个 `.gfx` 全是 3D 模型/粒子（`gfx/entities`、`gfx/models`、`gfx/particles`）。把 sprite 定义塞进 `gfx/interface/xxx.gfx` 是社区习惯，但原版没有先例——照原版放 `interface/` 最稳。
3. **原版 UI 图标几乎都是未压缩 32 位 DDS，不是 DXT5**（格式细节与生成管线见 [dds.md](dds.md)）。 实测 `gfx/interface/observer_button.dds`：64×64、`dwFlags=0x00081007`、`dwPitchOrLinearSize=16384`（总字节）、`pf_flags=0x41`、ARGB 掩码、无 mipmap、文件 16512 字节。**所以用 Pillow 直接存 DDS 就能被接受**，不必装 texconv；要体积再选 DXT5（原版字体图集就是 DXT5，引擎肯定读）。
4. **中文“方框/乱码”九成是字体名选错或 yml 编码错。** 中文界面下只有 `interface/core_chinese.gfx` 里 41 个 `bitmapfont_override`（`languages = { "l_simp_chinese" }`）列出的字体名带汉字。**在 GUI 里写 `font = "garamond_12"`/`hoi_20`/`standard_18`/`vic_18_grey` 这类没有中文 override 的字体 → 汉字必然方框/空白。** 另一半原因是 yml 不是“UTF-8 with BOM + 文件名含 `_l_simp_chinese`”。
5. **本地化不是“翻译文件”，是一个带作用域的表达式语言。** `[ROOT.GetName]` / `[?TAG.var]` / `[(Character?.GetName:'FALLBACK)]` 是**上下文求值**，只在被支持的上下文里生效（聚焦、事件、决议、自定义 effect/trigger tooltip、scripted GUI 面板等）；`pdx_tooltip` 里的 `$var$` 不会展开。`formatter|token`（如 `idea_name|xxx`）是另一套静态取词机制。

---

## 该领域最常见的坑（先看这 10 条）

| # | 现象 | 根因 | 去哪修 |
|---|---|---|---|
| 1 | 面板完全不出现 | `.gui` 里的 `containerWindowType` 名字 ≠ scripted_gui 的 `window_name`；或决策分类没写 `scripted_gui = ...`；或分类 `visible` 为假 | [scripted-gui.md](scripted-gui.md) |
| 2 | 面板出现但错位 | `position` 相对父容器/`orientation` 方向，不是屏幕绝对坐标 | [gui-basics.md](gui-basics.md) |
| 3 | 图标黑块 | DDS 尺寸不是 4 的倍数（DXT）；或 `texturefile` 路径大小写/斜杠错；或 sprite 名与 `GFX_` 前缀不匹配 | [dds.md](dds.md)、[gfx-sprites.md](gfx-sprites.md) |
| 4 | 图标花屏/条纹 | DDS 用了 DX10 扩展头或 BC7/BC6H；或把 TGA 当 DDS 引用 | [dds.md](dds.md) |
| 4b | 3D 模型空白/全黑/炮管不转 | `graphic_db` 的 entity / `.gfx` 的 pdxmesh / `.mesh` 文件断了任一层；或缺 locator、贴图路径错 | [models-3d.md](models-3d.md) |
| 5 | 汉字显示为 `?` 或方框 | GUI 用了没有 `l_simp_chinese` override 的字体名；或字形确实缺字 | [fonts-cjk.md](fonts-cjk.md) |
| 6 | 文本显示为 key 名（`HHO_focus_x`） | yml 没有 BOM、不是 UTF-8、文件名不含 `_l_simp_chinese`、或 key 写错/大小写不符 | [localisation.md](localisation.md) |
| 7 | 颜色代码溢出到后文 | 少写 `§!` 结尾；或 `§` 后面是空 | [localisation.md](localisation.md) |
| 8 | `£icon` 显示成文字 | 没有同名 `spriteType`（`£name` ↔ `GFX_name`）；多帧图标缺 `legacy_lazy_load = no` | [localisation.md](localisation.md) |
| 9 | 按钮点了没反应 | 按钮 `name` 与 scripted_gui 的 `effects` 键不匹配（键名 = `<元素名>_click`） | [scripted-gui.md](scripted-gui.md) |
| 10 | 音效不响 | `.asset` 里 `sound` 名与 `soundeffect.sounds` 引用名不一致；或 OGG/WAV 采样率/声道异常；或 `soundeffect` 没进 `category.asset` 的播放分组 | [audio.md](audio.md) |

---

## 文件类型速查：什么扩展名放哪、谁读

| 扩展名 | 放哪 | 谁读 | 关键规则 |
|---|---|---|---|
| `.gui` | `interface/` | 引擎 GUI 系统（启动时） | 最外层 `guiTypes = { }`；本身不会自己出现 |
| `.gfx`（2D） | `interface/` | 贴图系统 | 最外层 `spriteTypes = { }`；sprite 名以 `GFX_` 开头 |
| `.gfx`（3D） | `gfx/entities/`、`gfx/models/` | 模型系统 | 与 2D 完全不同的管线，别混 |
| `.dds` | `gfx/interface/`、`gfx/leaders/`、`gfx/texticons/`、`gfx/fonts/`、`gfx/models/` | 贴图加载器 | 128 字节头；UI 用 32bpp 未压缩；DXT 尺寸 4 的倍数（见 [dds.md](dds.md)） |
| `.tga` | `gfx/flags/`、`gfx/fonts/` | 贴图加载器 | **旗帜必须是 TGA**（82×52） |
| `.yml` | `localisation/<语言>/` | 本地化加载器 | UTF-8 **with BOM**；文件名 `_l_<语言>.yml`；首行 `l_<语言>:` |
| `.fnt` + `.dds/.tga` | `gfx/fonts/`（中文在 `gfx/fonts/chinese/`） | 字体系统 | BMFont 文本格式；4 页拆分 |
| `.asset` | `sound/`、`music/` | 音频系统 | 外层键 `sound` / `soundeffect` / `category` / `falloff` / `music` |
| `.wav` | `sound/` 子目录 | 音频系统 | 44.1 kHz 16-bit PCM（音效） |
| `.ogg` | `music/` | 音频系统 | Vorbis 44.1 kHz（音乐） |
| `.txt` | `common/scripted_guis/`、`common/scripted_localisation/`、`common/map_modes/`、`common/decisions/`、`common/alerts.txt` | 脚本系统 | 与界面/文字直接相关的那几类都在这 |

## 表现层加载链（一个面板从文件到屏幕）

```text
[interface/NS_dashboard.gui]  ─┐ 元素树（长什么样）
[interface/NS_icons.gfx]      ─┼→ 贴图查找（sprite 名 → 文件）
[gfx/interface/NS/*.dds]      ─┘
                              │
[common/scripted_guis/*.txt]  → 上下文 + 显示哪个 window_name + 按钮绑定
                              │
[common/decisions/categories] → scripted_gui = <gui 名>（挂载点）
                              │
[localisation/simp_chinese/*] → 所有 text/pdx_tooltip 的字面文本
[gfx/fonts/chinese/*]         → 汉字字形
                              ↓
                          屏幕上的面板
```

**排查顺序就按这条链走**：面板不显示 → 挂载链；显示但空白 → sprite；有字但方框 → 字体；有字但显示 key → 本地化。

## 常用尺寸速查（本机实测，别凭记忆）

| 资源 | 尺寸 | 格式 |
|---|---|---|
| 旗帜（大/中/小） | 82×52 / 41×26 / 10×7 | TGA 32bpp |
| 领袖肖像 | 156×210 | DDS 32bpp |
| 国策图标 | 100×88 | DDS 32bpp |
| 理念/特质/顾问图标 | ~65×67（不统一） | DDS 32bpp |
| 决议分类图标 | ~40×51 | DDS 32bpp |
| 决议图标 | ~32×33 | DDS 32bpp |
| 通用 UI 图标 | 64×64（也有 33×33、60×9 等） | DDS 32bpp |
| 字体图集 | 2048×1200/页（中文 4 页，地图字体 11 页） | DDS DXT5 |

## 推荐上手顺序

1. 先做**本地化**（[localisation.md](localisation.md)）：一个 yml + 一个 key，确认中文能显示。
2. 再做**图标**（[dds.md](dds.md) → [gfx-sprites.md](gfx-sprites.md)）：`dds_helper.py` 生成 64×64 DDS + 在 `interface/*.gfx` 注册，用原版已有的 GUI 位置引用它。
3. 然后做**面板**（[gui-basics.md](gui-basics.md) → [scripted-gui.md](scripted-gui.md)）：走 `decision_category` 挂载，四文件齐全。
4. 需要旗帜/肖像时看 [portraits-flags.md](portraits-flags.md)。
5. 中文字体一旦出问题直接跳 [fonts-cjk.md](fonts-cjk.md)。
6. 需要音效/音乐看 [audio.md](audio.md)；需要地图模式/告警看 [advanced-interface.md](advanced-interface.md)。
7. 要换 3D 模型（坦克/飞机/单位外观）看 [models-3d.md](models-3d.md)。

## 验收方法（本目录内容的验证手段）

| 验证 | 方法 |
|---|---|
| 语法 | 花括号平衡；`python $SKILL/scripts/hoi4_lint.py <PROJECT_DIR>` 跑一遍 |
| sprite 引用 | 对每个 `icon = GFX_xxx` / `spriteType = "GFX_xxx"` 执行 `grep -r 'name = "GFX_xxx"' interface/` |
| 本地化 | 控制台 `loc_check` 系列；肉眼确认中文文件与英文文件 key 一一对应 |
| 贴图 | `python $SKILL/scripts/dds_helper.py check <file>` 与同用途原版文件对比头字段（[dds.md](dds.md) §10） |
| 字体 | `python $SKILL/scripts/font_audit.py <PROJECT_DIR>`（退出码 0）；对照 [fonts-cjk.md](fonts-cjk.md) §4 名单 |
| 3D | 设计器/生产界面能看到模型；`logs/error.log` 无 entity/pdxmesh/贴图报错（[models-3d.md](models-3d.md) §12） |
| 运行时 | `hoi4.exe -gdpr-compliant -debug_mode` → `logs/error.log` 搜 `sprite` / `localisation` / `sound` / `Failed to load` |

## 术语中英对照（读原版文件时会遇到）

| 英文 | 中文 | 出现位置 |
|---|---|---|
| `guiTypes` | GUI 元素树根节点 | 每个 `.gui` 文件 |
| `containerWindowType` | 容器（无边框面板） | `.gui` |
| `windowType` | 窗口（可拖拽/全屏） | `.gui` |
| `iconType` | 图标元素 | `.gui` |
| `buttonType` / `guiButtonType` | 按钮 | `.gui` |
| `instantTextBoxType` | 文本元素 | `.gui` |
| `positionType` | 命名位置（供引擎塞动态元素） | `.gui` |
| `orientation` | 锚点/对齐基准 | `.gui` |
| `spriteTypes` | 贴图定义根节点 | 每个 `.gfx` |
| `spriteType` | 贴图定义 | `.gfx` |
| `frameAnimatedSpriteType` | 逐帧动画贴图 | `.gfx` |
| `corneredTileSpriteType` | 九宫格可拉伸贴图 | `.gfx` |
| `progressbartype` | 进度条贴图 | `.gfx` |
| `maskedShieldType` | 遮罩旗帜/盾徽 | `.gfx` |
| `legacy_lazy_load` | 是否延迟加载（`no`=立即） | `.gfx` |
| `scripted_gui` | 脚本化 GUI 定义块 | `common/scripted_guis` |
| `context_type` | 上下文类型（决定 scope 与挂载） | `common/scripted_guis` |
| `window_name` | 绑定的容器名 | `common/scripted_guis` |
| `properties` / `dynamic_lists` / `dirty` | 动态属性 / 动态列表 / 刷新触发变量 | `common/scripted_guis` |
| `defined_text` | 脚本化本地化定义块 | `common/scripted_localisation` |
| `bitmapfont` / `bitmapfont_override` | 位图字体定义 / 按语言覆盖 | `interface/*.gfx` |
| `scripted_map_modes` | 脚本化地图模式 | `common/map_modes` |
| `sound` / `soundeffect` / `category` | 声音 / 音效 / 播放分组 | `sound/*.asset` |

## 与其他知识域的边界

- 脚本执行模型（scope / effect / trigger / 变量）：见 [../01_script/](../01_script/)。
- 国策/事件/决议/理念/角色等内容字段：见 [../02_content/](../02_content/)——本目录只讲“它们怎么被画出来/写出来”。
- mod 打包、`descriptor.mod`、加载顺序与校验和：见 [../06_workflow/](../06_workflow/)。

---

## 自检清单（写完任何表现层内容后逐条过）

- [ ] 每个 `spriteType` 里引用的 `texturefile` 真实存在，扩展名是 `.dds`/`.tga`，路径用 `/`。
- [ ] 每个 `icon = GFX_xxx` / `picture = xxx` 都能在 `interface/*.gfx` 里 grep 到 `name = "GFX_xxx"`。
- [ ] `.gui` 花括号平衡；`guiTypes = { }` 在最外层；元素 `name` 唯一。
- [ ] `window_name` / `parent_window_token` / `scripted_gui` 三处名字互相对得上。
- [ ] 所有 yml：UTF-8 **with BOM**，首行 `l_simp_chinese:`，键以单空格缩进，值必须同一行（用 `\n`）。
- [ ] 每个新增本地化 key 在中文文件里都有一份（否则中文界面显示 key 名）。
- [ ] GUI 里的 `font = "..."` 属于中文 override 名单（否则汉字不显示）。
- [ ] 图片尺寸与用途匹配（见 [portraits-flags.md](portraits-flags.md) 的尺寸表），DXT 尺寸是 4 的倍数。
- [ ] `-debug_mode` 下看 `logs/error.log`：搜 `Failed to load` / `Could not find` / `sprite` / `localisation`。

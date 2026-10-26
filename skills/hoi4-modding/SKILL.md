---
name: hoi4-modding
description: 《钢铁雄心4》(Hearts of Iron IV, HOI4) 1.19.3 Mod 开发全流程技能：读游戏文件、新建 Mod、写国策/事件/决议/理念/角色/科技/州/MIO/特殊项目/scripted GUI、本地化与 DDS 图标、静态校验、安装启用、按 error.log 排错、发布创意工坊。Use whenever the user asks to create, edit, fix, validate, install, publish, or debug an HOI4 mod or asks about HOI4 scripting (scopes, effects, triggers, variables, focus trees, events, decisions, ideas, characters, MIO, special projects, GUI, localisation, DDS), even if they only say "做个国策树"/"加个事件"/"mod 报错了".
whenToUse: 用户要做/改/修/校验/安装/发布 HOI4 Mod，或问 HOI4 脚本写法（scope/effect/trigger/变量/国策/事件/决议/理念/角色/MIO/特殊项目/GUI/本地化/DDS）时。
---

# HOI4 1.19.3 Mod 制作全流程

面向 **1.19.3.0 "Operation Postern"**（`E:\Steam\steamapps\common\Hearts of Iron IV`）实测整理。
目标不是讲概念，而是**一次把可运行的 Mod 做出来**：放对文件 → 写对语法 → 本地化齐全 → 校验通过 → 装进游戏 → error.log 干净。

> 本机还保留了一套 57 篇的深度知识库（见文末「深度资料」）：需要查字段细节时读它；本 SKILL 与 `references/` 是压缩版，足够完成 90% 任务。

## 0. 开始前先确认 3 件事

1. **游戏路径**：`E:\Steam\steamapps\common\Hearts of Iron IV`（`HOI4_GAME` 环境变量可覆盖）。
2. **版本**：`launcher-settings.json` 里 `rawVersion` 应为 `1.19.3.0`；不是就按对应版本调整语法（尤其学说/特殊项目）。
3. **目标国家有没有专属国策树**：**1.19 每个国家同一时间只有一棵激活国策树**（`country = { }` 是打分，取最高分）。
   - 没有专属树（用 `generic_focus`，如 LUX、IRE、BHU）：可以新建一整棵树，`add = 10` 就接管。
   - 已有专属树（SWE、GER、SOV…）：不能"再加一棵"；只能覆盖原树文件、或 `load_focus_tree` 换树（会顶掉原树）。先向用户确认接受哪种。

## 1. 铁律（违反任何一条都会踩坑）

1. **永不改游戏安装目录**；所有内容写在 Mod 目录，装到 `Documents/Paradox Interactive/Hearts of Iron IV/mod/`。
2. **同名文件 = 整体替换**（不是合并）。优先**新增文件**，不要复制整份原版文件。
3. **同 ID = 后者覆盖前者**；ID 用你的 `NS_` 前缀，事件用独立 `add_namespace`。
4. **本地化 `.yml` 必须 UTF-8 with BOM**；目录名与首行根键一致（`english` → `l_english:`，`simp_chinese` → `l_simp_chinese:`）。
5. **2D sprite 定义放 `interface/*.gfx`**，DDS 文件放 `gfx/interface/...`；`gfx/` 下的 `.gfx` 是 3D 用的。
6. **图标尺寸**：国策 100×88（+ `_shine`）、理念 60×68、决议 32×33、决议类别 40×51、肖像 156×210、旗帜 82×52 TGA。
7. **DDS 用未压缩 raw32 最稳**（原版 UI 同构：`dwFlags=0x81007`、无 mipmap）；DXT 要求宽高为 4 的倍数。
8. **`.mod` 的 `path` 用纯 ASCII 正斜杠**；中文路径可能加载失败 → 用 `install_mod.py` 复制到玩家目录。
9. **`.mod` 字段是 `picture=`**，不是 `thumbnail=`；`supported_version` 写 `"1.19.*"` 或 `"1.19.3.0"`，写 `*`/`1.*` 会报错。
10. **不要依赖 DLC**：需要 DLC 内容时用 `has_dlc = "..."` 分支并标注；特殊项目依赖 `Gotterdammerung`。
11. **错误看 `logs/error.log`**（`[时间][游戏日期][文件:行]: 消息`），只 grep 自己的文件名/ID；原版噪声占 95%+。
12. **脚本改动必须重启游戏**，没有完整热重载；静态校验不能替代进游戏。

## 2. 标准工作流

```
0) 侦察    读游戏文件确认目标系统/字段/原版参考（grep 原版用例）
1) 骨架    scripts/new_mod.py 生成 descriptor.mod + .mod + 本地化 + 示例内容
2) 内容    按 references/cheatsheet.md 的配方逐类添加（国策/事件/决议/理念/角色/科技/州/GUI…）
3) 本地化  每个 ID 同时补 english + simp_chinese（BOM），key 规则见 cheatsheet §2
4) 校验    python scripts/hoi4_lint.py <Mod目录>
5) 安装    python scripts/install_mod.py <Mod目录> --yes --enable
6) 实测    启动游戏（-debug_mode）→ 新开档 → 控制台触发 → 看 error.log
7) 发布    descriptor.mod 的 name/supported_version/tags/picture 齐全；干净 playset 复测
```

每次只加一类内容、加完就校验；不要一次写 2000 行再排错。

## 3. 配方索引（代码在 `references/cheatsheet.md`）

| 任务 | 章节 |
|---|---|
| 新建 Mod 骨架 / `.mod` 与 `descriptor.mod` | cheatsheet §1 |
| 本地化规则、key 命名、颜色/变量/图标 | §2 |
| 国家精神（idea） | §3 |
| 国策树（含一国一树规则、互斥/前置/奖励） | §4 |
| 事件（MTTH / is_triggered_only / 选项 / 事件链） | §5 |
| 决议（category / decision / targeted / 任务型） | §6 |
| 角色（领袖/顾问/将领/科学家） | §7 |
| 科技（folder / dependencies / on_research_complete） | §8 |
| 州、资源、建筑 | §9 |
| 动态变量 + 动态修正 | §10 |
| scripted GUI 面板（4 文件挂载） | §11 |
| MIO / 特殊项目 | §12 |
| 贴图、DDS、GFX 注册 | §13 |
| 调试命令与 error.log 对照表 | §14 |
| 1.19 与旧教程差异清单 | §15 |

## 4. 工具（`scripts/`，仅标准库；DDS 工具需 Pillow）

`$S` = **本技能资源目录**下的 `scripts`（加载技能时返回的 Base directory；本地安装通常是
`~/.agents/skills/hoi4-modding/scripts`，从插件市场安装时在插件包的 `skills/hoi4-modding/scripts`）。
Windows PowerShell 示例（`python` 不可用时换成本机 Python 绝对路径）：

```powershell
$S = "$env:USERPROFILE\.agents\skills\hoi4-modding\scripts"   # 市场安装：换成技能返回的 Base directory\scripts
$GAME = "E:\Steam\steamapps\common\Hearts of Iron IV"

# 新建 Mod 骨架（--focus 可选；--tag 默认 LUX，因为 LUX 没有专属国策树）
& python "$S\new_mod.py" "D:\mods\MyMod" --name "My Mod" --prefix MY --tag LUX --focus

# 静态校验（语法/编码/本地化/GFX/ID冲突/.mod 结构；首次约 20s 建原版索引）
& python "$S\hoi4_lint.py" "D:\mods\MyMod" --game $GAME

# 只查语法、不建原版索引（快）
& python "$S\hoi4_lint.py" "D:\mods\MyMod" --no-vanilla

# 从官方 documentation/*.md 生成 effects/triggers/modifiers/console 参考
& python "$S\build_reference.py" --game $GAME --out .\reference

# 安装到玩家 mod 目录并启用（复制安装；不要 --link，路径含中文时会被警告）
& python "$S\install_mod.py" "D:\mods\MyMod" --yes --enable

# 卸载
& python "$S\install_mod.py" "D:\mods\MyMod" --uninstall --yes

# DDS 图标：生成/检查（Pillow）
& python "$S\dds_helper.py" make icon.png out.dds --width 60 --height 68
& python "$S\dds_helper.py" check out.dds
```

> Git Bash 中把 `$S\x.py` 写成 `"$S/x.py"`、`$GAME` 写成 `/e/Steam/...` 即可。
> 本机 DSH 自带 Python：`C:\Users\17876\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`（含 Pillow）。

`new_mod.py` 会生成：`descriptor.mod`、同级 `.mod`（path 指向目标目录）、`localisation/{english,simp_chinese}`（BOM）、1 个理念、`events/` 1 个可触发事件、可选国策树；并自动跑一次 lint。

## 5. 排错：从 error.log 反推

先确认「只启用原版 + 你的 Mod」，再 grep 自己的文件/ID：

| error.log 关键字 | 常见原因 | 修法 |
|---|---|---|
| `Invalid Scope, supported: Country, provided: None` | effect/trigger 用错 scope | 查效果文档的 `Supported Scopes`；用 `every_country`/`GER = { }` 切 scope |
| `Unknown effect-type: xxx` | 关键字拼错/版本没有/不在该 scope | `grep xxx reference/effects.json`；对照 1.19 官方文档 |
| `Unknown trigger-type` / `Not a valid value` | trigger 名或参数值错误 | 查 `reference/triggers.json`；值看文档枚举 |
| `Unknown modifier: xxx` | 修正名拼错（静态修正/动态修正都会） | `grep xxx reference/modifiers.json` |
| `Unexpected token` | 括号/引号不平衡；`.mod` 字段拼错（如 `thumbnail`） | 跑 lint；检查 `picture=`/`path=` |
| `Tried to get dynamic token` / `dynamic token ... OOS` | 本地化/脚本拼接 key 未注册 | 改用普通 loc key 或 `synchronized_dynamic_tokens` |
| 图标空白/黑块 | GFX 未注册、texturefile 不存在、DDS 头不对 | `dds_helper.py check`；确认 sprite 在 `interface/*.gfx` |
| 中文方框 | GUI 用了没有中文 `bitmapfont_override` 的字体名 | 换有中文覆盖的字体（见知识库 `05_presentation/chinese_fonts.md`） |
| 国策树不显示 | 原版树分数更高；或树 id/坐标错误 | 按 §4 规则选「无专属树国家」或覆盖原树 |

游戏内调试：`-debug_mode` 启动，控制台（`~`/`^`）常用 `event hho.1`、`focus.autocomplete`、`debug_events`、`tag SWE`、`pp 500`；完整命令见 `reference/CHEATSHEET_console.md`（若已生成）。

## 6. 验收清单

- [ ] `hoi4_lint.py` 0 error（warning 尽量清零）。
- [ ] 所有新增 ID 有 en + zh 本地化，`.yml` 带 BOM。
- [ ] 所有 `GFX_` 引用真实存在；自绘 DDS 尺寸/格式正确。
- [ ] 没有覆盖原版整文件（除非有意）；`.mod` path 为 ASCII。
- [ ] 干净 playset 进游戏：新开档、触发全部内容、`error.log` 无自己文件的报错。
- [ ] 发布信息（name/supported_version/tags/picture/README/依赖 DLC）齐全；联机 checksum 一致。

## 7. 深度资料

本机知识库（若存在，优先读具体主题文档）：

```
C:\Users\17876\Desktop\DeepseekHarness\钢铁雄心4\
├─ PLAYBOOK.md                 # 14 个任务配方（最常用）
├─ knowledge/00_environment.md # 两个根目录、加载顺序、覆盖语义、日志、性能
├─ knowledge/01_script/        # scope / effect/trigger / 变量 / 动态变量 / on_actions
├─ knowledge/02_content/       # 国策/事件/决议/理念/角色/科技/MIO/特殊项目…
├─ knowledge/03_military/、04_world_map/、05_presentation/、06_workflow/
├─ reference/                  # 自动生成的 effects/triggers/modifiers/console 数据
└─ example_mods/               # 两个可运行示例（hello_hoi4 / advanced_systems）
```

不在本机时：用 `references/cheatsheet.md` + 游戏自带 `documentation/*.md`（官方字段参考，但注意它**不是全集**：`unit_modifiers`、`is_fighting_in_strategic_region`、`is_deployed` 等 1.19 可用写法未收录，冲突时以游戏文件为准）。

## 8. 跨平台与共享

本技能是标准 Agent Skills 目录（`SKILL.md` + 可选 `scripts/`、`references/`），复制即可迁移：

| 平台 | 安装位置 |
|---|---|
| DeepSeek Harness | `~/.agents/skills/hoi4-modding/` |
| Claude Code | `~/.claude/skills/hoi4-modding/` 或项目内 `.claude/skills/hoi4-modding/` |
| 其他兼容客户端 | 其 Skills 设置/目录；zip 根目录必须是 `hoi4-modding/` |

- 游戏/玩家目录会**自动探测**；探测失败时设 `HOI4_GAME` / `HOI4_USER_DIR`（Linux Proton 必须设 `HOI4_USER_DIR`）。
- 依赖：Python 3.10+（标准库；DDS 需 Pillow）+ 本机 HOI4 1.19.3。
- 共享边界：不含游戏本体资源，只有原创笔记/脚本；不依赖本机知识库也能运行（`references/cheatsheet.md` 自足）。
- 详细安装/自检/更新说明见同目录 `INSTALL.md`。

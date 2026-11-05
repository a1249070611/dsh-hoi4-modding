# dsh-hoi4-modding

**English** | [中文](#中文)

[![npm version](https://img.shields.io/npm/v/dsh-hoi4-modding.svg)](https://www.npmjs.com/package/dsh-hoi4-modding)
[![ci](https://github.com/a1249070611/dsh-hoi4-modding/actions/workflows/ci.yml/badge.svg)](https://github.com/a1249070611/dsh-hoi4-modding/actions/workflows/ci.yml)

A DeepSeek Harness **skill bundle** for **Hearts of Iron IV 1.19.3** modding. It registers one skill,
`hoi4-modding`, and ships the working notes, references and Python tooling behind it, so the agent can
take an HOI4 mod from an empty folder to a verified, installed, `error.log`-clean mod — and debug the
parts that actually go wrong: tech-tree pages, the tank designer, icons, CJK fonts, scripted GUI and
topbar buttons.

- **One skill, no background services.** Installing the package only adds skill metadata; nothing runs
  until you ask for a task and the agent invokes a bundled script.
- **Built from real sessions.** Every reference section cites the game/mod file and line it came from;
  the 1.4.0 round is a read-only survey of 23 workshop mods (~44 GB) plus four overhauls (Kaiserreich,
  The Fire Rises, East Showdown, Road to 56).
- **14 Python tools.** All standard library except `dds_helper.py` (Pillow) — verifier, installer,
  tech-tree/icon/font auditors, designer layout generator, DDS pipeline.
- **No game assets, no network calls, no API keys.**

Current release: **1.4.1** — see [CHANGELOG.md](CHANGELOG.md). The package is also listed in
dsh-market through the `awesome-dsh-plugin` index (category `skill`).

## Install

```sh
# npm (what a market install does)
dsh plugin --profile web add dsh-hoi4-modding

# or straight from this repo
dsh plugin --profile web add github:a1249070611/dsh-hoi4-modding
```

Restart / refresh as the host asks. The skill shows up in the session skill catalog; trigger it by
asking for HOI4 work ("做个 HOI4 mod", "加个国策树", "mod 报错了") or explicitly "load hoi4-modding".
The bundle works on DeepSeek Harness **0.2.x** (`engines.dsh: >=0.2.0 <0.3.0`).

If the game is installed somewhere unusual, set `HOI4_GAME` / `HOI4_USER_DIR`; otherwise the scripts
auto-detect the Steam install and the player `mod/` directory.

## What it covers

| Area | What the skill knows how to do |
|---|---|
| Mod authoring | Scaffold `descriptor.mod` + `.mod` + localisation + a runnable idea/event (optional focus tree); focus trees, events, decisions, ideas, characters, technologies, states/resources/buildings, dynamic variables and modifiers, MIO, special projects, scripted GUI panels, text/icons/GFX registration |
| Tech-tree UI | `technology_folders.available` must use `original_tag` (flag-based conditions silently drop every connection line); big/small item mixing needs the small item background **sprites** to point at real small textures; split/merge pages; `@` grid macros; `gridbox` as a draw filter; three debugging recipes |
| Tank designer | Window/slot position tables, 16- and 18-slot layouts (7+4+7), `module_slots` data order vs `pos_custom_module_slot_window_N`, module categories, the fixed-size 1092×553 window background trap, `duplicate_archetypes` and `gui_category` |
| 3D tank models | `graphic_db` → `entity` (`.asset`) → `pdxmesh` (`.gfx`) → `.mesh/.anim/.dds`; reuse vanilla entities, repaint, or custom mesh; effect nodes (`barrel`, tracks, exhaust) |
| Icon pipeline | Photo/vector → 173×77 `.dds` with safe area and card preview, background removal (transparent/white/8px checkerboard), white-paint protection, 183×84 card self-check |
| Scripted GUI & topbar | `containerWindowType` only (`windowType` fails), `<button>_click` effect naming, topbar plate extension and alert/info-bar offsets, the three topbar mounting patterns, why scripted windows are never auto-closed by native windows, TNO-style native-shell tabs |
| Localisation & fonts | UTF-8 **with BOM**, key rules, multi-line escaping; the real CJK `????` root cause (`interface/core_chinese.gfx` `bitmapfont_override` slices — every `.fnt` has zero CJK glyphs), 37 safe font names, custom font slices, `font_audit.py` |
| Verification & triage | Static lint (syntax/encoding/BOM/localisation/GFX/ID conflicts/`.mod`), tech-page audit, item-size vs sprite check, `error.log` triage table, acceptance checklist that requires a real new-game test |
| Knowledge base | Compact cheatsheet for 15 common tasks, a topic→deep-doc index, the 23-workshop-mod technique survey, and a multi-agent division-of-labour playbook (survey / build / audit write domains, handoff contract) |

## Bundled tools

Run with the script directory of the installed skill (`$S` below). Python 3.10+; only DDS work needs
Pillow.

| Script | What it does |
|---|---|
| `new_mod.py` | Scaffold a runnable mod (`.mod`, `descriptor.mod`, BOM localisation, example idea/event, optional focus tree) and lint it |
| `hoi4_lint.py` | Static verifier: syntax, encoding/BOM, localisation, GFX references, ID conflicts, `.mod` structure; builds a vanilla index on first run (`--no-vanilla` to skip) |
| `install_mod.py` | Copy-install into the player `mod/` directory and enable in the playset (`--uninstall` to remove); never touches the game install |
| `build_reference.py` | Generate effects/triggers/modifiers/console references from the game's own `documentation/*.md` |
| `dds_helper.py` | Generate or inspect HOI4 DDS icons (Pillow) |
| `pdx_parser.py` | Tolerant PDX script parser shared by the linter |
| `tech_tree_audit.py` | Audit tech pages: registry vs page/tab/item templates/gridboxes/techs/localisation |
| `tech_folder_available.py` | Migrate `technology_folders.available` from `has_country_flag` to `original_tag` (`--check` / `--apply` / `--revert`, backs up) |
| `item_sprite_check.py` | Compare item template sizes with the actual item background sprite pixels ("small item looks big") |
| `errorlog_triage.py` | Triage `error.log` into tech-tree / texture / scope / unknown-field / localisation buckets |
| `tank_designer_probe.py` | Probe the designer: window, slot positions, slot-entry size, module categories, chassis slot counts, background DDS size |
| `tank_designer_layout.py` | Generate a custom designer slot layout (`16-compact`, `16-tall`, `18-compact` presets) without touching the game directory |
| `tech_icon_import.py` | Photo/vector → 173×77 DDS: de-background, safe-area placement, 183×84 card preview |
| `font_audit.py` | Scan `interface/` + `gfx/` for `font =` names that have no Chinese slices; `--list-supported`, `--json`, CI-friendly exit code |

## Reference index

| Topic | File |
|---|---|
| Copy-ready code for 15 common tasks, localisation keys, `.mod` fields | `references/cheatsheet.md` |
| Topic → deep-documentation map | `references/deep-dive.md` |
| Tech-tree pages, connections, big/small items, debugging | `references/tech-tree-ui.md` |
| Scripted GUI, topbar buttons, window lifecycle | `references/scripted-gui-and-topbar.md` |
| Tank designer: positions, layouts, module slots | `references/tank-designer.md` |
| 3D tank models: entity/pdxmesh/mesh chain | `references/tank-models-3d.md` |
| Icon pipeline: 173×77 DDS, de-background, safe area | `references/icon-dds-pipeline.md` |
| CJK fonts: `????` root cause and safe font names | `references/fonts-and-cjk.md` |
| 23 workshop mods: gridbox filters, `@` macros, `duplicate_archetypes`, topbar mountings | `references/vanilla-mod-survey.md` |
| Multi-agent split: write domains, handoff contract, audit separation | `references/agent-teams-playbook.md` |
| Install / self-check / update of the skill itself | `INSTALL.md` |

## Requirements

- DeepSeek Harness **0.2.x** with the skill registry.
- **Python 3.10+** for the bundled scripts (stdlib only; `dds_helper.py` needs `pip install pillow`).
- **HOI4 1.19.3** is optional but recommended: the verifier's vanilla index, GFX and ID checks read the
  installed game. Without it the skill still scaffolds and documents; the game directory is auto-detected
  and can be overridden with `HOI4_GAME` / `HOI4_USER_DIR`.
- No game files are shipped, no network access, no API keys.

## Permissions

The plugin registers skill metadata only. The bundled Python scripts run **when the user asks**; they
read the HOI4 install and, for `install_mod.py`, write into the player
`Documents/Paradox Interactive/Hearts of Iron IV/mod/` directory — never the game install itself.
Commands are visible in the conversation before they run.

## Layout

```
dsh-hoi4-modding/
├─ package.json              # name, dsh.bundle.patch, files, engines, peerDependencies
├─ cordis.patch.yml          # inserts the hoi4-modding skill plugin
├─ lib/index.js              # reads skills/hoi4-modding/SKILL.md and registers it with ctx.skills
├─ skills/hoi4-modding/      # SKILL.md + INSTALL.md + references/ + scripts/
├─ tests/smoke.test.mjs      # dependency-free tests: frontmatter, resources, registration, patch
├─ icon.svg                  # package icon
└─ .github/workflows/        # ci.yml (test on 22/24) and release.yml (tag → npm Trusted Publishing)
```

## Changelog (latest)

- **1.4.1** — packaging and metadata refresh: the npm tarball no longer ships `__pycache__/` and the
  6.9 MB `scripts/.cache/vanilla_index.json` (1.4.0 was 1.4 MB / 41 files; 1.4.1 is 116 KB / 34 files);
  README rewritten in both languages; `description` / `keywords` and the market listing text updated.
- **1.4.0** — CJK font root cause (`core_chinese.gfx` bitmapfont overrides, `font_audit.py`), the
  23-workshop-mod survey and the multi-agent playbook.
- **1.3.0** — scripted GUI / topbar guide and the 18-slot tank designer preset.
- **1.2.0** — tank designer, 3D tank models and the icon pipeline, plus four new scripts.
- **1.1.0** — tech-tree UI knowledge (connections, big/small items, debugging recipes) and four scripts.
- **1.0.0** — initial release.

Details: [CHANGELOG.md](CHANGELOG.md).

## Publishing (maintainers)

Releases are published by GitHub Actions with npm **Trusted Publishing (OIDC)** — no `NPM_TOKEN`:

1. npmjs.com → `dsh-hoi4-modding` → Settings → **Trusted Publisher** → GitHub Actions
   (`a1249070611/dsh-hoi4-modding`, workflow `release.yml`).
2. Bump the version, commit, then `git tag v1.4.1 && git push origin master --tags`; `release.yml` runs
   the tests and publishes with provenance.

The old granular-token flow (`npm publish` with a bypass-2FA token) is deprecated by npm and stops
working in **January 2027**.

## License

MIT. Skill text, references and scripts are original; no Paradox game assets are included.

---

## 中文

**《钢铁雄心4》(Hearts of Iron IV, HOI4) 1.19.3 Mod 开发技能包（DeepSeek Harness 插件）。**
安装后注册一个名为 `hoi4-modding` 的技能，并带上它的工作笔记、参考文档和 Python 工具，让 agent
能从空目录一路做出一份「校验通过、装进游戏、`error.log` 干净」的 Mod，并在出问题时定位到真正的原因：
科技页、坦克设计器、图标、中文字体、scripted GUI 与顶栏按钮。

- **只有一个技能，没有后台服务。** 安装只注册技能元数据；你不派任务，什么都不会自动执行。
- **来自真实工程。** `references/` 每条结论都标了游戏/Mod 的文件与行号；1.4.0 的内容来自 23 个工坊
  Mod（约 44 GB，只读）实测，外加 Kaiserreich、The Fire Rises、East Showdown、Road to 56 四个 overhaul。
- **14 个 Python 工具。** 除 `dds_helper.py` 需要 Pillow 外全部只用标准库：校验、安装、科技树/图标/
  字体审计、设计器布局生成、DDS 流水线。
- **不含游戏素材、不联网、不需要 API Key。**

当前版本：**1.4.1**（见 [CHANGELOG.md](CHANGELOG.md)）。本包已通过 `awesome-dsh-plugin` 索引
收录进 dsh-market（分类 `skill`）。

### 安装

```sh
# npm（市场安装等价于此）
dsh plugin --profile web add dsh-hoi4-modding

# 或直接从仓库安装
dsh plugin --profile web add github:a1249070611/dsh-hoi4-modding
```

刷新/重启后技能出现在技能目录。直接说「做个 HOI4 mod」「加个国策树」「mod 报错了」即可触发，
也可以显式说「加载 hoi4-modding 技能」。要求 DeepSeek Harness **0.2.x**
（`engines.dsh: >=0.2.0 <0.3.0`）。游戏装在非常规位置时设 `HOI4_GAME` / `HOI4_USER_DIR`，
否则脚本会自动探测 Steam 安装目录与玩家 `mod/` 目录。

### 能做什么

| 领域 | 技能掌握的内容 |
|---|---|
| Mod 制作 | 生成 `descriptor.mod` + `.mod` + 本地化 + 可运行的理念/事件（可选国策树）；国策/事件/决议/理念/角色/科技/州与资源/建筑/动态变量与修正/MIO/特殊项目/scripted GUI 面板/贴图与 GFX 注册 |
| 科技树 UI | `technology_folders.available` 只能用 `original_tag`（旗帜判定会让整页连线被静默丢弃）；大小框混排要让小框背景**精灵**指向真正的小图；拆页/并页；`@` 网格宏；`gridbox` 是「画不画」的开关；三种调试手法 |
| 坦克设计器 | 窗口与槽位坐标表、16 槽与 18 槽（7+4+7）布局、`module_slots` 书写顺序 vs `pos_custom_module_slot_window_N`、模块类别、固定 1092×553 窗口背景的坑、`duplicate_archetypes` 与 `gui_category` |
| 坦克 3D 模型 | `graphic_db` → `entity`（`.asset`）→ `pdxmesh`（`.gfx`）→ `.mesh/.anim/.dds`；复用原版实体、换贴图或自制 mesh；特效节点（炮管、履带、排气） |
| 图标流水线 | 照片/矢量图 → 173×77 `.dds`（安全区 + 183×84 卡片预览）、去背景（透明/白底/8px 棋盘格）、白色涂装保护、卡片自检 |
| scripted GUI 与顶栏 | 只能用 `containerWindowType`（`windowType` 会失败）、按钮 effect 必须叫 `<按钮名>_click`、顶栏底图补块与警报/信息栏避让、三种顶栏挂法、为什么脚本窗口永远不会被原生窗口自动关闭、TNO 式原生外壳 tab |
| 本地化与字体 | UTF-8 **带 BOM**、key 规则、多行转义；中文 `????` 的真实根因（汉字只在 `interface/core_chinese.gfx` 的 `bitmapfont_override` 分片里，`.fnt` 自身 CJK 字形为 0）、37 个安全字体名、自建分片、`font_audit.py` |
| 校验与排错 | 静态校验（语法/编码/BOM/本地化/GFX/ID 冲突/`.mod` 结构）、科技页审计、模板尺寸 vs 精灵像素、`error.log` 分诊表、要求「进游戏新开档」的验收清单 |
| 知识库 | 15 个常用任务的速查、主题→深度文档索引、23 个工坊 Mod 技法总览、多 agent 分工规范（survey / build / audit 写域与交接契约） |

### 随包工具

在已安装技能目录的 `scripts/` 下运行（下文 `$S`）。Python 3.10+，只有 DDS 相关需要 Pillow。

| 脚本 | 作用 |
|---|---|
| `new_mod.py` | 生成可运行 Mod 骨架（`.mod`、`descriptor.mod`、BOM 本地化、示例理念/事件、可选国策树）并自动 lint |
| `hoi4_lint.py` | 静态校验：语法、编码/BOM、本地化、GFX 引用、ID 冲突、`.mod` 结构；首次运行会建原版索引（`--no-vanilla` 跳过） |
| `install_mod.py` | 复制安装到玩家 `mod/` 并在 playset 启用（`--uninstall` 卸载）；绝不改游戏安装目录 |
| `build_reference.py` | 从游戏自带 `documentation/*.md` 生成 effects/triggers/modifiers/控制台参考 |
| `dds_helper.py` | 生成/检查 HOI4 DDS 图标（Pillow） |
| `pdx_parser.py` | 宽容的 PDX 脚本解析器，供 lint 使用 |
| `tech_tree_audit.py` | 审计科技页：注册表 ↔ 页面/页签/item 模板/网格/科技/本地化 |
| `tech_folder_available.py` | 把 `technology_folders.available` 从 `has_country_flag` 迁移到 `original_tag`（`--check` / `--apply` / `--revert`，自动备份） |
| `item_sprite_check.py` | 对比 item 模板尺寸与背景精灵实际像素（专治「小框显示成大框」） |
| `errorlog_triage.py` | 把 `error.log` 分成科技树/贴图/scope/未知字段/本地化几类 |
| `tank_designer_probe.py` | 设计器体检：窗口、槽位位置、槽位模板尺寸、模块类别、底盘槽数、背景 DDS 尺寸 |
| `tank_designer_layout.py` | 生成自定义槽位布局（`16-compact`、`16-tall`、`18-compact` 预设），不动游戏目录 |
| `tech_icon_import.py` | 照片/矢量图 → 173×77 DDS：去背景、安全区摆放、183×84 卡片预览 |
| `font_audit.py` | 扫 `interface/` + `gfx/` 里没有中文分片的 `font =` 名字；`--list-supported`、`--json`、退出码可用于 CI |

### 参考文档索引

| 主题 | 文件 |
|---|---|
| 15 个常用任务的现成代码、本地化 key、`.mod` 字段 | `references/cheatsheet.md` |
| 主题 → 深度文档地图 | `references/deep-dive.md` |
| 科技树页面、连线、大小框、调试 | `references/tech-tree-ui.md` |
| scripted GUI、顶栏按钮、窗口生命周期 | `references/scripted-gui-and-topbar.md` |
| 坦克设计器：坐标、布局、模块槽位 | `references/tank-designer.md` |
| 坦克 3D 模型：entity/pdxmesh/mesh 链路 | `references/tank-models-3d.md` |
| 图标流水线：173×77 DDS、去背景、安全区 | `references/icon-dds-pipeline.md` |
| 中文字体：`????` 根因与安全字体名 | `references/fonts-and-cjk.md` |
| 23 个工坊 Mod：gridbox 过滤、`@` 宏、`duplicate_archetypes`、顶栏挂法 | `references/vanilla-mod-survey.md` |
| 多 agent 分工：写域、交接契约、审计分离 | `references/agent-teams-playbook.md` |
| 技能自身的安装/自检/更新 | `INSTALL.md` |

### 依赖

- DeepSeek Harness **0.2.x**（含技能注册表）
- **Python 3.10+**（脚本仅标准库；`dds_helper.py` 需 `pip install pillow`）
- **HOI4 1.19.3** 可选但推荐：校验器的原版索引、GFX 与 ID 检查要读已安装的游戏；没有游戏也能生成
  骨架和查文档。游戏目录自动探测，可用 `HOI4_GAME` / `HOI4_USER_DIR` 覆盖。
- 不含任何游戏本体资源，不需要网络与 API Key。

### 权限说明

插件只注册技能元数据。技能里的 Python 脚本由 agent 在你要求时执行：读取游戏安装目录；
`install_mod.py` 会把 Mod 复制到玩家 `Documents/Paradox Interactive/Hearts of Iron IV/mod/`
（不改游戏安装目录）。所有命令在对话中可见。

### 目录结构

```
dsh-hoi4-modding/
├─ package.json              # 包名、dsh.bundle.patch、files、engines、peerDependencies
├─ cordis.patch.yml          # 安装时插入 hoi4-modding 技能插件
├─ lib/index.js              # 读取 skills/hoi4-modding/SKILL.md 并注册到 ctx.skills
├─ skills/hoi4-modding/      # SKILL.md + INSTALL.md + references/ + scripts/
├─ tests/smoke.test.mjs      # 无依赖测试：frontmatter、资源、注册、patch
├─ icon.svg                  # 包图标
└─ .github/workflows/        # ci.yml（22/24 测试）与 release.yml（打 tag → npm Trusted Publishing）
```

### 更新记录（最近）

- **1.4.1** — 打包与元数据刷新：npm 包不再夹带 `__pycache__/` 和 6.9 MB 的
  `scripts/.cache/vanilla_index.json`（1.4.0 是 1.4 MB / 41 个文件，1.4.1 是 116 KB / 34 个文件）；
  README 中英双版重写；`description` / `keywords` 与市场条目简介同步更新。
- **1.4.0** — 中文字体根因（`core_chinese.gfx` 的 bitmapfont_override、`font_audit.py`）、
  23 个工坊 Mod 技法总览、多 agent 分工规范。
- **1.3.0** — scripted GUI / 顶栏专题与 18 槽坦克设计器预设。
- **1.2.0** — 坦克设计器、坦克 3D 模型、图标流水线，新增 4 个脚本。
- **1.1.0** — 科技树 UI 知识（连线、大小框、调试手法）与 4 个脚本。
- **1.0.0** — 首个版本。

详见 [CHANGELOG.md](CHANGELOG.md)。

### 发布方式（维护者）

默认走 **GitHub Actions + npm Trusted Publishing (OIDC)**，不需要 `NPM_TOKEN`：

1. npmjs.com → `dsh-hoi4-modding` → Settings → **Trusted Publisher** → GitHub Actions
   （仓库 `a1249070611/dsh-hoi4-modding`、workflow `release.yml`）。
2. 改版本号、提交，然后 `git tag v1.4.1 && git push origin master --tags`；`release.yml` 会跑测试并
   带 provenance 发布。

旧的 granular token 直发方式（勾选 Bypass 2FA 后 `npm publish`）已被 npm 弃用，**2027 年 1 月起失效**。

### 许可

MIT。技能文本、参考文档与脚本为原创，不包含 Paradox 游戏素材。

# 参考库

84 篇上游文档（75 篇正文 + 9 个索引），覆盖 HOI4 1.19.x 的脚本语言、内容系统、军事、世界地图、表现层、工程流程。

**这不是我写的，也不是官方文档。** 它是一位作者在开发自己那个 mod 的过程中写的笔记。来源与许可见 [ATTRIBUTION.md](ATTRIBUTION.md)。

## ⚠️ 用之前先读这句

这套文档**有作者的项目印记**，不能整本当规范：

- 452 处 `HHO_` 前缀是作者自己 mod 的命名（分布在 31 篇），换你自己的前缀即可
- `90_case-studies/` 5 篇全是单个项目的实战记录，作者自己都标了「不是默认做法」
- 15 处引用 `.tmp/`、`game-survey.md` 等未随包分发的产物（分布在 7 篇），那些数字你无法复核
- 21 篇拿「本机实测」当证据，但没给可查坐标

**分级、溯源规则、哪些能直接用** → [AUTHORITY.md](AUTHORITY.md)。一句话版本：

> 结构和路径（`00_start` / `01_script` / `04_world`）可以照做；军事数值、字体名单、性能建议只当线索；案例区只读思路。

## 怎么读

三层，别一次通读：

1. **本目录 `_index.md`** —— 总路由表（「我要做 X → 读哪一篇」，50+ 条）。先查这里。
2. **域目录的 `_index.md`** —— 该域文档清单 + 5 条最重要结论 + 常见坑。比读单篇快。
3. **单篇文档** —— 具体字段、语法、实例路径。

也可以用检索直接命中（`references/` 已进知识库索引）：

```
kiant_hoi4_kb_search "字体 方框"      → 05_presentation/fonts-cjk.md
kiant_hoi4_kb_search "师编制"        → 03_military/division-templates.md
```

```
references/
├── _index.md              总路由
├── cheatsheet.md          跨域速查，抄了能跑的片段
├── 00_start/              环境、目录结构、加载与覆盖          4 篇
├── 01_script/             scope / effect / trigger / 变量 / 集合   10 篇
├── 02_content/            国策 事件 决议 理念 角色 科技 MIO 情报…  14 篇
├── 03_military/           陆海空 装备 编制 学说                 8 篇
├── 04_world/              州 战略区 建筑 资源 补给 地形 地图     8 篇
├── 05_presentation/       GUI scripted GUI GFX DDS 本地化 字体…  11 篇
├── 06_workflow/           初始化 调试 校验 性能 兼容 迁移 发布   8 篇
├── 07_tools/              命令行工具逐个用法                    15 篇
└── 90_case-studies/       真实项目实战记录（不是默认做法）        6 篇
```

## 权威性分层（冲突时按此取信）

写 mod 时两处说法打架，按这个顺序信任：

1. **游戏自带 `documentation/*.md`** —— effects / triggers / modifiers 的字段级权威。
2. **游戏自带 `common/**/_documentation.md`** —— 1.19.4.2 有 39 处域级文档（decisions、characters、MIO、raids、special_projects、factions 等）。
3. **原版实例文件** —— 没有专门文档的域（national_focus、ideas、technologies、units、history、interface、gfx、map、game_rules、defines）只能读实例。
4. **本参考库的域文档** —— 对上述三者的整理与实测补充。
5. **`90_case-studies/`** —— 单个项目的做法，**不能当通用规则**。
6. **网上教程** —— 只当线索。看到 `while = {`、`custom_trigger_tooltip` 占满全文的，基本是 1.9 前后的老引擎。

前三层在你本机就能查，用知识库索引它们：

```
kiant_hoi4_kb_build action=build
kiant_hoi4_kb_search "add_buildings_construction" source=vanilla
```

## ⚠️ 文中的工具命令指向的是上游 CLI

文档里会出现 `python $SKILL/tools/cli.py lint <mod>`、`scripts/hoi4_lint.py`、`dds_helper.py` 这类命令。**这些文件在本插件里不存在**——它们属于上游项目 dsh-hoi4-modding 的 CLI 工具链，我搬过来的是文档，不是代码。

功能等价物在本插件的 MCP 工具里：

| 文档里写的 | 本插件用什么 |
|---|---|
| `lint <mod>` | `kiant_hoi4_validate_mod` |
| `loc audit <mod>` | `kiant_hoi4_scan_localisation`，或 `kiant_hoi4_validate_mod` 的本地化部分 |
| `gfx audit <mod>` | `kiant_hoi4_validate_mod deep=true`（`assets` + `sprites` 校验器） |
| `tech audit <mod>` | `kiant_hoi4_validate_mod deep=true`（`technology` 校验器） |
| `item_sprite_check.py` | `sprites` 校验器 |
| `errorlog` / `errorlog_triage.py` | `kiant_hoi4_analyze_error_log` |
| `parse <file>` / `pdx_parser.py` | `kiant_hoi4_parse_script` |
| `init <dir>` / `new_mod.py` | `kiant_hoi4_scaffold kind=mod` |
| `reference build` | `kiant_hoi4_kb_search` + `kiant_hoi4_kb_lookup` |
| `self-test` | `mcp-server/selftest.py` |
| `font audit <mod>` | **无等价物** — 但 `05_presentation/fonts-cjk.md` 给了手工核对名单 |
| `map audit <mod>` | **无等价物** — 见 `04_world/` 各篇的字段清单自查 |
| `model chain-check` | **部分** — `assets` 校验器只查文件存在，查不了 `.mesh` 内部 |
| `dds make` / `icon import` | **无等价物** — 需要 Pillow，本插件零依赖不装 |
| `install` / `uninstall` | **无等价物** — 手工把两个描述文件放进 `mod/` |
| `tech available --apply` | **无等价物** — 目前只报不修 |
| `tank layout` | **无等价物** |

没等价物的是真的没有，不是我没找到。要用那些能力，直接装上游插件（`npm i -g dsh-hoi4-modding`），两者可以并存。

## 版本口径

文档字段以 **1.19.x** 为准，实测多为 1.19.3.0，并用 1.19.4.2 复核过文件位置。跨版本使用前先读 `06_workflow/migration.md`——1.19 改了不少东西：

- 学说从科技树独立成 `common/doctrines/`（folder → grand doctrine → track → subdoctrine）
- 地形从 `map/terrain.txt` 移到 `common/terrain/00_terrain.txt`
- 战斗宽度改成绝对方格，不再按 20/40 宽算
- 装备在 `common/units/equipment/`，**没有** `common/equipment/` 这个目录
- `create_faction` 已废弃，改 `create_faction_from_template`

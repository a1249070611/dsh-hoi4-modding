---
title: 速查表（通用片段，按 01–07 域分区）
domain: cheatsheet
scope: reference
verified_on: 1.19.x
verified_at: 2026-11-06
---

# HOI4 1.19.x 速查（通用片段）

> 只收「跨项目通用、抄了就能跑」的片段。字段全解以 `01_script`–`07_tools` 各域文档为准；真实项目排障见 `90_case-studies/`。文中 `NS_` 是占位前缀，换成人/项目自己的前缀；版本口径为 1.19.x。

## 01_script — 语言基础

| 类别 | 常用项 |
|---|---|
| scope 切换 | `ROOT` / `FROM` / `PREV` / `THIS`；`TAG = { }` 进国家，`<state_id> = { }` 进州，`owner = { }` 进所有国 |
| 常用 effect | `add_political_power` `add_stability` `add_war_support` `add_ideas` `set_variable` `add_to_variable` `country_event` |
| 常用 trigger | `tag` `original_tag` `has_idea` `has_completed_focus` `has_tech` `has_war` `political_power >` `check_variable` `num_of_factories >` |
| 条件组合 | 同块内多条件 = AND；`OR = { }` / `NOT = { }` / `XOR = { }`，嵌套深时用显式 `AND = { }` 提高可读性 |

- 头号错误是作用域：`add_political_power` 要国家 scope，`add_building_construction` 要州 scope；报 `Invalid Scope` 就去查该条的 Supported Scopes。
- 命名约定：自定义 id 统一加前缀；事件用 `namespace.n`；loc key 与 id 同名，描述用 `<id>_desc`。

## 02_content — 国策 / 事件 / 理念 / 决议 / 角色 / 科技

- 位置：`common/national_focus/`、`common/ideas/`、`common/decisions/`、`common/characters/`、`common/technologies/`、`common/technology_tags/`；事件在根目录 `events/`。
- 国策：`country = { factor = ... }` 是**打分**，每国只装分数最高的一棵树；`default = yes` 只影响全 0 分时。同 `prerequisite` 块内多个 `focus =` 是 AND，多个 `prerequisite` 块是 OR。
- 事件：`add_namespace = ns`；要么 `is_triggered_only = yes`，要么 `mean_time_to_happen`；选项 `option = { name = ns.1.a }`。
- 决议：顶层每个块就是一个**类别**，类别里直接放决议，没有 `decisions = { }` 外层。
- 科技：每项含 `folder { name position }`、`path`、`dependencies`、`categories`；新 folder 要在 `technology_folders = { }` 声明。
- 本地化 key：对象用 `<id>`；事件 `ns.1.t` / `.d` / `.a`；类别用类别 id。

## 03_military — 装备 / 模块 / MIO / 特殊项目

- 装备文件在 `common/units/equipment/`（**不是** `common/equipment/`）；底盘就是 archetype，派生用 `duplicate_archetypes`，且必须写在被复制对象之后求值。
- `module_slots` 的槽名必须在 slot 定义里存在；模块的 `category =` 隐式建类别；互斥用 `module_count_limit`；`default_modules` 写在 archetype 上。
- MIO 在 `common/military_industrial_organization/organizations/`，`allowed` 开局为真即自动建实例；特殊项目在 `common/special_projects/projects/`（需 Gotterdammerung）。
- 学说结构在 `common/doctrines/`：folder → grand_doctrines → tracks → subdoctrines → mastery/reward；旧教程「四条树 + path」已作废。

## 04_world — 州 / 资源 / 建筑 / 地图

- 州历史 `history/states/<num>-<name>.txt`：`id` 不能占用原版 id；`provinces` 里的省 id 必须在 `map/definition.csv` 存在。
- 加建筑/改归属优先用 effect（`add_building_construction`、`add_extra_state_shared_building_slots`、`set_owner`），不要直接改原版 history。
- 地形在 `common/terrain/00_terrain.txt`（旧 `map/terrain.txt` 已废），`combat_width` 是绝对值。
- `map/supplyareas/` 基本自动生成，不要按旧教程每区建一个文件。
- 州内写 `resources = { steel = 12 }`；可开采量还受科技/国策修正影响。

## 05_presentation — GUI / GFX / 图标 / 字体

- 2D sprite 只能注册在 `interface/**/*.gfx`：`spriteType = { name = "GFX_x" texturefile = "gfx/..." }`；`.gui` 里用 `spriteType = "GFX_x"` 引用。
- 官方常用尺寸：focus 100×88（另有同名 `_shine`）、idea 60×68、decision 32×33、decision category 40×51、portrait 156×210、flag 82×52（TGA）。
- DDS 用 raw32（未压缩、无 mipmap）最稳；改尺寸要连 sprite 引用与控件 size 一起改，否则只是被拉伸或裁切。
- scripted GUI 是四处闭环：`common/scripted_guis/` 定义 + `interface/*.gui` 窗口 + 挂载点（`context_type = decision_category` 最稳）+ 本地化；`effects` 键名规则 `<元素名>_click`。
- 往原生窗口里加东西只有两条路：新增容器挂 `parent_window_token`，或整份覆盖原版窗口文件——两者不能混着用。
- 中文显示成方框是字体缺中文覆盖（`gfx/fonts/`），不是文本编码问题。

## 06_workflow — 建 / 调试 / 校验 / 发布

- 一个 mod 有两个描述文件：本体 `descriptor.mod`（**不写** `path`、不能有 BOM）+ `<用户目录>/mod/<name>.mod`（写 `path`，正斜杠、纯 ASCII）。
- `.mod` 里用 `picture=` 不是 `thumbnail=`；`supported_version` 的通配符只能在最后一段，如 `"1.19.*"`。
- 调试启动加 `-debug_mode`（不是 `-debug`），崩溃定位加 `-crash_data_log`；脚本修改靠控制台 `reload` 系列，但 history/map 不热重载。
- error.log 95%+ 是原版噪声：只 grep 自己的文件名/ID/前缀，用 `scripts/errorlog_triage.py` 分类，只比「改动前后新增」。
- 校验分层：语法（`scripts/hoi4_lint.py`）→ 引用（loc key / sprite / 文件存在）→ 语义（科技挂载 / 国策连线 / archetype）→ 运行（error.log）；串成一次执行与退出码契约见 [06_workflow/validation.md](06_workflow/validation.md)。
- 发布前必查：`descriptor.mod` 在根、无 BOM、`thumbnail.png` <1MB、`picture=`、`version` 递增、`supported_version = "1.19.*"`、本地化 en + simp_chinese 齐全、只上传本体（带 `path` 的 `.mod` 不上传）。
- 旧教程与 1.19 的差异（学说、地形、装备目录、理念 on_add/on_remove、文档滞后）见 [06_workflow/migration.md](06_workflow/migration.md)。

## 07_tools — 本插件脚本入口

- 起步：`scripts/new_mod.py`（骨架）、`scripts/install_mod.py`（安装/启用）、`scripts/hoi4_lint.py`（语法）、`scripts/errorlog_triage.py`（日志分类）。
- 内容校验：`scripts/tech_tree_audit.py`（科技挂载链）、`scripts/tech_folder_available.py`（folder 可用性）、`scripts/item_sprite_check.py`（sprite/贴图）、`scripts/font_audit.py`（字体）。
- 表现与模型：`scripts/dds_helper.py`（DDS 生成/检查）、`scripts/tank_designer_probe.py` 与 `tank_designer_layout.py`（设计器槽位）、`scripts/tech_icon_import.py`（图标批量导入）。
- 基础库：`scripts/pdx_parser.py`（读 pdx 文本）、`scripts/_paths.py`（目录探测）、`scripts/build_reference.py`（从游戏文件重建参考表）。

## 常见报错速查（全局）

| 关键字 | 原因 | 修法 |
|---|---|---|
| `Invalid Scope, supported: Country, provided: None` | 效果/触发作用域不匹配 | 查该条 Supported Scopes；用 `TAG = { }` / `<state_id> = { }` 切 scope |
| `Unknown effect-type` / `Unknown trigger-type` | 拼错，或该版本没有 | 对照游戏 `documentation/` 与真实用例；wiki 可能滞后 |
| `Unknown modifier` | 修正名拼错 | grep 原版同名字段的确切拼法 |
| `Unexpected token` | 括号/引号/字段语法错 | 跑 `hoi4_lint.py`；`.mod` 用 `picture=` |
| `Found no grid box for tech %s` | 科技没有对应 gridboxtype | 补 `<root>_tree` 的 gridbox 与 item 模板（见 `90_case-studies/tech-tree-gridbox.md`） |
| 图标空白 / 黑块 | sprite 未注册、贴图缺失、DDS 头不对 | 先 `dds_helper.py check`，再查 sprite 是否在 `interface/` 注册 |
| 中文显示方框 | 字体缺中文覆盖 | 换/补有中文覆盖的字体 |

---
title: 环境、目录结构与加载机制
domain: 00_start
scope: project
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - launcher-settings.json
  - hoi4_rev.txt
  - code_revisions.log
  - dlc_load.json
  - wiki/Ace.html
  - Hearts of Iron IV 实际目录
---

# 00 · 环境、目录结构与加载机制

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 读完这一篇，你应该能回答：文件该放哪、谁先加载谁后加载、为什么「同名文件」会覆盖、校验和是什么、出错去哪看日志。
> 后续所有主题文档都默认你已经理解本篇的「两个根目录」和「加载顺序」。

## 1. 本机实测环境（2026-10-26）

| 项目 | 值 |
|---|---|
| 游戏 | Hearts of Iron IV — **Operation Postern** |
| 版本字符串 | `1.19.4.2`（2026-11-06 复核：`launcher-settings.json` → `"version": "Operation Postern v1.19.4.2.2da5 (0bdb)"`；2026-10-26 记录为 `1.19.3.0`） |
| 源码修订 | `c01a3d507f10bd8c713e88234de69ca110618138`（`hoi4_rev.txt` / `logs/code_revisions.log`） |
| Steam AppID | `394360`（`steam_appid.txt`） |
| 游戏根目录 | `<GAME_DIR>` |
| 玩家数据目录 | `<USER_DIR>` |
| 当前语言设置 | `l_simp_chinese`（`pdx_settings.txt` → `System.language`） |
| 渲染设置 | `dx11`、`borderless_fullscreen`、`3840x2160` |

已安装内容（影响可用脚本特性）：

- `dlc/`：**43** 个 DLC 目录（编号 `dlc001` … `dlc052`，中间有跳号）；**只装资产**（`gfx/`、`interface/`、`music/`、`sound/`、`portraits/`），DLC 脚本在主树用 `has_dlc` 门控（实证见 [mod-structure.md](mod-structure.md) §4）
- `integrated_dlc/`：4 个**所有玩家都有**的整合 DLC —— Together for Victory、Death or Dishonor、Waking the Tiger、Man the Guns
- 判断某功能是否可用：`has_dlc = "Man the Guns"`（trigger）；Mod 的 `dependencies` 里写 DLC 名不会阻止加载，只影响启动器提示。

> 经验：写 Mod 时尽量**不依赖 DLC**。需要 DLC 内容时用 `has_dlc` 做条件分支，并在 `descriptor.mod`/README 里写明。

## 2. 两个根目录（最容易搞混的第一件事）

### 2.1 游戏根目录（只读！）

`<GAME_DIR>`

这是 Paradox 发布的全部**原版内容**。升级游戏会整目录替换，所以**永远不要直接改这里**（改了也会被 Steam 校验/更新覆盖）。

顶层结构：

| 目录/文件 | 作用 |
|---|---|
| `common/` | 绝大多数「定义」：国家、国策、事件内容之外的静态数据、AI、装备、科技、修正……（见 §4） |
| `history/` | 开局历史：`countries/`（国家初始政治/科技/理念/OOB 引用）、`states/`（州归属/建筑/人口）、`units/`（开局部队）、`general/`（将领） |
| `events/` | 事件文件（`*.txt`），按 `namespace` 组织 |
| `map/` | 地图数据：省份位图、州边界、战略区、补给区、地形、河流、铁路……（见 §5） |
| `common/national_focus/` | 国策树 |
| `common/decisions/` | 决议与决议类别 |
| `common/ideas/` | 国家精神/理念 |
| `common/characters/` | 角色（领袖、顾问、将领） |
| `interface/` | `.gui` 界面布局 + `.gfx` 精灵定义（**图标、肖像、旗帜都在这里注册**） |
| `gfx/` | 实际贴图/模型/字体/粒子等资源文件 |
| `localisation/` | 本地化 `*.yml`，按语言分目录 |
| `sound/`、`music/` | 音效 `.asset` 与音乐 `.ogg` |
| `documentation/` | **官方脚本参考（Markdown）**：effects/triggers/modifiers/变量/本地化格式/控制台命令，本机自带，优先于网上 wiki |
| `wiki/` | 离线 wiki HTML（可能滞后） |
| `tests/` | 官方 AI/场景测试脚本（`tests/*.txt`），可读性一般 |
| `tools/` | Nudge（地图微调）、profiler 可视化等开发工具 |
| `dlc/`、`integrated_dlc/` | DLC 的**资产**（`gfx/`、`interface/`、`music/`、`sound/`、`portraits/`）；**不含 `common/`、`events/`、`history/`**——DLC 脚本写在主树里由 `has_dlc` 门控（见 [mod-structure.md](mod-structure.md) §4） |
| `pdx_launcher/`、`cef/`、`browser/` | 启动器与内嵌浏览器运行时，与 Mod 无关 |
| `hoi4.exe`、`launcher-settings.json` | 可执行文件与启动器配置（调试启动参数在这里） |

### 2.2 玩家数据目录（可读写，Mod 的「家」）

`<USER_DIR>`

| 路径 | 作用 |
|---|---|
| `mod/` | **本地 Mod 安装处**：每个 Mod 一个子目录 + 一个同名 `.mod` 描述文件 |
| `mod/*.mod` | Mod 描述文件（启动器扫描这里来列出 Mod） |
| `save games/` | 存档 |
| `logs/` | **排错核心**：`error.log`（脚本错误）、`game.log`（加载流程）、`code_revisions.log`（版本）、`ai.log` 等 |
| `dlc_load.json` | 当前启用的 Mod 与禁用的 DLC（启动器写） |
| `settings.txt` / `pdx_settings.txt` | 游戏与图形设置（语言在 `pdx_settings.txt`） |
| `launcher-v2.sqlite`、`playsets_backup/` | 启动器 playset（Mod 组合）数据库 |
| `crashes/`、`exceptions/`、`dumps/` | 崩溃与异常转储 |

> Steam 创意工坊的 Mod 不在 `mod/` 里：内容在 `<WORKSHOP_DIR>\<workshop_id>`，而 `mod/ugc_<id>.mod` 只是指向它的描述文件（`path` 字段指向工坊目录）。本地开发时你写的也是同样结构，只是 `path` 指向自己的工作目录。

## 3. Mod 描述文件：`.mod` 与 `descriptor.mod`

一个可被启动器识别的 Mod 需要**两个几乎相同**的文件：

1. `.../mod/my_mod.mod` —— 启动器扫描的描述文件，**必须含 `path`**；
2. `.../mod/my_mod/descriptor.mod` —— Mod 内容根目录里的描述文件（发布到创意工坊/打包时用），**不含 `path`**。

原版真实例子（Kaiserreich Music）：

```pdx
name="Kaiserreich Music"
dependencies={
	"Kaiserreich"
}
tags={
	"Sound"
}
picture="KR.jpg"
version="1.7.*"
supported_version="1.19.*"
path="<WORKSHOP_DIR>/1360299796"
remote_file_id="1360299796"
```

字段含义：

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | 是 | 显示名（唯一性由启动器保证，重名会警告） |
| `path` | `.mod` 必填 | 内容根目录，**正斜杠**，Windows 路径也可；指向你开发目录即可 |
| `supported_version` | 是 | 如 `"1.19.*"` 或 `"1.19.4.2"`；只是启动器兼容提示，版本不符仍可强行启用 |
| `version` | 否 | Mod 自己的版本号（与 supported_version 不同） |
| `tags` | 否 | 创意工坊分类：`"Historical" "Balance" "Gameplay" "Graphics" "National Focuses" "Events" "Technologies" "Translation" "Utilities" "Sound" "Alternative History" "Ideologies"` 等 |
| `picture` | 否 | 缩略图文件名（放在 Mod 根目录；创意工坊上传用，建议 512×512 JPG/PNG） |
| `dependencies` | 否 | 依赖的 Mod 名（启动器会提示，但**不会自动启用**） |
| `replace_path` | 否 | **整目录替换**（见 §6.2），总转换 Mod 大量使用 |
| `remote_file_id` | 工坊 | 创意工坊 ID，本地 Mod 不要写 |

## 4. `common/` 全景（按功能分组）

`common/` 下有 100+ 个目录/文件，是 Mod 工作量最大的地方。按用途分组（1.19.3 实测存在）：

**内容与政治**
`characters/`（角色）、`country_leader/`（领袖特质）、`countries/`（国家颜色/图标等）、`country_tags/`、`country_tag_aliases/`、`bookmarks/`（开局书签）、`ideologies/`、`ideas/`、`idea_tags/`、`decisions/`（含 `categories/`）、`national_focus/`、`events/`（在根目录 `events/`）、`continuous_focus/`、`factions/`、`wargoals/`、`peace_conference/`、`autonomous_states/`、`occupation_laws/`、`resistance_activity/`、`resistance_compliance_modifiers/`、`bop/`（权力平衡）、`opinion_modifiers/`、`scripted_diplomatic_actions/`

**军事**
`units/`（营/支援连/单位定义、命名）、`equipment_groups/`、`technologies/`、`technology_sharing/`、`technology_tags/`、`doctrines/`、`abilities/`、`aces/`、`unit_leader/`、`unit_medals/`、`unit_tags/`、`medals/`、`ribbons/`、`raids/`、`operations/`（含 `operation_tokens`、`operation_phases`）、`intelligence_agencies/`、`intelligence_agency_upgrades/`、`military_industrial_organization/`（MIO）、`special_projects/`、`scientist_traits/`、`combat_tactics.txt`、`acclimatation.txt`、`weather.txt`

**地图与经济**
`buildings/`、`resources/`、`state_category/`、`strategic_locations/`、`terrain/`（地形修正）、`defines/`、`modifiers/`、`modifier_definitions/`、`dynamic_modifiers/`

**AI**
`ai_areas/`、`ai_equipment/`、`ai_focuses/`、`ai_navy/`、`ai_strategy/`、`ai_strategy_plans/`、`ai_templates/`、`ai_faction_theaters/`、`ai_attitudes.txt`、`ai_personalities.txt`、`difficulty_settings/`

**脚本基础设施**
`scripted_effects/`、`scripted_triggers/`、`scripted_guis/`、`scripted_localisation/`、`on_actions/`、`game_rules/`、`collections/`、`script_constants/`、`script_enums.txt`、`mtth/`、`modifiers/`、`triggered_modifiers.txt`、`event_modifiers.txt`、`dynamic_modifiers/`、`synchronized_dynamic_tokens/`

**表现**
`frontend/`、`map_modes/`、`alerts.txt`、`profile_backgrounds/`、`profile_pictures/`、`focus_inlay_windows/`、`generation/`、`names/`、`scorers/`

> 每个目录的文件格式、参数、原版例子，见对应主题文档（`01_script/`、`02_content/`、`03_military/`、`04_world/`、`05_presentation/`）。

## 5. `map/` 与 `history/` 的关键文件

`map/`（25 项，实测）：

- `provinces.bmp`：省份颜色位图，**每像素颜色 = 省份 ID**（`definition.csv` 定义 RGB→省份映射）
- `definition.csv`：`省份ID;R;G;B;类型;海岸;地形;大陆;...`，改图的核心
- `default.map`：海陆/河流/湖泊/单位堆叠等全局参数
- `heightmap.bmp`、`terrain.bmp`、`rivers.bmp`、`trees.bmp`：地形渲染
- `strategicregions/`、`supplyareas/`：战略区、补给区定义
- `terrain/`、`continent.txt`、`adjacencies.csv`：地形类别、大陆、跨海连接
- `buildings.txt`、`positions.txt`、`railways.txt`、`supply_nodes.txt`、`unitstacks.txt`、`cities.txt`：建筑/单位在省内的位置与铁路
- `seasons.txt`、`weatherpositions.txt`、`ambient_object.txt`

`history/`（4 个子目录，实测）：

- `countries/TAG.txt`：开局政治（`set_politics`）、科技、理念、国家精神、部队经验、初始研究
- `states/<id>.txt`：州归属、核心、人口、建筑、资源、胜利点（`history/states/` 下按州 ID 命名）
- `units/TAG_1936.txt`：开局部队与舰队（`instant_effect`、`division_template`、`set_technology` 等）
- `general/TAG.txt`：开局将领

> ⚠️ 这些是「历史数据」，不是「规则」。改数值前先确认对应字段是否有 `common/` 里的定义支撑。

## 6. 加载顺序与覆盖语义（Mod 兼容性的根源）

启动游戏时内容按以下顺序合并：

```
原版基础内容
  → 整合 DLC（integrated_dlc/）
  → 已购买 DLC（dlc/，按 DLC 加载）
  → Mod（按 dlc_load.json 中 enabled_mods 的顺序，后面的覆盖前面的）
```

### 6.1 三种「覆盖」

1. **同名路径文件整体替换**
   Mod 里有 `common/ideas/GER.txt`，则原版 `common/ideas/GER.txt` **整个文件被忽略**，而不是合并。
   → 后果：原版后续更新新增的条目会丢失；两个 Mod 都改同一文件时只有一个生效。
   → 推荐：**新建文件**（如 `common/ideas/99_my_mod_ideas.txt`），而不是复制整份原版文件。

2. **同 ID 定义覆盖/合并**
   同一个 `focus`/`idea`/`decision`/`character`/`technology` 的 ID 在多个文件中重复时，通常由加载顺序靠后的定义胜出（部分类型会合并子块）。
   → 想「修改」一个原版国策/理念：可以只定义同 ID 的最小内容（但行为随类型不同，必须实测）。
   → 想「新增」：用唯一 ID（建议 `YOURTAG_` 前缀）。

3. **`replace_path` 整目录替换**
   `.mod` 里 `replace_path="common/ideas"` 表示：**原版 `common/ideas/` 整个目录不加载**，只用 Mod 的。总转换 Mod（Kaiserreich 等）会列出几十条 `replace_path`。
   → 危险：一条写错会丢掉整个子系统；兼容性极差（不能与其他大改 Mod 共存）。
   → 只在做「总转换/大型 overhaul」时使用，并逐条验证。

### 6.2 加载顺序在哪里看/改

- 玩家数据目录的 `dlc_load.json`：
  ```json
  {"enabled_mods":["mod/ugc_2977114459.mod","mod/BlackIce_Tech_Tree.mod"],"disabled_dlcs":[]}
  ```
  数组顺序即加载顺序，后者覆盖前者。（⚠️ 已实证部分：`dlc_load.json` 的数组顺序 = 启动器 playset 的 `position` 升序；但**引擎是否按此顺序决定覆盖优先级官方无文档**，详见 [load-order-and-override.md](load-order-and-override.md) §5。）
- 启动器 playset（`launcher-v2.sqlite` / `playsets_backup/`）管理同一份启用列表。
- **Mod 之间不应该互相写文件**；需要共享内容时用 `dependencies`（仅提示）+ 明确文档。

### 6.3 校验和（checksum）

- 主菜单/多人界面显示的 checksum 由游戏脚本内容决定；**启用 Mod 会改变 checksum**。
- 多人联机要求所有玩家**内容一致**（同版本 + 同 Mod 组合）；不一致会提示 checksum 不匹配。
- 控制台 `dump_checksum` 可打印当前校验和（命令以 `documentation/console_commands_documentation.md` 为准）；`compare_to_last_checksum` 比较。
- 开发期单机不受影响；**发布前**用「仅启用自己 Mod」的干净 playset 验证一次。

## 7. 启动参数、控制台与日志

### 7.1 调试模式

`launcher-settings.json` 里已经定义了调试启动项：

```json
"exePath": "./hoi4.exe",
"exeArgs": [ "-gdpr-compliant", "-debug_mode" ]
```

- `-debug_mode`：启用调试控制台与额外调试信息（推荐开发时一直开）。
- 控制台默认按键：`~` 或 `^`（视键盘布局）；`-debug_mode` 下功能最全。
- 常用：`debug`、`help`、`event <id>`、`focus.autocomplete`、`add_ideas`、`annex`、`tag`、`observe`、`ai`、`debug_events`、`dump_checksum`、`reload` 类命令。完整列表见 `documentation/console_commands_documentation.md`（386 个命令 + 44 个可调参数）。

### 7.2 日志：排错的第一现场

位置：`<USER_DIR>\logs\`

| 文件 | 用途 |
|---|---|
| `error.log` | **脚本/资源错误**。格式：`[时间][游戏内日期][文件:行]: 消息` |
| `game.log` | 加载流程（defines、省份数、历史执行、进入单人游戏） |
| `code_revisions.log` | 游戏版本哈希（核对版本用） |
| `ai.log` / `ai_trace.log` | AI 行为 |
| `memory.log` | 内存/性能采样 |

本机真实样本（2026-10-26 运行）：

```
[18:24:32][1936.01.01.12][trigger.cpp:460]: common/technology_tags/00_technology.txt:355: has_country_flag: Invalid Scope, supported: Country, provided: None
[18:24:30][1936.01.01.12][lexer.cpp:251]: Tried to get dynamic token that does not exist: nuclear_folder
[18:23:49][1936.01.01.12][effectbase.cpp:1783]: Something went wrong with the Conflict Risk stuff
```

读法：

- 第 3 段 `[文件:行]` 是**出错位置**；`Invalid Scope` 说明作用域不对（详见 `01_script/scopes.md`）。
- `Tried to get dynamic token` / `dynamic token ... can cause OOS`：脚本里用了未注册的动态 token（本地化/脚本变量拼 key），联机会 OOS。
- `Something went wrong with the Conflict Risk stuff` 这类是**游戏内部警告**，不一定是你的 Mod 造成的；用「空 Mod」对照法确认。
- 日志会**追加**（不是每次清空），排查前建议先记录文件大小/备份，或删掉后重启游戏再读。

### 7.3 排查方法论（增量二分）

1. 只启用「原版 + 你的 Mod」，看 error.log 是否还有目标错误 → 区分「你造成的」与「环境/DLC 造成的」。
2. 把 Mod 内容按目录二分（先只放 `common/`，再 `events/`……）定位。
3. 用 `-debug_mode` 进游戏，控制台 `event <id>`、`focus.autocomplete` 快速触发目标内容。
4. 脚本改动必须重启游戏（没有脚本热重载；界面/贴图有少数 `reload` 类命令，但不完整）。
5. 错误修完后，用我们的静态校验器做回归：
   `python $SKILL/scripts/hoi4_lint.py <PROJECT_DIR>`

## 8. 性能常识（写 Mod 前就该知道）

HOI4 的脚本是**每个 tick 对所有相关对象求值**的，写错位置会产生成倍开销：

- `available`/`visible`/`trigger` 会被**频繁求值**（决议类别、国策可用性、事件触发、scripted GUI）。把昂贵计算（`every_` 迭代、`count`、大量 `any_`）放进高频触发器会显著拖慢。
- `on_actions` 里的 `on_daily`/`on_monthly`/`on_yearly` 是最常见性能陷阱；能用「事件 + MTTH」就不要用每日 on_action 做全图轮询。
- `mean_time_to_happen` 的 `base` 越小越频繁；`modifier` 叠加不当会让事件每个月炸一次。
- scripted GUI 的 `properties`/`triggers` 每帧或每次刷新求值；不要在里面做全图遍历。
- 大量 `scripted_effects` 嵌套会增加调用开销；适度使用。
- 开局历史（`history/`）只在加载时执行，不影响运行时性能；但**过多的开局单位/建筑**会拖慢加载与 AI。
- 基准对比方法：同一存档、同一操作序列，看 `memory.log` 与游戏内速度；修改前后各测一次。

## 9. 工具链（本项目自带）

| 工具 | 用途 |
|---|---|
| `documentation/*.md` | 官方 1.19.x 脚本参考（最权威；字段释义以它为准） |
| 本地速查表（可选） | 用 `$SKILL/scripts/build_reference.py` 从官方 `documentation/*.md` 生成本地 JSON 索引（effects 553 / triggers 596 / modifiers 764 / console 430）；产物在本地生成，不随技能分发 |
| `$SKILL/scripts/pdx_parser.py` | PDX 脚本解析器（括号、作用域、ID 提取） |
| `$SKILL/scripts/hoi4_lint.py` | Mod 静态校验：语法、本地化、GFX、ID 冲突、`.mod` 结构 |
| `$SKILL/scripts/build_reference.py` | 从官方 `documentation/*.md` 重新生成本地 JSON 速查表 |
| `$SKILL/scripts/install_mod.py` | 把 `example_mods/` 安装到玩家 Mod 目录并启用（需退出游戏后运行） |
| Nudge（游戏内调试工具） | `-debug_mode` 下的地图/建筑位置微调模式，配合 `tools/` 里的导出设置使用 |

## 10. 1.19.x 实测补充：官方文档也会滞后

`documentation/*.md` 是最权威的**脚本参考**，但它不是全集。以下为 1.19.3 / 1.19.4 实测结论（差异清单以本机 `documentation/` 与游戏文件实测为准）：

- **文档未收录但仍可用的关键字**：`unit_modifiers`（替代已移除的 `add_temporary_buff_to_units`）、`is_fighting_in_strategic_region`（原版 `common/on_actions/14_sea_on_actions.txt` 有用例）、`is_deployed`、集合算子 `is_core_of` 等。
- **冲突时以游戏文件为准**：文档没写 ≠ 不可用；文档写了也可能过时（例如 wiki 仍写 `-debug`，本机实际参数是 `-debug_mode`）。
- **`.mod` 字段名**：主流写法是 `picture=`，不是 `thumbnail=`（写错会报 `Unexpected token`）。⚠️ 本机存在反例：`<USER_DIR>/mod/ugc_3243611664.mod:9` 用 `thumbnail="thumbnail.png"` 且该 mod 已被启动器收录 ⇒ 至少不是致命错误；新写 mod 仍用 `picture=`，详见 [mod-structure.md](mod-structure.md) §2.4。
- **`supported_version`**：接受 `1.19.*`、`1.19.4.2` 这类形式（只是启动器兼容提示，**不是运行门槛**）；写 `*` / `1.*` 会报 `Invalid supported_version`。
- **路径建议纯 ASCII**：本工作区路径含中文（`…\钢铁雄心4`），不要把 `.mod` 的 `path` 直接指向它；用 `$SKILL/scripts/install_mod.py` 复制安装到玩家 `mod/` 目录（路径为 ASCII），不要用 `--link`。
- **error.log 噪声**：本机 14664 行错误里 >95% 是原版自身（dynamic token、script enum、unrecognized upgrade、division name 等）。排查时**只 grep 自己 Mod 的文件名/ID**，否则会被淹没。

## 11. 从零到一个能跑的 Mod：10 步检查清单

1. 建目录 `MyMod/`，写 `MyMod/descriptor.mod`（name、supported_version、tags）。
2. 在 `<USER_DIR>/mod/MyMod.mod` 写 `path="mod/MyMod"`（相对 `<USER_DIR>`；也可用纯 ASCII 绝对路径）。
3. 加最小内容：`common/ideas/` 一条理念 + `localisation/english/` 对应 key（UTF-8 **BOM**）。
4. 启动器启用 Mod → 进游戏看理念是否出现、error.log 是否干净。
5. 依次加国策 → 事件 → 决议 → 角色，每加一类就重启验证一次（不要一次写 2000 行）。
6. 本地化同时做 `english` 与 `simp_chinese`；中文文件必须带 BOM。
7. 所有图标先引用原版已存在的 `GFX_` 精灵，最后再替换为自绘 DDS。
8. 跑 `python $SKILL/scripts/hoi4_lint.py <PROJECT_DIR>`，修到 0 error。
9. 开新档（不要用旧存档测试新增开局内容），用控制台触发关键事件。
10. 发布前：干净 playset 只启用本 Mod + 依赖，确认校验和、无 error.log 新错误。

## 12. 常见错误 / 自检清单

- [ ] 我把文件写进了**游戏根目录**（错），应该在玩家数据目录的 `mod/` 或自己的开发目录。
- [ ] `.mod` 里 `path` 指向错误（路径含反斜杠没转义、指向了 `descriptor.mod` 而非目录）。
- [ ] 我覆盖了原版同名文件，但只想要「加一条」→ 应该新建文件。
- [ ] `replace_path` 写错目录名，导致整个系统消失。
- [ ] 本地化文件没有 BOM / 目录名与 `l_english` 声明不一致 → 中文全变问号或乱码。
- [ ] 图标引用了不存在的 `GFX_` 名 → 图标空白/黑块（用 lint 查）。
- [ ] 用旧存档测试「开局才有」的内容 → 永远看不到。
- [ ] error.log 里大量错误其实来自其他 Mod（用干净 playset 对照）。
- [ ] 联机前没检查 checksum / Mod 组合。

---

**下一步阅读**：[mod-structure.md](mod-structure.md)（mod 长什么样、能覆盖哪些域）→ [load-order-and-override.md](load-order-and-override.md)（三种覆盖机制与加载顺序的实证边界）→ `../01_script/_index.md`（脚本语言）→ `../02_content/_index.md`（从国策开始做内容）。

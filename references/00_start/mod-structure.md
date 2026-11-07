---
title: Mod 结构与描述文件（目录 / descriptor / supported_version / DLC / 可覆盖域）
domain: 00_start
scope: any
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - documentation/（12 个 *.md 全量 grep：无 mod 结构、无 replace_path、无 load order 描述）
  - launcher-settings.json
  - <USER_DIR>/mod/*.mod（29 个描述文件实测）
  - <WORKSHOP_DIR>/*/descriptor.mod（23 个工坊 mod 实测）
  - dlc/、integrated_dlc/（43 + 4 个目录逐个清点）
  - common/*（has_dlc 分布统计）
  - audit/game-survey.md §7–§8（本机只读扫描产物）
  - 知识库母本 `06_workflow/project_setup`（同步后为 `06_workflow/setup.md`）
---

# Mod 结构与描述文件

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 1.19.3 / 1.19.4）

> 一句话定位：一个 mod = **一个描述文件**（告诉启动器"内容在哪"）+ **一个与游戏根目录同构的内容树**。搞清这两半，`supported_version` / `has_dlc` / `replace_path` 这些"看起来像配置"的东西才有位置可放。

本文只讲**结构**；三种覆盖机制（replace_path / 同路径整文件覆盖 / 同 ID 覆盖）的行为与风险见 [load-order-and-override.md](load-order-and-override.md)；本机路径与目录全景见 [environment.md](environment.md)。

## 1. 一个完整 mod 的目录结构

```
<USER_DIR>/                        ← 玩家数据目录
└─ mod/
   ├─ my_mod.mod                   ← ① 启动器扫描的描述文件（唯一必须写 path 的地方）
   └─ my_mod/                      ← ② 内容根：与游戏根目录同构
      ├─ descriptor.mod            ← ③ 随 mod 分发的描述文件（不写 path）
      ├─ thumbnail.png             ← ④ 封面（创意工坊/Paradox Mods 用）
      ├─ common/                   ← 游戏系统定义（国策/科技/理念/决议/on_actions/…）
      ├─ events/
      ├─ history/
      ├─ localisation/
      │  ├─ english/*.yml
      │  └─ simp_chinese/*.yml
      ├─ interface/                ← *.gui / *.gfx
      ├─ gfx/                      ← DDS / sprites / models
      └─ README.md                ← 非游戏目录，引擎不读
```

三件套缺一不可：**`.mod` + 本体目录 + `descriptor.mod`**（``06_workflow/setup.md`（母本 :32-33）`）。本机工坊 23 个 mod **全部**带 `descriptor.mod`（`<WORKSHOP_DIR>/*/descriptor.mod` 实测存在率 23/23），本地 29 个 `.mod` 描述文件全部指向同构目录。

关键约束（`environment.md` §3、`06_workflow/setup.md`（母本）:80-95`）：

- `path` **只用 `/`**，反斜杠会被当转义符；
- `path` **纯 ASCII**（含中文 → 启动器能看到名字，但内容不加载）；
- `path` 指向**直接包含 `common/` 的那一层**，不要多套一层；
- 相对路径以 `<USER_DIR>` 为基准（`path = "mod/my_mod"`）；绝对路径也支持（本机 `ugc_1360299796.mod` 用 `path="<WORKSHOP_DIR>/1360299796"`）。

## 2. 描述文件：`.mod` 与 `descriptor.mod`

### 2.1 两个文件的分工

| 文件 | 位置 | 谁读 | `path` | 用途 |
|---|---|---|---|---|
| `my_mod.mod` | `<USER_DIR>/mod/my_mod.mod` | 启动器（扫描 `mod/` 下所有 `*.mod`） | **必写** | 告诉启动器这个 mod 的内容在哪 |
| `descriptor.mod` | `<CONTENT_ROOT>/descriptor.mod` | 引擎/上传流程（启动器主要读上一份） | 本地开发**不写** | 随 mod 一起分发，让别处也能识别；上传创意工坊时被读取 |

> 工坊 mod 的 `descriptor.mod` 里**经常带着原作者本机的 `path`**（实例：`<WORKSHOP_DIR>/1521695605/descriptor.mod` 末段有一个指向**原作者本机**的 `path="<ABS_PATH>/Kaiserreich"`）。这说明 `descriptor.mod` 里的 `path` 不是"给本机用"的唯一依据——本机生效的 `path` 在 `<USER_DIR>/mod/*.mod` 里。自己开发时仍建议 `descriptor.mod` 不写 `path`，避免把绝对路径带进上传包。

### 2.2 字段表（按真实文件核对）

| 字段 | 必填 | 语义 | 本机实例（行号） |
|---|---|---|---|
| `name` | 是 | 显示名；**全局唯一**（重名只有先加载者生效） | `hist_tech_trees.mod:6`、`ugc_1137372539.mod:73` |
| `path` | `.mod` 必填 | 内容根目录（`/` + ASCII） | `hist_tech_trees.mod:9`、`ugc_3243611664.mod:11` |
| `supported_version` | 是 | **启动器兼容提示**，不是运行门槛（见 §3） | `hist_tech_trees.mod:8`、`ugc_1521695605.mod:84` |
| `version` | 否 | mod 自己的版本号，与 `supported_version` 无关 | `hist_tech_trees.mod:1`（`"0.3"`）、`ugc_1137372539.mod:66`（`"12.1.0"`） |
| `tags` | 否 | 创意工坊分类（`Historical`/`Balance`/`Gameplay`/`Graphics`/`National Focuses`/`Events`/`Technologies`/`Translation`/`Utilities`/`Sound`/`Alternative History`/`Ideologies`…） | `hist_tech_trees.mod:2-5`、`ugc_3243611664.mod:4-6`（`Translation`） |
| `picture` | 否 | 封面文件名，放在内容根目录下 | `hist_tech_trees.mod:7`（`picture="thumbnail.png"`）、`ugc_1521695605.mod:82`（`picture="KR.jpg"`） |
| `dependencies` | 否 | 依赖的 mod **name**（逐字符一致）；启动器只提示，**不自动启用** | `ugc_1360299796.mod:1-3`、`ugc_3243611664.mod:1-3` |
| `replace_path` | 否 | **整目录替换**，可重复多行；两个描述文件都要写（§2.3） | `ugc_1521695605.mod:2-75`（74 条） |
| `remote_file_id` | 工坊 | 创意工坊 ID；本地开发不要手写 | `ugc_1137372539.mod:76`、`The road to 56 CN.mod:20` |
| `user_dir` | 否 | 改存档子目录，防串档；**本机 29 个 `.mod` 无一使用** ⇒ 语义未实测 | — |
| `thumbnail` | ？ | 见 §2.4：疑似与 `picture` 等价或至少不致命 | `ugc_3243611664.mod:9`、同 mod 的 `descriptor.mod` |

### 2.3 `replace_path` 要写两遍（实证）

同一个 mod 的 `descriptor.mod` 与 `<USER_DIR>/mod/*.mod` 里 `replace_path` **条数完全一致**：

| mod | `descriptor.mod` | 本地 `.mod` |
|---|---|---|
| Kaiserreich（1521695605） | 74 条 | 74 条 |
| BlackICE（1137372539） | 65 条 | 65 条 |
| The road to 56 CN（2129897125） | 3 条 | 3 条 |

⇒ `06_workflow/setup.md`（母本）:76`「两个 `.mod` 都要写」被真实数据支持。只写一份时哪一份生效**未确认**，按惯例两份都写。

`descriptor.mod` 的编码要求与 `.yml` **相反**：**不能带 UTF-8 BOM**（`06_workflow/setup.md`（母本）:68-69`）；`.yml` 本地化则**必须有 BOM**。

### 2.4 `picture` 还是 `thumbnail`？（存疑，勿当铁律）

`environment.md` §10 记录过「字段名是 `picture=`，不是 `thumbnail=`（写错会报 `Unexpected token`）」。但本机存在反例：

- `<USER_DIR>/mod/ugc_3243611664.mod:9` 与 `<WORKSHOP_DIR>/3243611664/descriptor.mod` **两个文件都用 `thumbnail="thumbnail.png"`**，且该 mod 已被启动器收录（`mod/` 下有对应 `.mod`）。

⇒ **结论降级为"未确认"**：`thumbnail=` 至少没有让该 mod 无法加载；是否只是被启动器忽略、是否有日志告警，本任务未启动启动器复测。**新写 mod 一律用 `picture=`**（主流写法 + 有 20+ 个工坊 mod 支撑），但不必把 `thumbnail=` 当成硬错误去"修"。此项已列入审计报告待查。

## 3. `supported_version` 的语义

### 3.1 它是"启动器兼容提示"，不是"运行门槛"

本机版本 1.19.4.2（`launcher-settings.json:5` `"rawVersion": "1.19.4.2"`），同时挂着以下声明的 mod 且都能启用：

| mod | 声明 | 本机版本 | 结果 |
|---|---|---|---|
| BlackICE（1137372539） | `"1.19.2.0"` | 1.19.4.2 | 可加载（旧声明不阻碍） |
| The road to 56 CN | `"1.19.3.0"` | 1.19.4.2 | 可加载 |
| Kaiserreich（1521695605） | `"1.19.4.*"` | 1.19.4.2 | 可加载 |
| hist_tech_trees | `"1.19.*"` | 1.19.4.2 | 可加载 |

⇒ **不是"只能在该版本运行"**，也不是精确版本匹配；版本不符最多在启动器里被标为"旧"。

### 3.2 合法写法

| 写法 | 合法 | 依据 |
|---|---|---|
| `"1.19.*"` | ✅ | 推荐写法；`hist_tech_trees.mod:8` |
| `"1.19.4.*"` | ✅ | `ugc_1521695605.mod:84` |
| `"1.19.4.2"` | ✅ | `ugc_3243611664.mod:10` |
| `"1.19.2.0"` | ✅（小版本旧，不报错） | `ugc_1137372539.mod:74` |
| `"1.12.14"` | ✅（旧版本号，启动器标旧） | `06_workflow/setup.md`（母本）:105` |
| `"1.*"` / `"*"` / `"1.*.*"` | ❌ `Invalid supported_version` | `06_workflow/setup.md`（母本）:106-108`（5 / 1 / 1 个 mod 实测） |

**规则**：通配符**只能在最后一段**，且至少要写 `大版本.小版本`。**推荐 `"1.19.*"`**——1.19.x 小补丁不用跟着改。

### 3.3 与 `version` 的区别

- `supported_version`：给**启动器**看的"我能跑在哪个游戏版本"。
- `version`：**mod 自己的**版本号（`"0.3"`、`"1.7"`、`"12.1.0"` 都合法，格式自由）。

## 4. DLC 内容装在哪：默认只装资产，脚本留在主树用 `has_dlc` 门控

这是本机只读扫描得出的**结构性事实**，对"我的 mod 要不要依赖 DLC / 怎么兼容 DLC"有直接指导意义。

### 4.1 实证：`dlc/` 与 `integrated_dlc/` 里没有脚本

逐个清点（2026-11-06，只读）：

| 目录 | 子目录数 | 顶层内容 |
|---|---|---|
| `<GAME_DIR>/dlc/` | **43** | `gfx/`、`interface/`、`music/`、`sound/`、`portraits/`、`*.dlc`、`thumbnail.png`、2 个 `.zip` |
| `<GAME_DIR>/integrated_dlc/` | **4**（TfV / DoD / WtT / MtG） | `gfx/`、`interface/`、`music/`、`sound/`、`portraits/` |

- 43 个 `dlc/` 子目录里**没有一个**含 `common/`、`events/`、`history/`、`decisions/`、`national_focus/`；
- 两个压缩包同样只有资产：`dlc/dlc003_rocket_launcher_unit_pack/dlc003.zip`（36 项，全 `gfx/`）、`dlc/dlc005_heavy_cruisers_unit_pack/dlc005.zip`（1 项）。

⇒ **DLC 的脚本内容不与资产同目录分发**；国策/科技/事件的 DLC 分支写在**主树**的普通文件里，运行时按"是否拥有该 DLC"分叉。

### 4.2 门控方式：`has_dlc`

主树里 `has_dlc` 出现得极其密集（本机统计，`common/` + `events/` 下含 `has_dlc` 的文件数 / 总文件数）：

| 目录 | 文件数 | 含 `has_dlc` |
|---|---|---|
| `common/national_focus/` | 81 | **77** |
| `common/decisions/` | 146 | 87 |
| `common/characters/` | 232 | 51 |
| `common/ideas/` | 213 | 57 |
| `common/military_industrial_organization/` | 60 | 50 |
| `events/` | 128 | 68 |
| `common/special_projects/` | 13 | 6 |

写法（trigger，可直接抄进国策 `available` / 事件 `trigger` / 决议 `allowed`）：

```pdx
has_dlc = "No Step Back"          # DLC 显示名，逐字符一致
```

本机主树里出现频次最高的 `has_dlc` 值（`common/` 全量统计，前 16）：

| 值 | 次数 |
|---|---|
| `Arms Against Tyranny` | 1051 |
| `No Compromise, No Surrender` | 943 |
| `La Resistance` | 855 |
| `Gotterdammerung` | 686 |
| `Man the Guns` | 629 |
| `By Blood Alone` | 596 |
| `Battle for the Bosporus` | 559 |
| `Thunder at Our Gates` | 511 |
| `No Step Back` | 462 |
| `Graveyard of Empires` | 381 |
| `Trial of Allegiance` | 347 |
| `Together for Victory` | 249 |
| `Peace For Our Time` | 188 |
| `Waking the Tiger` | 185 |
| `Death or Dishonor` | 147 |
| `Poland: United and Ready` | 40 |

### 4.3 对写 mod 的三条直接含义

1. **DLC 兼容靠 `has_dlc`，不靠"把文件塞进 `dlc/`"**。`dlc/` 是发行方目录，mod 不要往里写；要么在主树里用 `has_dlc` 分叉，要么整段内容只在有 DLC 时生效。
2. **`integrated_dlc/` 是"已被吸收进主树的旧 DLC 资产目录"**，它参与加载、可被 mod 同名路径覆盖（本机 3 个 mod 往 `integrated_dlc/dlc022_waking_the_tiger/interface/…` 这类路径下叠加过文件，见 `game-survey.md` §7.6）。这属于高级玩法，非必要不要碰。
3. **DLC 资产可以引用，但要在 mod 里做"缺 DLC 兜底"**：引用 DLC 独有的 `GFX_` 名时，没买 DLC 的玩家会得到空白图标（不会崩），所以图标类内容建议 `has_dlc` 分支 + 原版兜底图标。

## 5. mod 能覆盖哪些域（77 行表的速览）

完整 77 行表（域 / 游戏内路径 / 官方文档 / 典型 mod 形态 / 备注）在 `.tmp/audit/game-survey.md` §8（`:545-629`）。这里按"要不要动"分组压缩，便于先判断工作量：

| 组 | 代表域（游戏内路径） | 典型 mod 形态 |
|---|---|---|
| **地图与地理** | `map/definition.csv`、`provinces.bmp`、`heightmap.bmp`、`map/strategicregions/`、`map/supplyareas/`、`map/supply_nodes.txt`、`map/railways.txt`、`map/continent.txt`、`map/seasons.txt` | 大改必配 `replace_path="map"` 或按子目录替换 |
| **国家与历史** | `history/countries/<TAG> - <名>.txt`、`common/country_tags/00_countries.txt`、`common/country_tag_aliases/tag_aliases.txt`、`country_metadata/00_country_metadata.txt`、`history/units/*.txt`（609 个 OOB） | 加国家 = 新增 tag + 三处登记 |
| **州与人口** | `history/states/<id>-<名>.txt`、`common/state_category/*.txt`、`common/resources/00_resources.txt`、`common/buildings/00_buildings.txt` + `map/buildings.txt` | 改州常配 `replace_path="history/states"` |
| **科技与装备** | `common/technologies/*.txt`、`common/technology_tags/00_technology.txt`、`common/technology_sharing/`、`common/units/equipment/*.txt`、`common/equipment_groups/*.txt`、`common/units/*.txt`、`common/doctrines/**`、`common/combat_tactics.txt` | 改科技树两块：科技定义 + `interface/*.gui` 里的树布局 |
| **军事系统** | `common/military_industrial_organization/**`、`common/special_projects/**`、`common/scientist_traits/`、`common/raids/**`、`common/intelligence_agencies/`、`common/factions/**`、`common/unit_leader/`、`common/portraits/`（+`portraits/00_portraits.txt`） | 新增为主，覆盖需谨慎 |
| **政治与外交** | `common/national_focus/*.txt`（81 文件/69 万行）、`common/decisions/**`（147 文件/34.5 万行）、`common/ideas/*.txt`（213 文件）、`common/characters/<TAG>.txt`（233 文件）、`common/ideologies/00_ideologies.txt`、`common/wargoals/`、`common/peace_conference/**`、`common/occupation_laws/`、`common/bop/<TAG>.txt`、`common/game_rules/00_game_rules.txt` | 内容型 mod 的主战场；优先"新增文件 + 同 ID 覆盖" |
| **界面与表现** | `interface/*.gui`（280 顶层 + 14 子目录）、`interface/*.gfx`、`common/scripted_guis/`、`gfx/interface/**`、`gfx/event_pictures/**`、`gfx/flags/**`、`gfx/fonts/**`（786 文件/1.7 GB）、`gfx/models/**`、`gfx/entities/*.gfx\|*.asset`、`music/`、`sound/` | 最容易与他 mod 冲突（同路径整文件覆盖，见下一篇） |
| **本地化** | `localisation/<lang>/*_l_<lang>.yml`（`.yml` 必须 UTF-8 **BOM**） | 翻译型 mod 的机制基础：通常不改 checksum |
| **脚本基础设施** | `common/on_actions/*.txt`、`common/scripted_effects/`（52 文件/7.4 万行）、`common/scripted_triggers/`（55 文件）、`common/scripted_localisation/`、`common/collections/`、`common/script_constants/`、`common/script_enums.txt`、`common/synchronized_dynamic_tokens/`、`common/dynamic_modifiers/`、`common/modifiers/`、`common/modifier_definitions/`、`common/defines/*.lua`、`common/difficulty_settings/` | 只写 `common/` 的新增文件 + 同 ID 覆盖，几乎不需要 replace_path |

**引擎不加载的目录**（`game-survey.md` §7.6，会随 mod 一起下载但不生效）：

`scenario_tests/`、`tests/`、`descriptions/`、`documentation/`、`tools/`、`README.md`、`.git*`。

**未确认是否生效**（本机 32 个 mod 无样本）：

`wiki/`、`dlc/`、`pdx_launcher/`、`browser/`、`cef/`、`assets/`、`EmptySteamDepot/`、`soundtrack/`、`crash_reporter/`、`previewer_assets/`。

真实 mod 的顶层目录并集（32 个 mod 统计，可当"实际会长出什么"的参照）：`localisation` 28、`gfx` 24、`interface` 24、`common` 22、`music` 17、`history` 15、`events` 14、`sound` 11、`map` 10、`portraits` 10、`tutorial` 4、`scenario_tests` 3、`tests` 3、`integrated_dlc` 3、`country_metadata` 2，其余各 1。

## 6. 本机复核备忘（2026-11-06）

- 本机游戏版本已到 **1.19.4.2**（`launcher-settings.json:4-5`：`"Operation Postern v1.19.4.2.2da5 (0bdb)"`）；`environment.md` §1 表里的 `1.19.3.0` 是 2026-10-26 的旧记录。
- `<USER_DIR>/dlc_load.json` 当前内容：`{"enabled_mods":["mod/ugc_2977114459.mod","mod/hist_tech_trees.mod"],"disabled_dlcs":[]}`。
- `<USER_DIR>/mod/` 下 29 个 `.mod`；`<WORKSHOP_DIR>` 下 23 个 mod 目录（均含 `descriptor.mod`）。

## 7. 自检清单

- [ ] `.mod` 有 `path`，`descriptor.mod` 没有 `path`？
- [ ] `path` 只用 `/`、纯 ASCII、指向含 `common/` 的那层？
- [ ] `supported_version` 用 `"1.19.*"` 这类"最后一段通配"写法（不是 `1.*` / `*`）？
- [ ] `dependencies` 里的名字与目标 mod 的 `name` **逐字符**一致？
- [ ] 用了 `replace_path` 时，`descriptor.mod` 与 `.mod` 两份都写了、且条数一致？
- [ ] DLC 相关内容用 `has_dlc = "..."` 门控，且**没有**把文件写进 `dlc/`？
- [ ] 封面字段写 `picture=`（不是 `thumbnail=`）？
- [ ] `descriptor.mod` 无 BOM；`localisation/*.yml` 有 BOM？

---

**下一步阅读**：[load-order-and-override.md](load-order-and-override.md)（三种覆盖机制与加载顺序的实证边界）→ [environment.md](environment.md)（本机路径/日志/目录全景）→ `../01_script/_index.md`（脚本语言怎么用）。

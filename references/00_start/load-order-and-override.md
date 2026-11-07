---
title: 加载顺序与覆盖机制（replace_path / 同路径整文件覆盖 / 同 ID 覆盖）
domain: 00_start
scope: any
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - documentation/（12 个 *.md 全量 grep：override|overwrite|replace the|same name|mod folder|load order 命中 222 处，全部是 effect/trigger 语义，无一处讲 mod 加载）
  - documentation/（replace_path|mod folder|load order|descriptor 独立 grep：0 命中）
  - <USER_DIR>/mod/*.mod、<WORKSHOP_DIR>/*/descriptor.mod（32 个已装 mod 逐个清点 replace_path 与同路径文件）
  - <USER_DIR>/launcher-v2.sqlite（playsets_mods.position 与 dlc_load.json 对账）
  - common/collections/_documentation.md、common/operations/_documentation.md 等（"定义必须唯一"）
  - audit/game-survey.md §7.1–§7.6（本机只读扫描产物）
---

# 加载顺序与覆盖机制

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 1.19.3 / 1.19.4）

> 一句话定位：mod 之间"谁能盖住谁"只有三种手段——**`replace_path` 整目录替换 / 同相对路径整文件覆盖 / 同 ID 覆盖**；而**决定顺序的规则，官方没有任何文档**，本文把"已实测"和"猜的"分开写。

## 0. 证据分级（全文通用）

| 标记 | 含义 |
|---|---|
| 【实证】 | 本机文件可直接核对（文件数、行号、SQL 查询结果） |
| 【推断】 | 由"文件事实 + 引擎必须自洽"反推，证据强但未直接观测 |
| 【未确认】 | 无文档、无样本、本轮未启动游戏，**不要写进交付物当结论** |

本文所有结论取自只读扫描：游戏文件、`<USER_DIR>/mod/`、`<WORKSHOP_DIR>/`、`launcher-v2.sqlite`。**本轮没有启动游戏做对照实验**，所以凡涉及"运行时谁生效"的判断都标了级别。

## 1. 前提：官方**没有** mod 加载顺序 / 文件覆盖的文档

两轮独立 grep（`documentation/` 下 12 个 `*.md` + 同名 `.html`）：

1. `override|overwrite|replace the|same name|mod folder|mod/|load order` → **222 处命中，全部是 effect/trigger 语义**（`custom_override_tooltip`、`relation_rule_override` 之类），**没有一处**在讲 mod 加载或文件覆盖（`audit/game-survey.md` §7.1，`:447-450`）。
2. `replace_path|mod folder|load order|descriptor` → **0 命中**。

⇒ **「加载顺序是什么」在官方随附文档里没有权威出处**。wiki/社区说法（按文件名、按启动器顺序、按字母序……）都属二手经验；本文只保留能从**本机文件与启动器数据库**核实的部分。写进交付文档时，**不要**把顺序规则写成"游戏就是这样"，最多写"当前启动器/本机表现为……"。

## 2. 机制一：`replace_path` —— 整目录替换

### 2.1 写法

```pdx
# 两个描述文件都写（实证，见 §2.3）
replace_path = "common/national_focus"     # 相对游戏根的目录，不带前后斜杠
replace_path = "history/states"
replace_path = "gfx/fonts"
```

### 2.2 语义：整目录丢弃

【推断（强）】加载时**丢弃原版该目录的全部内容**，只用 mod 同名目录里的文件。
理由：总转换 mod 的资源需要"用我的，而不是叠加"——若只是叠加，原版 81 个国策文件会和 mod 的定义同时存在，同一批 focus ID 重复定义必然互相污染；而这些 mod 的实际行为是原版内容**消失**（社区一致描述）。

【实证】使用广度（本机 32 个已装 mod）：

| mod | replace_path 条数 | 本地 `.mod` 行号 |
|---|---|---|
| Kaiserreich（1521695605） | **74** | `ugc_1521695605.mod:2-75` |
| BlackICE（1137372539） | **65** | `ugc_1137372539.mod:1-65` |
| ugc_2777392649 / 2438003901 | 74 / 73 | 各自 `.mod` 全文 |
| ugc_1851181613 / 2948642461 | 64 / 65 | 同上 |
| ugc_3350890356 | 61 | 同上 |
| The road to 56 CN（2129897125） | 3 | `The road to 56 CN.mod:14-16` |
| ugc_820260968 | 2 | 同上 |

汇总：**10 / 32 个 mod 使用，共 484 条**；另 22 个（含 `hist_tech_trees`）**完全不用**，只靠机制二/三。

【实证】`descriptor.mod` 与 `<USER_DIR>/mod/*.mod` 里的 `replace_path` **条数一致**（KR 74/74、BlackICE 65/65、Rt56 CN 3/3）⇒ 两份都要写。

### 2.3 危险点（全部有本机样本）

1. **整目录消失**：`replace_path="common/national_focus"` 后，**你没重写的国策树全部失效**。BlackICE 的 65 条里包含 `common/national_focus`、`common/technologies`、`common/decisions`、`common/on_actions` —— 换掉的就是整个玩法层。
2. **父目录 + 子目录同时列**（合法且常见）：BlackICE `:25 replace_path="common/units/equipment"` 与 `:30 replace_path="common/units"`；`:34 replace_path="map"`（整张地图）与 `:35 map/strategicregions`、`:37 map/terrain`。⇒ 子目录条目在父目录已被整体替换时**是冗余的**，但作者仍写，说明"写多不报错"（未确认是否被忽略）。
3. **兼容性归零**：两个同类总转换 mod 不可能共存（各自都要独占用同一批目录）。
4. **写错路径的后果【未确认】**：把 `replace_path="common/national_focuss"` 拼错，是"静默无效"还是加载期报错，本轮未启动游戏验证。**改这个字段后用 `error.log` 对照是最低要求**。

### 2.4 什么时候该用

- ✅ 总转换 / 大改：确定要替换掉原版整个子系统（国策树全换、地图全换、字体全换）。
- ❌ 只加几条内容：用机制二（新建文件）或机制三（同 ID）；用 `replace_path` 会把原版其余内容一起丢掉。
- ⚠️ 子 mod / 兼容补丁：不要用（会把父 mod 的其它文件也甩掉）。

## 3. 机制二：同相对路径 = **整文件覆盖**（不是合并）

### 3.1 实证：覆盖面有多大

本机 32 个 mod 中，"与原版同相对路径"的文件数量（只读统计）：

| mod | 自身文件数 | 与 vanilla 同路径 | 分布 |
|---|---|---|---|
| Kaiserreich（1521695605） | 35,880 | **937** | gfx 343 / common 251 / history 135 / loc 121 / interface 62 / map 20 / music 2 |
| The road to 56 CN | 28,739 | **6,519** | gfx 3,505 / history 1,458 / common 1,080 / map 313 / events 97 |
| hist_tech_trees | 1,108 | **260** | interface 257 / common 3 |

实例：`hist_tech_trees/interface/countrytechtreeview.gui` 与 `hist_tech_trees/interface/topbar.gui` 都是原版同名文件的完整副本，文件里的窗口名与 vanilla 完全一致（`interface/countrytechtreeview.gui` 的 `name="countrytechtreeview"`、`interface/topbar.gui` 的 `name="topbar"`）；另有 `common/units/equipment/tank_chassis.txt`、`common/technology_tags/00_technology.txt`。

### 3.2 语义：整个文件被替换

【推断（强）】同路径文件**整体替换**原版文件，不做行级/块级合并。
理由：mod 里这些文件是**原版文件的完整拷贝**（含未修改的条目）；若是合并，`common/technologies/*.txt` 这类会被双重定义、`.gui` 会出现重复窗口名。

### 3.3 风险：多 mod 抢同一个文件，只有一个赢

【实证】本机 **11 个**已装 mod 同时覆盖 `interface/countrytechtreeview.gui`：10 个工坊 mod
（`1137372539`、`1521695605`、`1851181613`、`2129897125`、`2438003901`、`2777392649`、`2948642461`、`3350890356`、`3431515994`、`820260968`）
+ 本地开发 mod `hist_tech_trees`（`<USER_DIR>/mod/hist_tech_trees/interface/countrytechtreeview.gui`，见 §3.1 表）。
同类冲突文件：`countrydiplomacyview.gui`、`frontendgamesetupview.gui`、`frontendmainview.gui`、`countrypoliticsview.gui` 各 9–10 个 mod 同时覆盖。

⇒ 装两个都改科技树界面的 mod 时，**只有一个的 `.gui` 生效**，另一个的界面改动完全消失——而 `error.log` **不一定**报错（是否报错【未确认】），表现为"功能在但界面错乱/按钮位置不对"。

### 3.4 对原版更新的脆弱性

覆盖整文件 = 把**原版当时的整个文件**冻进 mod。官方后续补丁在该文件里加一行，你的 mod 就永久缺少这一行（新国策不显示、新装备丢字段）。这是"大改 mod 往往要求锁版本"的根源之一。

### 3.5 推荐做法

- 能新增就**新建文件**（如 `common/ideas/zz_my_mod_ideas.txt`），不复制原版文件；
- 必须改原版文件时，记录"这份拷贝基于哪个游戏版本"，并在升级后 `diff` 一次；
- `.gui` 覆盖尽量只做一份、且自知会与他人 mod 互斥。

## 4. 机制三：同 ID 覆盖

### 4.1 依据：定义按 ID 全局索引

【实证】官方 `_documentation.md` 多处以"定义必须唯一"的方式描述 ID 语义：

- `common/collections/_documentation.md:16`
- `common/intelligence_agency_upgrades/_documentation.md:7`
- `common/operation_phases/_documentation.md:3`
- `common/operations/_documentation.md:11`
- `common/operation_tokens/_documentation.md:5`

⇒ 引擎按 **ID**（不是按文件）索引定义；同一 ID 出现多次时由加载顺序决定谁胜出（【推断（强）】，顺序规则本身见 §5）。

### 4.2 实证：重定义有多普遍（以科技为例）

- vanilla 科技 ID：**674** 个（`common/technologies/*.txt`）；
- Kaiserreich：590 个科技定义，其中 **549** 与 vanilla 同名；
- The road to 56 CN：1,026 个，其中 **644** 与 vanilla 同名；
- 同一文件内的位置也会变：vanilla `common/technologies/air_techs.txt:656` 的 CAS1，在 Kaiserreich 的同名文件里在 `:576`。

### 4.3 不是所有 mod 都走这条路（本机对照）

`hist_tech_trees` 的 `common/` 只有 9 个文件，其中**仅 3 个**与原版同路径（`script_enums.txt`、`technology_tags/00_technology.txt`、`units/equipment/tank_chassis.txt`），其余 6 个都是新文件名（`zz_htt_GER_armor_tech.txt` 等）。它的 163 个科技键**全是新增**，不与 vanilla 冲突。

⇒ 这正是"内容型 mod 的推荐姿势"：**新增 ID + 新增文件**，只在必须改原版块时才做同 ID 覆盖。

### 4.4 风险

- **整块替换 vs 子块合并，随类型不同【未确认】**：历史经验是 `idea`/`focus` 通常整体替换（覆盖后原定义里没写的字段会丢），而某些类型只改子块。**每类都要实测一次**，不要假设"只写 modifier 就能保留原 idea 的其它字段"。
- **覆盖 = 冻结原版内容**：官方给该 ID 加字段/改数值后，你的版本里永远是旧的。
- **ID 冲突不报错**：同 ID 重复定义通常静默；表现为"数值不对/属性没生效"，很难查。

## 5. 加载顺序：能确认的只有"写出顺序"

### 5.1 三种二手说法（互相矛盾，都没官方出处）

| 说法 | 出处（都属经验性） | 状态 |
|---|---|---|
| 按 `<USER_DIR>/mod/*.mod` **文件名**排序 | ``06_workflow/setup.md`（母本）:18`（"文件名决定加载顺序"） | 【未确认】 |
| 按 `dlc_load.json` 的 `enabled_mods` **数组顺序**，后者覆盖前者 | `environment.md` §6.2 | 【未确认】（但"写出顺序=数组顺序"已实证，见下） |
| 按启动器 playset 的 `position` | `launcher-v2.sqlite` 的 `playsets_mods.position` 字段 | 【实证】字段存在且被写 |

### 5.2 本机可实证的部分：`position` → `dlc_load.json` 顺序

查 `<USER_DIR>/launcher-v2.sqlite`（只读）：

- 表 `playsets_mods` 结构：`playsetId char(36), modId char(36), enabled boolean, position integer`；
- 当前 **active 的 playset = "史实装备"**（`playsets.isActive=1`），其 2 条 `enabled=1` 记录：

| position | mod | 来源 |
|---|---|---|
| 0 | `2977114459`（工坊） | `<WORKSHOP_DIR>/2977114459` |
| 1 | `hist_tech_trees` | `<USER_DIR>/mod/hist_tech_trees` |

- 同机 `<USER_DIR>/dlc_load.json`：

```json
{"enabled_mods":["mod/ugc_2977114459.mod","mod/hist_tech_trees.mod"],"disabled_dlcs":[]}
```

⇒ 【实证】**`dlc_load.json` 的 `enabled_mods` 数组顺序 = 启动器 playset 里 `position` 的升序**，且只包含 active playset 中 `enabled=1` 的 mod。

⇒ 【未确认】**引擎是否按这个数组顺序决定"谁覆盖谁"**。可能的表现有：按数组顺序（后者胜）、按文件名/路径字典序、或与数组顺序无关只做"先到先得"。**没有官方文档，也没有做过双 mod 抢同一文件的对照实验。**

### 5.3 怎么自测（30 分钟实验设计）

目标：确定"两个 mod 改同一 ID 时谁生效"。

1. 新建两个最小 mod `zz_a` / `zz_b`，各自 `common/ideas/00_ideas.txt` 里定义**同一个新增 idea ID**（同一 `modifier` 不同数值，如 `stability_factor = 0.1` vs `0.2`）。
2. 只启用 A+B，进游戏看该 idea 的 tooltip 数值（控制台 `add_ideas` 后看国家精神）。
3. 交换 playset 里的顺序（拖 `position`），重进游戏再读同一数值。
4. 判读：
   - 数值随顺序翻转 → 按 playset/`dlc_load` 顺序生效；
   - 与顺序无关、恒定由某一方胜 → 另有排序规则（如文件名/路径）；
   - 数值是"后者拼接前者"（两个 modifier 都在）→ 该类型是**子块合并**，机制三的语义要按类型细化。
5. 把结果记进 `error.log` 里有没有 `Duplicate definition`/`already defined` 类告警。

> 做这个实验的前提：`path` 纯 ASCII、不写用户目录（用 `path` 绝对路径指向 `<PROJECT_DIR>` 下的临时目录），详见 `environment.md` §2.2。

### 5.4 顺序的实际影响面

只有当**两个 mod 改同一个东西**时才重要：

- 同路径文件（尤其 `.gui`、`common/technologies/*.txt`）——见 §3.3，本机 10 个 mod 抢同一个国策界面文件；
- 同 ID 定义——§4.2，总转换之间几乎必然冲突；
- `replace_path` 之间——各占各的目录，通常不冲突，但与"另一个 mod 的同路径文件"叠加时行为【未确认】。

## 6. 一页速查：三种机制对照

| | `replace_path` | 同相对路径整文件覆盖 | 同 ID 覆盖 |
|---|---|---|---|
| 粒度 | 整目录 | 单个文件 | 单条定义（ID） |
| 语法 | `.mod` 里 `replace_path="dir"` | 新建同名文件 | 在任意文件里重写同 ID 块 |
| 原版内容 | **整目录消失** | 该文件内容全部消失 | 该 ID 的定义被替换（子块是否合并【未确认】） |
| 本机使用率 | 10/32 mod | 22/32 mod 大量使用 | 总转换普遍；内容 mod 少量 |
| 主要风险 | 漏写 → 子系统消失 | 与他 mod 互斥；原版更新丢失 | 静默失效；字段丢失 |
| 适用 | 总转换/大改 | 必须改原版整文件时 | 改单条国家精神/科技/国策 |

## 7. 未确认清单（写交付物时别当事实）

1. 两个 mod 同改一个文件/ID 时，**确切**的胜出规则（文件名序 / 数组序 / 其它）。
2. `replace_path` 写**不存在的目录**时的报错行为（静默 or `error.log`）。
3. 父目录与子目录同时 `replace_path` 时，子条目是否被忽略。
4. 同 ID 覆盖时，**哪些类型是整块替换、哪些是子块合并**（`idea`/`focus`/`decision`/`character`/`technology` 需分别实测）。
5. DLC 内容在加载链中的确切位置（`environment.md` §6 写"原版 → integrated_dlc → dlc → mod"，属【推断】，无官方文档；可观测的支持只有"mod 可覆盖 `integrated_dlc/` 下同路径文件"）。
6. `replace_path` 与"另一个 mod 的同路径文件"同时存在时的合并顺序。
7. 加载顺序与**校验和**的关系（`environment.md` §6.3）——顺序是否影响 checksum 未实测。

---

**相关文档**：[mod-structure.md](mod-structure.md)（目录/描述符/`supported_version`/DLC 资产布局）→ [environment.md](environment.md)（本机路径、日志、checksum 常识）。

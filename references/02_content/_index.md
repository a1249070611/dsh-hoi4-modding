---
title: 内容系统知识库（Content Systems）总索引
domain: 02_content
scope: country / state / global
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/decisions/_documentation.md
  - common/characters/_documentation.md
  - common/factions/_documentation.md
  - common/special_projects/special_projects_documentation.md
  - common/special_projects/projects/documentation.md
  - common/military_industrial_organization/organizations/_documentation.md
  - common/raids/_documentation.md
  - documentation/effects_documentation.md
---

# 内容系统知识库（references/02_content）

本目录回答一个问题：**「在 HOI4 1.19.x（本机 1.19.4.2）里做出完整内容，每个系统文件放哪、写什么、怎么被触发、localisation 怎么对」**。
脚本语言本身（scope / effect / trigger / 变量 / on_actions）不在这里讲，见 [脚本核心](../01_script/_index.md)。

所有结论的证据来自本机 1.19.4.2 文件（`<GAME_DIR>`，只读）与自带 `documentation/*.md`；
凡本机无法确认的写法一律标 `⚠️` 并给出来源。网络资料一律视为「社区经验」。

## 文档清单

| 文档 | 一句话定位 | 主要原版参考 |
|---|---|---|
| [focus-trees.md](focus-trees.md) | 国策树：focus_tree / focus / 前置互斥 / bypass / 共享树 / AI 与布局 | `common/national_focus/germany.txt`、`baltic_shared.txt`、`estonia.txt`、`latvia.txt` |
| [events.md](events.md) | 事件：namespace、country/news/state_event、MTTH、immediate/after、option/ai_chance、hidden | `events/Germany.txt`、`events/ElectionEvents.txt`、`events/stability_events.txt`、`events/BBA_NewsEvents.txt` |
| [decisions.md](decisions.md) | 决议：category 顶层块、targeted（target_trigger/targets）、cost/timeout/remove_effect | `common/decisions/_documentation.md`、`AST.txt`、`AFG.txt`、`GER.txt` |
| [ideas.md](ideas.md) | 理念/国家精神：ideas= 包裹、category、modifier、on_add/on_remove、removal_cost | `common/ideas/GER.txt`、`_economic.txt`、`common/idea_tags/00_idea.txt` |
| [characters.md](characters.md) | 角色：领袖/顾问/将领/科学家四种角色，招募与替换 | `common/characters/_documentation.md`、`common/characters/GER.txt` |
| [technologies.md](technologies.md) | 科技：technologies= 包裹、folder/path/cost、装备解锁、on_research_complete、科技共享 | `common/technologies/infantry.txt`、`support.txt`、`common/technology_sharing/00_tech_sharing_groups.txt` |
| [history-countries.md](history-countries.md) | 国家定义与初始设置：country_tags、common/countries、history/countries、书签 | `common/country_tags/00_countries.txt`、`common/countries/Germany.txt`、`history/countries/GER - Germany.txt`、`common/bookmarks/the_gathering_storm.txt` |
| [mio.md](mio.md) | 军工组织（MIO）：组织树、特质、政策，与装备/产线绑定 | `common/military_industrial_organization/**/_documentation.md`、`organizations/GER_organization.txt` |
| [special-projects.md](special-projects.md) | 特殊项目：设施/专精、项目树、突破点、原型奖励、科学家 | `common/special_projects/special_projects_documentation.md`、`projects/documentation.md`、`projects/nuclear_projects.txt` |
| [diplomacy-wargoals.md](diplomacy-wargoals.md) | 外交：宣战目标、阵营（factions 新系统）、和平会议、附庸/自治、脚本外交行动 | `common/wargoals/00_invasion.txt`、`common/factions/_documentation.md`、`common/peace_conference/**`、`common/autonomous_states/` |
| [intelligence.md](intelligence.md) | 情报：机构升级、行动/阶段/token、突袭（raids） | `common/operations/_documentation.md`、`operation_phases/`、`operation_tokens/`、`common/raids/_documentation.md`、`intelligence_agency_upgrades/_documentation.md` |
| [balance-of-power.md](balance-of-power.md) | 权力平衡：side/range/modifier、与决议分类联动 | `common/bop/_test.txt`、`common/bop/FIN.txt` |
| [occupation-resistance.md](occupation-resistance.md) | 占领法与抵抗/顺从阈值修正 | `common/occupation_laws/occupation_laws.txt`、`common/resistance_activity/resistance_activity.txt`、`common/resistance_compliance_modifiers/` |

## 各域规模与官方文档位置（1.19.4.2 实测，`<GAME_DIR>` 只读扫描，2026-11-06）

| 域 | 文件数 | 总行数 | 官方文档 |
|---|---|---|---|
| `common/national_focus/` 国策 | 81 | 691,478 | **无** `_documentation.md` |
| `events/` 事件 | 128 | — | 无（`events/` 无子目录） |
| `common/decisions/` 决议 | 147 | 345,066 | `common/decisions/_documentation.md` |
| `common/ideas/` 理念 | 213 | 151,368 | **无** |
| `common/characters/` 角色 | 233 | 165,061 | `common/characters/_documentation.md` |
| `common/technologies/` 科技 | 13 | 27,065 | **无** |
| `common/military_industrial_organization/` MIO | 63 | 44,406 | `organizations/_documentation.md`、`policies/_documentation.md`、`ai_bonus_weights/_documentation.md` |
| `common/special_projects/` 特殊项目 | 17 | 14,805 | `special_projects_documentation.md`（设计草案，25 KB）+ `projects/`、`prototype_rewards/`、`specialization/` 各有 `documentation.md` |
| `common/factions/` 阵营 | 30 | 20,286 | `common/factions/_documentation.md` |
| `common/raids/` 突袭 | 10 | 12,452 | `common/raids/_documentation.md` |
| `common/bop/` 权力平衡 | 10 | 3,738 | **无** |
| `common/occupation_laws/` 占领法 | 1 | — | **无** |

> 「无官方 `_documentation.md`」不等于「无文档」：这类域先查 `documentation/effects_documentation.md` / `documentation/triggers_documentation.md` 的对应条目，再抄 `common/` 下 vanilla 实例的字段。

## 本目录最重要的 5 条结论

1. **「数据文件」永远比「脚本逻辑」先加载**。`common/`、`history/`、`events/` 在启动时读取并建立数据库；改完必须重启游戏（无热重载）。
   加载顺序是 **原版 → 按 mod 顺序**，所以「**同 ID 定义后者覆盖前者**」（可用来覆盖单条国策/理念/角色），
   而「**同名文件整体替换**」只在你给出完整同名文件时发生（如你的 mod 里也有 `common/national_focus/germany.txt`）。
   推荐做法：**新增文件 + 新 ID**，需要改原版内容时只放最小改动并明确写 `README`（详见 [06_workflow](../06_workflow/compatibility.md)）。

2. **1.19.4.2 里多数内容系统自带 `_documentation.md` / `documentation.md`**，这是最权威的本地事实来源，优先级高于 wiki：
   `common/decisions/_documentation.md`、`common/characters/_documentation.md`、`common/factions/_documentation.md`、
   `common/operations/_documentation.md`、`common/raids/_documentation.md`、`common/intelligence_agency_upgrades/_documentation.md`、
   `common/special_projects/special_projects_documentation.md`（另有 `projects/`、`prototype_rewards/`、`specialization/` 三篇）、
   `common/military_industrial_organization/{organizations,policies,ai_bonus_weights}/_documentation.md` 等。
   **国策、理念、科技、权力平衡、占领法这五个域没有域级 `_documentation.md`**（详见上一节的清单），只能读 `documentation/` 大文档 + 抄 vanilla 实例。
   本目录每篇的「证据」小节都会点名这些文件，**写内容之前先读它们**。

3. **本地化 key 与 ID 强绑定，且不同系统后缀规则不同**：
   - 国策：`<focus_id>`（名称）+ `<focus_id>_desc`（描述）。证据：`localisation/english/wuw_focus_l_english.yml:3039-3040` 的 `GER_prioritize_economic_growth` / `..._desc`。
   - 事件：`<namespace>.<n>.t` / `.d`（旧写法 `.desc` 也可，见 `events/stability_events.txt:13`）/ `.a`（选项）。证据：`events/Germany.txt:10-12`。
   - 决议：`<decision_id>` + `<decision_id>_desc`。证据：`localisation/english/TAOG_decisions_l_english.yml:668-669` 的 `AST_union_strike`。
   - 理念/角色/科技/组织/项目：多数直接以 token 为 key，并支持 `TAG_` 前缀按国家覆写（见各篇原文引用）。
   → 因此所有示例 ID 都必须配一条本地化，**缺 key 在游戏里表现为空字符串或 `KEY` 原样显示**，不会崩，但等于没做。

4. **内容型系统之间的标准连接方式是「effect / trigger」，不是文件引用**：
   国策 `completion_reward` 里 `country_event`、`add_ideas`、`add_tech_bonus`、`activate_mission`（`documentation/effects_documentation.md:661`）；
   决议 `complete_effect` 里开事件链；事件 `option` 里 `add_ideas`/`create_wargoal`（见 `common/scripted_effects/DEN_scripted_effects.txt:3525`）；
   特殊项目 `project_output` 里 `unlock_module_tooltip` / `enable_equipments`。**把这些 effect 写成 `scripted_effect`** 再用 ID 复用，
   是原版主流写法（`common/scripted_effects/`）。

5. **1.19 时代的内容系统已经不是旧教程描述的样子**：
   - 决策文件的顶层就是**分类块**（`xxx_category = { ... }`），**不是** `decisions = { ... }` 包裹层；我对 `common/decisions/` 全目录 grep「以 `decisions =` 开头的行」，无任何命中（2026-10-26）。
   - 学说从科技树里独立成 `common/doctrines/`（陆海空 `grand_doctrines`/`subdoctrines`/`tracks`，见 `common/doctrines/_documentation.md`；军事侧详见 [03_military/doctrines.md](../03_military/doctrines.md)）。
   - 阵营系统重写：`create_faction` 被标注 **deprecated**（`documentation/effects_documentation.md:3105`），改为 `create_faction_from_template` +
     `common/factions/{templates,goals,rules,upgrades}`（`common/factions/_documentation.md`）。
   - 突袭（raids）多数受 `has_dlc = "Gotterdammerung"` 限制（`common/raids/air_raids.txt:42`）；
     特殊项目同样见 `has_dlc = "Gotterdammerung"`（`common/special_projects/projects/nuclear_projects.txt:275-276`）。

## 跨系统内容链的推荐骨架

做「一条完整内容线」时，按下面的顺序落地（最小可运行骨架见仓库根 `fixtures/mini_mod`，相对本文件是 `../../../../fixtures/mini_mod`）：

```text
① common/country_tags/  + common/countries/ + history/countries/   # 先把国家跑起来
② common/ideas/          # 国家精神（可被国策 add_ideas 授予）
③ common/characters/     # 领袖/顾问（先占位，避免 history 里 recruit_character 报错）
④ common/national_focus/ # 国策树，completion_reward 里发事件/给理念
⑤ events/                # 事件与事件链（is_triggered_only 由国策/决议触发）
⑥ common/decisions/      # 决议（常见 1 级：category + decision）
⑦ common/technologies/   # 新科技（可选）
⑧ localisation/{english,simp_chinese}/  # 所有 key 一次补齐（UTF-8 BOM）
```

## 三条学习路径

| 目标 | 阅读顺序 |
|---|---|
| 做一个「有国策 + 事件 + 决议 + 理念」的小国 | [history-countries.md](history-countries.md) → [focus-trees.md](focus-trees.md) → [events.md](events.md) → [decisions.md](decisions.md) → [ideas.md](ideas.md) |
| 替换/新增一个国家的政治人物与政府 | [characters.md](characters.md) → [ideas.md](ideas.md) → [history-countries.md](history-countries.md)（`set_politics`/`recruit_character`） |
| 做 1.19 的新系统内容（工业/科研/情报） | [mio.md](mio.md) → [special-projects.md](special-projects.md) → [intelligence.md](intelligence.md) → [technologies.md](technologies.md) |

外围系统按需查：[diplomacy-wargoals.md](diplomacy-wargoals.md)（阵营/宣战/和平）、[balance-of-power.md](balance-of-power.md)（滑条）、
[occupation-resistance.md](occupation-resistance.md)（占领区）。

## 本机 DLC 与内容系统的对应（`dlc/*.dlc` 实测，2026-11-06）

| DLC 名（`name =` 字段） | 目录名 | 本目录涉及的系统 |
|---|---|---|
| La Resistance | `dlc028_la_resistance` | 情报机构、行动（operations）、占领/抵抗 |
| No Step Back | `dlc034_no_step_back` | 坦克模块、`NSB_armor.txt` 科技、科学家前身 |
| By Blood Alone | `dlc036_by_blood_alone` | 飞机设计、`bba_air_techs.txt` |
| Arms Against Tyranny | `dlc038_arms_against_tyranny` | **MIO**（军工组织） |
| Trial of Allegiance | `dlc040_trial_of_allegiance` | 南美内容（`TOA_*` 文件） |
| Gotterdammerung | `dlc043_gotterdammerung` | **特殊项目**、**突袭（raids）**、德国"经济奇迹"类决议 |
| Graveyard of Empires | `dlc046_graveyard_of_empires` | 中东/印度内容（`GOE_*`） |
| Thunder at Our Gates | `dlc052_thunder_at_our_gates` | 1.19 配套内容包（`TAOG_*`、泰国/印尼） |
| No Compromise, No Surrender | `dlc049_no_compromise_no_surrender` | 中国相关内容（`land_infiltration_raids` 门控之一） |
| Peace For Our Time | `dlc051_peace_for_our_time` | 外交/绥靖相关 |

写 `has_dlc = "..."` 时**字符串必须与上表 `name` 完全一致**（大小写、空格、标点）。

## 本目录的验证方式

1. **文件/行数**：`references/02_content/*.md` 共 14 个文件，每个 100–400 行（见完成报告）。
2. **括号平衡**：对每个文件统计 `{` 与 `}` 数量（排除正文里刻意引用的 `decisions = { ... }` 这类片段后相等）。
3. **语法证据**：每篇的「证据」引用都指向具体文件路径（必要时带行号），来源限定为
   `documentation/*.md`、`common/**/_documentation.md`、`common/*`、`events/*`、`history/*`、`localisation/english/*`、`interface/*.gfx`。
4. **GFX 校验**：示例里用到的每个 `GFX_*` 都已在 `interface/*.gfx` 里 grep 到，或明确标注为「原版数据文件中的引用」。
5. **本地化清单**：每篇示例都附带 `.yml` 片段，key 与示例 ID 一一对应。

## 常见坑（全目录通用）

- **ID 撞车**：原版没有 `HHO_`/`ADV_` 前缀，但其他 mod 可能有。养成 `NAMESPACE_` 前缀 + 全库搜索的习惯。
- **namespace 重复声明**：一个事件 namespace 只需 `add_namespace = xxx` 一次；多个文件重复声明通常无害，但 `id` 必须全局唯一（`namespace.number`）。
- **忘了 `add_namespace`** → `events/` 里的事件 ID 找不到，error.log 报 unknown namespace / 事件不触发。
- **localisation 编码**：`.yml` 必须 UTF-8 **带 BOM**、`l_english:` 顶格、每行 1 个空格缩进、字符串用 `"`；中文包是 `l_simp_chinese:`。详见 [05_presentation/localisation.md](../05_presentation/localisation.md)。
- **图标引用**：`icon = GFX_xxx` 必须是已注册 sprite（原版或自建 `.gfx`）；引用不存在的 GFX 不崩但要报 error。自建图标见 [05_presentation/gfx-sprites.md](../05_presentation/gfx-sprites.md)。
- **别把 `common/` 里原版文件复制过来**：体积大、且原版更新后你的副本会静默落后。要改就用「同 ID 覆盖一个块」或「新文件」。
- **DLC 判定**：`has_dlc = "Gotterdammerung"` 这类字符串必须与 `dlc/dlcNNN_*.dlc` 里的 `name` 一致（本机 `dlc/` 共 42 个 `.dlc`、43 个 DLC 目录，`dlc052` = "Thunder at Our Gates"）。写错名字 = 条件永远假。

## 自检清单（写完任何一篇内容后）

1. `grep -c '{'` 与 `grep -c '}'` 在单文件里数量一致（本目录已逐文件核对，见任务报告）。
2. 每个 `icon = GFX_...` 都能在原版 `interface/`、`gfx/` 或自己的 `.gfx` 里 grep 到。
3. 每个 ID 都有对应本地化（英文至少一条），中文包可后补但**不能留 `l_english` 之外的空文件**。
4. `has_dlc` 字符串与 `dlc/*.dlc` 的 `name` 完全一致。
5. 事件/决议/国策里调用的每个 effect 都在 `documentation/effects_documentation.md` 里存在（`## effect_name`）。
6. 新文件没有和原版同名（`common/national_focus/germany.txt` 之类）。

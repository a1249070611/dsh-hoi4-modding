---
title: 旧 mod 升级到 1.19 的检查清单
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - https://hoi4.paradoxwikis.com/Patch_1.19
  - https://hoi4.paradoxwikis.com/Patch_1.19.X
  - https://hoi4.paradoxwikis.com/index.php?title=Patch_1.18&action=raw&section=6
  - documentation
  - error.log
---

# 旧 mod 升级到 1.19 检查清单

基线 **1.19.x**（1.19.3.x 实测 checksum `5632`）。本文分「必做」「按需」「已确认破坏性变更」三块，每条都标了判定依据。

## 0. 三条升级铁律

1. **不要相信「能进游戏就是升级成功」**：1.19 有写法被移除后会**静默失效**（不报错、不生效），只有对比 before/after 行为才发现。
2. **先备份再改**，并且**先记录基线**：空 mod 跑一次的 `error.log` 行数、checksum、以及「功能是否正常」的现象清单。
3. **一次一个层面**：描述文件 → 语法关键字 → 内容系统 → GUI/本地化 → 性能。跨层同时改，出问题无法定位。

## 1. 必做（30 分钟内可完成）

- [ ] **`supported_version` 改 `"1.19.*"`**
     语法：通配符只能在最后一段，至少写 `大版本.小版本`。`1.*`/`*`/`1.*.*` 全部非法。
     证据：实测 7 个已发布 mod 报 `Invalid supported_version`（`logs/error.log:1-8`），而 `1.19.*`、`1.19.3.*`、`1.19.3.0` 无报错。
- [ ] **`.mod` 里 `thumbnail=` 改为 `picture=`**
     证据：`mod/ugc_3243611664.mod:9` → `Error: "Unexpected token: thumbnail"`。
- [ ] **确认 `path` 仍合法**（正斜杠 + 纯 ASCII + 指向含 `common/` 的那层）。换机器/换目录后最容易失效。
- [ ] **重新生成封面**（若原来 > 1MB）：Paradox Mods 限制 < 1MB。
- [ ] **读一遍 1.19、1.19.1、1.19.2、1.19.3 的 Modding 段**（共 13 条；摘要见本文 §2.5，原文在官方 patch notes）。
- [ ] **清空/备份旧 `error.log`** 后跑一次，把「原版噪声基线」记下来（实测基线：14664 行）。

## 2. 已确认的破坏性变更（1.19，必须逐个查自己的 mod）

### 2.1 🚨 `add_temporary_buff_to_units` 已被移除

```bash
# 在你的 mod 里搜（这一条是 1.19 最容易炸的）
grep -rn "add_temporary_buff_to_units" . 2>/dev/null
```

- 官方原文：`Removes support for 'add_temporary_buff_to_units' and adds new 'unit_modifiers' to cover these use cases.`
- 实测：整个游戏目录 **0 命中**；`unit_modifiers` 在 `common/abilities/*.txt`、`common/unit_medals/00_default.txt`、`common/units/unit_modifiers/unit_modifiers.txt` 大量使用。
- 影响面：将领能力/技能、勋章、任何「临时给部队加成」的旧写法。
- 替代：`unit_modifiers`（新结构，**本地 `documentation/` 未收录**，要看上面那些游戏文件）。
  > ⚠️ 待验证：`unit_modifiers` 的完整字段（哪些 modifier 合法）尚未整理，需从 `common/units/unit_modifiers/unit_modifiers.txt`（97 行，列出 `sub_unit_modifiers` 可用项）逐条读。

### 2.2 decision 的 `war_with_on_remove` / `timeout` / `complete` 变成 scoped variable

- 官方 1.19 原文：`Decision's war_with_on_remove/timeout/complete are now scoped variables.`
- 你原来写 `war_with_on_remove = USA` 这种**直接写 tag** 的写法要复核（新语义接受变量）。
- ⚠️ 未在本机核对具体可接受形式（1.19.3 文档里应有对应条目，但本轮未查证）。

### 2.3 subdoctrine / doctrine 结构变化

- 1.19：subdoctrine 可指派给多种 doctrine track；新增 `allow_in_multiple_tracks`（默认 no）、`xor`（跨 track 互斥）。
- **同时** 1.19 免费内容新增「特种部队学说体系」（官方 free feature 段）。
- → 任何改 `common/doctrines/` 的 mod 都要重看结构；旧的「特种部队靠科技解锁」思路要改。

### 2.4 勋章 / raid / 新 modifier

- 勋章支持 `ship_modifiers`，并新增 `officer_xp` 字段；
- raid 目标类型新增 `captured_army_leader`；raid type 新增 `ai_min_success_chance`、`max_distance`；
- 新 modifier `casualty_trickleback`（本机 `modifiers_documentation.md` 已收录 ✅）。

### 2.5 1.19.1 / 1.19.2 / 1.19.3 的增量（按需）

| 版本 | 变更 | 何时需要管 |
|---|---|---|
| 1.19.1 | `impassable_ignored_links`（不可通行州的忽略州列表） | 做地图/改不可通行州归属 |
| 1.19.1 | 数学函数 `pow`/`sqrt`/`cos`/`sin`/`tan`/`exp`/`log` | 想把数值曲线写成表达式 |
| 1.19.2 | 数学表达式逻辑函数 `AND`/`OR`/`XOR`/`NOT`、`lerp`、`atan`/`atan2` | 同上 |
| 1.19.2 | Advisor 的 `always_show_on_actions_tooltip` | advisor 带自定义 tooltip 时 `on_add/on_remove` 效果说明丢失 |
| 1.19.2 | raid type 支持脚本化 `unit_animations` | raid 表现 |
| 1.19.3 | Admiral 战斗胜负 on_actions | 海军 mod |
| 1.19.3 | trigger `is_fighting_in_strategic_region`（**文档未收录**，游戏内用法 `= <战略区 ID>`） | 判断「是否在某战略区交战」 |
| 1.19.3 | 集合算子 `is_core_of` / `is_not_core_of`（性能优于触发器） | 集合运算 |
| 1.19.3 | `set_autonomy` 新增「保留原 subject」flag | 附庸体系 |
| 1.19.3 | `IsDeployed` trigger（Army HQ）+ `state_deployed`/`province_deployed` 变量 | Army HQ 相关 |

## 3. 按需检查（内容系统层）

- [ ] **Army HQ**：1.19 新增系统；若你改过 `common/units/`、`common/abilities/`、师模板，需复核。
- [ ] **Ship Captains**：舰长 + 勋章 + 可晋升 Admiral；改海军角色/勋章的 mod 必查。
- [ ] **Regimental Support**：师编辑器新增一行 + 12 个团属支援连；改 `common/units/` 的必查。
- [ ] **GUI**：1.19 有 UI 改动（HQ 计数器、装备窗口筛选等）；改原版 `.gui` 的 mod **必须重新 diff**（这是最容易「升级后界面错位」的地方）。
- [ ] **本地化**：新 modifier/trigger 需要新 loc key；别忘了补 `simp_chinese` 中文条目。
- [ ] **DLC 依赖**：新内容多挂在 DLC 后面（`has_dlc` 检查）；旧 mod 若假设「没有 DLC」可能行为不同。

## 4. 升级配方（可直接执行的检查脚本）

```bash
G="<游戏安装目录>"
M="<mod 目录>"

# ① 列出 mod 里用到的所有顶层键（粗筛），逐个查是否还在 1.19.3 文档里
grep -rhoE "^[[:space:]]*[a-z_]+[[:space:]]*=" "$M" | tr -d ' =' | sort -u > /tmp/mymod_keys.txt
while read -r k; do
  if ! grep -q "### $k\b" "$G/documentation/effects_documentation.md" \
     && ! grep -q "## $k\b" "$G/documentation/triggers_documentation.md"; then
     echo "NOT-IN-DOC: $k"
  fi
done < /tmp/mymod_keys.txt | head -50
# 注意：「不在文档里」≠ 错：本地 documentation 并不完整，下一步去游戏文件确认

# ② 确认是否还在游戏里被使用
grep -rn "<可疑关键字>" "$G/common" "$G/events" | head

# ③ 检查 .mod 字段
grep -H "supported_version\|thumbnail\|picture\|path" "$M"/*.mod "$M"/*/descriptor.mod
```

> 说明：① 的比对是**启发式**（本地 `documentation/` 并不完整），价值是**快速列出可疑项**，不是判死刑。

## 5. 存档兼容性（给玩家的承诺）

- 大版本（1.18→1.19）之间**不保证**存档可继续；原版自己都会在新版本出现存档问题。
- 你的 mod 若改了 `history/states`、州归属、国策树结构 → 存档内已有数据与新定义会错位。
- 建议在创意工坊描述里明确写：`Save-game compatible: yes / no (1.19 大版本)`。
- 判定方法（无游戏时的保守估计）：**只要 1.19 patch notes 里出现「Added … focus / states updated / states changed」而你改了对应内容 → 按不兼容处理**。1.19 明确写了 `Updated states in South-East Asia`、多个新国策树（澳大利亚/暹罗/荷属东印度）。

## 6. 1.16–1.18 的已知影响（诚实标注覆盖度）

| 版本 | 我掌握的 modding 变更 | 依据 |
|---|---|---|
| 1.18 | 仅 2 条：targeted advisor 的 `pp_spend_priority`；stability 触发器的范围校验 | wiki `Patch_1.18` Modding 段（A） |
| 1.17 | 仅 1 条间接证据：**集合（collections）体系**在此期上线，`every_collection_element` 在 `Scopes` 页标 `1.17` | wiki `Scopes`（B） |
| 1.16 | **未掌握** | — |

> ⚠️ 遗留：1.16 / 1.17 的 patch notes Modding 段本轮**未抓取**。补法：`https://hoi4.paradoxwikis.com/index.php?title=Patch_1.17&action=raw&section=<N>`（先用 TOC 数出 Modding 是第几段；1.18 的 Modding 是第 6 段、References 是第 8 段，可作参照）。
> 在补齐之前，**任何「1.16/1.17 改了什么」的说法都不应写进最终知识库**。

## 7. 升级后必须重新验证的 5 件事

1. 启动器里 mod **不再显示 out of date**（`supported_version` 正确）；
2. `error.log` 里**没有**新增 `Invalid supported_version` / `Unexpected token` / `Could not find sprite type`；
3. 主菜单 checksum 变化符合预期（改了 `common|events|history|map` 就该变）；
4. 进游戏实际看到：国策树可点、事件能触发、决议能点、GUI 不空白、文本不是 key 原文；
5. 旧存档读入后不崩（若承诺兼容）。

## 常见错误 / 自检清单

- [ ] 是否只改了 `supported_version` 就以为升级完了？
- [ ] `add_temporary_buff_to_units` 是否已全部替换？
- [ ] 改过 `common/doctrines/` 吗（1.19 学说体系变了）？
- [ ] 改过原版 `.gui` 吗（1.19 UI 变了，必须 diff）？
- [ ] 是否给了中文（`simp_chinese`）本地化？
- [ ] 是否声明了存档兼容性？
- [ ] 是否记录了升级前后的 error.log 行数基线？
- [ ] 1.16/1.17 的变更是否标注为「未掌握」而不是编造？

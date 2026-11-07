---
title: on_actions（事件钩子）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - common/on_actions/_documentation.md
  - common/on_actions/00_on_actions.txt
  - common/on_actions/04_mtg_on_actions.txt
  - common/on_actions/00_testing_on_actions.txt
  - common/on_actions/08_bba_on_actions.txt
---

# on_actions（事件钩子）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**`common/on_actions/*.txt` 是"游戏事件→脚本"的唯一注册表**。想"开局初始化""每天检查""某国被吞并时做点什么"，都在这里挂；挂错 hook 名**不会报错**，只会静默不执行。

## 1. 文件结构

```pdx
# 放置路径：common/on_actions/zz_MY_on_actions.txt（文件名随意，建议加前缀避免撞名）
on_actions = {
    # 每个 hook 是一级 key，里面可以放 effect / random_events
    on_startup = {
        effect = {
            # 这里没有国家 scope！必须显式切 tag
            SWE = { MY_init_sweden = yes }
        }
    }

    on_daily_SWE = {
        effect = {
            # 这里 scope = SWE
            MY_daily_sweden_check = yes
        }
    }
}
```

- **必须有 `on_actions = { ... }` 外层壳**（所有原版文件都是这个结构，见 `common/on_actions/00_on_actions.txt:1`）。
- 一个 hook 内可放两类块：
  - `effect = { <effects> }`：直接执行。
  - `random_events = { <权重> = <事件id> }`：按权重随机触发事件（原版例：`common/on_actions/04_mtg_on_actions.txt:2-6` 的 `on_new_term_election = { random_events = { 100 = mexico.18 } }`）。
- **同一 hook 可以重复定义，效果叠加**：原版 `00_on_actions.txt` 里 `on_startup` 出现在第 2 行和第 1634 行，两处都会执行；跨 DLC 文件也是叠加（`on_startup` 在 00/02/04/05/06/07/08/09/10/12/13/14/15/16 共 14 个文件里都有）。
- 一个最小的完整文件示例见 `common/on_actions/00_testing_on_actions.txt`（21 行，官方自带的"临时测试钩子"范本）。

## 2. scope 语义：每个 hook 的 ROOT / FROM 是什么

这是 on_actions 最容易出错的地方。**原版文件里的注释就是权威说明**，直接抄下表（全部从 `common/on_actions/*.txt` 的注释摘录，附文件:行号）。

| hook | ROOT | FROM | 证据 |
|---|---|---|---|
| `on_startup` | **无具体国家** | 无 | `00_on_actions.txt:1633` 注释 `#Not run on a specific country.` |
| `on_daily` / `on_weekly` / `on_monthly` | 当前遍历到的国家（每国各跑一次） | —— | 函数体直接写国家 trigger：`08_bba_on_actions.txt:128-155`、`12_wuw_on_actions.txt:1211-1237` |
| `on_daily_TAG` / `on_weekly_TAG` / `on_monthly_TAG` | 该 TAG | —— | `00_on_actions.txt:5770`（`on_daily_GER`） |
| `on_state_control_changed` | **新控制者国家** | 旧控制者国家；`FROM.FROM` = state id | `00_on_actions.txt:5075` |
| `on_declare_war` | 宣战国 | 战争目标 | `00_on_actions.txt:709` |
| `on_war_relation_added` | 攻击方 | 防守方 | `00_on_actions.txt:4914` 前后 |
| `on_capitulation` | 投降国 | 战胜国 | `00_on_actions.txt:931` |
| `on_uncapitulation` | 原本投降的国家 | —— | `00_on_actions.txt:1165` |
| `on_annex` | 战胜国 | 被吞并国 | `00_on_actions.txt:1615` |
| `on_civil_war_end` | 内战赢家 | 被吞并方；**也会触发 `on_annex`** | `00_on_actions.txt:1397` |
| `on_civil_war_end_before_annexation` | 赢家 | 即将被吞并方（片刻后才会被吞，故此刻国家与领土都还在） | 该 hook 上方的原版注释 |
| `on_puppet` | 被傀儡国 | 宗主国（仅和会中触发） | `00_on_actions.txt:1543` 前注释 |
| `on_release_as_puppet` | 被释放国 | 释放者 | `00_on_actions.txt:1581` 前注释 |
| `on_release_as_free` | 被释放国 | 释放者 | `01_tfv_on_actions.txt:482` 前注释 |
| `on_subject_annexed` | 附庸 | 宗主 | `01_tfv_on_actions.txt:219` 前注释 |
| `on_subject_free` | 附庸 | 前宗主 | `01_tfv_on_actions.txt:38` 前注释 |
| `on_subject_autonomy_level_change` | 附庸 | 宗主 | 注释同上系列 |
| `on_government_exiled` | 流亡政府 | 东道国 | `04_mtg_on_actions.txt:444` 前注释 |
| `on_host_changed_from_capitulation` | 流亡政府（Root is exile） | 新东道国；`From.From` = 旧东道国 | `04_mtg_on_actions.txt:8-10` |
| `on_exile_government_reinstated` | 流亡政府 | 旧东道国 | `04_mtg_on_actions.txt:23-24` |
| `on_leave_faction` | 退出国 | 阵营领袖 | `00_on_actions.txt:511` |
| `on_join_faction` | 加入国（ROOT 与 THIS 都是） | 阵营领袖 | `00_on_actions.txt:649` |
| `on_create_faction` | —— | 加入者 | `00_on_actions.txt:559` 前注释 |
| `on_assume_faction_leadership` | 新领袖 | 旧领袖 | `04_mtg_on_actions.txt:3296` |
| `on_send_volunteers` | 派出国 | 接收国 | `06_bftb_on_actions.txt:523` 前注释 |
| `on_naval_invasion` | 入侵国 | ——（当前 scope 是被入侵的州） | `00_on_actions.txt:5690` 前注释 |
| `on_paradrop` | ——（每个单位触发一次） | —— | `00_on_actions.txt:5718` |
| `on_units_paradropped_in_state` | 被空降的州 | 空降国；**每次空降跑一次**（不是每个单位） | `00_on_actions.txt:5798-5801` |
| `on_nuke_drop` | —— | —— | `00_on_actions.txt:384` |
| `on_pride_of_the_fleet_sunk` | 沉船所属国 | 击沉方 | `04_mtg_on_actions.txt:3260` |
| `on_before_peace_conference_start` | 战胜国 | 战败国（对所有胜-负组合各调一次） | `common/on_actions/_documentation.md:26` |
| `on_peaceconference_started` / `on_peaceconference_ended` | 战胜国 | 战败国 | `_documentation.md:27-28`；`00_on_actions.txt:5020` 前后 |
| `on_army_leader_daily` / `on_army_leader_won_combat` / … | 将领（character） | 所属国家 | `00_on_actions.txt:5548` 前注释 |
| `on_navy_leader_won_combat` | THIS = 海军将领 | FROM = 所属国，`FromFrom` = 战斗单位 | `00_on_actions.txt:5613` 前注释 |
| `on_mio_size_increased` | MIO 对象 | —— | `09_aat_on_actions.txt:6` 前注释 |
| `on_fully_decrypted_cipher` / `on_activated_active_decryption_bonuses` | 解密方国家 | 被解密国家 | `05_lar_on_actions.txt:344,351` 前注释 |

> ⚠️ 上表只覆盖最常用的；**完整列表**见 `common/on_actions/_documentation.md`（顶部标注 `(updated 2024-11)`，按 General/Politics/Diplomacy/Faction/Autonomy/States/Wargoals/Unit Leader/Aces/LaR/MIO 分组）。这份列表**已滞后于 1.19.x**，见下一节。

## 3. 文档滞后：1.19.3 实际在用的 115 个 key

用脚本统计 `common/on_actions/*.txt` 里所有**一级 key**（一个 tab 缩进的 `xxx = {`），1.19.3 实际出现 115 个。其中**未被 `_documentation.md` 收录**的有：

`on_add_history`、`on_call_allies`、`on_join_allies`、`on_project_completion`、`on_subject_annex`、`on_units_paradropped_in_state`、`on_unit_leader_promote_from_ranks_green`、`on_unit_leader_promote_from_ranks_veteran`

另外 `_documentation.md` 里有明显拼写错误：文档写 `on_mio_tech_reseach_completed/cancelled`，而实际文件里是 `on_mio_tech_research_completed` / `on_mio_tech_research_cancelled`（`09_aat_on_actions.txt`）。**以实际文件里的拼写为准。**

实测在用的 TAG 变体（可照此扩展）：`on_daily_AST/ETH/GER/ITA/SOV/SWE`、`on_weekly_BUL/ECU/ETH/FIN/GER/RAJ/SOV/SWE/VEN`、`on_monthly_AFG/AUS/BUL/CHI/COG/CZE/ENG/GER/JAP/MEX/NOR/PAL/PER/RAJ/SIA/SOV/SWE`。

## 4. 正确/错误用法对照

| 场景 | ✅ 正确 | ❌ 错误 | 后果 |
|---|---|---|---|
| 开局初始化国家 | `on_startup = { effect = { SWE = { MY_init = yes } } }` | `on_startup = { effect = { MY_init = yes } }`（无 scope） | `Invalid Scope, supported: Country, provided: None`，初始化不生效 |
| 每天检查某国 | `on_daily_SWE = { effect = { ... } }` | `on_daily = { effect = { SWE = { ... } } }` | 能跑，但**每个国家都跑一遍**，性能差 |
| 州易手时处理 | `on_state_control_changed = { effect = { ... } }` 里用 `ROOT`/`FROM`/`FROM.FROM` | 假设 `ROOT` 是州 | `FROM.FROM` 才是州 |
| 想"每次 X 时执行脚本" | 找对应 hook；没有就 `on_daily` + flag | 自己写 `on_action` 新名字 | **静默不执行**，无任何报错 |

## 5. `random_events`：钩子直接掷事件

```pdx
# 放置路径：common/on_actions/zz_MY_on_actions.txt
on_actions = {
    on_monthly_SWE = {
        random_events = {
            100 = MY_ns.10       # 权重 100 -> 事件 MY_ns.10
            50 = MY_ns.11
            0 = MY_ns.12         # 权重 0 = 永不触发（常用作"占位/开关"）
        }
    }
}
```

- 事件 id 必须已在自己的 `events/*.txt` 里定义，否则报 `Unknown event` 类错误或静默跳过。
- 事件是否真的能被触发，还取决于事件本身的 `is_triggered_only` / `trigger`（见 [../02_content/events.md](../02_content/events.md)）。`random_events` 走的是"直接触发"路径。

## 6. `on_startup`：唯一的"开局初始化"入口

为什么必须用它：**`history/countries/*.txt` 是给"新开局"读的静态文件**，而 mod 常常需要"按条件动态初始化"（比如按玩家国家/规则给不同变量）。`on_startup` 是加载完成后的第一个钩子，也是原版自己用的做法（`common/on_actions/00_on_actions.txt:2` 起就在补运河/水坝）。

```pdx
# 放置路径：common/on_actions/zz_MY_on_actions.txt
# 完整可跑：开局给所有国家初始化变量，并给瑞典一个动态 modifier
on_actions = {
    on_startup = {
        effect = {
            # ① 全局初始化（只跑一次）
            set_variable = { global.MY_world_tension = 0 }

            # ② 遍历所有已存在国家，做通用初始化
            every_country = {
                limit = { exists = yes }
                set_variable = { MY_score = 0 }
                set_variable = { MY_ready = 0 }
            }

            # ③ 给特定国家做特殊初始化（必须显式切 tag）
            SWE = {
                set_variable = { MY_score = 10 }
                add_dynamic_modifier = { modifier = MY_economy_modifier }
                MY_recalc_score = yes
                log = "MY: Sweden initialized on startup"
            }
        }
    }

    # ④ 每日检查（只对 SWE，性能友好）
    on_daily_SWE = {
        effect = {
            if = {
                limit = { check_variable = { MY_score > 50 } }
                add_stability = 0.001
            }
        }
    }

    # ⑤ 州易手：记录"最后易手的州"到全局变量（ROOT=新控制者, FROM=旧, FROM.FROM=州）
    on_state_control_changed = {
        effect = {
            if = {
                limit = { ROOT = { tag = SWE } }
                FROM.FROM = {                              # 切到州 scope 再读 id
                    set_variable = { global.MY_last_swedish_state = id }
                }
            }
        }
    }
}
```

> 在 effect 里"取某个对象身上的字段当数值"，安全写法是**先切到那个 scope**（`FROM.FROM = { ... id ... }`），而不是写 `FROM.FROM.id` 这种长链——切 scope 的写法在原版里随处可见且语义明确（`id` 在 state/country scope 上可读，见 `common/decisions/WTT_border_conflicts.txt:207-208`）。

## 7. 性能注意（on_actions 是性能重灾区）

1. **`on_daily` / `on_weekly` / `on_monthly`（不带 TAG）= 每个国家各跑一次**。里面再套 `every_country` 就是 O(国家数²)。原版 `08_bba_on_actions.txt:157` 就在 `on_monthly` 里套了 `every_country`——它能跑是因为有 `global_unification_request_sent_flag` 提前短路；**你写的时候一定要有等价的短路条件**。
2. **优先用 TAG 变体**（`on_daily_SWE`）而不是在通用 hook 里 `if tag = SWE`；这是引擎层的过滤，省掉绝大多数调用。
3. `on_army_leader_daily` 每个将领每天都会跑；`on_state_control_changed` 在战争初期可能一回合爆几十次。**这些 hook 里不要放 `every_state` / `every_country` 级别的遍历**。
4. 能"事件驱动"就别"每日轮询"：例如"某国投降后做 X"用 `on_capitulation`，不要写 `on_daily` 检查 `has_capitulated`。
5. 需要在 hook 里做重活时，先 `set_country_flag` 做一次性保护（原版通行做法，如上面 bba 的全局 flag）。

## 8. 常见错误 / 自检清单

**error.log 关键字（on_actions 相关）**

- **拼错 hook 名 → 完全没有报错**。这是最坑的：`on_dailly_SWE` 不会进 `error.log`，只会什么都不发生。排查靠：`log = "..."` 埋点 + 确认 `game.log` 有没有输出。
- 在 `on_startup` 里直接写国家 trigger/effect → `[...][trigger.cpp:460]: common/...: has_country_flag: Invalid Scope, supported: Country, provided: None`
- hook 里的 effect 拼错 → `[effect.cpp:358]: Error: "Unknown effect-type: xxx, near line: N" in file: "common/on_actions/zz_MY_on_actions.txt"`
- `random_events` 里事件 id 写错 → 触发时静默跳过；若 id 格式非法（少了 `.N`）可能在加载期报 `Invalid event` 类错误。
- 文件里 `on_actions = { }` 外层壳漏了 → 整个文件被忽略（无报错）。这是新手最常见的问题。

**自检清单**

- [ ] 文件有 `on_actions = { ... }` 外层壳。
- [ ] hook 名是**从原版文件里复制**的（不是凭记忆拼的）。
- [ ] 用了 `on_startup` 就检查里面每个 effect 都显式切了 scope（`TAG = { ... }` 或 `every_country = { ... }`）。
- [ ] 用了 `ROOT`/`FROM`/`FROM.FROM` 就对照第 2 节的表确认语义。
- [ ] 通用 `on_daily/on_weekly/on_monthly` 里有"提前短路"条件（flag/global flag）。
- [ ] 每个 hook 里放了一条 `log = "..."`（调试期），确认它真的被执行。
- [ ] 事件 id 在 `events/*.txt` 里存在；事件本身允许被直接触发。
- [ ] 改完重启游戏（新增/修改 on_actions 没有可靠热重载）。
- [ ] 跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。
- [ ] 完整钩子清单与 6-workflow 的调试流程交叉参考：[../06_workflow/debugging.md](../06_workflow/debugging.md)。

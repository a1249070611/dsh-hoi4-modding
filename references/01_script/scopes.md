---
title: 作用域（Scopes）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - documentation/loc_objects_documentation.md
  - common/on_actions/00_on_actions.txt
  - common/decisions/WTT_border_conflicts.txt
  - logs/error.log
---

# 作用域（Scopes）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**scope = "当前这段脚本在哪个游戏对象上执行"**。HOI4 的每条 effect/trigger 都只对自己支持的 scope 类型有效；scope 错了，轻则报错刷屏，重则整块脚本静默失效。

## 1. scope 类型全表（1.19.x）

从官方文档的 `## Effects for scope XXX` / `## Triggers for scope XXX` 分节可以穷举出引擎的 scope 类型。用脚本统计 `documentation/*.md` 里所有 `* Supported Scopes:` 行，得到 14 种：

| scope | 中文 | 典型对象 | 说明 |
|---|---|---|---|
| `COUNTRY` | 国家 | tag（`GER`） | 最常用；绝大多数 effect 都是 COUNTRY scope |
| `STATE` | 州 | state id（`58`） | 建筑、抵抗、人口、资源都在这里 |
| `CHARACTER` | 角色 | 将领/顾问/科学家/领袖 | 1.9 以后角色系统统一成 character |
| `COMBATANT` | 战斗单位 | 师/舰队/空军联队 | 战斗相关 trigger |
| `ACE` | 王牌飞行员 | ace | 数量少 |
| `STRATEGIC_REGION` | 战略区 | region id | 少量 effect |
| `OPERATION` | 情报行动 | operation 实例 | La Resistance |
| `INDUSTRIAL_ORG` | 军工组织（MIO） | `mio:token` | Arms Against Tyranny |
| `SPECIAL_PROJECT` | 特殊项目 | `sp:token` | Gotterdammerung |
| `PURCHASE_CONTRACT` | 采购合同 | 国际军售 | 1.15+ 国际市场 |
| `RAID_INSTANCE` | 突袭实例 | raid | 1.15+ |
| `FACTION` | 阵营 | 阵营对象 | 1.15+ 阵营目标系统 |
| `any` | 任意 | —— | 写作 `Supported Scopes: any`，即"任何 scope 下都能用"（如 `if`、`set_variable`、`log`） |

验证方式：`documentation/effects_documentation.md` 里共出现 15 种 `Supported Scopes` 组合（含 `any`），`documentation/triggers_documentation.md` 里 16 种；两者并集即上表。**如果某个 effect 不在对应 scope 分节里，就不要在那种 scope 里用它。**

## 2. 根 scope 是谁？—— 由"谁调用了这段脚本"决定

| 入口 | 根 scope（ROOT） | 证据 |
|---|---|---|
| `country_event` 的 `immediate` / `option` / `after` | 事件所属国家 | 事件体里直接写 `add_political_power`、`has_country_flag`（COUNTRY scope effect/trigger） |
| 国策 `completion_reward` / `available` / `visible` | 国策所属国家 | 同上 |
| 决议 `complete_effect` / `available` / `visible` | 决议所属国家 | 同上 |
| `on_startup` | **没有具体国家** | `common/on_actions/00_on_actions.txt:1633` 原版注释：`#Not run on a specific country.`（所以在里面必须显式 `GER = { ... }`） |
| `on_daily_TAG` / `on_monthly_TAG` / `on_weekly_TAG` | 该 TAG | `common/on_actions/00_on_actions.txt:5770` 的 `on_daily_GER` 直接写 `has_country_flag` 等国家 trigger |
| `on_state_control_changed` | ROOT = 新控制者，FROM = 旧控制者，FROM.FROM = 州 | `common/on_actions/00_on_actions.txt:5075` 原版注释：`#ROOT is new controller #FROM is old controller #FROM.FROM is state ID` |
| `scripted_gui` 的 `effects` | 由 `context_type` 决定 | 见 [05_presentation/scripted-gui.md](../05_presentation/scripted-gui.md) |

> 各内容系统（国策/事件/决议）的完整根 scope 规则见 [../02_content/events.md](../02_content/events.md)、[../02_content/focus-trees.md](../02_content/focus-trees.md)、[../02_content/decisions.md](../02_content/decisions.md)。

## 3. scope 导航词（写在 effect/trigger 的 block 上用）

官方文档每条 effect 都带一行 `* Supported Targets: THIS, ROOT, PREV, FROM, OWNER, CONTROLLER, OCCUPIED, CAPITAL`，这一行就是"我可以跳到哪"。用法是把导航词当**块级 key**：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_scope_demo = {
    # 当前 scope 是国家（假设由 country_event 调用）
    add_political_power = 10

    FROM = {                      # 跳到 FROM（例如事件里被触发的另一方）
        add_political_power = -10
    }
    ROOT = {                      # 跳到本次执行的根 scope
        set_country_flag = MY_flag
    }
    PREV = {                      # 跳到上一层 scope（进入块之前的那个）
        log = "back to previous scope"
    }
    owner = {                     # 州 scope 里：跳到此州的拥有者（大小写不敏感）
        add_stability = 0.01
    }
    controller = {                # 州 scope 里：跳到此州的控制者
        add_war_support = 0.01
    }
    capital_scope = {             # 国家 scope 里：跳到首都州（原版一律用这个写法）
        add_building_construction = { type = infrastructure level = 1 instant_build = yes }
    }
}
```

| 导航词 | 语义 | 备注 |
|---|---|---|
| `THIS` | 当前 scope 自己（显式写出，等价于不写） | 在 `check_variable = { THIS.x > 1 }` 里常用 |
| `ROOT` | 本次执行链的根 scope，**不会**被迭代器改变 | 在 `every_country` 里仍指最初那个国家 |
| `PREV` | 进入本块之前的 scope | 迭代器里 = 外层 scope（见第 6 节） |
| `FROM` / `FROM.FROM` | 事件/on_action 的"另一方"；可链式 | `FROM.FROM` 在 `on_state_control_changed` 里是州 |
| `OWNER` / `CONTROLLER` / `OCCUPIED` | 州→国家；占领相关 | 在 STATE scope 有效 |
| `capital_scope` | 国家→首都州 | 原版用例：`common/ai_areas/ai_faction_theaters.txt:41`（`capital_scope = { is_on_continent = europe }`）。⚠️ 官方文档的 `Supported Targets` 里写的是 `CAPITAL`，但原版**没有** `CAPITAL = { }` 的用例；**推荐 `capital_scope`** |
| ⚠️ `overlord` / `faction_leader` | 宗主 / 阵营领袖 | 见 wiki [Scopes](https://hoi4.paradoxwikis.com/Scopes)（抓取 2026-10-26）；本机未逐条验证 |
| `Country` / `State` / `Character` / `UnitLeader` … | **升格词**：把当前 scope 提升为某类型的对象 | 官方 `documentation/loc_objects_documentation.md:533-599` 的 `## Scope` → `### Promotions` 列全了：`Player`、`This`、`THIS`、`Root`、`Operation`、`Unit`、`Ace`、`IndustrialOrganisation`、`Prev`、`Character`、`PurchaseContract`、`Country`、`From`、`SpecialProject`、`State`、`Combatant` |

> 大小写不敏感：官方与社区混用 `ROOT`/`root`、`FROM`/`from`、`OWNER`/`owner`，实测原版文件里两种写法都存在（`common/decisions/AFG.txt:511` 用 `OWNER = {`，同文件 560 行用 `owner = {`）。**推荐一律大写**，便于和普通 key 区分。

## 4. 把"一个对象"直接当 scope 用

除了导航词，下列写法也能切换 scope（这在旧教程里几乎没人讲，是 1.19 里非常常用的写法）：

| 写法 | 含义 | 证据 |
|---|---|---|
| `GER = { ... }` | 切到该国家 | 遍布原版，如 `common/on_actions/00_on_actions.txt:1638` |
| `58 = { ... }` | 切到该 state id | `common/on_actions/00_on_actions.txt:10`（`58 = { add_building_construction = ... }`） |
| `event_target:my_target = { ... }` | 切到之前 `save_event_target_as` 存下的对象 | `common/decisions/anti_japan_infiltration.txt:102`：`event_target:WTT_communist_china = { country_event = wtt_infiltration.6 }` |
| `var:my_var = { ... }` | 切到变量里存的对象 | `common/ai_strategy/generic_operation_strats.txt:6`：`var:generic_operation_target = { ... }`；`common/decisions/AST.txt:699`：`var:FROM.AST_communist_civil_war_enemy_country = { ... }` |
| ⚠️ `global.my_var = { ... }` | 把全局变量里的对象当 scope | **待验证**：本机原版文件里没找到这种用法。要"存一个对象留到以后"，优先用 `event_target`（有 `has_event_target` 可校验）或普通 `var:` 变量 |
| `var:tag_name`（作为参数） | 把变量当"对象引用"传给 `target =`/`tag =` 等参数 | `documentation/effects_documentation.md:2907`：`SOV = { complete_special_project = var:my_project_var }` |

事件目标（event target）是"临时对象引用"的官方机制，效果是把某个 scope 存下来给后续脚本用：

```pdx
# 放置路径：events/MY_events.txt（放在 immediate 里）
country_event = {
    id = my_ns.1
    is_triggered_only = yes

    immediate = {
        # 把 FROM 这个国家存成事件目标，之后在其它事件里可以 event_target:MY_saved_country = { ... }
        FROM = { save_event_target_as = MY_saved_country }
        # 全局事件目标：任何国家、任何脚本都能用
        save_global_event_target_as = MY_global_country
    }

    option = {
        name = my_ns.1.a
        event_target:MY_saved_country = {
            add_opinion_modifier = { target = ROOT modifier = MY_opinion }
        }
    }
}
```

配套 effect/trigger：`save_event_target_as`、`save_global_event_target_as`（`documentation/effects_documentation.md:6496,6505`）、`clear_global_event_target`、`clear_global_event_targets`（同文件 2733/2742）、trigger `has_event_target`（`documentation/triggers_documentation.md:3844`，"checks if current scope or global scope has the specified event target saved"）。

生命周期差异（wiki 补充，[Effect](https://hoi4.paradoxwikis.com/Effect)，抓取 2026-10-26）：

- `save_event_target_as`：作用域内的临时保存，**本次执行结束后清除**（例如事件结束就没了）；且 "Do not use in Scripted GUIs"。
- `save_global_event_target_as`：持久保存，直到被 `clear_global_event_target(s)` 清除。

## 5. trigger 里的 scope 块

trigger 里同样用 `XXX = { ... }` 切 scope，只是语义变成"在那个 scope 下判断"。**注意：trigger 的 scope 块不会改变外部 scope**，只是局部求值。

> ⚠️ 一个文档缺口：**"建筑等级触发器"**（`infrastructure`、`industrial_complex`、`arms_factory`…）在 `triggers_documentation.md` 里**没有单独词条**，但原版大量使用，写法是"建筑 token + 比较符 + 数值"，仅在 STATE scope 有效：
> - `common/ai_strategy/ROM.txt:46` → `infrastructure < 4`
> - `common/scripted_effects/00_scripted_effects.txt:29-30` → `industrial_complex > 0`
> 想把建筑等级当**数值**用（而不是判断），用动态变量 `building_level@industrial_complex` / `industrial_complex_level`（`documentation/dynamic_variables_documentation.md:1101,1130`）。

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
MY_has_ally_with_core_on_my_capital = {
    # 当前 scope = 国家
    any_allied_country = {
        # 这里 scope 变成盟友国家
        any_owned_state = {
            # 这里 scope 变成盟友的州
            is_core_of = PREV.PREV    # PREV.PREV 回到"我"（外层外层）
        }
    }
}
```

## 6. 迭代器会改 scope —— PREV / ROOT / FROM 的相对关系

这是最容易写错的地方。官方在 `common/collections/_documentation.md:24-36` 里把语义写得很明确（针对集合的 `limit`，但同构于所有迭代器）：

> `SCOPE` = element of the input collection（元素）
> `PREV` = previous scope, defined by the context in which the collection is used（进入迭代器之前的 scope）
> `ROOT` = `PREV.ROOT`
> `FROM` = `PREV.FROM`
> "NOTE: the scope structure above mimics the scope structure of other `every_xxx` effects"

原版真实用例（注意 `@PREV` 就在迭代器内部用）：

```pdx
# 摘自 common/scripted_triggers/00_scripted_triggers.txt:31-57（节选，非完整文件）
has_not_initiated_border_incident_with_FROM = {
    # NOTE this check is very expensive! Use it with caution.
    custom_trigger_tooltip = {
        tooltip = not_initiated_border_incident_with_FROM
        NOT = {
            any_state = {                       # ← 进入州迭代器，scope = 州，PREV = 外层国家
                check_variable = { FROM.defender_state_vs_@PREV = id }   # @PREV 用在变量 target 上
            }
        }
    }
}
```

规则总结：

- `every_xxx` / `random_xxx` / `any_xxx` / `all_xxx` 内部：**`THIS` = 元素，`PREV` = 外层，`ROOT` 不变，`FROM` 不变**。
- 迭代器可以嵌套，每进一层 `PREV` 就往前推一层（`PREV.PREV` 回到两层外）。
- `save_event_target_as` 存下来的是"存的那一刻的 scope"，之后再 `event_target:x` 切换时 `PREV` 是当前块的外层，而不是当初那个 scope 的上下文。

## 7. 完整可跑示例：一次跨 4 种 scope 的操作

放到你自己的 mod 里，由 [on_actions](on-actions.md) 的 `on_startup` 调用一次即可观察效果。

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 调用方式（任选其一）：
#   on_startup 里：effect = { MY_scope_tour = yes }
#   控制台：effect GER MY_scope_tour
MY_scope_tour = {
    # 当前 scope：由调用方决定（这里是德国）
    set_country_flag = MY_scope_tour_done

    capital_scope = {                             # 国家 → 州
        add_building_construction = {
            type = infrastructure
            level = 1
            instant_build = yes
        }
        owner = {                                 # 州 → 拥有者国家（又回到国家）
            add_political_power = 5
        }
    }

    every_owned_state = {                         # 迭代：每个州
        limit = { is_core_of = ROOT }             # 只处理核心州；ROOT 仍是德国
        if = {
            limit = { industrial_complex > 0 }    # 州 scope trigger
            set_state_flag = MY_industrial_state
            PREV = {                              # PREV = 外层（德国）
                add_stability = 0.005
            }
        }
    }

    random_owned_state = {                        # 随机一个州
        limit = { is_coastal = yes }
        save_event_target_as = MY_sample_coast
        log = "MY: sampled coastal state [This.GetName]"
    }

    event_target:MY_sample_coast = {              # 之后仍可切回这个州
        add_extra_state_shared_building_slots = 1
    }
}
```

## 7.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Scopes）

**PREV 的 tooltip 与实际执行不一致**（wiki 明示的引擎行为）：tooltip 显示的内容不总是真实执行的——指向 `every_`/`all_` 型 scope 时只显示第一个可能目标，实际执行正常。需要给玩家看准确说明时，用 `hidden_effect` + `custom_effect_tooltip`（效果侧）或 `custom_trigger_tooltip`（触发侧）替换。

**invalid event target 的标准防御写法**：`overlord` / `controller` / `faction_leader` / `owner` 这些 dual scope 在上下文无目标时会刷 `invalid event target`（每 tick 一次）且效果被完全跳过。防御 = 先用 if 确认条件再进 scope：

```pdx
if = {
    limit = { is_subject = yes }
    overlord = { country_event = example.0 }
}
```

**limit 只能用在 effect scope**：`any_`/`all_` 触发器里写 `limit = { ... }` 是无效语法（静默）。`random_select_amount`（最多选 N 个）与 `prioritize`（州类 random scope 的优先州）是 effect 侧专属。

**三组前缀的完整语义**：`all_` = 全部满足才真（trigger）；`any_` = 任一满足即真，支持 `count = N`（至少 N 个满足）；`every_`/`random_` = 效果侧迭代。除 `every_possible_country` 外，这些 scope **不能选中不存在的国家**（分崩离析后的 tag 会静默失败）。

**游戏没有闰日**：一年固定 365 天，`days = 365` 即次年 1 月 1 日。按日期写的 trigger 在 2 月 29 日附近的预期要与引擎一致。

## 8. 常见错误 / 自检清单

**error.log 里"作用域错"长什么样**（本机真实日志格式）：

- **scope 完全为空**（在 `on_startup`、`scripted_gui`、全局脚本里误用国家 trigger/effect）：
  `[...][trigger.cpp:460]: common/technology_tags/00_technology.txt:355: has_country_flag: Invalid Scope, supported: Country, provided: None`
  → 读法：`supported: Country` = 这条只认国家；`provided: None` = 当前根本没有 scope。**修复：显式 `SOMETAG = { ... }` 包一层。**
- **effect 用错 scope**：通常表现为 `Unknown effect-type`（引擎在当前 scope 的 effect 表里找不到这个名字），例如
  `[effect.cpp:358]: Error: "Unknown effect-type: ai_create_variant/twin_cas_equipment, near line: 1668" in file: "common/technologies/FRA_air.txt"`
  注意：**"Unknown effect-type" 不一定是拼错，也可能只是 scope 不对**（该 effect 不在此 scope 的可用表里）。
- **trigger 用错 scope**：`[trigger.cpp:568]: Error: "Unknown trigger-type: RGR, near line: 139"`、`[trigger.cpp:700]: Invalid trigger 'RGR' in ... line : 139`。
- **把 tag 当 trigger 名**（常见笔误：想写 `tag = RGR` 却写成 `RGR = yes`）就会得到上面那条 `Unknown trigger-type: RGR`。

**自检清单**

- [ ] 每个 effect/trigger 我都能在 `documentation/effects_documentation.md` / `triggers_documentation.md` 的对应 scope 分节里找到它（或 `Supported Scopes: any`）。
- [ ] 进 `every_`/`random_` 块之前先写下"THIS 是 X、PREV 是 Y、ROOT 是 Z"，再写 body。
- [ ] 在 `on_startup` / 全局脚本里操作国家，一律先用 `TAG = { ... }` 或 `every_country = { limit = { ... } ... }` 明确 scope。
- [ ] 事件里用 `FROM` 前确认事件是 `country_event = { ... }` 且调用时给了 `FROM`（如 `country_event = { id = x FROM = GER }`），否则 `FROM` 为空 → 相关判断全部为 false（**静默失败**，不报错）。
- [ ] 用 `event_target:` 之前确认目标确实被 `save_event_target_as` 过；配合 `has_event_target = MY_target` 做防御判断，避免对空 scope 执行 effect（空 scope 上的 effect 被跳过，往往"什么都没发生"）。
- [ ] 州 id / 国家 tag 直接当 scope 时，确认它们存在；不存在的 tag 不会报错，只会静默什么都不做。

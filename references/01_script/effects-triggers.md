---
title: effect 与 trigger（执行与求值模型）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/scripted_effects/SOV_scripted_effects.txt
  - common/scripted_effects/CZE_scripted_effects.txt
  - common/on_actions/00_on_actions.txt
  - common/decisions/DEN.txt
  - common/bop/CZE.txt
  - logs/error.log
---

# effect 与 trigger（执行与求值模型）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**effect 是"动作"，只在块被真正执行时跑一次；trigger 是"命题"，会被反复求值——包括为了画 tooltip 而求值。** 把这条分清，80% 的"脚本没反应"和"性能莫名其妙差"都能自解释。

## 1. 两种原语

| | effect | trigger |
|---|---|---|
| 回答什么 | "做什么"（改状态） | "是否成立"（返回值） |
| 文档 | `documentation/effects_documentation.md`（553 条） | `documentation/triggers_documentation.md`（596 条） |
| 能否返回数值 | 不能（副作用型） | 能（`has_army_size > 10`、`num_owned_states > 5` 等可比较） |
| 放错位置 | 放进 trigger 块 → `Unknown trigger-type: xxx` | 放进 effect 块 → `Unknown effect-type: xxx` |
| 执行次数 | 所属块执行一次就一次 | **可能被执行多次**（tooltip 绘制、AI 评估、每日检查……） |

区分方法：看文档词条里写的是什么。`add_political_power`（effect）、`has_war`（trigger）不会混淆；真正容易混的是同一概念的成对词条，例如 `has_global_flag`（trigger）vs `set_global_flag`（effect）、`check_variable`（trigger）vs `set_variable`（effect）。

## 2. 求值时机（执行模型）

| 时机 | effect | trigger | 证据/说明 |
|---|---|---|---|
| 加载 `common/*` 时 | 不执行 | 不执行（只校验） | 加载阶段只解析与校验，见 error.log 里 `Unknown effect-type` 出现在加载期 |
| `on_startup` | 执行一次 | 可求值 | `common/on_actions/00_on_actions.txt:2`（原版第一件事就是补运河/水坝建筑） |
| `on_daily` / `on_weekly` / `on_monthly` | 按周期执行 | 可求值 | `common/on_actions/_documentation.md` |
| 事件 MTTH 判定 | —— | 反复求值 | 见 [../02_content/events.md](../02_content/events.md) |
| 事件 `immediate`/`option`/`after` | 执行 | 可求值 | —— |
| 决议 `available`/`visible`/`complete_effect` | 执行 | 求值（界面显示与可点性） | 见 [../02_content/decisions.md](../02_content/decisions.md) |
| **为画 tooltip** | **不执行**（除非放进 `effect_tooltip`？见第 8 节） | **会求值** | `documentation/triggers_documentation.md:5103-5114` 明说：hidden_trigger "can still be evaluate when generating a tooltip"，并可选择 `eval`/`no_eval`/`legacy` |
| 动态 modifier 数值 | —— | —— | 官方注释：动态 modifier "will only updated daily, unless forced by `force_update_dynamic_modifier`"（`common/dynamic_modifiers/0_dynamic_modifiers.txt:27`） |

**推论（重要）**：trigger 里出现 `set_temp_variable` / `add_to_variable` 这类有副作用的 effect，会被 tooltip 绘制重复执行 → 数值随机漂移、变量莫名其妙翻倍。官方为此专门造了 `hidden_trigger` + `tooltip_evaluation`。

## 3. `if` / `else` / `else_if`

官方 effects 文档只列了 `if`（"a conditional effect"）而**没有** `else`/`else_if` 词条（`documentation/effects_documentation.md:4677`），但 1.19.x 引擎明确支持后两者——原版有数千处用例（如 `common/decisions/DEN.txt:434`、`common/scripted_effects/CZE_scripted_effects.txt:449`）。这是"文档滞后于引擎"的典型案例。

```pdx
# 放置路径：common/decisions/MY_decisions.txt（完整可跑：一个三级判定 + 兜底）
MY_check_infrastructure_tier = {
    if = {
        limit = {
            any_owned_state = { infrastructure > 6 }
        }
        set_country_flag = MY_tier_high
        add_stability = 0.05
    }
    else_if = {
        limit = {
            any_owned_state = { infrastructure > 3 }
        }
        set_country_flag = MY_tier_mid
        add_stability = 0.02
    }
    else = {
        # else 不需要 limit
        set_country_flag = MY_tier_low
        add_stability = -0.02
    }

    # 文档里只有 if，但 else/else_if 是 1.19.x 实际支持的：
    # 判据 = 原版数千处用例 + 本机 error.log 无 Unknown effect-type: else_if
}
```

要点：

- `if` / `else_if` **必须**带 `limit = { <trigger> }`；`else` **不能**带 `limit`。
- `else` / `else_if` 要紧跟在配对的 `if`（或上一个 `else_if`）块之后书写，保证可读性与预期配对。
- key 大小写不敏感：原版混用 `if = {` 与 `IF = {`（`common/scripted_effects/SOV_scripted_effects.txt:7297` 就是 `IF = {`）。
- tooltip 呈现：`if` 的 tooltip 只显示"命中的那个分支"里的效果；`else` 分支的呈现由引擎处理，如果玩家看不懂前因后果，就用 `custom_effect_tooltip` 明说（见第 8 节）。

## 4. 随机分支：`random` 与 `random_list`

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_random_demo = {
    # ① 单分支概率：chance 是 0..1 的浮点（可用变量 / 动态变量）
    random = {
        chance = 0.25
        add_political_power = 25
    }

    # ② 加权列表：权重可以是常量、变量名、或者带 modifier 的动态权重
    random_list = {
        log = yes                # 可选：把掷骰结果写进 game.log（官方条目支持）
        seed = my_seed_var       # 可选：var_name / const / random，改变随机源
        60 = {
            add_stability = 0.02
        }
        30 = {
            add_war_support = 0.02
        }
        10 = {                   # 原版权重项里还能写 modifier 动态缩放权重
            modifier = {
                factor = 0.5
                has_war = yes
            }
            add_war_support = 0.05
        }
    }
}
```

- `random = { chance = X ... }`：原版用例 `common/scripted_effects/NORDIC_scripted_effects.txt:534-537`（`chance = GLOBAL.NORDIC_current_risk`，直接用全局变量当概率）。
- `random_list`：官方条目 `documentation/effects_documentation.md:5413-5431`，支持 `log = yes`、`seed = var_name/const/random`、权重可为变量名。
- 权重项内写 `modifier = { factor = 0.25 <trigger> }`：官方条目未列，但原版 `common/on_actions/00_on_actions.txt:1672-1703` 大规模使用，且本机 `error.log` 无 `Unknown effect-type: modifier` → 可用。

## 5. 循环：四个 effect，一个都别用错

| effect | 用途 | 关键参数 | 文档行 |
|---|---|---|---|
| `while_loop_effect` | 条件为真就一直跑 | `limit`（每轮前判定）、`break`（临时变量名，非零则跳出） | 8573 |
| `for_loop_effect` | 数值区间循环 | `start`、`end`、`compare`（默认 `less_than`）、`add`（步长，默认 1）、`value`（当前值变量名，默认 `v`）、`break` | 4312 |
| `for_each_loop` | 遍历**数组** | `array`、`value`（默认 `v`）、`index`（默认 `i`）、`break` | 4279 |
| `for_each_scope_loop` | 遍历**存了 scope 的数组**，并把 scope 切到元素 | `array`、`break`、`tooltip` | 4296 |

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 注意：本机 common/ 下没有任何裸 while = { ... } 用例，旧教程里的 while 写法请改掉
MY_loop_demo = {
    # ① while：最多抽 5 个符合条件的将领，抽不到就自然结束
    set_temp_variable = { MY_i = 0 }
    while_loop_effect = {
        limit = {
            check_variable = { MY_i < 5 }
            any_army_leader = { NOT = { has_character_flag = MY_marked } }
        }
        random_army_leader = {
            limit = { NOT = { has_character_flag = MY_marked } }
            set_character_flag = MY_marked
        }
        add_to_temp_variable = { MY_i = 1 }
    }

    # ② for：给前 3 个州各加 1 级基建（配合数组或纯计数）
    for_loop_effect = {
        start = 0
        end = 3
        add = 1
        value = MY_step
        random_owned_state = {
            limit = { is_core_of = ROOT }
            add_building_construction = { type = infrastructure level = 1 instant_build = yes }
        }
    }

    # ③ for_each：遍历数组，变量默认叫 v / i
    for_each_loop = {
        array = MY_state_ids
        # 这里 v = 元素值，i = 下标；等价于原版 events/LaR_espionage_operations.txt:189-202
        log = "MY: array element [?v] at index [?i]"
    }

    # ④ for_each_scope：数组里存的是 scope（州/国家），遍历时自动切 scope
    for_each_scope_loop = {
        array = MY_saved_states
        set_state_flag = MY_visited
    }
}
```

`for_each_loop` 的原版真实用例：`events/LaR_espionage_operations.txt:189-209`（遍历 `fake_intel_ids_to_delete` 并 `delete_unit = { id = v }`；第二段还演示了 `array = ids_to_remove` + `remove_from_array = { fake_intel_ids_to_delete = v }`）。

## 6. 迭代器族：`every_` / `random_` / `all_` / `any_`

**effect 侧**（会执行 body）：

- `every_<类型>`：对**所有**命中 `limit` 的对象执行。
- `random_<类型>`：只对**一个**命中的对象执行（`random_select_amount = N` 可选择 N 个）。
- 通用参数（依据 `documentation/effects_documentation.md:3846-3856` 的 `every_country`，其余 `every_state`/`every_owned_state`/… 同构）：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_iterator_params = {
    every_state = {
        limit = { is_core_of = ROOT }        # 过滤
        tooltip = MY_tooltip_loc            # 覆盖 tooltip 标题
        random_select_amount = 3            # 只随机选 3 个（可选）
        display_individual_scopes = yes     # 每个对象单独显示一次效果（默认只显示一次）
        add_extra_state_shared_building_slots = 1
    }

    random_state = {
        limit = { is_coastal = yes }
        prioritize = { 42 43 }              # 优先从这些 state id 里挑（random_state 特有）
        add_state_modifier = { modifier = MY_state_modifier }
    }
}
```

> 常用 effect 迭代器（全部在 `documentation/effects_documentation.md` 的 `Supported Scopes` 里可查）：`every_country`、`every_other_country`、`every_possible_country`、`every_neighbor_country`、`every_state`、`every_owned_state`、`every_controlled_state`、`every_core_state`、`every_neighbor_state`、`every_army_leader`、`every_navy_leader`、`every_unit_leader`、`every_character`、`every_operative`、`every_scientist`、`every_faction_member`、`every_subject_country`、`every_collection_element`（见 [collections.md](collections.md)）；对应的 `random_*` 版本基本一一对应。完整清单直接查 `documentation/effects_documentation.md`。

**trigger 侧**（只判断，不执行）：

| trigger | 语义 | 文档行 |
|---|---|---|
| `any_<类型>` | 存在一个满足即真 | 1336（`any_country`） |
| `all_<类型>` | 全部满足才真 | 908（`all_country`） |
| `any_of` / `all_of` | 对**数组**逐个判断 | 1515 / 1036 |
| `any_of_scopes` / `all_of_scopes` | 对**scope 数组**逐个判断，元素切 scope | 1531 / 1052 |
| `count_triggers` | 至少 N 个子 trigger 为真 | 2402 |
| `always` | 恒真/恒假 | 1179 |

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
MY_iterator_triggers = {
    # 至少 3 个国家满足：与我同阵营且军队规模 > 20
    count_triggers = {
        amount = 3
        any_country = {
            is_in_faction_with = ROOT
            has_army_size = { size > 20 }
        }
    }

    # 数组判定：我的每个州的基建都 >= 3
    all_of = {
        array = MY_state_ids
        any_owned_state = { state = var:v  infrastructure > 2 }
    }

    # 对存了 scope 的数组逐个判断（元素会切成 scope）
    all_of_scopes = {
        array = MY_saved_states
        is_fully_controlled_by = ROOT
    }
}
```

## 7. `limit` 的三种身份

同一个 `limit` 关键字，三种位置三种含义——混用会写出看似正确实则逻辑错的脚本：

1. `if = { limit = { <trigger> } ... }`：分支条件。
2. `every_state = { limit = { <trigger> } ... }`：**过滤**遍历对象（不满足的条目直接跳过，不执行 body）。
3. `while_loop_effect = { limit = { <trigger> } ... }`：**每轮循环前**判定，为假即退出。

## 8. tooltip 语义四件套（这决定玩家看到什么）

| 关键字 | 类型 | 作用 | 文档行 |
|---|---|---|---|
| `hidden_effect = { ... }` | effect | 照常执行，但**不产生任何 tooltip** | 4659 |
| `custom_effect_tooltip = KEY` | effect | 在当前位置**追加**一条自定义 tooltip（不执行任何效果） | 3320 |
| `custom_override_tooltip = { tooltip = KEY <effects> }` | effect | 执行内部 effect，但用一个 tooltip **压制**内部所有 tooltip | 3343 |
| `effect_tooltip = { <effects> }` | effect | **只显示**内部 effect 的 tooltip，不执行它们 | 3644 |
| `hidden_trigger = { ... }` | trigger | 不显示，但仍参与求值（可配 `tooltip_evaluation`） | 5103 |
| `custom_override_tooltip = { tooltip = KEY <triggers> }` | trigger | 用一条自定义 tooltip 替代内部所有 trigger 的显示 | 2431 |
| `custom_trigger_tooltip` | trigger | **向后兼容别名**，等价于上面的 trigger 版 `custom_override_tooltip` | 2482 |

真实用法示例（原版 BOE / 平衡系统里非常典型：effect 在 `if` 分支里真执行，在 `else` 里只显示"如果…会怎样"）：

```pdx
# 摘自 common/bop/CZE.txt:51-55 的写法（同类用法遍布 common/bop/*.txt）
if = {
    limit = { has_idea = CZE_army_readiness_5 }
    swap_ideas = { remove_idea = CZE_army_readiness_5 add_idea = CZE_army_readiness_3 }
}
else = {
    effect_tooltip = {                      # 只展示，不执行
        add_ideas = CZE_army_readiness_3
    }
}
```

`hidden_trigger` 的三种求值模式（官方原文要点，`documentation/triggers_documentation.md:5115-5144`）：

- `eval`：标准求值。**有副作用或有随机成分时必须用这个**（否则 tooltip 与真实结果不一致）。
- `no_eval`：不做求值，只做"轻量计算"，更快；适用于没有副作用/随机的判定。
- `legacy`：旧行为，官方原话："Using this explicitly is very likely a bug."

`custom_effect_tooltip` 是 **bindable localization**（可嵌套绑定），还能直接用格式化器：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_tooltip_demo = {
    hidden_effect = {
        add_political_power = 50
    }
    custom_effect_tooltip = MY_gain_50_pp_tt              # 普通 loc key
    custom_effect_tooltip = idea_desc|canadian_pacific_railway   # 格式化器（documentation/loc_formatter_documentation.md:84-94）

    custom_effect_tooltip = {                              # 嵌套绑定：给 loc key 里的 $TOKEN$ 赋值
        localization_key = MY_complex_tt
        AMOUNT = "50"
        TARGET = { localization_key = MY_target_name }
    }
}
```

> loc key `MY_complex_tt = "You gain $AMOUNT$ pp because of $TARGET$."` 会渲染出嵌套后的文本。详见 [../05_presentation/localisation.md](../05_presentation/localisation.md)。

## 9. `meta_effect`：用字符串"拼"出 effect

当 effect 的**名字本身**依赖变量时（例如 `add_ideas = TAG_tier_3_idea` 的 tier 是变量），普通脚本做不到，要用 `meta_effect`：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_add_tiered_idea = {
    set_variable = { MY_tier = 3 }
    meta_effect = {
        text = {
            add_ideas = MY_tier_[MY_TIER]_idea
        }
        MY_TIER = "[?MY_tier]"     # 变量插值语法：变量用 [?name]
        debug = no                 # 设为 yes 可在 game.log 里看到真正执行的字符串
    }
}
# 原版同款：common/scripted_effects/CZE_scripted_effects.txt:442-448
#   meta_effect = { text = { add_ideas = CZE_skoda_no_focus_optimization_[SKODA_OPT]_idea }
#                   SKODA_OPT = "[?skoda_optimization_tier]" }
```

## 10. 完整可跑示例：一个"每日巡检"式脚本块

把这段放进你的 mod，用控制台 `effect SWE MY_full_demo` 就能跑（或挂到 `on_daily_SWE`）。

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_full_demo = {
    # 1) 记一个数：用数学表达式而不是手搓 temp（见 math-operators.md）
    set_variable = {
        MY_score = {
            value = num_owned_states
            multiply = 2
            add = num_divisions
            clamp = { min = 0 max = 100 }
        }
    }

    # 2) 分级 + 兜底，用 else
    if = {
        limit = { check_variable = { MY_score > 60 } }
        add_stability = 0.03
        custom_effect_tooltip = MY_high_score_tt
    }
    else_if = {
        limit = { check_variable = { MY_score > 30 } }
        add_stability = 0.01
    }
    else = {
        add_stability = -0.01
        hidden_effect = { set_country_flag = MY_needs_attention }
    }

    # 3) 加权随机：对表现好的州追加奖励
    random_list = {
        70 = { add_political_power = 10 }
        20 = { add_war_support = 0.01 }
        10 = {
            modifier = { factor = 2 has_war = yes }
            army_experience = 10
        }
    }

    # 4) 遍历 + 过滤，并用 hidden_effect 避免刷屏 tooltip
    every_owned_state = {
        limit = { is_core_of = ROOT  industrial_complex > 3 }
        hidden_effect = { add_state_modifier = { modifier = MY_industrial_bonus } }
        custom_effect_tooltip = MY_one_state_bonus_tt
    }

    # 5) log 落到 game.log，便于验证是否真的执行了
    log = "MY_full_demo ran, score = [?MY_score]"
}
```

## 11. 常见错误 / 自检清单

**error.log 关键字（1.19.3 真实格式）**

| 你看到 | 含义 | 修法 |
|---|---|---|
| `[effect.cpp:358]: Error: "Unknown effect-type: xxx, near line: N"` | 该 scope 下没有这个 effect（拼错 / scope 错 / 未加载到定义） | 查 `CHEATSHEET_effects.md`；确认 scope |
| `[trigger.cpp:568]: Error: "Unknown trigger-type: xxx, near line: N"` | 同上（trigger 版） | 常见于把 tag 写在 trigger 名位置 |
| `[trigger.cpp:568]: Error: "Not a valid value: penal_battalion, near line: N"` | 参数值不合法（枚举/装备/地形 token 写错） | 查对应枚举：`common/script_constants`、`common/script_enums.txt` |
| `[trigger.cpp:460]: file:line: has_country_flag: Invalid Scope, supported: Country, provided: None` | 当前没有 scope | 外面包 `TAG = { ... }` |
| `[script_math.cpp:351]: Error: "" in file: "..." near line: N` | 数学表达式解析失败（**空错误信息**，通常是表达式写残了） | 检查 `value = / add = / multiply =` 的括号与操作数 |
| `[scopedvariable.cpp:571]: xxx is not a valid mtth database object` | 把一个不存在的 token 当变量用 | 变量名写错，或没先在 `common/mtth/mtth_variables.txt` / 动态变量表里确认 |

**自检清单**

- [ ] `if`/`else_if` 每个分支都有 `limit`，`else` 没有 `limit`。
- [ ] 循环里一定会改变"退出条件"（`while_loop_effect` 忘了 `add_to_temp_variable` → **死循环，游戏卡死**）。
- [ ] `every_*` 里的 effect 会不会每个对象都刷一条 tooltip？需要时用 `hidden_effect` + 一条 `custom_effect_tooltip`。
- [ ] trigger 块里没有任何 `set_*_variable`、`add_to_*variable`、`random_*` 等有副作用/随机的 effect。
- [ ] `random_list` 所有权重加起来 > 0（全 0 时引擎行为无意义，等于白写）。
- [ ] 任何"应该执行但没执行"的脚本，先在 `game.log` 里放一条 `log = "..."`（`documentation/effects_documentation.md:4802`）确认块是否真的进来了。
- [ ] 静态校验：`python $SKILL/scripts/hoi4_lint.py <mod目录>`，零 error 再进游戏。

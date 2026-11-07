---
title: 变量（普通 / 临时 / 全局 / 数组 / 变量 target）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/decisions/WTT_border_conflicts.txt
  - common/scripted_effects/operation_strat_effects.txt
  - common/scripted_effects/WTT_china_political_struggle_effects.txt
  - common/scripted_triggers/00_scripted_triggers.txt
  - events/LaR_espionage_operations.txt
  - logs/error.log
---

# 变量（普通 / 临时 / 全局 / 数组 / 变量 target）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：HOI4 的变量是**挂在 scope 上的浮点槽位**（数组则是浮点/对象列表）。1.19.x 的变量体系比旧教程描述的多三层：`scope` 前缀、`@target` 目标、`^index` 下标。

## 1. 四种存储位置

| 种类 | 写法 | 生命周期 | 存盘 | 典型用途 |
|---|---|---|---|---|
| 普通变量 | `set_variable = { x = 1 }` | 跟着 scope 对象活到游戏结束 | ✅ | 玩家长期状态、计数器 |
| 临时变量 | `set_temp_variable = { x = 1 }` | **只在当前 effect/trigger 执行链内有效**，不持久化 | ❌ | 循环计数、中间结果 |
| 全局变量 | `set_variable = { global.x = 1 }` | 全局，任何 scope 都能读 | ✅ | 世界级状态、跨国家共享 |
| 数组 | `add_to_array = { x = 42 }` | 同普通变量 | ✅ | 列表、待办队列、候选对象集 |

临时变量的"生命周期"要精确理解：它存在于**本次脚本执行**的临时变量表里，同一条 effect 链上后续的块都能读（哪怕中间换过 scope、进过迭代器），但**不会**跨到下一个 tick 或下一个事件。所以：

- 在 `while_loop_effect` 里当循环计数器 ✅
- 在 `every_state` 里给每个元素算个中间值 ✅
- 想留给"下次触发时再用" ❌（必须用普通变量或 `global.`）

## 2. 变量的寻址：四种前缀组合

```
<scope>.var:<name>@<target>      # 完整形态
```

| 形态 | 例子 | 含义 |
|---|---|---|
| `var:name` | `var:MY_score` | 当前 scope 上的变量 |
| `var:SCOPE.name` | `var:FROM.my_var`、`var:ROOT.my_var` | 指定 scope 上的变量 |
| `var:name@TARGET` | `var:defender_state_vs_@ROOT` | **变量 target**：同名的"按对象分槽"变量，取 TARGET 那一槽 |
| `var:SCOPE.name@TARGET` | `var:FROM.defender_state_vs_@ROOT` | 上面两者叠加 |
| `global.name` | `global.days_add_support` | 全局变量 |
| `name` | `check_variable = { MY_score > 10 }` | 在 `check_variable`/`set_variable` 等语境里可省略 `var:` |

写完变量再用它：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_variable_paths = {
    # ① 当前 scope 的变量
    set_variable = { MY_count = 0 }
    add_to_variable = { MY_count = 1 }

    # ② 全局变量
    set_variable = { global.MY_world_counter = 0 }
    add_to_variable = { global.MY_world_counter = 1 }

    # ③ 把变量当参数传给需要数值的 effect
    add_political_power = var:MY_count
    add_stability = var:global.MY_world_counter

    # ④ 读别的 scope 的变量（FROM 是事件另一方）
    set_temp_variable = { MY_from_count = FROM.MY_count }
    log = "FROM count = [?MY_from_count]"
}
```

> 前缀顺序别搞反：是 `var:SCOPE.name`，不是 `SCOPE.var:name`。原版全部写作 `var:FROM.defender_state_vs_@ROOT` 这种形式（`common/decisions/WTT_border_conflicts.txt:219,236,263`）。

## 3. 变量 target：`name@TARGET` —— 1.19 最容易被旧教程漏掉的能力

"变量 target"让你**用同一个变量名，按目标对象分槽存值**。典型需求："我对每个国家的边境事件各自记一个州 id"——旧写法要拼 `SOV_state_vs_GER`、`SOV_state_vs_POL`…（数量爆炸），新写法一个变量搞定。

```pdx
# 放置路径：common/decisions/MY_decisions.txt
# 原版同构实现：common/decisions/WTT_border_conflicts.txt:195-226
MY_record_state_per_target = {
    # 当前 scope 是 A 国，FROM 是 B 国；对"B 国"这一槽记下某个州 id
    random_owned_controlled_state = {
        limit = { is_core_of = ROOT }
        set_variable = { FROM.MY_state_vs_@ROOT = id }    # 在 FROM 身上存"相对 ROOT 的那一槽"
    }

    # 读取同一槽（在 A 国 scope 里读 FROM 的槽）
    set_temp_variable = { MY_read_back = var:FROM.MY_state_vs_@ROOT }
    log = "recorded state = [?MY_read_back]"
}

MY_use_recorded_state = {
    # 把变量里的州 id 当 scope 用（注意 var: 后面整体是一个 scope 路径）
    var:FROM.MY_state_vs_@ROOT = {
        add_extra_state_shared_building_slots = 1
    }
    # 清理
    clear_variable = FROM.MY_state_vs_@ROOT
}
```

检查是否存在：

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
MY_has_recorded_state = {
    # 注意 has_variable 的参数也是"变量路径"，不是带 var: 的字符串
    has_variable = ROOT.MY_state_vs_@FROM
}
```

（原版写法：`common/scripted_triggers/00_scripted_triggers.txt:32` → `has_variable = ROOT.defender_state_vs_@FROM`；同文件 41 行还演示了在 `any_state` 里用 `check_variable = { FROM.defender_state_vs_@PREV = id }`。）

## 4. 变量操作 effect 全表

全部 `Supported Scopes: any`，即任何 scope 都能用（`documentation/effects_documentation.md`，行号为该词条起始行）。

| effect | 说明 | 行 |
|---|---|---|
| `set_variable` | 赋值；value 可为数值 / 另一变量 / 数学表达式；支持 `tooltip =` 覆盖提示 | 7888 |
| `set_temp_variable` | 同上，临时版 | 7820 |
| `add_to_variable` / `add_to_temp_variable` | 加 | 2343 / 2327 |
| `subtract_from_variable` / `subtract_from_temp_variable` | 减 | 8203 / 8187 |
| `multiply_variable` / `multiply_temp_variable` | 乘 | 5028 / 5012 |
| `divide_variable` / `divide_temp_variable` | 除 | 3609 / 3587 |
| `modulo_variable` / `modulo_temp_variable` | 取模 | 4999 / 4986 |
| `clamp_variable` / `clamp_temp_variable` | 夹到 `[min, max]`；**顺序是 `Max(Min(var,max),min)`**；`max < min` 在 debug 模式会报错 | 2695 / 2681 |
| `round_variable` / `round_temp_variable` | 四舍五入（可简写 `round_variable = x`） | 6486 / 6476 |
| `randomize_variable` / `randomize_temp_variable` | 随机化（官方词条写 "refer to randomize_temp_variable"） | 5656 / 5621 |
| `set_variable_to_random` / `set_temp_variable_to_random` | 随机赋值，支持 `min` / `max` / `integer = yes` | 7910 / 7842 |
| `clear_variable` | 删除变量（可简写 `clear_variable = x`） | 2773 |
| `print_variables` | 把 scope 上所有变量 + 临时变量打到文件（`file` / `text` / `append` / `print_global` / `var_list`） | 5133 |

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_variable_ops_demo = {
    set_variable = { MY_val = 37 }

    add_to_variable = { MY_val = 5 }                 # 42
    subtract_from_variable = { MY_val = 2 }          # 40
    multiply_variable = { MY_val = 1.5 }             # 60
    divide_variable = { MY_val = 4 }                 # 15
    modulo_variable = { var = MY_val value = 4 }     # 3
    clamp_variable = { var = MY_val min = 0 max = 10 }   # 3（已在范围内）
    round_variable = MY_val

    # 随机：[min, max)
    set_variable_to_random = {
        var = MY_rand
        min = 5
        max = 10
        integer = yes
    }

    # 数学表达式版（推荐，见 math-operators.md）
    set_variable = {
        MY_expr = {
            value = num_owned_states
            multiply = 2
            add = num_divisions
            clamp = { min = 0 max = 100 }
            round = yes
        }
    }

    print_variables = {                              # 仅调试用，会生成文件
        file = MY_vars
        text = "MY_variable_ops_demo"
        append = no
        print_global = yes
    }
}
```

## 5. 数组

数组不是"另一种类型"，而是**同一个变量槽位里塞了多个值**：第一次 `add_to_array` 就创建了它。

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_array_demo = {
    # ① 建数组：先清空，再追加
    clear_array = MY_candidates
    every_owned_state = {
        limit = { is_coastal = yes }
        add_to_array = { MY_candidates = id }        # 简写：{ 数组名 = 值 }
    }

    # ② 追加到临时数组（不存盘，适合中间结果）
    clear_temp_array = MY_tmp
    add_to_temp_array = { MY_tmp = num_divisions }

    # ③ 删除元素（用 value 或 index；都不给则删最后一个）
    remove_from_array = { MY_candidates = 42 }
    remove_from_array = { array = MY_candidates index = 0 }   # 删第一个（注意会前移）

    # ④ 长度控制
    resize_array = { array = MY_candidates size = 5 }         # 多余截断，不足补 0
    resize_array = { array = MY_candidates size = 5 value = -1 }  # 新增元素填 -1

    # ⑤ 下标访问：array^i（i 是变量名）或 array^2（字面量）
    set_temp_variable = { MY_first = MY_candidates^0 }
    set_temp_variable = { MY_idx = 1 }
    set_temp_variable = { MY_second = MY_candidates^MY_idx }

    # ⑥ 找最大/最小（结果放在临时变量 v / i 里）
    find_highest_in_array = { array = MY_scores }      # v = 最大值，i = 下标
    find_lowest_in_array = { array = MY_scores value = MY_min index = MY_min_i }

    # ⑦ 遍历（见 effects-triggers.md 第 5 节）
    for_each_loop = {
        array = MY_candidates
        log = "state [?v] at [?i]"
    }
}
```

| 操作 | effect / trigger | 文档行 |
|---|---|---|
| 加元素 | `add_to_array` / `add_to_temp_array` | effects 2278 / 2312 |
| 删元素 | `remove_from_array` / `remove_from_temp_array` | effects 6016 / 6050 |
| 扩缩容 | `resize_array` / `resize_temp_array` | effects 6397 / 6412 |
| 清空 | `clear_array` / `clear_temp_array` | effects 2713 / 2763 |
| 是否包含 | `is_in_array`（trigger，可简写 `{ 数组名 = 值 }`） | triggers 5672 |
| 求极值 | `find_highest_in_array` / `find_lowest_in_array` | effects 4251 / 4265 |
| 遍历 | `for_each_loop` / `for_each_scope_loop` / `all_of` / `any_of` / `all_of_scopes` / `any_of_scopes` | effects 4279+；triggers 1036+ |

原版数组实战参考：

- `common/scripted_effects/operation_strat_effects.txt:150-219`：两个平行数组 `operation_types` / `operation_types_scores`，用 `operation_types_scores^i` 按下标改分数，再 `find_highest_in_array` 选最优 → `set_variable = { generic_operation_type_to_run = operation_types^i }`。
- `events/LaR_espionage_operations.txt:181-209`：`clear_temp_array` → `for_each_loop` 里 `add_to_temp_array` 收集待删 id → 第二个 `for_each_loop` 里 `remove_from_array`，是"边遍历边删会崩"的正确写法（**先收集，再删**）。

## 6. 读取变量：`check_variable` 与 `has_variable`

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
MY_variable_checks = {
    # 完整形态
    check_variable = {
        var = MY_score
        value = 12            # 可以是数字、变量名
        compare = greater_than_or_equals
        # compare 可取：less_than / less_than_or_equals / greater_than /
        #              greater_than_or_equals / equals / not_equals
        tooltip = MY_score_tt  # loc 里可用 LEFT / RIGHT 占位
    }

    # 简写形态（等价）
    check_variable = { MY_score = 0 }
    check_variable = { MY_score > 12 }
    check_variable = { MY_score < 42 }
    check_variable = { MY_score > MY_other_score }

    # 存在性
    has_variable = MY_score
    has_variable = ROOT.MY_score
}
```

- 官方词条：`documentation/triggers_documentation.md:2110-2133`（`check_variable`）、`:5006`（`has_variable`，"Checks if a variable exists in a scope"）。
- 变量比较规则：浮点比较，支持小数（`check_variable = { x > 12.5 }`）。
- `tooltip` 参数让玩家看到可读文案（`LEFT`/`RIGHT` 被替换成实际值）。

## 7. 在 trigger 里做算术？可以，但有代价

官方 trigger 表里赫然列着 `set_temp_variable`、`add_to_temp_variable`、`multiply_temp_variable`、`clamp_temp_variable`、`set_temp_variable_to_random`、`add_to_temp_array`、`remove_from_temp_array`、`resize_temp_array`（`documentation/triggers_documentation.md:603-604,641-642,679-695`）。也就是说**在 trigger 块里可以做临时变量运算**，用来算一个复合条件：

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
MY_complex_condition = {
    hidden_trigger = {
        tooltip_evaluation = eval       # 必须：里面有副作用
        set_temp_variable = { MY_power = num_divisions }
        multiply_temp_variable = { MY_power = 3 }
        add_to_temp_variable = { MY_power = num_factories }
    }
    check_variable = { MY_power > 100 }
}
```

但请记住 [effects-triggers.md](effects-triggers.md) 第 2 节的结论：**trigger 会被 tooltip 反复求值**。所以：

- 有副作用的 trigger 一律包 `hidden_trigger = { tooltip_evaluation = eval ... }`（官方文档原文给出这个组合，见 `documentation/triggers_documentation.md:5126-5136`）。
- 更好的做法：把计算搬到 **effect** 里（例如每日 on_action 算一次存普通变量），trigger 只读结果。
- 临时变量在 trigger 里可以被 `check_variable` 直接读到（不需要 `var:` 前缀），原版实例：`common/scripted_effects/SOV_scripted_effects.txt:631` → `check_variable = { temp_targets_index = 5 compare = less_than }`。

## 8. 文件局部宏 `@` 与跨文件常量 `constant:`

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
@MY_SMALL_GAIN = 5          # 只能在本文件（含本文件所有 effect）里用
@MY_BIG_GAIN = 12

MY_macro_demo = {
    add_political_power = @MY_SMALL_GAIN
    army_experience = @MY_BIG_GAIN
}
```

- `@` 是**文件局部**宏：官方原话 "the script macro operator `@` that is file local"（`documentation/script_concept_documentation.md:218`）。原版实例：`common/scripted_effects/WTT_china_political_struggle_effects.txt:1-3` 定义 `@SMALL_STATE_SUPPORT_VALUE = 5`，同文件 21 行用 `set_variable = { global.small_state_support_value = @SMALL_STATE_SUPPORT_VALUE }`。
- 要跨文件复用数值，用 **script constants** + `constant:` 前缀（见 [math-operators.md](math-operators.md) 第 5 节）。

## 9. 完整可跑示例：一套"国家评分"变量

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 初始化（建议由 on_startup 调用一次，见 on-actions.md）
MY_init_score_system = {
    set_variable = { MY_score = 0 }
    set_variable = { global.MY_world_score_sum = 0 }
    clear_array = MY_scored_states
}

# 每次调用重算
MY_recalc_score = {
    # 用数学表达式一次算完（比 4 条 add_to_variable 更快更清晰）
    set_variable = {
        MY_score = {
            value = num_owned_states
            multiply = 2
            add = num_of_military_factories
            subtract = num_of_civilian_factories
            clamp = { min = 0 max = 200 }
        }
    }

    # 对每个州记录"州 id → 分数"，用数组存 id、变量存在州自己身上
    clear_array = MY_scored_states
    every_owned_state = {
        limit = { is_core_of = ROOT }
        add_to_array = { MY_scored_states = id }
        set_variable = { MY_state_score = industrial_complex_level }   # 存在当前州 scope 上（动态变量见 dynamic-variables.md:1130）
    }

    if = {
        limit = { check_variable = { MY_score > 100 } }
        add_stability = 0.02
    }
    else = {
        add_stability = -0.01
    }

    log = "MY score = [?MY_score] over [?num_owned_states] states"
}

# 读取某个州的分数（state scope 下调用）
MY_get_state_score = {
    set_temp_variable = { MY_tmp = var:MY_state_score }
    log = "state score = [?MY_tmp]"
}
```

> "按对象分槽"的 `name@TARGET` 写法见第 3 节；只给自己存值用普通变量就够了。

## 9.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Variables）

**变量的真实精度**：一个变量 = 有符号 32 位整数（±2147483647）+ 0~99999 的小数部分，即精度到 **0.00001**。超出范围会**整数回绕**（从最大值跳到最小值）——计数器要 clamp，别指望引擎报错。

**数学表达式没有优先级**：`set_variable = { x = { value = 0 add = 2 multiply = 3 } }` 的结果是 **6** 不是 2——函数按书写顺序依次执行。这是「算出来不对」类问题的头号来源。

**空变量与空值合并**：所有运算符都可作用于不存在的变量（按 0 处理）；`cost = var_name?100` 的 `?` 是空值合并——变量未设置时用 100 而非 0。

**flag 与变量的分工**：flag 也是 32 位整数但只能设/加/读，不能乘除、不能存 scope；做布尔开关 **flag 更省内存更快**，需要算术才用变量。

**临时变量不跨 scripted effect 边界延续**：在 scripted effects/triggers 内定义的 temp 变量可能无法在同一块外继续存在；但**调用前定义的** temp 变量会正常传入且可被修改。

**check_variable 简写是严格比较**：`check_variable = { var_name > 10 }` 在恰好 10 时为**假**；需要「≥」必须写全 `compare = greater_than_or_equals`（也是默认值）。

## 10. 常见错误 / 自检清单

**error.log 关键字**

- `[scopedvariable.cpp:571]: ai_num_of_military_factories is not a valid mtth database object`
  → 把一个**不存在**的 token 当变量读（本机 error.log 真实行，来自第三方 mod）。变量名拼错、或忘了先定义，就会撞这条。**变量名请统一加前缀**，能让这条报错一眼定位到你的文件。
- `[script_math.cpp:351]: Error: "" in file: "..." near line: N`
  → 变量赋值里的数学表达式写坏了（错误信息为空是引擎的锅）。常见原因：`{ value = x  add = }`（操作数缺失）、括号不配对。
- `[trigger.cpp:568]: Error: "Not a valid value: xxx, near line: N"`
  → `compare = xxx` 写错（合法值只有 6 个：`less_than`、`less_than_or_equals`、`greater_than`、`greater_than_or_equals`、`equals`、`not_equals`）。

**自检清单**

- [ ] 临时变量 vs 普通变量选对了吗？（要跨 tick 就必须普通变量）
- [ ] 变量名有 mod 前缀（`MY_`）吗？全局变量有 `global.` 吗？
- [ ] 数组"边遍历边删"了吗？必须**先收集到临时数组再删**（参照 `events/LaR_espionage_operations.txt:181-209`）。
- [ ] `@` 宏只在本文件有效——跨文件用了会变成"裸标识符"，报 `Unknown` / `not a valid ...`。
- [ ] 变量 target 的 `@` 后面跟的是**对象/scope 表达式**（`@ROOT`、`@PREV`、`@FROM`、`@var:x`、`@GER`），不是变量名。
- [ ] 读变量前先用 `has_variable` 判断（尤其是存档兼容、事件链中断的情况）。
- [ ] 想在 UI 里显示变量，记得本地化用 `[?变量名]` 语法（`[?num_equipment@convoy]` 见 `localisation/english/*.yml`；原版 `log` 里也这么用：`common/decisions/NOR.txt:45`）。
- [ ] 改完跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

---
title: 数学表达式、运算符、script_constants 与 script_enums
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/script_math_functions.md
  - documentation/script_concept_documentation.md
  - documentation/triggers_documentation.md
  - common/script_constants/documentation.md
  - common/script_constants/state_groups.txt
  - common/script_enums.txt
  - common/decisions/SIA.txt
---

# 数学表达式、运算符、script_constants 与 script_enums

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：1.19.x 的 PDX 脚本**没有中缀表达式**（不能写 `a + b * 2`），所有算术都写成"**基值 + 一串顺序语句**"的块；官方明确说这比用临时变量一步步加更快。

## 1. 语法：基值 + 顺序语句

官方定义（`documentation/script_concept_documentation.md:184-213`）：

> All math expressions are based on **fixed point arithmetic**. For boolean operations, 0.0 is considered false and any other value is considered true. All operators that return a boolean value will return **1.0 for true and 0.0 for false**.
> Math expressions use a base value (`value = ...`) that is then modified by sequential statements.

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 结构：{ value = <基值>  <语句1>  <语句2> ... }  —— 顺序执行，累加器一路被改
MY_math_demo = {
    set_variable = {
        MY_result = {
            value = num_divisions        # 基值
            multiply = 2                 # ×2
            add = num_owned_states       # + 州数
            subtract = 10                # -10
            clamp = { min = 0 max = 100 }# 夹到 [0,100]
            round = yes                  # 取整
        }
    }
}
```

三种语句形态：

| 形态 | 例子 | 说明 |
|---|---|---|
| 无参语句 | `round = yes`、`not = yes` | 直接对累加器施加操作 |
| 单参/结构化语句 | `add = 5`、`clamp = { min = 0 max = 100 }`、`lerp = { to = 20 alpha = 0.5 }` | 参数本身也可以是表达式/变量 |
| 控制流 | `if = { limit = { <表达式> } add = 100 }` + `else = { ... }` | `limit` 是**数学表达式**，非 0 视为真 |
| 集合迭代 | `every_collection = { named_collection = my_collection  add = element_value }` | 见 [collections.md](collections.md) |

**错误处理**：官方原文 "If a math expression fails to parse properly, it will be replaced with the value **0.0** for runtime operations."（`script_concept_documentation.md:203-204`）——也就是说**写错不会崩，会静默变成 0**，这是数学表达式最大的坑。

## 2. 30 个函数全表（`documentation/script_math_functions.md`）

| 函数 | 作用 | 示例 | 文档行 |
|---|---|---|---|
| `add` | 加 | `{ value = 5.0  add = num_factories }` | 54 |
| `subtract` | 减 | `{ value = 20  subtract = 5 }` | 299 |
| `multiply` | 乘 | `{ value = 2.3  multiply = num_units }` | 220 |
| `divide` | 除 | `{ value = 100  divide = 5 }` | 112 |
| `mod` | 取余 | `{ value = 17  mod = 5 }` | 211 |
| `pow` | 幂（整数指数精确） | `{ value = 2  pow = 10 }` | 256 |
| `root` | n 次根（近似值） | `{ value = 16  root = 2 }` | 268 |
| `log` | 以某数为底的对数（近似） | `{ value = 1000  log = 10 }` | 181 |
| `min` / `max` | 取小 / 取大 | `{ value = 9  max = 15 }` | 193 / 202 |
| `clamp` | 夹到区间（**参数有顺序要求**） | `{ value = num_units  clamp = { min = 0 max = 100 } }` | 94 |
| `round` | 四舍五入到整数 | `{ value = 3.7  round = yes }` | 281 |
| `lerp` | 线性插值（alpha 会被夹到 0..1） | `{ value = 10  lerp = { to = 20  alpha = 0.5 } }` | 163 |
| `sin` / `cos` / `tan` | 三角函数（弧度） | `{ value = 0  cos = yes }` | 290 / 103 / 308 |
| `atan` / `atan2` | 反正切（弧度，近似） | `{ value = 1  atan2 = 1 }` | 72 / 83 |
| `less_than` / `<` | 小于返回 1，否则 0 | `{ value = 2  less_than = 5 }` | 36 |
| `greater_than` / `>` | 大于返回 1，否则 0 | `{ value = 10  greater_than = 5 }` | 45 |
| `less_than_or_equals` | ≤ | `{ value = 5  less_than_or_equals = 5 }` | 172 |
| `greater_than_or_equals` | ≥ | `{ value = 5  greater_than_or_equals = 5 }` | 142 |
| `equals` / `not_equals` | = / ≠ | `{ value = 7  equals = 7 }` | 121 / 238 |
| `and` / `or` / `not` / `xor` | 布尔运算（非 0 为真） | `{ value = 0  or = 1 }` | 63 / 247 / 229 / 317 |
| `if` | 条件语句（可带 `else`） | 见下 | 151 |
| `every_collection` | 对命名集合迭代累加 | `{ value = 0  every_collection = { named_collection = my_collection  add = element_value } }` | 130 |

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# ① 布尔运算：算一个"是否达标"的 0/1 分数
MY_math_bool = {
    set_variable = {
        MY_is_strong = {
            value = 1
            and = { value = num_divisions  greater_than = 20 }   # 参数本身可以是表达式
        }
    }
}

# ② 条件语句（limit 是表达式，非 0 为真）
MY_math_if = {
    set_variable = {
        MY_tier = {
            value = 0
            if = {
                limit = { value = num_owned_states  greater_than = 30 }
                add = 2
            }
            else = {
                add = 1
            }
        }
    }
}

# ③ 顺序敏感：clamp 要放在所有运算之后
MY_math_order = {
    set_variable = {
        MY_pct = {
            value = num_divisions
            divide = 200              # 先除（0..1 区间化）
            multiply = 100            # 再转百分比
            clamp = { min = 0 max = 100 }
        }
    }
}
```

> 小数与近似：`root` / `log` / `pow`（分数指数）/ `atan` / `atan2` 都是数值近似，官方好几处都写了 "follow with `round = yes` if you need an exact result"（`script_math_functions.md:75,86,184,259,271`）。做"档位判断"（`>= 3` 这种）时**务必先 round**，否则会得到 `3.00001` 或 `2.99999` 的意外结果。

## 3. 数学表达式能写在哪

| 位置 | 写法 | 证据 |
|---|---|---|
| `set_variable` / `set_temp_variable` 的 value | `set_variable = { x = { value = a  multiply = 2 } }` | `documentation/effects_documentation.md:7836-7838,7904-7906` |
| `add_to_variable` / `add_to_temp_variable` | `add_to_variable = { x = { value = a  multiply = 2 } }` | 同文件 2337-2339 / 2353-2355 |
| `check_expr`（trigger） | `check_expr = { value = 2  add = 3  greater_than = 4 }` | `documentation/triggers_documentation.md:2094-2107` |
| `debug_math_expr`（trigger，调试） | `debug_math_expr = { value = 120  add = 15  clamp = { min = 0  max = 100 } }` | 同文件 2535-2550（**恒为真**，只把结果写进 tooltip） |
| `clamp_variable` 等专用 effect 的 `value` 参数 | `clamp_variable = { var = x min = 0 max = y }` | effects 2695 |

**为什么值得用**：官方原话 "Using math expressions is expected to be more performant than using temporary variables for calculations."（`script_concept_documentation.md:187-188`）。也就是说：

```pdx
# ❌ 旧写法：4 条 effect，4 次变量表查找
set_temp_variable = { t = num_divisions }
multiply_temp_variable = { t = 2 }
add_to_temp_variable = { t = 5 }
clamp_temp_variable = { var = t min = 0 max = 100 }    # 注意参数是扁平 var/min/max（effects 2681）

# ✅ 新写法：1 条 effect，一次完成
set_temp_variable = {
    t = {
        value = num_divisions
        multiply = 2
        add = 5
        clamp = { min = 0 max = 100 }
    }
}
```

## 4. 运算符两套写法：表达式内 vs trigger 内

| 场景 | 写法 |
|---|---|
| 数学表达式内部 | `less_than` / `greater_than` / `less_than_or_equals` / `greater_than_or_equals` / `equals` / `not_equals`（也可用 `<` `>`） |
| trigger 的参数式比较 | `has_army_size = { size > 20 }`、`command_power > 1.5`、`has_war_support < 0.6`（trigger 名 + 中缀比较符） |
| 变量比较 | `check_variable = { x > 12 }` 或 `check_variable = { var = x compare = greater_than value = 12 }` |
| 集合大小比较 | `collection_size = { ... value > 42 }` —— **⚠️ 这里的 `>` 实际是 `>=`**（见第 7 节） |

## 5. `script_constants`：跨文件常量

### 5.1 定义（`common/script_constants/`）

结构见 `common/script_constants/documentation.md`：

```pdx
# 放置路径：common/script_constants/MY_constants.txt
# schema 必须是第一个条目
MY_gains = {
    schema = {
        any_key = yes          # 允许任意字母 key；或用 key = 具体名字
        data = fixed_point     # int / fixed_point / 复杂 schema 块
    }
    small = 1.5
    medium = 3
    large = 6
}

# 复杂 schema（每个条目是一组具名字段）——原版 sp_complexity 就是这么写的
MY_complexity = {
    schema = {
        any_key = yes
        data = {
            { key = min  data = int }
            { key = max  data = int }
        }
    }
    low  = { min = 20 max = 30 }
    high = { min = 5  max = 10 }
}
```

### 5.2 使用

```pdx
# 放置路径：common/decisions/MY_decisions.txt
MY_constant_decision = {
    icon = generic_political_actions
    cost = 50
    days_remove = constant:MY_gains.medium          # 30 天
    available = { always = yes }
    visible = { always = yes }
    complete_effect = {
        add_political_power = constant:MY_gains.large
        set_variable = { MY_threshold = constant:MY_complexity.high.max }
        army_experience = constant:MY_gains.small
    }
}
```

- 前缀固定为 **`constant:`**，"所有 scoped variables 都接受指向单个定点值的脚本常量"（`script_concept_documentation.md:220-221`）。
- 原版大量真实用法：`constant:sp_progress.gain.low`（`common/special_projects/projects/land_projects.txt:465`）、`constant:propaganda.SIA.default_propaganda_campaign_duration`（`common/decisions/SIA.txt:406`）、`constant:country_groups.nordics`（`common/scripted_triggers/NORDIC_scripted_triggers.txt:227`）。
- ⚠️ 文档示例里出现过 `constant:country_groups:nordics`（冒号）的写法（`documentation/triggers_documentation.md:1372`），但**实际游戏文件一律用点号** `constant:country_groups.nordics`。**以点号为准**。
- **重载规则**（官方专门说明）：改常量后不能只 reload 常量库——"one have to first reload the script constant database, and then reload the database that uses the script constant"（`script_concept_documentation.md:223-226`）。实践中直接重启游戏最省事。
- `@` 宏 vs `constant:`：`@` 是**文件局部**（见 [variables.md](variables.md) 第 8 节），`constant:` 是全局跨文件。官方原话："In general, script constants can be used instead of the script macro operator `@` that is file local."（`script_concept_documentation.md:218`）。

## 6. `script_enums`：合法取值清单

`common/script_enums.txt` 定义了 6 个枚举，用来约束/查证某些参数的合法取值：

| enum | 内容 | 行 |
|---|---|---|
| `script_enum_operative_mission_type` | 情报行动任务类型（`build_intel_network` 等 5 种） | 1 |
| `script_enum_advisor_slot_type` | 顾问槽类型（`theorist`、`high_command`、`army_chief`…） | 9 |
| `script_enum_equipment_stat` | 可被 MIO/装备修改的属性（`defense`、`soft_attack`…，带大量 `#Cannot be used with MIOS` 注释） | 18 |
| `script_enum_production_stat` | 生产相关可改项（`production_cost_factor` 等） | 101 |
| `script_enum_equipment_category` | 装备大类（`convoy`、`armor`、`infantry`…） | 111 |
| `script_enum_equipment_bonus_type` | `equipment_bonus` / MIO 里能用的装备类型集合 | 152 |

用法：它**不是**让你在脚本里"引用枚举值"的机制，而是**查合法 token 的权威清单**。例如：

- `equipment_bonus` 块里的 key（`armor_value`、`reliability`、`build_cost_ic`…）合法集合 = `script_enum_equipment_stat`（`common/script_enums.txt:18-99`；注意文件里大量 `#Cannot be used with MIOS` 注释，标了这些属性不能用于 MIO）。
- `has_mio_equipment_type` 的官方说明直接写 "possible values can be found in `script_enum_equipment_bonus_type` and in `common/equipment_groups`"（`documentation/triggers_documentation.md:4266-4272`）。

```pdx
# 放置路径：common/military_industrial_organization/organizations/MY_mio.txt（节选；MIO 完整结构见 ../02_content/mio.md）
# 原版同款：common/military_industrial_organization/organizations/00_generic_organization.txt:130-147
MY_mio_trait_sample = {
    equipment_bonus = {
        # key 的合法集合 = script_enum_equipment_stat
        armor_value = 0.05
        reliability = 0.05
        build_cost_ic = -0.05
    }
}
```

> ⚠️ 待验证：mod 能否在 `common/script_enums.txt` 里**新增**自己的 `script_enum_xxx` 并被引擎采纳，本机未做实验。稳妥做法是把自定义取值表写成 `common/script_constants/*` 里的常量（本知识库推荐后者）。

## 7. 坑：`collection_size` 的比较是"含等号"的

官方在 `collection_size` 词条里专门用大写 NOTE 警告（`documentation/triggers_documentation.md:2190-2202`）：

> NOTE! Comparison is **inclusive**, so "value > X" actually means "value **>=** X" etc.!!!

也就是说 `collection_size = { input = game:all_states  value > 42 }` 在"恰好 42 个州"时为 **true**。写边界条件时必须记住这一点，或者先把阈值 ±1 手工挪一位。

## 8. 常见错误 / 自检清单

**error.log 关键字**

- `[script_math.cpp:351]: Error: "" in file: "..." near line: N`
  → 数学表达式解析失败。**错误信息是空的**（引擎 bug），所以只能靠"这行附近哪个表达式写残了"来定位。常见：`add =` 后面没值、`clamp = { min = 0 }` 缺 max、括号不配对、用了 `+ - * /` 中缀。
- 上述失败在运行时被替换为 **0.0**（`script_concept_documentation.md:203-204`），所以**不会崩，只会结果全错**——症状通常是"数值一直是 0 / 阈值判断永远不成立"。
- `[scopedvariable.cpp:571]: xxx is not a valid mtth database object` → 表达式里引用了不存在的名字（变量名拼错，或想用动态变量却写错）。
- `[effect.cpp:358]: Error: "Unknown effect-type: clamp_temp_variable, ..."` → 这个 effect 只在 `Supported Scopes: any` 的地方能用；如果出现在 trigger 里应改用 trigger 版（`documentation/triggers_documentation.md:2145`），或干脆改用 `clamp = {...}` 表达式（推荐）。

**自检清单**

- [ ] 表达式里没有中缀运算符（`+ - * /`）——全部改成 `add`/`subtract`/`multiply`/`divide`。
- [ ] `clamp` 放在运算链**最后**（先算再夹）。
- [ ] 需要整数判断的地方补了 `round = yes`（尤其涉及 `root`/`log`/`pow` 分数指数）。
- [ ] 布尔语义确认过：**非 0 即真**，比较函数返回 1.0/0.0；`and`/`or`/`not`/`xor` 都是按"非 0"处理。
- [ ] 用 `constant:` 时拼写是**点号**（`constant:库.key`），并且常量文件确实在 `common/script_constants/` 下。
- [ ] modifier / 装备 type 之类的 token 都在 `script_enums.txt` 或 `common/equipment_groups/` 里查过，没有凭记忆写。
- [ ] 用 `collection_size` 做边界判断时，记得 `>` 实际是 `>=`。
- [ ] 调试数值：临时插一条 `debug_math_expr = { ... }`（恒真，会把结果写进 tooltip）或 `log = "..."`。
- [ ] 跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

---
title: Script Collections（脚本集合）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/script_collection_input.md
  - documentation/script_collection_operator.md
  - documentation/script_concept_documentation.md
  - common/collections/_documentation.md
  - common/collections/collections.txt
  - common/factions/goals/faction_goals_short_term.txt
---

# Script Collections（脚本集合）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：collection = **"一组同类游戏对象"+ 一串可以链式施加的过滤/变换操作**。它把"遍历 + 计数 + 比较"这种原本要写 `any_` + 临时变量的活，压成一条 trigger 或一条 effect。

## 1. 为什么要有它

官方给的理由（`documentation/script_concept_documentation.md:60-70`，原文意译）：

> 想判断"阵营成员拥有的州超过 42 个"，用数组 + trigger 也能做，但需要：对所有阵营成员做隐式循环（`all of`）、把每个成员的州数累加进临时变量、再比较——而且为了让玩家看懂，往往还得手写 custom tooltip。用 collection 一条就够：
> ```
> collection_size = {
> 	input = { input = game:scope  operators = { faction_members owned_states }  name = "States owned by any faction member" }
> 	value > 42
> }
> ```

官方明确说 collection "is expected to be **more efficient** and **easier to script**"。

## 2. 结构：`input` + `operators` + `name`

| 字段 | 必填 | 作用 |
|---|---|---|
| `input` | ✅ | 起始集合：内置集合（`game:*`、`country:*`）、命名集合（`collection:name`）、常量（`constant:name`） |
| `operators` | 可选 | 依次施加到每个元素上的操作（`owned_states`、`faction_members`、`limit = { }` 过滤…） |
| `name` | 可选 | 集合名，用于 **本地化**（`name` 填的是 loc key） |

构建方式（`script_concept_documentation.md:91-97`）：从 `input` 的所有元素出发，**按顺序**对每个元素施加 `operators` 里的每个操作，得到最终集合。

### 2.1 简写

只有 input 时可以省略外壳（`script_concept_documentation.md:99-108`）：

```pdx
# 这两种写法等价
my_collection = { input = game:all_states }
my_collection = game:all_states
```

### 2.2 匿名集合

在任何"期望一个集合"的位置直接写 `{ input = ... operators = ... }`，就是匿名集合（`common/collections/_documentation.md:46-60`）。

## 3. `input` 全表（`documentation/script_collection_input.md`）

| input | 含义 | 文档行 |
|---|---|---|
| `game:all_countries` | 所有**存在**的国家（含流亡政府） | 36 |
| `game:all_possible_countries` | 所有国家（含尚未存在的） | 49 |
| `game:all_states` | 所有存在的州 | 63 |
| `game:scope` | 当前 scope 对象本身 | 76 |
| `game:empty` | 空集合 | `common/collections/_documentation.md:71` |
| `collection:NAME` | 引用命名集合 | 12 |
| `constant:NAME` | 用 script constant 作为集合来源 | 25 |
| `country:faction_members` | 当前国家的阵营成员（无阵营则为空） | `common/collections/_documentation.md:80` |

## 4. `operators` 全表（`documentation/script_collection_operator.md`）

| operator | 作用 | 文档行 |
|---|---|---|
| `owned_states` | 该国的**拥有**州 | 71 |
| `controlled_states` | 该国的**控制**州 | 11 |
| `faction_members` | 该国所在阵营的所有成员（含自己） | 42 |
| `country_and_all_subjects` | 该国及其所有附庸 | 26 |
| `limit = { <trigger> }` | 过滤（保留满足 trigger 的元素） | 58 |

> ⚠️ 文档 bug：`script_collection_operator.md` 的 `limit` 词条标题写的是 `limit = PAYLOAD`，但**示例里写成了 `trigger = { has_government = democratic }`**。**以 `limit` 为准**——原版 `common/collections/collections.txt:13-17` 全部写 `operators = { limit = { ... } }`。
>
> 另外官方 `common/collections/_documentation.md:24-36` 展示的是**顶层 `limit`**（不在 `operators` 里）的写法，也有效；但为了与 `operators` 的顺序语义一致，**推荐把 `limit` 放进 `operators`**（它就是一个"过滤操作"，位置很重要）。

`limit` 里的 scope 语义（`common/collections/_documentation.md:30-35`）：

- `SCOPE` = 输入集合里的**元素**
- `PREV` = 使用该集合的那段脚本所处的 scope
- `ROOT` = `PREV.ROOT`，`FROM` = `PREV.FROM`
- 官方注释："the scope structure above mimics the scope structure of other `every_xxx` effects"

## 5. 在哪里消费集合（5 个 trigger / 2 个 effect）

| 消费方 | 类型 | 参数形状 | 用途 |
|---|---|---|---|
| `collection_size` | trigger | `input = <集合> value > N` | 比较集合大小（**含等号陷阱**，见第 7 节） |
| `collection_contains` | trigger | `collection = <集合> country = TAG` 或 `countries = { A B }` | 集合是否包含指定国家 |
| `count_in_collection` | trigger | `collection = <集合>` + `unit`/`buildings`/`manpower`/`stockpile` + `size > N` | 数**装备/建筑/人力**（比元素个数更强） |
| `any_collection_element` | trigger | `collection = <集合>` + 元素级 trigger + 可选 `count = N` | 存在满足者（可要求 ≥N 个） |
| `all_collection_elements` | trigger | `collection = <集合>` + 元素级 trigger | 全部满足 |
| `every_collection_element` | effect | **`input = <集合>`** + 元素级 effect | 对每个元素执行 effect |
| `has_resources_in_collection` | trigger | `collection = <集合>` + `resource = steel` + `amount > N` + `extracted = yes` | 集合内资源总量 |

> 注意参数名不统一：两个 trigger 系列用 `collection =`，而 `every_collection_element` 用 **`input =`**（`documentation/effects_documentation.md:3763-3797`，原版 `common/factions/goals/faction_goals_short_term.txt:141-157` 也是 `input =`）。

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
# ① 集合大小
MY_faction_state_check = {
    collection_size = {
        input = {
            input = game:scope
            operators = { faction_members owned_states }
            name = MY_faction_states_tt        # 本地化 key（可省略）
        }
        value > 42
    }
}

# ② 元素级 trigger（PREV 是外层 scope）
MY_some_controlled_core = {
    any_collection_element = {
        collection = {
            input = game:scope
            operators = { controlled_states }
        }
        is_core_of = PREV                      # 官方示例同款：documentation/triggers_documentation.md:1300-1306
    }
}

# ③ 要求至少 3 个满足（count 参数）
MY_three_controlled_cores = {
    any_collection_element = {
        collection = { input = game:scope operators = { controlled_states } }
        is_core_of = PREV
        count = 3
    }
}

# ④ 全部满足
MY_all_controlled_are_cores = {
    all_collection_elements = {
        collection = { input = game:scope operators = { controlled_states } }
        is_core_of = PREV
    }
}

# ⑤ 是否包含指定国家
MY_faction_contains_germany = {
    collection_contains = {
        collection = { input = game:scope operators = { faction_members } }
        country = GER
    }
}
```

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# ⑥ 对每个元素执行 effect（注意参数名是 input）
MY_buff_faction_members = {
    every_collection_element = {
        input = {
            input = game:scope
            operators = {
                faction_members
                limit = { has_government = democratic }
            }
            name = MY_democratic_members_tt
        }
        add_stability = 0.01
        add_war_support = 0.01
    }
}
# 原版同款：common/factions/goals/faction_goals_short_term.txt:135-158
#   every_collection_element = { input = { input = game:scope operators = { faction_members limit = {...} } name = GUERILLA_ABOVE_THRESHOLD } ... }
```

## 6. 命名集合（`common/collections/*.txt`）

定义格式（`common/collections/_documentation.md:14-44` + 实际文件）：

```pdx
# 放置路径：common/collections/MY_collections.txt
# 引用时用 collection:MY_democratic_faction_members
MY_democratic_faction_members = {
    input = game:scope                   # 注意：这里的 scope 是"使用该集合时"的 scope
    operators = {
        faction_members
        limit = { has_government = democratic }
    }
    name = MY_COLLECTION_DEMOCRATIC_FACTION_MEMBERS     # 本地化 key
}

MY_uncapitulated_democratic_members = {
    input = collection:MY_democratic_faction_members    # 命名集合可以作为别的集合的 input
    operators = {
        limit = { has_capitulated = no }
    }
    name = MY_COLLECTION_UNCAP_DEMOCRATIC_MEMBERS
}

MY_world_at_peace = {
    input = game:all_countries          # 不需要 country scope 的集合
    operators = {
        limit = { has_war = no }
    }
    name = MY_COLLECTION_COUNTRIES_AT_PEACE
}
```

原版真实用例（强烈建议对照阅读）：`common/collections/collections.txt` —— 11-19 行 `world_at_peace_countries`（`input = game:all_countries` + `limit = { has_war = no }`）、21-30 行 `democratic_faction_members`（`input = game:scope` + `faction_members` + `limit`）、32-42 行 `uncapitulated_democratic_faction_members`、70-78 行 `world_uncapitulated_democratic_countries`（用 `input = collection:world_democratic_countries` 链式复用）。

本地化只需要给 `name` 对应的 key 写文案（en + zh 各一套）：

```yml
# 放置路径：localisation/simp_chinese/MY_l_simp_chinese.yml（UTF-8 with BOM）
l_simp_chinese:
 MY_COLLECTION_DEMOCRATIC_FACTION_MEMBERS:0 "民主阵营成员"
 MY_COLLECTION_COUNTRIES_AT_PEACE:0 "处于和平的国家"
```

> 官方说明：集合的显示名用 `name` 属性；若没有 `name` 则回退到 input 集合的名字（`script_concept_documentation.md:120-122`）。

## 7. 三个必须记住的坑

### 7.1 `collection_size` 的比较是**含等号**的

`documentation/triggers_documentation.md:2192` 原文（大写 NOTE）：

> "Comparison is **inclusive**, so `value > X` actually means `value >= X` etc.!!!"

所以"州数 > 42"在恰好 42 个州时为真。写边界条件时请显式换算。

### 7.2 集合**不保证元素唯一**

官方（`script_concept_documentation.md:110-114`）：如果多个阵营成员都 core 同一个州，`core_states` 会让这个州在集合里出现多次。`collection_size` 数的是**出现次数**，不是唯一对象数。需要去重就先换成不会重复的 operator，或改用 `count_in_collection`/`any_collection_element` 这种按元素判断的消费方式。

### 7.3 `input = game:scope` 依赖调用点的 scope

命名集合里写 `input = game:scope`，表示"使用时的当前 scope"。所以在 STATE scope 里误用 `country:faction_members` 这类需要国家 scope 的 input 会出问题（官方 `every_collection_element` 的 "Scoped example" 专门演示了要先 `TAG = { ... }` 包一层，`documentation/effects_documentation.md:3784-3797`）。

## 8. 完整可跑示例：一个"阵营工业评估"决议

```pdx
# ===== 文件 1：common/collections/MY_collections.txt =====
MY_faction_industrial_states = {
    input = game:scope
    operators = {
        faction_members
        owned_states
        limit = {
            industrial_complex > 5
        }
    }
    name = MY_COLLECTION_FACTION_INDUSTRIAL_STATES
}

# ===== 文件 2：common/scripted_triggers/MY_scripted_triggers.txt =====
MY_faction_is_industrialized = {
    collection_size = {
        input = collection:MY_faction_industrial_states
        value > 9                        # ⚠️ 实际含义是 >= 9
    }
    any_collection_element = {
        collection = collection:MY_faction_industrial_states
        is_owned_by = PREV
        count = 2
    }
}

# ===== 文件 3：common/decisions/MY_decisions.txt =====
MY_economy_category = {
    icon = generic_industrial
    MY_industrial_survey = {
        icon = GFX_decision_generic_industrial
        available = { MY_faction_is_industrialized = yes }
        visible = { always = yes }
        cost = 25
        complete_effect = {
            every_collection_element = {
                input = collection:MY_faction_industrial_states
                add_extra_state_shared_building_slots = 1
            }
            custom_effect_tooltip = MY_industrial_survey_tt
        }
        ai_will_do = { base = 5 }
    }
}
```

## 9. 常见错误 / 自检清单

**error.log 关键字**

- `[trigger.cpp:568]: Error: "Unknown trigger-type: collection_size, ..."`
  → `collection_size` 是 trigger，不能写在 effect 块里（纯 effect 语境里要用 `every_collection_element`）。
- `[scopedvariable.cpp:571]: xxx is not a valid mtth database object`
  → 集合里引用了**不存在的命名集合**（忘了 `collection:` 前缀时最常撞这条，例如写成 `input = MY_collection` 而不是 `input = collection:MY_collection`）。
- 集合 `name` 没有本地化 → `No localisation for MY_COLLECTION_xxx`（和普通 loc key 一样）。
- 需要国家 scope 的 input 用在了错误 scope → 类似 `Invalid Scope, supported: Country, provided: None`；修法：外层包 `TAG = { ... }`。
- ⚠️ 已知文档 bug：`script_collection_operator.md` 里 `limit` 的示例写成 `trigger = {...}`；如果你照抄后发现过滤无效，改回 `limit = { ... }`。

**自检清单**

- [ ] `input` 用的是 `game:` / `collection:` / `constant:` / `country:` 前缀，没有裸名。
- [ ] `operators` 的顺序是有意的（`faction_members` 必须在 `owned_states` 前面才能"数阵营的州"）。
- [ ] `collection_size` 的阈值按"含等号"重新核对过。
- [ ] 需要唯一元素时，没有误用 `core_states` 之类可能重复的 operator。
- [ ] `name` 有对应的 en + zh 本地化。
- [ ] 用 `every_collection_element` 时参数写的是 `input =`，不是 `collection =`。
- [ ] 用 `any_collection_element` 的 `count =` 时确认语义是"**至少 N 个**满足"（官方原文 "equal or larger than `count`"，`documentation/triggers_documentation.md:1296`）。
- [ ] 跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

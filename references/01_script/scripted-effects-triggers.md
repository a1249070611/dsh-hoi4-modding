---
title: scripted_effects / scripted_triggers / scripted_localisation 复用
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - common/scripted_effects/00_scripted_effects.txt
  - common/scripted_triggers/00_scripted_triggers.txt
  - common/scripted_localisation/00_scripted_localisation.txt
  - common/scripted_guis/_documentation.md
  - documentation/triggers_documentation.md
  - documentation/effects_documentation.md
---

# scripted_effects / scripted_triggers / scripted_localisation 复用

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：三种"自定义名字"的复用件——**effect 函数、trigger 谓词、本地化文本函数**。它们都**没有参数**（1.19.3 实测），要"传参"只能靠约定变量。

## 1. 三个目录、三种语法

| 目录 | 定义方式 | 调用方式 | 官方模板注释 |
|---|---|---|---|
| `common/scripted_effects/*.txt` | `my_effect = { <effects> }` | `my_effect = yes` | `common/scripted_effects/00_scripted_effects.txt:1-16` |
| `common/scripted_triggers/*.txt` | `my_trigger = { <triggers> }` | `my_trigger = yes` | `common/scripted_triggers/00_scripted_triggers.txt:1-13` |
| `common/scripted_localisation/*.txt` | `defined_text = { name = GetXxx text = { ... } }` | 本地化里写 `[GetXxx]` | `common/scripted_localisation/00_scripted_localisation.txt:1-9` |

命名建议：effect `MY_`，trigger `MY_`，defined_text **必须以 `Get` 开头**（原版全部如此：`GetKdfWagenName`、`GetWehrmachtAngerLevel`、`GetSenateElectionOutcome`，`00_scripted_localisation.txt:13,129,238`）。

## 2. 最重要的事实：**没有 `$参数$`**

本机 `common/scripted_effects/` 全部文件里 **grep 不到任何 `$...$` 形式的参数占位符**；官方模板也只写了 `example_effect = yes` 这种无参调用（`00_scripted_effects.txt:15`）。所以网上"DLC 风格脚本参数"那套（EU4/CK3 的 `$PARAM$`）在 HOI4 里不存在。

1.19.x 可用的"参数化"手段（按推荐顺序）：

| 手段 | 传递什么 | 写法 | 优点 / 缺点 |
|---|---|---|---|
| **临时变量约定** | 数值/字符串 | 调用方 `set_temp_variable = { MY_arg = 42 }`，被调方读 `var:MY_arg` | 零成本；缺点：靠文档约定，漏设就是 0 |
| **普通/全局变量** | 需持久的值 | `set_variable = { MY_arg = 42 }` / `global.MY_arg` | 可跨 tick；缺点：污染存档 |
| **`event_target:`** | **scope（对象）** | 调用方 `save_event_target_as = MY_target`，被调方 `event_target:MY_target = { ... }` | 传对象最干净；缺点：要紧记清理 |
| **`constant:`** | 常量（编译期注入） | `common/script_constants/*` + `my_effect = { add_political_power = constant:my_ns.gain }` | 零运行时开销；缺点：不能变 |
| **`@` 宏 / `meta_effect`** | 文件内常量 / **动态名** | `@V = 5`；`meta_effect = { text = { add_ideas = X_[T]_idea } T = "[?MY_tier]" }` | `@` 只在本文件有效；`meta_effect` 开销大 |
| **`args^N`** | 控制台/外部调用入参 | `value = args^0?0.1`（`?` 为缺省值） | **双源实证**：原版 `common/scripted_effects/zz_debug_effects.txt`；East Showdown `ES_custom_console_commands.txt:6-8`（`d_add_ammunition = { add_to_variable = { FROM.ammunition_value_k = args^0 } }`）。**`d_` 前缀的 scripted effect 会自动暴露为同名控制台命令**（官方 debug 效果全用 `d_` 前缀即为此；ES 把自己的作弊命令写成 `console_commands.md` 交给测试员）。未进官方 wiki 的效果文档 |
| **`token:` 字面量进变量** | 名字引用（effect/事件/GFX 键） | `set_variable = { X = token:SE_YYY }`，比较 `check_variable = { X = token:SE_YYY }`，loc/GUI 侧 `[?X.GetTokenKey]` 动态拼名 | TNO super event 的核心（见下 2.1） |

### 2.1 工坊实战补充（TNO 实测，2026-11-07）

1. **`token:` + `GetTokenKey` 组合拳**：调用方
   `set_temp_variable = { TNO_temp_super_event = token:SE_XXX }`（decisions/
   TNO_BRA_decisions.txt:787-789），核心 effect 复制进持久变量
   `set_variable = { TNO_super_event = TNO_temp_super_event }`；
   展示侧一个 scripted_localisation 函数用
   `localization_key = "GFX_[?TNO_super_event.GetTokenKey]"` 动态拼出
   92 张事件图、音乐名同理（`scoped_play_song = "TNO_[SUPER]"`）。
   **一份展示框架吃下全部剧情演出**——比 per-事件复制 GUI 少两个数量级的维护量。
2. **meta_effect 泛型 idea**：`add_ideas = [currenttag]_Generic_Vacant_hog`
   用 `[THIS.GetTag]` 填 tag（TNO_useful_scripted_effects.txt:30-36）——
   全部国家的「空缺部长」idea 零复制。
3. **effect 库分三层**（TNO 实测组织法）：`TNO_useful_scripted_effects.txt`
   （通用工具）→ per-country 文件 → `TNO_arithmetic_functions_scripted_effects.txt`
   （9823 行纯数学库：while_loop 实现取模/开方/三角函数）。
   自己的 mod 至少把「通用工具 / 国家专属」分开。
4. ⚠️ **重复定义即覆盖**：TNO 实测 13 个 scripted_effect 被同名重复定义
   （state_control_effect_539 等），后定义静默吃掉前定义——复用库变大后
   用 `grep -c "^名字 = {"` 之类自检，本插件 `kb_symbol` 也能查多定义。

## 3. `scripted_effects`

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 定义：无参 effect（官方模板：common/scripted_effects/00_scripted_effects.txt:1-16）
MY_give_starting_bonus = {
    add_political_power = 25
    add_stability = 0.02
    army_experience = 10
    custom_effect_tooltip = MY_starting_bonus_tt      # 显示用文案（不产生效果）
}

# "带参"的正确姿势：调用方先把参数放进临时变量 / 事件目标
MY_give_bonus_to_target = {
    # 约定：调用前请先 event_target:MY_bonus_target 与 set_temp_variable = { MY_bonus_amount = N }
    event_target:MY_bonus_target = {
        add_political_power = var:MY_bonus_amount
        custom_effect_tooltip = MY_bonus_given_tt
    }
}

# 调用示例（放在同一文件仅作演示；实际调用点在国策/事件/决议里）
MY_demo_call = {
    SWE = { save_event_target_as = MY_bonus_target }
    set_temp_variable = { MY_bonus_amount = 50 }
    MY_give_bonus_to_target = yes
    MY_give_starting_bonus = yes
}
```

使用要点：

- **调用就是 `名字 = yes`**，写 `名字 = { }` 会报 `Unknown effect-type`。
- effect 内部 scope 沿用调用点；`ROOT`/`FROM` 也沿用调用点的（不会因为进了 scripted_effect 而重置）。这点和"函数"直觉不同，务必记住。
- 需要 tooltip 时，在定义里写 `custom_effect_tooltip` / `hidden_effect`（见 [effects-triggers.md](effects-triggers.md) 第 8 节），调用点没有参数可传。
- 想"临时改 scope"就在调用点包块：`GER = { MY_effect = yes }`。

## 4. `scripted_triggers`

```pdx
# 放置路径：common/scripted_triggers/MY_scripted_triggers.txt
# 定义（官方模板：common/scripted_triggers/00_scripted_triggers.txt:1-13）
MY_can_start_program = {
    is_subject = no
    has_war = no
    check_variable = { MY_program_budget > 100 }
    NOT = { has_country_flag = MY_program_running }
}

# 想给玩家看得懂的解释，就在定义里包 custom_override_tooltip
MY_has_enough_industry = {
    custom_override_tooltip = {
        tooltip = MY_has_enough_industry_tt
        # not_tooltip 不写时自动用 MY_has_enough_industry_tt_NOT
        any_owned_state = {
            limit = { is_core_of = ROOT }
            industrial_complex > 5
        }
    }
}
```

调用：

```pdx
# 放置路径：common/decisions/MY_decisions.txt
MY_program_decision = {
    icon = GFX_decision_generic_industrial
    available = {
        MY_can_start_program = yes        # ← 直接当 trigger 用
        MY_has_enough_industry = yes
    }
    visible = { always = yes }
    complete_effect = { MY_demo_call = yes }
}
```

要点：

- trigger 定义里出现 effect（如 `set_temp_variable`）是**允许**的（官方 trigger 表里就有这些），但会被 tooltip 重复求值 → 必须 `hidden_trigger = { tooltip_evaluation = eval ... }`。
- 定义里的 `ROOT`/`FROM`/`PREV` 取调用点的值，不是定义处的"全局"。这是 scripted trigger 最常见的坑：在事件里调用和在国策里调用，`ROOT` 可能不是同一个国家。
- 自定义提示：`custom_override_tooltip`（`documentation/triggers_documentation.md:2431`，官方推荐）；`custom_trigger_tooltip` 是**向后兼容别名**（`:2482`，官方原文 "Prefer `custom_override_tooltip` instead"）。

## 5. `scripted_localisation`（动态文本）

用途：同一 loc key 根据条件显示不同文本（性别代词、党派名、等级描述…）。结构见 `00_scripted_localisation.txt:1-9` 的头注释：

```pdx
# 放置路径：common/scripted_localisation/MY_scripted_loc.txt
defined_text = {
    name = GetMY_threat_level_name

    text = {
        trigger = {
            check_variable = { MY_threat = 0 }
        }
        localization_key = MY_threat_none          # 对应 loc 里的 key
    }
    text = {
        trigger = {
            check_variable = { MY_threat = 1 }
            check_variable = { MY_threat = 20 compare = less_than }
        }
        localization_key = MY_threat_low
    }
    text = {
        # 无 trigger 的 text 是"兜底"，必须放在最后
        localization_key = MY_threat_high
    }
}
```

本地化里这样用（原版写法：`localisation/english/focus_l_english.yml:297` 的 `"[Root.GetKdfWagenName]"`、`wuw_ideas_l_english.yml:316` 的 `"[GetReichsWerkeName]"`）：

```yml
# 放置路径：localisation/simp_chinese/MY_l_simp_chinese.yml（UTF-8 with BOM）
l_simp_chinese:
 MY_threat_status:0 "当前威胁等级：[Root.GetMY_threat_level_name]"
```

> 官方对 `defined_text` 的注释原文：`# text -> a discrete entry that can be picked to display in loc.` / `# trigger -> determines if a text entry will be picked or not.` / `# (The triggers need to be valid for the scope the key is called in`（`00_scripted_localisation.txt:1-9`）。

配合变量插值（`[?变量名]`）可以直接显示数值：`"[?MY_threat]"`、`"[?num_equipment@convoy]"`（`localisation/english/*.yml` 里大量使用；`common/decisions/NOR.txt:45` 的 `log` 也用了这个语法）。本地化完整规范见 [../05_presentation/localisation.md](../05_presentation/localisation.md)。

## 6. 一个完整的"复用件"实战：三件套协作

```pdx
# ===== 文件 1：common/scripted_triggers/MY_scripted_triggers.txt =====
MY_ready_for_reform = {
    custom_override_tooltip = {
        tooltip = MY_ready_for_reform_tt
        is_subject = no
        has_war = no
        check_variable = { MY_reform_progress > 50 }
        NOT = { has_country_flag = MY_reform_done }
    }
}

# ===== 文件 2：common/scripted_effects/MY_scripted_effects.txt =====
MY_apply_reform = {
    # 参数约定：调用方已设置 global.MY_reform_gain（默认 0.05）
    set_variable = { MY_reform_progress = 0 }
    add_stability = var:global.MY_reform_gain
    add_war_support = 0.02
    set_country_flag = MY_reform_done
    custom_effect_tooltip = MY_reform_tt
}

# ===== 文件 3：common/decisions/MY_decisions.txt（调用方）=====
MY_reform_category = {
    icon = generic_political_actions
    MY_reform_decision = {
        icon = GFX_decision_generic_political
        available = { MY_ready_for_reform = yes }
        visible = { always = yes }
        cost = 100
        complete_effect = { MY_apply_reform = yes }
        ai_will_do = { base = 10 }
    }
}
```

## 7. 和 scripted_gui 的关系

`common/scripted_guis/*.txt` 是"**能绑定界面的复用件**"：同一个定义里可以写 `effects`（按钮点击）、`triggers`（禁用/隐藏）、`properties`（图标/坐标）、`dynamic_lists`（用数组生成列表项）、`dirty`（用变量变化驱动刷新）。结构见 `common/scripted_guis/_documentation.md:1-145`（该文件就是权威注释）。它同时属于脚本与表现层，本目录只在 [on-actions.md](on-actions.md) 与 [variables.md](variables.md) 里交叉提到，完整做法见 [../05_presentation/scripted-gui.md](../05_presentation/scripted-gui.md)。

## 8. 加载、覆盖与命名

- 目录内文件名**建议加序号前缀**：原版 `00_scripted_effects.txt`、`00_scripted_triggers.txt`；mod 里用 `zz_MY_scripted_effects.txt` 或 `MY_scripted_effects.txt` 都行，加载顺序按文件名字典序（同目录下）。
- **不要和原版撞名**：vanilla 已有 `can_ROOT_get_wargoal_on_THIS`、`is_JAP_or_ally_of_JAP` 这类名字（`00_scripted_triggers.txt:16-29`）。撞名后哪个生效取决于加载顺序，属于"能跑但不可预期"的行为。
- ⚠️ 待验证：同名 `scripted_effect` 在多个文件里定义时的确切行为（覆盖还是重复注册）本机未做实验；**稳妥做法是一律用 `MY_`/`ADV_` 前缀避免撞名**。
- 改完必须重启游戏；没有官方支持的热重载路径。

## 9. 常见错误 / 自检清单

**error.log 关键字**

- `[effect.cpp:358]: Error: "Unknown effect-type: MY_effect, near line: N"`
  → ① 名字拼错；② 定义文件没被加载（路径不在 `common/scripted_effects/`）；③ 你把它当函数用了（`MY_effect = { arg = 1 }`——引擎会尝试解析 `arg` 为 effect 名）。**HOI4 没有参数块**。
- `[trigger.cpp:568]: Error: "Unknown trigger-type: MY_trigger, near line: N"` → 同上（trigger 版）。
- `[trigger.cpp:700]: Invalid trigger 'xxx' in <file> line : N` → 详细版，带文件路径与行号，定位更快。
- `No localisation for xxx` → `defined_text` 里的 `localization_key` 在 yml 里没有对应条目（`localisation/english/*.yml` 必须存在该 key）。
- `[triggerimplementation.cpp:3617]: Invalid focus scripted in trigger. has_completed_focus = X` → scripted trigger 里引用了**不存在的国策 id**（原版自身也有这种报错，见本机 error.log）。

**自检清单**

- [ ] 定义文件名/对象名统一 `MY_` 前缀，`defined_text` 用 `GetMY_` 前缀。
- [ ] 调用一律 `xxx = yes`；不要写 `xxx = { }`。
- [ ] 每个"靠约定传参"的 scripted_effect，在**定义处第一行写注释**列出它期望的变量/事件目标（否则三个月后自己都不认识）。
- [ ] scripted_trigger 里没有裸露的 `set_temp_variable`；有就包 `hidden_trigger` + `tooltip_evaluation = eval`。
- [ ] 定义里用到 `ROOT`/`FROM` 的地方，假设"调用点才是它们的值"，不要假设是某个固定国家。
- [ ] `defined_text` 的每个 `localization_key` 都在 en + zh 两套 yml 里存在（`loc_check` 控制台命令可批量检查，见 [console-commands.md](console-commands.md)）。
- [ ] 改完跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

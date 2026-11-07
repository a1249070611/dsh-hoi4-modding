---
title: 脚本语言与执行模型（总览与索引）
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/script_concept_documentation.md
  - documentation/effects_documentation.md
  - documentation/triggers_documentation.md
  - common/on_actions/00_on_actions.txt
  - common/collections/_documentation.md
---

# 脚本语言与执行模型（01_script）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**HOI4 的"编程语言"只有两种原语 —— effect（做什么）与 trigger（判断什么），两者都绑定在当前 scope（作用域）上执行**。本目录把这两件事、以及围绕它们的变量 / 迭代 / 复用 / 事件钩子讲透，其余目录只讲"内容怎么写"。

本目录只讲**机制**，不讲国策/装备/界面内容：国策、事件、决议、理念请看 [02_content](../02_content/_index.md)，界面绑定请看 [05_presentation](../05_presentation/_index.md)，地图/军事数据请看 [03_military](../03_military/_index.md) 与 [04_world_map](../04_world/_index.md)。

## 文档清单

| 文档 | 一句话摘要 |
|---|---|
| [scopes.md](scopes.md) | scope 类型、`THIS/ROOT/PREV/FROM` 导航、`event_target:`/`var:`/tag/state-id 作为 scope、错误作用域的真实报错 |
| [effects-triggers.md](effects-triggers.md) | effect 与 trigger 的区别与**求值时机**、`if/else/else_if`、`limit`、`random_list`、循环、`every_/random_/all_/any_` 迭代器、`hidden_*` 与 tooltip 语义 |
| [variables.md](variables.md) | 普通变量 / 临时变量 / 全局变量、`var:` 前缀、变量 target `name@TARGET`、数组与 `array^i`、`check_variable` |
| [dynamic-variables.md](dynamic-variables.md) | 引擎只读动态变量（`num_owned_states`、`party_popularity@x`…）与 `dynamic_modifiers` 的完整生命周期 |
| [scripted-effects-triggers.md](scripted-effects-triggers.md) | `scripted_effects` / `scripted_triggers` / `scripted_localisation` 的复用、为什么没有 `$参数$`、四种"参数化"土办法 |
| [on-actions.md](on-actions.md) | `common/on_actions` 的结构、1.19.3 实到的 115 个 hook、各 hook 的 scope 语义、`on_startup` 初始化与性能 |
| [math-operators.md](math-operators.md) | 数学表达式（33 个函数）、`check_expr` / `debug_math_expr`、`script_constants`、`script_enums` |
| [collections.md](collections.md) | script collections：`input` / `operators` / `name`、内置集合、`collection_size` 的含等号陷阱 |
| [console-commands.md](console-commands.md) | 调试控制台：`eval_effect` / `effect` / `set_var` / `list_vars` / `error` / `reload*` 的实战用法 |

配套：effect/trigger/modifier 的条数级清单以游戏 `documentation/*.md`（`effects_documentation.md` / `triggers_documentation.md` / `modifiers_documentation.md`）为准；需要 JSON 索引时用 `$SKILL/scripts/build_reference.py` 本地生成（产物不随技能分发）。

## 五条最重要的结论

1. **scope 是地基，报错也最频繁。** 每个 effect/trigger 都声明了自己支持的 scope（`documentation/effects_documentation.md` 的 `## Effects for scope COUNTRY` 分节就是这张表）。scope 错时，1.19.3 的报错长这样（本机 `logs/error.log` 实测）：
   `common/technology_tags/00_technology.txt:355: has_country_flag: Invalid Scope, supported: Country, provided: None`
   —— 看到 `Invalid Scope, supported: X, provided: None`，就是"这里根本没有国家/州"。

2. **effect 是"执行"，trigger 是"求值"，两者的调用次数完全不同。** effect 只在所属块真正跑起来时执行一次；trigger 会被反复求值——**包括为了画 tooltip 而求值**。官方文档在 `hidden_trigger` 词条里直接写明："The trigger can still be evaluate when generating a tooltip"，并因此提供了 `tooltip_evaluation = eval|no_eval|legacy`（`documentation/triggers_documentation.md:5103-5144`）。所以**不要**在 trigger 里做 `set_temp_variable` 这类有副作用的事，除非放在 `hidden_trigger` 里并明确 `tooltip_evaluation = eval`。

3. **数值运算不要再手搓 temp variable。** 1.19.x 支持数学表达式，可以内联在 `set_variable` / `add_to_variable` / `check_expr` 里：
   `set_variable = { num_dogs = { value = num_cats multiply = 2 add = 1 } }`（`documentation/effects_documentation.md:7888-7907`）。
   官方明确说这样比用临时变量做计算更快（`documentation/script_concept_documentation.md:184-213`）。

4. **复用靠三件套：`scripted_effects` + `script_constants` + `collections`。** `scripted_effects` 没有 `$PARAM$` 参数机制（本机 `common/scripted_effects/` 下 grep 不到任何 `$...$` 用例），参数化只能靠约定（temp 变量 / global 变量 / `constant:` / 文件局部 `@` 宏 / `event_target`）。而 `collections` 能把"遍历+计数+比较"压成一条 trigger：
   `collection_size = { input = { input = game:scope operators = { faction_members owned_states } } value > 42 }`（`documentation/script_concept_documentation.md:71-80`）。

5. **1.19.x 与网上大量旧教程有明显代差。** 最要紧的三条：① `if` 现在有 `else` / `else_if`（旧教程教你写两个互为 `NOT` 的 `if`）；② 循环统一走 `while_loop_effect` / `for_each_loop` / `for_loop_effect`，本机 `common/` 里**没有**任何裸 `while = {` 用例；③ 变量支持 target：`set_variable = { FROM.defender_state_vs_@ROOT = id }`（"对某个国家记一个值"），旧教程会让你用一堆 `TAG_xxx` 命名硬编码。详见下表。

## 术语表（中英对照，先扫一眼再往下读）

| 术语 | 含义 | 详见 |
|---|---|---|
| effect | 动作/副作用，只执行不返回 | [effects-triggers.md](effects-triggers.md) |
| trigger | 条件/命题，只求值不执行（除非内含副作用，那要 `hidden_trigger`） | [effects-triggers.md](effects-triggers.md) |
| scope（作用域） | 当前脚本作用的游戏对象（国家/州/角色…） | [scopes.md](scopes.md) |
| `ROOT` / `THIS` / `PREV` / `FROM` | 根 scope / 当前 / 上一层 / 事件另一方 | [scopes.md](scopes.md) |
| `limit` | 分支条件（`if`）或过滤条件（迭代器） | [effects-triggers.md](effects-triggers.md) |
| 迭代器 | `every_*` / `random_*` / `all_*` / `any_*`，会对元素逐个执行/判断 | [effects-triggers.md](effects-triggers.md) |
| 变量 target | `变量名@目标`，同名变量按目标对象分槽 | [variables.md](variables.md) |
| 动态变量 | 引擎实时算的只读值（`num_owned_states` 等） | [dynamic-variables.md](dynamic-variables.md) |
| dynamic modifier | 数值可以来自变量的 modifier 容器 | [dynamic-variables.md](dynamic-variables.md) |
| collection（集合） | 一组同类对象 + 可链式过滤/变换 | [collections.md](collections.md) |
| script constant | 跨文件常量，用 `constant:库.key` 引用 | [math-operators.md](math-operators.md) |
| on_action | 游戏事件钩子（开局/每日/宣战/州易手…） | [on-actions.md](on-actions.md) |
| `event_target` | 把某个 scope 存下来，稍后 `event_target:name` 取回 | [scopes.md](scopes.md) |

## 最小可运行骨架：一次把 5 个机制串起来

如果你只想"先跑通一个东西"，照下面 3 个文件建，然后控制台 `effect SWE MY_bootstrap` 即可看到效果。它串起了：**on_action 初始化 → scripted_effect 复用 → 变量 → 数学表达式 → 动态 modifier**。

```pdx
# ① 放置路径：common/scripted_effects/zz_MY_bootstrap.txt
MY_bootstrap = {
    # 用数学表达式算一个 0..100 的分数（不要手搓 temp 变量）
    set_variable = {
        MY_score = {
            value = num_owned_states
            multiply = 3
            add = num_divisions
            clamp = { min = 0 max = 100 }
            round = yes
        }
    }

    # 分级（1.19 支持 else / else_if）
    if = {
        limit = { check_variable = { MY_score > 60 } }
        add_stability = 0.02
        custom_effect_tooltip = MY_score_high_tt
    }
    else = {
        add_stability = -0.01
        custom_effect_tooltip = MY_score_low_tt
    }

    # 落到 game.log，确认真的执行了
    log = "MY_bootstrap ran on SWE, score = [?MY_score]"
}

# ② 放置路径：common/on_actions/zz_MY_on_actions.txt
# on_actions = {
#     on_startup = {
#         effect = {
#             # on_startup 没有国家 scope，必须显式切
#             SWE = { MY_bootstrap = yes }
#         }
#     }
# }
```

```pdx
# ③ 放置路径：common/dynamic_modifiers/zz_MY_dynamic_modifiers.txt
MY_score_modifier = {
    icon = GFX_idea_generic_economic_crisis
    enable = { always = yes }
    stability_weekly = MY_score            # 数值来自变量（见 dynamic-variables.md）
}
```

> 三个文件都放好后**重启游戏**；`game.log` 里应出现 `MY_bootstrap ran ...`。跑不通就按 [console-commands.md](console-commands.md) 第 9 节的闭环排查。

## 如何自己复核本文档的任意一条结论

本目录所有结论都能在本机 3 条命令内复核（Git Bash 写法）：

```bash
GAME="/c/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"   # 按你的安装位置改

# ① 查某个 effect/trigger 是否存在、支持哪些 scope、有没有官方示例
grep -n -A12 '^## add_dynamic_modifier$' "$GAME/documentation/effects_documentation.md"

# ② 查某个写法在本机原版（1.19.x）里是否真的有人用（最有力的"没写错"证据）
grep -rn --include=*.txt 'force_update_dynamic_modifier' "$GAME/common" | head

# ③ 查报错关键字（把 xxx 换成你 error.log 里的原文）
grep -n 'Unknown effect-type' "$USERPROFILE/Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log" | head
```

第三条在本机已经跑过：`error.log` 中确实存在 `Unknown effect-type` / `Unknown trigger-type` / `Invalid Scope, supported: ...` 等行（见各文档的"常见错误"小节，引用的是真实日志原文）。

## 1.19.x 与旧教程差异总表（共 14 条，均为本机验证）

| # | 旧教程常见写法 | 1.19.x 正确/推荐写法 | 证据 |
|---|---|---|---|
| 1 | `if = { limit = { NOT = { x } } ... }` 双写模拟 else | `if = { limit = { x } ... } else = { ... }`，多分支用 `else_if` | `common/decisions/DEN.txt:434`、`common/scripted_effects/CZE_scripted_effects.txt:449`（官方 effects 文档只列 `if`，未列 `else/else_if` → 文档滞后） |
| 2 | `while = { limit = { } ... }` | `while_loop_effect = { limit = { } break = my_break ... }` | `documentation/effects_documentation.md:8573`；本机 `common/` 无裸 `while = {` |
| 3 | 用 `add_to_temp_variable` 一步步算 | 内联数学表达式 / `check_expr` / `debug_math_expr` | `documentation/effects_documentation.md:7888`、`documentation/triggers_documentation.md:2094` |
| 4 | `any_country = { ... }` + 临时变量手动计数 | `collection_size = { input = ... value > N }` | `documentation/script_collection_input.md`、`common/collections/collections.txt` |
| 5 | 到处写魔数 | `common/script_constants/*` + `constant:propaganda.SIA.propaganda_cost_increase` | `common/script_constants/documentation.md`；`common/decisions/SIA.txt:406-419` |
| 6 | 只认识 `@` 宏（文件局部） | `@` 仍可用，但跨文件用 `constant:` | `documentation/script_concept_documentation.md:218`（"script macro operator `@` that is file local"） |
| 7 | 变量就是 `set_variable = { x = 1 }` | 支持 **变量 target**：`set_variable = { FROM.defender_state_vs_@ROOT = id }`、读取 `var:FROM.defender_state_vs_@ROOT` | `common/decisions/WTT_border_conflicts.txt:207,236`、`common/scripted_triggers/00_scripted_triggers.txt:32` |
| 8 | 所有数值都得自己存变量 | 大量 **只读动态变量**：`num_owned_states`、`num_divisions`、`party_popularity@communism`、`building_level@infrastructure` | `documentation/dynamic_variables_documentation.md`（1384 行，按 scope 分组） |
| 9 | 遍历靠 `every_` + 变量 | 数组 + `for_each_loop` / `for_loop_effect` / `for_each_scope_loop`；数组下标 `array^i` | `documentation/effects_documentation.md:4279-4329`；`events/LaR_espionage_operations.txt:189` |
| 10 | `custom_trigger_tooltip` 是标准写法 | 用 `custom_override_tooltip`（`custom_trigger_tooltip` 仅为向后兼容别名） | `documentation/triggers_documentation.md:2431,2482` |
| 11 | `hidden_trigger` 只用来"藏起来" | 还可用 `tooltip_evaluation = eval / no_eval / legacy` 控制 tooltip 求值方式 | `documentation/triggers_documentation.md:5103-5144` |
| 12 | 用字符串拼接生成 effect | `meta_effect = { text = { ... [TOKEN] ... } TOKEN = "..." }` | `documentation/effects_documentation.md:4833`；`common/scripted_effects/CZE_scripted_effects.txt:442-448` |
| 13 | 列表按钮/面板刷新靠自己轮询 | `scripted_gui` 的 `dirty = var_name`：改这个变量即触发界面重算 | `common/scripted_guis/_documentation.md:102-105` |
| 14 | tooltip 直接写 loc key | tooltip 是 **bindable localization**，可嵌套 + 可用格式化器 `custom_effect_tooltip = idea_desc\|token` | `documentation/script_concept_documentation.md:12-57,161-181`、`documentation/loc_formatter_documentation.md` |

> ⚠️ 上表第 2、3、4、5、7、8 条若你看的网络教程页面没有标注 "1.12+"/"1.13+"，基本可以判定它写的是 1.9 前后的老引擎。判断方法：在教程里搜索 `while =`、`custom_trigger_tooltip`、`check_variable` 占满全文，多半已过时。

### 网络交叉验证（2026-10-26 抓取，仅作旁证）

来源：[HOI4 Wiki · Effect](https://hoi4.paradoxwikis.com/Effect)（社区维护，页面自带"may be outdated"警告；本文只取它的 **Version Added** 列来判定"某写法从哪个版本开始有"，核心事实仍以本机 `documentation/*.md` + 游戏文件为准）。

| 写法 | wiki 标注的引入版本 | 与本目录的关系 |
|---|---|---|
| `custom_override_tooltip` | 1.15 | 印证第 10 条"旧教程用 `custom_trigger_tooltip`"已过时 |
| `var:<变量>` 作为 scope 块 | 1.5 | 印证第 7 条"变量可以当 scope/对象"不是新语法，但旧教程常漏讲 |
| `add_dynamic_modifier` / `force_update_dynamic_modifier` | 1.6 | 见 [dynamic-variables.md](dynamic-variables.md) |
| `every_collection_element` | 1.17 | 印证第 4 条"集合是新东西"，见 [collections.md](collections.md) |
| `log` | 1.5 | 见 [console-commands.md](console-commands.md) 调试闭环 |

> wiki 自己在 Effect 页顶部写明："The list of effects may be outdated. A complete ... list can be found in `documentation/effects_documentation.md`" —— 这正是本项目"本机文档 > 游戏文件 > 网络"优先级的外部佐证。

## 事实来源与验证方式（本目录通用）

1. **以本机官方文档为第一优先级**：`documentation/effects_documentation.md`（8603 行）、`triggers_documentation.md`（7713 行）、`dynamic_variables_documentation.md`、`script_math_functions.md`、`script_concept_documentation.md`、`script_collection_input.md` / `script_collection_operator.md`、`console_commands_documentation.md`、`loc_objects_documentation.md`、`loc_formatter_documentation.md`。
2. **第二优先级是本机真实游戏文件**：每个结论都尽量给 `common/…` 或 `events/…` 的文件路径 + 行号，可自行 `grep` 复核。
3. **第三优先级才是网络**：本目录正文只引网络资料来标注"社区常见但未验证"的说法，且带 URL 与版本适用性。当前正文未依赖任何网络断言，全部结论可在本机复核。
4. **报错格式来自真实日志**：`<USER_DIR>\logs\error.log`（2026-10-26 18:22 一次真实启动，含大量第三方 mod）。引用时保留原始行格式，方便你直接在自己的 `error.log` 里搜关键字。

## 学习路径（建议顺序）

1. [scopes.md](scopes.md) —— 先把"当前 scope 是谁"这件事搞清楚，否则后面全是玄学。
2. [effects-triggers.md](effects-triggers.md) —— effect/trigger 的分工与求值时机，决定你写的东西会不会被 tooltip 重复执行。
3. [variables.md](variables.md) → [dynamic-variables.md](dynamic-variables.md) —— 数据怎么存、怎么读、哪些根本不用存。
4. [math-operators.md](math-operators.md) —— 一切数值计算。
5. [collections.md](collections.md) —— 摆脱"遍历 + 手动计数"。
6. [scripted-effects-triggers.md](scripted-effects-triggers.md) —— 把重复代码收成可复用件。
7. [on-actions.md](on-actions.md) —— 唯一可靠的"初始化"和"定期逻辑"入口。
8. [console-commands.md](console-commands.md) —— 调试闭环。

## 和其它目录的边界

- 本目录**不**讲国策 id/图标/`x,y` 布局 → [../02_content/focus-trees.md](../02_content/focus-trees.md)
- 本目录**不**讲事件 `namespace`/`is_triggered_only`/`option` → [../02_content/events.md](../02_content/events.md)
- 本目录**不**讲 `interface/*.gui` 控件与 `.gfx` 精灵 → [../05_presentation/gui-basics.md](../05_presentation/gui-basics.md)
- 本目录**不**讲加载顺序、`replace_path`、校验和 → [../00_start/environment.md](../00_start/environment.md) 与 [../06_workflow/compatibility.md](../06_workflow/compatibility.md)
- 本目录**不**讲 error.log 全量排查流程 → [../06_workflow/debugging.md](../06_workflow/debugging.md)（本目录只给脚本相关的报错关键字）

## 常见错误 / 自检清单（总表）

- [ ] 写 effect/trigger 前，先确认它在文档里对**当前 scope** 有定义（搜 `documentation/effects_documentation.md` 的 scope 分节）。
- [ ] 任何"看起来没生效"的脚本，第一步看 `logs/error.log` 有没有 `Unknown effect-type` / `Unknown trigger-type` / `Invalid Scope` / `Not a valid value`。
- [ ] 缩写名、拼写错误导致的整块静默失效：`Unknown effect-type: xxx` 只会报一行，**它所在的整个 effect 块仍会继续执行后面的兄弟节点**（不要以为整块都没跑）。
- [ ] 在 trigger 里出现 `set_temp_variable` / `add_to_variable` → 几乎一定是 bug（会被 tooltip 重复求值）。
- [ ] 新增 `scripted_effects` / `scripted_triggers` / `on_actions` / `collections` / `dynamic_modifiers` / `script_constants` 文件后必须**重启游戏**，控制台 `reload` 不能完整热更（官方在 script constants 文档里专门说明要"先 reload 常量库，再 reload 使用它的库"，`documentation/script_concept_documentation.md:223-226`）。
- [ ] 所有改动跑一遍静态校验：`python $SKILL/scripts/hoi4_lint.py <mod目录>`（本技能自带脚本）。

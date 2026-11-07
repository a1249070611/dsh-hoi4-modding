---
title: 调试控制台命令
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/console_commands_documentation.md
  - documentation/script_concept_documentation.md
  - common/scripted_effects/zz_debug_effects.txt
  - launcher-settings.json
---

# 调试控制台命令

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：控制台是"**不重启游戏就能验证脚本是否真的执行、变量到底等于几**"的唯一手段。完整 430 条命令清单以游戏 `documentation/console_commands_documentation.md` 为准（可用 `$SKILL/scripts/build_reference.py` 生成 JSON 速查表），本文只讲"写脚本时真正会用到的"。

## 1. 打开控制台的前提

- 用调试模式启动：启动参数 `hoi4.exe -gdpr-compliant -debug_mode`（本机 `launcher-settings.json` 的启动参数，见 [../00_start/environment.md](../00_start/environment.md)）。
- 游戏内默认用 `~` 键呼出（⚠️ 视键盘布局/输入法可能是 `^`；若无反应请先确认 `-debug_mode` 生效）。
- **两类"命令"**（官方定义，`documentation/console_commands_documentation.md:1-13`）：
  1. **Console command**：通用操作（重载文件、切 tag、给经验……）。
  2. **Tweakable variable**：单个开关/数值。布尔型输入名字即切换，输入名字 + 非零/0 可强制启停；整型/浮点型输入名字打印当前值，名字 + 值则设置（见 `:1892-1928`）。
- **控制台会禁用成就（铁人）**；多人游戏里普通玩家不可用。调试完记得退出调试模式。

> ⚠️ **重要事实**：官方文档里有大量命令标注 `* Not available in release build`（如 `spawn`、`debug_achievements`、`dbg_enable_scripted_gui`、`randomlog`）。零售版（我们装的这个）属于 release build，**这些命令不可用**。用到某条命令前先在文档里查它有没有这行标注。

## 2. 脚本调试核心 6 条

| 命令 | 参数 | 作用 | 文档行 |
|---|---|---|---|
| `effect`（别名 `e`） | `<tag> <scripted_effect_name>` | **在指定国家上跑一个 scripted_effect** | 803 |
| `eval_effect` | （内联 effect） | 在选中 scope 上执行**内联** effect | 842 |
| `eval_trigger` | （内联 trigger） | 在选中 scope 上求值**内联** trigger | 846 |
| `event` | `<event id> [<Target Country Tag>]` | 立刻触发事件 | 850 |
| `error` | —— | 显示日志错误（快速查看当前错误数/内容） | 838 |
| `help` / `helplog` | `<command name>` | 查某命令帮助 / 把所有命令打进 `game.log` | 1020 / 1029 |

最常用的一条就是 `effect`：

```text
# 控制台输入（不是写进文件！）
effect GER MY_give_starting_bonus
```

只要把这个 effect 定义在 `common/scripted_effects/` 里（随便哪个文件），就能一行命令立刻验证逻辑，不用等国策/事件触发。这是**迭代脚本最快的闭环**。

## 3. 变量调试三件套

| 命令 | 参数 | 作用 | 文档行 |
|---|---|---|---|
| `set_var` | `<var name>` | 设置变量（⚠️ 官方只写 "Set a variable"，交互细节以 `help set_var` 为准） | 1539 |
| `get_var` | `<var name>` | 读取变量 | 981 |
| `list_vars` | `<scope>` | 列出某个 scope 上的所有变量 | 1116 |

```text
# 典型流程
tag SWE
set_var MY_test_var 42
get_var MY_test_var
list_vars SWE
```

配合脚本里的 `log`（`documentation/effects_documentation.md:4802`）把变量值写进 `game.log`：

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
log = "MY: score = [?MY_score], states = [?num_owned_states]"
```

`[?变量名]` 是变量插值语法（原版 `log` 实例：`common/decisions/NOR.txt:45`）。日志位置：`<USER_DIR>\logs\game.log`。

## 4. 重载类命令：能重载什么、不能重载什么

| 命令 | 重载对象 | 文档行 |
|---|---|---|
| `reloadinterface` | 整个界面（改 `interface/*.gui` 后用） | 1427 |
| `reload_textures`（别名 `rt`） | 贴图，可带文件名过滤 | 1416 |
| `reloadfx` | shader（`map/mapname/postfx` 或 `*.fx`） | 1422 |
| `reloadtechnologies` | 科技数据库 | 1436 |
| `reloadoob` | 某国的 OOB（`<Target Country Tag>`） | 1431 |
| `cityreload` / `gbreload` | 城市 / GB 相关重载 | 424 / 961 |
| `reloadweather` | 天气（带 randomseed 参数） | 1440 |

**必须清楚的限制**：

- **脚本逻辑（`common/scripted_effects`、`scripted_triggers`、`on_actions`、`dynamic_modifiers`、`collections`、`common/decisions` 里的 effect/trigger）没有可靠的控制台热重载**。改完请重启游戏。
- 官方唯一提到"两步重载"的是 **script constants**：改常量后要先重载常量库、再重载使用它的库（`documentation/script_concept_documentation.md:223-226`）；即便如此，实践中仍建议直接重启。
- `reloadinterface` 只解决"界面文件改动"，不解决"脚本逻辑改动"。

## 5. 定位错误与本地化

| 命令 | 作用 | 文档行 |
|---|---|---|
| `error` | 显示日志错误 | 838 |
| `loc_check` | 检查缺失本地化 | 1121 |
| `loc_check_focuses` / `_events` / `_decisions` / `_characters` / `_modifiers` / `_national_spirits` | 按类型检查缺失 | 1125-1145 |
| `debug_checkportraitssanity` | 检查全部角色肖像，问题写进 error log | 557 |
| `history_logger` | 开关 history logger（历史记录写入） | 1037 |
| `randomlog`（别名 `rlog`） | 开关随机日志（⚠️ release build 不可用） | 1389 |
| `dump_cached_random_logs` | 导出缓存的随机日志 | 777 |
| `test_log` | 开关测试日志 | 1732 |

## 6. 界面/地图调试

| 命令 | 作用 | 文档行 |
|---|---|---|
| `guibounds`（别名 `gui`） | 显示 GUI 边界框（改 `.gui` 必用） | 1005 |
| `debug_nogui` | 开关整个 GUI（排查"是不是界面卡住"） | 629 |
| `nudge` | 进入 Nudge 工具（调地图/单位位置） | 1238 |
| `imgui` | ImGui 调试面板 | 1050 |
| `dbg_enable_scripted_gui` `<scope>` | 启用 scripted GUI（⚠️ release build 不可用） | 498 |
| `map_icon_reload_type` | 重载 map icon 类型（`<NUM>` 或 `help`） | 1168 |
| `goto_province` / `goto_state` / `goto_region` | 视角跳到省/州/区域 | 986 / 996 / 991 |

## 7. 快速造局面（写事件/国策时验证分支）

| 命令 | 参数 | 作用 | 文档行 |
|---|---|---|---|
| `tag` | `<Country tag>` | 切换操作的国家 | 1712 |
| `observe`（别名 `spectator`） | —— | 变成观战（不选国家） | 1248 |
| `xp` | `<XP amount>` | 给陆海空经验 | 1887 |
| `manpower` | `<Amount>` | 加人力 | 1163 |
| `research` | `<slot id>` 或 `all` | 研究某槽位/全部科技 | 1455 |
| `instantconstruction`（别名 `ic`） | —— | 开关瞬间建造 | 1062 |
| `annex` | `<Target Country Tag>` | 吞并某国 | 345 |
| `whitepeace`（别名 `wp`） | `<country tags>` | 与指定国家白和 | 1875 |
| `teleport`（别名 `tp`） | `<province_id>` | 把选中部队/舰队传送到省 | 1721 |
| `setowner` | `<country tag> <state id>` | 设置州所有者 | 1554 |
| `setcontroller` | `<country tag> <province id>` | 设置省控制者 | 1549 |
| `add_equipment`（别名 `ae`） | `<amount> <equipment name>` | 加装备 | 166 |
| `ai` / `human_ai` | —— | 开关 AI / 让 AI 接管玩家国 | 253 / 1046 |
| `nukes`（别名 `nuke`） | `<count>` | 加核弹 | `nukes` 词条 |
| `spawn` | `<SubUnit Type> <Province ID> <Amount>` | 刷单位（⚠️ release build 不可用） | 1690 |

## 8. 一个"调试专用 effect 文件"模板

原版自己就有这么一个文件：`common/scripted_effects/zz_debug_effects.txt`。建议你也建一个 `zz_MY_debug_effects.txt`，把常用调试逻辑固化，靠控制台 `effect` 一行调用。

```pdx
# 放置路径：common/scripted_effects/zz_MY_debug_effects.txt
# 用法（控制台）：effect GER MY_debug_dump_state
MY_debug_dump_state = {
    log = "==== MY debug dump ===="
    log = "political_power = [?political_power]"
    log = "stability = [?stability]"
    log = "num_owned_states = [?num_owned_states]"
    log = "num_divisions = [?num_divisions]"
    log = "MY_score = [?MY_score]"
    print_variables = {                                # 把变量表写成文件
        file = MY_debug_vars
        text = "MY_debug_dump_state"
        append = no
        print_global = yes
    }
}

# 用法：effect GER MY_debug_give_resources
MY_debug_give_resources = {
    add_political_power = 1000
    army_experience = 500
    air_experience = 500
    navy_experience = 500
    add_command_power = 500
    custom_effect_tooltip = MY_debug_give_resources_tt
}

# 用法：effect GER MY_debug_test_trigger
MY_debug_test_trigger = {
    if = {
        limit = { MY_ready_for_reform = yes }
        log = "MY: trigger MY_ready_for_reform = TRUE"
    }
    else = {
        log = "MY: trigger MY_ready_for_reform = FALSE"
    }
}
```

> `log` 会写进 `game.log`、console（若可见）以及 history logger（若开启），且**可以被本地化**（`documentation/effects_documentation.md:4802`）。

## 9. 调试闭环工作流（推荐）

1. 改脚本（effect/trigger/decision…）。
2. **重启游戏**（脚本逻辑无可靠热重载）。
3. 控制台 `tag TAG` 切到目标国家。
4. `effect TAG MY_test_entry` 直接调用你的 scripted_effect。
5. 看 `game.log`（`log` 输出）和 `error.log`（报错），或 `error` 命令速查。
6. 数值不对 → `list_vars` / `get_var` / `print_variables` 三选一确认。
7. 界面不刷新 → `reloadinterface`（仅界面文件改动有效）。
8. 改完提交前跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

日志目录：`<USER_DIR>\logs\`
关键文件：`error.log`（脚本/资源报错）、`game.log`（`log` 输出）、`system.log`（启动流程）。

## 10. 常见错误 / 自检清单

- **敲了命令没反应** → ① 没加 `-debug_mode`；② 该命令标注了 `Not available in release build`；③ 拼写/别名错误（先 `help <name>`）。
- **`effect` 没效果** → scripted_effect 名字拼错（看 `error.log` 的 `Unknown effect-type`）；或 tag 写错；或 effect 内部 scope 不对（`on_startup` 式无 scope 问题）。
- **`set_var`/`get_var` 结果怪** → 变量有 scope 前缀（`TAG.var`）时要用完整路径；全局变量用 `global.x`。
- **重载后行为没变** → 你改的是脚本逻辑，控制台重载不了；重启。
- **控制台确认的效果与真实游戏不一致** → 控制台是在"当前 tick"直接执行，某些依赖每日更新的东西（如 dynamic modifier 数值）仍需等一天或 `force_update_dynamic_modifier`。

**自检清单**

- [ ] 调试用的是 `-debug_mode` 启动，正式发布时不再依赖控制台。
- [ ] 所有"验证分支"用的调试 effect 都放在 `zz_MY_debug_effects.txt` 里，**发布前删除或加 `hide_from_ui` 类隔离手段**（至少确保没有玩家可达入口）。
- [ ] `log` 里的变量插值写成 `[?变量名]`，且变量确实存在（否则日志里是空/0）。
- [ ] 不用控制台命令做"只能靠命令达成"的内容设计（玩家没有控制台）。
- [ ] 报错排查优先看 `error.log`，而不是凭感觉改代码；把本文与 [../06_workflow/debugging.md](../06_workflow/debugging.md) 配合看。

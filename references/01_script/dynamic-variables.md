---
title: 动态变量与 dynamic_modifiers
domain: 01_script
scope: any
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - documentation/dynamic_variables_documentation.md
  - common/dynamic_modifiers/0_dynamic_modifiers.txt
  - common/dynamic_modifiers/aat_dynamic_modifiers.txt
  - common/scripted_effects/PHI_scripted_effects.txt
  - documentation/effects_documentation.md
---

# 动态变量与 dynamic_modifiers

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**动态变量 = 引擎实时算给你、你只读不写的"计算字段"**（`num_owned_states`、`party_popularity@communism`、`building_level@infrastructure`…）；**dynamic_modifier = 一个"数值可以来自变量"的 modifier 容器**，两者配合就能做出"随状态自动变化的强力国家精神"。

## 1. 动态变量是什么

官方定义（`documentation/dynamic_variables_documentation.md:1-7`）：

> Dynamic variables are **read only** variables that can be used in effects & triggers that accept variables.
> When they are used, the game will compute and return the value of the dynamic variable.

三个要点：

1. **只读**：你 `set_variable` 改不了它；同名时"你写的变量"与"动态变量"是两套东西，不要混。
2. **懒计算**：用到时才由引擎算，不占你的存档。
3. **只能用在"接受变量"的位置**：`check_variable`、`set_variable = { x = <动态变量> }`、`value =` 参数、math expression 的操作数、`target =` 等。

## 2. 引用语法（四种形态）

```
<name>                      # 当前 scope 的动态变量
<SCOPE>.<name>              # 指定对象的动态变量
<name>@<TARGET>             # 带 target 的动态变量（需要 target 的那些）
<SCOPE>.<name>@<TARGET>     # 组合
```

| 例子 | 含义 | 出处 |
|---|---|---|
| `num_owned_states` | 当前国家的拥有州数 | `dynamic_variables_documentation.md:670` |
| `GER.air_intel@ENG` | 德国对英国的空情 | 同文件 `:138-140` |
| `party_popularity@communism` | 某意识形态支持率（target = 意识形态 token；也接受 `ruling_party` 或一个"存着意识形态的变量名"） | `:722-723` |
| `building_level@infrastructure` | 某建筑在州里的等级（target = 建筑 token） | `:1101-1102` |
| `days_mission_timeout@GER_mefo_bills_mission` | 某个限时任务的剩余天数（target = 任务 token） | `:238-239` |
| `modifier@local_manpower` | 州上某 modifier 的值（target = modifier token） | `:1136-1137` |
| `distance_to@124` | 到另一个州的距离 | `:1127-1128` |

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
# 注意：下面用到的每个动态变量名都能在 documentation/dynamic_variables_documentation.md 里搜到
MY_dynamic_var_demo = {
    # 直接当数值用
    add_political_power = num_owned_states
    add_command_power = num_divisions          # 需要除法就用 math expression，见 math-operators.md

    # 存进普通变量做快照
    set_variable = { MY_snapshot_pp = political_power }
    set_variable = { MY_snapshot_stab = stability }
    set_variable = { MY_snapshot_factories = num_of_military_factories }

    # 带 scope 前缀
    set_variable = { MY_enemy_intel = GER.army_intel@ENG }

    # 带 target
    set_variable = { MY_communism = party_popularity@communism }

    # 用在 check_variable 里
    if = {
        limit = { check_variable = { MY_snapshot_pp > 150 } }
        add_stability = 0.01
    }
}
```

> ⚠️ PDX 脚本**没有中缀运算符**：`num_divisions / 100` 这种写法不存在。要除法请写进 math expression（`{ value = num_divisions  divide = 100 }`）或用 `divide_variable`，见 [math-operators.md](math-operators.md)。

## 3. 按 scope 分组的常用动态变量（全部实测存在）

完整清单共 1384 行，分 6 个 scope 段（`global` 972 行起、`country` 18 行起、`state` 1096 行起、`unit_leader` 1176 行起、`military_industrial_organization` 1058 行起、`special_project` 1085 行起）。挑最常用的：

**COUNTRY（当前国家）**

| 动态变量 | 含义 | 文档行 |
|---|---|---|
| `num_owned_states` / `num_controlled_states` | 拥有州数 / 控制州数 | 670 / 541 |
| `num_divisions` / `num_armies` | 师数 / 集团军数 | 553 / 526 |
| `num_faction_members` | 阵营成员数 | 566 |
| `political_power` / `stability` | 政治点 / 稳定度 | 743 / 785 |
| `army_experience` / `air_experience` | 陆/空经验 | 168 / 135 |
| `capital` / `country_leader` / `army_chief` / `air_chief` | 首都州 / 领袖 / 陆空军参谋长（返回**对象**，可当 scope） | 180 / 226 / 165 / 132 |
| `controlled_states` / `core_states` / `allies` | 州/国家**数组** | 207 / 223 / 149 |
| `autonomy_ratio` | 自治度（非附庸为 -1） | 177 |
| `casualties` / `convoys_destroyed` | 伤亡 / 被击沉运输船 | 183 / 214 |
| `current_party_ideology_group` | 执政意识形态组 token | 232 |
| `army_intel@TAG` / `air_intel@TAG` / `civilian_intel@TAG` | 对某国情报 | 171 / 138 / 191 |

**STATE（当前州）**：`arms_factory_level`(1098)、`industrial_complex_level`(1130)、`infrastructure_level`(1133)、`building_level@<building>`(1101)、`compliance`(1104)、`controller`(1112)、`core_countries`(1115)、`modifier@<modifier>`(1136)、`distance_to@<state>`(1127)。

**GLOBAL**：`countries`（所有国家数组，974）、`majors`（主要国家数组，993）、`date`（977）、`num_days`（当前总天数，996）、`difficulty`（难度 0-2，980）、`global_resource_extracted@<resource>`（984）、`operations`（1003）。

**UNIT_LEADER / MIO / SPECIAL_PROJECT**：见 `dynamic_variables_documentation.md:1058`（MIO）、`:1085`（特殊项目）、`:1176`（将领）。将领段里也有 `num_units`(1310) 这类。

> 用法提示：文档里每条都标注了来源——`* (Auto generated using the trigger with same name)` 表示它就是把同名 trigger 当数值读，所以**语义可以直接查 triggers 文档**。

## 4. 动态变量 vs 普通变量：怎么选

| 需求 | 用哪个 |
|---|---|
| 查询"当前有多少州/多少师/多少政治点" | **动态变量**（不用存） |
| 需要"历史最高/累计/一次性快照" | 普通变量（`set_variable` 存一份） |
| 需要参与 UI 显示且要自动更新 | 普通变量 + `dynamic_modifier` 或 scripted GUI 的 `dirty` |
| 要给玩家看一个"实时变化的百分比" | 普通变量（每日 on_action 更新）+ `dynamic_modifier` 消费它 |

关键差别：动态变量**不能写**，所以任何"随时间累积"的东西必须落到普通变量里。

## 5. `dynamic_modifiers`：让 modifier 的数值来自变量

### 5.1 定义文件（`common/dynamic_modifiers/*.txt`）

官方在 `common/dynamic_modifiers/0_dynamic_modifiers.txt:1-27` 给了完整字段说明（**这是最权威的速查，建议直接打开该文件**）：

```pdx
# 放置路径：common/dynamic_modifiers/MY_dynamic_modifiers.txt
# 字段说明（依据 0_dynamic_modifiers.txt 头注释）：
#   icon = "GFX_idea_unknown"      # 可选，有 icon 才会在 GUI 里显示
#   enable = { always = yes }      # 可选，不满足则整个 modifier 不生效
#   remove_trigger = { ... }        # 可选，为真时自动移除
#   attacker_modifier = no          # yes = 该 modifier 在战斗中也会对进攻方读取
#   然后是一串 modifier = 值；值可以是数字，也可以是【变量名】

MY_economy_modifier = {
    icon = GFX_idea_generic_economic_crisis
    enable = { always = yes }

    # 当这三个变量都归零时自动移除
    remove_trigger = {
        check_variable = { MY_growth = 0 }
        check_variable = { MY_consumer_goods = 0 }
    }

    # 值 = 变量名（引擎每天从宿主 scope 上读这些变量）
    industrial_capacity_factory = MY_growth
    consumer_goods_factor = MY_consumer_goods
    stability_weekly = MY_stability_delta
}
```

**真实原版同款**（强烈建议照着抄结构）：`common/dynamic_modifiers/aat_dynamic_modifiers.txt:537-550` 的丹麦国家精神——

```pdx
DEN_neglected_military_dynamic_modifier = {
	enable = { always = yes }
	icon = GFX_idea_generic_neglected_military

	remove_trigger = {
		check_variable = { DEN.DEN_neglected_military_mobilization_speed = 0 }
		check_variable = { DEN.DEN_neglected_military_surrender_limit = 0 }
		check_variable = { DEN.DEN_neglected_military_planning_speed = 0 }
	}

	mobilization_speed = DEN_neglected_military_mobilization_speed   # -0.2
	surrender_limit   = DEN_neglected_military_surrender_limit       # -0.2
	planning_speed    = DEN_neglected_military_planning_speed        # -0.1
}
```

对应的变量在国策/事件里用 `add_to_variable` 修改：`common/national_focus/denmark.txt:9425` → `add_to_variable = { DEN_neglected_military_mobilization_speed = 0.1 }`。

> 注意头注释里那行 `max_fuel = var_max_fuel` **不是**新语法：它的意思是"这里填一个变量名，示例里那个变量恰好叫 `var_max_fuel`"（原文件 12 行）。

### 5.2 添加 / 移除 / 强制刷新

```pdx
# 放置路径：common/scripted_effects/MY_scripted_effects.txt
MY_apply_economy_modifier = {
    # ① 添加（默认：挂到当前 scope 上，只对当前 scope 生效）
    add_dynamic_modifier = { modifier = MY_economy_modifier }

    # ② 带时限 / 限定目标 scope
    add_dynamic_modifier = {
        modifier = MY_economy_modifier
        days = 90              # 到期自动移除，可以是变量
        scope = GER            # 可选：只对 GER 生效（state scope 下常这么用）
    }

    # ③ 移除
    remove_dynamic_modifier = { modifier = MY_economy_modifier }

    # ④ 改完变量后立刻刷新（不等引擎的每日更新）
    force_update_dynamic_modifier = yes
}
```

- `add_dynamic_modifier` 词条：`documentation/effects_documentation.md:1153-1172`；支持 scope 为 `STATE, COUNTRY, CHARACTER, SPECIAL_PROJECT`。
- `remove_dynamic_modifier` 词条：`:5978-5990`。
- `force_update_dynamic_modifier` 词条：`:4372-4381`，原文 "updates the modifiers in current scope (use if you don't want to wait for daily update)"。
- **原版活跃用例**（正确的"改完变量立刻刷新"写法）：`common/scripted_effects/PHI_scripted_effects.txt:375-390` —— 先 `set_variable` 改一堆 `PHI_ruling_ideology_ideology_drift_*`，最后一行 `force_update_dynamic_modifier = yes`；另有 `common/national_focus/congo_shared.txt:1149,4810`。

### 5.3 生命周期（务必记住）

1. 定义**在加载时**读入并校验（modifier 名写错 → 加载期报 `Unknown modifier: xxx`）。
2. 挂到 scope 上后，**数值每天更新一次**（`0_dynamic_modifiers.txt:27` 原文："will only updated daily, unless forced by `force_update_dynamic_modifier` effect"）。
3. `enable` 为假 → 整个 modifier 不生效（但仍"挂着"）。
4. `remove_trigger` 为真 → 自动移除。
5. `days` 到期 → 自动移除。
6. **tooltip 呈现**：wiki 在 `add_dynamic_modifier` 词条里明确写"用变量的 modifier 不会显示在这个 effect 的 tooltip 里，用静态数值的才会"（[Effect · add_dynamic_modifier](https://hoi4.paradoxwikis.com/Effect)，抓取 2026-10-26）。所以给玩家的说明要靠 `custom_effect_tooltip` 手写。

## 6. 完整可跑示例：变量驱动 + 定时刷新的动态国家精神

```pdx
# ① 定义：common/dynamic_modifiers/MY_dynamic_modifiers.txt
MY_industrial_push_modifier = {
    icon = GFX_idea_generic_economic_crisis
    enable = { always = yes }
    remove_trigger = {
        check_variable = { MY_push_factory_output = 0 }
        check_variable = { MY_push_consumer_goods = 0 }
    }
    industrial_capacity_factory = MY_push_factory_output
    consumer_goods_factor        = MY_push_consumer_goods
}

# ② 初始化 + 施加：common/scripted_effects/MY_scripted_effects.txt
MY_start_industrial_push = {
    set_variable = { MY_push_factory_output = 0.05 }
    set_variable = { MY_push_consumer_goods = 0.03 }
    add_dynamic_modifier = { modifier = MY_industrial_push_modifier }
}

# ③ 每次国策推进时加强，并立刻刷新：common/scripted_effects/MY_scripted_effects.txt
MY_boost_industrial_push = {
    add_to_variable = { MY_push_factory_output = 0.05 }
    clamp_variable = { var = MY_push_factory_output min = 0 max = 0.30 }
    force_update_dynamic_modifier = yes           # 不等明天，立刻生效
    custom_effect_tooltip = MY_industrial_push_tt  # 给玩家一条可读提示
}

# ④ 结束：common/scripted_effects/MY_scripted_effects.txt
MY_stop_industrial_push = {
    set_variable = { MY_push_factory_output = 0 }
    set_variable = { MY_push_consumer_goods = 0 }
    remove_dynamic_modifier = { modifier = MY_industrial_push_modifier }
}
```

> `industrial_capacity_factory` / `consumer_goods_factor` 都是真实 modifier 名（在 `documentation/modifiers_documentation.md` 里可搜到；也可在 `documentation/modifiers_documentation.md` 里全文检索）。**别凭记忆写 modifier 名**——写错只会在加载期报 `Unknown modifier: xxx`，然后整条定义被丢弃。

## 7. 常见错误 / 自检清单

**error.log 关键字**

- `[persistent.cpp:67]: Error: "Unknown modifier: sp_thermo_nuclear_bomb_speed_factor, near line: 422" in file: "common/buildings/00_buildings.txt"`
  → modifier 名不在数据库里（拼错或该 DLC/版本没有）。dynamic modifier 文件里同样会报这条，且**该 modifier 定义整块失效**。
- `[scopedvariable.cpp:571]: ai_num_of_military_factories is not a valid mtth database object`
  → 把不存在的名字当变量读。dynamic modifier 里写 `industrial_capacity_factory = MY_typo_var` 之后，如果没有地方定义 `MY_typo_var`，你会在加载/运行期撞上这类提示（数值被当 0）。
- `[effect.cpp:358]: Error: "Unknown effect-type: force_update_dynamic_modifier, ..."`
  → 不在合法 scope 里（它支持 `STATE, COUNTRY, CHARACTER, SPECIAL_PROJECT`，见文档 4374 行），或整个 effect 名拼错。

**自检清单**

- [ ] 每个 modifier 名都能在 `documentation/modifiers_documentation.md` 或 `documentation/modifiers_documentation.md` 里查到。
- [ ] 变量名带 mod 前缀，且**在施加 modifier 之前就已经 `set_variable` 初始化过**（否则首日数值为 0）。
- [ ] 需要"改完立刻生效"的地方都补了 `force_update_dynamic_modifier = yes`（它不会自动传播）。
- [ ] 有 `remove_trigger` 的 modifier，确认触发条件真的能到 0（否则永远挂着）。
- [ ] 用 `days` 做临时 modifier 时，注意 `days` 的倒计时与 `remove_trigger` 是两套独立机制。
- [ ] dynamic modifier 文件改完必须**重启游戏**（没有可靠的控制台热重载路径）。
- [ ] 跑 `python $SKILL/scripts/hoi4_lint.py <mod目录>`。

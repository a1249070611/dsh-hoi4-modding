---
name: kiant-hoi4-game-framework
description: HOI4 游戏框架层：defines 覆盖、on_actions 钩子、game rules、scripted effects/triggers/guis、国家历史与开局、AI 策略。改「系统级行为」而非加内容的场景。
---

# 游戏框架

这里放的是"改引擎行为"而不是"加内容"的东西。风险比加国策高一个量级——影响面是全游戏的。

## defines：改数值常数

`common/defines/*.lua`：

```lua
NDefines.NGame.START_DATE = "1936.1.1"
NDefines.NDiplomacy.VOLUNTEERS_DIVISIONS_REQUIRED = 20
NDefines.NMilitary.MAX_DIVISION_SIZE = 100
```

规则：

- 必须以 `NDefines.` 开头，裸变量赋值不生效
- 是 **Lua 语法**，但只有赋值语句有效，不要写循环/函数
- 覆盖是"改原版的值"，不是"追加"
- 改错一个常量可能让 AI 或战斗逻辑整体失衡，且不会报错

`defines` 校验器会检查括号配平与 `NDefines.` 前缀。

## on_actions：事件钩子

`common/on_actions/*.txt`：

```
on_actions = {
	on_startup = {
		effect = {
			set_variable = mymod_started = yes
		}
		events = { mymod.1 }
	}

	on_monthly = {
		random_events = {
			100 = mymod.10
			50 = mymod.11
		}
	}
}
```

常见钩子：`on_startup`、`on_daily`、`on_weekly`、`on_monthly`、`on_war_declared`、`on_capitulation`、`on_civil_war_start`、`on_puppet` 等。

`random_events` 的键是权重，值是事件 id；`events` 是必定触发。`on_actions` 校验器会检查引用的事件是否存在。

注意：`on_daily` / `on_monthly` 里的 effect 会对**每个国家**执行，写重了会明显拖慢游戏（尤其在 200 个国家上跑复杂效果）。

## scripted effects / triggers

`common/scripted_effects/`、`common/scripted_triggers/`：

```
# 定义
MY_check_industry = {
	has_tech = industry_1939
	num_of_factories > 30
}

# 调用处
available = { MY_check_industry = yes }
```

这是让 mod 可被 submod 复用的关键：暴露宏，而不是让 submod 复制你的逻辑。

命名规范：trigger 用 `_check_` / `_is_` 前缀，effect 用动词短语，都带 mod 前缀避免撞名。

## game rules

`common/game_rules/*.txt` 定义开局可选项（类似"历史国策 vs 非历史"）：

```
game_rules = {
	mymod_aggression = {
		name = "RULE_MYMOD_AGGRESSION"
		allowed = { always = yes }
		default = mymod_normal
		mymod_normal = {}
		mymod_high = {}
	}
}
```

规则只负责"玩家选了什么"，实际行为要靠 `has_game_rule = { name = mymod_aggression value = mymod_high }` 在 scripted trigger 里判断。

## 国家历史与开局

`history/countries/TAG - Name.txt`：

```
capital = 64
set_politics = {
	ruling_party = fascism
	elections_allowed = no
}
set_popularities = {
	democratic = 10
	fascism = 60
	communism = 5
	neutrality = 25
}
add_ideas = { MY_starting_idea }
oob = "GER_1936"
```

`oob` 指向 `history/units/<名字>.txt`。`history` 校验器会检查：

- `add_ideas` 里的精神是否真的定义过
- `oob` 指向的文件是否存在

缺 oob 的典型症状：该国开局没有部队，日志里只有一行 Failed to load，很容易被忽略。

## AI 策略

`common/ai_strategy/`、`common/ai_focuses/`、`common/ai_template/` 控制 AI 行为。做大型 mod 时如果 AI 表现怪异，先看这里有没有覆盖原版。

## 框架层的原则

1. **能加内容就不要改框架。** 改 defines / on_actions 会与所有同类 mod 冲突。
2. **改之前先备份原值。** 记在 ROADMAP.md 或注释里，否则半年后你不知道自己改了什么。
3. **影响面标注。** README 里写清"修改了 NGame.START_DATE，影响所有剧本"。
4. **每次改完跑 `kiant_hoi4_validate_mod deep=true`**，`defines` 与 `on_actions` 校验器会拦住最常见的手误。

## 需要原版参照时

框架层字段各版本差异大，别凭记忆：

```
kiant_hoi4_kb_lookup kind=on_action limit=3
kiant_hoi4_kb_search "NDefines.NGame" source=vanilla
kiant_hoi4_kb_search "game_rules"
```

先看原版怎么写，再动手。这是这个平台相较"让模型直接写"的核心差别。

## 音乐 / 电台（常见盲区）

音乐在**游戏根 `music/`**（不在 common/），两层缺一层就静默（EB-022）：
`music/*.asset` 定义歌（`music = { name file volume }`）→
`music/*.txt` 播放表（`music_station` + `chance` 加权选曲）。
`play_song = "X"` 引用未定义歌名不报错、直接跳过。
电台封面 sprite 固定命名 `GFX_music_station_<台名>`。
全文见 `references/05_presentation/audio.md` §6.3。

## replace_path 的连带义务

`replace_path="events"` 会让原版全部事件退场——间谍（LaR）、核爆等
被 on_actions/决议引用的系统事件要**手动补回**（TFR 拷整文件、ES 重写
namespace 双实证，见 EB-025）。replace 后目录里所有 txt 都会加载，
旧版遗留文件会与新文件并存双触发，清理要彻底。

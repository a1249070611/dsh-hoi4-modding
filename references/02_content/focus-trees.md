---
title: 国策树（Focus Trees）
domain: 02_content
scope: country
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - common/national_focus/germany.txt
  - common/national_focus/baltic_shared.txt
  - common/national_focus/estonia.txt
  - common/national_focus/latvia.txt
  - common/focus_inlay_windows/documentation.md
  - localisation/english/wuw_focus_l_english.yml
---

# 国策树（Focus Trees）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `common/national_focus/`（**只读 .txt，支持任意文件名**，原版按国家名命名，如 `germany.txt`、`china_nationalist.txt`） |
| 子目录 | 允许（原版有 `common/national_focus/<subdir>/` 的 mod 常见做法；最稳的是平铺） |
| 读取时机 | 游戏启动建库；改文件必须**重启游戏** |
| 覆盖语义 | 同名文件整体替换；**同 `focus` id 后者覆盖前者**（可用新文件覆盖单条国策） |
| 校验和 | 影响（内容进 `checksum`，联机需一致） |
| 本地化 | `<focus_id>` = 名称，`<focus_id>_desc` = 描述（证据 `localisation/english/wuw_focus_l_english.yml:3039-3040`） |

原版必读参考（按学习顺序）：

- `common/national_focus/germany.txt` —— 树头、shortcut、inlay_window、search_filters、completion_reward 的密集用法（38,934 行，1.19.4.2 实测，全库最全）。
- `common/national_focus/baltic_shared.txt` —— 文件开头的**注释模板**列出 `focus`/`shared_focus` 全参数（第 1-35 行）。
- `common/national_focus/estonia.txt:61-62` —— 树内挂共享国策：`shared_focus = BALTIC_rejoin_the_railways`。
- `common/national_focus/latvia.txt:1962,2690-2693` —— `will_lead_to_war_with` 的真实用法。
- `common/focus_inlay_windows/documentation.md` —— 1.19 的国策内嵌窗口（inlay window）系统。

**官方文档位置（1.19.4.2 实测）**：`common/national_focus/` **没有** `_documentation.md`——国策域唯一带官方说明的是 `common/focus_inlay_windows/documentation.md`（只讲 inlay 子系统）。因此国策字段的事实来源优先级是：
① `common/national_focus/baltic_shared.txt` 头部注释（`focus`/`shared_focus` 参数模板）+ `germany.txt` 头部注释（`search_filters` 全集）；
② `documentation/effects_documentation.md` / `triggers_documentation.md` 里被 `completion_reward`/`available` 调用的条目；
③ 抄 vanilla 实例。域规模：81 个 `.txt`、691,478 行。

## 2. 结构（带注释）

```pdx
# ============ 树头 ============
focus_tree = {
	id = my_tree_id                 # 全库唯一

	country = {                     # 哪些国家拥有这棵树（权重制）
		factor = 0                  # 0 = 默认不获得
		modifier = {
			add = 10
			tag = SWE               # 证据 germany.txt:27-34（用 tag = GER）
		}
	}

	initial_show_position = { x = 76 y = 0 }   # 打开国策界面时居中到哪（germany.txt:36-39）
	continuous_focus_position = { x = 500 y = 1300 } # 持续国策槽位置（germany.txt:94）

	shortcut = {                    # 左侧「路径跳转」按钮（germany.txt:42-49）
		name = MY_shortcut          # 本地化 key
		target = MY_first_focus     # 跳到哪个国策
		scroll_wheel_factor = 0.5   # 可选，缩放级别
		trigger = { has_dlc = "Gotterdammerung" } # 可选，不满足则不显示
	}

	inlay_window = {                # 1.19：把 common/focus_inlay_windows 定义的窗口嵌进树
		id = my_inlay_window
		position = { x = 4500 y = 1150 }
	}

	default = no                    # no = 只有 country 命中的国家才有（germany.txt:101）

	# 已有共享国策也可以在这里批量挂（等价于树里写 shared_focus = xxx）
	# reset_on_civil_war = yes      # ⚠️ 本机未在 1.19 活动文件中确认，见文末
}

# ============ 单个国策 ============
focus = {
	id = MY_focus_one               # 全局唯一，建议 NAMESPACE_ 前缀
	icon = GFX_focus_generic_industry # 必须是已注册 sprite
	x = 0                           # 网格横坐标（整数，可为负）
	y = 0                           # 网格纵坐标
	cost = 8                        # 天数 = cost × 7（原版 germany.txt:19 注释：x7 to get the days）

	prerequisite = { focus = MY_focus_zero }            # 前置（可写多行 = AND）
	# prerequisite = { focus = A focus = B }             # 多个写在同一块 = 全都要
	# 也可以用 OR 分支：prerequisite = { focus = A } + 另一个同名块（多个 prerequisite 块 = OR）
	mutually_exclusive = { focus = MY_focus_two }        # 互斥（双向：对方也要声明）

	available = {                   # 不满足 = 可见但灰、不能点
		has_political_power > 50
	}
	bypass = {                      # 满足则「跳过」该焦点（走 AI/剧情路线时用）
		has_war = yes
	}
	cancel_if_invalid = yes         # 完成前置后 available 失效是否取消当前进度
	continue_if_invalid = no        # available 失效时是否继续计时
	available_if_capitulated = no   # 投降后是否可选
	will_lead_to_war_with = POL     # 目标国家会因此对你提高战争倾向（latvia.txt:1962）

	# complete_tooltip = { ... }    # 覆盖完成提示的 effect 展示

	search_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_INDUSTRY } # 必须用原版过滤器 token

	ai_will_do = {                  # AI 选择权重
		factor = 10
		modifier = {
			factor = 0
			has_war = yes
		}
	}

	completion_reward = {           # 完成时执行的 effect（作用域 THIS = 国家）
		add_political_power = 50
		add_ideas = MY_idea_one
		country_event = { id = hho.1 days = 1 }
	}
}
```

### 可用 `search_filters` 全集（来自 `common/national_focus/germany.txt:2-17` 的文件头注释）

`FOCUS_FILTER_POLITICAL`、`FOCUS_FILTER_RESEARCH`、`FOCUS_FILTER_INDUSTRY`、`FOCUS_FILTER_STABILITY`、
`FOCUS_FILTER_WAR_SUPPORT`、`FOCUS_FILTER_MANPOWER`、`FOCUS_FILTER_ANNEXATION`、`FOCUS_FILTER_INTERNAL_AFFAIRS`、
`FOCUS_FILTER_ARMY_XP`、`FOCUS_FILTER_NAVY_XP`、`FOCUS_FILTER_AIR_XP`、`FOCUS_FILTER_BALANCE_OF_POWER`、
`FOCUS_FILTER_POLITICAL_CHARACTER`、`FOCUS_FILTER_MILITARY_CHARACTER`、`FOCUS_FILTER_INTERNATIONAL_TRADE`、
`FOCUS_FILTER_HISTORICAL`。
写不存在的过滤器 = 界面上不显示该标签，不报错，但等于白写。

## 2.5 国策树是怎么分配给国家的（最容易误解的一点）

`country = { ... }` 不是「谁拥有这棵树」的布尔开关，而是 **MTTH 式打分**：游戏在**开局前**给每个国家算一遍所有 `focus_tree` 的分数，**取分数最高的那一棵加载**（官方 wiki: National focus modding §Focus tree；游戏内字符串也有 `Only one national focus tree should be default`）。要点：

- **同一国家同一时间只有一棵激活的国策树**，没有「多棵树变成多个标签页」这回事。`default = yes` 只影响「所有树都是 0 分时选谁」（原版只有 `generic_focus` 是 default）。
- 给**已有专属树**的国家（如 SWE、GER、SOV）加国策，不能只写一棵新树——它会和原版树比分，可能被原版压掉、也可能顶掉原版（取决于分数/加载顺序），两种都不可靠。正确做法只有：
  1. **覆盖原版树文件**（复制整棵原树 + 改动；升级易冲突）；
  2. 用 `load_focus_tree = { tree = ... }` **换树**（会顶掉原树，适合政体切换）；
  3. 把新节点做成 **shared_focus** 并让原树 `shared_focus = ...`（仍需改原树或覆盖）。
- 给**没有专属树**的国家（用 `generic_focus`，分数 0）加一棵自己的树：只要 `modifier = { add = 10 original_tag = XXX }` 就稳定接管，这是最干净的入门做法。
- 官方原版里同 tag 的多个树（如法国 `french/vichy/free`、澳大利亚 `australian/australia_taog`）都是**互斥的候选树**，靠条件/DLC 分数或 `load_focus_tree` 切换，不是同时显示。

## 3. 最小可跑完整示例（放在 mod 里）

文件：`common/national_focus/HHO_luxembourg_industry.txt`（新文件，不覆盖任何原版；选 LUX 是因为它没有专属树，教程可稳定复现）

```pdx
focus_tree = {
	id = HHO_luxembourg_rebuild

	country = {
		factor = 0
		modifier = {
			add = 10
			original_tag = LUX        # LUX 原版只有 generic_focus（0 分），+10 即接管
		}
	}

	initial_show_position = { x = 4 y = 0 }
	continuous_focus_position = { x = 500 y = 900 }
	default = no

	focus = {
		id = HHO_rebuild_the_steelworks
		icon = GFX_focus_generic_industry_1
		x = 0
		y = 0
		cost = 6
		search_filters = { FOCUS_FILTER_INDUSTRY }
		ai_will_do = {
			factor = 8
			modifier = {
				factor = 2
				has_war = no
			}
		}
		completion_reward = {
			add_political_power = 25
			add_ideas = HHO_steel_boom
			custom_effect_tooltip = HHO_steel_boom_tt
		}
	}

	focus = {
		id = HHO_export_or_autarky
		icon = GFX_focus_generic_currency_reforms
		prerequisite = { focus = HHO_rebuild_the_steelworks }
		x = 0
		y = 1
		cost = 6
		search_filters = { FOCUS_FILTER_INDUSTRY FOCUS_FILTER_INTERNATIONAL_TRADE }
		completion_reward = {
			country_event = { id = hho.1 days = 1 }
			# 二选一分支在事件里完成，这里只触发
		}
	}

	focus = {
		id = HHO_export_agreements
		icon = GFX_focus_generic_trade_interdiction
		prerequisite = { focus = HHO_export_or_autarky }
		mutually_exclusive = { focus = HHO_autarkic_steel }
		x = -1
		y = 0
		cost = 6
		relative_position_id = HHO_export_or_autarky
		available = {
			has_political_power > 40
		}
		search_filters = { FOCUS_FILTER_INDUSTRY }
		completion_reward = {
			add_ideas = HHO_free_trade_steel
		}
	}

	focus = {
		id = HHO_autarkic_steel
		icon = GFX_focus_generic_industry_2
		prerequisite = { focus = HHO_export_or_autarky }
		mutually_exclusive = { focus = HHO_export_agreements }
		x = 1
		y = 0
		cost = 6
		relative_position_id = HHO_export_or_autarky
		bypass = {
			has_war = yes
		}
		search_filters = { FOCUS_FILTER_INDUSTRY }
		ai_will_do = {
			factor = 5
			modifier = {
				factor = 0
				has_war = no
			}
		}
		completion_reward = {
			add_ideas = HHO_autarkic_steel
			add_stability = 0.05
		}
	}
}
```

### 需要的本地化（`localisation/english/HHO_focus_l_english.yml`，UTF-8 BOM）

```yml
l_english:
 HHO_luxembourg_rebuild:0 "Luxembourgish Reconstruction"
 HHO_rebuild_the_steelworks:0 "Rebuild the Steelworks"
 HHO_rebuild_the_steelworks_desc:0 "Our mills stand idle. Rebuild them and Luxembourg will have steel for a century."
 HHO_export_or_autarky:0 "Export or Autarky"
 HHO_export_or_autarky_desc:0 "The world buys our iron — or we keep it at home."
 HHO_export_agreements:0 "Export Agreements"
 HHO_export_agreements_desc:0 "Sign long-term contracts with the buyers of our ore."
 HHO_autarkic_steel:0 "Autarkic Steel"
 HHO_autarkic_steel_desc:0 "Steel stays within the realm; foreign buyers can wait."
 HHO_steel_boom_tt:0 "Gain §YSteel Boom§! for as long as we hold it."
```

注意：`HHO_steel_boom` / `HHO_free_trade_steel` / `HHO_autarkic_steel` 是理念 ID，还必须出现在 `common/ideas/` 且各有一条本地化（见 [ideas.md](ideas.md)）；事件 `hho.1` 见 [events.md](events.md)。**整条链的 key 必须一次补齐，否则界面上是空白。**

## 4. 共享国策树（shared focus）

共享国策 = 一个 `focus` 定义被多棵树复用。写法分两步：

**第一步**：在任意 `common/national_focus/*.txt` 的**顶层**（不在 `focus_tree` 里）定义：

```pdx
shared_focus = {
	id = HHO_nordic_defense_council
	icon = GFX_goal_generic_construct_infrastructure
	x = 10
	y = 0
	cost = 8
	offset = { x = -6 y = 0 }   # 原版 baltic_shared.txt:49-50 的写法，用于摆放偏移
	available = { is_in_faction = no }
	completion_reward = { add_ideas = HHO_nordic_council }
}
```

**第二步**：在宿主 `focus_tree` 里挂载（国内原版写法 `common/national_focus/estonia.txt:61-62`）：

```pdx
focus_tree = {
	id = HHO_luxembourg_rebuild
	# ... country 块等
	shared_focus = HHO_nordic_defense_council
}
```

要点：

- 共享国策的 `id` 同样全局唯一，**不要带国家前缀**（多个国家共用）；它的 `x/y` 是相对宿主树的坐标，`offset` 用于微调。
- 一个共享国策只能被「挂一次」到一棵树里；想给多国共用就在各自的树里各写一行 `shared_focus = <id>`。
- 共享国策里**不要**写 `country = { }`（那是树级别的）。

### 4.1 工坊实战补充（Kaiserreich 实测，2026-11-07）

KR 的国策树是全工坊最复杂的共享场景（199 个文件、77.9 万行、单树最大 2.68 万行），
四条进阶技法都有实测出处：

1. **`offset` 带 trigger 做条件位移**：共享段被多棵树引用时坐标会撞，
   KR 用 `offset = { trigger = { has_focus_tree = Mongolia_Initial } x/y }`
   （282 处，`MON focus (Mongolia).txt:974-983`）按当前树整体平移共享段
   ——这是「多树共用一段 focus 还不错位」的关键。
2. **`load_focus_tree` 三种写法**：效果块内完整形式
   `load_focus_tree = { tree = Russia_Focus keep_completed = no }`
   （RUS effects:4728）；focus 内直接换（`MON focus:951`，可
   `keep_completed = yes`）；字符串简写 `load_focus_tree = QIE_manchu`
   （QIE focus:3873）。
3. **`dynamic = yes` 国策**（KR 237 处）：同一格按在位角色/变量渲染名称与图标
   ——「政变不改树、只换人」的实现底座。
4. **三层分支协议**（游戏规则 + 隐藏 AI 事件 + flag）：
   `game_rules_country_paths.txt` 给每个国家列可选路径（玩家开局选定）；
   AI 国家由 `hidden = yes`、`trigger = { is_ai = yes }` 的事件按
   `ai_chance` 抽签并 `set_country_flag`（RUS events:43-65）；
   此后**全部 focus/事件/刷新脚本只读 flag**——玩家与 AI 走同一套协议，
   树本身保持无状态。配合 `mutually_exclusive` 做树内路线互斥
   （GER focus:111）。
5. **大树导航**：`inlay_window` 内嵌窗口 + `shortcut` 跳转分区
   （RUS focus:14-60），配合 game rule 动态给不同路线加快捷入口
   （RT56 germany.txt:44-71 同款）。

## 5. 新增文件 vs 覆盖原版

| 做法 | 结果 | 何时用 |
|---|---|---|
| 新建 `common/national_focus/HHO_xxx.txt` | 追加一棵新树（只能接管「没有专属树」的国家）或新共享国策 | 推荐，但先确认目标国家原版没有专属树（`generic_focus`） |
| 新文件里重定义一个原版 `focus` id | 覆盖该条国策（后者覆盖前者，界面位置/前置会变） | 小改动、想保留原版其他国策（仍建议实测） |
| 同名文件 `common/national_focus/germany.txt` | **整体替换**德国整棵树 38,934 行 | 极不推荐：原版一更新你就落后，且极易漏写导致别国引用断链 |

## 6. 1.19 相关变化与注意

- **`inlay_window`**：1.19 的国策内嵌窗口，需在 `common/focus_inlay_windows/` 定义 GUI 组件与按钮（`common/focus_inlay_windows/documentation.md`：`scripted_images` / `scripted_buttons` / `scripted_progressbars`）。原版用法见 `common/national_focus/germany.txt:96-99`。
- **`alternate_icon_set`**：`germany.txt:103` 的 `alternate_icon_set = FOCUS_ICON_SET_HISTORICAL_KEY_FOCUS` 让同一棵树有两套图标（需本地化 `FOCUS_ALTERNATE_ICONS` 与 `GFX_FOCUS_ALTERNATE_ICONS`，见同处注释 104-106）。
- **`shortcut` 的 `scroll_wheel_factor`**：原版注释明确「没有好办法尊重客户端分辨率」（`germany.txt:63`），别指望它精确。
- ⚠️ `reset_on_civil_war`、`day_limit`、`dynamic` 之类树级参数在本机 1.19.4.2 活动国策文件中**未被确认**，写前先 grep 一个原版用例；无法确认就不要写。
- **1.19.4 的内容改动**：1.19.3→1.19.4 的脚本改动集中在 `common/national_focus/`——10-28 批改 28 个文件、10-29 批再改 31 个国家的树（无新增/改名的官方文档，属内容与平衡调整）。若你**覆盖原版树**或依赖原版行号（本页 `germany.txt:xx` 行号按 1.19.4.2 核对，文件现有 38,934 行），换小版本后需重新 diff；自己新增文件 + 新 ID 的写法不受影响。

## 6.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/National_focus_modding）

**cost 的真实单位**：`cost = 1` = **7 点**（`NDefines.NFocus.FOCUS_POINT_DAYS = 7`），每天完成 1 点，即 cost 1 约一周。支持小数（向下取整到天）。可用 `reduce_focus_completion_cost` 效果减免。

**completion_reward 执行时国策尚未标记为完成**——块内 `has_completed_focus = <本国策>` 返回 **false**，`mark_focus_tree_layout_dirty` 也一样。三种替代：① 用国家 flag 追踪完成（设置立即生效）；② 用隐藏事件延迟执行需要查完成状态的效果；③ `load_focus_tree` 重载同一棵树强制标记完成。

**select_effect 的副作用**：使该 focus **无法手动取消**，且 focus 被取消时不会执行任何「取消效果」——所以含 select_effect 的 focus 应配 `cancel_if_invalid = no` 防止重复执行。

**allow_branch 只在树首次加载时检查**，运行时不会重新评估；`mark_focus_tree_layout_dirty` 效果可强制刷新。另外：子分支上第一个自带 allow_branch 的 focus **不继承**父分支的禁用状态——子分支首个 focus 需要复制父分支的条件。

**prerequisite 的布尔语义**：同一个 `prerequisite = { ... }` 块内的多个 focus 是 **OR**；多个 prerequisite 块之间是 **AND**。无法表达否定逻辑——复杂条件放 `available` 里用 `has_completed_focus` + `custom_trigger_tooltip`。游戏假定前置 focus 位于被依赖者的**上方**，位置错了路径生成的连线 sprite 会出错。

**互斥与 ID 重复的连带效应**：focus ID 跨树重复不仅断连线，还会破坏整个树的路径生成算法（90° 转角 sprite 出错，甚至波及无重复的其他树）并使 `has_completed_focus` / `complete_national_focus` 失效。

**shared_focus 的两个崩溃点**：树内 `shared_focus = TAG_xxx` 指向不存在的国策 → **加载主菜单时崩溃**；树中只挂了共享国策、没有自己的 focus → 也会崩溃。joint_focus（1.12+）放在通用树（generic tree）上会刷 missing scope 错误日志。

**图标发光不生效的最常见原因**：发光动画 sprite 必须与本体 sprite 同名 + `_shine` 后缀（`GFX_focus_xxx` ↔ `GFX_focus_xxx_shine`），命名不一致就不会发光。`noOfFrames = 2` 的 sprite 定义两帧都要求存在。

**树分配的时机**：`country = { factor/modifier }` 评分**在游戏开始前评估，之后基本永不刷新**（动态国家创建、debug 重载除外）。`default = yes` 全局应恰好一个树。

**ai_will_do 的算法**：AI 对每个可用 focus 取 0 ~ ai_will_do 值之间的随机小数；刚完成其前置则 ×1.5（`FOCUS_TREE_CONTINUE_FACTOR`）；再乘 AI 策略计划的 `focus_factors`；取最高者执行。**低数值被选中的概率远低于直觉**，别用 0.5 和 1 想表达「偶尔 vs 经常」。

**texturefile 路径必须用正斜杠 `/`**，反斜杠会被当转义符 → 图标全透明（不是报错）。

## 7. 常见错误 / 自检清单

- [ ] `focus_tree` 里 `id` 与任何原版树不重名；`focus` 的 `id` 与全库不重名。
- [ ] 每个 `focus` 都写了 `x` 和 `y`（或用 `relative_position_id` 明确相对谁）。
- [ ] `prerequisite` 指向的国策**存在**且在同一棵树或已挂载的共享树里。
- [ ] `mutually_exclusive` 是**双向**的（两边都写），否则只是单向禁用、UI 会怪。
- [ ] `icon` 全部是真实 sprite；不确定就用 `GFX_focus_generic_*` 系列。
- [ ] `search_filters` 只用上面列出的 16 个 token。
- [ ] 树能被目标国家拿到：`country = { factor = 0 modifier = { add = 10 tag = XXX } }`（`tag` / `original_tag` 用对国家）。
- [ ] 每条国策有 `<id>` 与 `<id>_desc` 两条本地化。
- [ ] `completion_reward` 里引用的理念/事件/科技 ID 都已存在（这是最常见的「点了没反应」）。
- [ ] 花括号平衡（本目录示例已用等量 `{` / `}` 核对）。

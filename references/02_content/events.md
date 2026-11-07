---
title: 事件与事件链（Events）
domain: 02_content
scope: country / state / global
verified_on: 1.19.4.2
verified_at: 2026-11-06
sources:
  - events/Germany.txt
  - events/ElectionEvents.txt
  - events/stability_events.txt
  - events/BBA_NewsEvents.txt
  - events/Generic.txt
  - documentation/effects_documentation.md
---

# 事件与事件链（Events）

## 1. 文件放哪 / 命名 / 原版参考

| 项 | 值 |
|---|---|
| 目录 | `events/`（原版**平铺**，无子目录；文件名自由，惯例 `TAG.txt` / `DLC_Country.txt`） |
| 扩展名 | `.txt`（不要用 `.yml`） |
| 读取时机 | 启动建库；改文件需重启 |
| namespace | 每个文件开头 `add_namespace = xxx`（可多行，见 `events/BBA_NewsEvents.txt:1-3`） |
| 事件 ID | `namespace.整数`（如 `germany.4`、`stability.3`）；**全局唯一** |
| 覆盖语义 | 同 `id` 后者覆盖前者（新文件覆盖单条原版事件）；同名文件整体替换 |
| 校验和 | 影响 |

原版必读：

- `events/Germany.txt` —— 大型内容事件：`is_triggered_only`、`option` 内的省份/国家循环、`immediate`（12,525 行）。
- `events/ElectionEvents.txt:8-80,448-507` —— `mean_time_to_happen` + `trigger` + 两个 `option` + `ai_chance`。
- `events/stability_events.txt:10-95` —— **隐藏事件** + `mean_time_to_happen` 里的 `modifier { factor }` 全套写法（最标准的「机制事件」模板）。
- `events/BBA_NewsEvents.txt:5-18` —— 最小新闻事件（`major = yes`、单 option）。
- `events/Generic.txt` —— 通用事件与 `news_event = { id = news.289 hours = 12 }` 的调用方式（第 177/210/279/349 行）。

**官方文档位置（1.19.4.2 实测）**：`events/` 下**没有** `.md`（128 个 `.txt`、无子目录），也没有事件专章。`country_event` / `news_event` / `state_event` 三个块本身是 effect，条目在 `documentation/effects_documentation.md`（`days`/`hours`/`random`/`trigger` 等参数都在那里）；`immediate` / `option` 里能写什么同样查 `effects_documentation.md` 与 `triggers_documentation.md`。
因此事件域只有「vanilla 实例 + effects/triggers 文档」两个事实来源，**没有域级 `_documentation.md`**，抄原版事件是最快的路径。

## 2. 事件类型与可用字段

```pdx
# 一、国家事件（最常用）
country_event = {
	id = hho.1                    # 必填，namespace.数字
	title = hho.1.t               # 本地化 key（叫什么名字都行，但必须存在）
	desc = hho.1.d                # 同上；原版 `.d` 与 `.desc` 两种后缀都在用（stability_events.txt:13 用 .desc）
	picture = GFX_report_event_german_speech   # 事件图 sprite

	# ---- 触发方式（二选一）----
	trigger = { ... }             # MTTH 型：何时「可能」触发
	mean_time_to_happen = {
		days = 360                # 也可 months = 12
		modifier = {              # 每个 modifier 独立相乘，见 stability_events.txt:55-95
			factor = 2.0
			has_idea = disarmed_nation
		}
	}
	# 或者：
	is_triggered_only = yes       # 只由 effect 触发（国策/决议/别的 option）

	fire_only_once = yes          # 只触发一次（MTTH 型必备，否则会反复刷）
	hidden = yes                  # 隐藏事件：不弹窗，只执行 immediate/option 效果（stability_events.txt:16）
	major = yes                   # 仅 news_event 用：大新闻（全局播报）
	# timeout = 60                # ⚠️ 本机 1.19 未在 country_event 中确认，别用

	immediate = { ... }           # 弹窗前执行（在国家作用域）

	option = {
		name = hho.1.a            # 本地化 key
		ai_chance = {             # AI 选项权重（ElectionEvents.txt:485-497）
			base = 10
			modifier = { add = 5 has_war = yes }
		}
		# 这里写 effect（国家作用域）
		add_political_power = 25
	}
	option = {
		name = hho.1.b
		ai_chance = { base = 1 }
		country_event = { id = hho.2 days = 5 }
	}

	after = { ... }               # 所有 option 执行完后运行（Germany.txt:5793 有用例）
}

# 二、新闻事件（只播报，一图一标题一选项）
news_event = {
	id = hho_news.1
	title = hho_news.1.t
	desc = hho_news.1.d
	picture = GFX_news_event_generic_panzer_attack
	major = yes
	is_triggered_only = yes
	option = { name = hho_news.1.a }   # 新闻事件通常不带效果
}

# 三、州事件（作用于 STATE 作用域）
state_event = {
	id = hho_state.1
	title = hho_state.1.t
	desc = hho_state.1.d
	picture = GFX_report_event_worker_protests
	is_triggered_only = yes
	option = { name = hho_state.1.a }
}
```

## 3. 从别处触发事件（effect 语法，来自 `documentation/effects_documentation.md`）

```pdx
country_event = {
	id = hho.3
	days = 5            # hours / days / months 可叠加
	random_days = 2     # 再加 0~(n-1) 天随机
	tooltip = hho.3.t   # 可选：指定提示用的本地化
}
news_event = { id = hho_news.1 hours = 12 }
state_event = {
	id = hho_state.1
	days = 1
	trigger_for = owner   # 可选：controller / owner / occupied ...（effects_documentation.md:8117-8120）
}
```

⚠️ 事件 ID 在 effect 里写 `id = hho.3`（不带引号）；写错 namespace（如 `hho_news.1` 但文件里 `add_namespace = hho`）→ 事件永不触发，`error.log` 里是 `unknown event` 一类报错。

## 4. 最小可跑完整示例（事件链）

文件：`events/HHO_events.txt`（新建，不覆盖原版）

```pdx
add_namespace = hho

# ---------- 1) MTTH 型：瑞典钢铁业景气 ----------
country_event = {
	id = hho.1
	title = hho.1.t
	desc = hho.1.d
	picture = GFX_report_event_worker_protests

	trigger = {
		original_tag = SWE
		has_war = no
		NOT = { has_country_flag = HHO_steel_boom_started }
	}
	mean_time_to_happen = {
		days = 300
		modifier = {
			factor = 0.5
			has_completed_focus = HHO_rebuild_the_steelworks
		}
		modifier = {
			factor = 2.0
			has_idea = HHO_autarkic_steel
		}
	}
	fire_only_once = yes

	immediate = {
		hidden_effect = {
			set_country_flag = HHO_steel_boom_started
		}
	}

	option = {
		name = hho.1.a          # 拥抱出口
		ai_chance = {
			base = 10
			modifier = {
				add = 10
				has_completed_focus = HHO_export_agreements
			}
		}
		add_political_power = 25
		add_ideas = HHO_free_trade_steel
		news_event = { id = hho_news.1 hours = 6 }
	}
	option = {
		name = hho.1.b          # 维持自给
		ai_chance = {
			base = 5
			modifier = {
				add = 20
				has_idea = HHO_autarkic_steel
			}
		}
		add_stability = 0.05
	}
}

# ---------- 2) 由国策/决议触发的分支事件 ----------
country_event = {
	id = hho.2
	title = hho.2.t
	desc = hho.2.d
	picture = GFX_report_event_fascist_gathering
	is_triggered_only = yes

	immediate = {
		# 这里的临时变量可供 option 使用
		set_temp_variable = { hho_choice = 0 }
	}

	option = {
		name = hho.2.a
		ai_chance = { base = 1 }
		set_temp_variable = { hho_choice = 1 }
		add_ideas = HHO_free_trade_steel
	}
	option = {
		name = hho.2.b
		ai_chance = { base = 1 }
		set_temp_variable = { hho_choice = 2 }
		add_ideas = HHO_autarkic_steel
	}

	after = {
		hidden_effect = {
			if = {
				limit = { check_variable = { hho_choice = 1 } }
				country_event = { id = hho.3 days = 7 }
			}
		}
	}
}

# ---------- 3) 隐藏的机制事件：只做事，不弹窗 ----------
country_event = {
	id = hho.3
	title = hho.3.t          # 隐藏事件也必须给 title/desc key（可为占位）
	desc = hho.3.d
	picture = GFX_           # 原版隐藏事件常留空 sprite（stability_events.txt:14）
	hidden = yes
	is_triggered_only = yes

	immediate = {
		add_stability = 0.02
	}
}

# ---------- 4) 新闻事件 ----------
news_event = {
	id = hho_news.1
	title = hho_news.1.t
	desc = hho_news.1.d
	picture = GFX_news_event_generic_panzer_attack
	major = yes
	is_triggered_only = yes
	option = {
		name = hho_news.1.a
	}
}

# ---------- 5) 州事件 ----------
state_event = {
	id = hho_state.1
	title = hho_state.1.t
	desc = hho_state.1.d
	picture = GFX_report_event_worker_protests
	is_triggered_only = yes
	option = {
		name = hho_state.1.a
		add_extra_state_shared_building_slots = 1   # THIS = STATE
	}
}
```

### 需要的本地化（`localisation/english/HHO_events_l_english.yml`）

```yml
l_english:
 hho.1.t:0 "Steel Orders Flood In"
 hho.1.d:0 "Foreign buyers are lining up for Swedish steel."
 hho.1.a:0 "Sell to the highest bidder."
 hho.1.b:0 "Keep the steel at home."
 hho.2.t:0 "The Steel Debate"
 hho.2.d:0 "Our industry demands a decision."
 hho.2.a:0 "Open the markets."
 hho.2.b:0 "Close the markets."
 hho.3.t:0 "Quiet Adjustments"
 hho.3.d:0 "Nothing to see here."
 hho_news.1.t:0 "Swedish Steel Boom"
 hho_news.1.d:0 "Sweden's mills run day and night."
 hho_news.1.a:0 "Remarkable."
 hho_state.1.t:0 "New Industrial District"
 hho_state.1.d:0 "A new district is ready for construction."
 hho_state.1.a:0 "Excellent."
```

> 关键点：`title`/`desc`/`option name` 的值是**普通本地化 key**，名字随便起（`hho.1.d`、`hho.1.desc` 都行），只要 yml 里存在即可。原版两种后缀并存，说明后缀不是语法。

## 5. 事件链最佳实践

1. **一条链一个 namespace，编号分段**：主线 `hho.1-99`、支线 `hho.100-199`、隐藏机制 `hho.200+`。
2. **首事件用 `is_triggered_only` + 由国策/决议触发**，后续用 `option` 里的 `country_event = { id = ... days = N }`；不要在 option 里写 `days = 0`，至少 1 天，让玩家看到「路径」。
3. **`hidden = yes` 专门放「状态机推进」**：给旗标/变量、判定条件、再派发下一个可见事件。原版 `stability_events.txt` 的 `stability.3` 就是隐藏选择器。
4. **`ai_chance` 必须写**：不写时 AI 用默认权重（历史上就是第一个 option 常被选中），很容易出现「AI 永远走同一条线」。
5. **`after` 收敛善后逻辑**：所有 option 共享的效果放 `after`，避免每个 option 复制一份。
6. **`fire_only_once = yes` 用在状态跃迁事件上**；纯机制轮询事件不要加，靠 `trigger` 的旗标控制。
7. **不要在 MTTH 事件里同时写 `is_triggered_only`**（互相矛盾，后者会让 trigger/MTTH 失效）。

### 5.1 工坊实战补充（Kaiserreich / TNO 实测，2026-11-07）

叙事量大时的四条纪律，均有实测出处：

1. **ID 段位表写进文件头**：KR 在事件文件头列出
   `# russia_events.151-200 = Chernov assassination`（RUS events:20-41），
   接手者靠注释导航。⚠️ KR 这张表实测已自相矛盾（151-200 与 120-279 重叠、
   400-319 倒序）——段位表要么配工具校验，要么必然腐烂；本插件
   `kiant_hoi4_find_duplicate_ids` 可兜底查撞号。
2. **统一日志宏**：TNO/KR 全事件埋 `log = "[GetDateText]: [Root.GetName]: event X.Y"`
   （合计 6.5 万+ 条），宏定义在 scripted_localisation
   （KR `00 - logging_scripted_localisation.txt` 的 GetLogInfo/GetLogRoot）。
   排查「事件到底触发没有」时直接 grep 游戏日志；缺点是无开关，日志体量大，
   自己的 mod 可包一层 `if = { limit = { is_debug = true } }`（MD 的
   `log = ...` 未包 is_debug 常驻 game.log，是反面教材）。
3. **单文件多 namespace 的上限**：KR RUS 单文件连续 9 个 `add_namespace`
   （RUS events:10-18），TNO America 达 28 个，单文件最大 5.7 万行
   （TNO Guangdong）。文件一巨，diff/合并/检索全线劣化——
   参照 93_ecosystem「大文件的教训」控制粒度。
4. **条件文案块**：多阵营共享的事件用
   `desc = { trigger = { <派系条件> } text = KEY }` 渲染专属正文
   （KR `00 Political events.txt:13-37`），比复制事件省一半键量。

## 6. 新增 vs 覆盖

| 做法 | 说明 |
|---|---|
| 新文件 + `add_namespace = hho` | **推荐**；绝不与原版冲突 |
| 新文件里重定义 `germany.4` | 会覆盖原版事件（加载顺序后者胜），但原版其他文件对它的引用不变 → 谨慎 |
| 同名 `events/Germany.txt` | 整体替换 12,525 行 → 禁止 |

## 7. 1.19 相关注意

- `desc` 后缀 `.d` / `.desc` 都可用（原版并存：`events/Germany.txt:12` vs `events/stability_events.txt:13`）。
- 隐藏事件在手搓机制里非常常见：`events/` 下 grep `^\thidden = yes` 命中 **183** 处（2026-11-06 本机 1.19.4.2 统计，分布在 51 个文件），这是 1.19 内容的标准做法。
- `state_event` 的 `trigger_for`（controller/owner/occupied）是较新的可选字段（`documentation/effects_documentation.md:8117+`）。
- ⚠️ 事件级 `timeout`、`fire_only_once` 之外的新字段（如 `dynamic`）未在本机确认，别照抄网络教程。
- **1.19.4 的内容改动**：10-28 批改过 36 个事件文件、10-29 批再改 17 个（无新增/改名官方文档）。若你按原版事件 ID / 行号引用（例如复制 `Germany.txt` 的 option 或覆盖单条事件），换小版本后要重新对一遍；自己新建 namespace 不受影响。

## 7.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Event_modding）

以下是官方 wiki 确认、且本机文档此前没写的机制细节：

**事件内部 ID 的生成规则**（排查「Already exists in game」必读）：

- 每个命名空间按加载顺序（ASCII 文件名顺序）分配一个基准 ID，从 **10** 开始递增，内部 ID = 基准 × 100000 + 数字 ID。
- 命名空间后的数字 ID **必须是整数且 < 100000**，否则会被截成 0——多个非整数 ID 的事件会变成同一个事件，报 `Failed to create id 12300000 50. Already exists in game`。错误消息里第二个数字：50 = 事件、54 = 国家领导人、55 = 单位领导人。
- 未声明 `add_namespace` 直接写 `id = my_event.1` → `Malformed token` 错误。

**触发时机的硬数字**：

- 自动触发事件的 `trigger` 每 **20 天**检查一次（`NDefines.NCountry.EVENT_PROCESS_OFFSET = 20`），为真后才转每日检查 MTTH。所以窄日期窗口（如 `date > 1936.1.1` 且 `date < 1936.1.3`）大概率永不触发——用 `is_triggered_only = yes` + on_startup 延迟触发代替。
- `timeout_days` 默认 **13 天**，超时自动选第一个 option。
- `ai_chance` 的有效概率**下限 1%**，低于会按 1% 执行；权重不需要总和 100；全为 0 时选第一个。

**两类静默失效**（不报错）：

1. 想自动触发却保留了 `is_triggered_only = yes` → 事件永不触发。
2. `news_event` 不写 `major = yes` → 只有一个国家收到新闻（「新闻」名存实亡）。另外 `fire_only_once` 是**全局**一次（任何国家），与 `major = yes` 并存时前者优先——两者同时写，新闻还是只发一次。

**伴随错误日志的矛盾写法**：

- `Event is triggered only, but does not have a 1 base-factor`：`is_triggered_only` 与 `mean_time_to_happen` 同时存在。
- `Event is set to trigger every day`：可自动触发 + MTTH ≤ 1 天 + 可多次触发，三条同时成立。
- `major = yes` 的 news_event 想只给部分国家看，用 `show_major = { ... }`；排除发起国用 `fire_for_sender = no`。

**scope 传递规则**（写事件链必读）：效果触发事件时，事件内 ROOT = 接收国，**FROM = 触发时所在的效果块 scope**（俗称发送者）；原 FROM 顺移为 FROM.FROM。hidden 事件延迟执行时，`immediate = { ... }` 在选项之前立即执行（对 AI 也是）。

## 8. 常见错误 / 自检清单

- [ ] 文件里有 `add_namespace = hho` 且只写一次；所有 `id = hho.N` 的 N 是整数、< 100000，且不与同 namespace 其他文件重复。
- [ ] `is_triggered_only = yes` 的事件**没有** `trigger` / `mean_time_to_happen`；反之 MTTH 事件没有 `is_triggered_only`。
- [ ] MTTH 事件有 `fire_only_once = yes` 或 trigger 中有旗标互斥，避免刷屏。
- [ ] 每个 `option` 都有 `name`，且 yml 里存在；至少一个 option（无 option 的事件不会执行任何东西）。
- [ ] `picture` 是真实 sprite（隐藏事件可用 `GFX_` 占位，原版就这么干）。
- [ ] 所有 `country_event`/`news_event`/`state_event` 的 `id` 目标事件存在。
- [ ] 事件里调用的 effect/trigger 都在 `documentation/effects_documentation.md` / `triggers_documentation.md` 里。
- [ ] 事件效果若给理念/科技/角色，那些 ID 已存在（否则静默失败）。
- [ ] yml 是 UTF-8 **带 BOM**，`l_english:` 顶格，行首 1 空格。

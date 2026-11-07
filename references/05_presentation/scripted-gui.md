---
title: 脚本化 GUI（common/scripted_guis）
domain: 05_presentation
scope: interface
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - common/scripted_guis/
  - common/scripted_guis/_documentation.md
  - interface/*.gui
  - interface/alerts.gui
  - common/decisions/categories/
---

# 脚本化 GUI：让界面出现并能点

基线 **1.19.x**。路径相对 `<GAME_DIR>` / `<PROJECT_DIR>`。

## 1. 权威文档就在游戏里

`common/scripted_guis/_documentation.md`（原版自带，实测存在）是这个系统**唯一的完整字段说明**——比 wiki 新。本文所有字段都出自它 + 原版实例。**先读它，再读本文的“落地清单”。**

文件位置：`common/scripted_guis/*.txt`（一个文件可放多个 gui；原版 17 个文件 + 1 个 `_documentation.md`）。
加载时机：启动时；改完必须重启。mod 新增文件即可，不必覆盖原版。

```pdx
# common/scripted_guis/NS_dashboard.txt
scripted_gui = {

	NS_dashboard_ui = {                  # ← 这个名字会被决策分类/外交动作引用
		context_type = decision_category
		window_name = "NS_dashboard_window"   # ← interface/*.gui 里的 containerWindowType 名
	}
}
```

## 2. `context_type` 全表（决定“显示在哪、scope 是谁”）

| `context_type` | scope | 挂到哪 | 原版用例 |
|---|---|---|---|
| `player_context` | 玩家国家 | 默认挂主窗口；可用 `parent_window_token` 改 | 无（仅文档） |
| `selected_country_context` | 被右键的国家 | 选中国家视图 | 无（仅文档） |
| `selected_state_context` | 被左键的州 | 选中州视图 | 无（仅文档） |
| `diplomacy_target_context` | 当前外交目标 | 外交窗口 | 无（仅文档） |
| **`decision_category`** | 玩家（player） | **某个决策分类**，分类里写 `scripted_gui = <gui名>` | **全部 17 个原版实例都用它** |
| `diplomatic_action` | — | scripted diplomatic action | 无（仅文档） |
| `national_focus_context` | 打开国策树的国家 | 国策视图 | 无（仅文档） |
| `country_mapicon` | 每个国家 | 地图图标 | 无（仅文档） |
| `state_mapicon` | 每个州 | 地图图标 | 无（仅文档） |

> **实践结论**：想加一个“自己的面板”，99% 走 `decision_category`。

### 挂载点：`parent_window_token` 合法 token 全表

```
top_bar  decision_tab  technology_tab  trade_tab  construction_tab  production_tab
deployment_tab  logistics_tab  diplomacy_tab  national_focus  politics_tab
selected_country_view  selected_state_view  selected_country_view_info
selected_country_view_diplomacy
army_ledger  navy_ledger  civilian_ledger  air_ledger
tech_infantry_folder  tech_support_folder  tech_armor_folder  tech_artillery_folder
tech_land_doctrine_folder  tech_naval_folder  tech_naval_doctrine_folder
tech_air_techs_folder  tech_air_doctrine_folder  tech_electronics_folder  tech_industry_folder
```

另有 `parent_window_name = "容器名"`（挂另一个 GUI 容器）、`parent_scripted_gui = "NS_other"`（挂另一个 scripted GUI）；
还能用 `map_mode = map_mode_name` 限制只在某地图模式下显示。

> **拼错不报错，只是面板不出现。** 工坊 Rt56 里就写着 `parent_window_token = topbar`（少下划线），别抄。
> `tech_*_folder` 这组 token 在 23 个工坊 mod 里**没人用过**——想在单个科技页里塞自定义面板时可用。

## 3. 窗口类型：`window_name` 只能指向 `containerWindowType`

scripted GUI 的 `window_name` 必须落在 **`containerWindowType`** 的 `name` 上，**不能是顶层 `windowType`**。
写错时常见报错：

```text
Failed to create containerWindowType for NS_main_window
```

`containerWindowType` 的正确字段：

```pdx
containerWindowType = {
    name = "NS_main_window"
    position = { x = 0 y = 0 }
    size = { width = 100%% height = 100%% }
    clipping = yes
    background = { name = "Background" quadTextureSprite = "GFX_tiled_window_2b_border" }
}
```

- `size` 的百分比必须写成 **`100%%`**（GUI 语法转义）；写 `100%` 会被解析坏。
- 子控件用 `containerWindowType` / `buttonType` / `iconType` / `instantTextBoxType`；**不要**在 scripted GUI 窗口下塞 `windowType`。
- `position` 可以是固定值或屏幕相对；`parent_window_token = top_bar` 时 `0,0` 覆盖全屏，`production_tab` 只覆盖生产页半屏。
- 元素树语法见 [gui-basics.md](gui-basics.md)。

## 4. 行为绑定：`effects` / `triggers` 的命名规则

规则（`_documentation.md` 原文）：**用元素名绑定**；`effects` 的键是 `<元素名>_click`，还可以加 `right`/`alt`/`control`/`shift` 组合，例如 `<元素名>_alt_right_click`。

```pdx
# interface/NS.gui
buttonType = {
    name = "NS_open"
    ...
}
```

```pdx
# common/scripted_guis/NS_gui.txt
scripted_gui = {
    NS_buttons = {
        context_type = player_context
        window_name = "NS_buttons_window"
        parent_window_token = top_bar
        effects = {
            NS_open_click = { set_country_flag = NS_open }   # 必须正好是按钮名 + _click
        }
    }
}
```

⚠️ **最常见的静默失败**：如果按钮本身就叫 `NS_open_click`，引擎会去找 `NS_open_click_click`，于是**点击完全无反应，`error.log` 通常也不报**。
关闭按钮同理：`name = "close_button"` → `close_button_click`。

完整示例（含 `_enabled` / `_visible` / 右键变体）：

```pdx
scripted_gui = {
	NS_dashboard_ui = {
		context_type = decision_category
		window_name = "NS_dashboard_window"

		visible = { has_country_flag = NS_dashboard_open }        # 面板本身是否显示（scope = player）

		effects = {
			NS_dashboard_boost_click = {
				add_political_power = 25
				add_to_variable = { NS_boost_count = 1 }
			}
			NS_dashboard_boost_right_click = {                   # 右键同按钮
				add_stability = -0.02
			}
		}

		triggers = {
			NS_dashboard_boost_click_enabled = {                 # 为假 → 变灰不可点
				check_variable = { NS_boost_count < 5 }
			}
			NS_dashboard_value_visible = {                       # 为假 → 元素隐藏
				check_variable = { NS_boost_count > 0 }
			}
		}
	}
}
```

- `effects` 内的脚本执行 scope = `context_type` 决定的 scope（`decision_category` 下就是玩家国家）。
- 原版实例的 `effects` 极简（多数只做 `properties` 与 `visible`，效果交给决策本身执行），但字段完整支持。
- 元素名**区分大小写**，字段名不区分。

常用显示互斥：

```pdx
# 主窗
visible = { has_country_flag = NS_open }
# 入口按钮：常驻。不要写 visible = { NOT = { has_country_flag = NS_open } }
# 否则面板关掉后再也点不开；关闭依靠 close_button_click 清 flag
```

## 5. 动态内容：`properties` / `dynamic_lists` / `dirty`

### 5.1 `properties`：改图、改帧、改坐标

```pdx
properties = {
	NS_dashboard_icon = {          # 元素名（iconType）
		image = "[NS_GET_ICON_NAME]"  # 支持脚本化本地化/变量求出的 sprite 名
		frame = 2                     # 多帧 sprite 的第几帧，也可以是变量
	}
	NS_dashboard_icon_wrap = {
		x = 100                       # 直接改坐标
		y = 40
	}
}
```

原版两种写法都出现过：
- `frame = SOV_paranoia_photo_zinovyev`（变量名，`SOV_paranoia_system_scripted_gui.txt:8-10`）
- `frame = SOV_paranoia_generic_portraits_array^3`（数组第 3 个元素，同文件 `:36-38`）
- `image = "[INS_GET_WAR_ESCALATION_LEVEL_1_COLOR]"`（脚本化本地化返回 sprite 名，`INS_revolution_scripted_gui.txt:8-10`）

`image` 必须是 **sprite 名**（`GFX_...`），不是文件路径。

### 5.2 `dynamic_lists`：用数组批量生成元素

```pdx
# 1) 纯展示
dynamic_lists = {
	list = { array = my_array entry_container = "entry_template" }
}

# 2) 带索引/值：effects 里天然可用
dynamic_lists = {
	list = {
		array = my_array
		index = my_index          # 当前下标存到 my_index
		value = my_value          # 循环内当前值存到 my_value（文档默认名是 v）
		entry_container = "entry_template"
	}
}
effects = {
	entry_click = { set_variable = { selected = my_value } }
}

# 3) 列表套列表（MD 顶栏货币菜单）
dynamic_lists = { list = { array = "topbar_menu@var:topbar_i" entry_container = "..." } }
```

- 数组用 `add_to_array = { my_array = X }` 构建；列表本身不刷新，**改完数据要 bump `dirty`**。
- 模板里的子控件靠 `properties { icon = ... name = ... }` 绑定到数组元素字段。
- `country_scope_entry_container` 用于「按国家而不是按玩家」渲染（文档还列了 `state_scope_entry_container`；文档那一行写重复了，本机无原版用例，属未验证区）。
- `change_scope = yes` 可把 scope 切到数组元素。

### 5.3 `dirty`：唯一需要关心的性能开关

> 文档原文：**默认每个 tick 都刷新**；给 `dirty = 变量名` 后，只有该变量变化时才刷新。

```pdx
dirty = NS_dashboard_version
```
配合 `add_to_variable = { NS_dashboard_version = 1 }` 强制下一次刷新。

三种用法：`dirty = <player 变量>`（本国）、`dirty = ROOT`（整个根）、`dirty = global.<变量>`（所有国家，MD 顶栏用这种）。

## 6. 开合与刷新：三条硬事实

1. **`should_be_open` 不存在**（TNO/MD 全局零命中）。开合一律国家 flag/变量 + `visible`。
2. **脚本窗口之间没有自动互斥**。要「开 A 关 B」，A 的 open effect 里必须 `clr_country_flag = B_open`。原生窗口之间的互斥由引擎管，脚本窗口没有。
3. **`dirty` 不写 = 每 tick 重绘**。数据变了才 `add_to_variable = { var = ui_NS value = 1 }` bump，scripted gui 里写 `dirty = ui_NS`。

## 7. 完整落地清单：新增一个“真的会显示”的面板

四个文件 + 一个必须满足的挂载条件。全部用 `NS_` 前缀，避免与原版冲突。

### ① `interface/NS_dashboard.gui` —— 长什么样
见 [gui-basics.md](gui-basics.md) §7（`containerWindowType` 名必须是 `NS_dashboard_window`）。

### ② `common/scripted_guis/NS_dashboard.txt` —— 谁能看、点了做什么

```pdx
scripted_gui = {
	NS_dashboard_ui = {
		context_type = decision_category
		window_name = "NS_dashboard_window"

		visible = { always = yes }

		effects = {
			NS_dashboard_boost_click = {
				add_political_power = 25
			}
		}
	}
}
```

### ③ `common/decisions/NS_dashboard_decisions.txt` —— 挂载点（分类里写 scripted_gui）

```pdx
NS_dashboard_category = {
	priority = 200
	icon = GFX_decision_category_generic
	allowed = { always = yes }
	visible = { always = yes }

	scripted_gui = NS_dashboard_ui          # ← 关键一行：把面板挂到这个分类

	NS_dashboard_do_nothing = {             # 分类里最好放至少 1 个决策，否则界面可能只有空白区
		icon = GFX_decision_category_generic
		cost = 0
		available = { always = yes }
		complete_effect = { }
		ai_will_do = { base = 0 }
	}
}
```

> 决策/分类字段的完整说明在 [../02_content/decisions.md](../02_content/decisions.md)；这里只保证“挂载链”成立。原版同构证据：`common/decisions/categories/SOV_decision_categories.txt:13`（`scripted_gui = sov_paranoia_system_ui`）。

### ④ `localisation/simp_chinese/NS_dashboard_l_simp_chinese.yml`（+ english）—— 文字

```yml
l_simp_chinese:
 NS_dashboard_category: "我的面板"
 NS_dashboard_category_desc: "演示用的脚本化界面。"
 NS_dashboard_title: "国家发展面板"
 NS_dashboard_value_text: "已提升次数：§Y[?NS_boost_count]§!"
 NS_dashboard_boost: "提振民心"
 NS_dashboard_boost_tt: "花费 0 政治点数，获得 §G25§! 政治点数。"
 NS_dashboard_do_nothing: "什么也不做"
 NS_dashboard_do_nothing_desc: "占位决策。"
```

变量侧：在 `on_actions`/开局事件里 `set_variable = { NS_boost_count = 0 }`，否则 `[?NS_boost_count]` 显示空。

### ⑤ 生效判定（排查顺序）

1. 决策分类出现在「决议」页且能看到面板区域 → 挂载成功。
2. 面板区域空白 → `window_name` 与 `.gui` 容器名不一致。
3. 面板在但按钮不响应 → `effects` 键名与按钮 `name` 不一致（少了 / 多了 `_click`）。
4. 文字是 key 名 → yml 没 BOM / 文件名没带 `_l_simp_chinese` / key 拼错。
5. 汉字是 `????` → 字体名没中文分片，见 [fonts-cjk.md](fonts-cjk.md)。
6. 全都没有 → 分类 `visible`/`allowed` 为假，或决策分类 `priority` 被别的分类抢先。

## 8. 刷新机制与性能

| 机制 | 开销 | 建议 |
|---|---|---|
| 默认每 tick 刷新全部 `properties`/`triggers`/`visible` | 高：每个 tick × 每个打开的面板 × 每个表达式 | 面板一多就是掉帧元凶 |
| `dirty = 变量` | 仅变量变化时刷新 | **只要面板有动态内容就一定要写** |
| `visible` 为假 | 元素不显示，但表达式仍会求值 | 用 `dirty` 一起控制 |
| `map_mode = xxx` | 只在指定地图模式加载 | 地图类面板必加 |
| `dynamic_lists` | 每次刷新重建条目 | 数组别太长；条目容器要轻 |

经验值：一个面板 10 个 `properties` + 20 个 `triggers`，不开 `dirty` 时每 tick 都要跑 30 个脚本块；4 个这样的面板就足以在低端机看到卡顿。

## 9. 想「像原生窗口那样自动关闭」：先认清限制

用户常要求“打开军械部门时，其他部门窗口自动关闭”。这属于**原生窗口管理器**行为：

- 军官团、情报机构、生产页等是引擎原生窗口；互相打开时会自动关闭同组窗口。
- scripted GUI 窗口**不是**原生窗口：没有 `is_window_open` 触发器，也没有“窗口打开”on_action。
- 因此 scripted GUI **无法监听其他窗口打开并自动关闭自己**；只能：
  - 手动关闭按钮 / ESC；
  - 或改用原生窗口（但 mod 不能新增原生窗口类型）。

同理，复制 `countryofficercorpview.gui` 只能得到 `Placeholder` 外壳；顾问、司令官、精神、特种部队由引擎按原生窗口名动态填充，**不会**因为复制 GUI 就出现。要做独立部门必须自建数组、`dynamic_lists` 和 click effects——这是“重建”，不是“复制”。

### 唯一能“像原生一样自动关闭”的路：覆盖原生窗口的 `.gui`

**覆盖原生窗口的 `.gui`，在它内部塞自己的内容。** 外壳是原生窗口，关闭/互斥由原生窗口管理器负责。

TNO 的三层 tab 做法：

1. 覆盖 `interface/powerbalanceview.gui`，保留原生容器与关闭按钮；
2. 容器里放 `gridboxtype`，`dynamic_lists` 生成 tab 头：`properties tab = { frame = TNO_BoP_Tabs_Frames^Tab_i }`；
3. 点 tab 只改 `set_variable = { TNO_BoP_SelectedTab = Tab_v }`；
4. 每个 tab 内容 `visible = { check_variable = { TNO_BoP_SelectedTab = token:XXX } }`。

省资源变体（TNO 英国面板 `TNO_Britain_GUIs.txt:112-118`）：
`entry_container = "[BRI_Workshop_GetTabGUI]"`——脚本本地化返回容器名，1×1 gridbox 只实例化当前 tab。

**限制**：只能覆盖**已存在**的原生窗口；不能凭空造新的原生窗口类型；整份覆盖会在原版更新时冲突。

### 遮罩 / 全屏的取舍

| 方案 | 效果 | 代价 |
|---|---|---|
| `parent_window_token = production_tab` + `100%%` | 页面嵌在生产页左半屏 | production_tab 只有半屏，页面很小 |
| `parent_window_token = top_bar` + `100%%` | 真正全屏，可盖住生产页 | 需要 `clipping=yes`；顶栏/国旗可能被盖，需下移或单独处理 |
| top_bar 全屏 + 自绘遮罩（如 `HTE_overlay`） | 视觉上让生产页消失 | 遮罩盖国旗/顶栏；不是真关闭；ESC 仍需自己处理 |
| 原生窗口 | 自动关闭、数据完整 | mod 不能新增原生窗口 |

如果用户要求“打开后生产页消失”，优先做 **top_bar 全屏页面**，不要把 `windowType` 当全屏子窗。

## 10. 顶栏按钮：三种挂法

| 做法 | 例子 | 适用 |
|---|---|---|
| 独立容器 + `parent_window_token = top_bar` + 负坐标/orientation | TNO `TNO_bottom_gui`（95×95，`-83,-379`，`lower_right`） | 最常用；每按钮独立 `_visible`/`_click` |
| **窗口本身即顶栏元素**（无 parent，固定坐标） | East Showdown `top_bar_scripted_gui.txt:36-39` `energetics`（`x=692 y=2`） | 不随 top_bar 布局漂移，但要自己维护坐标 |
| 挂原生锚点容器 | KR `interface/topbar.gui:871` 的 `after_intel_agency_button` | 多按钮共用锚点，最不易撞车 |

弹窗**不要**挂 `top_bar` 再指望不挡顶栏；TFR 专门写 `#parent_window_token = top_bar` 把它注释掉。

### 顶栏新增按钮的底图配套（否则按钮悬在地图上）

原版顶栏底图 `GFX_topbar_background_extended` 是固定 2346×87，左侧按钮底板只到军官团附近。
新增按钮放在 `x=680 y=36` 时，按钮会悬在地图/生产页上。**不要**用 `GFX_tiled_generic_bg_1` 直接补一块——色差和边缘会像黑框。

推荐做法：

1. 从原版 `background_extended.dds` 裁 **底板主体 + 右端斜角/铆钉**；
2. 生成一张独立 `gfx/interface/topbar/NS_patch.dds`（例：230×62），用 `iconType` 叠在 `topbar` 的 `x=560 y=22`；
3. 同时右移信息栏，避免新按钮压住指挥点/经验：

```text
cp    732 -> 792
land  796 -> 856
navy  854 -> 914
air   912 -> 972
nukes 970 -> 1030
```

4. 覆盖 `interface/alerts.gui`：`alerticon_startposition 662 -> 735`、`alerticon_extended_startposition 718 -> 791`，否则警报层会压住新按钮。
5. 补块右侧保留原版斜角，否则用户会看到“底图边缘不圆滑”。

不要直接拉伸整张 2346×87 底图：顶部信息条、左右圆角和斜边都会变形。

## 11. AI 相关字段（可选，交互型 GUI 才需要）

```pdx
ai_enabled = { always = yes }     # 只检查一次；false 则 AI 整局忽略此 GUI
ai_test_interval = 24             # 检查间隔（小时）
ai_test_variance = 24
ai_check = { always = yes }       # 每个 tick 对每个 AI 检查
ai_test_scopes = test_self_country   # targeted 类 GUI 才需要，可多个
ai_check_scope = { always = yes }    # 对每个目标检查
ai_weights = {
	NS_dashboard_boost_click = {
		ai_will_do = { base = 10 }
		weight = 50
		ignore_lower_weights = yes
	}
}
ai_max_weight_taken_per_test = 100
```

`ai_test_scopes` 合法值（文档原文）：`test_self_country, test_enemy_countries, test_ally_countries, test_neighbouring_countries, test_neighbouring_ally_countries, test_neighbouring_enemy_countries, test_self_owned_states, test_enemy_owned_states, test_ally_owned_states, test_self_controlled_states, test_enemy_controlled_states, test_ally_controlled_states, test_neighbouring_states, test_neighbouring_enemy_states, test_neighbouring_ally_states, test_our_neighbouring_states, test_our_neighbouring_states_against_allies, test_our_neighbouring_states_against_enemies, test_contesded_states, test_if_only_major, test_if_only_coastal`（原文 `test_contesded_states` 就是拼错的，照抄无妨）。

`_documentation.md` 里还有 `parent_window_name` / `parent_scripted_gui` / `map_mode` / `properties` / `dynamic_lists` 等字段的完整说明，以它为准。

## 12. 常见错误 / 自检清单

- [ ] `scripted_gui = { <名字> = { ... } }` 外壳不能少，`<名字>` 与决策分类里的 `scripted_gui =` 完全一致。
- [ ] `window_name` 指向 **`containerWindowType`**（不是顶层 `windowType`）的 `name`，且全局唯一。
- [ ] `size` 百分比写 `100%%`（双百分号）。
- [ ] `effects` 键 = 元素名 + `_click`（按钮名本身**不要**再带 `_click`）；`triggers` 键 = 元素名 + `_click_enabled` 或 `_visible`。
- [ ] 所有 UI 元素名没写错大小写（元素名**区分大小写**，字段名不区分）。
- [ ] `parent_window_token` 拼写与 `size/position` 匹配（top_bar 全屏 / production_tab 半屏）。
- [ ] 顶栏补块使用原版斜角，信息栏与 `alerts.gui` 已右移。
- [ ] 面板有动态内容 → 写 `dirty`；开 A 关 B → A 的 effect 里 `clr_country_flag = B_open`。
- [ ] `properties` 里 `image` 必须是 sprite 名（`GFX_...`），不是文件路径。
- [ ] 本地化 yml 有 BOM、无裸换行、无重复 key。
- [ ] `font_audit.py` 退出码 0（字体名都有中文分片，见 [fonts-cjk.md](fonts-cjk.md)）。
- [ ] 修改后重启游戏；`-debug_mode` 下 `logs/error.log` 搜 `scripted gui` / `window_name` / `Failed to create containerWindowType`。
- [ ] 若用 `decision_category` 挂载：分类必须在决议页可见（`allowed`/`visible` 都为真，且 `priority` 别被挤没）。
- [ ] 明确告知用户：scripted GUI **不能**自动关闭，除非改用原生窗口（覆盖原生 `.gui`）。

## 13. 头部项目的实战模式（TNO / Millennium Dawn 工坊实测，2026-11-07）

以下是工坊 GUI 量最大的两个 mod（TNO：133 个 scripted_gui / 373 个 .gui；
MD：52 个 scripted_gui / 288 个 .gui）在真实规模下验证过的模式，
每条都有出处可回查。

### 13.1 多窗口共享一个刷新：全局计数器 dirty（MD）

`dirty` 只认一个变量，多个面板要同帧刷新时，用一个**全局计数器**当脏标记：

```pdx
# common/scripted_guis/00_MD_economyview_scripted_guis.txt:232-238
dirty = global.update_monie_ui
# 任何经济变动处（00_money_system.txt:274-283）：
add_to_variable = { global.update_monie_ui = 1 }   # 计数器自增即全员失效重绘
```

配套约定：AI 不刷 UI——所有 UI 刷新 effect 包 `limit = { is_ai = no }`
（00_money_system.txt:257-260），AI 国跑同样的记账但不付 GUI 成本。

### 13.2 全屏事件面板 = 关屏藏窗 + 变量即状态（TNO super event）

TNO 的全屏「超级事件」根本不是 event，是 scripted_gui：

- 窗口 `show_position = { x = 0 y = -6000 }` 藏在屏幕外，显示时归中
  （`interface/TNO_SG_Super_Event.gui:8-13`），`moveable = yes`。
- 显示条件 `has_variable = TNO_super_event`，图/题/文全部走 scripted_localisation
  动态拼名：`localization_key = "GFX_[?TNO_super_event.GetTokenKey]"`
  （TNO_Super_Events_scripted_loc.txt:30）——**92 张事件图只靠一个 token 变量切换**。
- 想做全屏剧情演出，这套「变量即状态、GUI 即视图」可直接移植，
  代价是事件日志/存档兼容要自己管。

### 13.3 布局取舍：平铺窗口，不做深嵌套（TNO）

TNO 最大的自建面板 `TNO_SG_Politics.gui`（2,914 行、63 窗口）最大嵌套深度
只有 6 层；9,165 行的经济视图靠 269 个**平铺** containerWindowType 组成。
例外只有一个：直接覆盖原版 `TNO_countryeconomyview.gui` 时跟随原版结构到 9 层。
**新面板学 TNO：宽度换深度**，嵌套一深，锚点/对齐就不可维护。

### 13.4 不用 dynamicIcons 也能活：properties.frame 切帧（TNO）

TNO 全库 **0 处** dynamicIcons/dynamicTexts——全部走「静态元素 +
`properties` 逐元素控制」：`electricity_toggle_button = { frame = TNO_lights }`
（TNO_economy.txt:57-59）用变量切多帧 sprite。老引擎兼容优先时这是
合法路线；新面板若目标 1.12+，dynamicIcons 仍更省脚本。

### 13.5 parent_window_token 用量分布（选挂点的参照）

TNO 全库 148 处注入实测分布：`top_bar`×25、`politics_tab`×29、
`decision_tab`×19、`trade_tab`×12；MD 侧 `politics_tab`×11、
`selected_state_view`×8、`trade_tab`×7、`top_bar`×5。
`context_type` 方面 TNO：`player_context`×267、`decision_category`×118、
`selected_state_context`×8——**把面板挂进决议页（decision_category）是
仅次于顶栏的常用入口**，比自建按钮入口省一个图标位。

### 13.6 工程约定（直接可抄）

- **每个 scripted_guis 文件头部维护目录注释**，并分 Deprecated/Unused 节
  （TNO_economy.txt:1-29，"Please maintain this listing for ease of use"）。
- **借用第三方 GUI 框架在文件头署名**（TNO_countryeconomyview.gui:1-2，
  "Credit to Yard1 for Pie Chart Framework"）。
- **GUI 挂不了的功能走 on_actions 替代**：MD 的
  `common/scripted_guis/README.md:5-28` 明文规定 AI 无 GUI 交互时必须给
  on_actions 等价路径，并列出原版主界面中 dirty 失效的 parent_window_token 清单
  （politics_tab/trade_tab 等 10 个）——**挂进原版 tab 的面板不要指望 dirty 生效**。
- **地图型 GUI 独立成目录**（TNO：`interface/brazil_gui/` + 同名 scripted_gui），
  别和常规面板混放。

### 13.7 TFR 补充（2026-11-07）：加载序与注入件

- **文件名前缀控加载序**：`TFR_scripted_guis_ZZZ_economy.txt` 用 `ZZZ_` 保证
  自己的 GUI 定义最后加载（同 mod 的 KR `zz_on_actions_models_warning.txt`
  同款手法，跨 common 目录通用）。
- **顶栏小组件**：金钱/债务部件直接
  `parent_window_token = top_bar` 注入原版顶栏
  （`money_top_bar_resource.txt:5-26`），可见性用
  `has_country_flag = TFR_money_element_small` 在紧凑/完整两态间切换。
- **决议页嵌状态条**：`context_type = decision_category` 把战争升级条嵌进
  决议分类页（`war_escalation_scripted_gui.txt:3-5`），图标颜色经
  `properties + image = "[GET_WAR_ESCALATION_LEVEL_x_COLOR]"` 交给
  scripted_loc 换图——「properties.image 接 scripted_loc 函数」是
  动态换图的标准写法之一。
- **开局说明菜单**：`visible = { is_ai = no  check_variable = { show_up = 0 } }`
  + 每页签一组 triggers/effects 变量开关（TFR_startup_menu.txt:2-52）；
  ⚠️ 该文件效果块里留着大段注释旧逻辑与 `0@` 笔误——复制粘贴型菜单
  要清理后再上架。

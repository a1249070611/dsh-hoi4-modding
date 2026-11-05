# 23 个工坊 Mod 的技法总览（HOI4 1.19.3 实测）

> 2026-11 实测：`E:\Steam\steamapps\workshop\content\394360\` 下 23 个目录，约 44 GB。
> 只读分析，未改任何 mod 文件。下面每条都带文件/行号，可直接去游戏目录复核。
> 用途：遇到「原版没这么写过」的需求时，先查这里有没有人做过。

## 1. 规模与定位

| ID | 名称 | 版本 | GUI | scripted_guis | 定位 |
|---|---|---|---|---|---|
| 2777392649 | Millennium Dawn | 2.0.3 | 288 | 51 | 现代全面改造 |
| 3350890356 | The Fire Rises | 1.0.9.1c | 161 | 32 | 现代/近未来 |
| 2438003901 | TNO | 1.10.0b | 373 | 133 | 架空叙事 |
| 1137372539 | Black ICE | 12.1.0 | 862 | 17 | 史实超精细装甲/装备 |
| 1851181613 | BlackICE TEST | 12.5.1 | 863 | 17 | 同上测试版 |
| 2948642461 | East Showdown | 0.8.0 | 100 | 28 | 现代东欧 |
| 1521695605 | Kaiserreich | 1.7 | 217 | 19 | 架空 1936 |
| 820260968 | Road to 56 | 1.19 | 31 | 17 | 延伸时间线 |
| 2129897125 | Rt56 CN | 1.17 | 31 | 17 | 汉化 |
| 3431515994 | 黑冰内核汉化 | 1.0 | 26 | 0 | 覆写原版 GUI |
| 2977114459 | 官方中文 52 字体替换 | 1.12 | 0 | 0 | 字体 |
| 2974493023 | Black Ice TEST CN | 8.1.7 | 0 | 0 | 字体 + 图标 |
| 其余 10 个 | 电台/音乐/番号/加速/汉化 | — | 0–3 | 0 | 无技法 |

**结论：GUI 量与玩法深度不成正比。** BI 862 个 GUI 是「全量覆盖 + 每个底盘一张设计器图」，
TNO 373 个 GUI 靠 133 个 scripted GUI 做叙事面板；Rt56 只有 31 个 GUI 却改了整棵科技树。

## 2. 科技树：`folder` 注册表与 gridbox 过滤器

- 统一做法：**整份替换 `common/technology_tags/00_technology.txt`**，里面
  `technology_categories = { ... }` + `technology_folders = { ... }`。
- folder 块里**唯一会被引擎使用的原版键是 `ledger = army/navy/air`**；其余
  （`available`、`picture`、`priority`）是 mod 层约定或引擎弱校验字段。
  BI 甚至加了 `available = { has_country_flag = X }` 做「某国专属页」。
- **坐标不在科技项上**，而在 folder 的
  `folder = { name = X position = { x = @COL y = @YEAR } }`。
- **`@` 宏**（BI / Rt56 都用）：

```pdx
# common/technology_tags/00_technology.txt 顶部
@1932 = 0
@1934 = 2
@1936 = 4
@CHASSIS_LIGHT1 = 14
```

改一行就重排整代科技，比逐个改 300 个科技快一个数量级。

- **「Found no grid box for tech」是特性不是 bug**：
  BI 有 2,480 个科技，`countrytechtreeview.gui` 里只有 894 个 `<techid>_tree` gridbox，
  即 **1,657 个科技根本不画**。想让某个科技出现，就声明它的 gridbox；
  不想让它出现在这页，就别声明。BI 用这个做「同一份科技数据、多套页面」。

- gridbox 必须放在**名字与 folder 完全相同**的 `containerWindowType` 里；
  一个 folder 可以有多个 root（`GER_pz1_a_tree`、`GER_pz35t_tree` 并列），
  每个无父科技的根都需要自己的 gridbox，否则该分支整条不画。

- `sub_technologies` 只用于变体小卡；`force_use_small_tech_layout` 很罕见（BI 仅 4 次）。

## 3. 装备与底盘：`duplicate_archetypes` 与前缀隔离

- **BI 不覆盖 `tank_chassis.txt`**。它用 10 个 `trm_tank_chassis_*.txt` +
  `trm_tank_variants.txt`，在 `duplicate_archetypes` 里克隆原版 archetype：

```pdx
duplicate_archetypes = {
    trm_medium_tank_chassis = {
        variant_name = { find_and_replace = { "chassis" "equipment" } }
    }
}
```

  规则：**必须在被复制的 archetype 定义之后求值**（文件加载顺序敏感）。
- **MD 用 0 字节文件抹掉原版**：`common/units/equipment/tank_chassis.txt` 放空文件，
  再在 `MD_tank_chassis.txt` 里重建全部底盘。比 `replace_path` 更干净。
- **槽位互斥不是 XOR**，是 `module_count_limit`：

```pdx
module_slots = {
    special_type_slot_1 = {
        allowed_module_categories = { addon_armor smoke endurance }
        module_count_limit = { category = addon_armor count < 2 }   # 同类只能一个
    }
}
```

- **`gui_category`**（BI 900 处）：模块同时写
  `category = trm_suspension_christie`（细，用于槽白名单）与
  `gui_category = trm_suspension`（粗，用于设计器选择器分组）。
  原版模块没有这个字段，但引擎接受。889 个细 category 被归成 142 个分组。
- **每个底盘的槽位美术**：`interface/equipmentdesigner/tanks/<chassis>.gui`，
  容器名必须是 `equipment_designer_<equipment_id>`，每槽三件套
  `<slot>` / `<slot>`（同名子容器）/ `<slot>@highlight`。
  **脚本里加了槽，美术文件里没有同名容器 → 该槽没有热区，点不了。**
  TFR 就踩了这个坑（`tank_chassis.txt:95-99` 加了 `tank_sights_module`，美术没跟上）。
- BI 把 253 个原版底盘 GUI 换成一字节桩文件（`interface/equipmentdesigner/tanks/` 共 717 个文件，
  464 真实 + 253 桩），只保留自己那批。

## 4. Scripted GUI：字段全集与生命周期

`common/scripted_guis/_documentation.md`（KR 自带）是 1.19 的**权威字段表**，比 wiki 全。

```pdx
scripted_gui = {
    NS_panel = {
        context_type = player_context          # 9 种，见下
        window_name = "NS_panel_window"
        parent_window_token = top_bar          # 或 parent_window_name / parent_scripted_gui
        dirty = ui_NS                          # 只在变量变化时重绘
        visible = { has_country_flag = NS_open }
        effects = {
            NS_open_click = { set_country_flag = NS_open }
            close_button_click = { clr_country_flag = NS_open }
            item_click = { ... }               # dynamic_lists 的 index/value 在此可用
        }
        triggers = {
            buy_button_click_enabled = { has_army_experience > 99 }
            panel_visible = { ... }
        }
        properties = { image = ... frame = ... x = ... y = ... }
        dynamic_lists = {
            list = {
                array = my_array
                value = my_value
                index = my_index
                change_scope = no
                entry_container = "entry_template"
                country_scope_entry_container = "..."
            }
        }
        ai_enabled = no
    }
}
```

### 合法 `parent_window_token` 全表（1.19）

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

> ⚠️ Rt56 里有一处 `parent_window_token = topbar`（少下划线）——拼错不报错、面板不出现。
> 正确是 `top_bar`。

### 三条硬事实

1. **`should_be_open` 不存在**（TNO/MD 全局零命中）。窗口开合一律用国家 flag / 变量 + `visible`。
2. **脚本窗口之间没有自动互斥**。要「开 A 关 B」必须自己在 A 的 open effect 里清 B 的 flag。
3. **`dirty` 默认每 tick 刷新**；不写 `dirty` 会持续重绘，卡顿。推荐
   `add_to_variable = { var = ui_NS value = 1 }` 触发，`dirty = ui_NS`。

### `dynamic_lists` 的三种用量

```pdx
# 1) 简单列表：数组 + 模板
dynamic_lists = { list = { array = my_array entry_container = "entry" } }

# 2) 带索引/值：点击读 index
dynamic_lists = { list = { array = my_array index = my_i value = my_v entry_container = "entry" } }
effects = { entry_click = { my_array = { ... } } }

# 3) 列表套列表（MD 顶栏货币）
dynamic_lists = { list = { array = "topbar_menu@var:topbar_i" entry_container = "..." } }
```

列表改动后必须 bump `dirty` 才重绘。

## 5. 原生外壳 + 脚本内容：唯一能「像原生一样自动关闭」的做法

TNO 的三层 tab 是这套做法的完整样本：

1. **覆盖原生窗口的 `.gui`**（如 `powerbalanceview.gui`），保留原生容器与关闭按钮；
2. 在容器里塞自己的 `gridboxtype`，用 `dynamic_lists` 生成 tab 头：
   `properties tab = { frame = TNO_BoP_Tabs_Frames^Tab_i }`；
3. 点 tab 只改一个变量 `set_variable = { TNO_BoP_SelectedTab = Tab_v }`；
4. 每个 tab 内容用 `visible = { check_variable = { TNO_BoP_SelectedTab = token:XXX } }`。

因为外壳是原生窗口，所以**原生窗口管理器会负责互斥与自动关闭**。

更省资源的变体（TNO 英国面板，`TNO_Britain_GUIs.txt:112-118`）：
`entry_container = "[BRI_Workshop_GetTabGUI]"`——脚本本地化返回容器名，
1×1 gridbox 只实例化当前 tab，不用把所有 tab 都画出来再隐藏。

**代价**：必须整份覆盖那个原生 `.gui`，原版更新时会冲突；且只能用于**已存在**的原生窗口，
不能凭空造一个新的原生窗口类型。

## 6. 顶栏：三种挂法

| 做法 | 例子 | 特点 |
|---|---|---|
| 独立容器 + `parent_window_token = top_bar` + 负坐标/orientation | TNO `TNO_bottom_gui`（95×95，`-83,-379`，`lower_right`） | 最常用；每个按钮独立 `_visible`/`_click` |
| **窗口本身即顶栏元素**（无 parent，固定坐标） | East Showdown `top_bar_scripted_gui.txt:36-39` 的 `energetics`（`x=692 y=2`） | 不受 top_bar 布局变动影响，但坐标要自己维护 |
| 挂原生锚点容器 | KR `interface/topbar.gui:871` 的 `after_intel_agency_button` | 多个按钮共用一个锚点，最不容易撞车 |

**不要**把弹窗挂 `top_bar` 再指望它不挡顶栏；TFR 专门写注释
`#parent_window_token = top_bar` 来屏蔽。

## 7. 性能：一条规则省一半卡顿

BI 的所有每日钩子第一行：

```pdx
on_daily = {
    if = { limit = { has_country_flag = player } }   # 只有玩家国家跑
    ...
}
```

世界级循环放在 `on_daily_ENG` / `on_monthly_GER` 这种**分国钩子**里，不要放 `on_daily`。

脉冲阶梯（BI）：

```pdx
set_global_flag = { flag = on_monthly_set value = 1 days = 2 }   # 守卫
# 用 months_since / days_since 生成 two/three/six-monthly、yearly 脉冲
```

## 8. 界面覆盖策略：只有两种

1. **整份覆盖**原版 `.gui`（BI / TNO / MD）——能改原生窗口内部，但原版更新即冲突；
2. **新增独立容器 + 挂 token**（KR / TFR / Rt56）——零冲突，但改不了原生窗口内部。

没有「局部 patch」这种机制。要留扩展点，就在自己覆盖的页面里放一个空容器：

```pdx
containerWindowType = { name = "my_research_hook" size = { width = 0 height = 0 } }
```

再用 `parent_window_name = "my_research_hook"` 挂脚本 GUI（BI 的 `research_slots_hook`）。

不想要的原版子控件，挪到 `position = { x = 9000 y = 9000 }`（BI 的「扔到平流层」写法）。

## 9. 抄什么 / 别抄什么

| 可以抄 | 别抄 |
|---|---|
| `@` 宏做科技坐标 | `parent_window_token = topbar`（拼错） |
| `module_count_limit` 限同类 | 用 XOR 思路硬凑槽位互斥 |
| `gui_category` 做选择器分组 | 只留细 category，选择器会爆长 |
| 0 字节文件抹原版 | `replace_path` 抹原版（更难排错） |
| 每日钩子 `has_country_flag = player` 门控 | 把世界循环写进 `on_daily` |
| 空容器当 hook | 靠容器名硬挂（KR 文档标注 may not work） |
| 原生外壳 + 脚本内容做 tab | 以为脚本窗口能自动关闭 |

## 10. 复核入口

| 主题 | 文件 |
|---|---|
| scripted GUI 字段全集 | `<KR>/common/scripted_guis/_documentation.md` |
| 科技树 folder/gridbox | `<BI>/common/technology_tags/00_technology.txt`、`<BI>/interface/countrytechtreeview.gui` |
| 底盘克隆 | `<BI>/common/units/equipment/trm_tank_variants.txt`、`<MD>/common/units/equipment/MD_tank_chassis.txt` |
| 设计器槽位 | `<BI>/interface/tank_designer_view.gui:161-275` |
| 原生外壳 tab | `<TNO>/interface/powerbalanceview.gui`、`<TNO>/common/scripted_guis/TNO_BoP_Tabs*.txt` |
| 顶栏锚点 | `<KR>/interface/topbar.gui:871` |
| 中文字体 | `<游戏>/interface/core_chinese.gfx`，见 `fonts-and-cjk.md` |
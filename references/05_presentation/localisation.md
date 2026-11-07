---
title: 本地化（localisation/*.yml）
domain: 05_presentation
scope: localisation
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 本地化：`localisation/*.yml`

## 1. 目录、文件名、编码（本机 2083 个文件全量实测）

| 项 | 事实 |
|---|---|
| 根目录 | `localisation/`（**任意子目录都行**，但语言由文件名与首行键共同决定，见下） |
| 语言子目录 | `english、simp_chinese、french、german、spanish、russian、polish、braz_por、japanese、korean`（`languages.yml` 列全部 10 种） |
| 总文件数 | **2083 个 yml**；其中 `english/` 207、`simp_chinese/` **208** |
| 编码 | **UTF-8 with BOM**：实测 2083 个文件 **100% 带 `EF BB BF`**，0 个例外 |
| 文件名 | 必须含 `_l_<语言>.yml`（实测全部满足；`l` 是小写 L） |
| 首行 | 必须是 `l_<语言>:`（实测全部满足：208 个 `l_english`、207 个 `l_simp_chinese`…） |
| 同键覆盖 | 同语言内重复 key 在 `logs/text.log` 里报重叠（wiki：优先原版）；**`localisation/<语言>/replace/` 目录优先级最高** ⚠️ 原版 1.19.x **没有** `replace` 目录，该特性见 [wiki](https://hoi4.paradoxwikis.com/Localisation)（抓取 2026-10-26） |
| 热重载 | 不支持，改完重启 |
| 检查命令 | 控制台 `loc_check` / `loc_check_focuses` / `loc_check_events` / `loc_check_decisions` / `loc_check_characters` / `loc_check_modifiers` / `loc_check_national_spirits`（`documentation/console_commands_documentation.md`）；忽略名单：`localisation/ignored_loc_keys.txt` |

## 2. 文件结构（照抄即可）

```yml
l_simp_chinese:
 # 单空格缩进；# 是注释行
 NS_dashboard_title: "国家发展面板"
 NS_dashboard_title_desc:0 "带版本号的写法，0 可省略，游戏不读它"
 NS_dashboard_value_text: "已提升次数：§Y[?NS_boost_count]§!"
```

硬性规则（违反 → **从出错点开始整段失效**）：

1. 首行 `l_simp_chinese:` 顶格，冒号后不能再有内容。
2. 每行 `key: "值"` 或 `key:0 "值"`；值**必须在同一行**，换行用 `\n`。
3. 引号内要写引号用 `\"`；要写 `$` 用 `$$`。
4. key 只允许 ASCII 字母、数字、下划线、点、连字符（**不能有空格/中文**）。
5. `l_simp_chinese:` 不写在文件里（或整个文件没有该行）而文件却带 BOM → **可能直接崩溃 0xC0000005** ⚠️（wiki 记录，本机未复现）。

## 3. `§` 颜色代码（原版 `interface/core.gfx:797+` 的 `textcolors` 表）

原版 `localisation/english/*.yml` 里的实际用量：`§!` 19949 次、`§Y` 12131、`§G` 2819、`§R` 2249、`§H` 1837、`§L` 391、`§T` 213、`§W` 184、`§g` 88、`§[` 13、`§O` 11。

| 代码 | 颜色 | RGB（core.gfx 原值） |
|---|---|---|
| `§!` | 结束当前颜色（**必须写**，否则溢出到后文） | — |
| `§Y` / `§H` | 黄 / “header” | 255 189 0 |
| `§W` / `§T` | 白 / “title” | 255 255 255 |
| `§G` | 绿 | 0 159 3 |
| `§R` | 红 | 255 50 50 |
| `§L` | “lilac” 脏橙灰 | 195 176 145 |
| `§O` | 橙 | 255 112 25 |
| `§C` | 青 | 35 206 255 |
| `§B` | 蓝 | 0 0 255 |
| `§b` | 黑 | 0 0 0 |
| `§g` | 灰 | 176 176 176 |
| `§0`…`§9`、`§t` | 渐变阶梯 0–10（紫→红） | 见 core.gfx 原表 |

- **可以自定义**：`interface/core.gfx` 的 `bitmapfonts = { textcolors = { ... } }` 里加/改键（键只能 1 个字符），或在某个 `bitmapfont = { ... }` 块内单独写一组 `textcolors`（原版 `core.gfx:956` 附近就是 `vic_18_black` 的专属配色）。
- **动态颜色**：`§[GetColorForCurrentIntegration]` —— `§` 后面直接跟命名空间函数，返回颜色代码。原版用例：`localisation/english/*.yml` 里有 `§[GetColorForCurrentIntegrationCap]`、`§[GetPropagandaCampaignRequirement]` 等 13 处。
- 常见报错（wiki）：`Could not find coloring for character 'M'`（非法颜色字母）、`... character id '0'`（`§` 后面什么都没有，通常是漏了 `§!`）。

## 4. `£` 行内图标

```yml
 NS_pol_power_gain: "获得 §G+50§! £pol_power"
 NS_my_icon: "自定义图标：£my_text_icon"
 NS_my_icon_frame: "取第 2 帧：£my_text_icon|1"
```

- 规则：`£name` → 引擎去找 sprite `GFX_name`（`interface/*.gfx` 里的 `spriteType`/`textSpriteType`）。
- 实测对应关系：`£pol_power`(198 次) ↔ `GFX_pol_power`（`interface/texticons.gfx:262`）；`£GFX_topbar_convoys`(41 次) ↔ `GFX_topbar_convoys`（`interface/topbar.gfx:232`）——两种写法都在原版出现，引擎兼容（⚠️ 精确匹配规则未实测）。
- **多帧文本图标必须**在 sprite 里写 `legacy_lazy_load = no`，否则图标不显示/要重载界面才显示（wiki 明确要求，原版 `texticons.gfx` 每个条目都写）。
- 常用原版图标：`£pol_power`、`£command_power`、`£army_experience`、`£navy_experience`、`£air_experience`、`£resources_strip`、`£trigger_no`、`£victory_points`、`£doctrine_mastery`。

## 5. `$变量$` 三种来源

| 形式 | 来源 | 例子 |
|---|---|---|
| `$KEY$` | 嵌套另一个本地化 key | `my_tt: "$modifier_production_speed_infrastructure_factor$: §R-10%§!"` |
| `$$` | 字面美元符号 | `cost_tt: "花费 $$100"` |
| `$NAME$`（bindable，1.15+） | 脚本绑定，用 `custom_effect_tooltip` / `custom_trigger_tooltip` 传入 | 见下 |
| `$FOCUS_NAME$` 等 | 引擎内部变量，只在特定 key 内存在 | `confirm_cancel_national_focus_desc: "取消 §H$FOCUS_NAME$§!？"` |

**bindable localisation（原版 `documentation` 未覆盖，wiki 1.15+ 特性）**：

```pdx
custom_effect_tooltip = {
	localization_key = my_bindable_tooltip
	NAME = "John"
	USRNAME = "George"
	TIME = { localization_key = COLOR_YELLOW DATA = "Morning" }   # 可递归
}
```

```yml
 my_bindable_tooltip: "Hello $NAME|Y$. I am $USRNAME$. Good $TIME$"
 COLOR_YELLOW: "§Y$DATA$§!"
```

⚠️ **`pdx_tooltip` 里的 `$KEY$` 不会展开**（wiki 明确）：GUI 的 `pdx_tooltip` 要用 `defined_text` 脚本化本地化绕开，或直接用 `custom_effect_tooltip` 那套 bindable 机制。

## 6. `[命名空间]` —— 上下文求值

语法：`[<scope>.<函数>]`；`scope` 省略时用当前上下文。

```yml
 NOR_desc: "把 [ROOT.GetName] 准备好。\n\n支持度：[?NOR.NOR_country_preparedness]/30"
 NOR_desc2: "在 [NOR.GetAdjective] 社会中……最终 [ROOT.GetNameDef] 将 [ROOT.GetNameDefCap] 崛起。"
```

原版真实行（`localisation/english/*.yml`）：

| 写法 | 含义 |
|---|---|
| `[ROOT.GetName]` | 当前作用域国家名 |
| `[NOR.GetAdjective]` | 指定 tag 的形容词（“挪威的”） |
| `[SOU.GetNameDef]` | 带定冠词形式 |
| `[ROOT.GetLeader.GetSheHe]` | 链式：领袖 → 代词 |
| `[OMA.capital.GetName]` | 变量当作 scope 用（首都州名） |
| `[123.owner.GetName]` | 州 ID → 所有者 |
| `[?NOR.NOR_country_preparedness]` | **读变量**（`?` 前缀），显示数值 |
| `[(Character?.GetName:'PROGRAM_NO_SCIENTIST_ASSIGNED)]` | 空值回退（wiki “Condition in contextual localization”） |

数值格式化（wiki，1.19 可用）：`[?var|Y]`（黄色）、`[?var|%G0]`（百分比+绿+0 位小数）、`[?modifier@my_modifier|.1%%+]`（+/- 自动红绿）。

### 命名空间“在哪里有效”这件事很重要

wiki 给的可用位置（未在本机逐项验证，⚠️ 见 [wiki/Localisation](https://hoi4.paradoxwikis.com/Localisation)）：

- 国策（标题要 `dynamic = yes` 才会刷新；描述天然动态）
- 理念与动态修正（1.13+）
- 决议、事件、操作、布尔 flag 名、海峡规则 tooltip
- `custom_effect_tooltip` / `custom_trigger_tooltip`（**自定义修正 tooltip 不支持**）
- **自定义界面元素**：容器必须挂在一个 `context_type` 有效的 scripted GUI 上

**在大多数普通 GUI 文本（国家名、战争名等）里 `[ ]` 会原样显示**——这是最常见的“为什么我的 `[GetName]` 没生效”。

## 7. Localization Formatter（`formatter|token`）

格式：`<formatter>|<token>`，可带参数。官方文档：`documentation/loc_formatter_documentation.md`（本机，8 个 formatter）：

| formatter | 取什么 | 例 |
|---|---|---|
| `advisor_desc` | 顾问描述 | `custom_effect_tooltip = advisor_desc\|hjalmar_schacht` |
| `building_state_modifier` | 建筑提供的州修正 | `custom_effect_tooltip = building_state_modifier\|dam`（支持 `INDENT`） |
| `character_name` | 角色名 | `custom_effect_tooltip = character_name\|hjalmar_schacht` |
| `country_culture` | 文化覆写名（`TAG_token` 优先） | `custom_effect_tooltip = country_culture\|generic_tank_organisation` |
| `country_leader_desc` | 领袖描述/特质（`IDEOLOGY = token:fascism` 必填） | 见文档 |
| `idea_desc` / `idea_name` | 理念描述/名字 | `custom_effect_tooltip = idea_name\|canadian_pacific_railway` |
| `tech_effect` | 科技完成效果 | `custom_effect_tooltip = tech_effect\|early_transport_plane` |

参数写法（多参数要写成块）：

```pdx
custom_effect_tooltip = {
	localization_key = country_leader_desc|hjalmar_schacht
	IDEOLOGY = token:fascism
	INDENT = 2_SPACES
}
```

## 8. Localization Objects（`documentation/loc_objects_documentation.md`）

本机文档列出 15 个对象：`Ace、Building、Character、Country、Faction、IndustrialOrg、LocalizationEnvironment、Operation、Province、PurchaseContract、Scope、SpecialProject、State、Terrain、UnitLeader`。

- 用法：`[(Object.)+Property]`，如 `[Character.GetName]`、`[Character.Owner.GetName]`。
- 还可用“Promotions”（对象直接暴露的属性），如 `Country` 的 `Capital`、`Overlord`、`FactionLeader`、`OriginalCapital`；`Country` 的 Properties 有 `GetLeader`、`GetTag`、`GetName`、`GetNameDef`、`GetAdjective`、`GetFlag`、`GetManpower`…
- 与脚本 scope 的关系：在 effect/trigger 上下文里本地化时，根对象来自当时的 scope；`FROM/THIS/PREV/ROOT` 都可用于本地化（wiki “Relation to Event Scopes”）。

## 9. 脚本化本地化（`common/scripted_localisation/*.txt`）

当 `[命名空间]` 不够用（要按条件返回**不同的 key**），用 `defined_text`：

```pdx
# common/scripted_localisation/NS_scripted_loc.txt
defined_text = {
	name = NS_GetDashboardTitle
	text = {
		trigger = { has_government = fascism }
		localization_key = NS_title_fascist
	}
	text = {
		trigger = { has_government = communism }
		localization_key = NS_title_communist
	}
	text = {
		localization_key = NS_title_default       # 兜底（无 trigger）
	}
}
```

```yml
 NS_dashboard_title: "[NS_GetDashboardTitle]"
```

原版：`common/scripted_localisation/00_scripted_localisation.txt`（文件头注释解释字段）。**注意**：`defined_text` 的 trigger 用的是**调用处作用域**，写错 scope 会静默走兜底。
（scripted localisation 的完整机制在 [../01_script/](../01_script/)；本文只讲它在界面/本地化里的用法。）

## 10. 中文落地要点

- 简体中文目录已存在：`localisation/simp_chinese/`（208 个文件）。
- 中文 yml 必须是 **UTF-8 with BOM**，且文件名含 `_l_simp_chinese`；en/zh 各一份（缺中文 → 中文界面显示 key 名）。
- 汉字字形问题（方框/`?`）**不是本地化问题**，是字体问题 → [fonts-cjk.md](fonts-cjk.md)。
- 简体中文下 `[ROOT.GetName]` 返回的是中文国名（因为读 `l_simp_chinese` 的 key），无需特殊处理。

## 11. 完整可复制模板

**覆盖原版键值不必复制整个原文件**：放进 `localisation/english/replace/` 目录（如 `localisation/english/replace/my_replace_l_english.yml`），该目录享有优先级。注意「优先级」只对这个目录成立——其他位置的键重叠**没有一致的覆盖规律**，选择哪个值要看 `logs/text.log`（重叠键会被记录在那里）。

**键重叠与版本号**：
- `key:0 "value"` 里的 `0` 是 Paradox 内部翻译追踪用的版本号，游戏完全不读、可以省略；但**只能是数字**，写连字符会报 `Expected colon(:) at line ...` 并破坏该行之后整个文件。
- 键名只允许英文字母、下划线、点、连字符、数字；空格或非拉丁字符会破坏文件剩余部分。

**一个会导致闪退的组合**：文件是 UTF-8-BOM、里面有键、但**没有**首行 `l_english:` 语言数据库声明 → 可能触发崩溃 `0xC0000005`。BOM 和语言头必须成对存在。

**颜色错误日志的解读**（`Could not find coloring for character ...`）：
- 报 `id '0'` 是特殊情况：字符串以 `§` 结尾（§ 后面什么都没有）——直接搜 `§"` 定位，通常是漏写 `§!`。
- 多字节字符（如 `§Ā`）游戏只读最后一个字节，**报出来的字符和实际写的不一致**，别按报错字符搜。

**换行与引号**：值必须严格单行，换行用 `\n`（反斜杠 + n，后面别加空格）；值内含引号用 `\"`；美元符本身用 `$$`。



```yml
l_simp_chinese:
 NS_mod_name: "我的 mod"
 NS_dashboard_title: "国家发展面板"
 NS_dashboard_value_text: "已提升次数：§Y[?NS_boost_count]§! / 5"
 NS_dashboard_boost: "提振民心"
 NS_dashboard_boost_tt: "花费 §Y0§! 政治点数，获得 §G25§! 政治点数\n当前政治点数：£pol_power §Y[?ROOT.political_power]§!"
 NS_dashboard_value_text_unused: "未使用的 key 请删掉"
```

```yml
l_english:
 NS_mod_name: "My Mod"
 NS_dashboard_title: "National Development Panel"
 NS_dashboard_value_text: "Boosts used: §Y[?NS_boost_count]§! / 5"
 NS_dashboard_boost: "Boost the People"
 NS_dashboard_boost_tt: "Costs §Y0§! political power, gain §G25§! political power\nCurrent: £pol_power §Y[?ROOT.political_power]§!"
```

## 11.5 官方 wiki 校对补充（2026-11-07 抓取自 hoi4.paradoxwikis.com/Localisation）

## 12. 常见错误 / 自检清单

- [ ] 文件是 **UTF-8 with BOM**（用十六进制看开头是 `EF BB BF`）。
- [ ] 文件名以 `_l_simp_chinese.yml` / `_l_english.yml` 结尾。
- [ ] 首行 `l_simp_chinese:` / `l_english:`，且文件里所有 key 都在该语言块下。
- [ ] 键名只含 ASCII；值单行；换行用 `\n`；引号转义 `\"`；`$` 用 `$$`。
- [ ] 每个 `§X` 都有配对的 `§!`。
- [ ] `£` 图标对应的 sprite 真实存在且写了 `legacy_lazy_load = no`（多帧）。
- [ ] `[命名空间]` 只在受支持的上下文里用（GUI 里用 → 必须挂在 scripted GUI 上）。
- [ ] `pdx_tooltip` 里不要用 `$KEY$`。
- [ ] 用控制台 `loc_check` 系列命令检查缺失；`localisation/ignored_loc_keys.txt` 可放行误报。
- [ ] 中英各一份；中文文件里不要留英文原文当占位（会漏 key）。

## 13. 汉化子模组的分层工作流（2026-11-07 工坊 6 个汉化 mod 实测）

做汉化子模组前，先判断目标 mod 的文本散布在哪几层，再决定做几层。
层越深维护越贵，能不用就不用。实测成本对照：

| 层 | 实测样本 | 体量 | 升级成本 |
|---|---|---|---|
| 1 纯 loc | KR CN | 433 yml | 上游加键才补 |
| 2 common 覆盖 | BICE 内核汉化 | 25 文件 | 上游每次更新重 diff |
| 3 字体 | 52 字体 / BICE CN | 40–53 对文件 | 游戏改字体清单才动 |
| 4 texticon | ES 汉化 | 1099 dds | 上游加图标就要补图 |

### 第 1 层：纯 loc 键覆盖（90% 文本，成本最低）

- `localisation/simp_chinese/xxx_l_simp_chinese.yml`，键名照抄上游英文文件。
- 只补简中即可：`l_english` 缺键自动回落上游英文，**不要**整包复制英文文件。
- loc 文件可直接放 `localisation/` 根——语言由 `_l_<lang>` 文件名后缀决定，
  目录只是惯例（原版 localisation/ 根就有几百个文件）。
- 覆盖个别键放 `localisation/simp_chinese/replace/`（语言混合的替换目录；
  52 字体 mod 用它修官方简中的繁体字/英文标点）。

### 第 2 层：common/ 硬编码字符串覆盖（见 EB-023）

情报机构名、AI 条件名、编制名、角色名等字面量必须**同路径覆盖 common 文件**：
先 diff 上游原文件，只改字符串、保留其余内容。BICE 内核汉化实测 25 个文件、
单文件 diff 48 行——这就是「硬编码文本的汉化税」。

### 第 3 层：字体

- 最省事：不自带字体，只保证**用中文标点、不用繁体字**，让用户装字体 mod。
- 自带时的关键技巧是**语言条件覆盖**（原版 `core_chinese.gfx` 同款手法）：

```pdx
bitmapfont_override = {
    name = "ToolTip_Font"
    fontfiles = { "gfx/fonts/garamond_16" "gfx/fonts/Arial_14" }   # 回退链
    languages = { "l_simp_chinese" }   # 只在简中时生效
}
```

- 地图字体独立一套：`mapfont_chn_0..7`（8 个 unicode 段）。地图国名/州名乱码
  查它，不是查界面字体。

### 第 4 层：图像化文本（texticon，成本最高）

文字烤进贴图的图标只能逐张替换 DDS：ES 汉化带 1099 个 `*_texticon.dds`
+ `gfx/backup/` 存原图；BICE TEST CN 带 `gfx/cn_icon/` 全套并自建
`blackice_cn_icon.gfx` 注册。工作流：grep 上游 `interface/*.gfx` 找 spriteType
→ 逐张出图 → 同名覆盖或改名注册。能推动上游改用动态文字就不要烤图。

### 收尾三件套

1. **语言探测提示**：KR 系在 `localisation/` 根放 8 个语言的
   `play_in_english_l_<lang>.yml`，非中文环境显示「请把游戏语言设为中文」。
2. descriptor 写 `tags = { "Translation" }`，说明里注明适配的上游版本号。
3. 回归：`kiant_hoi4_scan_localisation` 查 BOM/键格式；
   `kiant_hoi4_validate_mod` 确认覆盖文件没改坏上游结构。

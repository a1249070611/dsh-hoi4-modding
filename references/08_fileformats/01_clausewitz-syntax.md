---
title: "Clausewitz 语法：4892 个 .txt 文件共用的那一套规则"
domain: 08_fileformats
verified_on: 1.19.4.2
verified_at: 2026-11-06
method: 对 common/events/script/history 全量正则实测，非文档抄录
---

# Clausewitz 语法

`.txt` / `.gui` / `.gfx` / `.asset` / `.anim` / `.mesh` 全是同一个引擎的同一种语法。
学会一次，六种文件一起会。这篇按**实测数据**写，每条规则后面都给原版里的真实出现次数——
次数为 0 的写法说明引擎不支持，不要凭想象用。

## 一、只有一种结构：`键 = 值`

```clausewitz
name = GER_the_four_year_plan          # 值是裸标识符
icon = GFX_goal_generic_construct      # 值也是裸标识符
cost = 10                              # 值是数值
text = "一段话"                         # 值是字符串
available = {                          # 值是一个块
    always = yes
}
```

`common/` 下 84 万个赋值语句的真实形态分布：

| 形态 | 次数 | 说明 |
|---|---:|---|
| 值是裸标识符 | 933026 | 最多。`foo = bar`，不加引号 |
| 值是块 `{ }` | 839488 | 第二多。可以无键纯列表 |
| 值是数值 | 208185 | `cost = 10`、`factor = -0.5` |
| 值是字符串 | 24675 | 只在必须含空格/特殊字符时用 |
| 换行后跟块 | 1729 | `available =` 后换行缩进写 `{`，等价于同行 |

**没有分号，没有逗号，不用引号包标识符。** 唯一的分隔符是空白（空格、Tab、换行等价）。

## 二、注释只有 `#`

```clausewitz
# 整行注释
cost = 10   # 行尾注释，到行末为止
```

引擎不认识 `//`、`/* */`、`--`。写了会当成语法错误或莫名其妙被解析成键名。

## 三、比较运算符：只有 `>` 和 `<`

这是最容易踩的一条。全量实测（已剥离注释）：

| 写法 | 真实次数 | 能用吗 |
|---|---:|---|
| `>` | 13597 | ✅ |
| `<` | 6877 | ✅ |
| `<=` | **0** | ❌ 引擎不支持 |
| `>=` | **0** | ❌ |
| `==` | **0** | ❌ 等于是不写运算符 |
| `!=` | **0** | ❌ 取反用 `NOT = { }` |

```clausewitz
# 原版写法（common/achievements.txt:14）
difficulty > 1
has_start_date < 1936.01.02

# 想表达 >= 只能写成这样
NOT = { difficulty < 2 }

# 想表达 != 只能写成这样
NOT = { has_government = democratic }
```

> **为什么这条重要**：很多教程教你写 `x >= 5`，引擎不会报错，而是**静默忽略整条触发器**。
> 结果就是「条件明明写了却不生效」，排查半天找不到原因。`NOT` 才是官方的取反手段。

## 四、块可以无名

同一个 `{ }`，有键时是「字典」，无键时是「列表」。靠位置和上下文区分：

```clausewitz
# 有键：字典
modifier = {
    army_attack_factor = 0.1
}

# 无键：列表（多个值堆在一个块里）
add_core_states = { 1 2 3 4 }
countries = { GER FRA SOV }
```

列表项之间**不加任何符号**，纯空格分隔。`{ GER FRA SOV }` 和下面等价：

```clausewitz
countries = {
    GER
    FRA
    SOV
}
```

### 同一个键，值可能是标量，也可能是块

写脚本时最容易忽略的一点：**很多字段同时接受「一个值」和「一个条件块」**，
引擎按块内的 `trigger` 挑一个用。

```clausewitz
# 标量：唯一的图标
icon = GFX_focus_foo

# 条件块：按条件换图标（原版 44 个国策这么写）
icon = {
    GFX_focus_democratic = { has_government = democratic }
    GFX_focus_generic   = yes
}

# 决议的写法不同：sprite 名写在 key 里（原版 66 个决议这么写）
icon = { key = GFX_decision_foo trigger = { original_tag = USA } }

# 事件正文可以重复多个块，每个变体一个 text 键（原版 214 处）
desc = { text = my_event.1.desc_den trigger = { tag = DEN } }
desc = { text = my_event.1.desc_gen trigger = { always = yes } }
```

原版实测（1.19.4.2）：

| 字段 | 标量 | 条件块 |
|---|---|---|
| event `desc` | 6629 | 214 |
| event `title` | 6826 | 18 |
| focus `icon` | 10297 | 44 |
| decision `icon` | 3654 | 66 |

**写的时候两条规矩：**

1. **块里最后一个分支用 `= yes`（或 `always = yes`）兜底。** 所有 `trigger`
   都不成立时游戏会退回默认图标/空正文，界面上不会报错，只是"莫名其妙不显示"。
2. **`key =` 结构和"sprite 名当键"结构不能混用。** 国策用后者，决议用前者；
   写反了游戏读不到 sprite，显示为空白或粉黑方块。

**解析的时候**（自己写工具时）：`as_text()` 这类"只认标量"的取值函数，
遇块会返回空串——**空串不等于没写**，必须单独判断。漏了这一点会同时造成
误报（块里的键被当成不存在）和漏检（块里的 sprite 引用根本没进检查）。
详见 `99_plugin-devlog/DEVB-026-value-may-be-block.md`。

## 五、`@` 变量：文件级常量

`@name = 值` 在文件顶部定义，整文件内可用。**不跨文件**。

```clausewitz
# common/country_leader/00_traits.txt:1  （注意：不是 common/ideas/，
# 原版有 3 个同名 00_traits.txt，只有这个开头就是 @变量定义）
@tier1_cp_cap_increase = 10
@tier2_cp_cap_increase = 20

# 后面就能用
command_power = @tier1_cp_cap_increase
```

全库共 186 处 `@` 定义、4330 处引用。作用域是**单文件**，改的时候注意别在别的文件里引用。

## 六、`scope:目标` 前缀：10 种

游戏里没有 `$占位符$` 这种写法（全库实测 **0 次**）。真正做「指到别处去」的是前缀体系：

| 前缀 | common/ 内次数 | 作用 |
|---|---:|---|
| `var:` | 1285 | 引用变量值 |
| `event_target:` | 706 | 引用事件链里存下的目标 |
| `mio:` | 602 | 指向军工组织 |
| `game:` | 396 | 指到全局（`game:all_states`、`game:scope`） |
| `constant:` | 232 | 引用 `common/script_constants/` 里的常量 |
| `sp:` | 186 | 指向特殊项目 |
| `collection:` | 125 | 指向脚本集合 |
| `token:` | 24 | 令牌替换 |
| `scope:` | 4 | 显式 scope 引用 |
| `temp_var:` | 3 | 临时变量 |

```clausewitz
# 真实用法
add_opinion = { target = event_target:WTT_china_incident modifier = ... }
set_temp_variable = { temp_var:x = 1 }
```

## 七、日期是特殊类型

不带引号，用点分隔，引擎会自动认成日期：

```clausewitz
date > 1947.12.31
has_start_date < 1936.01.02
```

写成 `"1947.12.31"`（带引号）会被当字符串，比较行为未定义。**这是静默错误**。

## 八、数值可以带表达式

简单四则运算在数值位置直接写：

```clausewitz
factor = 0.5
add = -10
value = 2.5
```

原版里 `value = [ ... ]` 这种内联 math 块是 **0 处**——那是别的 P 社游戏的写法，HOI4 不用。

## 九、一条完整的真实国策（`germany.txt:1679`，原样摘录）

```clausewitz
focus = {
    id = GER_the_four_year_plan
    icon = GFX_focus_GER_the_four_year_plan              # 图标在 interface/*.gfx 注册 → 指向一张 dds
    alternate_icon = GFX_focus_GER_the_four_year_plan_historical

    mutually_exclusive = { focus = GER_prioritize_economic_growth }   # 互斥，二选一
    x = 6                                                 # 格子坐标，从 0 开始
    y = 0
    relative_position_id = GER_prioritize_economic_growth # ★ 坐标相对于谁
    cost = 5                                              # 天数，不是政治点
    available = { }                                       # 空块 = 无条件可点

    search_filters = { FOCUS_FILTER_RESEARCH FOCUS_FILTER_INDUSTRY FOCUS_FILTER_HISTORICAL }

    completion_reward = {
        every_core_state = {
            limit = {
                is_fully_controlled_by = ROOT
                free_building_slots = {
                    building = industrial_complex
                    size > 0                              # ★ 只能写 > ，不能写 >=
                    include_locked = yes
                }
            }
            random_select_amount = 2
            add_extra_state_shared_building_slots = 1
            add_building_construction = {
                type = industrial_complex
                level = 1
                instant_build = yes
            }
        }
        custom_effect_tooltip = generic_skip_one_line_tt   # 在提示框里插一个空行
        add_tech_bonus = {
            name = GER_the_four_year_plan                  # ★ 这个名字会在 localisation 里查词条
            bonus = 1
            uses = 1
            category = industry
        }
    }
}
```

### `relative_position_id` 是什么

**这是国策树可视化的命门，绝大多数教程不提。** 它把 `x`/`y` 从「绝对格子坐标」
改成「相对某个锚点的 delta」：

```clausewitz
# 没有 relative_position_id：x/y 是绝对格子坐标
x = 6
y = 0

# 有它：x/y 是相对那个国策的偏移量
relative_position_id = GER_prioritize_economic_growth
x = 6    # 「比锚点往右 6 格」
y = 0    # 「和它同一行」
```

官方文档（`common/military_industrial_organization/organizations/_documentation.md:186`）原话：

> by default position is the absolute coordinate in the tree grid.
> if `relative_position_id` is provided, **it becomes a delta applied to the input position**

### 必须是递归解算，不是单层相加

锚点自己也可能带 `relative_position_id`，所以 delta 要**沿链累加到底**。
用实测数据裁决了三种解释，判据是「同一棵树内坐标重复的节点数」——正确解释应该接近 0：

| 解释方式 | 67 棵树内的重叠节点数 | 判断 |
|---|---:|---|
| 直接用 `x`/`y` | **8440** | ❌ 完全不可用 |
| 只跟一层锚点相加 | **6680** | ❌ 几乎没改善 |
| **递归沿链累加** | **140** | ✅ 消除 98.3% |

那 140 个残留不是算错：`china_warlord_sea.txt` 这类文件把 SIK / XSM / SIC / YUN
**多个军阀的国策塞进同一棵树**，它们各自从相同格子起步，是真实的设计重叠。

**尺度参考**：德国 438 个国策、锚点链最深 12 层，解算后横跨 **148 列 × 20 行**。
只看原始 `x`/`y` 会以为是 90 列，画出来挤成一团。

实现见 `mcp-server/preview.py` 的 `resolve_positions()`——带环检测，因为 mod 里
「A 相对 B、B 相对 A」是常见手误，不设防会直接爆栈。

## 十、跨文件的四层调用关系

上面这一段国策已经串起了整个链条，这是「知其所以然」的核心：

```
common/national_focus/germany.txt          id = GER_the_four_year_plan
        │
        ├─ icon = GFX_focus_GER_the_four_year_plan
        │        └→ interface/*.gfx:  spriteType 注册这个名字
        │                 └→ texturefile = gfx/interface/goals/....dds
        │                          └→ 真正的图片文件（99% 未压缩 32bpp）
        │
        ├─ add_tech_bonus { name = GER_the_four_year_plan }
        │        └→ localisation/*.yml:  GER_the_four_year_plan:0 "四年计划"
        │                 缺了这条，游戏里显示成未本地化的 key
        │
        └─ every_core_state / limit / is_fully_controlled_by
                 └→ documentation/triggers.md   （180 KB，权威清单）
                 └→ documentation/effects.md    （222 KB，权威清单）
```

**任何一环缺了，游戏不报错，只是那个东西不显示**。这是 HOI4 modding 最常见的
「改了没反应」根源。逐环追查的方法见 `04_world/` 与 `05_presentation/`。

## 十一、解析器：不用自己写

仓库里已有 `mcp-server/cw.py`（290 行，零依赖）。**不要另写一个**——它已经处理了
「同键多次出现」和「无名列表」这两个必踩的坑，而这两个坑自造解析器十个有九个会漏。

```python
from cw import parse_file, to_python, get_all

root, errs = parse_file("common/national_focus/GER.txt")
for st in get_all(root, "focus"):        # 同键多次出现，get_all 返回全部
    ...
data = to_python(root)                    # 转成普通 dict/list，方便 json 导出
```

两个坑具体是什么：

| 坑 | 表现 | cw.py 的做法 |
|---|---|---|
| 同键多次出现 | 一国有十几个 `focus = { }`，`dict` 后写的覆盖前面的 | `Block.items` 是 list，`get_all()` 取全部 |
| 无名列表 | `{ GER FRA SOV }` 没有键，只有值 | `Block` 里存 `Scalar`，不要求成对 |
| 半合法文件 | mod 里常见引擎能加载但语法不严谨的文件 | 收集 `errors` 而不抛异常，照样返回 AST |

## 十二、引擎的宽容度：实测边界

拿 `tools/kiant-hoi4-lint.py` 扫原版 `common/` 全部 **2224 个文件**，结果 **1 个错误、14 个警告、2214 个干净**。
这个数字本身就是知识——它划出了引擎的真实容忍边界：

| 写法 | 引擎行为 | 实测例证 |
|---|---|---|
| 文件末尾少 `}` | **容忍**，EOF 当隐式闭合 | `ideas/SOV.txt` 2536 个 `{` 对 2535 个 `}`，游戏正常加载 |
| 文件末尾多 `}` | **报错**，在该行截断解析 | `TSR_lingguang_incident_joint_branch.txt` 第 420 行，7 个 `joint_focus` 块只闭合 6 次 |
| `<=` `>=` `==` `!=` | **静默忽略**整条语句，不报错 | 全库 0 次使用，说明 P 社自己都不敢写 |
| `#` 后的内容 | 全当注释，**包括里面的 `{` `}`** | 968 行的 ASCII art 注释里全是括号，不影响解析 |
| 引号内的 `#` | **不是**注释起点 | `NOT = { has_dlc = "No Compromise, No Surrender" }` |

**结论**：少括号不会炸，多括号会炸，运算符写错不炸但失效。所以 lint 把「少 `}`」
降成 warning、「多 `}`」保持 error——跟着引擎的实际行为走，而不是跟着语法教科书走。

## 十三、自查

```bash
python tools/kiant-hoi4-lint.py common/national_focus/germany.txt
python tools/kiant-hoi4-lint.py --all                    # 扫整个 mod 目录
```

它会报三类：结构错（多 `}` / 引号未闭合）、引擎不支持的运算符、`=` 后无值。
这三类占了新手工错误的绝大多数，而且**都不会进 error.log**——只能静态扫出来。

工具本身也踩过坑，记在 `91_error-book/` 里：最初用 `line.split("#")[0]` 剥注释，
遇到引号含 `#` 的文件就凭空造出括号失衡；又因为跨盘符 `os.path.relpath` 抛
`ValueError` 直接崩掉整个扫描。

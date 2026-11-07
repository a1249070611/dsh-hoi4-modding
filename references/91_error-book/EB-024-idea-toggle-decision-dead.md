---
title: "EB-024 开关型 idea 的决策点了没反应（allowed 拦截 / modifier 量纲写错）"
id: EB-024
domain: 91_error-book
symptom_class: 功能不生效
severity: 一般
verified_on: 1.19.4.2
verified_at: 2026-11-07
first_seen: 工坊 mod「海军生产加速」(2412454301)：修理/改装/建造三组开关永远开不起来
related: [02_content/ideas.md, 02_content/decisions.md]
---

# EB-024 开关型 idea 的决策点了没反应（allowed 拦截 / modifier 量纲写错）

## 症状

「决策 A 开 → 加 idea，决策 A 关 → 移除 idea」这套最常见的开关模式，
有些开关点了没任何效果；或者效果数值离谱（强得像作弊）。

## 根因一：idea 的 `allowed` 挡住了 `add_ideas`

`allowed` 在**添加时**求值：不满足就不加上，`add_ideas` 静默无效。

实测案例（海军生产加速 `common/ideas/000naval.txt`）：

```pdx
NAVAL_repair = {
    allowed = { always = no }     # ← 永远不允许存在
    ...
}
# common/decisions/NAV_decisions.txt
NAVAL_repair_on = { complete_effect = { add_ideas = NAVAL_repair } }   # ← 永远无效
```

该 mod 五组开关里三组的 idea 写了 `allowed = { always = no }`，只有
`NAVAL_productioning`（`allowed = { original_tag = ROOT }`）能正常工作。
推测作者本意是「不自动出现」——那用 `allowed_civil_war`/不放 `allowed` 即可，
`allowed = { always = no }` 等于判死刑。

**同一写法的正当用法**（别矫枉过正）：Kaiserreich 用 `allowed = { always = no }`
的哑 idea 做子模组探测占位（`common/ideas/00 Submod trigger ideas.txt:1-30`，
`kr_music_submod` 等占位被子 mod 覆盖后解锁）。判据很简单——
**这个 idea 会不会被自己 `add_ideas`**：会，`always = no` 就是 bug；
只当占位/探测用，合法。

## 根因二：百分比修正的量纲

HOI4 modifier 的两种量纲，混用就会差 10~100 倍：

| 类型 | 含义 | 例子（原版实测分布） |
|---|---|---|
| `*_factor` / 隐式百分比 | 小数，0.1 = +10% | `industrial_capacity_dockyard`：原版 ideas/focus 全部 0.05~0.2 |
| `add`/裸数值 | 按字段语义 | `consumer_goods_factor` 同为小数；`political_power_gain` 是每日点数 |

同案实证：`industrial_capacity_dockyard = 10` = **+1000%** 船坞产出。
作为「加速 mod」可能是有意的，但更多时候是作者不懂量纲。
`repair_speed_factor = 5`（+500%）与 `refit_ic_cost = -0.9`（-90%）在同一文件里
混用两种口径，说明作者没统一理解。

## 诊断步骤

1. 开关无效 → 先看目标 idea 的 `allowed`：`kiant_hoi4_kb_symbol name=<idea id>`
   定位定义文件，读 `allowed` 块。
2. 效果可疑 → 查该 modifier 在原版的取值分布：
   `grep -rh "<modifier> = " 原版/common/ideas 原版/common/national_focus | sort | uniq -c`，
   数量级差 10 倍以上就是量纲错误。
3. `removal_cost = -1` **不是** bug——原版 ideas 里 3600+ 处，是「常驻型 idea 免费移除」
   的标准写法，别误修。

## 标准化方案

```pdx
# 正确的开关 idea
NAVAL_repair = {
    # 不写 allowed（或写真实条件）
    removal_cost = -1
    modifier = { repair_speed_factor = 0.5 }   # +50%，不是 5
}
```

配对决策记得给「开」加 `available = { NOT = { has_idea = X } }` 防重复点亮，
给「关」加 `available = { has_idea = X }`（该 mod 的关开关写对了，开开关漏了）。

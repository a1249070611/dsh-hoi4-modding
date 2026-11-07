---
title: 性能（可量化的脚本性能实践）
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - console_commands_documentation.md
  - _documentation.md
  - https://hoi4.paradoxwikis.com/Patch_1.19.X
---

# 性能

> 本文是可直接照做的工程版：先量化、再改架构、最后抠写法。凡标「社区经验」的排序，都先用 §1 的 timer 流程复核。

## 1. 唯一可信的优化方式：`timer`

游戏自带 `documentation/console_commands_documentation.md`（A 级）确认存在：

```
timer_start / timer_stop / timer_reset / timer_restart / timer_dump / timer
```

流程（缺一不可）：

```
同存档 + 同 mod 版本 → timer_reset → 跑固定天数（如 30 天，1 速或暂停推进）→ timer_dump
改动一处 → 重复 → 对比数字
```

**没有这一步的「优化」都是猜测。** 本文件里凡标「社区经验」的排序，都要用这套流程复核后才能写进结论。

## 2. 结构性事实（对原版文件 grep 得到，可复现）

| 事实 | 值 | 含义 |
|---|---|---|
| `events/` 里 `is_triggered_only` | **6635** | 原版绝大多数事件靠显式触发 |
| `events/` 里 `mean_time_to_happen` | **406** | MTTH 只占约 6%，是少数派 |
| `common/on_actions/` 里 `on_X = {` | **315** | 原版已占用 315 个挂载点，每次 tick 都在跑 |
| on_actions 文件数 | 17（+`_documentation.md`） | 按 DLC 分文件，`00_on_actions.txt` 是主体 |

→ **架构结论：优先「动作驱动」，避免「周期扫描」。** 这不是微优化，是「你的 mod 每天要跑多少脚本」的量级问题。

## 3. 架构选择（按收益从大到小）

| 方式 | 何时执行 | 用在哪 | 风险 |
|---|---|---|---|
| `completion_reward`（国策） | 点击完成时，一次 | 一次性收益 | 无 |
| `complete_effect`（决议） | 决议完成时 | 一次性收益 | 无 |
| `immediate`（事件） | 事件触发时 | 一次性 | 无 |
| `on_declare_war` / `on_capitulation` / `on_civil_war_end` 等 | 事件发生时 | 状态响应 | 挂载点必须存在于 `common/on_actions/_documentation.md` |
| **`on_startup`** | 新游戏开局一次 | 初始化（不要覆盖 history） | 每次开新档都跑，别做重活 |
| `on_monthly` / `on_weekly` | 周期 × 国家 | 必须周期检查的东西 | 每月 × 100+ 国家 |
| **`on_daily` / MTTH** | 每天 / 随机 | 最后手段 | 最大的性能坑 |

**判断口诀**：能挂在「玩家动作」或「游戏事件」上，就不要挂在「时间」上。

## 4. 写法层清单

```pdx
# ❌ 差：全世界扫描 + 每个都做重判断
every_country = {
    limit = { has_war = yes }
    every_owned_state = { limit = { is_core_of = PREV } add_building_construction = { type = infrastructure level = 1 instant_build = yes } }
}

# ✅ 好：先做最便宜的剪枝，再进重逻辑；且用 1.19.x 的集合算子
every_country = {
    limit = {
        has_war = yes            # 便宜
        is_ai = no               # 便宜
    }
    ...
}
```

要点：

1. **剪枝条件放最前**：`tag =`、`exists =`、`is_ai =`、`has_war =`、数值比较 → 然后再进 `any_state`/`any_country` 这类遍历。
2. **避免三层嵌套**（国家 × 州 × 省份）。原版自己的 scripted trigger 里也很少这么写。
3. **1.19.3 起（1.19.x 沿用）优先用集合算子** `is_core_of` / `is_not_core_of`（Patch 1.19.3 原文说 "better performance than the trigger alternatives"）。⚠️ 本地 `script_collection_operator.md` 尚未收录，写法需回游戏文件确认。
4. **动态变量只在变化时刷新**：`force_update_dynamic_modifier` 不要挂 `on_daily` 全量刷。⚠️ 社区经验。
5. `scripted_trigger` / `scripted_effect` 复用只减**体积**，不减**求值次数** —— 不要为了「性能」而滥用间接层（反而更难 profiler）。
6. 长文本 tooltip（尤其中文）避免超长单条：1.19.3 修过「modded 内容文本缓冲区过小导致 CTD」（官方 patch notes），说明这类边界真实存在。

## 5. 已知引擎级问题（1.19.x 官方修复，遇到别先怀疑自己）

来自 Patch 1.19 / 1.19.3 的 Stability & Performance 段（A 级）：

- 1.19.3：优化 `this`/`prev`/`from`/`root` 的 ScopedVariable 遍历；
- 1.19.3：修复「读档后补给系统严重降速」；
- 1.19.3：修复「火箭任务数量多时某些 mod 崩溃」；
- 1.19：减少存档中省份数据体积；优化海军 HQ 计算与陆军 HQ 寻路；贸易系统改用更多 core。

→ 玩家报「越玩越卡」时，先确认是**读档后**还是**持续运行**，再看是不是自己的脚本。用 `timer` 而不是猜。

## 6. 与调试模式的交互（重要）

- 调试模式会**显著降速**（wiki）。**测性能必须关掉 `-debug_mode`**。
- 但 `timer` 命令本身是否依赖调试模式 ⚠️ 待验证 —— 建议实测：正常启动能否用 `timer_start`。

## 7. 自检清单

- [ ] 我的 mod 有没有 `on_daily` / `on_monthly` / MTTH 周期扫描？能不能改成事件/国策驱动？
- [ ] 循环里的最外层是不是最便宜的剪枝？
- [ ] 有没有「国家 × 州 × 省份」三层遍历？
- [ ] 动态变量是不是每次变化才刷新？
- [ ] 优化前后有没有 `timer_dump` 的数字对比？
- [ ] 测性能时是否关掉了调试模式？
- [ ] 长中文 tooltip 是否控制在合理长度？

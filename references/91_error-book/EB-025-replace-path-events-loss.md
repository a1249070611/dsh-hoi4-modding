---
title: "EB-025 replace_path=events 之后，间谍/核爆等系统事件全部失踪"
id: EB-025
domain: 91_error-book
symptom_class: 功能不生效
severity: 严重
verified_on: 1.19.4.2
verified_at: 2026-11-07
first_seen: East Showdown / The Fire Rises 双实证：整目录替换 events 后，依赖原版事件的 on_actions 断链
related: [02_content/events.md, 90_case-studies/vanilla-mod-survey.md]
---

# EB-025 replace_path=events 之后，间谍/核爆等系统事件全部失踪

## 症状

全转换 mod（或滥用 `replace_path="events"` 的 mod）里：情报机构玩法不触发、
核弹没有事件、on_actions 里引用的事件 404。`error.log` 会有
`event xxx not found` 之类，也可能只静默。

## 根因（TFR + ES 双实证，2026-11-07）

`replace_path="events"` 让**整个 events/ 目录由 mod 接管**——原版 263 个事件
文件全部退场。但很多引擎系统不是「可选加成」而是「硬依赖」事件：

| 被断链的系统 | 依赖的原版事件 |
|---|---|
| LaR 情报机构（特工招募/任务） | `lar_operative_event.*` |
| 核弹投放反馈 | 原版核事件族 |
| 部分 DLC 机制 | BBA/AAT/NV 等按 DLC 挂的事件 |

两个头部 mod 的补救方式完全一致，证明这是必修课：

- **East Showdown**：`events/ES_intelligence_events.txt:4` 手动重写
  `add_namespace = lar_operative_event`，只保住自己 `es_on_actions.txt`
  引用的 `lar_operative_event.6`。
- **The Fire Rises**：直接把原版 `events/LaR_agent_events.txt` **整文件拷贝**
  进自己的 events/（实测在包内），保证 replace 后间谍事件不空。

## 标准化方案

1. replace `events` 前，先列清单：mod 的 on_actions / 决议 / 国策里引用的
   **非自有 namespace**（即原版/DLC namespace）有哪些。
2. 两种补法：**最小补**（只重写被引用的 namespace 与事件号，像 ES）或
   **整文件拷贝**（像 TFR，保 DLC 完整行为但背维护债）。
3. 每次游戏版本升级后重跑一遍核对：`kiant_hoi4_list_overrides` +
   `kiant_hoi4_kb_build` 索引原版后，用 `kiant_hoi4_kb_symbol` 抽查
   被引用的原版事件是否仍存在。
4. 能不用 `replace_path="events"` 就不用——MD/TNO 级别确实需要整目录
   接管时再上，并且把「补回系统事件」写进版本升级清单
   （`06_workflow/migration.md` 的升级 Checklist 应包含此项）。

## 关联

- replace_path 的总代价与组合拳：`93_ecosystem/mod-maintenance-engineering.md` §6。
- 另一个同款坑：ES 的 `events/SuperEvents_0.6.txt` 旧版遗留——replace 后
  **目录里所有 txt 都加载**，旧版和新版超级事件并存双触发；replace 的
  目录没有「加载一半」这种事，清理要彻底。

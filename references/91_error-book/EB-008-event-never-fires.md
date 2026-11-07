---
title: "EB-008 事件不触发"
id: EB-008
domain: 91_error-book
symptom_class: 游戏内行为
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 事件系统通用场景
related: [02_content/events.md]
---

# EB-008 事件不触发

## 症状

事件写好了，条件看起来都满足，游戏里等到天荒地老也不弹。

## 错误做法（我试过的）

1. 以为是 `trigger` 条件太严，一条条放宽 → 放到全 `always = yes` 还是不触发
2. 以为是 `fire_only_once` 之类参数写错 → 去掉也一样
3. 以为是 `mean_time_to_happen` 太长，改短 → 还是不触发
4. 反复 `event xxx.1` 手动触发 → **手动能触发说明事件本身是好的，问题在自动触发条件**

## 根因

第 4 条错误做法其实提供了关键信息。手动能触发 = 事件注册成功，问题在触发机制：

| 根因 | 说明 |
|---|---|
| **`is_triggered_only = yes` 但没配触发源** | 声明了只由脚本触发，却没有 `on_actions` 或别的事件去 `country_event` 它。它永远不会自己弹 |
| **`mean_time_to_happen` 缺失** | 没有 `is_triggered_only` 也没有 MTTH 时，事件不知何时评估 |
| **缺 `add_namespace`** | ID 是 `namespace.number`，namespace 未声明则整个事件无效 |
| **`trigger` 里的 scope 不对** | 在 country scope 里用了 state scope 的条件 |
| **MTTH 的 `modifier` 里条件恒假** | 见 EB-010，MTTH 被 modifier 拉到极长 |

## 标准化方案

```bash
# 1. 先分叉：手动触发能弹吗？
#    能 → 触发机制问题（本条目）
#    不能 → 注册问题（EB-007）
```

2. 检查 `is_triggered_only` 与触发源是否配套：

```
country_event = {
    id = mymod.1
    is_triggered_only = yes      # 声明只由脚本触发
    # ↑ 那就必须有一处 country_event = { id = mymod.1 } 去调它
}
```

3. 或者改用 MTTH 自动触发：

```
country_event = {
    id = mymod.1
    trigger = { ... }
    mean_time_to_happen = {
        months = 6
        modifier = { factor = 0.5 has_country_flag = my_flag }
    }
}
```

4. 确认 `add_namespace = mymod` 在文件顶部。

## 预防

- 写事件时明确选一种触发方式：MTTH 自动 / `is_triggered_only` + 显式调用，不要两种都半配
- `kiant_hoi4_validate_mod` 会查 namespace

## 验证

1. `kiant_hoi4_validate_mod` 通过
2. 游戏内手动 `event mymod.1` 能弹（证明注册正常）
3. 满足条件后等待 MTTH 时间，能自动弹

## 备注

**「手动能触发吗」是最高效的分叉判断。** 这一步能在 10 秒内把问题空间砍一半，不要跳过。

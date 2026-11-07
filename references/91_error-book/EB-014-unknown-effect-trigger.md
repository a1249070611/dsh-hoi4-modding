---
title: "EB-014 Unknown effect-type / Unknown trigger-type"
id: EB-014
domain: 91_error-book
symptom_class: 日志校验
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 旧教程写法移植
related: [01_script/effects-triggers.md, 01_script/_index.md]
---

# EB-014 Unknown effect-type / Unknown trigger-type

## 症状

`error.log` 里有：

```
[19:12:03][parser.cpp:1234]: Error: Unknown effect-type "check_variable" in file: common/scripted_effects/mymod.txt line: 42
[19:12:03][parser.cpp:1234]: Error: Unknown trigger-type "set_temp_variable" in file: ... line: 88
```

## 错误做法（我试过的）

1. 以为是拼写错误，逐字母核对 → 拼写是对的
2. 以为是版本太旧不支持 → 当前是 1.19.x，够新
3. 在网上的教程里找到了这个写法，认为教程不会错 → **教程写的是 1.9 前后的老引擎**

## 根因

三种可能，按频率：

| 根因 | 判断方法 |
|---|---|
| **写法已废弃**（老教程） | 查 `documentation/effects_documentation.md` 里有没有 `## 这个名字` |
| **effect 用在了 trigger 位置**（或反之） | 名字存在，但类型不对 |
| **该 scope 下不支持** | 名字存在，但你的 scope 里没有 |

**最常见的第 1 种**：网上大量教程停留在旧版本，`while =`、`check_variable` 满篇。

## 标准化方案

```bash
# 1. 确认这个名字现在还存在吗（唯一权威来源）
grep -n "^## check_variable" <GAME_DIR>/documentation/triggers_documentation.md
grep -n "^## check_variable" <GAME_DIR>/documentation/effects_documentation.md
```

没有输出 = 这个名字不存在了。

2. 查 1.19.x 的正确写法。`01_script/_index.md` 有一张 **14 条新旧写法差异表**，直接对照：

| 旧写法 | 1.19.x 正确写法 |
|---|---|
| `while = { limit = {} ... }` | `while_loop_effect = { limit = {} break = ... }` |
| `custom_trigger_tooltip` | `custom_override_tooltip` |
| `if/else` 双写模拟 | 原生 `else` / `else_if` |
| 字符串拼接生成 effect | `meta_effect` |

3. 改完重跑日志，看该类是否消失。

## 预防

- **不要照抄网上教程的 effect/trigger 名字。** 所有名字先在 `documentation/*.md` 里 grep 一遍
- 判断教程是否过时：搜全文有没有大量 `while =`、`custom_trigger_tooltip`、`check_variable`，有就是老引擎

## 验证

重跑 `error.log`，`Unknown effect-type` / `Unknown trigger-type` 该类别消失。

## 备注

**这是「文档滞后」的典型场景**：`documentation/effects_documentation.md` 本身也不全（例如官方文档只列了 `if`，没列 `else`/`else_if`，但引擎实际支持）。所以除了 grep 文档，还要看原版怎么做：

```bash
grep -rn "else_if" <GAME_DIR>/common/ | head
```

原版有 = 引擎支持，即使文档没写。

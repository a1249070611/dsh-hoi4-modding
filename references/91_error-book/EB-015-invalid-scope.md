---
title: "EB-015 Invalid Scope, supported: ..."
id: EB-015
domain: 91_error-book
symptom_class: 日志校验
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: scope 切换场景
related: [01_script/scopes.md, 01_script/effects-triggers.md]
---

# EB-015 Invalid Scope, supported: ...

## 症状

`error.log` 里：

```
[19:15:22][scopes.cpp:90]: Error: Invalid Scope, supported: country, state, ...
```

## 错误做法（我试过的）

1. 以为是 effect 名字错 → 名字存在且拼写正确
2. 以为是括号嵌套问题 → 括号平衡
3. 在错误的 scope 里反复加 `ROOT`/`FROM` 前缀 → 前缀不能改变当前 scope 类型

## 根因

你在 `A` 类型的 scope 里，用了一个只支持 `B` 类型 scope 的 effect/trigger。

典型场景：在 `country` scope 里遍历 state 并直接对 state 用 country 操作；或 `every_country = {}` 里以为自己在 state scope。

## 标准化方案

1. **先明确当前位置的 scope 类型。** 读 `01_script/scopes.md` 的 scope 表和切换语法。

2. 用显式切换进入正确 scope：

```
every_owned_state = {          # 进入 state scope
    add_building_construction = { ... }   # state scope 的操作
}
```

3. 需要回到上层时用 `ROOT` / `PREV` / `FROM`。

4. 确认该 effect 支持的 scope 列表：`documentation/effects_documentation.md` 里每个 effect 都标了 scope。

## 预防

- 写复杂嵌套前先画 scope 树（哪一层是什么类型）
- 用 `debug_log` 打印 `[This.GetName]` 之类确认当前对象

## 验证

重跑日志，`Invalid Scope` 消失。

## 备注

**scope 错误的特征是「名字对、位置错」**：grep 文档能找到这个 effect，但它不支持你当前所在的对象类型。

判断技巧：报错行里的 `supported:` 后面列的就是该 effect 支持的 scope 列表。对照你现在的 scope 类型，一眼能看出差在哪。

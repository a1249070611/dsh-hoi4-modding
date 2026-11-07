---
title: "EB-010 条件判断永远为假（trigger 恒 false）"
id: EB-010
domain: 91_error-book
symptom_class: 游戏内行为
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: DLC 判定与 scope 混用场景
related: [01_script/effects-triggers.md, 01_script/scopes.md]
---

# EB-010 条件判断永远为假

## 症状

写了 `trigger` / `limit` / `potential`，逻辑看起来完全正确，但条件**始终不成立**——该触发的不触发，该显示的选项不显示。

`error.log` 通常无报错（又是静默失败）。

## 错误做法（我试过的）

1. 以为是逻辑写错，反复调整 `AND`/`OR`/`NOT` 结构 → 逻辑没问题
2. 以为是变量没赋值，加 `debug_log` 打印 → 变量有值
3. 怀疑 trigger 本身不存在 → 查文档，存在

## 根因

按出现频率排：

| 根因 | 说明 |
|---|---|
| **`has_dlc` 字符串拼错** | 必须与 `dlc/dlcNNN_*.dlc` 里的 `name` **完全一致**。写错 = 条件永远假，且不报错 |
| **scope 不对** | 在 `country` scope 里用了 `state` scope 的 trigger。某些情况下返回 false 而非报错 |
| **变量未初始化就读** | 读未定义变量返回 0 或 false，不报错 |
| **`original_tag` vs `tag` 混用** | 国家变身后 `tag` 变了但 `original_tag` 不变，判断建国用哪个要分清 |
| **引用了不存在的 flag** | 从未 `set_country_flag` 却去 `has_country_flag` |

## 标准化方案

```bash
# 1. 查 DLC 名字（最常见的坑）
ls <GAME_DIR>/dlc/*.dlc | head
grep -h "^name" <GAME_DIR>/dlc/*.dlc
```

把你脚本里的 `has_dlc = "XXX"` 与上表逐个对照，**逐字比对**（含空格、大小写）。

```bash
# 2. 确认 scope 类型
#    在 trigger 前加临时日志，或读 01_script/scopes.md 的 scope 表
```

3. 变量先赋值再读：

```
set_variable = { my_var = 0 }   # 先初始化
...
check_variable = { my_var > 0 }
```

## 预防

- `has_dlc` 字符串从原版文件里复制，不手打
- 写 trigger 前先确认当前 scope 类型
- 变量在使用前显式初始化

## 验证

用 `debug_log` 打印中间值：

```
debug_log = "my_var is [my_var]"
```

在 `error.log` 里看输出。这是**唯一可靠的**判断 trigger 内部状态的方法——不能靠"看起来对"。

## 备注

`has_dlc` 这条坑特别隐蔽，因为 DLC 名字是字符串常量，写错了 IDE 不会提示、游戏不报错、逻辑上完全说不通（"我明明有这个 DLC"）。

本机的判断依据：`<GAME_DIR>/dlc/` 下有 42 个 `.dlc` 文件、43 个 DLC 目录。例如 `dlc052` 的 name 是 `"Thunder at Our Gates"`。如果你的脚本写 `has_dlc = "Thunder At Our Gates"`（大写 A），条件恒假。

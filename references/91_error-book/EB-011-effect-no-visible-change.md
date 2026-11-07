---
title: "EB-011 效果执行了但数值没变"
id: EB-011
domain: 91_error-book
symptom_class: 游戏内行为
severity: 一般
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 脚本效果调试
related: [01_script/effects-triggers.md, 01_script/variables.md]
---

# EB-011 效果执行了但数值没变

## 症状

`add_political_power = 100` 之类写好了，事件弹了、日志没报错，但游戏里数值纹丝不动。

## 错误做法（我试过的）

1. 以为是数值太小看不出，改大 10 倍 → 还是不变
2. 以为是 effect 名字错 → 名字对，且日志无 `Unknown effect-type`
3. 以为是 UI 刷新问题，等了一会儿再看 → 不是延迟

## 根因

| 根因 | 说明 |
|---|---|
| **作用对象错**（最常见） | 你改的是 `ROOT`，但你以为在改 `FROM`。效果确实执行了，改的是另一个国家 |
| **变量未初始化** | 读未定义变量得 0，加减 0 等于没变 |
| **被后续效果覆盖** | 同一 tick 内后面有别的 effect 把值重置了 |
| **改的是临时变量** | `set_temp_variable` 的值不跨事件/不持久 |

## 标准化方案

```bash
# 1. 打印确认作用对象
#    在 effect 前后加：
#    debug_log = "before: [This.GetName] pp=[This.political_power]"
#    add_political_power = 100
#    debug_log = "after: [This.GetName] pp=[This.political_power]"
```

看 `error.log` 里打印的是哪个国家、数值有没有变。

2. 如果打印显示"对象是 A，但你以为在改 B" → 用显式 scope 限定：

```
FROM = { add_political_power = 100 }   # 明确指定 FROM
```

3. 如果是变量问题，先初始化：

```
set_variable = { my_var = 0 }
add_to_variable = { my_var = 100 }
```

## 预防

- 复杂效果链每个关键步骤都加 `debug_log`，不要写完了才一起测
- 变更数值类效果时，明确写出目标 scope，不依赖隐式 `This`

## 验证

`debug_log` 打印的前后数值差等于预期值。

## 备注

**`debug_log` 是 HOI4 脚本调试的唯一可靠手段。** 不能靠"看界面有没有变"来验证逻辑——界面可能是缓存、可能延迟、可能显示别的地方。

一个实用模式：一段效果链写完后，在开头和结尾各打一行日志，中间不动。这样既能看到最终结果，也能在结果不对时二分定位。

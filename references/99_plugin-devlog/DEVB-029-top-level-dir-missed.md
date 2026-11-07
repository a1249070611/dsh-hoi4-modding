---
title: "DEVB-029 顶层目录被路径判断漏掉，整类符号静默丢失"
id: DEVB-029
domain: 99_plugin-devlog
symptom_class: 索引构建
severity: 阻断
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: 解析原版后发现事件一条都抽不出来
related: [mcp-server/kb.py, 91_error-book/EB-017]
---

# DEVB-029 顶层目录被路径判断漏掉

> 维护者条目。这是本插件自身的索引 bug，不是 mod 写法问题。
> modder 遇到「查不到东西」看 `91_error-book/EB-017` 和 `EB-019`。

## 症状

`kb_lookup kind=event` 返回 0 个，`kb_stats` 的 `symbols_by_kind` 里**根本没有 `event` 这个键**。

但原版 `events/` 下明明有 128 个文件、约 7000 个 `country_event` / `news_event` / `state_event`。

其它类型都正常，于是第一眼会以为索引是好的：

```
focus      10341 个   ← common/national_focus/ 能抽到
tech         554 个   ← common/technologies/   能抽到
idea        6515 个   ← common/ideas/          能抽到
event          0 个   ← events/                抽不到
```

## 错误做法（我试过的）

1. 以为原版没有事件 → `ls events/` 有一百多个 txt
2. 以为事件 id 带点号（`denmark_political_events.1`）导致解析失败 → 关键词其实能搜到文件内容，只是没进 symbols 表
3. 反复重建索引，每次都是 0 → 判断逻辑本身就不匹配，重建多少次都一样
4. 加 `progress_every` 看进度 → 文件数是 6167，全都在扫，只是抽不出符号

**第 2 步的线索最有价值**：同一个文件里的内容用关键词能搜到，说明**文件读到了**，问题在抽取。先分清「没读到」和「没抽出」，能省一半时间。

## 根因

路径判断写成了「子串包含 `/xxx/`」，而顶层目录的相对路径没有前导斜杠。

```python
lower = relpath.lower().replace("\\", "/")

if "/national_focus/" in lower:   # ✅ common/national_focus/germany.txt 命中
elif "/events/" in lower:          # ❌ events/AAT_Denmark.txt 不命中
```

`common/national_focus/germany.txt` 里有 `/national_focus/`，因为前面还有 `common`。
但 `events/AAT_Denmark.txt` 里根本没有 `/events/` 这五个字符——只有开头的 `events/`。

**这个洞只有顶层目录才暴露**：`events/`、`history/`、`interface/`、`gfx/` 全中招。
二级目录的 `common/`、`dlc/` 安然无恙，所以不逐类点数就看不见。

## 修法

给相对路径统一补一个前导斜杠，让所有 `/xxx/` 判断对顶层也成立。

```python
lower = "/" + relpath.lower().replace("\\", "/").lstrip("/")
```

改完后符号数 62120 → 69102，多出 6982 个事件。

代价：某处逻辑如果依赖 `lower` 不带前导斜杠，要一起改。本项目里没有（`endswith` 判断不受影响）。

## 为什么值得记一条

**用「补前导斜杠」而不是在一堆 `if` 里逐个加 `startswith("events/")`。** 后者改一处漏一处，
下一个顶层目录还会犯。

**静默丢数据比报错危险得多。** 这个 bug 从头到尾没抛过一次异常，索引照样建完、篇数照样对、
其它类型照样能查。如果自检只断言「总量 > 0」，总量由 focus 那 1 万条撑着，少一类完全看不出来。

## 现在由什么挡着

自检里有按类型点数的断言，不再只看总量：

```python
assert st["symbols_by_kind"]["event"] > 0
assert st["symbols_by_kind"]["focus"] == 10341
```

## 验证

```python
r = kb.lookup("event", limit=1)
assert r["examples"][0]["relpath"].startswith("events/")
assert "country_event" in r["examples"][0]["excerpt"]

d = kb.find_symbol("denmark_political_events.1")
assert d["definitions"][0]["kind"] == "event"      # 带点号的 id 也能定位
```

对照磁盘实际点数：`ls events/*.txt | wc -l` 和 `kb_stats` 的事件数应该同量级。
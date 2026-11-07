---
title: "SOL-009 从游戏文档生成 effect/trigger 速查表"
id: SOL-009
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/build_reference.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-009 从游戏文档生成 effect/trigger 速查表

## 它想解决什么

`documentation/effects_documentation.md` 有 8000+ 行，`triggers_documentation.md` 也有几千行。查一个 effect 支持哪些 scope、参数是什么，靠翻文件很慢。

而这两个文件是**判断「某个 effect 是否真实存在」的唯一权威来源**（对应错题本 `EB-014`）。

## 思路

上游 `build_reference.py` 从游戏文档生成速查表：effects / triggers / modifiers / console commands。

核心洞察：`documentation/*.md` 里每个 `## effect_name` 就是一条定义。所以可以结构化解析成表：

```
effect_name | scope 支持 | 参数 | 行号
```

生成后可按 scope 或关键词快速查，不用读 8000 行原文。

## 为什么没被采用

本插件用**知识库索引**替代了它：`kb_build` 把 `documentation/*.md` 索引进去（走 `code` 表，unicode61 精确匹配），`kb_symbol` 能直接查某个 effect 的定义位置。

功能上覆盖了，但体验不同：
- 速查表 = 静态、可离线浏览、可以打印
- kb_search = 动态、需要建索引、给出精确行号

## 如果要用，怎么验证

1. 读上游 `build_reference.py`，看它怎么处理文档里的 scope 标注格式
2. 生成一次，抽查 10 个 effect 与原文对照
3. 特别验证容易错的边界：同名 effect 在多个 scope 下有不同签名的情况

验证标准：随机抽 10 条，生成结果与 `documentation/*.md` 原文一致。

## 备注

**这个能力与知识库是互补而非重复。**

一个实际场景：查某个 effect 时，`kb_symbol` 告诉你"在第 4279 行"，你还是要去读那一行附近的上下文。而速查表直接给出"支持 scope: country/state，参数: value"。

如果要补，最简方案不是重写工具，而是**给 `kb_lookup` 加一个"按 scope 过滤"的能力**——从索引里提取 scope 信息，比生成静态表更轻。

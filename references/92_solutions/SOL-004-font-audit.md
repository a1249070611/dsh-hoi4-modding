---
title: "SOL-004 中文字体映射体检"
id: SOL-004
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/font_audit.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-004 中文字体映射体检

## 它想解决什么

中文显示成 `????`（对应错题本 `EB-002`）。根因不是字库缺字形，而是**字体名/字重没有映射到中文分片**。

这个问题靠人眼看界面排查极其低效：你得逐个 GUI 元素看，才发现"哦这个字体名没映射"。

## 思路

上游 `font_audit.py` 的做法是**静态扫描**：

1. 解析 `interface/*.gfx` 里所有 `.gui` 文件的 `font = "xxx"` 引用
2. 解析 `interface/core_chinese.gfx` 里的 `bitmapfont_override` 块——这些块定义了哪些字体名被映射到中文分片
3. 求差集：**被 GUI 引用但没有中文映射的字体名**

关键实证数据（1.19.4 实测）：
- `gfx/fonts/chinese/*.fnt` 四个分页各约 **7677 / 7813 / 8002 / 7041** 个字
- 所以字库肯定是够的，问题一定在映射层

`font list` 子命令单纯列出「当前被映射到中文分片的字体名」，用作对照基线。

## 为什么没被采用

本插件把字体相关知识放进了 `05_presentation/fonts-cjk.md`（文档），没做工具化。文档能解决"知道原理"，但解决不了"我这 40 个 GUI 文件里到底是哪个字体名没映射"。

**这是个真实缺口。**

## 如果要用，怎么验证

1. 读上游 `font_audit.py`，确认它解析 `.gfx` 的方式（正则还是结构化）
2. 在原版数据上跑，确认 `font list` 输出与 `interface/core_chinese.gfx` 里的 override 块数量一致
3. 故意在某个 `.gui` 里加一个不存在的字体名，确认能被报出来

验证标准：`font list` 列出的字体名，与手工 grep `core_chinese.gfx` 的结果一致；注入的假字体名能被检出。

## 备注

**这是「文档讲原理，工具解决具体定位」的典型对照。**

`05_presentation/fonts-cjk.md` 已经讲清楚了机制（为什么是映射问题不是字库问题），但使用者看完文档还是要自己去 40 个文件里找一个写错的字体名——这正是工具该做的事。

优先级：与 SOL-003 地图审计并列，是最值得补的两个缺口之一。

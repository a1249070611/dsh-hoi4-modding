---
title: 解析库调研：jomini 双子星与陈旧项处置
domain: 93_ecosystem
scope: tooling
verified_on: rakaly/jomini（99★，main @ 2026-11-05）+ nickbabcock/jomini（96★，WASM 绑定）
verified_at: 2026-11-07
source: 双仓库源码精读 + 作者官方语法陷阱长文（pdx.tools/blog/a-tour-of-pds-clausewitz-syntax）
---

# 解析库调研：jomini 双子星与陈旧项处置

## 1. 先说破：两个 jomini 是同一解析器

`rakaly/jomini`（Rust 内核，99★，两天前还在推）与 `nickbabcock/jomini`
（TS，96★）**同出 Nick Babcock 一人之手**——后者是前者的 WASM 绑定
（`njomini/src/jomini.ts` 直接 import `./pkg/jomini_js.js`）。
它是 pdx.tools（在线 EU4 存档分析器）、Paradox Game Converters、
pdx_unlimiter 三家的解析底座，主打存档：**1 GB/s、零依赖、 fuzz 过**。

## 2. 作者官方语法陷阱清单（对 cw.py 的反向测验）

作者的《A Tour of PDS Clausewitz Syntax》是公开资料里最全的格式陷阱表。
拿它逐条对照本插件 `cw.py`，2026-11-07 实测结果：

| 陷阱 | cw.py 现状 | 处置 |
|---|---|---|
| 重复键收敛成列表 | ✅ `to_python`/`entries()` 一直如此 | 无需动 |
| 压缩写法 `a={b="1"c=d}` | ✅ tokenizer 天然支持 | 无需动 |
| **无等号块 `foo{...}`** | ❌ key 变裸 Scalar、块变兄弟节点，get_one 静默丢失 | **已修**：归一为 Stmt（原版 HOI4 全量扫描零命中，属 EU4/CK3 习惯写法，跨游戏 mod 作者会带进来） |
| **`?=` 运算符** | ❌ `?` 落进 word 类，关联丢失 | **已修**：op 正则加 `\?=` |
| **行尾分号 `textureFile="x.dds";`** | ❌ `;` 落进 word 类成裸 scalar 污染块 | **已修**：tokenizer 显式跳过 |
| 注释在引号外任意处 / `#` 引号内是字面量 | ✅ | 无需动 |
| 引号转义 `\"` `\\`、引号内换行 | ✅ string 正则覆盖 | 无需动 |
| BOM / 编码（Win-1252 vs UTF-8） | ✅ utf-8-sig 起步 + 本轮解码链 | 无需动 |
| 多余右括号 / 未闭合块 | ✅ 宽容诊断不崩溃 | 无需动 |
| rgb/hsv/list 外标签类型 | ✅ 普通键值块 | 无需动 |
| 数值宽度（u64 丢精度）、延迟定型 | 存档域问题，mod 脚本不涉及 | 不适用 |

**结论**：cw.py 的宽容设计在陷阱清单面前只漏了三条「跨游戏写法」，
当日修复并钉回归断言（自检 319 项）。jomini 是严格解析器（存档必然良构），
mod 文件的坏输入容忍仍是我们的差异化——双方互证。

## 3. 值得记下的设计

- **serde 式 schema 抽取**（`#[jomini(alias, duplicated, take_last)]`、
  `Property<T>` 保留运算符）：把「抽哪几个字段」声明在类型上——若将来
  给 kb 加类型化抽取层，这是组织范本；
- **tape/DOM 两段架构**（text/tape.rs 先打平再查询）：性能轮的参照；
- **encoding.rs**（278 行）：BOM/Win-1252/UTF-16 探测顺序的权威实现，
  我们的解码链可与之对照补 UTF-16 一档（暂无证据 HOI4 文件用 UTF-16，不急）；
- **fuzz 文化**：`fuzz/` 目录 + 恶意输入测试——我们的解析器若暴露给
  不可信输入（远端知识库），值得补最小 fuzz 集。

## 4. 陈旧项处置（按任务要求的筛选纪律）

| 仓库 | 最后活动 | 处置 | 理由 |
|---|---|---|---|
| QAston/clausewitz-antlr-grammar | **2016-07** | **舍弃** | 10 年前的语法，目标是老引擎规则文件；ANTLR 生成器思路教科书化，对本插件零增量 |
| grgrzybek/hoi4-db | **2022-12** | **舍弃** | 3 年未更新；Java 侧游戏数据解析，能力与我们 kb 重叠且无独家发现（README 级核对） |
| MattMcFarland/hoi4-txt-parser | **2017-09** | **舍弃** | 8 年未更新；几十行的 demo 级 JS 解析器，连引号转义都不处理 |
| rakaly/jomini | 2026-11-05 | **收录**（本文） | 语法陷阱清单 + 编码探测 + schema 设计 |
| nickbabcock/jomini | 2026-03 | **收录**（同上，合并一条） | 同一解析器的 TS 形态，供将来做 web 端预览时参考 |

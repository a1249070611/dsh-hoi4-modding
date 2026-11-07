---
title: "EB-023 展示文本硬编码在 common/ 里，汉化覆盖 localisation 没用"
id: EB-023
domain: 91_error-book
symptom_class: 汉化
severity: 一般
verified_on: 1.19.4.2
verified_at: 2026-11-07
first_seen: BlackICE 内核汉化 (3431515994) 覆盖 25 个 common 文件；KR 情报机构名、BICE ai 条件名都是字面量
related: [05_presentation/localisation.md, 05_presentation/fonts-cjk.md]
---

# EB-023 展示文本硬编码在 common/ 里，汉化覆盖 localisation 没用

## 症状

给某个大 mod 做汉化：localisation 层全部翻完，游戏里**仍然有英文**——
出现在情报机构名、AI 战略名、自定义 tooltip、部队番号、角色名等位置。
改 loc 文件毫无作用。

## 根因（实测）

一部分展示文本**根本不是 loc 键**，是写死在 `common/` 脚本里的字面量字符串。
原版引擎在多处接受「loc 键或直接字符串」二选一，大 mod 常图省事直接写字符串：

| 位置 | 实例 | 出处 |
|---|---|---|
| `intelligence_agencies` 的机构名 | `names = { "Secretaría de Inteligencia" }`（注释原文写明 "Can be a localization entry, or the name directly"） | Kaiserreich `common/intelligence_agencies/00_intelligence_agencies.txt` |
| scripted_effects 内的条件/提示串 | `condition = "Army-Navy rivalry-Naval dominance"`（汉化版改为 `"军种对立-海军主导"`） | BlackICE `common/scripted_effects/JAP_scripted_effects.txt:440` 一带 |
| `division_template` 的编制名 | `name = "SS-Totenkopf"` | BlackICE 系 `common/scripted_effects/*` 与 `history/units/*`（OOB 里） |
| 角色名 | `name = "哈利勒·内古蒂"  # Halil Nergutti` | 工坊汉化 mod `common/characters/ALB.txt` |
| 舰船/单位名 | `common/units/names/` 的 prefix/generic/unique 大量直接字符串 | 原版同目录即如此 |

## 为什么「内核汉化」要覆盖 25 个 common 文件

工坊上的 BlackICE 内核汉化 (3431515994) 实测覆盖：
`scripted_effects`×6、`scripted_localisation`×3、`scripted_triggers`×1、
`equipment`×11（舰船 hull）、`intelligence_agencies`×1、`ideas`×2、
`national_focus/germany.txt`、`unit_leader/00_traits.txt`。
对其中 `JAP_scripted_effects.txt` 的 diff = 48 行——全是字符串替换。
这就是「硬编码文本的汉化税」：**逐文件 diff + 全量覆盖，上游一更新就得重做**。

## 标准化方案

1. 先穷尽 loc 层：`kiant_hoi4_scan_localisation` + `kiant_hoi4_kb_search` 确认
   目标文本确实不是 loc 键（很多「看似没翻译」的其实是 `replace/` 目录没覆盖到）。
2. 对硬编码文本，按 `05_presentation/localisation.md` §13 的
   分层工作流做**同路径文件覆盖**；不要重新生成文件，diff 上游原文件后只改字符串，
   保留其余内容，降低升级合并成本。
3. 用 `grep -P "[\x{4e00}-\x{9fff}]"` 反向检查自己的 mod：common/ 里出现
   中文字面量 = 有文本没走 loc，发布英文版会翻车。
4. OOB/编制名这类「必须写死」的，接受覆盖式汉化，但在 mod 说明里标注
   兼容的上游版本号。

## 关联

- `history/units` 的编制名为什么必须整文件覆盖：见人名/开局部队汉化 mod 实测。
- 图标里烤死的文字（texticon）是同一问题的图像版：见 localisation.md §13 第 4 层。

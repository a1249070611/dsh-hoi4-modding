---
title: "DEVB-024 我的验收标准一直是错的：跑过了 ≠ 验过了"
id: DEVB-024
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 阻断
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: 学习 hagane-studio 的 mutation_receipt 时对照自查
related: [93_ecosystem/hagane-studio-mutation-receipt.md, 06_workflow/debugging.md]
---

# DEVB-024 跑过了 ≠ 验过了

## 症状

我给用户的报告一直是这些话：

- "已修复 3 个问题"
- "自检 209/209 全绿"
- "功能可用"

**但每一条都需要打折扣：**

| 我说的 | 实际情况 |
|---|---|
| 已修复 | 改了代码，lint 过了，**没进游戏试过** |
| 全绿 | 209 条**我自己写的**断言过了，没覆盖的照样可能坏 |
| 功能可用 | 单测过了，**没在真实项目上跑过** |

问题不在这些话是假的，而在**我没告诉使用者它们打了多少折扣**。
使用者看到"已修复"，会以为不用再检查了。

## 根因

我把「我的规则没意见」当成了「这件事对了」。

这两者的差距：

```
我的规则能覆盖的              ← 我说"验过了"
─────────────────────
                             ← 我说"完成"时，这里全是黑的
游戏实际能接受的
```

`kiant-hoi4-lint.py` 只查三件事：括号、运算符、空值赋值。它**不查**本地化键、贴图引用、
游戏内行为、引擎实际加载结果。但输出只有"X 个错误、Y 个警告、Z 个干净"——
**"干净"读起来像"没问题"。**

## 对照：hagane-studio 怎么做的

它的 `mutation_receipt` 把状态拆成两个**互不替代**的维度：

```json
{
  "write_status": "committed",        // 东西确实写进去了
  "verification_status": "not_run",   // 但完全没验证
  "reporting_rule": "The write committed, but semantic verification did not run.
                     Report only values returned by this result; re-read and
                     validate before claiming completion."
}
```

**`committed` + `not_run` 是最常见的组合。** 它把这件事明说出来，并且给出
一段**给 AI 看的措辞规则**：只报返回值，别说完成。

它还区分：
- `partially_committed`：批量里部分失败 → "never describe the full batch as completed"
- `verification_unavailable`：想验没验成 → "do not claim completion until they pass"
- `no_change`：`ok=false` → "Do not claim that the requested change was applied"

**关键词全是动作**（report / do not claim / re-read / validate），不是"请注意"。

## 修法

给 `kiant-hoi4-lint.py` 的输出加一段回执：

```
--- 回执 ---
checked_scope:   81 个文件的括号 / 运算符 / 空值赋值，以及国策引用完整性
verification:    syntax_only
not_checked:     本地化键、贴图引用、游戏内行为、引擎实际加载结果
reporting_rule:  以上结果只说明静态规则内未发现问题，不代表 mod 能正常运行；
                 不要仅凭此结论宣称「已完成」或「已修复」。
```

四件事讲清楚：**查了什么、验到什么程度、没查什么、能怎么说话。**

配套 4 条断言钉住它（断言 `--- 回执 ---` / `syntax_only` / `游戏内行为` /
`不要仅凭此结论` 都出现），否则下次重构会悄悄丢掉。

## 同类修正：诊断要带后果和改法

hagane-studio 的诊断结构：

```go
type ReferenceIntegrityFinding struct {
	Code, File, Line, Target   // 哪错了
	Summary     string         // 一句话说明
	Consequence string         // ★ 会造成什么后果
	EditAt      string         // ★ 去哪改
	Severity    string         // warning=会坏 / review=可疑
}
```

实际文案是三段式：

```
"refs.focus_case.summary": "Focus \"{focus}\" names its {relation} as \"{target}\",
                             but that focus is defined as \"{exact}\" (letter case
                             must match exactly)."
"refs.focus_case.impact":   "This focus path may not unlock or exclude as planned."
"refs.focus_case.edit":     "Change that reference in the focus tree to \"{exact}\"."
```

**注意 `may not` 不是 `will not`**——它对没完全证实的后果用不确定措辞。

我的 lint 原来只输出"行号 + 一句话"。改成三段：

```
✗ xxx.txt:3  引擎不支持的运算符 '>='：available = { difficulty >= 2 }
    后果：整条语句会被引擎静默忽略（不报错），条件永远不生效
    改法：只能写 > 或 <，或用 NOT 包一层
```

## 更重要的：改自己的说话方式

| 不该说 | 应该说 |
|---|---|
| 已修复 N 个问题 | 改了 N 处，lint 通过，**未进游戏验证** |
| 自检全绿 | 216 条**静态断言**全过，只覆盖规则内可检的部分 |
| 功能可用 | 接口存在且单测通过，**未在真实项目中验证** |
| 全部完成 | 上述部分完成；以下未验证：… |

**这不是自我贬低，是让使用者能准确判断风险。** 使用者有权知道我说"完成"时
背后验证到了什么程度。

## 预防

1. **任何"检查/验证"输出，必须同时说明"没检查什么"。**
   只报好的那边，等于误导。
2. **给工具加回执，别靠自觉。** 人是会偷懒的，机制不会。
3. **回执要有断言守着**，否则重构时第一个被删的就是它。
4. **诊断三段式**：发现什么 → 会怎样 → 怎么改。缺哪段，用户都得自己补课。
5. **不确定的后果用不确定的措辞**（`may` 而非 `will`）。宁可少断言，也不过度断言。

## 相关

- `tools/kiant-hoi4-lint.py` — 回执段 + 诊断三段式
- `references/93_ecosystem/hagane-studio-mutation-receipt.md` — 完整机制
- `references/93_ecosystem/hagane-studio-deep-notes.md` §四 — 诊断结构精读

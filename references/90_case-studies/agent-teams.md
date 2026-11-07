---
title: 案例：用 Agent 团队做 HOI4 Mod（分工、写域与验收）
domain: 90_case-studies
scope: case-study
verified_on: 1.19.x
---

# 案例：用 Agent 团队做 HOI4 Mod（分工、写域与验收）

> **案例说明**：本文是一次多 agent 协作的**流程复盘**（按文件所有权分工、写域隔离、非写者验收）。**它不是默认做法**：通用规则以本插件各域文档为准，本文只沉淀可迁移的协作约束与失败模式。

> 适用：一个 Mod 里同时要动「科技数据 + GUI + 图标 + 本地化 + 校验」等多条线，
> 单线程容易被 40 GB 的原版/工坊文件淹没，或者几个 agent 同时改同一个生成器。

## 0. 一句话

**按「文件所有权」分工，不按「功能」分工。**
一个生成器只能有一个写者；其余 agent 只产出**结构化结论**，不碰文件。

## 1. 三角色（最小可用团队）

| 角色 | 职责 | 写权限 | 产出 |
|---|---|---|---|
| **survey（调研）** | 读游戏/工坊 mod、验证字段、找原版用例 | **只读** | 带 `文件:行号` 的结论清单 |
| **build（实现）** | 改 `_data/*.json`、生成器、GUI、本地化 | 写**源码树** | 通过 `auto_check` 的改动 |
| **audit（验收）** | 跑校验链、对比安装目录、查 error.log | 只写**报告** | PASS/FAIL + 失败项定位 |

原则：**调研的结论必须能被复核**（给文件路径 + 行号 + 原文片段），
否则实现方会把它当成事实写进代码。

## 2. 写域划分（避免互相覆盖）

```
_data/**.json                -> build 独占
_tools/gen_*.py              -> build 独占（同一时间只有一个 build 改它）
hist_tech_trees/interface/** -> 一个 agent 一个 .gui 文件
localisation/**              -> 一个 agent 一种语言
gfx/**                       -> 一个 agent 一个子目录
_docs/**, 报告               -> audit / survey 只写这里
```

**生成器是单点**：两个 agent 同时改 `gen_hist_tech.py` 必然互相覆盖。
需要并行时，让 A 改 `_data`，B 改 GUI 模板，最后由**一个** build 跑生成器。

## 3. 交接契约

调研 agent 的返回必须长这样：

```markdown
## 结论
- 「没有 gridbox 的科技不画」— 证据：`<BI>/interface/countrytechtreeview.gui`
  2,480 个科技 / 894 个 `<techid>_tree`，其余 1,657 个无 gridbox。
## 可执行建议
- 在 `countrytechtreeview.gui` 为每个要显示的科技声明 `<id>_tree`。
## 不确定
- `ledger` 是否影响排序：未验证。
```

**「不确定」一节不能省。** 实现方据此决定要不要先做对照实验。

## 4. 验收必须由非写者执行

写者自己跑 `auto_check` 通过，不代表没问题（他可能改了检查阈值）。
验收 agent 的固定动作：

```bash
python _tools/gen_hist_tech.py          # 只读式重生成？否——只在 build 完成后跑
python _tools/verify_hist_tech.py
python _tools/hoi4_lint.py <mod>
python _tools/auto_check.py             # 要求全 PASS
# 源码 vs 安装目录哈希比对
diff -r hist_tech_trees "$INST" | head
```

并把 `_docs/auto_check_report.json` 的**逐项结果**贴回来，而不是只写「通过了」。

> 本案的 `_tools/*`、`_docs/*` 是该项目私有脚本与报告目录；本插件里对应的实现是 `scripts/hoi4_lint.py`、`scripts/tech_tree_audit.py`、`scripts/errorlog_triage.py` 等，逻辑同构、可直接替换。

## 5. 并发读、串行写

- 调研可以 3–4 个 agent 同时读不同 mod（只读，无冲突）。
- 实现必须串行到**同一个生成器**；不同文件可以并行。
- 图标/贴图这类二进制产物，按**目录**分给不同 agent，别按文件分。

## 6. 常见失败模式

| 症状 | 原因 | 处理 |
|---|---|---|
| 两个 agent 的改动「消失」 | 都在改同一个生成器，后保存的覆盖前者 | 收回写权限，改为单一 build |
| 调研结论互相矛盾 | 都只读了 wiki，没读游戏文件 | 要求给 `文件:行号`，冲突时以游戏文件为准 |
| 校验通过但游戏里坏 | 写者改宽松了 `auto_check` 阈值 | 验收方独立跑原始校验脚本 |
| 本地化大面积 `????` | 字体名没有中文分片（见 `../05_presentation/fonts-cjk.md`） | `font_audit.py` 先扫 |

## 7. 最小提示词模板

```text
你是 survey。只读，不要修改任何文件。
目标：确认 HOI4 1.19 的 <字段/机制> 是否支持 <需求>。
步骤：
1. 在 <游戏安装目录> 里 grep 原版用例；
2. 在工坊 mod 里找更复杂的用例（列出目录名+文件+行号）；
3. 输出：结论 / 证据（文件:行号 + 原文片段）/ 可执行建议 / 不确定项。
禁止：只给 wiki 链接、不给行号、写「应该可以」。
```

```text
你是 build。你独占 _tools/gen_*.py 与 _data/*.json。
只改 _data，然后跑生成器；不要手改生成物。
完成后必须跑 verify / lint / auto_check，把逐项结果贴回来。
如果校验失败，先修到全 PASS，不要调整检查阈值。
```

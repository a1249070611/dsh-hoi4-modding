---
name: kiant-hoi4-planning
description: 大型 HOI4 mod 的分阶段规划：从想法拆到可验收的步骤、八阶段模板、每阶段的验收门槛、用 kiant_hoi4_plan 跟踪进度、避免半途返工。
---

# 规划

## 为什么需要

一个完整 mod 有几十到几百个内容单元，顺序错了会返工：

- 先写 300 个国策、最后才发现国家 TAG 没定义 → 全部 id 要改
- 先做界面、最后才补本地化 → 所有控件文本要重排
- 先追求美术、最后才校验 → 几十个文件路径错，逐个查要一天

规划的价值不是"显得有条理"，是把**不可逆的决策往前放**。

## 八阶段模板

`kiant_hoi4_plan action=init` 生成，也可以自定义。

| 阶段 | 目标 | 验收门槛 |
|---|---|---|
| s1 骨架 | 目录、descriptor、启动器能识别 | 启动器里能看到 mod |
| s2 设计 | 国家/时间线/核心机制写清 | ROADMAP 备注里有可执行的设计，不是形容词 |
| s3 内容 | 国策/事件/决议/科技落地 | `validate_mod` 0 error |
| s4 本地化 | 文本齐全 | 覆盖率 100%，无乱码 |
| s5 校验 | 深度检查清零 | `validate_mod deep=true` 0 error |
| s6 游戏内 | 真跑一遍 | `error.log` 无新增错误，关键内容可达 |
| s7 兼容 | 覆盖面清楚 | 无 `replace_path`，加载顺序已注明 |
| s8 发布 | 可分发 | 版本号、缩略图、更新日志齐 |

**s5 与 s6 不能合并。** 静态校验保证结构对，游戏内验证保证行为对。两者失败的原因完全不同：前者查括号和键，后者查触发条件与 AI。

## 怎么拆步骤

好步骤的标准：**能被一个明确的动作完成，且有可观察的结果**。

坏：「实现国策系统」
好：「为 GER 加 12 个国策，覆盖工业与外交两条线，坐标不重叠」

坏：「处理本地化」
好：「补齐 6 个国策的 `_desc` 键，运行 scan_localisation 无 missing」

拆到「一次会话能做完」的粒度最合适。太大容易半途而废，太小则规划成本超过收益。

## 用法

```json
{"mod_path": "...", "action": "init"}
```

自定义步骤：

```json
{
  "mod_path": "...",
  "action": "init",
  "steps": [
    {"id": "a", "title": "定义 GER 的 12 个国策", "accept": "坐标无重叠，全部有本地化", "depends": []},
    {"id": "b", "title": "写 3 个联动事件", "accept": "控制台 event 能弹出", "depends": ["a"]}
  ]
}
```

推进：

```json
{"action": "update", "step_id": "a", "status": "done"}
```

`status` 看进度和下一步。工具会算出「当前可做」的步骤——依赖全部完成的第一个 pending。

同时生成 `ROADMAP.md`，纯 Markdown 复选框，适合放进 git、给协作者看、或在 issue 里引用。

## 与其它工具的配合

每个阶段该调什么：

| 阶段 | 工具 |
|---|---|
| s1 | `kiant_hoi4_scaffold kind=mod` |
| s2 | `kiant_hoi4_kb_lookup` 看同类 mod 怎么做的 |
| s3 | `kiant_hoi4_scaffold` + 手写 + `kiant_hoi4_kb_lookup` 取结构 |
| s4 | `kiant_hoi4_scan_localisation` / `kiant_hoi4_fix_localisation` |
| s5 | `kiant_hoi4_validate_mod deep=true` |
| s6 | `kiant_hoi4_analyze_error_log` |
| s7 | `kiant_hoi4_list_overrides` |
| 随时 | `kiant_hoi4_preview` 看结构 |

## 常见规划错误

**一次规划 50 步。** 超过 15 步的计划基本不会被执行完。按模块分批，做完一批再规划下一批。

**没有验收标准。** 「完成国策」不算完成，「12 个国策都有本地化且坐标不重叠」才算。

**跳过 s2。** 设计没写清就开始写代码，写到一半改方向，之前的内容全废。s2 只需要一段文字，但能省几天。

**把 s6 当形式。** 静态校验全绿不等于游戏里能玩。触发条件恒假、坐标重叠、AI 永不走某条线，这些只有进游戏才发现。

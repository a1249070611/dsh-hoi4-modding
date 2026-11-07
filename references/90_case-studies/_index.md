---
title: 案例索引（真实项目实战记录）
domain: 90_case-studies
scope: index
verified_on: 1.19.x
verified_at: 2026-11-06
---

# 90_case-studies — 案例索引

> **这里全部是「某个真实 mod 的实战记录」，不是默认做法。**
> 通用规则、字段语义与推荐写法以 `01_script`–`07_tools` 各域文档为准；案例的价值在于：真实症状长什么样、当时怎么定位、哪个假设被实测推翻、修完怎么验证。读案例时先看它写于哪个版本、针对什么项目规模，再决定要不要照抄。

## 案例清单

| 案例 | 一句话摘要 | 适用场景 | 对应通用域 |
|---|---|---|---|
| [tech-tree-gridbox.md](tech-tree-gridbox.md) | 一个 2900 科技、多国专属科技页的 mod，科技树页面/连线/大小框的完整排障：gridbox 缺失为何静默、`available` 写法为何让连线全消失、拆页/合并页 6 步配方 | 科技页不显示科技、连线错乱或缺失、大框小框混用、`Found no grid box for tech` | 02_content（科技）、05_presentation（GUI/GFX） |
| [18-slot-tank-designer.md](18-slot-tank-designer.md) | 把坦克设计器从 9 槽改成 16/18 槽：槽位位置表、背景图固定尺寸（非九宫格）、槽位命名与蓝图容器匹配 | 增删装备设计器槽位、窗口高度不够、槽位重叠/无热区、每底盘不同槽位 | 03_military（装备/模块）、05_presentation（GUI） |
| [icon-pipeline-tech-card.md](icon-pipeline-tech-card.md) | 把照片/矢量图批量做成科技卡图标：去背（白底/棋盘格/保护白涂装）、别名表消歧、DDS 输出与卡片预览自检 | 批量出科技/装备 2D 图标、白底或棋盘格背景、图标偏左/被裁、同型号多名称 | 05_presentation（图标/DDS） |
| [vanilla-mod-survey.md](vanilla-mod-survey.md) | 对 23 个已发布工坊 mod 的只读调研：科技树过滤器、`duplicate_archetypes`、0 字节抹原版、scripted GUI 字段全集、顶栏挂法、性能门控 | 「这个需求原版/大型 mod 有没有做过」、找可抄的写法、判断某 API 是否真实存在 | 02–05 全域 + 07_tools |
| [agent-teams.md](agent-teams.md) | 多 agent 协作复盘：按文件所有权分工、写域隔离、单一生成器、非写者执行的验收 | 一个 mod 同时动「数据 + GUI + 图标 + 本地化 + 校验」多条线；需要并行又怕互相覆盖 | 06_workflow（流程）、本插件各域写域 |

## 使用建议

1. **先看结论再看配方**：每篇开头都有「适用」与「结论先行」，确认命中你的症状再往下读。
2. **不要照抄数字**：尺寸、槽位数、科技数都是那个项目的选择（例如 173×77、18 槽、2900 科技），通用推导在对应域文档里。
3. **注意版本**：案例记录的是一段时间内的行为（多为 1.19.3.x–1.19.4.x），引擎行为变化后以实测为准。
4. **案例里的工具名**：`_tools/*`、`_docs/*` 是原项目私有脚本；本插件对应实现是 `scripts/*.py`（`hoi4_lint.py`、`tech_tree_audit.py`、`item_sprite_check.py`、`errorlog_triage.py` …）。

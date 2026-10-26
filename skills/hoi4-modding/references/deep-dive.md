# 深度资料地图（何时读哪一篇）

本技能自带 `cheatsheet.md` 覆盖 90% 日常任务；遇到字段细节、边界情况、1.19 差异时按下表查。
**本机知识库根目录**（若存在）：

```
C:\Users\17876\Desktop\DeepseekHarness\钢铁雄心4
```

> 路径不存在时：以游戏自带 `E:\Steam\steamapps\common\Hearts of Iron IV\documentation\*.md` 为准（注意它不是全集），
> 并在游戏文件里 `grep` 至少两个真实用例确认写法。

## 一、通用与工作流

| 需求 | 文件 |
|---|---|
| 两个根目录、加载顺序、覆盖语义、校验和、日志、性能 | `knowledge/00_environment.md` |
| 从零建 Mod、发布创意工坊、兼容性、调试、迁移 | `knowledge/06_workflow/*.md` |
| 14 个任务配方（最常用） | `PLAYBOOK.md` |
| 网络资料与可信度 | `web_notes/SOURCES.md` |

## 二、脚本语言

| 需求 | 文件 |
|---|---|
| scope 类型、ROOT/FROM/PREV/THIS、迭代器 | `knowledge/01_script/scopes.md` |
| effect/trigger 求值模型、if/else、while、random_list、hidden_* | `knowledge/01_script/effects_triggers.md` |
| 变量、数组、`var:`、target、`check_variable` | `knowledge/01_script/variables.md` |
| 动态变量与 dynamic_modifiers | `knowledge/01_script/dynamic_variables.md` |
| scripted_effects / scripted_triggers / 参数化 | `knowledge/01_script/scripted_effects_triggers.md` |
| on_actions 类型、ROOT/FROM 语义、性能 | `knowledge/01_script/on_actions.md` |
| 数学函数、操作符、script_constants/enums | `knowledge/01_script/math_operators.md` |
| collections（集合） | `knowledge/01_script/collections.md` |
| 控制台命令与调试闭环 | `knowledge/01_script/console_commands.md` |

## 三、内容系统

| 需求 | 文件 |
|---|---|
| 国策树（含「一国一树」打分规则） | `knowledge/02_content/focus_trees.md` |
| 事件与事件链 | `knowledge/02_content/events.md` |
| 决议（category/decision/targeted/任务型） | `knowledge/02_content/decisions.md` |
| 理念与 idea 分类 | `knowledge/02_content/ideas.md` |
| 角色（领袖/顾问/将领/科学家） | `knowledge/02_content/characters.md` |
| 科技树与 technology_folders | `knowledge/02_content/technologies.md` |
| 国家历史、书签、开局设置 | `knowledge/02_content/history_countries.md` |
| MIO（军工组织） | `knowledge/02_content/mio.md` |
| 特殊项目 / 科学家 / 设施 | `knowledge/02_content/special_projects.md` |
| 外交、阵营、战争目标、和平会议 | `knowledge/02_content/diplomacy_wargoals.md` |
| 情报行动、突袭 | `knowledge/02_content/intelligence_operations.md` |
| 权力平衡 | `knowledge/02_content/balance_of_power.md` |
| 占领与抵抗 | `knowledge/02_content/occupation_resistance.md` |

## 四、军事与地图

| 需求 | 文件 |
|---|---|
| 单位/营/支援连 | `knowledge/03_military/units.md` |
| 装备、底盘、模块、升级 | `knowledge/03_military/equipment.md` |
| 师编制与 AI 模板 | `knowledge/03_military/division_templates.md` |
| 陆战/战斗数值/战术 | `knowledge/03_military/land_combat.md` |
| 海军 | `knowledge/03_military/navy.md` |
| 空军 | `knowledge/03_military/air.md` |
| 学说（1.19 重写后的五层结构） | `knowledge/03_military/doctrines.md` |
| 地图文件、省份、战略区、补给、地形 | `knowledge/04_world_map/*.md` |
| 州、建筑、资源 | `knowledge/04_world_map/states.md`、`buildings.md`、`resources.md` |

## 五、表现层

| 需求 | 文件 |
|---|---|
| GUI 基础（.gui 元素/定位/完整面板） | `knowledge/05_presentation/gui_basics.md` |
| scripted GUI 绑定/挂载/刷新 | `knowledge/05_presentation/scripted_gui.md` |
| GFX sprite、动画、DDS 格式 | `knowledge/05_presentation/gfx_sprites.md` |
| 肖像与旗帜命名/尺寸 | `knowledge/05_presentation/portraits_flags.md` |
| 本地化语法、颜色、loc formatter | `knowledge/05_presentation/localisation.md` |
| 中文字体/方框排查 | `knowledge/05_presentation/chinese_fonts.md` |
| 音频 | `knowledge/05_presentation/audio.md` |
| 地图模式/alerts/高级界面 | `knowledge/05_presentation/advanced_interface.md` |

## 六、示例与参考数据

| 资源 | 用途 |
|---|---|
| `example_mods/hello_hoi4/` | 入门全栈示例（LUX：国策/事件/决议/理念/角色/本地化/自绘图标） |
| `example_mods/advanced_systems/` | 进阶示例（IRE：动态变量/GUI/MIO/特殊项目/数组） |
| `reference/effects.json` | 全部 effect + 支持 scope + 示例 |
| `reference/triggers.json` | 全部 trigger + scope |
| `reference/modifiers.json` | 全部 modifier（含模板型） |
| `reference/console.json` | 控制台命令与可调参数 |
| `reference/CHEATSHEET_*.md` | 按 scope/分类的中文速查表 |
| `tools/build_reference.py` | 游戏更新后重新生成上述数据 |
| `tools/hoi4_lint.py` | 静态校验（本技能 `scripts/` 内有同款） |

## 七、权威来源与顺序

1. 本机 `documentation/*.md`（1.19.3 官方脚本参考）
2. 本机原版文件真实用例（`grep` 找 2 处以上，记下文件:行）
3. 官方 wiki / 官方论坛 patch notes（`web_notes/` 已整理）
4. 社区教程（仅作旁证，必须本地验证）

冲突时永远以「游戏文件 + 进游戏实测」为准；官方文档也会滞后（1.19 有多个未收录的可用关键字）。

---
title: 起步与环境（总览与索引）
domain: 00_start
scope: project
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - launcher-settings.json
  - hoi4_rev.txt
  - code_revisions.log
  - dlc_load.json
  - <USER_DIR>/launcher-v2.sqlite
  - <USER_DIR>/mod/*.mod
  - <WORKSHOP_DIR>/*/descriptor.mod
  - documentation/（12 个 *.md 全量 grep：无 mod 结构、无 load order 描述）
---

# 起步与环境（00_start）

> 版本口径：**1.19.x**（字段以游戏 `documentation/` 为准；本机实测于 **1.19.3 / 1.19.4**）

> 一句话定位：**先搞清"文件放哪儿、引擎怎么认、谁覆盖谁"，再写第一行脚本**。这三件事弄错，后面所有内容都会以"改了没反应"或"进游戏就崩"的形式报复回来。

本目录只讲**工程前提**，不讲内容怎么写：写国策/事件/科技看 [02_content](../02_content/_index.md)，写军事/地图数据看 [03_military](../03_military/_index.md) 与 [04_world](../04_world/_index.md)，写界面看 [05_presentation](../05_presentation/_index.md)。

## 文档清单

| 文档 | 一句话摘要 |
|---|---|
| [environment.md](environment.md) | 游戏根目录与用户目录（`Documents/Paradox Interactive/Hearts of Iron IV`）、`.mod` 与 `descriptor.mod`、`common/` 全景、`map/`+`history/` 关键文件、启动参数与控制台、日志位置、性能常识、10 步从零清单 |
| [mod-structure.md](mod-structure.md) | 一个完整 mod 的目录结构、描述文件六个字段的实测取值、`supported_version` 的真实语义（不是运行门槛）、DLC 默认只装资产而脚本留在主树用 `has_dlc` 门控、mod 可覆盖的 77 个域速览 |
| [load-order-and-override.md](load-order-and-override.md) | 三种覆盖机制（`replace_path` 整目录替换 / 同相对路径整文件覆盖 / 同 ID 覆盖）分别实证到什么程度、加载顺序能确认的只有"写出顺序"、以及一份别当事实用的未确认清单 |

## 五条最重要的结论

1. **两个根目录别混**：游戏目录只有只读内容；mod、存档、日志、`dlc_load.json`、`launcher-v2.sqlite` 都在用户目录下。技能里统一写成 `<GAME_DIR>` 与 `<USER_DIR>`。
2. **`supported_version` 不是运行门槛**：它只影响启动器/工坊的兼容提示，写 `1.19.*` 是为了让人看懂，不代表引擎会因此拒绝加载。
3. **官方对 mod 加载与覆盖零文档**：`documentation/` 12 个文件里 `replace_path|load order|mod folder` 的 grep 命中全是 effect/trigger 语义。所有关于"谁覆盖谁"的规则来源只能是原版实例与实测。
4. **覆盖是替换，不是合并**：`replace_path` 让原版整个目录消失；同相对路径是整文件覆盖；同 ID 是定义级覆盖且**不报错**。三条都会静默生效，冲突只能靠加前缀和自查避免。
5. **加载顺序只实证到"写出顺序"**：`dlc_load.json` 的数组顺序与启动器 playset 的 `position` 升序一致，但引擎是否据此决定优先级仍属**未确认**——写交付物时按"可能有序、不要依赖"处理。

## 与其它目录的边界

- 想知道**内容怎么写** → 02/03/04/05 域。
- 想知道**改完怎么证明没错** → [06_workflow/validation.md](../06_workflow/validation.md) 与 [07_tools/](../07_tools/_index.md)。
- 想知道**某个真实项目当初怎么踩坑的** → [90_case-studies/](../90_case-studies/_index.md)（实战记录，不是默认做法）。

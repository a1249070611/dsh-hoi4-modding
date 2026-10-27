# Changelog

## 1.1.2

- 发布通道切换为 **npm Trusted Publishing (OIDC)**：`release.yml` 去掉 `NPM_TOKEN` 依赖，改用 OIDC 发布并生成 provenance；
  README 的中英「Publishing」小节同步更新。技能内容与 1.1.1 相同（纯发布/文档变更）。

## 1.1.1

- 文档同步补丁：README 增加「Publishing」小节（2026 年可用 granular token 直发；**2027-01 起该方式移除**，
  改用 stage only + `npm stage publish` 或 GitHub Actions Trusted Publishing），CHANGELOG 记录同项。
  1.1.0 已包含全部功能与脚本，本版仅同步文档，避免 npm 包与仓库不一致。

## 1.1.0

科技树 UI 专题（来自一次 2900 科技/多国科技页大型 Mod 的真实排障，全部结论经游戏内对照实验验证）：

- **新增** `references/tech-tree-ui.md`
  - `technology_folders.available` 必须用 `original_tag`：用 `has_country_flag` 时引擎建页画线阶段的
    运行时二次求值失败，**整页连线被静默丢弃**（方框在、日志干净、旧存档正常而新开档必现）。
  - 大框/小框混排三件套：`force_use_small_tech_layout` + `techtree_<folder>_small_item` 模板 +
    `GFX_technology_<folder>_small_*_item_bg` **指向真正的小图**（模板 size 只管排版，贴图按像素绘制）。
  - 拆页/合并页 6 步配方、网格原点统一规则、跨页 path 不画线的必然性。
  - 三种调试手法：留痕法（改名 gridbox 判断页面是否被建）、对半分实验、对照探针。
- **新增脚本**
  - `tech_tree_audit.py`：科技页完整性审计（注册表 ↔ 页面/页签/item 模板/网格/科技/本地化）
  - `tech_folder_available.py`：`has_country_flag` → `original_tag` 批量迁移（check/apply/revert）
  - `item_sprite_check.py`：item 模板尺寸 vs 背景精灵实际像素（专治"小框显示成大框 + 偏位"）
  - `errorlog_triage.py`：error.log 分诊（科技树/贴图/scope/未知字段/本地化），并给出"日志干净即静默跳过"的判语
- **SKILL.md**：铁律新增 2 条（科技页可用性、大小框三件套）；排错表新增 3 行症状；验收清单新增 2 条；
  工具与配方索引补充新内容。
- README：脚本清单、更新记录（中英）。
- README：补充 npm 发布方式说明（2027-01 起 granular token 直发被移除，改用 stage only / Trusted Publishing）。

## 1.0.0

- 首个版本：HOI4 1.19.3 Mod 全流程技能（骨架/国策/事件/决议/理念/角色/科技/州/MIO/特殊项目/GUI/本地化/DDS/校验/安装/排错/发布）。

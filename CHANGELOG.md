# Changelog

## 1.2.0

坦克设计器 + 3D 模型 + 图标流水线专题（来自一次 30 科技德国坦克树 / 16 槽设计器改造的真实工程，
全部结论经游戏内对照验证）：

- **新增** `references/tank-designer.md`
  - 设计器文件地图：`interface/tank_designer_view.gui`（窗口 1091×542、`equipment_modules` 13/146 512×350、
    9 个 `pos_custom_module_slot_window_*`）、`equipmentdesignerview.gui`（槽位按钮模板 **76×47**）、
    每底盘蓝图 GUI（`equipment_designer_<底盘>` → archetype 回退）。
  - 数据侧：槽位 = `module_slots` 书写顺序；模块类别由 `category =` 隐式创建；装备可自定义 `module_slots`。
  - 16 槽布局（上 7 + 第二排 2 + 下 7，窗口不加高 542）完整坐标与取舍。
  - **窗口背景固定尺寸坑**：`GFX_tank_designer_popup_bg` 是 1092×553 贴图，只改窗口 size 会让内容溢出；
    给出“顶部原样 + 中间平铺 + 底部原样”生成加高 DDS 的配方。
  - 隐藏升级区/自动按钮的安全做法（position 移出屏幕；`auto_upgrade_button` 可能被代码自动摆放）。
- **新增** `references/tank-models-3d.md`
  - 四层链路 `graphic_db` → `entity`（`.asset`）→ `pdxmesh`（`.gfx`）→ `.mesh/.anim/.dds`；
  - 原版德国实体清单（`GER_iw/light/medium/heavy/super_heavy_armor_entity`）、特效节点
    `barrel`/`left_tracks`/`right_tracks`/`left_exhaust`/`right_exhaust`；
  - 复用原版 / 换贴图 / 自制 mesh 三条路线，导出器（Maya 官方、Blender 社区）与排错表。
- **新增** `references/icon-dds-pipeline.md`
  - 科技卡几何：183×84 卡、`Icon` 中心 x=74 → 内容右移 8px（左 20 / 右 4 / 上下 2，最大 149×73）；
  - 去背（透明/白底/8px 棋盘格）、白色涂装保护规则（亮度≥235 且 relY<0.8）、批量别名表、卡片预览自检、踩坑表。
- **新增脚本**
  - `tank_designer_probe.py`：设计器体检（窗口/槽位位置/槽位模板/背景 DDS 尺寸/模块类别/底盘 archetype 槽数/隐藏元素）
  - `tank_designer_layout.py`：从原版 GUI 生成自定义槽位布局（默认 16 槽紧凑版，支持 16-tall、背景 sprite 替换、dry-run）
  - `tech_icon_import.py`：照片/矢量图 → 173×77 DDS（去背 + 安全区 + 183×84 卡片预览，可调尺寸/边距）
- **文档补充**
  - `references/tech-tree-ui.md` 新增：多根分支 gridbox（一个页面多个 `_tree`）、生成文件被外部改写导致
    `Found no grid box` 的排查顺序；
  - `references/cheatsheet.md` 新增 §16：坦克设计器 / 3D 模型 / 173×77 图标速查；
  - SKILL.md 铁律 +2 条、配方索引 +3 行、排错表 +3 行、验收清单 +2 条。

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

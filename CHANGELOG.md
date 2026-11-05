# Changelog

## 1.4.1

打包与描述刷新（技能内容与 1.4.0 一致，没有新增/修改 references、scripts、SKILL.md）：

- **修复** npm 包体过大：`files` 白名单 `skills/**/*` 把 `.gitignore` 忽略的
  `scripts/__pycache__/`（6 个 .pyc）和 `scripts/.cache/vanilla_index.json`（6.9 MB）一起打进
  tarball —— 1.4.0 的包是 **1.4 MB / 41 个文件**（解包 7.3 MB）。
  改为显式白名单（`skills/hoi4-modding/SKILL.md`、`INSTALL.md`、`references/*.md`、
  `scripts/*.py`）后，1.4.1 是 **116 KB / 34 个文件**（解包约 325 KB），本机缓存与字节码不再分发。
- **更新** `README.md`：中英双版重写——能力面按 8 个领域重排、新增 14 个脚本与 10 篇
  references 的索引表、补全 1.2.0 / 1.3.0 / 1.4.0 变更、删掉重复且为空的 `## License` 标题，
  并写明市场条目、权限、依赖与发布方式。
- **更新** `package.json`：`description` 改为可核对的能力描述（一个技能 + 14 个 Python 工具 +
  23 个工坊 Mod 总览 + 多 agent 规范，不含游戏素材），`keywords` 补 `focus-trees`、`tech-tree`、
  `localisation`、`dds`、`cjk-fonts`、`agent-teams`。
- **更新** 对外简介文案：GitHub 仓库描述与主页、dsh-market 条目
  （`awesome-dsh-plugin` 的 `data/plugins/a1249070611__dsh-hoi4-modding.yml`）的中英文描述，
  与 1.4.x 实际能力一致；不夸大、不写营销词。
- **更新** `market/SUBMISSION.md`：上架流程已从「PR 改 README 加一行」变为「改自己的
  `data/plugins/<owner>__<repo>.yml`」，记录当前上架状态（条目已由维护者落到 main）与本次更新方式。
- **测试**：`npm test` 9 项全过；`npm pack --dry-run` 34 个文件，无 `__pycache__`/`.cache`。

## 1.4.0

23 个工坊 Mod（约 44 GB，只读）实测后的知识回灌：**推翻「中文乱码 = 字体 mod 冲突」的旧结论**，
补齐 scripted GUI 全字段/合法 token 表，并落地一个可进 CI 的字体体检脚本。

- **新增** `references/fonts-and-cjk.md` + `scripts/font_audit.py`
  - 根因：汉字只存在于 `interface/core_chinese.gfx` 的 `bitmapfont_override` 挂载的
    `gfx/fonts/chinese/<name>_Nof4` 分片；游戏全部 57 个 `.fnt` 自身 CJK 字形数为 0。
  - 因此**名字不在 override 名单里就必然 `????`**（`hoi_14mbs` 是典型），与装不装字体 mod 无关；
    两个字体 mod 同时启用时 `core_chinese.gfx` 整体替换，只有一个生效。
  - 给出 37 个安全字体名、场景选型表、自建 `bitmapfont_override` 的写法、排查顺序。
  - `font_audit.py`：读游戏 `core_chinese.gfx` 取真实名单，扫 Mod 的 `interface/**` 与 `gfx/**` 下
    所有 `font = "..."`，列出无中文分片的名字 + 行号；`--list-supported` / `--json`；退出码可进 CI。
  - **修正** `scripted-gui-and-topbar.md` §7 的旧表述（原写“字体 mod 下没有中文字形”，不准确）。
- **新增** `references/vanilla-mod-survey.md`
  - 23 个工坊 Mod 的规模表与技法矩阵，全部带 `文件:行号`：
    gridbox 当“画不画”过滤器（BI 2,480 科技只画 816）、`@` 宏排坐标、
    `duplicate_archetypes` 克隆底盘、0 字节文件抹原版、`gui_category` 分选择器、
    每底盘设计器美术三件套、`module_count_limit` 互斥、原生外壳 + 脚本 tab、
    顶栏三种挂法、每日钩子 `has_country_flag = player` 门控。
- **新增** `references/agent-teams-playbook.md`
  - 按“文件所有权”而非“功能”分工：survey（只读）/ build（写源码）/ audit（只写报告）；
    生成器单点写者、写域表、交接契约（必须有 `文件:行号` 与“不确定”一节）、并发读串行写、
    四种常见失败模式、两组最小提示词模板。
- **更新** `references/scripted-gui-and-topbar.md`
  - 新增 §9 字段全表 + **合法 `parent_window_token` 全表**（含 10 个 `tech_*_folder`）；
    新增 §10 `dynamic_lists` 三种用法；§11 开合与刷新三条硬事实（`should_be_open` 不存在、
    脚本窗口无自动互斥、`dirty` 不写就每 tick 重绘）；§12 原生外壳 + 脚本 tab（唯一能自动关闭的路）；
    §13 顶栏三种挂法。
- **更新** `references/tech-tree-ui.md` §11
  - gridbox 是“画不画”的开关；`@` 宏重排整代；多 root 必须各自声明 gridbox。
- **更新** `references/tank-designer.md` §10
  - `duplicate_archetypes`（BI）与 0 字节抹除（MD）两条克隆路线；
    `gui_category`（细 category 给槽位、粗 category 给选择器）；
    每底盘美术三件套缺一即无热区（TFR 实例）；`module_count_limit` 做同类唯一。
- **修复** `SKILL.md` 工具段中 4 处历史遗留的 `	`/`` 被写成真实制表符/换页符的路径。
- **测试**：smoke 增加字体参考/脚本、工坊总览、团队分工三组断言；`font_audit.py` 对示例 Mod 实测退出码 0。

## 1.3.0

scripted GUI / 顶栏按钮专题，以及 18 槽坦克设计器落档（来自一次“军官团右侧新增军械部门”的完整实战）：

- **新增** `references/scripted-gui-and-topbar.md`
  - 最小 4 文件结构、`containerWindowType` 限制（`windowType` 会报 `Failed to create containerWindowType`）；
  - 按钮 effect 必须为 `<按钮名>_click`，否则点击静默失败；
  - 顶栏新增按钮：`x=680 y=36`、底图补块用原版底板+右端斜角、信息栏右移、alerts 起始位右移；
  - 原生窗口自动关闭限制：无 `is_window_open` / 窗口 on_action，scripted GUI 不能自动互斥关闭；
  - 中文字体坑：`hoi_14mbs`/`hoi_24mbs` 在字体 mod 下显示 `????`，改 `hoi_16mbs`/`hoi_24header`；
  - 多行本地化必须 `loc_escape` 成 `
`，否则整份 yml 失效。
- **更新** `references/tank-designer.md`
  - 新增 **18 槽紧凑布局（7+4+7，窗口 542）**：第二排 col0/1/5/6，数据 `module_slots` 顺序 0..17。
- **更新** `scripts/tank_designer_layout.py`
  - 新增 `18-compact` 预设；位置生成函数支持 7/4/7。
- **测试**：smoke 增加 scripted GUI 参考与 18 槽预设检查。

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

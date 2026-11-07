---
title: 错题本索引（常见错误 → 标准化解决方案）
domain: 91_error-book
scope: index + 检索协议
verified_on: 1.19.x
verified_at: 2026-11-06
---

# 91_error-book — 错题本

> **这里不是教程，是病历。** 每条记录都来自一次真实的踩坑：当时看到什么症状、试了什么错的做法、根因到底是什么、最后怎么解决的。
>
> 用途只有一个：**下次遇到同样的症状，直接查到标准答案，不要再重新踩一遍。**

## 检索协议（遇到问题按这个顺序走）

```
1. 症状 → 本文件第 1 节「症状速查表」，按你看到的原文找
2. 命中 → 打开对应条目，跳到「标准化方案」直接执行
3. 未命中 → kb_search 全文检索本目录（中文子串可搜到）
4. 仍未命中 → 去 92_solutions/ 找思路，或按第 3 节格式新建一条
```

**先查这里，再看域文档。** 域文档讲「怎么写对」，错题本讲「这么写为什么错、错了长什么样」。症状描述比正确写法更容易匹配上你当前的处境。

## 一、症状速查表

按**你实际看到的东西**查，不按原因查。

### 界面 / 显示类

| 症状（原文或现象） | 条目 | 一句话原因 |
|---|---|---|
| 界面显示 `GFX_xxx` 或 `some_key` 原样文字 | [EB-001](EB-001-loc-key-shown-raw.md) | 本地化键缺失或 `.yml` 没 BOM |
| 中文全是 `????` | [EB-002](EB-002-chinese-question-marks.md) | 字体名/字重映射错，不是字形缺失 |
| 科技页方框都在、连线一条没有 | [EB-003](EB-003-tech-lines-silently-gone.md) | `technology_folders.available` 用了 `has_country_flag` |
| 国策树连线重叠、错位（**游戏内**） | [EB-004](EB-004-focus-tree-lines-overlap.md) | `x`/`y` 坐标跨层冲突或相对定位误用 |
| 国策树整棵树位置全乱（**离线预览/工具画的图**） | [EB-021](EB-021-focus-relative-position.md) | 工具没解算 `relative_position_id`，把 delta 当绝对坐标 |
| 图标被拉伸、偏左、被裁 | [EB-005](EB-005-icon-distorted-or-cropped.md) | 出图尺寸与槽位不符，或 DDS 头信息不对 |
| 顶栏/窗口挂不上自定义 GUI | [EB-006](EB-006-scripted-gui-not-mounting.md) | `containerWindowType` 的 name/positionType 不合约定 |

### 游戏内行为类

| 症状 | 条目 | 一句话原因 |
|---|---|---|
| 写了国策/事件/决议，游戏里完全不出现 | [EB-007](EB-007-content-not-appearing.md) | ID 撞车被覆盖，或缺 namespace |
| 事件不触发 | [EB-008](EB-008-event-never-fires.md) | `is_triggered_only` 没配 `mean_time_to_happen`，或 namespace 缺失 |
| 改了原版内容但没生效 | [EB-009](EB-009-override-not-taking-effect.md) | 用了 `replace_path` 整目录替换，或同名文件未覆盖 |
| 条件判断永远为假 | [EB-010](EB-010-trigger-always-false.md) | `has_dlc` 名字拼错，或 scope 不对 |
| 效果执行了但数值没变 | [EB-011](EB-011-effect-no-visible-change.md) | 作用域错（改的是错的 scope），或变量未初始化 |
| 音乐 mod 装了没声 / `play_song` 触发不了 | [EB-022](EB-022-music-mod-silent.md) | 歌没进 `.asset` 定义层；条件依赖别的 mod 的 flag |
| replace events 后间谍/核爆等系统事件失踪 | [EB-025](EB-025-replace-path-events-loss.md) | 整目录替换把原版系统事件一并退场，被引用的 namespace 要手动补回 |
| 「开关决策」点了没反应 / 效果强得离谱 | [EB-024](EB-024-idea-toggle-decision-dead.md) | idea 的 `allowed = { always = no }` 拦截了 `add_ideas`；或 modifier 量纲写错（0.1=10%） |

### 汉化 / 多语言类

| 症状 | 条目 | 一句话原因 |
|---|---|---|
| loc 全翻了，游戏里仍有英文（机构名/AI 战略/编制名） | [EB-023](EB-023-hardcoded-strings-in-common.md) | 部分展示文本硬编码在 `common/` 脚本里，必须覆盖 common 文件 |

### 日志 / 校验类

| 症状 | 条目 | 一句话原因 |
|---|---|---|
| `error.log` 里同一句话刷几千行 | [EB-012](EB-012-error-log-flood.md) | 一处根因被逐文件重复报告，先聚类再修 |
| error.log 干净但功能不对 | [EB-013](EB-013-silent-failure.md) | 引擎静默失败：覆盖、连线、图标都可能不报错 |
| `Unknown effect-type` / `Unknown trigger-type` | [EB-014](EB-014-unknown-effect-trigger.md) | 该 scope 下无此 effect/trigger，或拼写错 |
| `Invalid Scope, supported: ...` | [EB-015](EB-015-invalid-scope.md) | 当前 scope 类型不支持这个操作 |

### 工具 / 流程类

| 症状 | 条目 | 一句话原因 |
|---|---|---|
| 校验报大量假阳性，满屏红字 | [EB-016](EB-016-false-positive-validator.md) | 启发式判断把合法写法当错误（决策类别重名等） |
| 索引里查不到刚写的文件 / 来源路径是旧的 | [EB-017](EB-017-index-stale-path.md) | 索引是快照，不跟随文件变化；自己的 mod 默认不在索引里 |
| 工具报告"命令不存在" | [EB-018](EB-018-tool-command-missing.md) | 参考库描述的 CLI 与本插件 MCP 工具不是同一套 |
| 中文搜不到 / 搜到的全是无关的 | [EB-019](EB-019-chinese-multichar-search-miss.md) | 整句被当短语，虚词抢排序。改用关键词，空格分开 |
| 离线预览的国策树节点挤成一团 | [EB-021](EB-021-focus-relative-position.md) | 预览按绝对坐标画，没解算 `relative_position_id` |

> 校验器报出成百上千条错、你怀疑它乱报时，看 `EB-016`：哪些可以先忽略、
> 怎么确认是工具的问题而不是你的 mod 坏了。
> 校验器自己算错哪几行、索引怎么建的，记在 `99_plugin-devlog/` 里，
> 那是维护者才需要读的，写 mod 不用看。

## 二、按域归类

| 域 | 条目 |
|---|---|
| 本地化 / 编码 | EB-001、EB-002 |
| 科技树 | EB-003、EB-016 |
| 国策树 | EB-004、EB-007、EB-021 |
| 表现层（GFX/DDS/GUI） | EB-005、EB-006 |
| 内容系统 | EB-008、EB-011、EB-024 |
| 覆盖 / 加载顺序 | EB-009、EB-025 |
| 脚本语言 | EB-010、EB-014、EB-015 |
| 音频（sound/music） | EB-022 |
| 汉化 / 多语言 | EB-023 |
| 调试方法论 | EB-012、EB-013 |
| 工具行为（报错/检索/预览异常） | EB-016、EB-017、EB-018、EB-019、EB-021 |

## 三、新增条目的格式

**每次踩坑后立刻记，别攒。** 拖延会让"当时试过什么"这段彻底丢失，而那段恰恰最值钱——它防止你下次又走一遍同样的弯路。

文件命名：`EB-NNN-短横线症状.md`，NNN 三位递增，不复用编号。

```markdown
---
title: "EB-NNN 一句话症状"
id: EB-NNN
domain: 91_error-book
symptom_class: 界面显示 | 游戏内行为 | 日志校验 | 工具流程 | 功能不生效 | 汉化
severity: 阻断 | 严重 | 一般 | 轻微
verified_on: 1.19.x
verified_at: YYYY-MM-DD
first_seen: 哪个项目 / 哪个任务
related: [域文档路径]
---

# EB-NNN 一句话症状

## 症状

你实际看到什么。**贴原文**：报错行、界面上的错字、日志片段。
不要写"不生效"这种概括，写"国策树页面里方框都在，但一条连线都没有，error.log 无相关行"。

## 错误做法（我试过的）

按时间顺序列出走过的弯路，每条注明**为什么当时会这么想**。
这一段是错题本的核心价值——它记录的是思维陷阱，不是知识点。

1. 我以为是 X，于是做了 Y → 结果 Z（说明为什么这个假设错了）

## 根因

一句话说清机制层面的原因。能指到游戏文件行号就指。

## 标准化方案

可以直接照做的步骤。有命令就给命令。

```bash
# 具体命令
```

## 预防

写什么检查能提前拦住它。能挂到 `validate_mod` 的校验器上就说明挂哪个。

## 验证

改完怎么确认真的好了。给可观察的判据，不要写"进游戏看看"。
```

## 四、维护约定

- **编号只增不改**。修好了也留着，标 `status: resolved`，因为别人可能正在踩。
- **一条只讲一个错**。一个坑带出三个错，就拆成三条。
- **不写没有实证的条目**。听说的、猜的、从别处抄来未验证的，进 `92_solutions/` 而不是这里。错题本只收「我亲自踩过并解决了的」。
- **根因写不准就空着**。写"根因待查，现象如此"比编一个似是而非的原因好——编的原因会让后来者往错方向修。

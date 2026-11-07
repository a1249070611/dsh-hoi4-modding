---
name: kiant-hoi4-debug-validate
description: HOI4 调试与校验：-debug_mode 启动参数、控制台命令速查、error.log 精读、常见报错对照表、静态校验工作流，以及崩溃与静默失效的分诊路径。
---

# 调试与校验

## 打开调试能力

Steam → 库 → 右键 HOI4 → 属性 → 通用 → 启动选项，填：

```
-debug_mode
```

**证据**：游戏自带 `launcher-settings.json` 里 `alternativeExecutables` 有一项
`"label": {"en": "Open game in Debug Mode"}`，其 `exeArgs` 就是
`["-gdpr-compliant", "-debug_mode"]`。这是官方启动器自己的调试入口，照抄即可。

作用：写出完整 `error.log`、解锁控制台、允许 `nudge` 等调试命令。**不开调试模式时 `error.log` 几乎什么都不写**，这是很多人"日志是空的"的原因。

⚠️ 网上大量教程写 `-debug`。游戏 `documentation/triggers_documentation.md` 在 `is_debug` 词条里确实还写着"launched with -debug argument"，属于文档滞后。以启动器为准，用 `-debug_mode`。两个都填也不冲突。

崩溃定位另可加 `-crash_data_log`（社区常用，本插件的启动器清单里没有，未在本机验证）。

## 日志位置

```
文档/Paradox Interactive/Hearts of Iron IV/logs/
├── error.log      ← 主要看这个
├── game.log       ← 加载流程、mod 列表
└── ...
```

用 `kiant_hoi4_analyze_error_log` 不传路径时会自动在这几个常见位置找（含 OneDrive 重定向的情况）。

## 控制台常用命令

游戏中按 `~` 或 `§` 打开（需 `-debug_mode`）。

| 命令 | 用途 |
|---|---|
| `event mymod.1` | 直接触发事件，验证事件是否注册成功 |
| `decision GER_autobahn_program` | 执行决议 |
| `tag GER` | 切换国家 |
| `annex GER` | 吞并 |
| `pp 500` | 加政治点数 |
| `xp 500` | 加陆海空经验 |
| `research_on_icon_click` | 点科技图标直接完成 |
| `debug_mode` | 显示省份 id、州 id |
| `nudge` | 打开 GUI 编辑器，拖界面并导出坐标 |
| `reload_loc` | 重载本地化（部分版本可用，不确定时直接重启游戏） |
| `effect add_political_power = 50` | 在目标国作用域执行 effect |
| `trigger has_war = yes` | 检查 trigger 真假 |
| `yesman` | AI 全盘接受外交提议 |

`effect` 和 `trigger` 两个命令是排查逻辑的核心工具：把可疑的条件/效果单独拎出来执行，立刻知道真假。

## 先过滤，再修错

**`error.log` 里 95% 以上是原版自带的噪声**，跟你的 mod 一点关系没有。开着一堆 mod 启动一次，日志几万行是常态。

所以第一步不是"修第一个报错"，而是**只留与你相关的行**：

```bash
# 只留提到自己 mod 文件名或 ID 前缀的行（把 NS_ 换掉）
grep -nE "NS_|mymod" error.log | head -50

# 或者反过来，排除已知的原版噪声
grep -vE "common/(ai|countries|ideas|technologies)/" error.log | head -50
```

更可靠的做法是**只比"改动前后新增"**：改之前跑一次记下行数，改之后再看多出来的部分。`kiant_hoi4_analyze_error_log` 会按消息模板聚类，把 3 万行压成 20 条，先看它。

## 报错对照表

| error.log 消息片段 | 含义 | 处理 |
|---|---|---|
| `Invalid Scope, supported: Country, provided: None` | 这条 effect/trigger 不支持当前作用域，且此处根本没有对象 | 用 `TAG = { }` / `<state_id> = { }` 切 scope；查 `documentation/effects_documentation.md` 里该条的 scope 分节 |
| `Unknown effect-type` / `Unknown trigger-type` | 名字拼错，或该版本没有 | 对照 `documentation/` 与原版真实用例。**注意：它只报一行，所在块的后续兄弟节点仍会执行**，别以为整块都没跑 |
| `Unknown modifier` | 修正名拼错 | grep 原版同名字段的确切拼法 |
| `Invalid supported_version` | 版本号写法不合法，如 `"1.*"` | 通配符只能放最后一段，写 `"1.19.*"` |
| `Found no grid box for tech %s` | 科技没有对应的 gridboxtype | `technology_folders` 里补 gridbox 与 item 模板 |
| `Unexpected token` | 语法错误，多半括号/等号不配对；`.mod` 写 `thumbnail=` 也会报这个 | `kiant_hoi4_validate_mod` 定位文件与行号 |
| `Could not find sprite GFX_xxx` | sprite 未注册或名字不符 | 查 `interface/*.gfx`，注意前缀规则 |
| `Missing localisation key xxx` | 缺本地化键 | 补齐，注意 BOM |
| `Multiple definitions of xxx` | id 重复 | `kiant_hoi4_find_duplicate_ids` |
| `Invalid xxx value` | 枚举值写错（ideology、slot 名等） | 对照原版同名文件 |
| `Province N is not within specified state` | 省份与州归属不符 | 改地图或建筑位置时常见 |
| `Failed to load` / `Error loading` | 文件格式或路径问题 | 查路径大小写、BOM、编码 |

## 分诊路径

> **动手排查前，先查错题本。**
> 用 `kiant_hoi4_error_book query="你实际看到的现象"`——按**你看到的东西**查（报错原文、界面上的错字、缺了什么），不按原因查。
> 已知的 18 个坑都写好了根因和标准解法，比现场推理快得多。
>
> 命中就 `action=get id=EB-00X section="标准化方案"` 直接照做；没命中再走下面的分诊路径。
> 走完发现是新坑，**回头记一条 EB 条目**（格式见 `references/91_error-book/_index.md` 第三节）。
> 错题本也没思路时，`kiant_hoi4_solutions query="关键词"` 去翻未验证的思路池——注意看 `status`，那里每条都可能错。

**症状：游戏进得去，但我的内容完全不出现**

1. `kiant_hoi4_validate_mod` —— 先排除硬错误
2. 启动器里 mod 是否勾选启用
3. `game.log` 里搜 mod 名，确认它被加载了
4. 确认 `supported_version` 匹配
5. 内容本身：国策树有没有被国家认领？事件有没有 `add_namespace`？决议分类有没有本地化？
6. 详见 `EB-007`（内容不出现）、`EB-009`（覆盖没生效）

**症状：内容出现但显示问号/键名**

1. 缺 sprite → `error.log` 搜 `Could not find sprite`
2. 缺本地化键 → `kiant_hoi4_scan_localisation`
3. 编码不对 → 检查 BOM
4. 详见 `EB-001`（键名原样显示）、`EB-002`（中文问号——**注意这通常不是字库问题**）

**症状：逻辑不生效（点了没反应）**

1. effect 写进了 trigger 槽，或反之
2. 引用了不存在的 idea / flag / tech
3. id 被别处覆盖
4. `days_remove` 与 `complete_effect` 用错槽位
5. 详见 `EB-011`（效果执行了但数值没变）、`EB-010`（条件恒假）

**症状：日志干净但功能不对**

**这是最容易卡住的一类。** 不要继续翻日志，改走结构化校验：

1. `kiant_hoi4_validate_mod deep=true` 全类型校验
2. `kiant_hoi4_list_overrides` 查覆盖关系
3. `kiant_hoi4_preview` 离线看结构
4. 详见 `EB-013`（静默失败总纲）、`EB-003`（科技连线消失的典型例）

**症状：崩溃**

1. 看 `crashes/` 目录的时间戳，对上最近一次改动
2. 二分法：注释掉一半内容，看是否还崩
3. 常见元凶：改地图文件、`replace_path`、循环调用 `scripted_effect`

**症状：日志刷几千行同一句**

不要逐条读。`kiant_hoi4_analyze_error_log` 先聚类，把几万条收敛到几十类再动手。详见 `EB-012`。

## 静态校验工作流

这套顺序能拦掉 90% 的问题，代价几乎为零：

```
1. kiant_hoi4_scaffold         生成骨架（不手写）
2. 写内容
3. kiant_hoi4_validate_mod     必须 0 error
4. 进游戏 -debug_mode
5. kiant_hoi4_analyze_error_log 确认没有新增错误
6. 反复迭代
```

**每次改动后都跑第 3 步。** 攒 20 个文件再校验，错误会互相掩盖——比如一个未闭合的大括号会让其后所有内容都被判为异常。

## 怎么读校验结果

三级含义不同，处理顺序也不同：

| 等级 | 含义 | 处理 |
|---|---|---|
| `error` | 已确认的硬错误 | **必须清零**。进游戏一定静默失效 |
| `warn` | 可疑，但存在合法写法 | 逐条判断，多数要改 |
| `info` | 无法确认（通常缺原版索引） | 建完索引再看，多半会消失 |

`info` 不是"不重要"，是"工具没有证据"。最典型的是贴图/sprite 找不到：不索引原版就分不清是拼错还是原版本来就有。**先跑 `kiant_hoi4_kb_build` 索引原版，再重新校验**，很多 info 会自动升级成 error 或直接消失。

明细被截断时看三个字段：

| 字段 | 是什么 | 什么时候用 |
|---|---|---|
| `summary.breakdown` | **全量**分项（缺键 / 语法 / EOF 未闭合 / 其它），不受截断影响 | 判读"哪一类偏多"只能看这个 |
| `summary.by_check` | 每类的完整计数，不截断 | 看某类总量 |
| `shown_by_check` | 形如 `"localisation": "25/64035"` | 判断明细是否被截断 |

**不要用 `issues` 的长度做统计。** 那个列表已经按 `per_check` 每类截过，拿它数会得出假数字：原版实测 localisation 真实 2041 条，用截断列表数出来只有 400 条。

大模组嫌明细多，传 `per_check`（每类条数，默认 25）和 `max_issues`（总数，默认 200）调小。

## 校验器自身的可信度

`kiant_hoi4_validate_mod` 报的东西不一定都对。怀疑某个"错误"其实是原版的合法写法时，跑：

```
kiant_hoi4_self_check          # 把原版游戏目录当 mod 跑一遍
```

原版是"已知正确"的语料，它跑出成百上千条 error 只有一个解释——校验器判过头了，不是你的 mod 坏了。判据是**单向**的：

- 原版跑出大量 error → 大概率假阳性，可以先把这一类的报错放到一边
- 原版跑出 0 条 → 只说明没有系统性误报，**不保证查得全**，真问题还是得逐条看

判断某条报错该不该信、哪些可以先忽略，见 `kiant-hoi4-validator-trust` 技能。

## 排查重复定义时先问一句：真的重复吗

HOI4 里有些同名是**官方写法**，不要改：

| 现象 | 是不是 bug |
|---|---|
| 同一个 `decision_category = { ... }` 在几十个国家文件里出现 | 不是。引擎按名合并 |
| `scripted_effect` 同名 | 不是。子模组覆盖父模组的标准手段 |
| 同一个 `tech` id 在多个文件里定义 | **是**。后定义覆盖前定义，你在别处改的数值不会生效 |

最后一条是常见"我明明改了却没生效"的根因。

## 多人游戏注意

HOI4 的校验和包含所有已启用 mod 的内容。任何一方 mod 列表或版本不一致就无法联机。开发期做多人测试时，把 mod 打进压缩包分发，别指望"内容差不多就行"。

## 成就与铁人

启用任何 mod 都会禁用成就。想做"成就友好"的改动（纯界面、纯本地化）也不行——引擎层面直接判定。

# kiant-hoi4-modkit

**《钢铁雄心4》模组开发工具包**：一个模组工程师 agent、15 个技能、20 个工具，配一套以原版游戏为参照的知识库。

面向 HOI4 1.19.x（Operation Postern）｜纯 Python 标准库｜零依赖｜MIT

> 当前版本 **3.0.1**（2026-11-07 发布）。仓库：<https://github.com/Kiant98/dsh-hoi4-modding>
>
> 3.0 是一次结构性重写：参考库扩到 153 篇，校验器扩到十类，知识库支持平台/本地两级资料库，自检 311 项。

## 特性一览

| 能力 | 说明 |
|---|---|
| 静态校验 | 十类检查，error / warn / info 三级，每条带文件、行号和修法 |
| 知识库 | 索引原版游戏与随包参考库，SQLite + FTS5 全文检索，支持两级资料库 |
| 脚手架 | 12 类内容骨架，自动生成带 BOM 的本地化文件 |
| 离线预览 | 国策树自包含 HTML，自动解算坐标与前置连线 |
| 排障 | error.log 聚类、覆盖比对、重复 ID、错题本 24 条实证 |
| 规划 | 八阶段 ROADMAP，每阶段带验收标准 |
| 自检 | 311 项自检 + 17 个变异测试，文档数字与实际值双向核对 |

## 适合谁

- **第一次做 mod 的人**：按 [GETTING-STARTED.md](GETTING-STARTED.md) 走一遍，半小时拿到一个能进游戏的国策树。
- **正在维护大模组的人**：用 `kiant_hoi4_validate_mod` 把静默失败变成带行号的报告，用知识库查原版真实写法。
- **给 AI 客户端接工具的人**：这是一个完整的 MCP server + agent + 技能包，可接入 Claude Code、Cursor、Codex、WorkBuddy 等。

## 为什么做这个


Paradox 引擎的失败方式很讨厌：它不崩溃。

本地化文件少了 BOM，整个文件被忽略，界面显示 `GER_autobahn` 而不是文本。事件忘写 `add_namespace`，事件根本不注册。国策 id 撞了，其中一个被悄悄丢掉。effect 拼错，那一行被跳过，其余照常执行。这些都不报错，甚至不一定进 `error.log`。

另一半问题出在模型身上。`scripted_gui` 的字段、`archetype` 怎么挂模型、某个 effect 在 1.19 有没有改名，这些答案不在参数里，在原版文件里。让模型凭记忆直接写，拿到的文件语法挑不出毛病，字段名却根本不存在。

这个工具包的应对办法很朴素：把真实实现索引起来，写之前先查；写完用机器校验，而不是靠眼睛看。

## 闭环

```
索引原版  →  查真实实现  →  生成骨架  →  机器校验  →  离线预览  →  进游戏验证
    ↑                                                                  │
    └────────────────────  把结论记回知识库  ←────────────────────────────┘
```

## 三条规矩

### 知识只从正规渠道来

原版游戏自带的 `documentation/*.md`（8600 行 effects、7700 行 triggers）和 31 处域级 `_documentation.md` 是字段级的权威，全部进索引。没有官方文档的域（国策、理念、科技、装备、地图）以原版实例文件为准。第三方经验只当线索用，并且标明可信度分级，详见 [`references/AUTHORITY.md`](references/AUTHORITY.md)。

### 每条结论都能查到出处

说「这个 effect 存在」，给的是 `documentation/effects_documentation.md:2343` 和它支持的作用域；说「这个字段拼错了」，给的是文件和行号。不给「一般情况下」「社区常用」这种查不到的说法。

### 零经验也能上手

不用先学 Clausewitz 语法。工具生成的是能进游戏跑起来的骨架，校验器说的是人话（「第 42 行少一个右花括号，从这往后整个文件都会被忽略」，而不是 `unclosed block@42`）。第一次做 mod 的人按 [GETTING-STARTED.md](GETTING-STARTED.md) 走一遍，能拿到一个自己写的国策。

## 里面有什么

### 1. 参考库：153 篇（136 正文 + 17 索引）

`references/` 下 153 篇文档，136 篇是正文，17 篇是各域索引。按来源分六块：

| 来源 | 篇数 | 构成 |
|---|---|---|
| 上游知识域 | 63 | `00_start` 到 `06_workflow`，56 正文 + 7 域索引，一字未改 |
| 后加的知识域 | 29 | `07_tools` / `08` / `09` / `10` / `93_ecosystem`，24 正文 + 5 索引 |
| 案例区 | 6 | `90_case-studies`，5 正文 + 1 索引 |
| 错题本 | 25 | 24 条正文 + 1 索引 |
| 方案库 | 11 | 10 条正文 + 1 索引 |
| 根文件 | 5 | `_index`、`cheatsheet`、`README`、`ATTRIBUTION`、`AUTHORITY` |

上面六块加起来是 139 篇。另有 `99_plugin-devlog/` 14 篇，记的是开发这个插件本身踩的坑，
**不属于**给 modder 用的参考库。它用 `DEVB-` / `DEVN-` 前缀，和 `EB-` / `SOL-` 不共用序列，
检索时不会混进 mod 相关的条目里。

覆盖脚本语言、内容系统、军事、世界地图、表现层、工程流程六个主题域（`07_tools` 是工具类，不算主题域）。

```
references/_index.md          「我要做 X → 读哪一篇」，50+ 条路由
references/01_script/         scope / effect / trigger / 变量 / 集合 / on_actions
references/03_military/       陆海空、装备、编制、学说（本插件的校验器不覆盖这些域）
references/04_world/          州、战略区、建筑、资源、补给、地形、地图
references/90_case-studies/   真实项目实战记录（不是默认做法）
references/91_error-book/     错题本：24 条实证踩坑 → 标准化方案
references/92_solutions/      方案库：10 条未验证思路，按状态标记
```

这套文档不全是我写的。正文来自 MIT 许可的开源项目 `dsh-hoi4-modding`，一字未改；出处、许可、以及我核对过哪几条，见 [references/ATTRIBUTION.md](references/ATTRIBUTION.md)。

搬进来之前，我挑了几条会推翻本插件现有写法的结论，在真实文件上验了一遍：

| 上游结论 | 验证结果 |
|---|---|
| `.mod` 用 `picture=` 不是 `thumbnail=` | 本机 29 个真实 `.mod`：14 个用 `picture`，1 个用 `thumbnail` ✅ |
| `common/units/equipment/` 存在、`common/equipment/` 不存在 | 游戏目录实测 ✅ |
| 地形在 `common/terrain/00_terrain.txt`，不在 `map/terrain.txt` | 实测 ✅ |
| 启动参数是 `-debug_mode` 不是 `-debug` | 启动器 `launcher-settings.json` 的「以调试模式打开游戏」用的就是 `-debug_mode` ✅ |

### 2. 知识库：能学习，不只是能生成

把原版、已装模组、你的笔记索引成一个 SQLite 库。之后：

```
kiant_hoi4_kb_lookup kind=tech          → 取 3 个真实科技定义，带行号与代码
kiant_hoi4_kb_search "scripted_gui"     → 在 5000 个文件里定位
kiant_hoi4_kb_symbol name=GER_pz1_a     → 这个 id 在哪些文件里定义过
kiant_hoi4_kb_search "add_to_variable" kind=md   → 查游戏自带的字段级文档
```

游戏自带的 `documentation/*.md`（`effects_documentation.md` 8600 行、`triggers_documentation.md` 7700 行）和 `common/**/_documentation.md`（实测 31 处，参考库写的 39 是把 `documentation.md` 也混算了）同样进索引，检索结果带 `authority` 标注：`game-doc` > `domain-doc` > `vanilla-instance`，冲突时按这个顺序取信。

还有一层。`documentation/` 里每个 `## name` 会被抽成符号，于是「这个 effect 到底存不存在」可以一条命令回答：

```
kiant_hoi4_kb_symbol name=add_to_variable
→ effect, documentation/effects_documentation.md:2343, Supported Scopes: any
kiant_hoi4_kb_symbol name=add_stabiltiy
→ found: false        ← 拼错了
```

实测抽出 553 个 effect、596 个 trigger，544/553 带作用域。

本地化默认只索引 `english` + `simp_chinese`。原版带 10 种语言、每种约 13 万条，全存是 130 万行 / 350 MB / 9 分钟，而其中九成永远不会被查。收窄到两种之后是 26 万条 / 108 MB / 73 秒。要全量传 `loc_langs: []`。

实测索引原版 1.19.4.2：6167 个脚本文件、6.2 万符号、26 万词条、16 秒。

### 3. 校验：十类检查，可插拔

```
kiant_hoi4_validate_mod deep=true
```

| 检查 | 内容 |
|---|---|
| 描述文件 | 两个 descriptor、`path` 解析与 ASCII 检查、`picture`/`thumbnail`、BOM、`replace_path` 双写、版本格式 |
| 本地化 | BOM、编码、语言头、重复键、缺键（精确到引用位置） |
| 语法 | 括号配平、token 错误、未闭合块 |
| 重复 id | 国策/精神/决议/事件/科技/角色，跨文件 |
| 科技 | 前置与依赖目标是否存在、本地化齐不齐 |
| 资产 | 贴图与 `.mesh` 文件是否真的存在 |
| 图标 | 国策/精神/决议/事件引用的 sprite 能否解析 |
| 界面 | `.gui` 语法、窗口重名、sprite 引用 |
| 框架 | `on_actions` 引用的事件、`oob` 文件、`add_ideas`、`defines` 前缀 |
| 音乐 | `play_song`/电台选曲引用的歌曲是否已进 `.asset` 定义层、音频文件是否存在、非 ogg 混入（EB-022） |

结果带 `file`、`line`、`hint`。`hint` 说的是「为什么会这样」和「怎么改」，不是「请检查语法」。

分级不是拍脑袋定的，每条结论都要区分「我确认了」和「我猜不了」：

| 等级 | 含义 |
|---|---|
| `error` | 已确认的硬错误，进游戏一定静默失效 |
| `warn` | 可疑，但存在合法写法 |
| `info` | 无法确认，通常是没有索引原版/父模组 |

举个具体的。模组引用 `gfx/leaders/leader_unknown.dds` 但自己没带这个文件。索引了原版，能查证，报 `error`；没索引，那文件很可能就在原版里，硬报 error 等于冤枉每个复用原版素材的模组，所以降为 `info` 并说明原因。同理，一个只翻了 40% 的汉化子模组缺五万个键是事实，但缺的键由父模组提供，于是键数够多且覆盖率低于七成时自动按「翻译子模组」处理，只给一条覆盖率摘要。

这套降级规则是被真实大模组压出来的。最初一跑 7 万条 error，其中 99% 是假阳性。一路收敛下来，同一批文件只剩两位数，而且每条都能点开核实。

加一类新检查是三步：写个函数、加个装饰器、完事。见 [ARCHITECTURE.md](ARCHITECTURE.md#扩展点)。

### 4. 预览：不开游戏看结构

```
kiant_hoi4_preview
```

生成一个自包含 HTML：国策树按真实 x/y 坐标渲染并画出前置连线，事件/决议/精神卡片带已解析文本，本地化覆盖率与问题清单一并呈现。

零外部依赖，九 KB，双击就开。坐标重叠、图标缺失、文本没写，在这个阶段就能看出来。

### 5. 规划：不让长任务跑偏

```
kiant_hoi4_plan action=init     → 八个阶段，各带验收标准
kiant_hoi4_plan action=status   → 进度、下一步、依赖是否满足
```

同步写 `ROADMAP.md`，纯 Markdown 复选框，能进 git，也能给协作者看。

## 快速开始

**第一步：获取代码**（两种方式，内容一致）

```bash
# 方式一：克隆仓库
git clone https://github.com/Kiant98/dsh-hoi4-modding.git kiant-hoi4-modkit
cd kiant-hoi4-modkit

# 方式二：从 Releases 下载 kiant-hoi4-modkit-3.0.1.zip，解压后进入目录
```

**第二步：确认工具与知识库状态**

```bash
python mcp-server/server.py --list                              # 列出 20 个工具
python mcp-server/server.py --call kiant_hoi4_kb_stats '{}'     # 看知识库是否已建
```

**第三步：建立索引**（首次约 30 秒，之后走增量）

```bash
python mcp-server/server.py --call kiant_hoi4_kb_build '{"action":"discover"}'   # 先看能索引什么
python mcp-server/server.py --call kiant_hoi4_kb_build '{"action":"build"}'      # 建库
```

**第四步：接入你的客户端**

本工具包刻意不预置会自动加载的 MCP 配置。复制 [platform/README.md](platform/README.md) 里的配置片段，粘到你信任的位置即可；Claude Code、Cursor、Codex、WorkBuddy 和任何支持 stdio 的 MCP 客户端都适用。

零经验用户请接着读 [GETTING-STARTED.md](GETTING-STARTED.md)：从空目录到第一个可进游戏的国策，全程有命令和预期输出。

## 资料库：平台优先，本地兜底

知识分成两级，检索默认先查平台库。

| 层级 | 内容 | 谁维护 | 什么时候建 |
|---|---|---|---|
| 平台资料库 | 作者发布的知识（字段说明、坑、版本差异） | 作者，不定期更新到开源平台 | `kiant_hoi4_kb_sync action=pull` |
| 本地资料库 | 原版游戏索引、随包参考库、你的笔记、点名的本地目录 | 你自己 | `kiant_hoi4_kb_build`（默认只建原版 + 参考库） |

```bash
# 拉平台库
kiant_hoi4_kb_sync action=pull

# 建本地库（原版 + 参考库，20 秒）
kiant_hoi4_kb_build action=build

# 想让它读你某个文件夹时，点名给路径。工具不自己扫目录
kiant_hoi4_kb_build action=build local_dirs=["D:/我的笔记","D:/旧mod文档"]
```

### 检索层级

`kiant_hoi4_kb_search` 的 `scope` 参数控制查哪一级：

| scope | 行为 |
|---|---|
| `auto`（默认） | 先查平台库；命中就返回并提示「本地库未检索」；没命中才退到本地库并说明「以下来自本地」 |
| `platform` | 只查平台库。想知道「作者到底怎么说」时用 |
| `local` | 只查本地库。查你自己的笔记、原版实例时用 |
| `all` | 两级都查，平台库的结果排在前面 |

返回里带 `answered_from`、`tiers`（各级命中数）、`message`（这次为什么给了这个层级的结果），不用你猜数据从哪来。

### 平台库怎么同步

`knowledge/remote.json` 填一次仓库名：

```json
{ "repo": "用户名/仓库名", "branch": "main", "paths": ["knowledge/notes", "references"] }
```

之后三条命令：

```
kiant_hoi4_kb_sync action=status   → 本地 2026.11.06 / 远端 2026.11.06-2 / 过期 true
kiant_hoi4_kb_sync action=pull     → 下载约 1 MB，缓存到 ~/.kiant-hoi4-modkit/remote/
kiant_hoi4_kb_build action=build   → 多出一个 remote 源，检索即可命中
```

`pull` 是幂等的，版本一致直接返回 `skipped: true`。断网时不动缓存，检索继续用旧数据，并在返回里写明是哪一版。

### 作者侧

仓库布局、`manifest.json` 格式、发布流程、自查清单见 [PUBLISHING-KB.md](PUBLISHING-KB.md)。

流程本身很轻：改完知识，把 `manifest.json` 的 `version` 改掉，push。插件不需要你构建任何产物。

本地与 WorkBuddy 资料库怎么保持一致（本地优先、格式一致、旧版归档、双向核对）见 [PUBLISHING-LIBRARY.md](PUBLISHING-LIBRARY.md)。

### 为什么 SQLite 不随包走

| 原因 | 具体 |
|---|---|
| 体积 | 131 MB，比插件本体大一两个数量级 |
| 绑机器 | 里面是作者那台机器的游戏文件路径、行号、mod 列表 |
| 是派生物 | 从游戏安装目录索引出来的，换台机器重跑一遍就有 |

远端仓库里只放知识（markdown，约 1 MB），不放游戏索引。

### 没建索引也能用，但会告诉你缺了什么

校验结果里有一块 `summary.index`：

```json
{
  "vanilla_indexed": false,
  "kb_loaded": false,
  "degraded": ["assets", "sprites", "technology", "history"],
  "hint": "尚未建索引：这四类检查只做到「文件存在」…跑一次 kiant_hoi4_kb_build action=build 即可"
}
```

留这块是有原因的。没有它，新用户看到「0 error」就以为全查过了，实际上四类检查整段降级。这正是本插件一直在批评的那种静默失败，不能自己犯。

### 首次建索引只收三样

```bash
python mcp-server/server.py --call kiant_hoi4_kb_build '{"action":"build"}'
```

```
vanilla   原版游戏 6167 个文件      ← 一手事实，所有校验的参照物
refs      参考库 153 篇（63 篇上游 + 6 篇案例 + 5 篇根文件 + 79 篇自建），随插件走，开箱就有
notes     本机笔记
```

第三方模组默认不收。装了 40 个工坊模组时全收进来，首次索引会从 20 秒变成几十分钟，半成品和纯汉化包还会把检索结果搅浑。要用就显式点名：

```bash
... '{"action":"build","include_mods":true}'      # 全部
... '{"action":"build","only":"mod:我的模组"}'    # 单个
```

`action=discover` 会列出所有能发现的模组并标 `opt_in: true`，方便挑。

## 自检与压力测试

改过核心模块就跑一遍，比手点工具可靠：

```bash
python mcp-server/selftest.py                 # 311 项断言，十七组：解析/校验/规划/预览/脚手架/知识库/协议/远端/两级/错题本/状态/文档一致性/独立工具/本地化真实写法/条件块/原版宽容度
python mcp-server/bench.py <模组路径>          # 在真实模组上量耗时，顺便看假阳性
```

`selftest.py` 里带一份 `examples/broken_mod/`：一个故意写坏的模组，注入 18 处经典缺陷（丢 BOM、少括号、id 撞车、事件忘 namespace、贴图不存在、版本号写 `1.19.x`……）。自检逐条断言其中 14 处被对应检查逮住，且等级正确。想确认某个检查是不是真在工作，去看它就行。

### 一个完整回合

```
用户：给 GER 加一条工业国策线，6 个国策，然后看看效果

agent → kiant_hoi4_kb_lookup kind=focus           看原版国策树结构
      → kiant_hoi4_scaffold kind=focus            建第一个，自动带本地化
      → 写入其余 5 个，坐标与前置连好
      → kiant_hoi4_validate_mod deep=true         0 error
      → kiant_hoi4_preview                        生成 HTML，发现第 3、4 个坐标重叠
      → 修正坐标，重新校验
      → 报告：改了哪些文件、树长什么样、还剩什么没做
```

## 工具

| 工具 | 用途 |
|---|---|
| `kiant_hoi4_self_check` | 体检校验器本身：把原版当 mod 跑一遍。改完校验逻辑先跑它，原版跑出成百上千条 error，唯一解释是校验器错了 |
| `kiant_hoi4_validate_mod` | 结构体检，`deep=true` 启用全部校验器；`per_check`/`max_issues` 控明细条数 |
| `kiant_hoi4_scaffold` | 生成 12 类内容骨架，自动带 BOM 本地化 |
| `kiant_hoi4_scan_localisation` | 专查本地化层 |
| `kiant_hoi4_fix_localisation` | 补 BOM、GBK→UTF-8 |
| `kiant_hoi4_find_duplicate_ids` | 查重复定义 |
| `kiant_hoi4_parse_script` | Clausewitz → JSON，支持下钻 |
| `kiant_hoi4_analyze_error_log` | 日志聚类分类 |
| `kiant_hoi4_error_book` | 按现象查错题本（24 条实证踩坑，带根因与修法） |
| `kiant_hoi4_solutions` | 查方案库（10 条带 status 的未验证思路） |
| `kiant_hoi4_list_overrides` | 覆盖范围比对 |
| `kiant_hoi4_kb_build` | 建/更新索引 |
| `kiant_hoi4_kb_search` | 全文检索 |
| `kiant_hoi4_kb_lookup` | 取真实范例 |
| `kiant_hoi4_kb_symbol` | 追符号定义 |
| `kiant_hoi4_kb_note` | 补充本地笔记 |
| `kiant_hoi4_kb_sync` | 平台资料库同步（status / pull，默认离线） |
| `kiant_hoi4_kb_stats` | 索引现状 |
| `kiant_hoi4_preview` | 生成离线 HTML |
| `kiant_hoi4_plan` | 分阶段跟踪 |

## 技能（15）

`mod-skeleton` · `clausewitz-script` · `localisation` · `focus-tree` · `events-decisions` · `technology` · `models-3d` · `ui-interface` · `game-framework` · `gfx-interface` · `debug-validate` · `compat-release` · `knowledge-base` · `planning` · `validator-trust`

按需自动触发。写的是「哪里会出错」和「怎么判断」，不是教程。

## 目录

每个文件、每个文件夹干什么用，见 [STRUCTURE.md](STRUCTURE.md)：一页看完，含分层图、逐文件说明、以及「想改东西时改哪」。这里只给树。

```
kiant-hoi4-modkit/
├── plugin.json              跨平台能力清单（版本/技能/工具/资源的唯一真相来源）
├── README.md                本文件
├── STRUCTURE.md             组织架构：每层每文件干嘛用 + 改东西时改哪
├── ARCHITECTURE.md          五层架构、数据流、扩展点
├── GETTING-STARTED.md       零经验走通第一个国策
├── PUBLISHING-KB.md         作者侧：怎么把知识库发布到开源平台
├── PUBLISHING-LIBRARY.md    作者侧：本地与资料库怎么保持一致（本地优先/格式一致/旧版归档）
├── agents/kiant-hoi4-modder.md    全生命周期 agent 定义
├── skills/                  15 个技能，各一个文件夹
├── mcp-server/              零依赖 Python，12 个模块
│   ├── server.py            20 个工具 + MCP 协议
│   ├── checks.py            结构校验
│   ├── kb.py                知识库索引与两级检索
│   ├── cw.py                Clausewitz 解析器（地基）
│   ├── validators.py        8 个可插拔类型校验器
│   ├── playbook.py          错题本与方案库检索
│   ├── preview.py           离线预览渲染
│   ├── scaffolder.py        12 类骨架生成
│   ├── remote.py            远端知识库同步
│   ├── planner.py           分阶段规划
│   ├── selftest.py          311 项自检
│   └── bench.py             真实模组压力测试
├── references/              153 篇，16 个目录（上游 MIT + 自撰 + 自建）
│   ├── _index.md            总路由：「我要做 X → 读哪一篇」
│   ├── 00_start … 07_tools      七个知识域 + 工具，63 篇上游
│   ├── 07_tools             上游 CLI 用法 ⚠ 本插件无此命令，见 EB-018
│   ├── 90_case-studies      真实项目实战记录（不是规范）
│   ├── 91_error-book        24 条实证踩坑 → 标准化方案
│   ├── 92_solutions         10 条未验证思路（按状态标记）
│   └── README / AUTHORITY / ATTRIBUTION / cheatsheet
├── knowledge/
│   ├── notes/               你的笔记，会被索引
│   ├── sources.example.json 固化索引源的样例：复制成 sources.json 再改
│   ├── sources.json         实际生效的索引源（你自己建，含本机路径，已 gitignore）
│   └── remote.json          远端知识库仓库配置
├── platform/                各客户端接入（手动粘贴，不预置自动加载）
└── examples/
    ├── sample_mod/          可运行正例：0 error，自检基准
    └── broken_mod/          故意写坏的反例：18 处缺陷，14 处有断言
```

## 边界

### 哪些工具只读，哪些会写

20 个工具里 13 个只读。会写盘的那几个，写哪里写在明面上：

| 工具 | 写盘 | 写在哪 |
|---|---|---|
| `kiant_hoi4_self_check` | — | 只读（跑完不改任何文件） |
| `kiant_hoi4_validate_mod` | — | 只读 |
| `kiant_hoi4_scan_localisation` | — | 只读 |
| `kiant_hoi4_find_duplicate_ids` | — | 只读 |
| `kiant_hoi4_parse_script` | — | 只读 |
| `kiant_hoi4_analyze_error_log` | — | 只读 |
| `kiant_hoi4_list_overrides` | — | 只读 |
| `kiant_hoi4_kb_search` / `lookup` / `symbol` / `stats` | — | 只读 |
| `kiant_hoi4_error_book` / `solutions` | — | 只读，每次现读 md 文件，不依赖已建索引 |
| `kiant_hoi4_kb_build` | ✅ | `~/.kiant-hoi4-modkit/kb.sqlite`（不在游戏目录，也不在 mod 目录）。`action=discover` 时纯只读 |
| `kiant_hoi4_kb_sync` | ✅ | `~/.kiant-hoi4-modkit/remote/`（远端知识的缓存）。`action=status` 时纯只读；只有 pull 会联网 |
| `kiant_hoi4_kb_note` | ✅ | 同上，只往数据库加笔记 |
| `kiant_hoi4_preview` | ✅ | 默认 `<mod>/.modkit/preview.html`。不想让 mod 目录多东西就传 `out_path` 指到别处 |
| `kiant_hoi4_plan` | ✅ | `<mod>/.modkit/plan.json` + `<mod>/ROADMAP.md` |
| `kiant_hoi4_scaffold` | ✅ | `<mod>/` 下新建内容文件 |
| `kiant_hoi4_fix_localisation` | ✅ | 会改 `<mod>/localisation/*.yml` 的编码与 BOM。默认 `dry_run=true` 只报告 |

`.modkit/` 是工具自己的元数据目录，HOI4 不会加载它（引擎只读白名单目录）。但如果你希望 mod 目录保持纯净，预览用 `out_path` 外指，计划用 `kiant_hoi4_plan` 时避开。

游戏安装目录永远是只读的，没有任何一行代码会写 `<GAME_DIR>`。

### 其他

不运行游戏。所有检查都是静态的，平衡性、AI 行为、实际手感只能进游戏测。

不生成 3D 模型。`.mesh` 是二进制，需要 Blender + Paradox 导出插件，平台只校验引用路径。

不联网。工具只读本地文件。查 Wiki/GitHub 由 agent 自己去做，结论可以存回本地知识库。

不自动执行。没有预置会自动加载的 MCP 配置、hook 或安装脚本。接入要你手工粘贴配置，这几行值得亲自看一眼。

版本绑定 1.19。1.20 若改了 effect 名，校验器不会自动知道，但日志分析仍能发现 `invalid`；参考库的 `06_workflow/migration.md` 有升级清单。

effect/trigger 名能查但不自动报。名字表从游戏 `documentation/` 抽出来了（553 + 596 条），`kiant_hoi4_kb_symbol name=xxx` 一条命令能确认存在性与支持的作用域。但不做成自动扫描，因为判断「这个键是 effect 调用还是结构字段」需要完整语义表，猜错就会刷出几万条假阳性。宁可让 agent 主动查。

军事、地图、字体只做浅检查。校验器能查「引用的文件存不存在」，查不出「字段填得对不对」。这些域的字段清单在 `references/03_military`、`04_world`、`05_presentation`。

## 开发状态

框架已完成，并在真实数据上跑过：

| 对象 | 规模 | 索引 | 校验 | 结论 |
|---|---|---|---|---|
| `examples/sample_mod` | 10 文件 | — | 0.1 s | 0 error |
| `examples/broken_mod` | 12 文件 | — | 0.1 s | 18 处注入缺陷，14 处断言全命中 |
| 原版 vanilla 1.19.4.2 | 6167 文件 / 26 万词条 / 50 篇官方文档 | 16 s | — | 553 effect + 596 trigger 可查 |

311 项自检全绿，覆盖解析器、示例模组、错误夹具（12 处缺陷断言全命中）、规划器、预览（含国策坐标解算）、脚手架、知识库、MCP 协议握手、远端同步、两级资料库、错题本与方案库检索、平台状态提示、组织架构文档与实际一致、独立工具（DDS 头部与块数取整、lint 三类错误与误报边界）、条件块采集、原版真实写法的宽容度。

## 校验器可信到什么程度

工具报的错，你能信几分？这个问题有实测答案。

把原版游戏（已知正确）当 mod 喂给校验器，看它冤枉多少条。1.19.4.2 上跑完是
1838 条 error，其中绝大多数是原版真实的本地化缺失（1000 多个 idea 待在
`hidden_ideas` 里，玩家看不到）。

这个数字本身就是结论：**校验器的严格度上限是引擎的严格度，超出去的部分全是误报。**
1 万条 error 没人会看，等于没检查。

所以遇到满屏红字时，先按这个顺序判断：

| 情况 | 判断 | 怎么做 |
|---|---|---|
| 报的东西原版里也这么写 | 大概率误报 | 暂时忽略，但记下来 |
| 只在你文件里出现 | 真问题 | 按报错改 |
| 分不清 | 查错题本 | `EB-016`，按假阳性类型列了对照表 |

`kiant_hoi4_self_check` 可以一条命令把原版当模组跑完，按类给出「这像不像误报」的判读。
自己动手确认的话，这样跑：

```python
import checks, kb
van = kb.find_game_dir()
r = checks.validate_mod(van, per_check=100000, max_issues=100000)
print(r["summary"]["breakdown"])
```

判据是单向的：原版跑出大量 error，说明有系统性误报；原版跑出 0 条，只说明没有
系统性误报，**不保证查得全**。

工具内部怎么修的、每一版降了多少条，记在 `references/99_plugin-devlog/`，
那是改这个插件的人需要读的，用插件的不用看。

## License

MIT。文本、agent、代码都可以改、商用、闭源分发，保留版权声明即可。

Hearts of Iron IV 是 Paradox Interactive AB 的商标。本项目是非官方社区工具，与 Paradox 无关联。
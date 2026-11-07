# 架构

这份文档讲 `dsh-hoi4-modding` 怎么组织起来，以及怎么往上加东西。如果你只想知道怎么用，去看 README。

想知道「哪个文件干什么」，去看 [STRUCTURE.md](STRUCTURE.md)。那份是清单。这份讲设计理由：为什么这样分层，为什么有些东西故意不做。

## 一句话

把「凭记忆写 HOI4 模组」换成「查真实实现 → 生成 → 机器校验 → 离线预览 → 进游戏验证」这条链路。

## 五层

```
┌─ L4 编排 ─────────────────────────────────────────────┐
│  agent（工作流与纪律） + 15 个技能（领域知识）           │
│  references/（163 篇：上游 + 自撰 + 错题本 + 方案库，读用）   │
├─ L3 能力 ─────────────────────────────────────────────┤
│  MCP 工具层：20 个工具，stdio JSON-RPC                    │
│  检索 / 校验 / 生成 / 预览 / 规划 / 日志 / 覆盖 / 错题本   │
├─ L2 分析 ─────────────────────────────────────────────┤
│  checks.py（结构）  validators.py（按类型可插拔）        │
│  kb.py（索引与检索） playbook.py（错题本/方案库）        │
│  preview.py（渲染） planner.py（规划）                  │
├─ L1 解析 ─────────────────────────────────────────────┤
│  cw.py  Clausewitz 词法/语法 → 带行号的 AST             │
│  yml 解析 / .asset / .gui / .lua / documentation 抽取   │
├─ L0 数据 ─────────────────────────────────────────────┤
│  文件系统（mod / 原版 / 笔记） + SQLite FTS5 索引        │
└───────────────────────────────────────────────────────┘
```

依赖是单向的：上层调下层，下层不知道上层存在。`cw.py` 不知道有 MCP，`kb.py` 不知道有 agent。

`references/` 是个例外。它是纯文本，不参与运行，只被 agent 和技能按需读。放在 L4 是因为它服务判断，不服务执行。它也不进模型上下文：163 个文件按索引路由，读到哪篇算哪篇。错题本和方案库另说，那两个由工具按症状定向检索，不靠逐篇读。

## 数据流

**学习阶段**

```
原版 + 已装模组 + 笔记
   ↓ kb.build()  遍历 → 解析 → 抽符号/词条 → 写库
SQLite（symbols / loc / code FTS / text FTS）
   ↓ kb.lookup() / search() / find_symbol()
真实代码范例 → agent 照结构写新内容
```

**查证阶段**（回答「这个 effect 到底存在吗」）

```
documentation/effects_documentation.md
   ↓ _extract_engine_docs()  每个 `## name` 一条，作用域来自正文
symbols(kind=effect|trigger|modifier, extra=Supported Scopes)
   ↓ kiant_hoi4_kb_symbol name=xxx
「存在，COUNTRY 作用域，文档 2343 行」 或 「不存在，检查拼写」
```

**生产阶段**

```
kiant_hoi4_scaffold 生成骨架（含 BOM 本地化）
   ↓ 手写扩充
kiant_hoi4_validate_mod（结构检查）→ 修
   ↓ deep=true
validators（科技/资产/图标/UI/钩子/历史/defines）→ 修
   ↓
kiant_hoi4_preview 生成 HTML → 看结构对不对
   ↓
进游戏 -debug → kiant_hoi4_analyze_error_log → 修
   ↓
kiant_hoi4_plan 标记完成
```

## 几个关键决定

### 1. 解析器容错，永不抛异常

`cw.py` 遇到畸形输入不中断，只累积诊断，每条带行号。理由很实际：模组目录里全是半合法文件，游戏照样加载。严格解析器会在你最需要诊断的时候拒绝打开文件。

### 2. 双全文索引

| 索引 | 分词器 | 服务对象 | 为什么这么选 |
|---|---|---|---|
| `code` | unicode61 | 脚本文件 | 标识符要精确匹配，`add_political_power` 必须能命中 |
| `text` | trigram | 笔记、文档 | 中文没空格，unicode61 会把整段当一个词 |

本地化不进 trigram。十万级词条逐条建 trigram 索引，会把全量构建从 45 秒拖到 3 分钟以上，收益接近零。本地化检索改走 `loc` 表的子串匹配，反而能直接返回键名、语言、文件、行号。

### 3. 校验器可插拔

`validators.py` 里每个校验器是一个函数加一个装饰器：

```python
@validator("technology", "科技树")
def check_technology(ctx: Ctx) -> list[dict]:
    ...
```

注册表 `VALIDATORS` 由 `run(ctx)` 统一驱动。加一个新内容类型，等于写一个函数，别处一行不用改。

上下文 `Ctx` 提供 `known(kind)`（mod 与知识库合并后的已知符号集合）、`mod_file()`、`script_files()` 和缓存。校验器只依赖这些，不自己 walk 文件系统。

### 4. 没有知识库时降级，而不是猜

这是这个项目花时间最多的地方。原版还没索引时，一个「找不到的 sprite」可能是原版 sprite，也可能是拼错。校验器在这种情况下降级并注明原因，不报 error。

```python
have_vanilla = bool(ctx.vanilla_root)   # 只有真索引到原版才敢报警告
```

道理不复杂：假阳性比漏报更伤信任。用户被误报折腾三次之后，会关掉整个检查。

降级不是一个大 if，是四个互相独立的判断维度：

| 维度 | 判据 | 动作 |
|---|---|---|
| 原版是否已索引 | `ctx.vanilla_root` | 贴图/sprite/oob/科技目标找不到 → `info` |
| 是否声明了依赖 | `descriptor.mod` 的 `dependencies` | 缺本地化键 → `info` |
| 是否是翻译子模组 | 需求键 ≥200 且覆盖率 <70% | 逐条降级，只留一条覆盖率摘要 |
| 是否真的过大 | 键数少时覆盖率没有意义 | 小模组缺键照样是 `error` |

第四条是后来才补的。一个只有 8 个键、缺 6 个的新模组，覆盖率 25%，如果按「低覆盖 = 子模组」处理，最该报的缺失全被降级成 info，检查等于失效。所以覆盖率的免罪符只对规模足够大的模组发行。

`Ctx.loc_level()` 把这四维收成一个函数，所有校验器共用：

```python
def loc_level(self, default="error"):
    if default != "error":                 return default
    if self.has_dependencies or self.loc_partial: return "info"
    if not self.vanilla_root:              return "warn"
    return "error"
```

### 4b. 合法写法不等于缺陷

HOI4 里有一批写法看起来像重复，其实是特性。不识别它们，就会产出海量假错误。目前已识别的：

| 写法 | 真相 |
|---|---|
| 同一个 `decision_category = { ... }` 出现在几十个国家文件里 | 引擎按名合并，是官方惯例 |
| `scripted_effect` / `scripted_trigger` 同名 | 子模组覆盖父模组的标准手段 |
| `random_events = { 17000 = 0 }` | 权重槽位留空，原版大量使用 |
| `names = { Alhx'es L'if' }` | 裸 token 允许含撇号，不是未转义引号 |
| 根目录的 `Credits.txt`、`"Unique Commanders IDS.txt"` | 纯文本笔记，不是脚本 |
| `on_map_area = { state=.. target_root_trigger={..} }` | 分类字段，不是一条决议 |

每一条都是被真实模组打出来的。判定手法分两种：结构铁律（`common/decisions/categories/` 下不定义决议）优先于字段签名（决议必有 `available`/`complete_effect`/`cost` 之一），字段签名又优先于看名字猜。

### 5. 预览在 Python 里算完布局

`preview.py` 不做运行时布局。坐标、连线路径、缩放比例全部在 Python 里算好，输出静态 SVG 加绝对定位 div。结果是零 JS 依赖，双击即开，断网也能看。

六国策的示例产出 9KB HTML，无外部请求。

### 6. 知识分四层，冲突时按层取信

这条是从 `references/` 的并入里学来的，现在写进了 agent 的硬约束：

```
游戏 documentation/*.md          字段级权威，553 个 effect + 596 个 trigger
  ↓
common/**/_documentation.md      31 处域级文档
  ↓
原版实例文件                      没有文档的域只能靠它
  ↓
references/ + 技能                整理与实测补充
  ↓
网上教程                          只当线索
```

为什么必须有这层？因为本插件自己的技能里曾经写着 `-debug`，而启动器官方的调试入口用的是 `-debug_mode`；也曾写着「`thumbnail` 是缩略图字段」，而真实 mod 里 14 个用 `picture`、1 个用 `thumbnail`。这类错误不靠更努力写文档能避免，只能靠「先查第一手来源」的纪律。

落到实现上是两件事。

第一，`kb.search()` 给每条结果标 `authority`：`game-doc` / `domain-doc` / `vanilla-instance`。agent 看到 `game-doc` 就知道不用再找旁证。

第二，`documentation/*.md` 抽成符号表（kind=`effect`/`trigger`/`modifier`，extra 存 Supported Scopes）。这样「这个 effect 存在吗」可以一条命令回答，不用读 8600 行。

### 7. 搬文档，不搬工具

`references/` 来自上游 dsh-hoi4-modding（MIT）。它同时有 21 个 CLI 脚本，本插件一个都没搬。

理由是架构不同。上游是 CLI 加退出码加 `--json`，本插件是 MCP 加结构化返回加分级 issue。两套工具链并存，用户会不知道该信哪个，agent 也会在两套命令之间摇摆。

所以只搬纯知识（`.md`），工具保持单一路径。代价是上游几个能力暂时空缺：`font audit`（中文字体分片）、`map audit`（省/州引用）、`dds make`（生成 DDS）、`tank layout`（设计器槽位）。这些缺口在 `references/README.md` 的映射表里逐条列明，写的是「无等价物」，没有含糊带过。要用就直接装上游插件，两者可以并存。

## 扩展点

### 加一种内容类型的校验

三步，都在 `validators.py` 内完成：

```python
@validator("my_kind", "我的检查", needs_kb=True)   # needs_kb=True 会要求先建索引
def check_my_kind(ctx: Ctx) -> list[dict]:
    issues = []
    for path in ctx.script_files("/my_folder/"):    # 路径片段过滤
        root, _ = cw.parse_file(path)
        for st in cw.get_all(root, "my_block"):
            if st.key not in ctx.known("my_kind"):
                issues.append({
                    "level": "warn",
                    "kind": "my_kind",
                    "file": ctx.rel(path),
                    "line": st.line,
                    "message": "...",
                    "hint": "...",        # hint 必须说「为什么」和「怎么改」
                })
    return issues
```

`needs_kb=True` 时若索引不存在，该校验器返回 `status: skipped` 并在报告里说明，不会静默跳过。

### 加一种符号的抽取

在 `kb.py` 的 `extract_symbols()` 里加一个分支，同时在 `checks.collect_definitions()` 里加对应逻辑。前者服务知识库检索，后者服务校验器。两处都加，才能既搜得到又校验得到。

这次就踩了这个坑：科技只加进了校验器，没加进 `collect_definitions`，于是「自己定义的科技」不被算作已知，全报「前置目标未找到」。

### 加一个技能

`skills/<name>/SKILL.md`，YAML frontmatter 必须有 `name` 和 `description`：

```markdown
---
name: kiant-hoi4-my-topic
description: 一句话说清「什么场景下用这个技能」。这段是路由依据，要写具体的触发场景，不要写形容词。
---
```

技能内容写会出错的地方和判断依据，不写教程式的基础介绍。用户已经有 agent 了，不需要被科普。

### 加一个知识源

三种方式，优先级从高到低：

1. `knowledge/sources.json`：固化源列表
2. `kiant_hoi4_kb_build` 的 `sources` 参数：临时指定
3. 自动探测：Steam 库 + 用户目录 + `knowledge/notes/`

## 安全与边界

不自动执行任何东西。没有预置会自动加载的 MCP 配置，没有 hook，没有安装脚本。接入必须由用户手工粘贴配置。

不联网。所有工具只读本地文件。要查 Wiki/GitHub 由 agent 自己去，结论用 `kiant_hoi4_kb_note` 存回本地。

只读游戏目录。`vanilla_path` 只用于比对和查找资源，从不写入。

不运行游戏。所有检查都是静态的。平衡性、AI 行为、实际手感只能进游戏测，文档里明确说了。

写入范围限于 mod 目录，且 `scaffold` 默认不覆盖已存在文件（`force=false`），本地化是 merge 而非覆盖。

## 已知限制

| 限制 | 影响 | 缓解 |
|---|---|---|
| 纯 Python 递归下降解析 | 超大文件（>5 万行）解析慢 | 索引时截断到 24k 字符；文档类给到 400k |
| 符号抽取依赖目录约定 | 自造目录名的定义抽不到 | `kiant_hoi4_kb_search` 兜底 |
| 不自动校验 effect/trigger 名 | 拼错的 effect 静默失效 | 已能查证（`kiant_hoi4_kb_symbol` 命中 553 个 effect + 596 个 trigger），但不自动报。判断「这个键是 effect 调用还是结构字段」需要完整语义表，猜错就会像当初的 `instance` 那样刷几万条假阳性。宁可让 agent 主动查，不自动扫 |
| 预览不渲染 3D、不模拟运行 | 看不到模型与动画 | 明确标注为「静态快照」 |
| 版本相关语义硬编码 1.19 | 1.20 若改名会漏报 | 报错日志仍能发现 `invalid`；参考库有 `migration.md` |
| 缺键判定靠覆盖率阈值 | 极端写法可能误判子模组 | 报告里始终带覆盖率摘要，可人工推翻 |
| 首次全量索引原版约 6 分钟 | 第一次用要等 | 之后增量构建是秒级；可用 `max_files_per_source` 试跑 |
| 军事、地图、字体的校验只到「文件存在」 | 字段级错误查不出 | 参考库 `03_military` `04_world` `05_presentation` 给了字段清单，人工对照 |

## 自检体系

两个脚本，职责分开。

`mcp-server/selftest.py` 有 330 项断言，十七组。纯接口级，不依赖外部数据，CI 里能跑。其中最关键的一组是 `examples/broken_mod/`：一个故意写坏的模组，注入 12 处经典缺陷，逐条断言「必须被某条检查以某个等级命中」。它同时是一份可执行的文档。想知道 `duplicates` 到底查什么，去读那个文件夹。

`mcp-server/bench.py` 在真实模组上量耗时与噪音比，用法 `python bench.py <模组名或路径>`。它输出的 `error` 数量是假阳性的体温计：某次改动让一个干净 mod 的 error 从 0 跳到几百，说明新加的判定过严。

两者合起来解决的是同一个问题：框架类项目的回归，靠眼睛看不出来。校验器多一个判断分支，可能在示例模组上毫无变化，却在 4871 文件的真实模组上多报 5 万条。

## 下一步能加的

按价值排序：

1. effect/trigger 词表校验。名字表已经有了（`_extract_engine_docs()` 从 `documentation/` 抽），缺的是「哪些位置算 effect 调用」的判定规则。做法：只校验 `completion_reward` / `complete_effect` / `immediate` / `option` / `on_startup` 这类已确定是 effect 上下文的块，块内非结构键才查表。宁可少查几个块，也不要误报，这是 7 万条假阳性换来的教训。
2. DDS 头与尺寸校验。参考库给了官方尺寸表（focus 100×88、idea 60×68、portrait 156×210、flag 82×52 TGA）和 vanilla 的 128 字节头字段。做一个只读 128 字节头的检查器，不要 Pillow。
3. 跨 mod 冲突分析。多个已索引 mod 同时定义同一 id 时给出冲突矩阵。
4. 本地化回填。用 `loc` 表做 key 对齐，批量补 `_desc`。
5. CHANGELOG 与版本对比。两次索引之间的符号差异，生成「上个版本改了什么」。
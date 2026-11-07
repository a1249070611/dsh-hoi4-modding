---
title: "hagane-studio 深度解剖：社区开源 HOI4 可视化编辑器"
domain: 93_ecosystem
repo: https://github.com/hagane-works/hagane-studio
license: GPL-3.0-only
verified_at: 2026-11-06
commit: main @ 2026-11-01
method: 本地全量源码逐模块阅读 + 行数实测，非二手转述
---

# hagane-studio（钢之工坊）

社区开源的 HOI4 可视化 Mod 编辑器。**Go 后端 + React 前端 + WebView2 桌面壳**，
本地运行、零在线依赖。本文是对它源码的解剖，重点在**它解决了什么、用什么方法解决的**，
以及**哪些设计值得本库吸收**。

> 引用规范：本域所有结论都基于 commit `main @ 2026-11-01` 的实际源码。
> 上游仍在活跃开发（仓库创建于 2026-10-30），数字会变，阅读时以当时代码为准。

## 一、硬数据（实测，不是估计）

| 指标 | 数值 |
|---|---:|
| Go 源文件 | **1291 个**，其中 **529 个是 `_test.go`** |
| Go 代码行数 | 20812 行 |
| TS/TSX 行数 | 17406 行 |
| `internal/` 下文件 | 1935 个 |
| 对外工具数 | **149 个**（`docs/cli.md` 声称） |
| 依赖数 | **5 个直接依赖**（见下） |
| 仓库体积 | 约 10 MB（不含 assets 与 node_modules） |

**529 / 1291 = 41% 的文件是测试。** 分层看更明显：

| 层 | 代码行 | 测试行 | 测试占比 |
|---|---:|---:|---:|
| `internal/hoi4/` | 29166 | 15104 | 34% |
| `internal/toolapi/` | 16485 | **13818** | **46%** |
| `internal/api/` | 2177 | 1351 | 38% |
| `internal/domains/` | 30491 | 4667 | 13% |
| `internal/gameindex/` | 4468 | 897 | 17% |

`toolapi` 的测试占比接近一半——**对外接口层测得最狠**，这是"接口就是契约"的态度。

## 二、依赖极简：5 个，且都很克制

```
github.com/jchv/go-webview2     # WebView2 桌面壳
golang.org/x/image              # 图像处理（DDS/PNG 编解码）
golang.org/x/sync               # errgroup 之类
golang.org/x/sys                # Windows API
golang.org/x/text               # 编码（UTF-16、大小写折叠）
```

**没有 web 框架、没有 ORM、没有数据库、没有 CLI 框架。** HTTP 层是手写的
（`internal/server/`、`internal/apiutil/`），JSON 是标准库 `encoding/json`，
存储全是文件。

对照本库：我们也是零依赖路线（Python 只用标准库），方向一致。但它把"零依赖"推到
了 20 万行代码的规模，证明这条路能撑住生产级项目。

## 三、五层结构

```
cmd/haganeworks           桌面入口（WebView2 窗口）
cmd/hw                    命令行客户端（thin client）
  ↓
internal/api               HTTP 路由（面向界面）
internal/toolapi           工具 API + MCP 协议 + mutation receipt
  ↓
internal/domains/<域>      业务域：focus / events / countries / technology / states ...
  ↓
internal/hoi4/<引擎>       游戏引擎层：paradox / emit / guirender / exportengine ...
  ↓
internal/project           项目持久化（JSON 表 + 素材文件）
```

**关键分工**：`domains` 管"一类内容怎么表达"，`hoi4` 管"游戏怎么读它"。
`toolapi` 不碰业务，只做**参数校验、调用、回执**。

## 四、项目存储：JSON 表 + 原始文件

```text
<创作目录>/<项目>/
  project.json        项目元数据、国家、DLC 选择、编号计数器
  data/<表名>.json    每类可编辑内容一个文件
  files/              导入上传的图片与源文件
```

- **一类内容一张表**，不是一个大 JSON。并发写不同表互不阻塞，冲突面小。
- **保存走临时文件 + rename**，避免中断留下半截文件。这是原子写，本库
  `_sync_state.json` 也用了同样思路但没那么严格。
- **不依赖数据库**：直接复制目录就是完整备份。

对照本库：我们用 `knowledge/survey.json` 这类单文件存派生数据，规模小没问题；
一旦到"每类内容一张表"的量级，分表是必然。

## 五、最值得学的三个机制

### 5.1 Token 级 trivia：无损往返的基础

详见 `hagane-studio-paradox.md`。一句话：**每个 token 都带着自己的前导空白和注释**，
读进来再写出去，字节级一致。这是我们完全没有的能力。

### 5.2 mutation_receipt：写给 AI 看的诚实约束

详见 `hagane-studio-mutation-receipt.md`。一句话：**每次写操作返回一个回执，
里面有一段 `reporting_rule` 明确告诉调用方（尤其是 AI）哪些话能说、哪些不能说。**

这是全仓库我认为最有价值的设计，直接冲着"AI 谎报成功"这个问题去的。

### 5.3 gridbox 几何：科技树布局的真实来源

详见 `hagane-studio-guirender.md`。一句话：**科技树的格子尺寸和排列方向不是猜的，
是从 `.gui` 文件里 `gridboxType` 的 `slotSize` 和 `format` 读出来的。**

## 六、它明确不做的事

README 自己写清楚了边界，这点值得记：

> 不同功能的导入、导出覆盖程度并不完全相同，大型 Mod 也可能包含编辑器尚不能完整保留的特殊写法。
> 请保留备份，并在发布前进入游戏测试导出结果。

换句话说：**它承认"往返保真"是有损的**，只是损多少看内容类型。这不是缺陷隐瞒，
是把限制写在最显眼的位置。

## 七、和本库（dsh-hoi4-modding）的定位差异

| | hagane-studio | dsh-hoi4-modding（本库） |
|---|---|---|
| 形态 | 桌面 GUI 应用 | MCP 工具 + Agent + 参考库 |
| 使用者 | 人（可视化操作） | AI agent（自然语言驱动） |
| 写入方式 | 表单 → 结构化数据 → 生成 | Agent 写文本 → 工具校验 |
| 长处 | 所见即所得、布局可视化 | 任意写法都能处理、知识可追溯 |
| 短处 | 只能编辑建模过的字段 | 没有可视化反馈 |

**两者不冲突，是互补的。** 它证明了"结构化编辑"这条路能走通；
本库走的是"文本优先 + 静态校验"，覆盖它建模不到的部分。

## 八、篇目

| 篇 | 讲什么 |
|---|---|
| `hagane-studio-paradox.md` | 解析器：token/trivia、错误恢复、Python 兼容层 |
| `hagane-studio-mutation-receipt.md` | 写操作回执：防 AI 谎报的机制 |
| `hagane-studio-guirender.md` | 界面重建：gridbox 几何与 170 个渲染模块 |
| `hagane-studio-toolapi.md` | 149 个工具的组织方式与测试策略 |

## 九、怎么自己看

```bash
git clone --depth 1 https://github.com/hagane-works/hagane-studio.git
# 或者只下载 tarball（约 7 MB，比 git clone 快）
curl -L https://codeload.github.com/hagane-works/hagane-studio/tar.gz/refs/heads/main -o hs.tar.gz
```

优先读这几个文件，性价比最高：

```
internal/hoi4/paradox/token.go          183 行  ← trivia 机制全在这
internal/hoi4/paradox/trivia.go         105 行  ← 注释归位逻辑
internal/hoi4/paradox/parser.go         345 行  ← AST + 三类错误恢复
internal/toolapi/mutation_receipt.go    513 行  ← 防谎报机制
internal/hoi4/guirender/geometry.go     101 行  ← 科技树几何
docs/cli.md                             150 行  ← 作者自述的设计意图
```

# 零经验上手

目标很简单：半小时之内，让游戏里出现一个你自己写的国策。

不用先学 Clausewitz 语法，也不用读完 153 篇参考库。先照着做一遍，做完再理解为什么。

## 准备

| 需要 | 说明 |
|---|---|
| 游戏本体 | 装在哪个盘都行，工具会自动找（`HOI4_GAME` 环境变量可以强制指定） |
| 本插件 | 已接好 MCP，或者直接用 `python mcp-server/server.py --call <工具> '<json>'` |
| 一次索引 | `kiant_hoi4_kb_build action=build`，约 20 秒（原版加参考库，不含第三方模组）。不建也能做，但四类检查会降级，校验结果里会写 `summary.index.hint` 提醒你 |

## 第 1 步：建一个空壳 mod

```
kiant_hoi4_scaffold  kind=mod  mod_path=<你想放的位置>/myfirst  display_name=我的第一个mod  tag=GER
```

下面的例子假设放在 `D:/mods/myfirst`，你换成自己的目录即可（任何盘、任何位置都行）：

它会在 `D:/mods/myfirst` 生成这些：

```
D:/mods/
├── myfirst.mod                            ← 外层描述文件（带 path），和文件夹同级
└── myfirst/
    ├── descriptor.mod                     ← 内层描述文件（不带 path）
    └── localisation/english/
        └── myfirst_l_english.yml          ← 已带 BOM，可以直接往里加词条
```

> **选目录时只有一个硬要求：路径必须是纯 ASCII。** `C:/Users/张三/mods/...` 这种带中文的路径会让 mod 在启动器里正常显示、但进游戏毫无效果，而且不报错。用户名是中文的话，把 mod 放到 `D:/mods/` 这类与用户名无关的位置。

为什么要两份描述文件？游戏读外层那份找路径，创意工坊读内层那份取元数据。两份内容只差 `path` 那一行，缺一份游戏就不认。这是新手遇到的第一个坑。

## 第 2 步：装进游戏

把整个文件夹和外层 `.mod` 文件一起放进：

```
文档/Paradox Interactive/Hearts of Iron IV/mod/
```

启动游戏，启动器左侧应该能看到「我的第一个mod」，勾选启用。

看不到的话，`kiant_hoi4_validate_mod mod_path=<你的 mod>` 会告诉你哪一步错了。

## 第 3 步：加第一个国策

```
kiant_hoi4_scaffold  kind=focus  mod_path=<你的 mod 目录>  name=rebuild  tag=GER
```

这一步同时做三件事：

1. 建 `common/national_focus/ger_rebuild.txt`，里面是一棵能用的国策树
2. 在 `localisation/english/ger_rebuild_l_english.yml` 写带 BOM 的名字与描述
3. 用 `country = { modifier = { tag = GER } }` 把树挂到德国

生成完直接跑一次 `kiant_hoi4_validate_mod`，应该是 `0 error`。这一步是基准。如果这里就报错，说明环境有问题，先解决再往下改。

打开那个文件，只看这几个字段：

```
focus = {
    id = GER_rebuild              ← 全局唯一，撞了会被静默覆盖
    icon = GFX_focus_generic_industry_2   ← 必须是原版真有的 sprite
    cost = 10                     ← 天数/7
    x = 0                         ← 横向格子
    y = 0                         ← 纵向格子
    completion_reward = {
        add_political_power = 50  ← 点了给什么
    }
}
```

改 `add_political_power` 的数值，或者换成 `add_stability = 0.05`，这就是你的第一个改动。

## 第 4 步：校验（每次改完都跑）

```
kiant_hoi4_validate_mod  mod_path=<你的 mod 目录>  deep=true
```

要看到 `errors: 0`。常见输出长这样：

| 它说什么 | 你该做什么 |
|---|---|
| `缺少本地化键 GER_rebuild` | 在 `.yml` 里补一行 `GER_rebuild:0 "名字"` |
| `缺少本地化键 GER_rebuild_desc` | 补描述，悬停时显示的文本 |
| `国策图标引用的 sprite 'GFX_xxx' 未找到` | 图标名写错了，换成原版存在的（生成器默认给的是 `GFX_focus_generic_industry_2`） |
| `unclosed block` | 少一个右花括号，从这行往后整个文件都被忽略 |

顺带提一句：`kiant_hoi4_fix_localisation` 解决的是另一类问题，文件编码和 BOM 不对，不是缺键。别指望它补词条。

## 第 5 步：不开游戏先看效果

```
kiant_hoi4_preview  mod_path=<你的 mod 目录>
```

在浏览器打开 `<mod>/.modkit/preview.html`。国策按真实坐标画出来，前置连线也在，缺本地化的地方直接标红。

不想让 mod 目录多东西的话，传 `out_path` 指到别处。

## 第 6 步：进游戏

启动参数加 `-debug_mode`（不是 `-debug`，后者是旧版参数）：

```
Steam → 右键 HOI4 → 属性 → 启动选项 → -debug_mode
```

进游戏切到德国，打开国策树，应该能看到你的国策。

看不到就：

```
kiant_hoi4_analyze_error_log
```

它会把几万行日志压成几十条，按 `Invalid Scope` / `Unknown effect-type` / `Could not find sprite` 分类。只关注提到你 mod 文件名或 ID 的行，其余是原版噪声。

### 日志干净但还是不对？先查错题本

这是最容易卡住的情况：游戏不报错，功能就是不生效。引擎有很多静默失败路径，日志里一行都不会有。

```
kiant_hoi4_error_book query="科技页方框都在但一条连线都没有"
```

query 写你实际看到的现象，不要写你猜的原因。错题本按症状组织：「科技页连线没了」能查到，「technology_folders 的 available 写错了」反而查不到，因为你还没确定是那里错了。

命中之后：

```
kiant_hoi4_error_book action=get id=EB-003 section="标准化方案"
```

直接照做。24 条覆盖了本地化乱码、国策/事件不出现、覆盖失效、静默失败、日志洪水、校验假阳性这些最常见的情况。

错题本里没有的，再去 `kiant_hoi4_solutions` 找思路。那里是没验证过的，用之前自己确认前提成立。

## 新手最常踩的五个坑

| 坑 | 症状 | 原因 |
|---|---|---|
| 中文路径 | 启动器有、游戏里没有 | `path` 必须纯 ASCII 加正斜杠 |
| `.yml` 没 BOM | 界面显示 `GER_rebuild` 而不是中文 | 本地化文件必须 UTF-8 带 BOM，脚本文件则不带 |
| 少 `add_namespace` | 事件不触发 | `events/` 里的文件顶部要写 `add_namespace = xxx` |
| id 撞了 | 你的国策不出现 | 全局唯一，用 `NAMESPACE_` 前缀；`kiant_hoi4_find_duplicate_ids` 查 |
| 改完没重启 | 改了没反应 | `common/`、`history/`、`map/` 不热重载，必须重启游戏 |

## 接下来

会做第一个之后，按需要查：

- 写什么内容 → `references/_index.md` 的路由表（「我要做 X → 读哪一篇」）
- 某个字段到底存不存在 → `kiant_hoi4_kb_symbol name=<名字>`
- 原版是怎么写的 → `kiant_hoi4_kb_lookup kind=focus`（取 2~3 个真实实现）
- 想系统学 → 技能会在写具体内容时自动带上要点，不用预先通读

## 最后一句提醒

不要一上来改原版文件。复制原版文件改一行，原版更新后会静默落后，而且会和别的 mod 冲突。新增文件、用新 ID，需要改原版行为时用 effect/trigger 在运行时注入。

这条比其余所有技巧加起来都重要。
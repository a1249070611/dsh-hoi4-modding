# 资料库

这里放本地知识来源。索引是 SQLite，内容是原版、已装模组和你的笔记。

## 三种源

| 类型 | 来源 | 用途 |
|---|---|---|
| `game` | 游戏安装目录 | 原版权威写法，校验时用作参照 |
| `mod` | 用户目录下任何有 `descriptor.mod` 的模组 | 学习大改 mod 的实现，或排查冲突 |
| `notes` | 本目录下的 `notes/` | 你的结论、踩坑记录、设计约定 |

## 自动发现

没有 `sources.json` 时，`kiant_hoi4_kb_build action=discover` 会探测：

- Steam 库里的 `Hearts of Iron IV`（注册表 `SteamPath` → 逐盘扫 `Steam`/`SteamLibrary` → 读 `libraryfolders.vdf`，支持多盘）
- `文档/Paradox Interactive/Hearts of Iron IV/mod/` 下每个有 `descriptor.mod` 的模组
- 本目录的 `notes/`

> 历史坑：2.2.0 之前的版本只查 `C:\Program Files (x86)\Steam`，Steam 装在别的盘就永远返回空，
> 于是 `find_game_dir()` 为 `""`，所有依赖原版的检查**静默降级为 info**，看不出任何异常。
> 现在有三重探测，且 `kiant_hoi4_kb_build action=discover` 会直接回显 `game_dir`——**先看这一行是不是空的**。

## 远端知识库（作者维护）

`remote.json` 指向作者发布知识的开源仓库。填好后：

```
kiant_hoi4_kb_sync action=status   → 看本地缓存与远端版本差
kiant_hoi4_kb_sync action=pull     → 拉取约 1 MB，缓存到 ~/.kiant-hoi4-modkit/remote/
kiant_hoi4_kb_build action=build   → 多出一个 remote 源
```

只同步知识（markdown），不同步游戏索引——后者是本机派生物。仓库该怎么组织、发布流程见根目录 `PUBLISHING-KB.md`。

检索分两级：**平台库优先**。`kiant_hoi4_kb_search` 默认 `scope=auto`，先查 `remote`，命中就返回；没命中才退到本地（`vanilla` / `refs` / `notes` / 点名的目录）。返回里的 `answered_from` 会说明这次来自哪一级。

- `scope=platform` 只查平台库
- `scope=local` 只查本地
- `scope=all` 两级一起查，平台排前面

要读某个本地目录（比如旧笔记、别人给的文档），点名给它，工具不会自己扫：

```bash
kiant_hoi4_kb_build action=build local_dirs=["<你的笔记目录>"]
```

## 固化源列表

**没有 `sources.json` 时**（别人刚拿到插件的情况），`build` 默认只索引三个源：

```
vanilla   原版游戏
refs      参考库 143 个文件（84 篇上游 + 5 篇自撰 + 54 篇自建，随插件分发）
notes     本目录的 notes/
```

第三方模组**默认不收**。装了几十个工坊模组时全收进来会让首次索引从 20 秒变成几十分钟，而且半成品/纯汉化包会污染检索。要用就显式点名：

```bash
... '{"action":"build","include_mods":true}'      # 收全部
... '{"action":"build","only":"mod:我的模组"}'    # 只收一个
```

`action=discover` 会列出所有能发现的模组，并给它们标 `opt_in: true`。

**本机有 `sources.json` 时**，它完全接管——自动探测被跳过，只索引文件里列出的源。这个文件记录的是**使用者自己的**绝对路径，所以不随包分发；要固化就复制样例再改路径：

```bash
cp knowledge/sources.example.json knowledge/sources.json   # 然后改里面的 path
```

示例（Windows，路径按你自己的安装位置改）：

```
vanilla   游戏本体       C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV
notes     本目录的 notes/
refs      本目录的 references/
```

### 游戏装在非标准位置

探测顺序是：环境变量 `HOI4_GAME` → 注册表 `SteamPath`/`InstallPath` → 逐盘扫 `Steam`/`SteamLibrary`。三条都不中才会失败。

临时覆盖不用改文件：

```bash
HOI4_GAME="F:/Games/Hearts of Iron IV" python server.py --call kiant_hoi4_kb_build '{"action":"build"}'
```

`HOI4_USER_DIR` 同理，用于用户数据目录不在「文档」下的情况。

### 四个环境变量

| 变量 | 管什么 | 什么时候改 |
|---|---|---|
| `HOI4_GAME` | 游戏本体在哪 | 装了多份、或不在 Steam 默认位置 |
| `HOI4_USER_DIR` | 用户数据目录（`.mod` 和存档） | 用户目录不在「文档」下 |
| `HOI4_KB_DB` | 索引库 `kb.sqlite` 放哪 | 想把库放共享盘、或跑 CI 时要隔离 |
| `HOI4_MODS_ROOT` | 扫描第三方模组的根目录 | mod 不装在默认的 `mod/` 下 |

默认值全部由程序算出来，不含任何写死的本机路径：游戏目录靠探测，索引库在
`~/.kiant-hoi4-modkit/kb.sqlite`。**换一台电脑不用改任何东西。**

### 自己写 `sources.json` 时，路径怎么写

`path` 支持三种写法，按推荐程度排：

| 写法 | 例子 | 说明 |
|---|---|---|
| 相对路径 | `knowledge/notes` | **以插件根目录为基准。** 插件自带的两个目录就该这么写——它们对所有安装者都处在同一个相对位置 |
| 家目录 | `~/Documents/Paradox Interactive/...` | 跨机器可用 |
| 绝对路径 | `E:/Steam/steamapps/...` | 只在确实要钉死某个本机位置时用，换电脑会失效 |

写相对路径的最大好处：**配置文件可以跟着仓库走，别人 clone 下来直接能用。**
写绝对路径的话，每个人都要改一遍，而且很容易把本机路径误提交上去。

## 笔记

两种放法：

**长文档** —— 在本目录的 `notes/` 下放 `.md`，重建索引时收录。适合设计稿、会议结论、从 Wiki 抄下来的长文。

**短记录** —— `kiant_hoi4_kb_note action=add`，直接进数据库。适合"今天搞清楚了某个字段"这类碎片。

两者都能被 `kiant_hoi4_kb_search` 检索到。

推荐记什么：

- 版本差异（1.19 改了什么、哪个 effect 改名了）
- 反直觉的行为（"原来 `path` 不阻止研究"）
- 与其他 mod 的冲突与解法
- 团队约定（命名规范、目录约定）

不要记什么：

- 原版已经能查到的东西（重复索引，还会过期）
- 一次性的路径与临时状态

## 索引有多大

实测参考：

| 源 | 文件数 | 符号 | 词条 | 耗时 | 库大小 |
|---|---|---|---|---|---|
| 原版 vanilla 1.19.4.2 | 6167 | 62k | 26 万 | 16s | 131MB |

增量构建只处理变化的文件，日常更新是秒级。

第一行这个 26 万词条是**过滤后的**数字：原版带 10 种语言、每种约 13 万条，全存是 130 万行 / 9 分钟。默认只留 `english` + `simp_chinese`，要全量传 `loc_langs: []`。

## 位置

默认 `~/.kiant-hoi4-modkit/kb.sqlite`，不在插件目录里，避免插件更新时丢失。用 `db_path` 可以指向别处（比如项目内共享一份）。

删掉重建是安全的，代价只是重新索引一次。

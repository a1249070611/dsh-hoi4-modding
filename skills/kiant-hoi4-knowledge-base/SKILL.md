---
name: kiant-hoi4-knowledge-base
description: 用知识库学习原版与其它 mod 的真实写法：建索引、检索代码、取范例、追符号定义、补充本地笔记。回答「原版怎么做的」这类问题的工作流。
---

# 知识库工作流

## 它解决什么问题

模型对 HOI4 的记忆有两类：

1. **稳定的**：目录结构、本地化是 UTF-8 BOM、事件要 namespace。这些可以放心讲。
2. **不稳定的**：`scripted_gui` 的字段名、`archetype` 与模型挂接的方式、某个 effect 在 1.19 是不是改了名。这些凭记忆写 100% 会出错，而且错得很像对的。

知识库把第 2 类换成"查原版真实文件"。这是整个平台可信度的来源。

## 建立索引

```json
{"action": "discover"}
```

先看能索引什么。会自动发现：

- `vanilla` —— 游戏安装目录（Steam 库自动探测）
- `mod:<名字>` —— 用户目录下每个有 `descriptor.mod` 的模组
- `notes` —— 插件自带的 `knowledge/notes/`

确认后：

```json
{"action": "build"}
```

首次全量视规模可能几分钟（5000 文件约 45 秒，原版 2 万文件约 3 分钟）。之后增量，只处理变化的文件。

只想索引某个大改 mod 参考写法：

```json
{"action": "build", "only": "mod:你的模组"}
```

索引结果：每个文件一个代码文档、每个定义一个符号、每条本地化一个词条。实测原版产出 6.2 万符号与 26 万词条。

## 三种检索，别用错

| 工具 | 什么时候用 | 例子 |
|---|---|---|
| `kiant_hoi4_kb_lookup` | 想写某类内容，先看真实结构 | `kind=tech limit=2` |
| `kiant_hoi4_kb_search` | 知道关键词，找在哪出现 | `"add_political_power"`、`"scripted_gui"` |
| `kiant_hoi4_kb_symbol` | 查一个 id 的所有定义与文本 | `name=GER_pz1_a` |

`lookup` 返回带行号的代码摘录，直接能抄结构。`search` 返回命中片段，适合定位。`symbol` 适合排查撞名与追踪引用。

## 错题本与方案库也在索引里

`references/91_error-book/` 和 `references/92_solutions/` 会随 `refs` 源一起进索引，**可以直接全文搜**。

| 想找 | 怎么搜 |
|---|---|
| 某个报错的解法 | `kb_search "Unknown trigger-type"` 或搜症状原文 |
| 某类问题的历史记录 | `kb_search "静默失败"`、`kb_search "连线消失"` |
| 某个未实现能力的思路 | `kb_search "map audit"`、`kb_search "字体映射"` |

中文子串可以搜到（这两类走 trigram 索引），不用分词。

**但检索有前提**：先跑过 `kb_build`。如果搜不到，不是没有，可能是索引没建或过期——查 `kb_stats`。

### 三种检索方式，别用错

| 方式 | 适用 | 代价 |
|---|---|---|
| **`kiant_hoi4_error_book query="现象"`** | **排查时的默认选择**——按症状加权匹配，命中即给 ID 与摘要 | 免费、即时，不需要建索引 |
| 直接读 `91_error-book/_index.md` 的症状速查表 | 想一眼扫完 25 条全貌，或不确定该怎么描述 | 要用眼睛读，占上下文 |
| `kb_search` 全文搜 | **有明确关键词**——报错原文、工具名、字段名、中文子串 | 需先跑过 `kb_build`，且不区分「已实证」与「未验证」 |

**优先用 `kiant_hoi4_error_book`，不是因为它更准，而是因为它不受索引影响。** 你遇到问题的时刻，往往正是索引没建、或者刚改了目录还没同步的时候。这个工具每次现读 md 文件，坏的时机也不会掉链子。

它还会拒掉「字面碎片」式的假命中。搜「性能不好」时不会因为文中有「能不」两个字就把半个错题本推给你——虽然结果会是空的，而空的答案比错的答案有用。

## 典型问题怎么问

**「原版国策树怎么组织多棵树？」**
→ `kiant_hoi4_kb_lookup kind=focus_tree`，看 2~3 个原版例子，比较 `country` 块的写法。

**「scripted_gui 有哪些字段？」**
→ `kiant_hoi4_kb_search "scripted_gui"`，挑一个原版文件用 `kiant_hoi4_parse_script` 解析成树看结构。

**「我这个 idea id 为什么没生效？」**
→ `kiant_hoi4_kb_symbol name=GER_xxx`，看是否有多个定义，以及分别来自哪个源。

**「中文文本在哪，为什么显示英文？」**
→ `kiant_hoi4_kb_search "关键词"`，`type=loc` 的命中会带语言与文件行号。

**「报错了，这个错我见过吗？」**
→ `kiant_hoi4_error_book query="报错原文或现象"`。没命中再 `kb_search "报错原文"`。
→ 还是没有，`kiant_hoi4_solutions query="关键词"` 看未验证的思路池。

## 补充本地资料

遇到知识库里没有的东西（论坛结论、自己踩的坑、团队约定），存成笔记：

```json
{"action": "add", "title": "1.19 改模型必须同步 .asset 的 scale", "body": "...", "tag": "models"}
```

之后 `kiant_hoi4_kb_search` 能检索到。也可以在 `knowledge/notes/` 放 `.md` 文件，重建索引时会一并收录——适合放长文档、会议结论、设计稿。

`knowledge/sources.json` 可以固化你常用的源列表，避免每次自动探测：

```json
{
  "sources": [
    {"name": "vanilla", "path": "C:/Steam/.../Hearts of Iron IV", "kind": "game"},
    {"name": "mod:我的模组", "path": ".../mod/我的模组", "kind": "mod"}
  ]
}
```

## 边界

- **索引是静态快照。** 游戏更新后要重建（增量即可）。
- **不含运行时语义。** 它知道 `add_political_power = 50` 出现在哪，但不会计算效果。
- **不联网。** 需要查 Wiki 或 GitHub 时，由 agent 本身去查，然后把结论用 `kiant_hoi4_kb_note` 存回本地。
- **符号抽取有盲区。** 非标准目录（自造文件夹名）里的定义可能抽不到，此时用 `kiant_hoi4_kb_search` 兜底。

## 判断索引是否够用

```json
{"action": "stats"}
```

看 `symbols_by_kind`：如果没有 `focus` / `idea` / `tech`，说明只索引了本地化或资源文件，需要加上原版或内容模组。`game_dir` 显示"未找到"时，所有依赖原版比对的检查都会降级为 info。

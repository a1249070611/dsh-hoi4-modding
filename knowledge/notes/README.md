# 笔记

这个目录里的 `.md` 会被 `kiant_hoi4_kb_build` 收录，之后可以用 `kiant_hoi4_kb_search` 检索到。

## 文件怎么组织

一个主题一个文件，用短横线命名，前缀标类型：

```
notes/
├── syntax-focus-prerequisite.md        语法与语义
├── version-1.19-changes.md             版本差异
├── conflict-rt56-and-blackice.md       冲突与解法
├── convention-naming.md                团队约定
└── pitfall-decision-category.md        踩坑记录
```

不用建子目录，扁平放就好——检索是按全文，不是按路径。

## 每条笔记要有据

一条笔记值钱的地方不是结论，是**结论的依据**。抄一个说法进来，要能回答「从哪看到的、在哪个文件哪一行验证过」。

```markdown
# 国策前置的与/或语义

**结论**：同一个 `prerequisite` 块里写多个 `focus` 是「与」，写多个 `prerequisite` 块是「或」。

**依据**：原版 `common/national_focus/germany.txt` 第 412 行起，
`GER_four_year_plan` 的两个前置用了两个独立块，游戏内两者任一即可点。
另见 `POL_central_industrial_region` 同块双前置，必须全满足。

**易错**：写反了不报错，只是国策永远点不亮或过早可点。

**适用版本**：1.14 起一致，1.19 复验。
```

字段固定成四段：结论 / 依据 / 易错 / 适用版本。「适用版本」不是形式主义——Paradox 会改语义，没标版本的笔记三年后是负债。

## 只有一种情况可以不写依据

你自己在游戏里试出来的。那就把「怎么试的」写下来：

```markdown
**依据**：实测。控制台 `focus.autocomplete` 后建新档，
点掉 A 再看 B 是否可点。
```

## 一次性的东西不要放这里

索引是给未来的自己用的。以下内容进笔记只会污染检索结果：

- 临时路径、当前调试到一半的状态
- 原版文件里就能查到、不做任何加工的内容
- 「今天做了 X」这类流水账（那是 `.workbuddy/memory` 的事）

## 检索

```bash
kiant_hoi4_kb_search "prerequisite" kind=md
kiant_hoi4_kb_search "粉黑方块"
```

中文走 trigram 索引，子串能命中；英文标识符走 `unicode61`，精确匹配快。

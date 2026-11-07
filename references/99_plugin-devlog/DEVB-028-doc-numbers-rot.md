---
title: "DEVB-028 文档里的数字不会自己更新，包括自检的章节号"
id: DEVB-028
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 误导
verified_on: 1.19.4.2
verified_at: 2026-11-07
first_seen: 用 humanizer 通读七份说明文档，逐项核对数字
related: [99_plugin-devlog/DEVB-026-value-may-be-block.md]
---

# DEVB-028 文档里的数字不会自己更新，包括自检的章节号

## 症状

去 AI 味改写七份说明文档时，顺手把文中每个数字都实测了一遍。改完发现有六类
问题，全部是「文档写着某个数，实际是另一个数」：

| 文档 | 写的 | 实际 |
|---|---|---|
| STRUCTURE.md | 三个学习域（6 篇） | 五个域，28 篇 |
| STRUCTURE.md | 自建的两本（40 篇） | 43 篇（28 + 15） |
| STRUCTURE.md | selftest.py 1684 行 | 1692 行 |
| STRUCTURE.md | mcp-server 合计 8690 行 | 8698 行 |
| PUBLISHING-LIBRARY.md | 152 个 md / 143 篇 / 54 自建 | 176 个 md / 145 篇 / 77 自建 |
| PUBLISHING-LIBRARY.md | 归档区叫 `hoi4-moding-old` | 已改名 `hoi4-moding-archive` |
| PUBLISHING-KB.md | 84 上游 + 55 自建 | 63 上游 + 77 自建 |
| PUBLISHING-KB.md | file_count: 92 | 148 |
| agents 人设 | 25 条错题 | 27 条 |
| `_index.md` 路由 | 50+ 条 | 87 条表行 |

「三个学习域（6 篇）」这一条尤其说明问题：标题说三个，表格里列了五个目录，
篇数加起来 28。这不是笔误，是**标题和内容各改了一次、没对上**。

## 错在哪

错在以为「自检里有文档一致性检查」就万事大吉。实际上那条检查只覆盖四类数字
（N 个技能 / N 个工具 / N 篇 / N 条错题本），因为只有这四类能用正则稳定抓取。

其余数字全靠人记得改。而人不会记得。

更要命的是：**自检自己的章节号也不在检查范围内**。这次发现 `section("11. …")`
出现两次、`13` 缺失，编号序列是 `1..10, 11, 11, 12, 14, 15, 16, 17`。
自检是全绿的，因为它跑的是断言，不是编号。

## 根因

自动化的边界被误当成了「已覆盖」的边界。一条断言管住的东西，人就不再盯；
而断言没管的地方，腐烂程度跟没有断言时完全一样，只是现在多了「有自检所以应该没问题」
这层错觉。

## 标准化方案

写文档里的数字，只认实测，不认记忆。改完跑：

```bash
# 篇数分解
python -c "
import os
R='references'
root=[f for f in os.listdir(R) if f.endswith('.md')]
dirs={d:sum(1 for f in os.listdir(os.path.join(R,d)) if f.endswith('.md'))
      for d in os.listdir(R) if os.path.isdir(os.path.join(R,d))}
print('根',len(root),'合计',len(root)+sum(dirs.values()))
for k in sorted(dirs): print(' ',k,dirs[k])
"

# 行数
for f in mcp-server/*.py; do printf "%-16s %s\n" "$f" "$(wc -l < $f)"; done

# 全仓 md 总数
find . -name "*.md" -not -path "*/__pycache__/*" | wc -l
```

章节号另有一条土办法，改完 section 顺手跑一次：

```bash
grep -o 'section("[0-9]*\.' mcp-server/selftest.py | sed 's/section("//;s/\.//' | tr '\n' ' '
```

输出应该是连续的 `1 2 3 … 17`。看着像 `1 2 3 … 11 11 12 14 …` 就是漏了或重了。

## 同一批改动里藏着的第二个坑

改完数字要同步到资料库，一同步又出问题：8 份文档在主目录各多出一个同名节点。

根因在 `_resync.py` 的一行调用：

```python
old_ids = stale_siblings(rel, parent, keep=_node_of(rel))
```

`stale_siblings` 的 `keep` 参数语义是「这个节点是对的，留着别动」。而
`_node_of(rel)` 取的是 `_sync_state.json` 里上次上传成功返回的 id——在重传场景下，
**那个节点恰恰就是内容已过期、该退休的对象**。于是旧节点被保护、新节点又传上去，
一个路径两个节点。

参数名 `keep` 读起来像「要处理的那个」，实际是「不要碰的那个」。这种命名歧义在
单人写的脚本里特别容易埋雷，因为调用点看起来完全合理。

修法不是改参数值，是改默认值：`stale_siblings` 的 `keep` 改成默认空串，
`resync()` 里显式写 `keep=""`，并在 docstring 里写清「重传时没有任何节点是对的」。

验证要看两个方向，缺一不可：

```bash
python _resync.py GETTING-STARTED.md   # 必须报「旧节点 xxx 已移入归档」
python _verify_library.py               # 必须 0 处同路径多节点
```

只跑第一次看不出问题——不归档也能上传成功，脚本照样打印 `ok`。必须用核对脚本
数节点，才知道旧的那个走没走。连续跑两次还要再核对一次，这是查幂等：
如果第二次把第一次的新节点也退掉了，节点数会变成 0 而不是 1。

## 教训

文档一致性检查的覆盖面要跟着文档长大的速度扩。加了新章节、新目录、新的篇数
统计口径，就该问一句「这条断言还管得住它吗」。

管不住的地方，下次写文档时一定会错，只是错得没人发现。

还有一条更通用的：**改数字是机械劳动，同步是危险操作。** 前者错了自检会抓，
后者错了自检不管——它只比对路径和标题，同名节点它数不出来，除非核对脚本专门
去数。手工改文档顺手同步，正是最放松警惕的时候。

## 关联

- DEVB-06：断言写得不够严，「检查被拆掉」和「检查通过」是同一个结果
- 这次是同一类问题的文档版：不是断言不严，是断言管不到
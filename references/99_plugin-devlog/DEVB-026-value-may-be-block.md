---
title: "DEVB-026 值可能是块：被 as_text 静默吞掉的三类引用"
id: DEVB-026
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 阻断
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: 修完 DEVB-05 后再跑一次原版，仍剩 140 条事件缺键
related: [99_plugin-devlog/DEVB-025-vanilla-as-testcase.md, 99_plugin-devlog/DEVB-024-verification-vs-execution.md]
---

# DEVB-026 值可能是块：被 as_text 静默吞掉的三类引用

## 症状

DEVB-05 修完，原版 error 从 11694 降到 2079，我以为这事结了。
再跑一遍、逐条看剩下的 2079，发现有 **140 条是事件正文缺键的误报**：

```
events/AAT_Iceland.txt:925  iceland_events.17
    报: 缺少本地化键 iceland_events.17.desc
    实际写了: iceland_events.17.desc_kingdom
```

去原文看：

```
desc = {
    text = iceland_events.17.desc_kingdom
    trigger = { ROOT = { tag = DEN NOT = { has_government = communism } } }
}
desc = {
    text = iceland_events.17.desc_generic
    trigger = { ROOT = { ... } }
}
```

**`desc` 写成了条件块，而且可以重复出现多次，每个变体一个 `text =` 键。**

## 根因：一个函数假设，三处伤

采集代码用的是：

```python
def _stmt_value_text(block, key):
    st = cw.get_one(block, key)      # 只取第一个
    ...
    return cw.as_text(st.value)      # 块 → 返回 ""
```

`as_text()` 只认 `Scalar`，遇到 `Block` 一律返回空串。于是：

| 环节 | 后果 |
|---|---|
| `get_one` | 只取**第一个** `desc`，后面的块全丢 |
| `as_text` | 第一个也是块，返回 `""` |
| 空串被当「没写」 | 回退到 `<id>.desc` / `<id>.d` 默认键 |
| 默认键不存在 | **误报缺键** |

## 这不是一个 bug，是一整类

顺着 `_stmt_value_text` 往下查，把所有采集字段的**实际值类型**统计一遍：

| 字段 | 标量 | 块 | 块内结构 |
|---|---|---|---|
| event `desc` | 6629 | **214** | `text = <键>` + `trigger =` |
| event `title` | 6826 | **18** | 同上 |
| focus `icon` | 10297 | **44** | sprite 名当**语句键** |
| decision `icon` | 3654 | **66** | sprite 名写在 `key =` 里 |
| idea `picture` | 6110 | 0 | — |

**112 处块形式引用完全不在检查范围内。**

块里声明的键抽查：`desc` 512 个、`title` 46 个，**全部在原版本地化里真实存在**——
说明这不是原版写错，是工具没读到。

### 三种块的结构互不相同

这是最容易踩的坑：以为「块就是块，一套逻辑通吃」。

```
# 国策 icon —— sprite 名当语句键，条件是值
icon = {
    GFX_focus_A = { OR = { has_government = democratic } }
    GFX_focus_B = yes
}

# 决议 icon —— sprite 名写在 key 里
icon = {
    key = GFX_decision_foo
    trigger = { original_tag = USA }
}

# 事件 desc —— 键写在 text 里
desc = {
    text = some.key
    trigger = { ... }
}
```

实测 110 个 icon 块中，108 个用第一种、2 个用第二种（同时决议全部用第二种）。

## 修法

三个采集函数，按结构分开处理：

```python
def _stmt_keys(block, key):     # title / desc：遍历所有同名语句
    for st in cw.get_all(block, key):
        Scalar → 收
        Block  → 收块内 text = 的值
```

```python
def _stmt_sprites(block, key):  # icon / picture：两种块结构
    Scalar → 收
    Block  → 有 key = 就只收它（且必须立即收手）
             否则收块内所有语句键
```

关键细节：

1. **`get_all` 不是 `get_one`。** 同名语句可以重复多次，只取第一个必丢。
2. **取到 `key =` 必须 `continue`。** 否则会继续落进「语句键即 sprite」分支，
   把同级的 `trigger` 当成贴图名。
3. **只取顶层键，不能 `walk` 深挖。** 条件表达式在**值**里，深挖会把
   `has_government`、`OR` 这些词当成 sprite 名。
4. **标量字段保留，另开 `pictures` / `*_keys` 列表。** 老的 `extra` / `title` /
   `desc` 被 `preview.py` 等消费方按「取一个来展示」使用，直接改成列表会炸。

校验侧用 `need_any()`：块里声明多个键时，**任一命中即通过**，不要求每个都在
（每个键对应一个触发分支，玩家只会看到其中一个）。

## 结果

| 指标 | DEVB-05 后 | 本次后 | 变化 |
|---|---|---|---|
| errors | 2079 | **1939** | -140 |
| 事件正文缺键误报 | 140 | **0** | -100% |
| 自检断言 | 234 | **246** | +12 |
| 变异测试 | 无 | **8/8** | 新增 |

减少的 140 条与预测的 140 条**精确相等**——不是「大概少了些」，是逐条对得上。

## 收益不只是少报 140 条

误报清零只是「不再吵人」。真正重要的是**被漏检的 112 处引用现在进了检查范围**：

修复前，你在国策 icon 块里写错一个 `GFX_` 名字，deep 校验**一声不响**。
修复后用最小 mod 验证，三类坏引用全部被抓：

```
info | 国策图标引用的 sprite 'GFX_focus_does_not_exist' 未在 mod 中定义
info | 国策图标引用的 sprite 'GFX_focus_also_missing'  未在 mod 中定义
info | 决议图标引用的 sprite 'GFX_decision_nope'        未在 mod 中定义
```

同时正确注册的两个 sprite 没被误报。

**假阴性（漏检）和假阳性（误报）是同一个 bug 的两面**：都是因为
「块没被读」。一边制造噪音，一边放走真错。

## 方法论：三条这次的教训

### 1. 修完一轮不要收工，再跑一次

DEVB-05 修完 11694 → 2079，降了 82%，很容易觉得「差不多了」。
但 2079 里还藏着 140 条同一性质的问题。**82% 的降幅掩盖了 100% 同类残留。**

判据：修完之后再跑一遍，把剩下的**逐条看**，而不是只看总数。

### 2. 「剩余问题」要按类型聚类，不能只看数量

2079 条如果只当数字，就是「还有硬错误」。按 `missing_key` 后缀聚类：

- 140 条 `.desc` → 事件正文
- 其余 → idea 真缺失（DEVB-05 已核对过是原版真没写）

**只有聚类才能看出「这 140 条是一类，而且是我造成的」。**

### 3. 变异测试暴露了 3 条无效断言

第一版 §16 写了 12 条断言，全绿。跑变异测试发现 3 条**改坏了也不报**：

| 断言 | 为什么不报 |
|---|---|
| 「块形式 desc 不再被当空串丢弃」 | 它断言 `desc == ""`，块被丢弃时它**正好成立**——断言写反了 |
| 「icon 块里的条件不会被当 sprite 名」 | 那条黑名单过滤一次都没命中过，删掉代码也不影响结果 |
| 「title 块内的键被采集到」 | 我把它标给了采集变异，但真正改坏的是校验回退，标错位置 |

修正办法：

- 第 1 条：改断言语义，且**本地化里故意不提供回退键**，让「块被丢弃 → 必然误报」
- 第 2 条：删掉没实测支撑的黑名单（110 个块的语句键 100% 是 sprite 名，没有例外），
  改成用 `walk` 深挖的变异来验证「只取顶层键」
- 第 3 条：补一条独立的校验侧断言，并给块内键**单独存在**的本地化

**全绿的断言等于没有断言。** 只有能让它报红的变异，才能证明它在测东西。

### 4. 顺手发现：文档数字核对也是「单向比较」

加完断言要改文档里的「N 项自检」，翻旧代码时发现这条核对本身有漏洞：

```python
# 旧：在 test_structure_doc 里比
claimed_counts = [int(m) for m in re.findall(r"(\d+)\s*项自检", doc)]
stale = [n for n in claimed_counts if n < _passed]   # ← 只查「文档 < 实际」
ok("文档的自检项数没落后于实际", not stale)
```

问题：**这一组跑的时候后面的组还没跑**，`_passed` 只有中间值（约 182）。
所以文档写 232 永远算「不落后」，实际早就 247 了也没人知道——
它只挡「文档写得比实际小」，挡不住「文档写得比实际大」，也挡不住滞后。

修法：这里只把数字存进全局，等 `main()` 全部跑完再**双向严格相等**：

```python
if _CLAIMED_SELFTEST_COUNTS:
    bad_counts = sorted({n for n in _CLAIMED_SELFTEST_COUNTS if n != total})
    if bad_counts:
        _failed.append(f"文档写的自检项数都等于实际（实际 {total}，文档写 {bad_counts}）")
```

改完立刻应验：文档写的 247 被判定不等于实际 246——**我之前那个 247 本身就是错的**，
因为写作时是把「一条新断言」算进去了，但那条断言在统计口径里已被其他条目覆盖。
这个错误靠单向比较永远发现不了。

**教训是通用的：凡是「拿 A 和 B 比」的断言，先问「比较的时机对吗、两个数都取全了吗」。**
拿中间态做比较，等于给自己发一张免死金牌。

## 相关

- `mcp-server/checks.py` — 新增 `_stmt_keys()` / `_stmt_sprites()`，改 4 处采集
- `mcp-server/checks.py` — `check_missing_loc` 的事件段改用 `need_any`
- `mcp-server/selftest.py` §16 — 13 条断言，8 个变异全部报红
- `mcp-server/selftest.py` — 自检项数改为 `main()` 里双向严格核对
- `tools/kiant-hoi4-mutate.py` — 变异测试工具（`python tools/kiant-hoi4-mutate.py`，改完校验逻辑就跑）
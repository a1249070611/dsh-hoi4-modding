---
title: 校验器维护手册（改校验逻辑前读）
domain: 99_plugin-devlog
scope: 怎么改校验器、怎么验自己改对了
verified_at: 2026-11-07
---

# 校验器维护手册

这份是给改 `mcp-server/checks.py`、`validators.py`、`selftest.py` 的人看的。
写 mod 的人不需要读——他们需要的判读方法在 `skills/kiant-hoi4-validator-trust/SKILL.md`。

## 一、假阳性：把原版当 mod 跑

原版是已知正确的语料。它跑出成百上千条 error，只有一个解释：校验器错了。

```
kiant_hoi4_self_check
```

或手工：

```python
import checks, kb
van = kb.find_game_dir()
r = checks.validate_mod(van, per_check=100000, max_issues=100000)
print(r["summary"]["breakdown"])
```

**判据是单向的**：

- 原版跑出大量 error → 大概率假阳性，**按类修，不要按条改**
- 原版跑出 0 条 → 只说明没有系统性误报，**不保证查得全**

后半句最重要。这个方法对假阴性完全无能为力，要靠第二节。

## 二、假阴性：变异测试

做法：故意把代码改回错误行为，看对应断言会不会报红。不报红 = 那条断言恒真，等于没写。

```
python tools/kiant-hoi4-mutate.py
```

改了一处校验逻辑、加了一条断言，就必须在 `MUTATIONS` 里加一条对应的变异。
规矩写在工具头注释里。

### 本项目的真实战绩

§16 第一版 12 条断言全绿，变异测试抓出 3 条无效：

| 断言 | 为什么无效 |
|---|---|
| 「块形式 desc 不再被当空串丢弃」 | 它断言 `desc == ""`，块被丢弃时正好成立，写反了 |
| 「icon 块里的条件不会被当 sprite 名」 | 那条黑名单过滤一次都没命中过，删掉代码结果不变 |
| 「title 块内的键被采集到」 | 预期标给了采集变异，真正改坏的是校验回退 |

这三条如果不删，会一直给人「测过了」的错觉。

### 锚点选不对，绿色是假的

同一条断言，选错变异点会得到「没被捕获」的假警告。踩过一次：

跨文档数字漂移那条断言，第一版变异把 `got = real` 改成让比较永远相等——
不报红，看着像变异无效。但它其实**让 `if got != real` 永不成立**，等价于把检测
拆掉，那不报红是对的。第二版变异清空被检查的文件元组——还是不报红。这次不是
变异的错，是**断言本身有漏洞**：只写了 `not stale_suspects`，一份都不扫同样是空
列表，检测被删掉和检测通过是同一个结果。

修法是让断言同时要求「扫满了 7 份文档」，被清空的元组立刻被抓到。

推论：**当变异没被捕获时，先怀疑断言，别急着怀疑变异。**

### 第三种情况：变异根本没改变行为

上一条说「先怀疑断言」，但还有更隐蔽的一种——**变异和原代码在语义上等价**，
断言当然不炸，因为什么都没坏。

实例：测 `_resolve_source_path()` 的「绝对路径原样保留」，变异写成

```python
# 原
if os.path.isabs(p):
    return os.path.normpath(p)
# 变异（把条件废掉，让它往下走到 join 分支）
if os.path.isabs(p) and False:
    return os.path.normpath(p)
```

在 Windows 上这个变异**没有任何效果**，因为 `os.path.join(root, "C:\\x")`
遇到绝对路径会丢弃前缀，直接返回 `"C:\\x"`。走 join 和直接 return 结果一样，
于是断言全绿、变异被判「无效」。

要让变异真的改变输出，得让下游逻辑做出不同的事：

```python
if os.path.isabs(p) and False:
    return os.path.normpath(p)
p = os.path.basename(p)      # 真的把绝对路径变成裸文件名
```

这样才炸。

**教训：变异没被捕获时，除了怀疑断言，还要确认变异真的改变了行为。**
验证办法很简单——把变异手工应用一次，打印同一个输入的输出，看和原版是否不同。
不同才是有效变异；相同说明你测的是平台特性，不是自己的规则。

这也解释了为什么 `os.path.join` 这类函数值得警惕：它对绝对路径有「丢弃前缀」的
副作用，很容易让「忘了判断绝对路径」的 bug 在 Windows 上看起来不存在。

## 三、统计口径：数字本身可能是假的

**展示用的列表不能用来做统计。**

```python
# 错：issues 已按 per_check 每类截断
issues = result["issues"]
n = len([i for i in issues if i.get("validator") == "localisation"])

# 对：breakdown 是截断前算的
n = result["summary"]["breakdown"]["localisation_missing_key"]
```

真实踩过：`per_check=400` 把 localisation 的 2041 条截成 400 条，于是报告写
「缺键 400」，真实值是 1879。误差 4.7 倍，且完全看不出来。

**推而广之：任何「从展示数据反推统计」的写法都要查一遍数据来源。**

## 四、修完不要收工：按类聚类

总数降下来不等于修完了。**82% 的降幅可能掩盖 100% 的同类残留。**

```python
import collections
c = collections.Counter(
    (i.get("validator"), i.get("kind"), (i.get("message") or "")[:30])
    for i in r["issues"]
)
for k, v in c.most_common(20):
    print(v, k)
```

真实例子：原版校验从 11694 降到 2079，看着降了 82%，聚类之后发现还剩 140 条
同一性质的事件缺键误报（`desc` 写成了条件块）。只看总数会以为已经干净了。

## 五、已确认的五类「原版这么写、引擎能跑、解析器读不懂」

这五条都是把原版当 mod 跑抓出来的，全部有原版行号。**改校验器，不要改文档去迁就。**

| 现象 | 原版证据 | 正确做法 |
|---|---|---|
| 命名空间大小写不一致 | `events/BBA_Switzerland.txt:30` 声明 `BBA_Switzerland`，55 个事件全写 `id = BBA_switzerland.N` | 折小写比较 |
| 字段名首字母大写 | `events/USA.txt:1487` 的 `Hidden = yes`；另有 8 处 `Picture = ...` | 用 `cw.get_one_ci` |
| 隐藏事件的空 option | 6950 个事件里 116 个零 option、9 个有 option 无名，全部 `hidden = yes` | 跳过 hidden 事件 |
| 事件预约被当成定义 | `history/countries/CZE - Czechoslovakia.txt:639` 的 `MUN_czech.6` | 按特征键区分，见 `_looks_like_event_definition` |
| 值可能是块 | `desc`/`title`/`icon` 的条件块写法，见 `DEVB-026` | 见 `references/10_internals/_index.md` |

第五条（值可能是块）的三种块结构互不通用，是最容易反复踩的坑：

| 字段 | sprite/键写在哪 | 原版处数 |
|---|---|---|
| 国策 `icon` | sprite 名当**语句键**，条件是值 | 108 |
| 决议 `icon` | sprite 名写在 `key =` 里 | 66 |
| 事件 `title`/`desc` | 键写在 `text =` 里，同名语句可重复多块 | 214 + 18 |

## 六、改动前的检查清单

要动校验逻辑，按这个顺序：

1. 先跑 `kiant_hoi4_self_check` 拿基线，记下 errors / breakdown
2. 改代码
3. 再跑一次，看目标类别是否下降、别的类别是否被带坏
4. 降的数字要能对得上预测。对不上说明改到了别的地方
5. 补断言 → 加变异 → `python tools/kiant-hoi4-mutate.py` 全绿
6. 聚类剩余问题，确认没有同类残留
7. 同步文档里的数字（自检项数、行数、工具数都有断言守着）

第 4 步很关键。原版那轮从 2079 降到 1939，减少 140 条，与「140 个事件缺正文键」
精确相等——数字对上才说明修因不是修表。

## 关联

- `skills/kiant-hoi4-validator-trust/SKILL.md` —— 给 modder 的报错判读版
- `99_plugin-devlog/DEVB-025` —— 原版当测试用例的完整记录
- `99_plugin-devlog/DEVB-026` —— 值可能是块的完整记录
- `99_plugin-devlog/DEVB-027` —— 大小写与宽容度的完整记录
- `mcp-server/selftest.py` §16 §17 —— 对应的回归断言
- `tools/kiant-hoi4-mutate.py` —— 变异测试
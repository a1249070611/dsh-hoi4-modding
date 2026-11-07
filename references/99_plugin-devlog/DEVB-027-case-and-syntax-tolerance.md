---
title: "DEVB-027 校验器对大小写和语法宽容度的假设全错了"
id: DEVB-027
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 阻断
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: DEVB-06 修完降到 1939，聚类剩余问题后仍有 5 类同性质误报
related: [99_plugin-devlog/DEVB-026-value-may-be-block.md, 99_plugin-devlog/DEVB-025-vanilla-as-testcase.md, 99_plugin-devlog/DEVB-024-verification-vs-execution.md]
---

# DEVB-027 校验器对大小写和语法宽容度的假设全错了

## 症状

DEVB-06 修完，原版 error 从 2079 降到 1939，减少的 140 条与预测精确相等。
按「修完不要收工，先把剩余问题聚类」的纪律再跑一次聚类：

```python
c = collections.Counter((i.get("validator"), i.get("kind"), i.get("message")[:30]) for i in issues)
```

前 5 类全部指向同一件事：**原版写得出来、引擎跑得通、我的校验器读不懂。**

| 类别 | 条数 | 表现 |
|---|---|---|
| 命名空间未在本文件声明 | 34 error | `'BBA_switzerland' 未在本文件声明` |
| 事件选项没有 name | 122 warn | `usa.50 的选项没有 name` |
| 无法解析的行 | 2 warn | `research_l_braz_por.yml:693` |
| 事件预约被当定义 | 5 error | `MUN_czech.6 的选项没有 name` |

## 根因

四个互相独立的假设，每一个都以为「原版会按我想的方式写」：

### 1. 大小写敏感 —— 引擎其实不敏感

```
events/BBA_Switzerland.txt:30    add_namespace = BBA_Switzerland   ← 大写 S
events/BBA_Switzerland.txt:73    id = BBA_switzerland.1            ← 小写 s
```

同文件里 55 个事件全用小写，`grep -c "id = BBA_Switzerland\."` 是 0，
而游戏正常注册。校验器做精确字符串比较，一个文件刷出 34 条 error。

同类还有**字段名**：`events/USA.txt:1487` 写的是 `Hidden = yes`（首字母大写），
另有 8 处 `Picture = ...`。`cw.get_one()` 精确匹配，于是 `hidden` 被读成空，
`hidden = yes` 的豁免（见下一节）根本不生效。

### 2. 隐藏事件也会被要求写选项名

先把 125 条「选项没有 name」按 `hidden` 分组，实测：

```
events 6950 个
  ├─ 零 option      116
  ├─ 有 option 无名   9
  └─ 有命名 option 6825
```

那 125 个**全部**是 `hidden = yes`。去原文看：

```
country_event = {
    id = lar_france_volunteers.2
    hidden = yes
    ...
    option = {}          ← 空块，只为让事件能触发
}
```

隐藏事件玩家永远看不到，原版大量直接写 `option = {}` 甚至干脆不写。
对它报「选项缺名称」是纯噪音。

### 3. history 里的事件预约不是定义

```
history/countries/CZE - Czechoslovakia.txt:639
country_event = { id = MUN_czech.6 days = 958 random_hours = 12 }
```

这是**预约触发**（给国家排定未来某天触发），事件本体定义在 `events/` 下。
旧代码不看结构，凡 `country_event = {` 块就收进定义表，于是这条预约被当成定义校验，
报「MUN_czech.6 的选项没有 name」——定义在别处，纯误报。

### 4. `str.splitlines()` 认的换行符不止 `\r\n`

`localisation/braz_por/research_l_braz_por.yml:693` 的原始字节：

```
... esconder. \n\xc2\x85o são só os submarinos ...
```

`\n` 是作者写的转义换行，紧跟的 `\xc2\x85` 是 **U+0085（NEL）** —— 一个错码字符。
`splitlines()` 把 NEL 也当换行符，于是把一行劈成两行：

```
行 693:  raider_patrols_desc: "Patrulhas ... esconder. \n      ← 前半截
行 694:  ão são só os submarinos que podem caçar."             ← 后半截，无键名
```

后半截没有 `KEY:` 前缀，于是报「无法解析的行」。**解析器自造的假错。**

`splitlines()` 认的换行符：`\n` `\r` `\r\n` `\v` `\f` `\x1c` `\x1d` `\x1e` `\x85` `\u2028` `\u2029`。

## 标准化方案

```python
# 1. 命名空间：折小写比较
nsset_lower = {s.lower() for s in nsset}
if ns and ns.lower() not in nsset_lower: ...

# 2. 字段名读取：用大小写不敏感的查找（cw.py 新增）
def get_one_ci(block, key):
    low = key.lower()
    for s in stmts(block):
        if s.key.lower() == low:
            return s
    return None

# 3. 隐藏事件跳过选项名检查
if not item.get("hidden"):
    ...  # 才检查 option 的 name

# 4. 事件预约不当定义
EVENT_DEF_MARKERS = {"title","desc","option","immediate","trigger",
                     "is_triggered_only","fire_only_once","mean_time_to_happen",
                     "picture","major","hidden", ...}
def _looks_like_event_definition(block):
    return any(st.key.lower() in EVENT_DEF_MARKERS for st in cw.stmts(block))

# 5. 本地化分行：只认 \n，且先归一化 \r\n
lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
```

**第 5 条有个坑："** 换成 `split("\n")` 之后，Windows 的 CRLF 文件每行尾部会留 `\r`，
语言头 `l_english:` 匹配不上，整文件被判「格式不对」。必须先归一化。
这一点是自检断言抓出来的——我第一版只写了 `text.split("\n")`，测试直接报红。

## 预防

- `cw.get_one_ci()` / `cw.get_all_ci()` 用于**读取字段值**；sprite 名等**标识符**
  仍要用大小写敏感的 `get_one()`，不能折叠
- 分类靠**结构特征键**，不靠字段名猜测（见 `_looks_like_event_definition`）
- 加行分隔处理时，永远先归一化 `\r\n`

新增 6 条回归断言（`selftest.py` §17），每条都配了变异，14/14 全部捕获。

## 验证

```
kiant_hoi4_self_check
→ errors 1939 → 1838，warnings 128 → 1
→ breakdown: 缺键 1815 / 语法 21（19 条 EOF 未闭合）/ 其它 3
→ verdict: 没有大面积误报迹象
```

逐类核对：

| 修复 | 消除 | 原版证据 |
|---|---|---|
| 命名空间大小写 | 34 | BBA_Switzerland 实例 |
| 隐藏事件豁免 | 122 | 6950 事件全量统计 |
| 字段名大小写 | 2 | `Hidden = yes` 2 处、`Picture` 8 处 |
| 事件预约 | 5 | MUN_czech.6 |
| splitlines | 2 | braz_por NEL |

## 教训

**「大小写敏感」是我自己加上去的严格性，不是引擎的要求。**
校验器比引擎严格，报出来的就是误报。凡是「我要求比原版更多」的地方，
都要先问一句：原版这么写，游戏跑不跑得起来？

这条的普适形式：**校验器的严格度上限 = 引擎的严格度。** 超出去的部分全是假阴性
换来的假阳性，没人会看 1 万条 error，等于没检查。
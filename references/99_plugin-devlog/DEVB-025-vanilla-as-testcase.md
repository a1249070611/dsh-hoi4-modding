---
title: "DEVB-025 把原版当 mod 跑：6 类系统性误报一次暴露"
id: DEVB-025
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 阻断
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: 用户要求「把原版游戏和工具联系起来看」
related: [99_plugin-devlog/DEVB-024-verification-vs-execution.md, 10_internals/_index.md, 08_fileformats/01_clausewitz-syntax.md]
---

# DEVB-025 把原版当 mod 跑：6 类系统性误报一次暴露

## 症状

工具跑了 2.9.3、自检 216/216 全绿。但我从没做过一件事：
**把原版游戏目录本身当成一个 mod 喂给校验器。**

跑了之后：

```
errors   = 11694
warnings = 19278
verdict  = 还有硬错误，进游戏会静默失效
```

原版游戏自己「进游戏会静默失效」——这显然不是原版的问题，是校验器的问题。

## 为什么自检没抓到

自检用的是 `examples/broken_mod/`（12 处注入缺陷）和 `examples/sample_mod/`
（一个我写的玩具模组）。**两个样本都是我自己写的**，用的是我理解的写法。

原版用的是**真实的、我没想到的写法**。自检只能验证「我想到的规则没写错」，
验证不了「我的规则假设本身对不对」。

这就是 DEVB-04 的同一个病换了位置：我把「我的测试过了」当成了「工具是对的」。

## 6 类误报，逐条实证

### 1. 行尾注释被判成解析失败 —— 19061 行

原版写法（`localisation/braz_por/aat_ideas_l_braz_por.yml:425`）：

```
 DEN_overlord_licensing_ns_desc: "$DEN_danish_licensing_ns_desc$" #TODO_DANNE; Refine
 FRLOC_A: "Sarajéviens" ## EN: Governorate of Sarajevo
```

旧正则 `^\s*(KEY)\s*:\s*\d*\s*"(.*)"\s*$` 要求**整行以右引号结尾**。
引号后面跟注释 → 匹配失败 → 判「无法解析」→ **键也没收进字典**。

连锁后果：这些键在 `check_missing_loc` 里又变成「缺少本地化」的 error。
**一个正则，两处伤害。**

实测：411 个文件、19061 行受影响；键从 149170 涨到 165115（**+15955，+10.7%**）。

修法：找最后一个右引号，只有它后面还有非空内容且含 `#` 时才截断。
**不能用「第一个 # 之前」**——文本里的 `#` 合法（颜色码 `§G#FF0000§!`、标题 `#`），
切在引号内会把译文改坏。

### 2. languages.yml 被当成词条文件 —— 90 条假「重复键」

原版 `localisation/languages.yml` 是**语言清单**：

```
l_english:
 l_english: "English"
 l_french: "Français"
```

它每节都列一遍所有语言名，所以 `l_english` 这个「键」重复 9 次。
这不是本地化内容，是元数据。当成词条扫就是 90 条纯噪音。

### 3. 纯注释文件报「缺语言头」

`localisation/french/career_profile_zelosissimo.yml` 全文是 LocEditor 生成的说明：

```
# === [LocEditor:RedundantFile] File contains no active keys, does not exist in English ===
# === [LocEditor:OrphanedKeys] Keys that do not exist in English ===
```

一条有效词条都没有。缺语言头**不算错**——没内容可生效。
判据：有词条却没语言头才报。

### 4. 国策 `text =` 重定向被忽略

`common/national_focus/ethiopia.txt:6049`：

```
focus = {
    id = ETH_peoples_army
    text = ETH_peoples_army_focus   #otherwise conflicts with Mass Assault doctrine peoples_army
```

**`text =` 才是引擎去查的本地化键，`id` 只是脚本内部引用名。**
只按 id 找键 → 误报「缺键」。

### 5. idea 的 `name =` 重定向被忽略 —— 最大单一来源

`common/ideas/GER.txt:726`：

```
GER_redirecting_naval_production_2 = {
    name = GER_redirecting_naval_production
```

同一个 idea 块在多个变体间复用同一段文本。

**实测：6563 个 idea 块里 1392 个（21.2%）用了 `name =`。**
这就是 idea 类误报 7102 条的主因。

### 6. `_desc` 被当成所有类型都必须 —— 误报 2800+ 条

实测原版各类的 `_desc` 覆盖率：

| 类型 | 总数 | 有 `_desc` | 覆盖率 | 结论 |
|---|---|---|---|---|
| focus | 10341 | 10335 | **100%** | 必需 |
| idea | 6515 | 1766 | **27%** | 可选 |
| decision_category | 1306 | 792 | **61%** | 可选 |
| decision | 4186 | 1387 | **33%** | 可选 |

只有国策的 `_desc` 是 100%——因为它决定国策详情面板，缺了是空白。
其余三类缺 desc 完全合法，悬停面板只显示标题和效果。

### 附带：事件正文 `.desc` vs `.d`

原版两种都在用：`.desc` **5209** 个、`.d` **1538** 个。
旧代码只试 `.d`，是`.desc` 的 1/3 都不到。

### 附带：`DEBUG_` 前缀

`common/decisions/CZE.txt` 里 `DEBUG_MUN_show_skoda` 这类，`allowed = { always = no }`，
玩家永远看不到，原版**故意不写本地化**。这类有 112 个。

### 附带：选项键的循环 bug

```python
for letter in "abcdef":
    key = f"{eid}.{letter}"
    if key in loc_keys:
        break
    issues.append({...})   # ← 在循环内！第一个字母 a 找不到就报 warn
```

原版大量事件只写 `.b`/`.c`。改成 `any(... for letter in "abcdefgh")`。

## 结果

| 指标 | 修复前 | 修复后 | 变化 |
|---|---|---|---|
| errors | 11694 | **2079** | **-82%** |
| warnings | 19278 | **128** | -99.3% |
| 本地化键 | 149170 | **165115** | +15955 |
| 本地化问题条目 | 19153 | **2** | -99.99% |

剩下 2079 条**全是原版真缺失**。我做了严格核对：随机抽 40 个报缺的 idea，
把 `localisation/english/` 全部 14MB 原文拼起来搜，**40 个全部一个字都搜不到**。
原版自己就有 1000+ 个 idea 没写本地化（多在 `hidden_ideas` 里，玩家看不到）。

**我没有为了让数字好看而去豁免它们。** 报出来是诚实的，只是不该报成 error。

## 方法：把原版当 mod 跑

这是这次唯一真正重要的收获，比 6 个 bug 更值钱。

```python
import checks
r = checks.validate_mod(VANILLA_ROOT, deep=False)
```

判据极其简单：

- 原版跑出大量 error → **工具错了**（原版是「标准答案」）
- 原版跑出 0 error → 工具至少没系统性误报（不保证查得全）

**一个永远不会有假阳性的校验器，和一个到处假阳性的校验器，后者更危险**——
因为没人会看 1 万条 error，等于没检查。

### 为什么我早没想到

因为我把「原版」当成了「参照物」，没想到它也可以当「测试用例」。
参照物和测试用例是同一个东西的两面：

```
原版 → 提供定义（参照物）
原版 → 提供正确写法（测试用例）   ← 我漏了这面
```

## 预防

1. **任何「校验器 / 检查器 / linter」，第一件事是拿「已知正确的大样本」跑一遍。**
   原版就是 HOI4 领域最好的那个样本：60366 个文件、真实工程、真实妥协。
2. **假阳性率比假阴性率更致命。** 假阴性用户会在游戏里发现；假阳性会让用户
   直接关掉工具。
3. **自检样本不能全自己写。** 自己写的样本只验证自己理解的写法。
   机制上要有一个「外部真实语料」的开关（本库是 `HOI4_VANILLA_DIR`）。
4. **数字不对先查口径，别急着改代码。** 我一开始以为是「缺 desc」，
   查下去才发现是「键根本没收到」——上游问题伪装成下游问题。
5. **报告时要区分「误报」和「真缺失」。** 剩下 2079 条我特意做了抽样核对，
   否则下一轮又会有人以为工具还有 bug。

## 相关

- `mcp-server/checks.py` — `scan_localisation` / `check_missing_loc` 的 6 处修正
- `mcp-server/selftest.py` §15 — 15 条回归断言，每条都做过变异测试
- `references/10_internals/_index.md` — 引擎如何处理本地化表
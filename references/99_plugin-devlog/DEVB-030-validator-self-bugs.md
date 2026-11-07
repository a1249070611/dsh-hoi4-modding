---
title: "DEVB-030 校验器一天内三次误报，根因是同一个"
id: DEVB-030
domain: 99_plugin-devlog
symptom_class: 校验器实现
severity: 警告
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: kiant-hoi4-dds.py 对正常 DDS 报「偏大」；kiant-hoi4-lint.py 在原版报 21 个不存在的问题
related: [tools/kiant-hoi4-dds.py, tools/kiant-hoi4-lint.py, DEVB-025]
---

# DEVB-030 校验器一天内三次误报

> 维护者条目。记录的是校验器自身实现错在哪几行。
> modder 遇到满屏报错、判断该不该信工具，看 `91_error-book/EB-016`。

写校验器的风险不在「抓不到错」，而在**「冤枉对的」**——误报会让人不再信任工具，
最后整个工具被弃用。这一天之内踩了三次，形态各不相同，但根因是同一个：
**把「我没想到的写法」当成「错误」。**

## 案例一：DDS 体积公式算错，反倒诬告文件偏大

### 症状

```
accept_decline_icon.dds
  72x21  DXT5  mips=1  文件 1.8 KB  ⚠ 偏大（单级理论 1440 B，实际 1728 B）
```

看着像文件损坏。

### 根因

```python
base = max(1, w // 4) * max(1, h // 4) * 16   # 错
```

DXT 块压缩必须**向上**取整。`21 // 4 = 5`，但 21 像素高需要 **6** 个块
（最后一行只覆盖 1 像素，也得占满一整块）。
正确：`ceil(72/4) × ceil(21/4) × 16 = 18 × 6 × 16 = 1728` ← 正好等于实际值。

**是我的公式错了，不是文件有问题。**

### 修法

```python
def _level_size(w, h, fmt):
    if "DXT1" in fmt:
        return ((w + 3) // 4) * ((h + 3) // 4) * 8
    if fmt in ("DXT3", "DXT5", "RXGB"):
        return ((w + 3) // 4) * ((h + 3) // 4) * 16
```

### 验证

拿 `gfx/` 下 **21898 个真实 DDS** 全跑一遍：**零例外全部精确匹配**。
这才是「验证过了」。只测自己造的那一个样本不算。

## 案例二：剥注释把引号里的 # 也剥了

### 症状

`common/ideas/SOV.txt` 报「花括号不配对」，但游戏能正常加载。

### 根因

```python
code_only = line.split("#")[0]     # 错
```

只认「第一个 # 之后全是注释」。但 HOI4 里引号内的 `#` 不是注释起点：

```clausewitz
NOT = { has_dlc = "No Compromise, No Surrender" }
```

这类写法虽然含 `#` 的情况不多，但 `split` 还会把字符串里任何 `#` 后面的
右括号一起切掉，凭空造出括号失衡。

### 修法

逐字符扫，跟踪引号状态：

```python
def strip_comment(line):
    inq = False
    for i, c in enumerate(line):
        if c == '"': inq = not inq
        elif c == "#" and not inq: return line[:i]
    return line
```

## 案例三：跨盘符 relpath 直接崩掉整个扫描

### 症状

```python
ValueError: path is on mount 'E:', start on 'C:'
```

用户去检查原版目录（`E:\Steam`），工具在 `C:` 盘，`os.path.relpath` 直接抛异常，
**整个进程挂掉**，一个结果都没输出。

### 修法

```python
def _short(p):
    try:
        return os.path.relpath(p, MOD_ROOT)
    except ValueError:
        return p            # 跨盘符时退回绝对路径
```

## 案例四（最重要）：原版文件被当成错误

修完上面三个后，扫原版 `common/` 2224 个文件，报 **21 个错误**。
但原版游戏能正常加载——**这说明我的判断标准错了，不是文件错了**。

逐个核实：

| 报错 | 实际 | 结论 |
|---|---|---|
| 14 个「末尾缺 `}`」 | 游戏正常加载 | **引擎把 EOF 当隐式闭合**，应降为 warning |
| 1 个「多余的 `}`」 | `TSR_lingguang...txt:420`，7 个块只闭合 6 次 | **真错**，原版自己的 bug |

最终 **1 error / 14 warning / 2214 干净**。

### 这一条的方法论

**当工具在原版文件上大量报错时，先假定工具错，别假定原版错。**
原版是 P 社自己发出去、几百万玩家跑过的，它「不合法」的概率远低于我的规则写错。

验证方法：找一个原版的**大样本统计分布**，看自己的规则和分布是否吻合。

## 通用预防

1. **误报比漏报更有害**。漏报只是没帮上忙，误报会让人不信工具。
2. **判断标准要跟引擎的实际行为对齐**，不是跟语法教科书对齐。
   少括号引擎容忍 → 就该是 warning；多括号引擎报错 → 才是 error。
3. **每条规则都要在原版全量上跑一遍**。单个样本通过不代表规则对。
4. **跨盘符 / 异常路径 / 空文件** 这些边界一开始就要想到，
   `relpath` 崩溃一次要重跑几分钟的全量扫描。
5. **改完工具要反向验证**：故意造一个错文件，确认能抓到；再拿正常文件，确认不误报。
   两头都测过才算完。

## 相关

- `tools/kiant-hoi4-dds.py` — `_level_size()`
- `tools/kiant-hoi4-lint.py` — `strip_comment()` / `_short()`
- `references/08_fileformats/01_clausewitz-syntax.md` §十一 引擎容忍边界
- `references/09_assets/01_dds-textures.md` §四 体积校验
- `91_error-book/EB-016` — 同一件事的使用者视角：报错该不该信、哪些可以先跳过
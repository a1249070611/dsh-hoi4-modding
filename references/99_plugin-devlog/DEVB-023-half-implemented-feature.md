---
title: "DEVB-023 功能只写了一半：docstring 说能查悬空引用，代码里 dead code"
id: DEVB-023
domain: 99_plugin-devlog
symptom_class: 工具流程
severity: 警告
verified_on: 1.19.4.2
verified_at: 2026-11-06
first_seen: 全量复查时用 AST 扫死函数，发现 kiant-hoi4-lint.py 里 collect_defs_and_refs 从没被调用
related: [08_fileformats/01_clausewitz-syntax.md, 99_plugin-devlog/DEVB-022-validator-false-positive.md]
---

# DEVB-023 功能只写了一半

## 症状

`tools/kiant-hoi4-lint.py` 的 docstring 写着：

```
Clausewitz 语法体检：括号 / 运算符 / 悬空引用。
用法：
    python tools/kiant-hoi4-lint.py --all --strict           # 悬空引用也算失败
```

但实际跑 `--strict` 只影响警告的退出码，**悬空引用压根没查**。

## 根因

代码里有两个半成品：

```python
# 这两个常量定义了，但全文件没人引用
DEF_KEYS = {"focus", "idea", "event", "option", "decision", "category"}
REF_KEYS = {
    "focus": "focus",
    "id": None,          # ← 自己都标了「语义随上下文变，不单查」
    "prerequisite": "focus",
    "mutually_exclusive": "focus",
    "completion_reward": None,
}

def collect_defs_and_refs(files):   # ← 定义了，但 main 从没调用
    defs = set()
    refs = []                       # ← 永远返回空
    ...
    return defs, refs
```

写完就搁下了，**只有 docstring 和 help 输出承诺了功能**。

## 怎么发现的

没用肉眼扫。用 AST 扫「顶层函数名在整个仓库里只出现 1 次」：

```python
occurrences = len(re.findall(r'\b' + name + r'\b', all_src))
if occurrences <= 1:
    print(f"疑似死函数: {p}:{n.lineno} {name}")
```

一次扫出 7 个，其中 6 个是 `@validator` 装饰器注册的（假阳性，装饰器本身就是引用），
剩下 1 个就是 `collect_defs_and_refs`。

> **检测脚本自己也会误报。** 装饰器注册、动态分发、`getattr` 反射都会让「零引用」
> 看起来像死代码。逐个核实再删，别批量清理。

## 修法：真把功能做出来

不是删代码了事——悬空引用是真实需求（引擎对这类错误完全静默，国策永远灰着）。

### 第一次实现：认错声明形态，刷出 966 条假阳性

原版 `common/national_focus/` 81 个文件跑出 966 条「悬空引用」。

```
✗ abdacom_shared_branch.txt:789  悬空引用：没有国策 id = ABDA_the_malay_barrier
```

但 `grep` 一下就知道它在同文件 596 行定义着：

```clausewitz
joint_focus = {          # ← 不是 focus
    id = ABDA_the_malay_barrier
}
```

我只认 `focus`，漏了 `joint_focus`。

### 第二次：还是错

加上 `joint_focus` 后降到 509 条。查下一个：

```
✗ baltic_shared.txt:836  悬空引用：没有国策 id = BALTIC_german_baltic_industry
```

定义在 790 行：

```clausewitz
shared_focus = {         # ← 第三种
    id = BALTIC_german_baltic_industry
}
```

### 第三次：归零

```python
FOCUS_DECL_KEYS = ("focus", "joint_focus", "shared_focus")
```

```
检查 81 个文件：1 个错误、0 个警告、80 个干净
悬空引用：0 条
```

**剩下那 1 个错误是真 bug**：`TSR_lingguang_incident_joint_branch.txt:420`
多余的 `}`（7 个 joint_focus 块只闭合 6 次），原版自己的问题。

## 关键教训：抄现成的实现，别重新想一遍

`mcp-server/checks.py` 的 `collect_definitions` **早就正确处理了三种形态**：

```python
for st in cw.get_all(tree.value, "focus"): ...
for st in cw.get_all(tree.value, "shared_focus"): ...
```

同一个仓库、同一个问题、别人已经写对过，我从零想，连错两次。

**写新模块前先 `grep` 仓库里有没有同类实现。** 有就照抄它的边界处理，
那不是偷懒，是避免重复踩坑。

## 预防

1. **docstring 里承诺的每个能力，必须有对应断言**。
   `kiant-hoi4-lint.py` 现在有 5 条悬空引用断言，覆盖三种声明形态 + 两个引用键 + scope 分离。
2. **功能没接进调用链，就别先写进 docstring**。写「TODO」都比写假的 help 好。
3. **AST 扫死代码可以定期跑**，但要人工核实装饰器/反射的情况。
4. **工具在原版全量上跑一遍**。这个功能第一版在原版上刷出 966 条，一眼就知道错了；
   只拿自己造的样例测，三条样例正好都用 `focus`，根本发现不了。

## 复现验证

```bash
# 原版上零悬空（除了那个真实的括号 bug）
python tools/kiant-hoi4-lint.py "E:/Steam/.../common/national_focus" --refs

# 造一个真悬空，必须被逮住
python tools/kiant-hoi4-lint.py /tmp/x --refs
#   ✗ a.txt:7  悬空引用：没有国策 id = A_does_not_exist
```

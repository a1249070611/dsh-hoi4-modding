---
title: "EB-009 改了原版内容但没生效（replace_path 与同名覆盖）"
id: EB-009
domain: 91_error-book
symptom_class: 游戏内行为
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 兼容性调整场景
related: [00_start/load-order-and-override.md, 06_workflow/compatibility.md]
---

# EB-009 改了原版内容但没生效

## 症状

你复制了原版某个文件、改了里面的数值、放进了 mod 对应路径，进游戏**毫无变化**，原版行为照旧。`error.log` 无报错。

## 错误做法（我试过的）

1. 以为文件没被读到，反复检查 `.mod` 的 `path` 和目录结构 → 路径正确
2. 以为是加载顺序问题，调整 `.mod` 列表顺序 → 无效
3. 以为是改的地方不对（以为改错了字段）→ 核对后字段是对的
4. **加了 `replace_path` 想着"强制替换"** → 结果更糟：原版该目录**全部消失**，相关功能大面积失效

## 根因

两个机制被混淆了：

| 机制 | 行为 |
|---|---|
| **同名文件覆盖** | mod 里 `common/ideas/germany.txt` 会覆盖原版同名文件。未加 `replace_path` 时，引擎按加载顺序取 mod 的文件 |
| **`replace_path`** | **整目录替换**，不是合并！用了它，原版该目录下**所有文件全部消失**，只剩你给的 |

第 4 条错误做法的危险性在于：`replace_path = "common/ideas"` 会让原版**所有国家**的 ideas 文件消失，而不只是你想改的那个。游戏可能仍能启动，但大量内容缺失，且未必报错。

还有一个隐蔽点：**如果你只复制了原版文件的一个片段**（比如只保留德国那段），配合 `replace_path` 后，其余内容就真的没了。

## 标准化方案

```bash
# 1. 先看清当前 mod 到底覆盖了什么、新增了什么
#    MCP: kiant_hoi4_list_overrides
```

2. **默认不要用 `replace_path`。** 只改某几项时，正确做法是：

   - 方案 A（推荐）：新建一个文件，用**同 ID 覆盖单个块**
   - 方案 B：复制原版整个文件，改其中几行，放在同路径（同名覆盖）

3. 确实需要整目录重写时才用 `replace_path`，且必须把你需要的原版内容**全部**搬进你的目录。

4. 检查现有 `replace_path`：

```bash
grep -rn "replace_path" *.mod descriptor.mod
```

## 预防

- `kiant_hoi4_list_overrides` 会读取 `replace_path` 并标出影响范围
- 写 `.mod` 时，`replace_path` 每加一行都要问："这个目录下原版还有什么我需要的？"

## 验证

1. 进游戏确认你要改的地方变了
2. **同时确认原版其他内容还在**——这是最容易被漏掉的检查项
3. `kiant_hoi4_list_overrides` 显示的覆盖范围符合预期

## 备注

**这条坑的核心是"以为 replace_path 是合并"。** 名字里的 "replace" 已经说清楚了，但直觉上容易读成"替换我想替换的部分"。实际是替换整个路径。

判断你当前是否踩了这个坑：如果游戏能启动但"有些原版内容不见了"，且 `error.log` 没有对应报错，先查 `replace_path`。

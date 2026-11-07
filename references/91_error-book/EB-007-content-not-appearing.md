---
title: "EB-007 写了国策/事件/决议但游戏里完全不出现"
id: EB-007
domain: 91_error-book
symptom_class: 游戏内行为
severity: 阻断
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 内容系统通用场景
related: [02_content/_index.md, 02_content/events.md]
---

# EB-007 写了国策/事件/决议但游戏里完全不出现

## 症状

脚本文件写好了、语法看起来也对，`error.log` 可能干净，但游戏里**完全没有**这个国策/事件/决议。不是"不生效"，是"压根不存在"。

## 错误做法（我试过的）

1. 以为是文件没被加载，反复检查目录名和 `.mod` 的 `path` → 目录是对的
2. 以为语法错，逐行核对括号 → 括号平衡，语法没问题
3. 以为是本地化缺失导致不显示 → 补了 loc，还是不出现（因为不是显示问题，是没被注册）
4. 以为是 DLC 限制 → 关掉 DLC 判断，还是不出现

## 根因

主要有三种，症状相同但根因完全不同：

| 根因 | 机制 |
|---|---|
| **事件缺 `add_namespace`** | 事件 ID 是 `namespace.number` 形式，namespace 未声明则整个 ID 无法解析，事件不注册 |
| **ID 与别的 mod 撞车被覆盖** | 同 ID 在另一个 mod 里也有定义，加载顺序靠后者**覆盖**前者，静默生效，不报错 |
| **文件名与原版同名** | 例如 `common/national_focus/germany.txt`，除非你用了 `replace_path`，否则你的文件与原版同名时可能整个被忽略或被覆盖 |

第一种最容易被忽略，因为 `add_namespace` 写在文件顶部，看起来像注释。

## 标准化方案

```bash
# 1. 查重复 ID（定位覆盖问题）
#    MCP: kiant_hoi4_find_duplicate_ids
```

```bash
# 2. 查 namespace 声明
grep -rn "add_namespace" events/*.txt
# 每个事件文件都应有一行 add_namespace = your_namespace
```

```bash
# 3. 查文件名是否与原版撞车
#    对比你的目录和 <GAME_DIR> 下同名路径
#    MCP: kiant_hoi4_list_overrides 可以列出「覆盖原版」与「新增」
```

三条都过一遍，基本能定位。

## 预防

- 所有自定义 ID 加 `NAMESPACE_` 前缀（如 `mymod_ger_industry`），避免跨 mod 撞车
- 每个 `events/*.txt` 顶部固定写一行 `add_namespace = xxx`
- 新文件名不与原版同名，除非明确要覆盖
- 写完跑 `kiant_hoi4_validate_mod`，它会查 namespace

## 验证

1. `kiant_hoi4_find_duplicate_ids` 报告 0 个重复
2. `kiant_hoi4_validate_mod` 通过
3. 游戏内该内容出现

## 备注

**判断技巧**：如果是"某些内容消失、另一些正常"，优先怀疑 ID 覆盖（只影响撞车的那个）；如果是"整批都没了"，优先怀疑 namespace 缺失（影响整个文件）。这个分叉能省一半排查时间。

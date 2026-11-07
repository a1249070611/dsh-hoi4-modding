---
title: "EB-003 科技页方框都在但连线一条没有（静默失败）"
id: EB-003
domain: 91_error-book
symptom_class: 界面显示
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: hist_tech_trees（2900 科技多国科技页）
related: [02_content/technologies.md, 90_case-studies/tech-tree-gridbox.md]
---

# EB-003 科技页方框都在但连线一条没有

## 症状

科技树页面打开，**所有科技方框正常显示、图标正常、名称正常**，但**一条前置连线都没有**。`error.log` 干净，没有任何相关报错。

这个症状极具欺骗性：内容都在，看起来只是"线没画出来"，很容易怀疑是 GUI 或贴图问题。

## 错误做法（我试过的）

1. 以为是连线贴图（`GFX_technology_...line`）缺失 → 补齐贴图，无效
2. 以为是 `gridbox` 尺寸不够，调大 `position` 和 `slots` → 无效
3. 以为是坐标超出页面，逐个挪科技位置 → 无效，且挪到哪都没线
4. 以为是 GUI 文件的 `containerWindowType` 问题 → 无效

## 根因

`common/technology_tags/` 下 `technology_folders` 的 **`available` 块里写了 `has_country_flag` 之类的条件**。

引擎在构建科技树时，`available` 只认 `original_tag`。一旦里面出现 `has_country_flag` 这类运行时条件，**整页的连线构建会被静默丢弃**——不报错、不警告，方框照常渲染（方框是另一套渲染路径）。

关键点：**方框渲染和连线渲染是两条独立路径**，所以才会出现"框在、线无"这种半残状态。

## 标准化方案

```bash
# 1. 找出违反规则的 folder
grep -rn -A5 "technology_folders" common/technology_tags/ | grep -B2 "has_country_flag"
```

2. 把 `available` 改成只用 `original_tag`：

```
technology_folders = {
    my_folder = {
        available = {
            original_tag = GER          # 正确
            # has_country_flag = my_flag  ← 删掉这行
        }
        ...
    }
}
```

3. 如果确实需要运行时条件控制科技可见性，改用**单个科技**上的 `allow_branch` / `path` 等机制，不要放在 folder 的 `available` 里。

## 预防

- `kiant_hoi4_validate_mod deep=true` 的 `technology` 校验器会查 folder 结构
- 写完 technology_tags 后专门 grep 一次 `has_country_flag`，成本极低

## 验证

进游戏打开该科技页，确认：
1. 连线出现
2. 前置关系正确（不是全连在一起）
3. 该页所有 folder 都正常

## 备注

**这是本库记录的最贵的一个坑**：症状指向 GUI，根因在数据结构，两者隔了三层。完整排障过程见 `90_case-studies/tech-tree-gridbox.md`，含 6 步修复配方和 RVA 级原理分析。

教训：**引擎的"静默失败"往往发生在两条渲染路径交界处。** 当一部分正常、一部分完全消失时，先怀疑数据供给被截断，而不是怀疑渲染本身。

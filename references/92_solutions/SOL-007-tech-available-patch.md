---
title: "SOL-007 批量修补 tech_folder 的 available 条件"
id: SOL-007
domain: 92_solutions
status: upstream-only
source: skills/hoi4-modding/tools/tech_folder_available.py
verified_on: 未验证（本插件未实现）
verified_at: 2026-11-06
---

# SOL-007 批量修补 tech_folder 的 available 条件

## 它想解决什么

错题本 `EB-003` 记录的坑：`technology_folders` 的 `available` 里写了 `has_country_flag` 之类的运行时条件，导致**整页连线静默消失**。

如果项目里已经写了大量这样的 folder，手工一个个改很痛苦。这个工具做批量修补。

## 思路

上游 `tech_folder_available.py` 三个模式：

```bash
# 检查：列出所有违规的 folder
python tools/cli.py tech available <mod> --check

# 修补：把违规条件替换成 original_tag
python tools/cli.py tech available <mod> --apply --yes

# 回滚：从备份恢复
python tools/cli.py tech available <mod> --revert
```

**`--revert` 是关键设计**：批量改写脚本必须可回滚，否则改错了没有退路。

修补策略推测是把 `available` 块内的运行时条件删除，或替换成 `original_tag`。

## 为什么没被采用

本插件的 `validate_mod deep=true` 里 `technology` 校验器能**检测**这类问题，但只报告不修补。

当时的判断是：自动改写用户脚本风险太高（可能改坏语义），只做检测更安全。

## 如果要用，怎么验证

1. 读上游 `tech_folder_available.py`，重点看它**怎么决定替换成什么**——这一步是风险点
2. 在测试 mod 上先 `--check` 看命中列表
3. `--apply` 后跑 `kiant_hoi4_validate_mod deep=true` 确认违规清零
4. 进游戏确认连线出现了，且**前置关系正确**（不是因为全删而乱连）

验证标准：违规清零 + 连线恢复 + 科技前置关系未被破坏。

## 备注

**这是「检测 vs 自动修复」的典型权衡。**

检测永远安全，修复才省时间但可能改坏。一个好做法是：检测报告里直接给出「改成什么」的具体建议文本，让用户复制粘贴——既省了打字，又不承担自动改写的风险。

如果本插件要补这个，我倾向做成"生成修补建议"而不是"直接改写"。

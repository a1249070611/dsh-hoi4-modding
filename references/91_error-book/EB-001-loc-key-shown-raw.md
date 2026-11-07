---
title: "EB-001 界面显示 loc key 原样文字（如 GFX_xxx / some_key）"
id: EB-001
domain: 91_error-book
symptom_class: 界面显示
severity: 严重
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: 本地化排查通用场景
related: [05_presentation/localisation.md, 02_content/_index.md]
---

# EB-001 界面显示 loc key 原样文字

## 症状

游戏界面上本该显示「工业技术」的地方，显示成 `tech_industry_name`；本该显示图标的地方显示 `GFX_tech_industry` 字样。

`error.log` 里可能有一行：

```
[19:23:41][persistent.cpp:58]: Error: "Unknown key tech_industry_name in localisation"
```

但**也可能一行都没有**——某些情况下缺 loc 只是静默显示键名。

## 错误做法（我试过的）

1. 以为是键名拼错了，于是把脚本里的 `tech_industry_name` 改成别的 → 没用，因为脚本这边才是对的，缺的是 loc 条目
2. 以为 `.yml` 文件放错目录，于是复制到 `localisation/english/` 和 `localisation/` 两处 → 反而制造了重复键
3. 只看 `l_english` 有没有，忽略了目标语言包 → 中文用户看到的是 `l_simp_chinese` 缺失

## 根因

三层都可能断，且断在不同层的表现不同：

| 断点 | 表现 |
|---|---|
| 脚本里的键名与 `.yml` 里的键名不一致（含大小写） | 显示键名 |
| `.yml` 缺 UTF-8 BOM | 整个文件被静默忽略，该文件所有键都"不存在" |
| `.yml` 语言头写错（如 `l_english:` 前有空格） | 该语言整段失效 |
| 目标语言包不存在该键 | 回退到 `l_english`；`l_english` 也没有则显示键名字号 |

**`.yml` 必须 UTF-8 带 BOM** 这一条是最容易漏的。没有 BOM 时游戏不报错，直接跳过整个文件。

## 标准化方案

```bash
# 1. 先跑本地化专项扫描，看清断在哪一层
#    MCP: kiant_hoi4_scan_localisation
#    CLI: python tools/cli.py loc audit <mod>

# 2. 自动补 BOM / 转编码（默认 dry_run，只报告）
#    MCP: kiant_hoi4_fix_localisation  dry_run=true  先看
#    MCP: kiant_hoi4_fix_localisation  dry_run=false 再改
```

手工确认三件事：

```bash
# BOM 是否存在（输出应为 efbbbf）
head -c 3 localisation/english/mymod_l_english.yml | xxd

# 语言头是否顶格（前面不能有空格）
head -1 localisation/english/mymod_l_english.yml

# 键名是否逐字一致（注意大小写）
grep -n "tech_industry_name" localisation/english/*.yml
grep -rn "tech_industry_name" common/
```

## 预防

- 写完任何脚本内容后跑 `kiant_hoi4_validate_mod`，它默认就查「缺失本地化键」
- `.yml` 一律用带 BOM 的 UTF-8 保存，别用记事本默认的 ANSI
- 中文包 `l_simp_chinese:` 与英文包同时建，哪怕内容是占位——避免发布前批量补

## 验证

改完后确认：

1. `head -c 3 xxx.yml | xxd` 输出 `efbbbf`
2. `kiant_hoi4_scan_localisation` 报告 0 个缺失键
3. 游戏里该处显示正常文本

## 备注

键名大小写敏感这一点常被忽略：`Tech_Industry_Name` 和 `tech_industry_name` 是两个不同的键，都能通过语法检查，但只有一个能匹配上。

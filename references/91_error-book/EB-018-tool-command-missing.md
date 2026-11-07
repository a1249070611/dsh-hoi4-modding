---
title: "EB-018 参考库里的工具命令在新插件里不存在"
id: EB-018
domain: 91_error-book
symptom_class: 工具流程
severity: 一般
verified_on: 1.19.x
verified_at: 2026-11-06
first_seen: v2.7.x 参考库移植后核对
related: [07_tools/_index.md, 92_solutions/_index.md]
---

# EB-018 参考库里的工具命令在新插件里不存在

## 症状

照着 `references/07_tools/` 里的示例执行：

```bash
python tools/cli.py tank probe --game "E:/Steam/.../Hearts of Iron IV" --mod <mod>
```

报「文件不存在」或「命令不存在」。但这份文档明明就在参考库里，还写了详细参数。

## 错误做法（我试过的）

1. 以为路径写错了，反复试 `tools/cli.py`、`./tools/cli.py`、`scripts/cli.py` → 都不存在
2. 以为要装什么东西 → 没有安装步骤，因为根本没有这个文件
3. 读了半篇文档才发现示例全是这样 → 时间已经浪费了

## 根因

**参考库来自上游项目 `dsh-hoi4-modding`，那套工具是 CLI 命令（30 个）；本插件把它们改成了 MCP 工具（17 个）。**

`07_tools/` 的 15 篇是上游原文，按「正文一字不改」的溯源原则保留了原样，所以里面的示例仍然指向 `python tools/cli.py xxx`。

对应关系不是一对一的：30 个命令里有约一半没迁移，部分命令合并进了 `validate_mod deep=true`。

## 标准化方案

**先查对应表，不要照抄示例命令。**

| 文档里写的命令 | 本插件对应 | 状态 |
|---|---|---|
| `python tools/cli.py lint` | MCP `kiant_hoi4_validate_mod` | 已迁移 |
| `loc audit` | `kiant_hoi4_scan_localisation` + `fix_localisation` | 已迁移 |
| `gfx audit` | `validate_mod deep=true` | 已迁移 |
| `tech audit` / `tech sprites` | `validate_mod deep=true` | 已迁移 |
| `errorlog` | `kiant_hoi4_analyze_error_log` | 已迁移 |
| `parse` | `kiant_hoi4_parse_script` | 已迁移 |
| `init` | `kiant_hoi4_scaffold kind=mod` | 已迁移 |
| `map audit` | — | **未实现** |
| `model chain-check` | 仅查文件存在性 | **部分实现** |
| `font audit` / `font list` | — | **未实现** |
| `tank probe` / `tank layout` | — | **未实现** |
| `dds make/solid/check` | — | **未实现** |
| `icon import` | — | **未实现** |
| `install` / `uninstall` | — | **未实现** |
| `tech available --apply` | 仅检测，不修补 | **部分实现** |
| `doctor` | — | **未实现** |
| `reference build` | — | **未实现** |

未实现的那些，思路和参数语义收录在 `92_solutions/`，可查可试。

## 预防

- 读 `07_tools/` 任何一篇时，先看 `07_tools/_index.md` 顶部的状态声明
- 看到 `python tools/cli.py` 就意识到这是上游示例，需要查上表转换

## 验证

MCP 工具是否可用：`kiant_hoi4_validate_mod` 能正常返回结果即为通。

## 备注

**这条是自己踩的坑**：移植参考库时只核对了文件内容一致性（MD5 全部一致），没核对「文档里的命令是否还能跑」。内容溯源做对了，可用性没做。

教训：**移植文档时，"文字没改"和"照着做能用"是两件事。** 后者需要单独验证一遍。

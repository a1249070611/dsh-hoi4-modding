---
title: "self-test：离线自检（CI 用）"
domain: 07_tools
scope: 不需要游戏与 Mod，用临时样本验证工具链自身的 15 个用例
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py self-test
  - tools/selftest.py
---

# `self-test`：离线自检

改工具代码、升级 Python、CI 里打包前跑一次。不需要游戏、不需要任何 Mod，自动在临时目录造样本。

```bash
python tools/cli.py self-test            # 人读：15 行 PASS/FAIL + 汇总
python tools/cli.py self-test --json     # 机器读：summary.results 是逐用例列表
python tools/cli.py self-test --verbose  # 额外打印每个用例的细节
```

退出码：`0` 全部通过、`1` 有用例失败、`2` 工具自身起不来、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 15 个用例

| 用例 | 验证什么 |
|---|---|
| `imports` | 23 个工具模块都能 import（含 legacy 脚本实现） |
| `dds.header` | 造一个 32×16 raw32 DDS，头解析正确、`multiple_of_four` 为真 |
| `dds.truncated` | 截断文件不崩溃，`valid=False` |
| `loc.happy` | 最小 Mod 的 2 个 loc 引用都能找到定义 |
| `loc.missing` | 删掉一个定义后报 `loc.missing`，退出码 1 |
| `gfx.happy` | gfx sprite 与 DDS 闭合 |
| `gfx.texture_missing` | `texturefile` 指向不存在的贴图时报错 |
| `lint.happy` | 完整样本 0 error / 0 warning |
| `lint.broken` | 括号不闭合 + 贴图缺失 + `.mod` 缺 path → 至少 3 error，含 `syntax.parse`/`gfx.texture_missing`/`mod.sibling_mod_missing` |
| `map.empty` | 没有地图层内容时不崩溃，给 `map.nothing_to_check` |
| `model.empty` | 没有 3D 内容时不崩溃，给 `model.nothing_to_check` |
| `map.broken_no_crash` | 故意坏的 map 文件不抛异常 |
| `paths` | 游戏探测能跑通（有游戏则命中，没有也不崩） |
| `doctor` | 环境体检能跑通并给出 summary |
| `cli.json_contract` | 嵌套调用 `lint --json`，校验 `{ok, exit_code, command, problems[], summary{}}` 五键与退出码一致 |

样本 Mod 由 `build_sample(root, broken=False)` 生成：`descriptor.mod`、`common/ideas`（`st_test_idea` + `picture = "GFX_st_test_idea"`）、`events`（`title = st_title` / `desc = st_desc|st_missing_desc`）、`localisation/english/*_l_english.yml`（带 BOM）、`interface/selftest.gfx`、64×64 raw32 DDS、同级 `<dir>.mod`（**绝对路径**，否则会触发 `mod.path_relative`）。`broken=True` 时额外写括号不闭合的 `common/ideas/broken.txt` 与指向缺失贴图的 sprite。

## 输出示例

```text
# hoi4mod self-test（2.0.0）
PASS imports            23/23 模块可 import
PASS dds.header         valid=True 32x16
...
PASS cli.json_contract  exit=1 五键齐全
15/15 PASS
```

## `--json`

```json
{"ok": true, "exit_code": 0, "command": "self-test",
 "problems": [],
 "summary": {"results": [{"name": "imports", "ok": true, "detail": "23/23"}, ...],
             "passed": 15, "failed": 0, "temp": "C:\\...\\Temp\\hoi4mod-selftest-xxxx",
             "errors": 0, "warnings": 0}}
```

临时目录每次新建，跑完保留（便于失败时看样本）；可以放心删。

## 什么时候必须跑

- 改了 `tools/**` 任何 `.py`；
- 改了 `scripts/*.py` 薄 shim；
- 升级 Python 大版本；
- 发布前（`npm pack` 之前），和 `pytest tests/py` 一起跑。

## 已知限制

- 用例只覆盖「主路径 + 1 个失败样例」，不覆盖真实游戏数据的兼容性（那靠 `.tmp/audit/runs/sweep*.csv` 那种全量回归）。
- `paths`/`doctor` 用例只要求「能跑不崩」，不要求本机一定装了游戏。
- 嵌套 `cli.json_contract` 会临时改写全局输出状态，跑完已复原；不要在其它线程里并发调用。

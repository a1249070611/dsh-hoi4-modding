---
title: "tank：坦克设计器布局与实测"
domain: 07_tools
scope: 读 1.19 的 tank_designer_view.gui，实测窗口/槽位坐标，或生成 16/18 槽布局
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py tank probe / tank layout
  - tools/tank_designer_probe.py / tank_designer_layout.py
---

# `tank`：坦克设计器布局与实测

18 槽设计器（1.19 的 `common/units/equipment/modules` + `interface/tank_designer_view.gui`）改起来最容易「进游戏才发现槽位叠在一起」。两个子命令：**probe 只读实测**，**layout 生成布局**。

```bash
# 只读：打印窗口尺寸、模块区、预览区、每个槽位坐标、底盘槽数
python tools/cli.py tank probe --game "E:/Steam/.../Hearts of Iron IV" --mod <mod>

# 生成布局（不写游戏目录；--dry-run 只看计划）
python tools/cli.py tank layout --game "..." --mod <mod> --out <输出.gui> --preset 18-compact --dry-run
python tools/cli.py tank layout --game "..." --mod <mod> --out <输出.gui> --preset 18-compact
```

退出码：`0` 成功、`1` 有问题（probe 目前恒 0）、`2` 找不到文件/缺参数、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## `tank probe` 看什么

- 窗口 `size = { width = 1091 height = 542 }`（以及其它预设高度）；
- `equipment_modules` 的 `position`/`size`；
- `equipment_preview` 的 `position`/`size`，背景 sprite 指向的 DDS 实际宽高（小于窗口会提示）；
- 每个 `pos_custom_module_slot_window_N` 的 `(x, y)`（宏 `@fixed_btn_mod_col_*` 会展开）；
- `equipment_designer_module_slot_entry` 模板尺寸；
- 被移到屏幕外的元素（`-4000,-4000` 之类）；
- 模块数量（`common/units/equipment/modules/*.txt` 里 `equipment_modules` 一层子块，按 category 统计）；
- 底盘槽数（`tank_chassis.txt` 里 `is_archetype = yes` 的 `module_slots`）。

输出里会给出「槽位位置数 vs 底盘槽数」的结论，例如 9 个位置对应 9 槽。

`tank probe` 的 JSON 结构是旧工具输出转的：`{"command": "tank probe", "summary": {"mod": "...", "exit": 0, "lines": N, "log": ["...每行..."]}}`。

## `tank layout` 的预设

| preset | 说明 | 关键参数 |
|---|---|---|
| `16-compact` | 16 槽紧凑 | 窗口 1091×542，`rows=(0,50,300)`，`row_slots=(7, 2, 7)` |
| `18-compact` | 18 槽紧凑 | 同上尺寸，`rows=(0,50,300)`，`row_slots=(7, 4, 7)` |
| `16-tall` | 16 槽加高 | 窗口高 760，`preview=(2,182)`，`rows=(22,100,486)` |

其它参数：`--height`（覆盖窗口高）、`--background-sprite`（换背景 sprite 名）。

布局做了什么：

1. 改窗口 `size` 与 `equipment_modules`/`equipment_preview` 的位置尺寸；
2. 重写槽位段（`@fixed_btn_mod_col_0..6 = 72*i`、`row_0..2`、`positionType ypos_module_row_N`、`pos_custom_module_slot_window_N`；第二排按 `row_slots` 取列）；
3. 隐藏底部/预览相关元素（`reset_button`、`duplicate_button`、`save_button`、`experience_bg`、`experience`、`resources_bg`、`production_resources`、`refit_cost`、`production_value`），或按 `window_h - 542` 下移；
4. 括号配平检查，然后写 `--out`。

**安全边界**：`--out` 不允许指向游戏目录（会拒绝），因此不会误改原版文件；要生效自己把产物拷进 Mod 的 `interface/`。

## 已知限制

- 只按 1.19 的 `tank_designer_view.gui` 结构做替换；大改过的 GUI（自定义控件名）会提示找不到目标。
- 不改 `equipment_designer_module_slot_entry` 的图标贴图，也不改 `common/` 里的模块数据。
- 槽宽 76px 与 72px 列距的原版叠压是已知现象，layout 只按列距排，不解决像素级重叠。
- `tank layout` 需要 `--mod` 或 `--out`；都没有时报「缺 --mod 或 --out」（退出 `2`）。

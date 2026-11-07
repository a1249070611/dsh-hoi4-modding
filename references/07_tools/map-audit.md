---
title: "map audit：地图 / 州 / 战略区一致性"
domain: 07_tools
scope: definition.csv、default.map、history/states、strategicregions、buildings、supply 之间的引用是否闭合
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py map audit
  - tools/map_audit.py
  - 实测：23 个工坊 Mod
---

# `map audit`：地图 / 州 / 战略区一致性

地图层最容易出「莫名其妙进不了游戏」「某州没有归属」「supply 节点失效」。这个命令把 province / state / strategic region / building 的引用对一遍。

```bash
python tools/cli.py map audit <mod> --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"
python tools/cli.py map audit <mod> --json=map.json
```

退出码：`0` 无问题、`1` 有 error/warning、`2` 找不到 Mod、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 为什么要 `--game`

绝大多数 Mod 只加 `history/states/*.txt`，不自带 `map/definition.csv`。这时命令会：
1. 用**原版** `map/definition.csv` 建立 province 基准（`map.definition_from_game`，info）；
2. 只校验 Mod 自己有的 state / strategicregions / buildings。

没有游戏目录又没有 `definition.csv` 时，只会给 `map.no_definition` 提示，不会瞎报错。

## 读什么文件

- `map/definition.csv`：`id;r;g;b;type;continent;...`（分隔符 `;`，跳过表头）
- `map/default.map`：`max_provinces`、`definitions`、`continents`、`sea_starts`
- `history/states/*.txt`：`id`、`provinces = { ... }`（也支持裸值列表）
- `map/strategicregions/*.txt`：`id`、`provinces`
- `map/buildings.txt`：每行 `<province>; <building>; <level>`
- `common/supply_nodes.txt` / `common/supply_areas` 类：state/province 引用

## rule ID

| rule | 级别 | 含义 / 怎么修 |
|---|---|---|
| `map.province_duplicate` | error | definition.csv 里 province id 重复 |
| `map.province_color_invalid` | error | RGB 越界或全 0（保留色） |
| `map.state_id_bad` | error | state id 非数字/≤0 |
| `map.state_duplicate_id` | error | 两个 state 用了同一个 id |
| `map.province_multi_state` | error | 同一 province 被多个 state 认领 |
| `map.state_province_missing` | error | state 引用了 definition.csv 里没有的 province |
| `map.sr_id_bad` / `map.sr_duplicate_id` | error | strategic region id 非法/重复 |
| `map.sr_province_missing` | error | 战略区引用了不存在的 province |
| `map.building_province_missing` | error | buildings.txt 里的 province 不存在 |
| `map.supply_state_missing` | error | supply 节点引用了不存在的 state |
| `map.supply_province_missing` | error | supply 节点引用了不存在的 province |
| `map.default_map_bad` | error | `max_provinces`/`definitions` 等字段缺失或非法 |
| `map.definition_encoding` | error | definition.csv 编码不是 UTF-8/ANSI 预期 |
| `map.max_provinces_small` | error | `max_provinces` 小于实际使用的最大 province id |
| `map.province_type_unknown` | warning | type 不是 land/sea/lake 等已知值 |
| `map.max_provinces_bad` | warning | `max_provinces` 不是整数 |
| `map.definitions_ref_missing` | warning | default.map 指向的 definition 文件不存在 |
| `map.sea_start_missing` | warning | `sea_starts` 里的 province 不存在 |
| `map.state_parse_fail` / `map.buildings_parse_fail` | warning | 文件解析失败（先修语法） |
| `map.continent_unknown` | warning | continent 名不在 default.map 的 continents 列表 |
| `map.default_map_missing` | warning | 有 `map/` 但没有 default.map |
| `map.definition_from_game` | info | 用原版 definition.csv 作基准 |
| `map.no_definition` | info | 没有可用 definition.csv（无法校验 province 引用） |
| `map.nothing_to_check` | info | Mod 没有地图层内容，跳过 |

## `--json` 关键字段

```json
{"ok": true, "exit_code": 0, "command": "map audit",
 "problems": [],
 "summary": {"mod": "...", "provinces": 13414, "province_source": "game",
             "states": 0, "strategic_regions": 0, "max_provinces": 13414,
             "omitted_by_code": {}, "omitted_total": 0}}
```

## 已知限制

- 不解析 `map/*.bmp`（地形图/高度图），像素层面的问题查不出。
- 不校验 continent 的 RGB 映射，只校验名字是否出现在 default.map。
- supply 相关文件各家 Mod 写法差异大，解析失败时给 warning 而不是硬报。

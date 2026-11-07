---
title: "model chain-check：3D 模型四层闭环"
domain: 07_tools
scope: .mesh → pdxmesh 声明 → entity → animation 四层引用是否闭合，找出白模/不显示/无动画的根因
verified_on: 1.19.x
verified_at: 2026-11-06
sources:
  - tools/cli.py model chain-check
  - tools/model_chain.py
  - 实测：BlackICE / TNO / MD / Kaiserreich
---

# `model chain-check`：3D 模型四层闭环

HOI4 的 3D 模型要四层都接上才会显示，缺任何一层表现为「白模 / 不显示 / 站桩无动画」。这个命令把四层引用对一遍。

```bash
python tools/cli.py model chain-check <mod> --game "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV"
python tools/cli.py model chain-check <mod> --json=model.json
```

退出码：`0` 无问题、`1` 有 error/warning、`2` 找不到 Mod、`3` 不适用。

> **⚠️ 本篇讲的是上游项目的 CLI，本插件里没有 `tools/cli.py`。**
> 照着敲命令会报 `No such file or directory`。
> 该用本插件的工具时，查 `STRUCTURE.md` 的 MCP 工具表，或直接用
> `kiant_hoi4_validate_mod` / `kiant_hoi4_self_check` 等 `kiant_hoi4_*` 工具。
> 保留这一页是因为**里面的检查思路和判据仍然有效**，可以照着思路自己实现。
> 对照关系见 `91_error-book/EB-018-tool-command-missing.md`。

## 四层

```text
L1  .mesh 文件                gfx/models/**.mesh
L2  pdxmesh 声明              pdxmesh = { name = "x" file = "gfx/models/.../x.mesh" }
                              （常在 gfx/entities/*.gfx 的 objectTypes = { ... } 里）
L3  entity                    entity = { name = "x" pdxmesh = "x_mesh" }
                              或 entity = { clone = "另一个 entity" name = "x" }
L4  animation                 animation = { name = "x_idle_animation" file = "x_idle.anim" }
```

## 解析细节（踩过的坑，改模型时对着看）

- **声明不一定在顶层**：`gfx/entities/*.gfx` 通常写成 `objectTypes = { ... }`，所以工具递归遍历整棵树。
- **`animation` 的 `file` 相对声明文件目录**：`gfx/models/units/infantry/GER/vehicles/x.asset` 里写 `file = "x_idle.anim"` 指的是同目录；工具按「声明文件目录 → Mod 根」两级解析。
- **DLC 内容按 `gfx/` 根合并**：`integrated_dlc/dlc022_waking_the_tiger/gfx/models/units/artillery/a.mesh` 与声明里的 `gfx/models/units/artillery/a.mesh` 是同一个逻辑路径（工具建了 `gfx/` 后缀索引）。
- **原版声明分散在 DLC**：只扫 `game/gfx` 时原版 pdxmesh 声明只有 473 个，加上 `dlc/*/gfx` 与 `integrated_dlc/*/gfx` 后是 2045 个；漏扫会把「引用原版模型」误报成缺失。
- **clone 是合法的继承**：`entity = { clone = "building_generic_dam" name = "building_dam" }` 不需要自己写 pdxmesh。
- **音效/特效 entity 没有 mesh 是正常的**：`ambient_wind_entity`、`overrun_effect_entity` 这类原版同名实体本来就没有 pdxmesh。

## rule ID

| rule | 级别 | 含义 / 怎么修 |
|---|---|---|
| `model.mesh_file_missing` | error | pdxmesh 声明的 `file` 或 entity 直接引用的 `.mesh` 不存在 |
| `model.anim_file_missing` | error | animation 声明的 `file` 不存在 |
| `model.mesh_undeclared` | error | entity 引用的 pdxmesh 在 Mod 与原版都没有声明（拼写错/漏 L2） |
| `model.entity_no_mesh` | error | entity 既没 pdxmesh 也没 clone（白模/不显示的典型） |
| `model.entity_clone_missing` | error | clone 目标不存在 |
| `model.mesh_no_file` | warning | pdxmesh 声明缺 `file=` |
| `model.orphan_mesh` | info | Mod 里的 `.mesh` 没有被任何声明引用（素材还没接完） |
| `model.entity_no_mesh_vanilla` | info | 原版同名 entity 也没有 pdxmesh（环境音效/特效） |
| `model.no_game` | info | 没找到游戏，原版声明不计入，可能误报 |
| `model.nothing_to_check` | info | Mod 没有 3D 内容 |

## 典型修法

- 改完 `pdxmesh`/`entity` 忘了同步 `file=` 路径 → `model.mesh_file_missing`。
- 新模型只放了 `.mesh`，没写 pdxmesh 声明 → `model.orphan_mesh`，进游戏看不到。
- 换车体后 entity 还指向旧 mesh → 看 `model.mesh_undeclared` 的 entity/mesh 对。
- 三轮车/坦克「不动」→ 先确认 `animation` 的 `.anim` 在同目录或根路径能解析到。

## `--json` 关键字段

```json
{"ok": true, "exit_code": 0, "command": "model chain-check",
 "summary": {"asset_files": 97, "mesh_files": 2195, "anim_files": 2146,
             "mesh_decls": 1059, "anim_decls": 103, "entities": 2351,
             "game_mesh_decls": 2045, "game_anim_decls": 1993, "game_entities": 5678,
             "declared_meshes_used": 931, "meshes_declared_in_game": 13,
             "omitted_by_code": {}, "omitted_total": 0}}
```

## 已知限制

- 不检查 `.mesh`/`.anim` 二进制内部（骨骼、locator、动画帧），只查引用闭合。
- entity 的 `state`/`locator`/`attach` 不做语义校验。
- 原版与 DLC 声明依赖游戏目录；离线时 `meshes_declared_in_game` 会是 0。

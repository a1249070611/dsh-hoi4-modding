# 1.19 改过位置的路径：别照旧教程找

**结论**

1. **地形**：`common/terrain/00_terrain.txt`。`map/terrain.txt` 已不存在。
2. **学说**：`common/doctrines/{folders,grand_doctrines,tracks,subdoctrines}/`。不再是科技树里的 `path` 线性树。
3. **装备**：`common/units/equipment/`。**没有** `common/equipment/` 这个目录。
4. **阵营**：`create_faction` 已废弃，改 `create_faction_from_template` + `common/factions/`。
5. **2D sprite 定义**：`interface/*.gfx`。原版 `gfx/interface/` 下**一个 `.gfx` 都没有**（0 个），那里只放 `.dds`。
6. **补给区**：`map/supplyareas/` 只剩 1 个文件 1 个定义，绝大多数由引擎按州/战略区自动生成。旧教程「每区一个文件」作废。

**依据**

在 `<GAME_DIR>`（你的 HOI4 安装目录）直接 stat 验证：

```
MISS  common/equipment
OK    common/units/equipment
OK    common/terrain/00_terrain.txt
MISS  map/terrain.txt
OK    common/doctrines
OK    interface/core_chinese.gfx
OK    documentation
OK    common/decisions/_documentation.md
```

前六条与参考库 `references/` 的 `02_content/`、`03_military/`、`04_world/`、`05_presentation/` 一致。
第 6 条（补给区）参考库自己标了 ⚠️，属「本地文件观察 + 推断，官方文档未说明」——不是硬结论。

**易错**

- 写 `common/equipment/` 不会报错，只是**静默不加载**。装备代码看着完全正确，游戏里就是没有。
- 改 `map/terrain.bmp` 只改「画面上是什么地形」，战斗修正来自 `common/terrain/00_terrain.txt` 的 `categories`。两个都改才生效。
- 把 sprite 定义放进 `gfx/interface/*.gfx` 是社区习惯，原版没有先例。本插件的 `assets` 校验器对两处都扫，但照原版放 `interface/` 最稳。

**适用版本**

1.19.4.2 实测。这些是 1.18 → 1.19 的变更点，跨版本前先读 `references/06_workflow/migration.md`。

---

顺带记一条环境问题：本插件 2.2.0 之前的 `kb._steam_libraries()` 只查 `C:\Program Files (x86)\Steam`，
Steam 装在 `E:\Steam` 时永远找不到游戏，导致所有依赖原版的检查悄悄降级为 info。
已改为「注册表 `SteamPath`/`InstallPath` + 逐盘扫描 + 环境变量 `HOI4_GAME` 优先」。
如果发现校验结果全是 info，先跑 `kiant_hoi4_kb_build action=discover` 看 `game_dir` 是不是空的。

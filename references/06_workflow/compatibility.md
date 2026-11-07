---
title: 兼容性（覆盖式 vs 补丁式 / 加载顺序 / 冲突 / replace_path / 校验和）
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - https://hoi4.paradoxwikis.com/Modding
  - https://hoi4.paradoxwikis.com/Mod_structure
  - https://hoi4.paradoxwikis.com/Replace_path
  - checksum_manifest.txt
  - dlc_load.json
---

# 兼容性

基线 **1.19.x**。本文「顺序/语义」结论来自 wiki `Modding` 与 `Replace_path`（采信度 B），**校验和覆盖范围来自游戏根目录的 `checksum_manifest.txt`（A）**，`.mod` 真实写法来自 1.19.x 用户目录下 25 个 `.mod`（A）。

## 1. 唯一的加载顺序（记住这一条，其余都是推论）

```
原版(游戏根目录)
  → DLC（按内部 ID / 发售顺序）
  → 用户目录（Nudger 输出、你自己放的文件）
  → mod（按用户特定 descriptor 的【文件名】排序）
```

推论清单：

| 推论 | 说明 |
|---|---|
| 后加载覆盖先加载 | 同路径同名文件，只有后加载的那份存在 |
| **mod 之间的顺序看 `.mod` 文件名** | `aaa.mod` 先于 `zzz.mod`；与 `name=`、与启动器列表顺序无关 |
| 只有 `dependencies` 能改顺序 | `dependencies = { "其它 mod 的 name" }` → 本 mod 排到对方之后 |
| `replace_path` **不改顺序** | 它只是「卸载此前已索引的文件夹内容」 |
| 用户目录优先级高于原版 | 这就是 Nudger 输出会污染本机原版的原因 |
| DLC 文件夹不能靠 `mod/dlc/` 覆盖 | 要按真实加载位置放，如 `modname/music/mtg_music.txt` |

## 2. 覆盖式 vs 补丁式：推荐哪一种

| 方式 | 做法 | 优点 | 缺点 | 建议 |
|---|---|---|---|---|
| **覆盖式（整文件替换）** | 复制原版 `events/Generic.txt` 到 mod 改一行 | 立刻生效、无需钩子 | 原版一更新，你的旧副本会**回退原版的所有新内容**（灾难） | **仅用于最后手段** |
| **新增文件式（推荐）** | 新文件放 `common/national_focus/hho_tree.txt` | 无冲突、原版更新不影响 | 不能改原版已存在条目 | **首选** |
| **补丁式（运行时注入）** | 用 `on_actions` / 事件 / `scripted_effects` 在运行时修改 | 最兼容；可与其他 mod 共存 | 不能改「开局前就必须定下」的数据（如州归属） | **内容型改动的首选** |
| **`replace_path` 卸载** | 整个文件夹替换 | 大地图/大 overhaul 必需 | 会让「该类型数据库为空」而 CTD；影响所有其它 mod | **危险，只在 overhaul 用** |

**判定流程**：

```
要改的东西「在开局前就必须确定」吗（history/states、history/countries、map/、tech 前置）？
├─ 是 → 新增文件 or（必要时）replace_path
└─ 否 → 运行时注入（on_actions/事件/决议/scripted_effects），不碰原版文件
```

## 3. `replace_path` 到底怎么用（最容易「配了不生效」）

```pdx
# 用户目录 mod/hho_hello.mod           ← 必须写
# hho_hello/descriptor.mod             ← 也必须写
replace_path = "history/states"
replace_path = "map/strategicregions"
```

硬性事实：

1. **两个 `.mod` 都必须写**。只写 mod 特定的那份 → 不生效；只写用户特定那份 → 启动器会把 mod 特定那份里的删掉。wiki 明确。
2. **只卸载「主菜单加载时索引的文件夹」**。以下用 `replace_path` **无效**：
   - `history/units`（走 `oob = "TAG_1936"` 直接链接）
   - `gfx/flags`（换意识形态时按命名规则读）
   - `gfx/loadingscreens`（会自动加载；`replace_path` 只能清掉原版加载图，但主菜单背景仍来自 sprite 直接链接）
3. **不改变顺序**。想让你的文件压过另一个 mod，得用 `dependencies`。
4. **滥用会 CTD**。wiki `Troubleshooting` 列的典型：`common/national_focus`、`history/states`、`common/unit_leader` 被清空 → 该类型条目为 0 → 崩溃。**替换任何文件夹都必须至少放一个同类型文件进去**。
5. **文件名大小写「近似」导致的重复加载，`replace_path` 管不了**：`events/Generic.txt` 与 `events/GENERIC.txt` 会各加载一次。**文件名必须完全一致或完全不同**。

## 4. 多 mod 冲突的判定方法（不启动游戏也能做一半）

```bash
# 1) 列出两个 mod 的「同路径同名文件」= 直接覆盖关系
comm -12 \
  <(cd modA && find . -type f | sort) \
  <(cd modB && find . -type f | sort)

# 2) 找「同 ID 定义」（更隐蔽，靠 grep 你的命名空间/原版 ID）
grep -rn "^HHO_\|^focus_tree = {" modA/common/national_focus modB/common/national_focus

# 3) 看 dependencies 声明是否与文件名顺序冲突
grep -H "^dependencies" mod*/*.mod
```

判定表：

| 冲突形式 | 表现 | 谁赢 |
|---|---|---|
| 同路径同名文件 | 只有一份生效 | 后加载者（按 `.mod` 文件名 / `dependencies`） |
| 同 ID 的数据库条目（两个不同文件里都有 `state 123`） | 可能双份都进内存 → 行为不可预期 | **取决于解释顺序**（文件按 ASCII 排序解释，先解释者常胜）⚠️ 需实测 |
| 同 sprite 名（`.gfx`） | 只有一份贴图 | 后解释者（`zz_` 前缀可提高优先级） |
| `replace_path` 撞车 | 文件被整体卸载 | 加载顺序中更高的那个 mod 之后的内容才会留下 |

## 5. 校验和与联机（工程决策的真正约束）

游戏根目录 `checksum_manifest.txt` 实际覆盖：

```
common/  (**.txt, **.lua, 含子目录)
events/  (**.txt)
history/ (**.txt)
map/     (**.txt, **.map, **.bmp, **.csv)
```

| 你改了什么 | 改校验和？ | 联机 | 成就 |
|---|---|---|---|
| `common/` `events/` `history/` `map/` 任一条目 | ✅ 改 | 需所有人同 mod 同版本 | 失效 |
| 仅 `localisation/` | ❌ 不改 | 可与原版联机（这就是汉化包能联机的原因） | 通常仍可 |
| 仅 `gfx/` `interface/` | ❌（不在清单） | 同上 | ⚠️ 未实测 |
| `defines`（在 `common/`） | ✅ 改 | — | — |

→ **产品化建议**：把「纯文本/翻译」与「改数值」拆成两个 mod。翻译 mod 不破坏校验和，玩家接受度最高。

## 6. 与其它 mod 共存的推荐写法

1. **新建文件**，文件名带自己的命名空间：`common/national_focus/hho_hello_focus.txt`。
2. **运行时注入**：`common/on_actions/hho_on_actions.txt` 里用 `on_startup` 初始化，而不是覆盖 `history/countries/`。
3. **不要动 `history/states/`**（除非做地图 mod）—— 这是冲突最高的目录之一。
4. `defines` 要改就用「覆盖式」但**只放你要改的那几个 define 的完整文件**（wiki 说 defines 用 override 文件几乎是必须的）。
5. 发布时在描述里写清 `dependencies`，别让玩家手动排序 —— 顺序不由玩家拖动决定。

## 常见错误 / 自检清单

- [ ] 是否先问过「这个改动能不能用运行时注入」？
- [ ] 覆盖了原版文件吗？如果覆盖了，原版下一次更新你怎么办？
- [ ] `replace_path` 是否两个 `.mod` 都写了、且替换的文件夹里至少有一个文件？
- [ ] 是否确认自己没制造「大小写近似」的同名文件？
- [ ] 是否清楚自己的改动会不会改校验和（能不能联机）？
- [ ] `dependencies` 里的 mod 名是否逐字符一致（含 `–` vs `-`）？
- [ ] 是否把「翻译」和「改数值」拆成了两个 mod？

---
title: 调试（-debug_mode / 控制台 / error.log 定位 / 增量排查）
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - launcher-settings.json
  - console_commands_documentation.md
  - https://hoi4.paradoxwikis.com/Modding
  - https://hoi4.paradoxwikis.com/Troubleshooting
  - error.log
---

# 调试

基线 **1.19.x**。凡运行时的描述都注明来源：是「wiki 描述」还是「实测已验证」。

## 1. 开调试模式：`-debug_mode`，不是 `-debug`

启动器生成的 `launcher-settings.json` 里，「以调试模式打开游戏」这个 alternate executable 定义是：

```json
"exeArgs": [ "-gdpr-compliant", "-debug_mode" ]
```

而 wiki 至今写 «Do this by adding **-debug** to your launch options»。
→ **统一用 `-debug_mode`**（启动器文件是 A 级证据）；`-debug` 是否仍被识别未验证，不要依赖。

其它有用的启动参数（wiki `Modding`/`Troubleshooting`，采信度 B）：

| 参数 | 作用 |
|---|---|
| `-debug_mode` | 调试模式（启动器默认写法） |
| `-crash_data_log` | 崩溃时在 `crashes/<时间>/meta.yml` 写 `LastRead: 文件 (行号)`；**同时隐含开调试**，但会显著降速 |
| `-checksum` | 在 `system.log` 输出校验和明细，可与他人对比找出差异文件 |
| `-start_tag=ALB` | 直接以某国开局（wiki 示例） |

## 2. 调试模式能给你什么（wiki 描述）

1. **热加载**：改 mod 文件后不用重启就生效 —— 但**只对启动时已存在的文件**生效，且下列目录**永不**热加载：
   - `history/countries/`
   - `history/states/`
   - `map/`
   （例外：`load_oob` 这种直接链接、GFX 这种直接引用图片路径的可以生效，但贴图会显示为错误颜色，需重启）
2. **地图错误不崩**：有 `MAP_ERROR` 时正常模式会拒绝启动，调试模式继续加载。
3. **更全的 error.log**：部分错误只在调试模式记录（尤其 MAP_ERROR）。
4. **错误日志自动弹出**：有错时加载完/选完国家会自动打开；右下角「错误狗」图标点击可再开。
5. **主菜单可按 `` ` `` 看 GUI 元素名/sprite 名**（等价于 `gui` 命令）。
6. **鼠标悬停省份显示 ID/归属**；悬停国旗显示 tag/original_tag/cosmetic tag。
7. **解锁部分开发者控制台命令**。
8. **悬停 GUI 元素 Ctrl+Alt+右键** 打开调试菜单，可直接跳到该元素的 `.gui` 定义文件。
9. 和平会议自动存档。

> ⚠️ 性能代价：wiki 明说调试模式会**关掉多人**且**性能下降**。别在「测性能」时开着调试模式做对比。

## 3. 控制台命令（命令名以本机文档为准）

游戏自带 `documentation/console_commands_documentation.md`（2046 行，**A 级**）核对过的实用命令：

| 命令 | 作用 | 备注 |
|---|---|---|
| `reload_textures`（别名 `rt`, `reload_texture`） | 重载贴图（可带过滤关键字） | wiki 写的 `reload texture` 不是真名 |
| `reloadinterface` | 重载全部 `.gui` | 调界面必备 |
| `reloadfx` | 重载 shader | |
| `reloadtechnologies` | 重载科技库 | 出错会崩 |
| `reloadoob <TAG>` | 重载某国 OOB | |
| `update_loc` | 重载指定本地化 key | wiki 的 `reload localization` 实际是它 |
| `updateequipments` / `updatesubunits` | 重载装备/单位 | |
| `debug` | 运行时切换调试模式 | 只给「最后 4 项」调试收益（wiki） |
| `tag <TAG>` / `event <id>` / `effect <...>` | 切国家 / 触发事件 / 跑效果 | 测试自己写的东西 |
| `tdebug` | 调试 tooltip（州/省 ID 等） | wiki 列 |
| `timer` / `timer_start` / `timer_stop` / `timer_dump` / `timer_reset` | 脚本耗时 | 性能排查唯一量化手段 |
| `nudge` | 进地图编辑器 | 用它退出会崩 |

完整清单别背 —— `grep "^## " documentation/console_commands_documentation.md` 就有 700+ 条。

## 4. error.log 定位法（核心工作流）

### 4.1 先建立预期：日志里绝大多数不是你的错

实测基线（1.19.3，14664 行）：`is a dynamic token ... OOS` 4273 行、`script enum` 2757 行、`Unrecognized equipment upgrade` 2098 行、`duplicate division name` 1133 行……**合计 >95% 出自原版文件**。
→ **目标不是「清零」，而是「找到属于我的那几行」。**

### 4.2 四步过滤

```bash
LOG="<用户目录>/logs/error.log"

# ① 只看加载期（没有游戏日期）的错 —— 通常是数据结构/描述文件问题
grep -n "no_game_date" "$LOG" | head -50

# ② 只看与你相关：ID 前缀 / 文件名
grep -n "<你的ID前缀>\|my_mod" "$LOG"

# ③ 只看「必管」类别
grep -n "Invalid supported_version\|Unexpected token\|Could not find sprite type\|Unknown effect\|Unknown trigger\|Invalid event target" "$LOG"

# ④ 统计变化（改动前后对比总量，而不是逐条读）
wc -l "$LOG"
```

### 4.3 三条判读规则

1. **路径是虚拟根**：报 `common/technologies/NSB_armor.txt` 并不意味着「原版的问题」——如果你 mod 里有同名文件覆盖了它，错误就来自你的副本。**先 `ls mod/*/common/technologies/`。**
2. **`[no_game_date]` vs `[1936.01.01.12]`**：前者是加载期（数据结构、`.mod`、GFX 定义），后者是游戏内（GUI 构建、事件/国策求值）。看到 `Could not find sprite type` 带游戏日期，就说明是**界面建出来的时候**才缺 sprite。
3. **`Invalid event target`（如 `controller: invalid event target: controller`）**：dual scope 指向了不存在的对象（如无主州）。它会被**每 tick 刷屏**，且可能引发崩溃。规避写法：

```pdx
if = {
    limit = { is_subject = yes }
    overlord = { country_event = hho_example.0 }
}
```

### 4.4 完整逐条解读

逐条分类用 `python scripts/errorlog_triage.py <error.log>`（按类别聚合、给计数与典型原文），再按 §4.3 的三条判读规则定位到自己的文件；分层校验方法见 [validation.md](validation.md)。

## 5. 崩溃（CTD）排查：二分法

wiki `Troubleshooting`（B 级）给的流程，配合用户目录 `crashes/` 下每次崩溃的目录：

```
1. 加 -crash_data_log 启动 → 复现崩溃 → 打开 crashes/<时间>/meta.yml
   找 "LastRead: <文件> (<行号>)"
2. 若 LastRead 是文件最后一行 → 真正崩的可能是「下一个被读的文件」，继续往下猜
3. 二分：把 mod 里的文件夹成批移除（先移一半），直到定位到单个文件
   - 可以保留必要的 replace_path（history/states、map/strategicregions），其它先去掉
4. 定位到文件后，再二分「块」：注释掉一半的条目
```

wiki 列的**最常见的 CTD 原因**：
- `replace_path` 把某类型数据库清空（`common/national_focus`、`history/states`、`common/unit_leader`）；
- state 的 `victory_points` 指向不存在的省份；
- `map/buildings.txt` 不完整（海军基地找不到出海省 → 死循环 → 崩）；
- `tutorial/tutorial.txt` 没有 `tutorial = { }`；
- `common/ai_templates` 找不到可用模板（有师模板却没 AI 模板）。

## 6. 增量排查法（推荐的开发节奏）

```
1. 基线：空 mod（只有 3 个描述文件）→ 启动 → 记录 error.log 行数与 checksum
2. 每次只加「一类文件」：
   common/ → events/ → localisation/ → interface/ + gfx/ → history/
   每加一类就启动一次，记录 error.log 行数增量
3. 一旦某次增量爆炸，问题就在这一类里
4. 最后再做「组合验证」：与另一个 mod 同时启用，看是否冲突
```

配套自检：

| 步骤 | 期望 | 不符就是有问题 |
|---|---|---|
| 只放描述文件 | error.log 行数 = 基线 ± 0 | 描述文件格式错（`supported_version`/`thumbnail`） |
| 加 `common/national_focus` | 无新增「Invalid focus」 | focus 的 `id`/`x,y`/`icon` 有问题 |
| 加 `localisation` | 游戏内不显示 key 原文 | 缺 BOM / 语言目录错 / key 拼错 |
| 加 `interface/*.gui` | 无 `Could not find sprite type` | `.gfx` 里没定义那个 sprite |

## 7. 不启动游戏也能做的静态调试

- 括号平衡、`UTF-8`/`BOM`、本地化 key 与 ID 对应 → `python scripts/hoi4_lint.py <mod>`。
- GFX 引用存在性：`grep -rn "GFX_xxx" interface/ gfx/` 与 `grep -rn 'name = "GFX_xxx"' gfx/interface interface/` 两边都要有。
- 效果/触发器合法性：`grep -n "^### <key>" documentation/effects_documentation.md`，再 `grep -rn "<key>" common/` 找真实用例。

## 常见错误 / 自检清单

- [ ] 用的是 `-debug_mode` 还是过时的 `-debug`？
- [ ] 是否知道改了 `history/states`、`history/countries`、`map` 必须重启？
- [ ] 是否把 error.log 里的原版噪声当成自己的 bug？
- [ ] 报错路径是原版路径时，是否检查了「我有没有覆盖这个文件」？
- [ ] 崩溃时是否先看 `crashes/*/meta.yml` 的 `LastRead`？
- [ ] 是否用「一次只加一类文件 + 对比行数」而不是一次性堆完再找？
- [ ] 控制台命令名是否与本机 `console_commands_documentation.md` 一致？
- [ ] 是否记得 error.log 每次启动被重写（要先备份）？

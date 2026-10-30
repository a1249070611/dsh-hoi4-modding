# 科技树 UI：页面 / 连线 / 大小框（HOI4 1.19.3 实战）

> 本文来自一次真实排障的完整复盘：一个 2900 科技、多国专属科技页的大型 Mod，
> 出现"某国科技页方框全在、连线一条没有、error.log 干净"，以及"合并拆页后配件全变大框"。
> 下面每条结论都在 1.19.3.0 上通过**游戏内对照实验**证实，并给出可复制的配方。
> 文中的 RVA 是本机 `hoi4.exe` 静态反汇编得到的排查线索，**版本更新后会变，只作原理参考**。

## 0. 一句话铁律

| 想做什么 | 唯一正确做法 |
|---|---|
| 让某个国家的科技页出现连线 | folder 的 `available` 用 **`original_tag = XXX`**，**绝不要用 `has_country_flag`** |
| 同一页里"大框 + 小框"混排 | 小框科技加 `force_use_small_tech_layout = yes`，**并且**把 `GFX_technology_<folder>_small_*_item_bg` 指向真正的小图 |
| 页面完全不显示 | 检查 `available` 是不是被写成 `always = no` + `NOT = {...}`（AND 关系 = 永远 false） |

## 1. 四类文件与数据模型

| 位置 | 作用 |
|---|---|
| `common/technology_tags/00_technology.txt` | `technology_folders = { <folder> = { available / ledger / doctrine } }`：**页面注册表**（决定页面是否存在、对谁可见） |
| `common/technologies/*.txt` | 科技本体：`folder = { name = <folder> position = { x y } }` 决定它落在哪一页的哪个格子 |
| `interface/countrytechtreeview.gui` | 页面容器 `<folder>`、页签 `<folder>_tab`、格子容器 `gridboxtype name = "<分支根>_tree"`、item 模板 `techtree_<folder>_item` / `_small_item` |
| `interface/*.gfx` | item 背景精灵 `GFX_technology_<folder>_<state>_item_bg` 与小框版 `..._small_<state>_item_bg` |

三条容易忽略的对应关系：

1. item 模板名 = `techtree_` + **folder 名** + `_item`（小框是 `_small_item`），必须是 `guiTypes` 的**顶层**容器。
2. 格子容器名 = **分支根科技名** + `_tree`；引擎从"预计算的分支根候选"里找，找不到会报 `Found no grid box for tech %s`。
3. item 背景精灵由引擎按名字拼：`GFX_technology_<folder>_<state>_item_bg`，小框科技用 `..._small_<state>_item_bg`。
   **模板里的 `background` 只是占位，实际贴图看这个名字；贴图按自身像素尺寸绘制，不看模板 size。**

## 2. 症状 → 故障点对照表（先查这张表）

| 你看到的 | 引擎里发生了什么 | 去哪查 |
|---|---|---|
| 页面在、方框在、**一条线都没有**、error.log 干净 | 画线循环在"解析网格"之前就把每个科技跳过了，或 path 没登记 | `available` 是否用了 `has_country_flag`（§3）；`path` 两端是否同 folder（§5.4） |
| 一部分线没有（通常是底盘↔配件这类跨页关系） | 两端不在同一 folder，跨页 path 永远不画 | 把两端并到同一 folder（§5.2） |
| 方框没有了 | 该科技的 `<分支根>_tree` 找不到（`Found no grid box for tech`）或 item 模板名对不上 | GUI 里补齐网格 / 模板名 |
| 小框科技显示成大框、还整体偏位 | 小框模板被用上了，但 `..._small_*_item_bg` 指向大图（203×84） | §4.3 |
| 整页从不出现 | `available` 恒 false（`always = no` + `NOT`） | §3.4 |
| 别的国家冒出不该有的页面 | `available` 条件写太宽（例如默认给所有国家发旗帜） | 改成 `original_tag` |

## 3. 文件夹可用性：不要用运行时旗帜

### 3.1 症状与机理（本次最大坑）

写法（**错误**，但在很多大型 Mod 里大量存在）：

```txt
technology_folders = {
    luftwaffe_folder = {
        ledger = air
        available = { has_country_flag = GER_air }
    }
}
```

配合 `on_startup` 里 `every_country { set_country_flag = ... }` 的初始化方式。

**症状**：页面能进、科技方框整齐、**连线一条不画**、error.log 里一条相关记录都没有。旧存档里可能正常，
**新开档必现**（这也是最容易误判成"存档问题"的地方）。

**机理**（1.19.3 反汇编确认）：页面构建函数在建页时会遍历该页科技，对每个科技调用一次
"解析该科技归属哪个 folder"（`0xad01a0`），这一步会**把 folder 的 available 触发器再按运行时状态求值一次**；
`has_country_flag` 在这条路径上不成立时返回空对象，folder 名比对失败 →
**该科技的所有 path 被静默跳过**（无日志）。方框由同一函数的另一个循环生成，所以照常显示。

### 3.2 正确写法

```txt
technology_folders = {
    luftwaffe_folder = {
        ledger = air
        available = { original_tag = GER }   # 只看国家标签，不依赖运行时旗帜
    }
}
```

`original_tag` 对傀儡/被吞并也稳定，且不受 `on_startup` 执行时机影响。

### 3.3 批量修复脚本

```powershell
# 先看要改哪些（只读）
python scripts/tech_folder_available.py "<Mod目录>" --check

# 应用：has_country_flag = GER_air -> original_tag = GER（自动推断 XXX_air/XXX_armor -> XXX）
python scripts/tech_folder_available.py "<Mod目录>" --apply

# 回滚
python scripts/tech_folder_available.py "<Mod目录>" --revert
```

脚本会：
- 只处理 `technology_folders` 里的 `available`，把 `has_country_flag = <TAG>_air/<TAG>_armor` 换成 `original_tag = <TAG>`；
- 报告无法推断的旗帜名（保留原样，交人工判断）；
- 备份原文件、支持回滚。

### 3.4 顺带坑：`always = no` + `NOT = {...}`

```txt
# 永远不可见（AND 关系：always=no 已经把它锁死）
available = { always = no  NOT = { has_country_flag = GER_armor  ... } }
```

如果本意是"除这些国家之外的默认页"，应该是：

```txt
available = { NOT = { original_tag = GER  original_tag = SOV  ... } }
```

### 3.5 验证方式（必做）

只改数据不够，必须**新开档**（旧存档会掩盖问题）进对应国家，打开该页看连线。
诊断时可以用 `scripts/errorlog_triage.py` 先扫一遍日志：如果没有科技树相关记录，基本就是这类静默跳过。

## 4. 大框 / 小框混排

### 4.1 引擎规则（1.19.3 实测 + 官方 wiki）

- 科技**解锁装备**（`enable_equipments`）→ 用普通 item（`techtree_<folder>_item`）；
- 科技**不解锁装备** → 用 small item（`techtree_<folder>_small_item`）；
- `force_use_small_tech_layout = yes` → **强制**用 small item；
- **前提**：该 folder 必须定义了 `techtree_<folder>_small_item`，否则全部退回普通 item。

### 4.2 混排三件套（缺一不可）

```txt
# 1) 科技：需要小框的那些加标志
tech_my_accessory = {
    force_use_small_tech_layout = yes
    ...
}

# 2) GUI：同一页要同时有两套模板（都是 guiTypes 顶层）
containerWindowType = { name = "techtree_my_folder_item"       size = { width = 203 height = 84 } ... }
containerWindowType = { name = "techtree_my_folder_small_item" size = { width = 72  height = 72 } ... }

# 3) GFX：小框的背景精灵必须指向小图
spriteType = {
    name = "GFX_technology_my_folder_small_unavailable_item_bg"
    textureFile = "gfx/interface/techtree/tech_small_unavailable_item_bg.dds"   # 72x72
}
```

### 4.3 最隐蔽的坑：背景精灵像素尺寸

**模板 `size` 只决定排版和子元素坐标；背景贴图按自身像素尺寸绘制。**
所以会出现这种反直觉现象：

> 小框模板 `size = 72×72` 已经生效（子元素位置正确、整体偏位），
> 但 `GFX_technology_<folder>_small_*_item_bg` 还指着 203×84 的通用大图
> → 画面上仍然是"大框"，只是位置歪了。

排查：

```powershell
python scripts/item_sprite_check.py "<Mod目录>" --folder my_folder
# 输出模板 size 与每个 state 精灵贴图的实际像素，并给出 mismatch 警告
```

修法：把 `..._small_<state>_item_bg` 的 `textureFile` 改成真正的 72×72 小图
（原版可用 `gfx/interface/techtree/tech_doctrine_*_item_bg.dds` 系列）。
`currently_researching` 是动画条：小图应为 72 宽 × 帧数（例如 9 帧 = 648×72）。

### 4.4 不要指望"普通科技自动变小框"

`force_use_small_tech_layout` 对普通科技有效；但**只靠"不解锁装备"**不一定够——
解锁装备模块（`enable_equipment_modules`）等字段在部分数据下仍会走了普通 item 分支。
**要稳定混排，就显式加 `force_use_small_tech_layout` + 保证小框精灵尺寸正确。**

## 5. 拆页 / 合并页

### 5.1 拆分（大框底盘 / 小框配件分两页）

拆分成两个 folder 时，**科技坐标一个都不用改**（原本就是同一页的坐标）：

1. 新 folder 名 `<原>_components`；
2. 把要小框的科技的 `folder.name` 改成新 folder 名（其余字段不动）；
3. GUI 复制一份页容器（改名）+ 一个新页签 + 复制两套 item 模板（都改成小框尺寸）；
4. 注册表加新 folder 条目；
5. 网格：新页只需要放"会出现在新页的分支根"的 `<root>_tree`，位置 = **新页自己的原点**。

### 5.2 合并回单页（6 步，本轮实操配方）

```
1) 科技：把 <X>_components 里所有科技的 folder.name 改回 <X>
   需要小框的加 force_use_small_tech_layout = yes
2) GUI：主页面 techtree_<X>_small_item 换成小框模板（72×72）
3) GUI：把 components 页的所有 gridboxtype 搬进主页面
4) GUI：所有网格 position 统一成同一原点（见 §5.3）
5) GUI：删除 components 页容器 + 它的 <X>_components_tab
6) 注册表：删除 <X>_components folder 条目
```

附带收益：原来跨页的 path（底盘↔配件）在合并后自动恢复连线（同页 path 才画）。

### 5.3 网格原点（position）必须全页统一

- 网格 `position` 就是该页所有科技/连线的像素原点；**同一页内所有 gridbox 必须同原点**。
- 拆分后两页原点常常不同（例如主页面被调过 `-216`、配件页 `239`），合并时**只能留一个**，
  否则一半科技会跑到页面外，或者两组之间错位。
- 想要"保持当前视觉"，注意不同原点差 455px ≈ 6.5 格，**不是整数格，无法逐像素还原**；
  要么统一回原版原点重排，要么接受半格级偏移。

### 5.4 跨页 path 永远不画

一条 `path` 的父和子必须在**同一个 folder** 才会画线（否则被静默跳过）。
拆分必然产生跨页 path——这是拆分的固有代价；想恢复这些线就合并回同一页。

## 6. 三条调试手法（省掉一半猜谜时间）

### 6.1 留痕法：确认"页面到底有没有被建"

把一个**确定会被解析到的** gridbox 改名（例如 `X_tree` → `X_tree_MARKER`）：

- 若日志出现 `Found no grid box for tech <相关科技>`，且游戏里对应方框消失 → 页面被建过、网格解析跑过；
- 若什么都没变 → 页面压根没被建（问题在 folder 可用性 / 页签层）。

用完记得改回（备份原文件或写脚本 reversible）。

### 6.2 对半分实验：同屏对照

把目标群体的**一半**改掉（例如 27/54 个配件科技禁用某字段），另一半保留，一次进游戏就能看出差异，
避免"改一次跑一次游戏"的低效循环。

### 6.3 对照探针：验证字段在当前 Mod 环境里是否真的生效

在**已知正常的原版页面**上用同样的写法加一个探针（例如给原版 `infantry_folder` 的某个科技加
`force_use_small_tech_layout = yes`）：

- 探针页面表现正常 → 字段有效，问题在你的页面/数据；
- 探针页面也异常 → 字段在当前环境失效（被别的文件覆盖、GUI 被替换等）。

## 7. 静默失败点（排查顺序）

按"一条 path 从数据到屏幕"的顺序，这些点都**可能不报错**：

| # | 条件 | 结果 | 日志 |
|---|---|---|---|
| 1 | 科技归属 folder 判定失败（§3） | 该科技所有线跳过 | 无 |
| 2 | `allow_branch` / 可见性不满足 | 线与方框都异常 | 无 |
| 3 | `<分支根>_tree` 网格找不到 | 该科技方框+线跳过 | `Found no grid box for tech %s` |
| 4 | 该科技的 path 列表为空（子科技查不到 / 父子无同名 folder） | 无 | 无 |
| 5 | path 已登记，但当前页 folder 不在其坐标表（跨页） | 无 | 无 |
| 6 | 起点格 == 终点格 | 无 | 无 |

**只有 3 会留日志**；1/4/5/6 全静默。所以"日志干净 + 整页无线"优先怀疑 1、4、5。

## 8. 验收清单（科技树相关）

- [ ] 新开档（不是旧存档）进每个相关国家，逐页确认连线；
- [ ] 大框/小框：小框科技的**背景像素**是小的（不是只看模板 size）；
- [ ] 合并/拆页后：页面数量、页签名、注册表条目数三者一致；
- [ ] `tech_tree_audit.py` 报告 0 问题；
- [ ] error.log 里没有 `Found no grid box`、`Trying to draw a path in Folder`；
- [ ] 跨页 path 是否可接受（不能接受就合并页面）。


## 9. 多根分支（独立分支根）

一个科技页可以有多个 `<root>_tree` 网格框（多个 root），用于表达“互不相连的几条研发线”，
例如：一号坦克线（`GER_pz1_a` 根）+ 捷克 35(t) 线（`GER_pz35t` 根）。

```pdx
# interface/countrytechtreeview.gui（同一页里两个 gridbox）
gridboxtype = {
	name = "GER_armor_tree"
	position = { x = 180 y = 70 }
	slotsize = { width = 96 height = 82 }
	# ...
}
gridboxtype = {
	name = "GER_pz35t_tree"      # 第二个根网格，可不同原点
	position = { x = 180 y = 610 }
	slotsize = { width = 96 height = 82 }
}
```

数据侧：根技术 `path = { ... }` 的第一项决定了它画在哪个网格——
**`path` 里出现哪个 root 网格的 id，就连到哪个网格**，与 `dependencies` 无关。

- 每个 root 的 `position` 独立，两个网格可以上下/左右排；
- 同一页多个 root 时，**所有 root 都必须有对应 gridbox**，少一个 → 该根下所有科技报
  `Found no grid box for tech ...`（该科技方框+线被跳过，日志有这条）；
- 年份行号/列号在整个页内是**每个 root 各自独立**的，不要混用坐标。
- 生成器/手工都适用：只要 `folder` 注册了页面，页面里挂几个 `_tree` 都行。

## 10. 生成文件被外部改写的坑（科技树 + 生成式 Mod）

用脚本生成 `_data/*.json` → GUI/科技/装备文件的项目，常见事故：
**生成好的 `common/technologies/<tree>.txt` 被手工/其它工具改写，丢了 `path`/`dependencies`/`folder` 等字段**，
游戏加载时该科技找不到网格 → 报 `Found no grid box for tech X`（X 可能几十条），但文件本身语法合法。

排查顺序：
1. `common/technology_tags/00_technology.txt` 里 `folder` 是否注册、`available` 是否 `original_tag`；
2. 页面 GUI 里是否有该科技所属 `root` 的 gridbox；
3. 科技条目是否仍有 `path = { ... }`（每段第一个元素是 root 网格 id）与 `folder = <folder>`；
4. 对比 `_data` 源与生成文件：生成文件被改写后，重新生成并比对哈希即可定位。

**规矩：生成文件只由生成器写；要改先改数据源。** 生成器里给所有生成文件加统一前缀（如 `zz_`）
还能顺带解决“加载顺序早于原版定义”导致的 `Malformed token`（例如自定义底盘要晚于原版 `tank_chassis.txt` 解析）。

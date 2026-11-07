---
title: 案例：18 槽坦克设计器（槽位表 / 背景尺寸 / 命名）
domain: 90_case-studies
scope: case-study
verified_on: 1.19.x
---

# 案例：18 槽坦克设计器（槽位表 / 背景尺寸 / 命名）

> **案例说明**：本文是真实 Mod 项目 `hist_tech_trees`（德国科技树 / 装甲配件 overhaul）的实战记录，结论来自真机对照实验。**它不是默认做法**：通用规则、字段语义与推荐写法以 `01_script`–`07_tools` 各域文档为准，本文只回答「当时怎么定位、踩了什么坑、怎么验证」。

> 适用：想改坦克设计器界面、增减模块槽、做"装备设计器"玩法、或排查"槽位不显示 / 重叠 / 窗口溢出"。
> 全部结论来自 1.19.3 + Arms Against Tyranny、`gui_scale` 1.5@4K 实机对照（Black ICE Tech Tree 与本项目 16/18 槽改造）。

## 0. 一句话

坦克设计器 = **全局窗口 `interface/tank_designer_view.gui`（槽位按钮的位置表）** + **按底盘插入的蓝图 GUI
`interface/equipmentdesigner/tanks/*.gui`（美术/挂点）** + **数据侧 `module_slots`（槽位数量与可装类别）** + **模块定义（`category` 隐式建类别）**。
**槽位按钮显示哪些位置，由 `tank_designer_view.gui` 的 `pos_custom_module_slot_window_N` 数量决定；每个槽是哪一类，由底盘 `module_slots` 里的书写顺序决定（第 N 个槽 → 第 N 个位置）。**

## 1. 文件地图

| 文件 | 作用 |
|---|---|
| `interface/tank_designer_view.gui` | 设计器窗口：窗口尺寸、蓝图容器、**槽位位置表**、底部按钮（重置/保存/生产花费） |
| `interface/equipmentdesignerview.gui` | 设计器通用控件；**`equipment_designer_module_slot_entry` 槽位按钮实例模板（76×47）**、模块选择弹窗 |
| `interface/equipmentdesigner/tanks/*.gui` | 每类/每国底盘的 2D 蓝图与模块挂点（容器名 `equipment_designer_<底盘装备名>`，可回退到 archetype 名） |
| `common/units/equipment/tank_chassis.txt` | 底盘装备；**archetype（`is_archetype=yes`）里定义 `module_slots` 白板槽位**，普通底盘多写 `module_slots = inherit` |
| `common/units/equipment/modules/00_tank_modules.txt` | 模块定义；`category = xxx` **隐式创建模块类别**（无单独类别声明文件） |
| `gfx/interface/equipmentdesigner/graphic_db/*.txt` | 底盘 → 2D 图标池 / 3D 模型池（`models = { ENTITY }`） |
| `gfx/entities/tanks.gfx` / `units_tanks.asset` | 3D 用 `pdxmesh` / `entity`（见 `../05_presentation/models-3d.md`） |

## 2. 窗口与关键控件（原版数值）

```pdx
# tank_designer_view.gui
containerWindowType = { name = "tank_designer_view" size = { width = 1091 height = 542 } orientation = CENTER origo = center }
  background = { spriteType = "GFX_tank_designer_popup_bg" }   # 贴图 tank_designer_popup_bg.dds，固定 1092×553
  containerWindowType = { name = "equipment_modules" position = { x=13 y=146 } size = { width=512 height=350 }
    containerWindowType = { name = "equipment_preview" position = { x=3 y=50 } size = { width=508 height=248 } }  # 代码在此插入蓝图 GUI
    positionType = { name = "pos_custom_module_slot_window_0..8" }   # 9 个槽位按钮位置
    containerWindowType = { name = "equipment_upgrade_0/1" ... }     # 引擎/装甲等级（不是模块槽）
  }
```

- 槽位按钮实例 = `equipment_designer_module_slot_entry`，**尺寸 76×47**（由 `icn_module_slot_frame` 决定）；
  所以列距必须 ≥76，否则按钮会叠压。原版列宏 `@fixed_btn_mod_col_0..6 = 1,74,147,220,293,366,439`（73 间距，**有一像素级叠压**）。
- 行宏：`@fixed_btn_mod_row_0 = 1`、`@fixed_btn_mod_row_1 = 300`；`ypos_module_row_0` 只用于 tooltip 上下锚点。
- 原版 9 槽映射（槽位序号 = `module_slots` 书写顺序）：

| 序号 | 位置 | 原版常见槽 |
|---|---|---|
| 0,1 | 上排 col0,col1 | 炮塔、主武器 |
| 2,3,4 | 下排 col0,col1,col2 | 悬挂、装甲、引擎 |
| 5,6,7,8 | 上排 col2..col5 | 特殊模块 1–4 |
| — | 上排 col6 + 末位 | 原版由代码追加“+”/自动升级圆钮，不占 `positionType` |

## 3. 数据侧：槽位数与可装类别

- 槽位名（如 `main_armament_slot` / `special_type_slot_1`）只是**键名**；真正约束来自
  `allowed_module_categories = { ... }`（引用模块的 `category`）与 `required = yes/no`。
- **模块类别不需要注册**：在 `modules/*.txt` 里写 `category = my_new_category`，再在槽位 `allowed_module_categories` 引用即可。
- 一个装备的槽位数量 = 它（或其 archetype）的 `module_slots = { ... }` 条目数；
  普通底盘写 `module_slots = inherit` 继承 archetype。
- **装备可以自己写 `module_slots` 覆盖**（飞机 airframe 就是这么做的；坦克底盘实测也可行，
  这是给不同坦克不同槽数的关键，无需改 archetype）。
- 槽位数量上限由 **`tank_designer_view.gui` 里 `pos_custom_module_slot_window_N` 的个数**决定：
  数据里第 k 个槽没有对应位置时，该槽不显示（表现为“少了几个槽”）。
- 数量限制用 `module_count_limit = { category = tank_special_module count < N }`（防叠加），
  单件上限如 `module = armor_skirts count < 1`。
- `default_modules = { slot = module }` 只写在 **archetype** 上最稳；写在普通装备上是否生效随版本而定，先按“让玩家自己填”处理。

## 4. 自定义槽位数：扩展位置表

### 4.1 参考：Black ICE 的 23 槽
`BlackIce_Tech_Tree/interface/tank_designer_view.gui`：

- 17 个 `pos_fixed_module_slot_window_0..16`（固定显示槽：炮塔/主炮/弹药/同轴/车体MG/发动机/变速箱/齿轮箱/悬挂/装甲厚度/装甲设计/装甲分布/装甲结构/炮塔装甲结构/无线电/人机工效/工艺）；
- 6 个 `pos_custom_module_slot_window_0..5`（特殊槽）；
- 行宏扩到 5 行（`row_0=0,row_1=48,row_2=204,row_3=252,row_4=300`），按钮压着蓝图放。
  → 结论：**位置名可自定义、数量可扩展**，代价是窗口变挤/蓝图被压。

### 4.2 本项目采用的 16 槽紧凑布局（窗口高度不变 542；18 槽见 4.2.1）

在 `equipment_modules`（512×350）内：

| 排 | 位置 | 槽位 |
|---|---|---|
| 上排（y=0） | `pos_*_0..6`，col0..col6（72 步距，`@fixed_btn_mod_col_i = 72*i`） | 炮塔 / 主武器 / 弹药 / 副武器 / 发动机 / 传动 / 车体防护 |
| 第二排（y=50） | `pos_*_7`（col0）、`pos_*_8`（col6） | 通信（左角）/ 工程（右角）——正好压在原蓝图标题行左右 |
| 下排（y=300） | `pos_*_9..15`，col0..col6 | 炮塔防护 / 内部安全 / 瞄准 / 观察 / 附加防护 / 烟幕 / 续航（+ 若 7 个则加发动机等） |

```pdx
@fixed_btn_mod_col_0 = 0
@fixed_btn_mod_col_1 = 72
...
@fixed_btn_mod_col_6 = 432
@fixed_btn_mod_row_0 = 0
@fixed_btn_mod_row_1 = 50
@fixed_btn_mod_row_2 = 300

positionType = { name = "ypos_module_row_0" position = { x=0 y=@fixed_btn_mod_row_0 } }
positionType = { name = "pos_custom_module_slot_window_0" position = { x=@fixed_btn_mod_col_0 y=@fixed_btn_mod_row_0 } }
...
positionType = { name = "pos_custom_module_slot_window_7" position = { x=@fixed_btn_mod_col_0 y=@fixed_btn_mod_row_1 } }
positionType = { name = "pos_custom_module_slot_window_8" position = { x=@fixed_btn_mod_col_6 y=@fixed_btn_mod_row_1 } }
...
positionType = { name = "pos_custom_module_slot_window_15" position = { x=@fixed_btn_mod_col_6 y=@fixed_btn_mod_row_2 } }
```

### 4.2.1 本项目最终采用的 18 槽紧凑布局（窗口高度不变 542）

在同样的 `equipment_modules`（512×350）里：

| 排 | 位置 | 槽位 |
|---|---|---|
| 上排（y=0） | `pos_*_0..6`，col0..col6 | 炮塔 / 主武器 / 弹药 / 副武器 / 发动机 / 传动 / 车体防护 |
| 第二排（y=50） | `pos_*_7..10`，col0/1/5/6 | 通信（左 2）/ 工程（右 2） |
| 下排（y=300） | `pos_*_11..17`，col0..col6 | 炮塔防护 / 内部安全 / 瞄准 / 观察 / 附加防护 / 烟幕 / 续航 |

数据侧（`tank_chassis.txt` 的 `module_slots`）必须按 **位置 0..17 的同一顺序**写 18 个槽；多出的位置不显示，
少的位置不会被占位。18 个槽位按钮仍会因 76px 槽宽 > 72px 列距而相邻叠 4px，这是原版模板尺寸决定的；
要消除需加宽容器或缩小槽位模板。

`scripts/tank_designer_layout.py --preset 18-compact` 可直接生成这套 18 槽 GUI。

要点：
- 蓝图容器保持原版 `position {x=3 y=50} size 508×248` 不动；16 槽时第二排 2 个槽叠在蓝图顶部两角；18 槽时第二排 4 个槽占 col0/1/5/6，同样只压标题两侧（原版那一带只有标题文字）。
- 下排 y=300 正好落在原“悬挂/装甲/引擎 3 槽 + 空位 + 引擎/装甲等级区”，把 `equipment_upgrade_0/1` 移走即可整排利用。
- 7 个槽 × 76px = 532px > 容器 512px：所以列距只能 72（相邻叠 4px，视觉连成一排）；要严格不叠压需把窗口/容器加宽，或缩小槽位模板。

### 4.3 加高窗口的坑（必看）

**窗口背景 `GFX_tank_designer_popup_bg` 是一张固定尺寸贴图（1092×553），不是九宫格**。
只改 `tank_designer_view` 的 `size`，背景仍按原尺寸绘制 → 槽位/按钮会“溢到窗口外”，表现为：
底部槽位/按钮出现在地图背景上、窗口看起来没变高。

修法（二选一）：
1. **不加高窗口**（推荐，改动最小）：用 §4.2 的紧凑布局，把槽位塞进原 512×350 区域。
2. 确实要加高：在 mod 里生成一张更长的背景 DDS（例如把原图中段深色纹理纵向平铺到目标高度，保留顶/底边框），
   注册新 sprite，再把窗口 `background` 换成它：

```bash
# 生成 1092×780（Pillow + 技能自带 dds_helper）
python - <<'PY'
from PIL import Image
im = Image.open(r"<game>/gfx/interface/equipmentdesigner/tanks/tank_designer_popup_bg.dds").convert("RGBA")
W, H = im.size
top, bot = 380, 470            # 保留顶部 380 行、底部 83 行
need = 780 - top - (H - bot)
canvas = Image.new("RGBA", (W, 780))
canvas.paste(im.crop((0, 0, W, top)), (0, 0))
y = top
while y < top + need:
    take = min(bot - top, top + need - y)
    canvas.paste(im.crop((0, top, W, top + take)), (0, y))
    y += take
canvas.paste(im.crop((0, bot, W, H)), (0, y))
canvas.save("bg.png")
PY
python scripts/dds_helper.py make bg.png gfx/interface/equipmentdesigner/tanks/NS_bg.dds --width 1092 --height 780
```

```pdx
# interface/NS_designer.gfx
spriteTypes = { spriteType = { name = "GFX_NS_tank_designer_bg" texturefile = "gfx/interface/equipmentdesigner/tanks/NS_bg.dds" } }
```

```pdx
# tank_designer_view.gui：只改窗口背景引用 + 窗口高度
background = { name = "Background" spriteType = "GFX_NS_tank_designer_bg" }
size = { width = 1091 height = 780 }
```

> 背景贴图本身自带左右两栏分隔/米色数据区纹理，**加高时不要简单整图拉伸**（数据区/边框会变形），
> 用“顶部原样 + 中间平铺 + 底部原样”的方式拼。

## 5. 隐藏原版控件（升级区 / 自动按钮 / 悬浮图标）

改窗口时经常需要清掉原版元素。统一做法：**保留控件本体，只把 position 移到屏幕外**（删元素可能被代码引用报错）。

```python
import re
pat = re.compile(r'position\s*=\s*\{\s*x\s*=\s*-?\d+\s*y\s*=\s*-?\d+\s*\}')

def hide(text, name):
    i = text.find(f'name = "{name}"')
    if i < 0: return text
    m = pat.search(text, i)
    return text[:m.start()] + "position = { x = -4000 y = -4000 }" + text[m.end():]
```

可安全隐藏：`equipment_upgrade_0/1`（引擎/装甲等级）、`niche_button`、`tag_icon_bg`、
`auto_button`、`auto_upgraded_checkbox_button`、`save_to_file_button`、`historical_design_button`、
`design_company_icon`、`design_team_button`、`upgrade_assigned_industrial_org`、`icon_selection_container`。

> `auto_upgrade_button`（末位圆钮）有时由代码自动摆放，**改 position 可能无效**；真正要去掉需删元素，
> 但这棵按钮与升级逻辑相关，删前先备份并在 error.log 确认没有 `auto_upgrade` 相关报错。

底部栏元素在窗口加高后一起下移（示例 +218）：
`reset_button`、`duplicate_button`、`save_button`、`experience_bg`、`experience`、`resources_bg`、
`production_resources`、`refit_cost`、`production_value`。

## 6. 蓝图 2D GUI 与“设计器容器选择”

- 代码把**底盘对应的 2D 蓝图容器**插入 `equipment_preview`。容器名匹配顺序：
  `equipment_designer_<底盘装备 id>` → 回退 `equipment_designer_<archetype>`（原版有 253 个这样的文件/容器）。
- 蓝图 GUI 里的小图标（`main_armament_slot`、`suspension_type_slot`…）只是**美术挂点/highlight**，
  与 `tank_designer_view.gui` 的槽位按钮是两套东西；槽位名改掉后这些挂点对不上只是“蓝图不再高亮”，不报错。
- 想让某个底盘有专属蓝图布局：新建 `interface/equipmentdesigner/tanks/NS_<chassis>.gui`，
  容器名 `equipment_designer_<chassis>`，内部尺寸对齐 `508×248`。

## 7. 验收清单（设计器相关）

- [ ] `tank_designer_view.gui` 括号配平（`{`/`}` 数量相等），元素名唯一；
- [ ] 槽位按钮不重叠、不越出 `equipment_modules` 区域（槽宽 76：列距 ≥76 或接受 4px 叠压）；
- [ ] 数据侧 `module_slots` 条目数 = 位置数（多出的不显示，少的不占位）；
- [ ] 所有 `allowed_module_categories` 引用的 `category` 都能在某个模块文件里找到；
- [ ] 进游戏开设计器：窗口不破图、无报错；槽位能点开、能选模块、能保存设计；
- [ ] `logs/error.log` 无 `gui` / `tank_designer_view` / `module` 相关新错误；
- [ ] 旧存档/新开档都试一次（GUI 改动通常与新开档无关，但设计数据可能受影响）。

## 8. 症状 → 故障点

| 症状 | 最可能原因 |
|---|---|
| 改了窗口高度，内容溢出到窗口外/地图上 | 背景贴图固定尺寸（§4.3） |
| 槽位少显示 | `pos_custom_module_slot_window_N` 数量 < 数据槽数 |
| 槽位重叠/挤压 | 槽位模板 76px > 列距；容器宽度不足 |
| 窗口里出现原版的“+”/圆钮/等级区 | 未隐藏对应控件（§5） |
| 设计器打不开/空白 | GUI 语法错、缺少代码必需控件（不要删窗口/统计/3D 相关元素） |
| 新槽位点开无模块 | `allowed_module_categories` 里的类别没有任何模块，或模块没被科技解锁 |
| “设计无效”无法保存 | 必选槽（`required = yes`）为空，或有冲突的 `module_count_limit` |

## 9. 配套脚本

- `scripts/tank_designer_probe.py`：读游戏文件，打印窗口尺寸、槽位位置表、槽位模板尺寸、模块类别、
  底盘 archetype 槽数、背景贴图尺寸（排错第一步）。
- `scripts/tank_designer_layout.py`：从原版 GUI 生成自定义槽位布局（`16-compact` / `16-tall` / `18-compact`），
  可隐藏升级区/自动按钮，输出到 mod；支持 `--dry-run` 只打印将要改的坐标。

## 10. 跨 mod 实测：克隆底盘、`gui_category`、每底盘美术

### 10.1 `duplicate_archetypes`：不覆盖原版也能克隆整个底盘家族

BI 不覆盖 `common/units/equipment/tank_chassis.txt`，而是用
`trm_tank_variants.txt` + 10 个 `trm_tank_chassis_*.txt`：

```pdx
duplicate_archetypes = {
    trm_medium_tank_chassis = {
        variant_name = { find_and_replace = { "chassis" "equipment" } }
    }
}
```

- 复制出的 `trm_medium_tank_equipment` 直接继承原版全部字段（含 `module_slots`）；
- **必须在被复制的 archetype 定义之后求值**（加载顺序敏感）；
- 好处：原版更新时不用同步整份 `tank_chassis.txt`。

对照：MD 走另一条极端——在 mod 里放一个 **0 字节的 `tank_chassis.txt`** 抹掉原版，
再在 `MD_tank_chassis.txt` 里从零重建。两种做法都比「整份复制再手改」好维护。

### 10.2 `gui_category`：细 category 给槽位，粗 category 给选择器

```pdx
hist_module_x = {
    category = hist_suspension_christie   # 细：槽位白名单用
    gui_category = hist_suspension        # 粗：设计器选择器分组用
    ...
}
```

BI 有 889 个细 category，汇总成 142 个 `gui_category`。原版模块文件里没有这个字段，
但引擎接受。不加 `gui_category` 时，选择器会把 889 个类别平铺，用户根本翻不完。

### 10.3 每底盘槽位美术：脚本加了槽，GUI 必须同步

`interface/equipmentdesigner/tanks/<chassis>.gui`：

- 容器名必须是 **`equipment_designer_<equipment_id>`**；
- 每个槽是**三件套**：`<slot>` 容器 → 同名子容器 → `<slot>@highlight`；
- 缺任何一件，该槽**没有热区**（能看见、点不了）。

TFR 踩过：`tank_chassis.txt:95-99` 新增第 6 个特殊槽 `tank_sights_module`，
但没加对应的设计器美术 → 新槽在界面上点不动。本项目的 18 槽同样要靠 253 个
蓝图 GUI 桩来补热区（见 §6）。

### 10.4 槽位互斥：用计数器，不要用 XOR 思路

```pdx
special_slot_1 = {
    allowed_module_categories = { hist_addon hist_smoke hist_endurance }
    module_count_limit = { category = hist_addon count < 2 }
}
```

`module_count_limit` 是**每 archetype 每 category** 的数量上限；
多个特殊槽共用白名单 + 各自计数器，就能做到「同类只能装一个」，
不需要为每个组合建一个「互斥类别」。

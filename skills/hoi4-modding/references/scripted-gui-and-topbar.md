# Scripted GUI 与顶栏按钮：窗口、绑定、遮罩、字体坑（HOI4 1.19.3 实战）

> 来源：一次“在军官团右侧新增独立军械部门窗口、复制完整军官团 UI、加顶栏按钮”的真实改造。
> 结论覆盖 scripted GUI 的窗口类型、点击绑定、父窗口、原生窗口自动关闭限制、顶栏补图与中文乱码。

## 1. 最小可用结构

一个 scripted GUI 面板通常需要：

| 文件 | 作用 |
|---|---|
| `interface/NS_panel.gui` | `guiTypes = { containerWindowType = { ... } }` 与按钮/入口 |
| `common/scripted_guis/NS_panel_gui.txt` | `scripted_gui = { NS_main = { ... } }`：visible/effects |
| `common/scripted_effects/NS_effects.txt` | 打开/关闭/解锁/创建装备等 effect |
| `common/scripted_triggers/NS_triggers.txt` | 按钮可见/可点的 `has_tech`、`has_army_experience` 等 |
| `interface/NS.gfx` | 自定义图标/DDS 的 sprite 注册 |
| `localisation/*/NS_l_*.yml` | 所有界面文字；UTF-8 BOM |

```pdx
scripted_gui = {
    NS_main = {
        context_type = player_context
        window_name = "NS_main_window"
        parent_window_token = top_bar
        dirty = ui_NS
        visible = { has_country_flag = NS_open }
        effects = {
            close_button_click = {
                clr_country_flag = NS_open
                dirty = ui_NS
            }
        }
    }
}
```

## 2. 窗口类型：只能用 containerWindowType

scripted GUI 的 `window_name` 必须是 **`containerWindowType`**，不能是顶层 `windowType`。
写错时常见报错：

```text
Failed to create containerWindowType for NS_main_window
```

`containerWindowType` 的正确字段：

```pdx
containerWindowType = {
    name = "NS_main_window"
    position = { x = 0 y = 0 }
    size = { width = 100%% height = 100%% }
    clipping = yes
    background = { name = "Background" quadTextureSprite = "GFX_tiled_window_2b_border" }
}
```

- `size` 的百分比必须写成 **`100%%`**（GUI 语法转义），写 `100%` 会被解析坏。
- 子控件用 `containerWindowType`/`buttonType`/`iconType`/`instantTextBoxType`；**不要**在 scripted GUI 窗口下塞 `windowType`。
- `position` 可以是固定值或屏幕相对；`parent_window_token = top_bar` 时 0,0 覆盖全屏，`production_tab` 只覆盖生产页半屏。

## 3. 按钮点击绑定：effect 名必须是 `<button名>_click`

这是最容易静默失败的一条。

```pdx
# interface/NS.gui
buttonType = {
    name = "NS_open"
    ...
}
```

```pdx
# common/scripted_guis/NS_gui.txt
scripted_gui = {
    NS_buttons = {
        context_type = player_context
        window_name = "NS_buttons_window"
        parent_window_token = top_bar
        effects = {
            NS_open_click = { set_country_flag = NS_open } # 必须正好是按钮名 + _click
        }
    }
}
```

如果按钮叫 `NS_open_click`，引擎会去找 `NS_open_click_click`，点击完全无反应；`error.log` 也通常不报。
关闭按钮同理：`name = "close_button"` → `close_button_click`。

常用显示互斥：

```pdx
# 主窗
visible = { has_country_flag = NS_open }
# 入口按钮：常驻
# 不要写 visible = { NOT = { has_country_flag = NS_open } }
# 否则隐藏后无法再点开；关闭依靠 close_button_click 清 flag
```

## 4. 顶栏新增按钮：补底板，不要用 generic 黑块

原版顶栏底图 `GFX_topbar_background_extended` 是固定 2346×87；左侧按钮底板只到军官团附近。
新增按钮放在 `x=680 y=36` 时，按钮会悬在地图/生产页上。不要用 `GFX_tiled_generic_bg_1` 直接补一块——
色差和边缘会像黑框。

推荐做法：

1. 从原版 `background_extended.dds` 裁 **底板主体 + 右端斜角/铆钉**；
2. 生成一张独立 `gfx/interface/topbar/NS_patch.dds`（例：230×62），用 `iconType` 叠在
   `topbar` 的 `x=560 y=22`；
3. 同时右移信息栏，避免新按钮压住指挥点/经验：

```text
cp    732 -> 792
land  796 -> 856
navy  854 -> 914
air   912 -> 972
nukes 970 -> 1030
```

4. 覆盖 `interface/alerts.gui`：`alerticon_startposition 662 -> 735`、
   `alerticon_extended_startposition 718 -> 791`，否则警报层会压住新按钮。
5. 补块右侧保留原版斜角，否则用户会看到“底图边缘不圆滑”。

不要直接拉伸整张 2346×87 底图：顶部信息条、左右圆角和斜边都会变形。

## 5. 原生窗口自动关闭：scripted GUI 做不到

用户常要求“打开军械部门时，其他部门窗口自动关闭”。这属于**原生窗口管理器**行为：

- 军官团、情报机构、生产页等是引擎原生窗口；互相打开时会自动关闭同组窗口。
- scripted GUI 窗口不是原生窗口，没有 `is_window_open` 触发器，也没有“窗口打开”on_action。
- 因此 scripted GUI **无法监听其他窗口打开并自动关闭自己**；只能：
  - 手动关闭按钮/ESC；
  - 或改用原生窗口（但 mod 不能新增原生窗口类型）。

同理，复制 `countryofficercorpview.gui` 只能得到 `Placeholder` 外壳；顾问、司令官、精神、特种部队由引擎按
原生窗口名动态填充，不会因为复制 GUI 就出现。要做独立部门必须在 scripted GUI 里自建数组、dynamic_lists 和
click effects，这是“重建”，不是“复制”。

## 6. 遮罩/全屏的取舍

| 方案 | 效果 | 代价 |
|---|---|---|
| `parent_window_token = production_tab` + 100%% | 页面嵌在生产页左半屏 | production_tab 只有半屏，页面很小 |
| `parent_window_token = top_bar` + 100%% | 真正全屏，可盖住生产页 | 需要 `clipping=yes`；顶栏/国旗可能被盖，需下移或单独处理 |
| top_bar 全屏 + `HTE_overlay` | 视觉上让生产页消失 | 遮罩盖国旗/顶栏；不是真关闭；ESC 仍需自己处理 |
| 原生窗口 | 自动关闭、数据完整 | mod 不能新增原生窗口 |

如果用户要求“打开后生产页消失”，优先做 **top_bar 全屏页面**，不要把 windowType 当全屏子窗。

## 7. 中文字体：`hoi_14mbs`/`hoi_24mbs` 可能显示 `????`

本地化 key 正确、`HTE_TITLE` 中文正常，但卡片/家族全是 `????` 时，先查字体：

- 标题用 `hoi_36header` 正常；
- 卡片/家族曾用 `hoi_14mbs`/`hoi_24mbs`，在用户字体 mod 下没有中文字形；
- 改用 `hoi_16mbs`（卡片）与 `hoi_24header`（家族标题），通常恢复。

排查顺序：

1. yml 是否 UTF-8 BOM、根键是否与目录一致；
2. 同一 yml 中哪个 key 能显示中文（若能，说明文件加载了，不是 key 缺失）；
3. 看该控件 `font =`；换成 `hoi_16mbs`/`hoi_24header` 测试；
4. 最后才怀疑本地化覆盖/语言设置。

## 8. 本地化多行：必须转义换行

HOI4 yml 的 `"..."` 内不能直接换行；多行描述必须写成 `\n`：

```python
def loc_escape(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
```

否则典型坏行：

```yaml
NS_TECH_TOOLTIP:0 "第一行
第二行"
```

整份 yml 会因引号不闭合而失效，表现是页面大面积 key/问号；`hoi4_lint` 的 BOM 检查不校验这个语义。

## 9. 验收清单

- [ ] `window_name` 指向 `containerWindowType`，不是 `windowType`；
- [ ] 每个按钮名 + `_click` 能在 scripted GUI `effects` 里找到同名键；
- [ ] `parent_window_token` 与 `size/position` 匹配（top_bar 全屏 / production_tab 半屏）；
- [ ] 顶栏补块使用原版斜角，信息栏与 alerts 已右移；
- [ ] 本地化 yml 有 BOM、无裸换行、无重复 key；
- [ ] 卡片/家族字体能在用户字体 mod 下显示中文；
- [ ] `error.log` 无 `Failed to create containerWindowType`、无按钮找不到；
- [ ] 明确告知用户：scripted GUI 不能自动关闭，除非改用原生窗口。

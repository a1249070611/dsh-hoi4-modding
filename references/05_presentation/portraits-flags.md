---
title: 肖像与旗帜（gfx/flags、gfx/leaders、portraits/）
domain: 05_presentation
scope: gfx
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 肖像与旗帜

## 1. 旗帜：目录 + 尺寸 + 命名（全部实测）

### 1.1 目录与尺寸

| 目录 | 文件数 | 尺寸 | 格式 | 用途 |
|---|---|---|---|---|
| `gfx/flags/` | 2203 个 `.tga`（+`medium/`、`small/` 两个子目录） | **82×52** | **TGA 32bpp** | 主旗帜（外交、国家选择、地图） |
| `gfx/flags/medium/` | 2203 | **41×26** | TGA | 中等尺寸 |
| `gfx/flags/small/` | 2226 | **10×7** | TGA | 极小（列表、地图角标） |

> 实测样例：`gfx/flags/GER_fascism.tga` = (82,52,32bpp)；`gfx/flags/medium/GER_fascism.tga` = (41,26)；`gfx/flags/small/GER.tga` = (10,7)。
> **旗帜是 `.tga` 不是 `.dds`**。这是唯一必须用 TGA 的常见资源。

### 1.2 命名规则（决定游戏取哪张旗）

| 文件 | 何时使用 |
|---|---|
| `gfx/flags/TAG.tga` | 无匹配意识形态时的默认旗 |
| `gfx/flags/TAG_<意识形态组>.tga` | 该国执政党属于该组时（组名见 `common/ideologies/00_ideologies.txt`：`democratic`(L3)、`communism`(L73)、`fascism`(L140)、`neutrality`(L203)） |
| `gfx/flags/<任意名>.tga` | `set_cosmetic_tag` 动态换旗时按该名查 |

原版 `gfx/flags/` 后缀统计：`fascism` 537、`neutrality` 532、`communism` 491、`democratic` 477 —— 这四组占绝对多数。
**同一国家可以完全没有 `TAG.tga`**（实测 `GER.tga` 不存在，只有四个意识形态旗 + 一堆临时政府旗），引擎会按当前执政意识形态选。

`GER` 的完整旗组（说明「动态换旗」的实际形态）：

```text
gfx/flags/GER_communism.tga
gfx/flags/GER_democratic.tga
gfx/flags/GER_fascism.tga
gfx/flags/GER_neutrality.tga
gfx/flags/GER_german_kaiserreich_neutrality.tga
gfx/flags/GER_german_monarchy_conservative_democratic.tga
gfx/flags/GER_german_monarchy_democratic.tga
gfx/flags/GER_german_monarchy_liberal_democratic.tga
gfx/flags/GER_german_socialist_union_communism.tga
gfx/flags/GER_greater_proletarian_german_state_communism.tga
gfx/flags/GER_peoples_republic_communism.tga
gfx/flags/GER_provisional_gvt_democratic.tga
gfx/flags/GER_provisional_gvt_neutrality.tga
gfx/flags/GER_strasserite_state_fascism.tga
```

- `_<组>` 结尾的按意识形态自动选取；其余靠 `set_cosmetic_tag` 主动指定（cosmetic tag 名 = 文件名去掉扩展名）。
- 新增旗帜的做法：把 **三份尺寸**（82×52 / 41×26 / 10×7）的 TGA 放进 mod 的 `gfx/flags/`、`gfx/flags/medium/`、`gfx/flags/small/`，文件名一致。只放主尺寸也能跑，但小尺寸缺失处会缩放大图（糊）。

### 1.3 旗帜绘制机制（为什么换框不用换旗）

`interface/general_stuff.gfx:253-310` 用 `maskedShieldType` 把国旗“塞进”旗框：

```pdx
maskedShieldType = {
	name = "GFX_shield_medium"
	textureFile1 = "gfx/interface/flag_overlay.dds"       # 框/高光
	textureFile2 = "gfx/interface/shield_medium_mask.tga" # 遮罩：白=显示旗帜
	effectFile = "gfx/FX/maskedflag.lua"
}
```

→ 想让旗帜以新形状显示（圆形/盾形/竖幅），改的是 `textureFile1`+`textureFile2`，**国旗图本身不用动**。详见 [gfx-sprites.md](gfx-sprites.md) §7。

## 2. 肖像

### 2.1 领袖/将领肖像

| 项 | 事实 |
|---|---|
| 目录 | `gfx/leaders/<TAG>/`（如 `gfx/leaders/GER/`）；另有跨文化通用池 `gfx/leaders/Africa`、`Asia`、`Europe`… |
| 尺寸 | **156×210**（实测 `gfx/leaders/GER/Portrait_Germany_Albert_Kesselring.dds` = 156×210，未压缩 32bpp，131168 字节） |
| 格式 | `.dds`，未压缩 32bpp 即可（与 UI 图标同构，见 [gfx-sprites.md](gfx-sprites.md) §10） |
| 注册 | 必须写 sprite：`interface/_leader_portraits.gfx` 的 `spriteTypes = { }` 里 `name = "GFX_portrait_<tag>_<name>"` |
| 小头像 | 同名 `_small` sprite 指向 `gfx/interface/ideas/idea_*.dds`（列表/理念里用，约 65×67） |

原版写法（`interface/_leader_portraits.gfx:26-38`）：

```pdx
spriteType = {
	name = "GFX_portrait_ger_felix_steiner"
	texturefile = "gfx/leaders/GER/portrait_ger_felix_steiner.dds"
}
spriteType = {
	name = "GFX_portrait_ger_felix_steiner_small"
	texturefile = "gfx/interface/ideas/idea_GER_felix_steiner.dds"
}
```

### 2.2 角色怎么引用肖像（content 侧只使用，定义在 gfx 侧）

`common/characters/GER.txt:17-21`：

```pdx
GER_adolf_hitler = {
	name = GER_adolf_hitler
	portraits = {
		civilian = {
			large = GFX_portrait_GER_adolf_hitler
		}
	}
	country_leader = {
		ideology = nazism
		traits = { GER_der_fuhrer }
		expire = "1965.1.1.1"
		id = -1
	}
}
```

- 槽位名：`civilian`（文职/领袖）、`army`、`navy`、`operative`（特工）；每个槽位下 `large` / `small`。
- 带 `small` 的完整写法：`portraits = { civilian = { large = GFX_portrait_GER_eva_braun small = GFX_portrait_GER_eva_braun_small } }`（`GER.txt:32-37`）。
- **引用的永远是 sprite 名（`GFX_...`），不是文件路径**。所以新增角色必须同时改 `.gfx`。
- 女性角色写 `gender = female`。

### 2.3 随机/通用肖像池：`portraits/*.txt`

游戏根目录还有一层 `portraits/`（**不是** `gfx/portraits`），里面是两个脚本：

| 文件 | 行数 | 作用 |
|---|---|---|
| `portraits/00_portraits.txt` | 1522 | 通用肖像池：`default`、`continent = { name = europe ... }`、以及按国家 `GER = { ... }` 的池 |
| `portraits/998_scientist_portraits.txt` | — | 科学家肖像池 |

```pdx
# portraits/00_portraits.txt:33-46
continent = {
	name = europe
	army = {
		male = {
			"GFX_Portrait_Europe_Generic_land_1"
			"GFX_Portrait_Europe_Generic_land_2"
		}
	}
	navy = { male = { ... } }
}
```

- 作用：将领/顾问随机生成时从这里按大陆/国家取 sprite。
- 新增“通用肖像”不用动这里，**指定了 `portraits = { ... }` 的角色会优先用自己的**。
- 大量 `_random_portraits.gfx` / `_scientists_portraits.gfx` 里的 sprite 就是被这个池引用的。

## 3. 完整体检表（换一套国旗 + 一个领袖头像）

任务：给 `SWE` 加一个自定义国家（`HHO`）+ 领袖。

1. `gfx/flags/HHO.tga`（82×52，32bpp TGA）
2. `gfx/flags/HHO_fascism.tga`、`HHO_communism.tga`、`HHO_democratic.tga`、`HHO_neutrality.tga`
3. `gfx/flags/medium/HHO.tga` 等（41×26）
4. `gfx/flags/small/HHO.tga` 等（10×7）
5. `gfx/leaders/HHO/portrait_hho_leader.dds`（156×210）
6. `interface/NS_leaders.gfx` 里注册 `GFX_portrait_hho_leader`
7. `common/characters/HHO.txt` 里 `portraits = { civilian = { large = GFX_portrait_hho_leader } }`
8. `common/country_tags/` 定义 `HHO`；`common/countries/` + `history/countries/` 建立国家

（2–4 的三份尺寸可以先用主尺寸缩放出图；缺 `medium`/`small` 不会崩，只会模糊。）

## 4. 常见错误 / 自检清单

- [ ] 旗帜是 **TGA 32bpp**，扩展名不能写 `.dds`；文件放对三档目录。
- [ ] 意识形态后缀必须是 `democratic` / `communism` / `fascism` / `neutrality`（组名，不是子意识形态如 `nazism`）。
- [ ] `set_cosmetic_tag` 用的名字 = 文件名（含 `_ideology` 后缀时按意识形态轮换）。
- [ ] 领袖肖像 156×210；`.dds` 未压缩；文件在 `gfx/leaders/<TAG>/`。
- [ ] 角色 `portraits = { ... }` 里写的是 **sprite 名**，且 `.gfx` 已注册。
- [ ] 小头像 sprite（`_small`）指向 `gfx/interface/ideas/` 的图，别和 large 用同一张（比例不对）。
- [ ] 肖像文件名大小写、空格都会导致找不到（原版有 `'focus_AFG_anti_malaria .dds'` 这种带空格的坑，自己别学）。
- [ ] 换旗帜后必须重启游戏 + 新开档（旗帜缓存按国家计算）。

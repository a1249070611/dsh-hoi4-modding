---
title: 从零建一个 mod（目录 / descriptor / path / supported_version / 启动器识别）
domain: 06_workflow
scope: workflow
verified_on: 1.19.x
verified_at: 2026-10-26
sources:
  - https://hoi4.paradoxwikis.com/Modding
  - https://hoi4.paradoxwikis.com/Mod_structure
  - launcher-settings.json
  - mod
  - dlc_load.json
---

# 从零建 mod

基线 **1.19.x**（1.19.3.x 起实测，1.19.4.x 上未变）。所有模板都能直接抄，但**先读 §6 的 ASCII 路径陷阱**——它决定你把 mod 放在哪。

## 1. 最终形态（最小可被启动器识别的 mod）

```
用户目录/
└─ mod/
   ├─ hho_hello.mod              ← ① 用户特定描述（唯一写 path 的地方；文件名决定加载顺序）
   └─ hho_hello/                 ← ② mod 本体根目录（等同原版 game 根目录）
      ├─ descriptor.mod         ← ③ mod 特定描述（跟随分发，不写 path）
      ├─ thumbnail.png          ← ④ 封面（可选但建议；文件名必须这个）
      ├─ common/
      ├─ events/
      ├─ history/
      ├─ localisation/
      │  ├─ english/
      │  └─ simp_chinese/
      ├─ interface/  gfx/
      └─ README.md
```

三件套缺一不可：**① `.mod` + ② 本体目录 + ③ `descriptor.mod`**。
（wiki `Mod_structure`：`.mod` 负责告诉启动器怎么加载；`descriptor.mod` 是随 mod 一起分发的那份信息；封面放在本体根目录。）

## 2. 三个文件的完整模板（命名空间示例 `HHO_`）

### ① `用户目录/mod/hho_hello.mod`（本地安装用）

```pdx
name = "Hello HOI4"
version = "0.1.0"
supported_version = "1.19.*"
tags = {
	"Gameplay"
	"Historical"
}
picture = "thumbnail.png"
path = "mod/hho_hello"
```

- `path` 写**相对用户目录**的短路径（`mod/hho_hello`）或绝对路径（`C:/hoi4mods/hho_hello`）。**只用 `/`，只用 ASCII。**
- `name` 必须**全局唯一**（同名 mod 只有先加载的那个生效，wiki 明确列为常见错误）。
- 本地 mod 的 `picture` **在启动器里不会显示**，这是正常行为（wiki 原文）。

### ② `hho_hello/descriptor.mod`（随 mod 分发）

```pdx
name = "Hello HOI4"
version = "0.1.0"
supported_version = "1.19.*"
tags = {
	"Gameplay"
	"Historical"
}
picture = "thumbnail.png"
```

**没有 `path`**。其余字段与 ① 保持一致。
> 注意：`descriptor.mod` **不能存成 UTF-8 BOM**（wiki 明写）——这是它和 `.yml` 本地化文件相反的编码要求。

### ③ 发布时才出现的字段（先知道，见 [publishing.md](publishing.md)）

```pdx
remote_file_id = "1234567890"   # 创意工坊/Paradox Mods 回填，本地开发时不要手写
dependencies = { "Main Mod" }   # 子 mod 用；name 必须逐字符一致
replace_path = "history/states" # 危险字段，两个 .mod 都要写
user_dir = "MyModSaves"         # 改存档目录，防止与其它 mod 串档
```

## 3. `path` 的规则（本领域最贵的坑）

| 规则 | 说明 | 违规后果 |
|---|---|---|
| 分隔符**只能是 `/`** | `path = "mod\my_mod"` 里的 `\` 会被当**转义符** | 启动器显示 invalid path / 加载不到 |
| **只能是 ASCII** | 含中文、西里尔、带变音符的字母 → mod **加载失败** | 启动器能看到名字，进游戏毫无效果 |
| 指向**直接包含 `common/` 的那一层** | 多套一层（`mod/my_mod/cool_mod`）而 path 写 `mod/my_mod` → 文件被当成别的路径 | 部分内容「消失」 |
| 相对路径自动补成「用户目录 + path」 | `mod/hho_hello` → `C:/Users/…/Hearts of Iron IV/mod/hho_hello` | — |
| 绝对路径也支持 | 本机创意工坊 mod 就这么写：`path="<工坊目录>/3243611664"` | — |

工坊 mod 的 `.mod` 实例（可对照）：

```
mod/ugc_3243611664.mod:
  path = "<工坊目录>/3243611664"   ← 绝对路径 + 正斜杠 + 纯 ASCII ✅
```

## 4. `supported_version` 的合法写法（本机实测得出）

| 写法 | 是否合法 | 实测证据（1.19.x） |
|---|---|---|
| `"1.19.3.0"` | ✅ | `mod/The road to 56 CN.mod`、`ugc_2067895531.mod`，无报错 |
| `"1.19.*"` | ✅ | `mod/BlackIce_Tech_Tree.mod`，无报错 |
| `"1.19.3.*"` | ✅ | `mod/ugc_1521695605.mod`，无报错 |
| `"1.19.2.0"` | ✅ | `mod/ugc_3243611664.mod`，无报错（小版本旧不算错） |
| `"1.12.14"` | ✅（旧版本号） | 合法但启动器会标旧 |
| `"1.*"` | ❌ | **5 个 mod 报 `Invalid supported_version`** |
| `"*"` | ❌ | 1 个报错 |
| `"1.*.*"` | ❌ | 1 个报错 |

**规则**：通配符**只能在最后一段**，且至少要写 `大版本.小版本`。
**推荐**：`"1.19.*"` —— 1.19.x 小补丁不用改。

## 5. 启动器如何「认出」你的 mod

1. 启动器扫描**用户目录 `mod/` 下所有 `.mod` 文件**（读 `name`/`path`/`picture`/`tags`/`version`）。
2. 把结果写进 `launcher-v2.sqlite`（播放集信息）。**启动器有缓存**：改了 `.mod` 但启动器还显示旧信息/一直报 invalid path 时，wiki 给的解法是**删掉 `launcher-v2.sqlite`**（本机该文件存在，另有 `launcher-v2_backup.sqlite`）→ 启动器会重新扫描所有 `.mod` 重建列表。
3. 你勾选 mod 后，启动器把启用列表写进 `dlc_load.json`，游戏读它。

`dlc_load.json` 的真实形态：

```json
{"enabled_mods":["mod/ugc_2977114459.mod","mod/BlackIce_Tech_Tree.mod"],"disabled_dlcs":[]}
```

- 路径是「相对用户目录的 `.mod` 路径」。
- **不要手写这个文件去做「测试」**：启动器每次启动都会重写它。

## 6. 🚨 路径含非 ASCII 的陷阱（本领域最贵的一条）

- 两条硬结论（wiki）：
  1. `path` **只能 ASCII**，否则 mod 加载失败；
  2. **用户目录**本身含非 ASCII 时，游戏**连 `error.log` 都打不开**。
- 推论：开发目录（中文用户名、中文项目名）与安装目录要分开；`path` 只能指向纯 ASCII 路径。

**三种方案（按推荐度）**：

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| A（推荐） | 把 mod 目录放到/复制到纯 ASCII 路径（如 `C:/hoi4mods/my_mod`），`.mod` 的 `path` 指过去 | 100% 符合 wiki 规则 | 需要一份 ASCII 路径的副本 |
| B | `.mod` 里的 `path` 写成 `mod/my_mod`，把目录放进用户目录 `mod/` 下 | 最标准（相对路径） | 要写用户目录 |
| C | 把 `path` 直接指向含中文的开发目录 | 零成本 | **大概率加载失败**，不能作为交付形态 |

> 结论先行：**不要把「mod 能跑」建立在中文路径上。** 失败表现可能是完全不加载、只加载一部分、或无任何报错——先在纯 ASCII 路径下复现，再谈其它原因。

## 7. 建 mod 的落地步骤（不启动游戏也能做到 90%）

```bash
# 1) 建骨架（先在任何可写目录写，验证通过后再决定安装位置）
mkdir -p my_mod/{common,events,localisation/english,localisation/simp_chinese}

# 2) 写三个描述文件（见 §2），注意 descriptor.mod 不加 BOM

# 3) 静态自检（不需要游戏）
#    a. 花括号平衡
python scripts/hoi4_lint.py my_mod
#    b. 手工兜底：用编辑器确认 {} 配对、文件编码 UTF-8(no BOM) / .yml UTF-8(BOM)
```

装到机器的最后一步（要写用户目录，建议由人确认后执行）：

```
1. 把 <mod 文件夹> 放到纯 ASCII 路径（方案 A）
2. 在用户目录 mod/ 放 <name>.mod，path 指过去
3. 启动器 → 播放集 → 勾选 → 启动游戏
4. 看主菜单版本旁的 checksum 是否变化（变了说明 mod 被加载）
5. 若加载不到：删 launcher-v2.sqlite 重开启动器；再核对 path 是否含中文/反斜杠
```

## 8. 校验和：什么时候你的 mod 会破坏联机/成就

`checksum_manifest.txt`（本机实际内容）覆盖：

```
common/**.txt  common/**.lua
events/**.txt
history/**.txt
map/**.txt  map/**.map  map/**.bmp  map/**.csv
```

- 改这些 → **改校验和** → 只能与相同校验和的人联机、拿不到成就。
- 只改 `localisation/`、`gfx/`、`interface/` → 通常**不改**校验和（这是「翻译类子 mod 可以和原版联机」的机制基础）。
- 结论：**想兼容联机，就把内容做成「新增文件 + 运行时注入」并尽量不碰上面四类目录**（但内容型 mod 必然要碰 `common/`，此时只能接受「需同 mod 才能联机」）。

## 常见错误 / 自检清单

- [ ] `mod/xxx.mod` 有 `path`，`xxx/descriptor.mod` 没有 `path`？
- [ ] 两个文件的 `name` 完全一致？
- [ ] `path` 是正斜杠 + 纯 ASCII + 指向含 `common/` 的那层？
- [ ] `supported_version` 是 `1.19.*`（不是 `1.*`）？
- [ ] 封面叫 `thumbnail.png`，字段叫 `picture=`？
- [ ] `descriptor.mod` 没有 BOM；`.yml` 有 BOM？
- [ ] 启动器报 invalid path 时，试过删 `launcher-v2.sqlite`？
- [ ] 是否知道自己的 mod 会不会改校验和？
- [ ] `path` 是否指向纯 ASCII 路径（不含中文）？

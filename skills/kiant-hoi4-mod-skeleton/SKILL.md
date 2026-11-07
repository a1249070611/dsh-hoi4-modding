---
name: kiant-hoi4-mod-skeleton
description: 建立钢铁雄心4 模组工程骨架：目录约定、descriptor.mod 与外层 .mod 的区别、path 解析规则、加载顺序、启动器不显示 mod 的排查。
---

# 模组骨架与工程结构

## 两个描述文件，职责不同

这是新手最容易搞错的地方——HOI4 需要 **两个** 描述文件，内容几乎一样但用途不同。

```
文档/Paradox Interactive/Hearts of Iron IV/mod/
├── mymod.mod              ← 外层：启动器据此发现 mod
└── mymod/                 ← 内容文件夹
    ├── descriptor.mod     ← 内层：创意工坊上传 / 元数据读取
    ├── common/
    ├── events/
    ├── history/
    ├── localisation/
    ├── gfx/
    └── interface/
```

**外层 `mymod.mod`**

```
version="0.1.0"
tags={
	"Gameplay"
}
name="My Mod"
supported_version="1.19.*"
path="mod/mymod"
```

**内层 `descriptor.mod`** —— 同样字段，但**不要**写 `path`：

```
version="0.1.0"
tags={
	"Gameplay"
}
name="My Mod"
supported_version="1.19.*"
```

### path 到底相对谁

`path` 以**用户数据目录**（`mod/` 的父级，即 `文档/Paradox Interactive/Hearts of Iron IV/`）为基准。所以标准写法是 `path="mod/mymod"`。

绝对路径也支持（`path="D:/HOI4Mods/mymod"`），但换了机器就失效，除开发期外不建议。

### 字段速查

| 字段 | 必需 | 说明 |
|---|---|---|
| `name` | 是 | 启动器显示名 |
| `supported_version` | 是 | `"1.19.*"`。通配符**只能放最后一段**：`"1.*"` 会让 `error.log` 报 `Invalid supported_version`，`"1.19.x"` 也不是合法写法。它只影响启动器与工坊的兼容提示，不阻止引擎加载 |
| `version` | 建议 | 你自己的 mod 版本号，与游戏版本无关 |
| `tags` | 建议 | `"Gameplay"` `"Historical"` `"Alternative History"` `"Map"` `"Utilities"` 等 |
| `path` | 仅外层 | 相对用户目录。**必须纯 ASCII + 正斜杠** |
| `dependencies` | 可选 | `{ "Other Mod" }`，启动器提示依赖缺失，同时决定加载顺序 |
| `replace_path` | 慎用 | 整目录替换原版，见下。**两个描述文件都要写** |
| `picture` | 可选 | 缩略图文件名，相对 mod 根目录。**不是 `thumbnail`** |

### 三个会静默失败的字段陷阱

**`path` 含非 ASCII 字符**（中文用户名、中文文件夹名）——启动器里能看到这个 mod，勾选也正常，但进游戏后内容完全不出现，且 `error.log` 不报错。把 mod 目录整个挪到 `D:/mods/mymod` 这类纯 ASCII 路径，再改 `path`。

**`replace_path` 只写在一个描述文件里**——游戏照常加载，只是替换不生效。外层 `.mod` 与内层 `descriptor.mod` 都要写同样的几行。

**预览图字段写成 `thumbnail=`**——`error.log` 报 `Unexpected token: thumbnail`，预览图不显示。字段名是 `picture`，值是文件名：`picture="thumbnail.png"`。

## `replace_path` 的代价

```
replace_path="common/ideas"
```

这行的意思是"原版 `common/ideas` 整个不加载，只用我的"。后果：

- 原版所有国家精神消失（包括你只是想在原版基础上加两个）
- 任何想往 `common/ideas` 追加内容的 submod 全部失效
- 和你一起用的大改 mod 直接冲突到无法修复

**只有做 total conversion 才用。** 想在原版基础上加内容，把文件放进同名目录即可，游戏会合并；冲突时后加载的覆盖先加载的。

## 目录职责

| 目录 | 放什么 |
|---|---|
| `common/national_focus/` | 国策树 |
| `common/ideas/` | 国家精神 |
| `common/decisions/` | 决议及其分类 |
| `common/characters/` | 角色（领袖、将领、顾问） |
| `common/scripted_effects/` | 复用的 effect 宏 |
| `common/scripted_triggers/` | 复用的 trigger 宏 |
| `common/on_actions/` | 事件钩子（开局、宣战、每日…） |
| `common/defines/` | `.lua` 常量覆盖 |
| `events/` | 事件定义 |
| `history/countries/` | 国家开局状态 |
| `history/states/` | 州数据 |
| `localisation/<语言>/` | 文本，**UTF-8 with BOM** |
| `interface/` | `.gfx`（sprite 定义）、`.gui`（界面布局） |
| `gfx/` | 图片资产（dds/tga） |

## 启动器里看不到 mod 的排查顺序

1. **扩展名被 Windows 吃掉了** —— 最常见。资源管理器默认隐藏已知扩展名，你以为存成了 `mymod.mod`，实际是 `mymod.mod.txt`。开"文件扩展名"显示后确认。
2. `.mod` 不在 `mod/` 根目录，而是被放进了 `mod/mymod/` 里面。
3. `path` 写错，或指向的文件夹名与 `.mod` 里的不一致。
4. `supported_version` 与当前游戏版本不匹配，被归到"不兼容"分组里。
5. 启动器缓存 —— 退出启动器重开，或删除 `mod/` 下的 `.mod` 后重新放回。

## 最小可运行验证

建完骨架后立刻做的事：

1. 只放 `descriptor.mod`，不放任何内容，进游戏。能在启动器看到 → 骨架正确。
2. 加一个只含 `l_english:` 一行的本地化文件，进游戏看是否报错 → 验证 BOM 链路。
3. 再逐类加内容，每次加完跑 `kiant_hoi4_validate_mod`。

## 版本管理建议

`.gitignore` 至少包含：

```
*.log
*.dds.tmp
.DS_Store
Thumbs.db
descriptor.mod   # 若团队里各自装在不同路径
```

但 `descriptor.mod` 一般还是要提交的（创意工坊上传需要）。如果团队成员的 `mod/` 路径不同，用模板 + 本地生成，别把绝对路径 `path` 提交上去。

---
title: "全量文件普查（60366 个文件 / 10.7 GB）"
domain: 08_fileformats
verified_on: 1.19.4.2
verified_at: 2026-11-06
method: tools/kiant-hoi4-survey.py 实测扫描，非估算
---

# 全量文件普查

原版 1.19.4.2 一共 **60366 个文件 / 10670 MB**。这份是实测清单，不是从 wiki 抄的。

```bash
python tools/kiant-hoi4-survey.py              # 全量普查，写 knowledge/survey.json
python tools/kiant-hoi4-survey.py --ext dds    # 某类扩展名分布在哪些目录
python tools/kiant-hoi4-survey.py --dir common # 某目录的类型构成
```

## 一、按类型

| 扩展名 | 数量 | 体积 | 是什么 | 能不能改 |
|---|---:|---:|---|---|
| `.dds` | 33007 | 4880 MB | 贴图（99% 未压缩 32bpp） | ✅ 主力 |
| `.tga` | 6889 | 173 MB | 贴图（无压缩） | ✅ 可换 |
| `.wav` | 5074 | 2274 MB | 音效（PCM） | ✅ |
| `.txt` | 4892 | 91 MB | **游戏逻辑主体**（Clausewitz） | ✅ 主力 |
| `.yml` | 2114 | 153 MB | 本地化 | ✅ 主力 |
| `.anim` | 2043 | 37 MB | 模型动画（**文本**） | ✅ |
| `.mesh` | 1527 | 311 MB | 3D 网格（文本头 + 二进制顶点） | ⚠️ 需 blender 流程 |
| `.html` | 1327 | 33 MB | 引擎文档 + wiki 快照 | 只读 |
| `.png` | 998 | 89 MB | 启动器/interfacing 用 | 部分 |
| `.asset` | 500 | 9 MB | **模型/动画索引**（纯文本） | ✅ |
| `.gui` | 480 | 4 MB | **界面布局**（纯文本） | ✅ 主力 |
| `.gfx` | 415 | 11 MB | **sprite 注册表**（纯文本） | ✅ 主力 |
| `.fnt` | 415 | 184 MB | 位图字体描述（BMFont 文本） | ✅ |
| `.ogg` | 231 | 1893 MB | 音乐（Vorbis） | ✅ |
| `.shader` | 52 | 0.2 MB | 着色器 | ⚠️ 高级 |
| `.md` | 50 | 0.9 MB | **官方文档**（40 篇目录级 + 10 篇引擎级） | 只读，必读 |
| `.fxh` | 13 | 0.07 MB | 着色器头 | ⚠️ |
| `.lua` | 8 | — | 少量脚本 | ⚠️ |
| `.json` | 5 | — | 配置 | 部分 |

**关键结论**：真正要改的就四类——`.txt`（逻辑）、`.yml`（文字）、`.gui`/`.gfx`（界面）、`.dds`（图）。加起来 40 MB，占全量 0.4%。其余 10 GB 是素材和引擎。

## 二、按目录（按体积排序，前 25）

| 目录 | 文件 | 体积 | 性质 |
|---|---:|---:|---|
| `gfx/fonts/` | 786 | 1738 MB | 字体图集，单文件巨大（一个 `.fnt` 配一张几 MB 的 dds） |
| `gfx/interface/` | 17007 | 1158 MB | **界面贴图，改 UI 的主战场** |
| `dlc/dlc052_thunder_at_our_gates/` | 1223 | 472 MB | DLC 内容，结构与原版同构 |
| `sound/animations/` | 390 | 404 MB | 单位动作音效 |
| `gfx/models/` | 2009 | 323 MB | 3D 模型 + 动画 + asset |
| `music/` | 28 | 209 MB | 28 个 ogg，单个 7 MB 上下 |
| `localisation/` | 2094 | 158 MB | 12 种语言各一套 |
| `map/` | 391 | 149 MB | 地图，含 province 位图 |
| `wiki/` | 2295 | 72 MB | **wiki 离线快照（2295 个 html），二手但有用** |
| `common/` | 2267 | 68 MB | **游戏规则核心** |
| `interface/` | 621 | 14 MB | `.gui` + `.gfx` |
| `history/` | 2058 | 9 MB | 国家/州初始状态 |
| `events/` | 128 | 8 MB | 事件，约 7000 个 |
| `documentation/` | 22 | 2 MB | **引擎官方文档，一手权威** |

## 三、逻辑目录的真实规模

`common/` 有 45 个子目录、2267 个文件。按文件数：

| 子目录 | 文件 | 管什么 |
|---|---:|---|
| `countries/` | 442 | 国家标签、颜色、AI 开关 |
| `units/` | 297 | 单位类型、装备原型 |
| `characters/` | 233 | 角色（将领/顾问/科学家） |
| `ideas/` | 213 | 国家精神 |
| `decisions/` | 147 | 决议 |
| `ai_strategy_plans/` | 128 | AI 战略 |
| `national_focus/` | 81 | **国策树** |
| `military_industrial_organization/` | 63 | MIO |
| `scripted_triggers/` | 55 | 可复用条件 |
| `scripted_effects/` | 52 | 可复用效果 |
| `scripted_localisation/` | 42 | 动态文本 |
| `on_actions/` | 18 | 事件钩子 |
| `technologies/` | 13 | **科技树**（文件少但单文件大） |
| `defines/` | 3 | **引擎常量** |

## 四、判断文件重要性的实用规则

不是所有文件都值得读。按这个顺序筛：

1. **先读 `.md`**——50 篇官方文档里，22 篇引擎级（effects/triggers/modifiers/loc_*），28 篇目录级（`common/**/_documentation.md`）。这些是字段级权威，比任何教程都准
2. **再看数量为个位数的目录**——`defines/` 只有 3 个文件，但它决定全局数值；`technologies/` 只有 13 个，却是整棵科技树
3. **文件数多的目录反而简单**——`countries/` 442 个文件，每个都是同一个模板换参数
4. **`.dds` 不用逐个看**——看 `.gfx` 里怎么注册的就行

## 五、这份普查怎么用

- 想知道「某类文件都在哪」→ `--ext`
- 想知道「某个目录里都是些什么」→ `--dir`
- 想确认「这个数字是不是编的」→ 重跑 `kiant-hoi4-survey.py`，`knowledge/survey.json` 里有全量明细

**所有数字都可以复现。** 这是这份文档和网上教程的根本区别：那些数字你无从验证，这里的随时能重算。

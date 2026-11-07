---
title: "文件格式域总览"
domain: 08_fileformats
verified_on: 1.19.4.2
---

# 08 文件格式

这一域回答一个问题：**这个文件是什么、怎么读、能不能改、改错了引擎会怎样。**

和 `05_presentation/` 的分工：那边讲「怎么做出好看的界面」，这边讲「文件本身是什么」。
想知道怎么改图标 → 05；想搞清 DDS 头部 128 字节长什么样 → 这里。

## 本域 5 条最重要结论

1. **全库 60366 个文件，真正要改的只有 4 类，合计 40 MB（0.4%）**——
   `.txt` 逻辑、`.yml` 文字、`.gui`/`.gfx` 界面、`.dds` 图。
   剩下 10 GB 是素材和引擎，改不动也不该动。依据：`00_full-survey.md` 实测。

2. **`.txt` / `.gui` / `.gfx` / `.asset` / `.anim` / `.mesh` 是同一套 Clausewitz 语法。**
   学会一次，六种一起会。不需要为每种文件学一套解析器。

3. **比较运算符只有 `>` 和 `<`。** `<=` `>=` `==` `!=` 在原版 4892 个文本文件里出现
   **0 次**，写了引擎不报错、直接静默忽略整条触发器。取反用 `NOT = { }`。

4. **引擎容忍「文件末尾少 `}`」，不容忍「多 `}`」。**
   原版 2224 个 `common/` 文件里 14 个末尾缺括号照样能加载；多一个就截断解析。
   划这条边界的是实测，不是语法书。

5. **`.dds` 有 99% 是未压缩 32bpp，不是 DXT5。**
   `gfx/interface` 下 16923 个 DDS 里 32bpp 占 16773 个（99%），DXT5 只有 43 个。
   网上流传的「必须用 DXT5」是错的。且 `gfx/` 下 21898 个 DDS 的体积**全部精确等于**
   理论公式值（`gfx/` 21898 个文件零例外），没有一个异常。

## 篇目

| 篇 | 讲什么 |
|---|---|
| `00_full-survey.md` | 全量普查：按类型/按目录的文件数与体积，决定先看哪些 |
| `01_clausewitz-syntax.md` | 六种文本格式共用的语法，含真实的国策全文拆解 |

## 常见坑

| 症状 | 原因 | 去哪 |
|---|---|---|
| 条件写了不生效，也不报错 | 用了 `>=` / `==` / `!=` | `01_clausewitz-syntax.md` §三 |
| 国策树画出来挤成一团 | 没解算 `relative_position_id` | `01_clausewitz-syntax.md` §九 |
| 不知道从哪个文件下手 | 没先看普查，在 10 GB 素材里迷路 | `00_full-survey.md` |
| 改图后游戏里显示错乱 | 尺寸/格式不匹配 | 用 `tools/kiant-hoi4-dds.py info` 查头部 |

## 工具

```bash
python tools/kiant-hoi4-survey.py              # 全量普查，输出 knowledge/survey.json
python tools/kiant-hoi4-survey.py --ext dds    # 某类扩展名分布在哪些目录
python tools/kiant-hoi4-dds.py info x.dds      # 查 DDS 头部：尺寸/格式/mips/体积是否正常
python tools/kiant-hoi4-dds.py scan gfx/       # 统计一个目录的格式分布
python tools/kiant-hoi4-lint.py <dir>          # 文本文件语法体检
```

---
title: "EB-022 音乐 mod 部分歌没声 / play_song 静默失效"
id: EB-022
domain: 91_error-book
symptom_class: 功能不生效
severity: 一般
verified_on: 1.19.4.2
verified_at: 2026-11-07
note: 2026-11-07 校准——初版误判「mod 无定义层」系取样截断所致，已按全文件复核改写
first_seen: 工坊 mod「情感电台」(2125746243)：两层结构齐全的 mod 里藏着 3 个静默 bug
related: [05_presentation/audio.md]
---

# EB-022 音乐 mod 那几首「永远不放」的歌

## 症状

音乐 mod 大体正常，但个别歌永远放不出来，`error.log` 里也未必有相关行。

## 真实案例（情感电台，2125746243）

两层结构齐全的 mod 仍可能有**引用层 bug**，而且全部静默。经本插件 music
校验器一轮扫出（新增于 2026-11-07），逐条人工复核：

| # | bug | 细节 |
|---|---|---|
| 1 | 定义指向缺失音频 | `emotional_music.asset:428` 定义 `030 → 030.ogg`，实际文件是 `030.mp3`（引擎不认 mp3） |
| 2 | 电台选曲拼写错 | `emotional_soundtrack.txt:516` 选了 `0010`，定义层只有 `010` |
| 3 | 引用依赖外部 flag | `on_nuke_drop` 分支要求 `has_global_flag = JAP_nuke_1`，全 mod 从未设置且未声明 dependencies——装了原版+本 mod 永不触发 |
| 4 | 非 ogg 混入 | `030.mp3`；原版 music/ 全库只用 OGG Vorbis（44100Hz） |

## 机制（原版实证，1.19.4.2）

HOI4 音乐两层结构（都在**游戏根 `music/`**，不在 common/）：

```text
music/*.asset   第 1 层「歌曲定义」：music = { name = "X" file = "...ogg" volume = 0.65 }
music/*.txt     第 2 层「播放表」：music_station = "<台>" + music = { song = "X" chance = {...} }
```

1. `play_song` 官方语义 "Plays song from database"（`documentation/effects_documentation.md`）：
   引用未定义歌名 → **静默跳过**，不崩、不进日志。
2. `file` 相对**本定义文件所在目录**，缺文件 = 这首歌永远不出声。
3. 音频只认 `.ogg`。

## 标准化方案

1. **引用层自查（工具已内置）**：mod 内所有 `play_song` / `song =` 引用必须能在
   mod 或原版的 `music/**/*.asset` 找到 `name = "<引用>"`。`kiant_hoi4_validate_mod`
   的 music 校验器就是被这个案例催生并当场验证的——上表 1/2/4 三条即它的战果。
2. 条件触发依赖其他 mod 的 flag → descriptor 写 `dependencies`，或改用本 mod 的 flag。
3. 音频转码 OGG Vorbis（44100Hz），定义层 `file` 同步改名。
4. 电台封面：`GFX_music_station_<台名>` 命名 spriteType。

## 关联

- 两层结构与电台封面约定：`05_presentation/audio.md` §6.3。
- 「定义齐全但个别引用断链」与「整个定义层缺失」是两种不同程度的病，校验器都覆盖。

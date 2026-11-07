---
title: 音频（sound / music）
domain: 05_presentation
scope: audio
verified_on: 1.19.x
verified_at: 2026-10-26
---

# 音频：`sound/*.asset` 与 `music/`

## 1. 目录与文件（本机实测）

```text
sound/
├─ sound.asset                 # 第 1 层：把“文件”注册成“声音”（sound = { name file }），901 处 .wav 引用
├─ soundeffects.asset          # 第 2 层：把“声音”组合成“音效”（soundeffect = { name sounds{...} }）
├─ category.asset              # 第 3 层：把“音效”分进播放/音量分组（category = { name soundeffects{...} }）
├─ falloff.asset               # 3D 距离衰减曲线（min_distance/max_distance/height_scale）
├─ compressor.asset            # 动态压缩器
├─ gui/gui_sound_effects.asset # UI 音效（click_default / click_close / click_ok …）
├─ menu/                       # 主菜单音效 wav（click_default.wav 等）
├─ animations/ awards/ weather/ audiofiles/ placeholders/ gtd/ sea/
music/
├─ music.asset                 # 音乐文件注册（music = { name file volume }）
├─ _songs.txt                  # 播放表 + 播放条件（music_station / music = { song chance }）
└─ *.ogg                       # 26 首 OGG（顶层），加上 soundtrack/ 下 DLC 共 61 首
soundtrack/                    # DLC 音乐包目录（dlc011_german_march_order_music_pack 等）
```

**三层对象的关系**（一定分清）：

```text
文件 (a.wav/.ogg)  --sound.asset-->  sound  --soundeffects.asset-->  soundeffect  --category.asset--> 播放分组
                                                                    ↑
                                       GUI 的 clicksound / oversound、脚本的 play_sound 都引用 soundeffect 名
```

## 2. 第 1 层：`sound = { }`（文件 → 声音）

```pdx
# sound/sound.asset 节选
sound = {
	name = "click_default"
	file = "menu/click_default.wav"     # 相对 sound/ 目录
	always_load = no                    # no = 用到时加载
}
```

- `file` 是相对 `sound/` 的路径；原版 901 处引用**全是 `.wav`**。
- `always_load = yes` 会把音频常驻内存（只给极少用的音效用）。

## 3. 第 2 层：`soundeffect = { }`（声音 → 音效）

```pdx
# sound/gui/gui_sound_effects.asset
soundeffect = {
	name = click_default
	volume = 0.45
	sounds = {
		sound = click_default          # 引用 sound.asset 里的 name
	}
}
```

3D 音效（`sound/soundeffects.asset:2-12`）：

```pdx
soundeffect = {
	name = horse_walking
	loop = yes
	falloff = "falloff_100"            # 引用 falloff.asset 里的曲线
	sounds = {
		sound = cavalry_entity_move_01
	}
	is3d = yes
	max_audible = 1                    # 最多同时播放 1 个
	max_audible_behaviour = fail       # 超过上限时的行为
	volume = 0.5
}
```

- `sounds = { }` 里可放多个 `sound`：每次随机取一个（原版用这个做“连续点击不重复”）。
- `falloff` 定义格式（`sound/falloff.asset`）：`falloff = { name = falloff_100 min_distance = 20.0 max_distance = 100.0 height_scale = 1.0 }`。
- UI 音效不要写 `is3d = yes`，不要写 `falloff`。

## 4. 第 3 层：`category = { }`（音效 → 播放分组）

```pdx
# sound/category.asset
category = {
	name = "Effects"
	soundeffects = {
		peace_conference
		event_popup
		complete_focus
		research_complete
		click_default          # 注意：需要在该分组里出现，音量滑块才管得住它
		...
	}
}
```

作用：把音效归入「效果音 / 音乐 / 界面」等分组，玩家的音量设置按组生效；**没有归组的音效可能不播放或不受音量控制**。

## 5. GUI / 脚本里怎么用

| 位置 | 写法 | 例 |
|---|---|---|
| `.gui` 按钮点击音 | `clicksound = <soundeffect 名>` | `clicksound = click_default`（原版 758 处） |
| `.gui` 按钮悬停音 | `oversound = <soundeffect 名>` | `oversound = command_power_ability_over` |
| 脚本 effect | `play_sound = <soundeffect 名>`（详见 `documentation/effects_documentation.md` 搜 `play_sound`） | — |

原版 `clicksound` 常用值：`click_default`(758)、`click_checkbox`(347)、`click_close`(227)、`click_scroll`(81)、`click_ok`(51)。

## 6. 音乐：两个文件配合

### 6.1 `music/music.asset`（注册曲目）

```pdx
# music/music.asset
music = {
	name = "maintheme"
	file = "hoi4mainthemeallies.ogg"     # 相对 music/ 目录
	volume = 0.65
}
music = {
	name = "general_peace_1"
	file = "general_peace_heartsofmen.ogg"
	volume = 0.65
}
```

### 6.2 `music/_songs.txt`（播放表 + 条件权重）

```pdx
music_station = "base_music"      # 电台名（文件第一行）

music = {
	song = "maintheme"
	chance = {
		modifier = {
			factor = 0.5
		}
	}
}

# 只在“和平时”播这首
music = {
	song = "general_peace_1"
	chance = {
		modifier = {
			factor = 1
			has_war = no
		}
	}
}

# 共产党 + 战争 权重 ×2
music = {
	song = "comintern_war_3"
	chance = {
		modifier = {
			factor = 2
			has_war = yes
			has_government = communism
		}
	}
}
```

- `song` 的名字必须等于 `music.asset` 里的 `name`。
- `chance = { modifier = { factor/条件 } }` 控制“下一首抽到它的权重”，条件写 scope = 玩家国家的 trigger。

### 6.3 mod 新增电台（2026-11-07 工坊实测补证）

mod 加电台**不需要注册任何额外东西**：`music_station = "<名字>"` 一行即可建台。
此前的「mod 新增电台未经实测」悬案由两个在营 mod 实测落定：

- 百年战争电台 (3794947970)：6 个台 = 6 个 `music/<台名>.txt`（每台一行
  `music_station` + 按年代/国家加权的选曲表），每台另配一个
  `music/<台名>.asset` 做歌曲定义层——与原版两层完全同构。
- KR Music (1360299796)：单文件 `music/00 general music.txt` 内多个
  `music_station` 分段收几百首。

**两条高频失效**（详见错题本 [EB-022](../91_error-book/EB-022-music-mod-silent.md)）：

1. 只带 ogg 不带 `.asset` 定义 → `play_song`/电台全静默（官方文档原话
   "Plays song from database"，没进库就跳过，不报错）。
2. 条件触发依赖其他 mod 的 flag（如 `JAP_nuke_1`）而没写 `dependencies` → 永不触发。

电台封面：`GFX_music_station_<台名>` 命名的 spriteType，电台列表自动取用。
事件驱动放歌：

```pdx
on_declare_war = {
    effect = {
        if = { limit = { ROOT = { tag = GER } FROM = { tag = POL } }
            hidden_effect = { play_song = "my_song" } }   # 歌名必须已进 .asset
    }
}
```

## 7. 音频格式规范（本机实测参数）

| 用途 | 格式 | 实测参数 | 说明 |
|---|---|---|---|
| 音乐 | **OGG Vorbis** | 立体声 44100 Hz，nominal bitrate **320 kbps** | `music/*.ogg` 26 首；单曲 2–14 MB |
| 音效（SFX） | **WAV PCM** | 单声道 44100 Hz 16-bit | 例：`sound/menu/click_default.wav`（原版 901 处引用全为 `.wav`） |

- OGG 必须是 **Vorbis**（不是 Opus）。用 `ffmpeg` 转：`ffmpeg -i in.wav -c:a libvorbis -ar 44100 -ac 2 -b:a 320k out.ogg`。
- WAV 用 16-bit PCM，别用 24/32-bit 或 float（发动机对 PCM 格式挑剔）。
- UI 音效建议做成单声道、音量归一化到 -3 dB 左右（原版 `volume = 0.45` 的量级）。
- ⚠️ 音效用 `.ogg` 是否被 HOI4 接受：原版 0 先例（全是 wav），未经实测，**保守起见音效用 wav、音乐用 ogg**。

## 8. 新增一个「点击音效」完整流程（最小 4 步）

1. 放文件：`sound/NS/my_click.wav`（44.1kHz 16-bit mono）。
2. `sound/NS_sound.asset` 注册声音：

```pdx
sound = {
	name = "NS_my_click"
	file = "NS/my_click.wav"
	always_load = no
}
```

3. `sound/NS_soundeffects.asset` 注册音效：

```pdx
soundeffect = {
	name = NS_my_click_sfx
	volume = 0.5
	sounds = { sound = NS_my_click }
}
```

4. `sound/category.asset` 里把 `NS_my_click_sfx` 加进 `Effects` 分组（**改原版文件 = 整文件替换**，更安全的做法是新增自己的 category 文件——但同一 `category` 名重复会被后加载的覆盖；⚠️ 本机未验证多文件同名 category 的合并行为，保守做法是复制原 `category.asset` 后追加）。

5. `.gui` 里用：`clicksound = NS_my_click_sfx`。

## 9. 常见错误 / 自检清单

- [ ] 三层名对得上：`sound.name` ← `soundeffect.sounds.sound` → `soundeffect.name` ← `clicksound`/`play_sound`。
- [ ] `.asset` 放在 `sound/`（或 `sound/` 子目录）下，扩展名 `.asset`，外层键是 `sound` / `soundeffect` / `category` / `falloff`。
- [ ] `file` 路径相对 `sound/`（音乐相对 `music/`），用 `/`。
- [ ] 音乐 `.ogg` 是 Vorbis、44.1kHz；音效 `.wav` 是 16-bit PCM。
- [ ] UI 音效没写 `is3d = yes` / `falloff`。
- [ ] `soundeffect` 已加入某个 `category`（否则可能不受音量控制）。
- [ ] `_songs.txt` 里 `song` 名与 `music.asset` 的 `name` 一致。
- [ ] 改音频资源后重启；`logs/error.log` 搜 `sound` / `Failed to load`。

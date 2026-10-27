# dsh-hoi4-modding

**English** | [中文](#中文)

A DeepSeek Harness **skill bundle** for Hearts of Iron IV (HOI4) **1.19.3** modding. It registers one
skill, `hoi4-modding`, which turns the agent into a working HOI4 modder: create a mod from scratch,
write focus trees / events / decisions / ideas / characters / technologies / MIO / special projects /
scripted GUI, add localisation and DDS icons, run a static verifier, install into the game, and debug
`error.log`.

## Install

```sh
# from npm (market install does the same thing)
dsh plugin --profile web add dsh-hoi4-modding

# or straight from the source repo
dsh plugin --profile web add github:a1249070611/dsh-hoi4-modding
```

Restart / refresh as the host asks. The skill appears in the session skill catalog; invoke it by asking
for HOI4 modding, or explicitly “load hoi4-modding”.

npm: https://www.npmjs.com/package/dsh-hoi4-modding

## What is inside

| Path | Purpose |
|---|---|
| `skills/hoi4-modding/SKILL.md` | The skill body: rules, workflow, error-log triage, acceptance checklist |
| `skills/hoi4-modding/references/cheatsheet.md` | Copy-ready code for 15 common tasks |
| `skills/hoi4-modding/references/deep-dive.md` | Topic → deep-documentation index |
| `skills/hoi4-modding/scripts/new_mod.py` | Scaffold a runnable mod (optional focus tree; runs the linter) |
| `skills/hoi4-modding/scripts/hoi4_lint.py` | Static verifier: syntax, encoding/BOM, localisation, GFX, ID conflicts, `.mod` structure |
| `skills/hoi4-modding/scripts/install_mod.py` | Copy-install a mod into the player `mod/` directory and enable it |
| `skills/hoi4-modding/scripts/build_reference.py` | Generate effects/triggers/modifiers/console references from the game's `documentation/*.md` |
| `skills/hoi4-modding/scripts/dds_helper.py` | Generate / inspect HOI4 DDS icons (needs Pillow) |
| `skills/hoi4-modding/scripts/pdx_parser.py` | Tolerant PDX script parser used by the linter |
| `skills/hoi4-modding/references/tech-tree-ui.md` | Tech tree UI: folder availability, connection lines, big/small item layouts, split/merge recipes, debugging recipes |
| `skills/hoi4-modding/scripts/tech_tree_audit.py` | Audit a mod's tech pages: registry vs page/tab/item templates/gridboxes/techs/localisation |
| `skills/hoi4-modding/scripts/tech_folder_available.py` | Migrate `technology_folders.available` from `has_country_flag` to `original_tag` (check/apply/revert) |
| `skills/hoi4-modding/scripts/item_sprite_check.py` | Compare item template sizes with the actual item background sprite pixels ("small item looks big") |
| `skills/hoi4-modding/scripts/errorlog_triage.py` | Triage `error.log`: tech tree / textures / scopes / unknown fields / localisation |

## Requirements

- DeepSeek Harness with the skill registry (0.2.x).
- **Python 3.10+** for the bundled scripts (stdlib only; `dds_helper.py` needs `pip install pillow`).
- **HOI4 1.19.3** for the verifier's vanilla index, GFX and ID checks. Without the game the skill still
  works for scaffolding and code recipes; the game directory is auto-detected (`HOI4_GAME` /
  `HOI4_USER_DIR` override).
- No network access, no API keys, no game files are shipped.

## Permissions

The plugin registers skill metadata only. The bundled Python scripts are run by the agent **when the
user asks**; they read the HOI4 install and, for `install_mod.py`, write into the player
`Documents/Paradox Interactive/Hearts of Iron IV/mod/` directory (never the game install itself).
All commands are visible in the conversation before they run.

## License

## Publishing

Releases are published by GitHub Actions using npm **Trusted Publishing (OIDC)** — no `NPM_TOKEN`
secret and no bypass-2FA token are required:

1. npmjs.com → package `dsh-hoi4-modding` → Settings → **Trusted Publisher** → GitHub Actions
   (repository `a1249070611/dsh-hoi4-modding`, workflow file `release.yml`, "Allow npm publish").
2. Release: `npm version patch -m "release %s" && git push origin master --tags`.
   The `release.yml` workflow runs the tests and publishes with provenance.

The old granular-token flow (bypass-2FA token + `npm publish`) is deprecated by npm and stops working
in **January 2027**.

## Changelog

- **1.1.0** — Tech tree UI knowledge from a real large-mod debugging session: `technology_folders.available`
  must use `original_tag` (flag-based conditions silently drop every connection line on a page in new games),
  big/small item mixing requires the small item background **sprites** to point at real small textures,
  plus three debugging recipes (marker rename, half-split experiment, control probe) and four new scripts.
- 1.0.0 — Initial release.

## License

MIT. The skill text and scripts are original; no Paradox game assets are included.

---

## 中文

**DeepSeek Harness 的 HOI4 1.19.3 Mod 制作技能包。** 安装后注册一个名为 `hoi4-modding` 的技能：
从零建 Mod、写国策/事件/决议/理念/角色/科技/MIO/特殊项目/scripted GUI、本地化与 DDS 图标、
静态校验、安装进游戏、按 `error.log` 排错。

### 安装

```sh
dsh plugin --profile web add dsh-hoi4-modding
# 或从源码仓库：
dsh plugin --profile web add github:a1249070611/dsh-hoi4-modding
```

刷新/重启后，技能出现在技能目录；直接说「做个 HOI4 mod」「加个国策树」「mod 报错了」即可触发，
也可以显式说「加载 hoi4-modding 技能」。

### 本次新增（1.1.0）
- `references/tech-tree-ui.md`：科技树页面可用性 / 连线 / 大小框混排 / 拆页合并 / 三种调试手法（留痕法、对半分、对照探针）
- 4 个新脚本：`tech_tree_audit.py`（科技页完整性审计）、`tech_folder_available.py`（旗帜判定→国家标签，批量修复整页无连线）、
  `item_sprite_check.py`（模板尺寸 vs 背景精灵像素，专治"小框显示成大框"）、`errorlog_triage.py`（error.log 分诊）

### 发布方式（npm）
- 默认走 **GitHub Actions + Trusted Publishing (OIDC)**，不需要 `NPM_TOKEN`、也不需要 bypass-2FA token。
  在 npmjs.com 的包设置里把仓库 `a1249070611/dsh-hoi4-modding` 与 workflow `release.yml` 注册为 Trusted Publisher；
  发版只需 `npm version patch -m "release %s"`，然后 `git push origin master --tags`，CI 会自动测试并带 provenance 发布。
- 旧的 granular token 直发方式（勾选 Bypass 2FA 后 `npm publish`）已被 npm 弃用，**2027 年 1 月起失效**。

### 依赖

- DeepSeek Harness（含技能注册表，0.2.x）
- Python 3.10+（脚本仅标准库；DDS 工具需 Pillow）
- HOI4 1.19.3（校验器需要；游戏目录自动探测，可用 `HOI4_GAME` / `HOI4_USER_DIR` 覆盖）
- 不含任何游戏本体资源，不需要网络与 API Key

### 权限说明

插件只注册技能元数据；技能里的 Python 脚本由 agent 在你要求时执行：读取游戏安装目录，
`install_mod.py` 会把 Mod 复制到玩家 `Documents/Paradox Interactive/Hearts of Iron IV/mod/`
（不改游戏安装目录）。所有命令在对话中可见。

### 许可

MIT。技能文本与脚本为原创，不包含 Paradox 游戏素材。

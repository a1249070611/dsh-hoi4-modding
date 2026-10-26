# hoi4-modding 技能 —— 安装与共享说明

这是一个 **Agent Skill**：一个以 `SKILL.md`（YAML frontmatter + Markdown 指令）为入口、
可附带 `scripts/` 与 `references/` 的目录。它不绑定某个具体客户端，**复制目录即可迁移**。

## 目录要求

```
hoi4-modding/
├─ SKILL.md          # 必需：frontmatter 含 name、description
├─ references/       # 可选：参考资料（本技能为 cheatsheet.md、deep-dive.md）
├─ scripts/          # 可选：可执行工具（Python 3.10+，标准库；DDS 需 Pillow）
└─ INSTALL.md        # 本文件
```

## 安装到各平台

| 平台 | 放置位置 | 备注 |
|---|---|---|
| **DeepSeek Harness（本项目）** | `~/.agents/skills/hoi4-modding/` | 已安装；重开会话后出现在技能目录 |
| **Claude Code** | `~/.claude/skills/hoi4-modding/`（个人）或 `<项目>/.claude/skills/hoi4-modding/`（项目级） | 同样读 `SKILL.md` 的 `name`/`description` |
| **Claude.ai / 支持 Agent Skills 的客户端** | 按其「Skills / 技能」设置上传 zip 或目录 | zip 根目录必须是 `hoi4-modding/`，不要把 `SKILL.md` 放在 zip 顶层 |
| **其他兼容 Agent Skills 的工具** | 其 skills 目录或配置项 | 只要支持 `SKILL.md` + frontmatter 即可 |

Windows 下路径示例：

```powershell
# DeepSeek Harness
Copy-Item -Recurse .\hoi4-modding "$env:USERPROFILE\.agents\skills\hoi4-modding"

# Claude Code
Copy-Item -Recurse .\hoi4-modding "$env:USERPROFILE\.claude\skills\hoi4-modding"
```

Linux / macOS：

```bash
cp -r hoi4-modding ~/.agents/skills/          # DSH
cp -r hoi4-modding ~/.claude/skills/          # Claude Code
```

## 运行要求

- **Python 3.10+**（脚本仅用标准库；`dds_helper.py` 需要 `pip install pillow`）。
- **HOI4 1.19.3** 安装（用于 `hoi4_lint.py` 的原版索引与 GFX/本地化校验）。
  游戏目录自动探测；探测不到时设置：
  - `HOI4_GAME`：游戏根目录（含 `hoi4.exe`）
  - `HOI4_USER_DIR`：玩家数据目录（含 `mod/` 与 `logs/`）
- 首次运行 `hoi4_lint.py` 会在 `scripts/.cache/` 生成约 6–7 MB 的原版索引（可删除，会自动重建）。

```powershell
$env:HOI4_GAME = "D:\SteamLibrary\steamapps\common\Hearts of Iron IV"
$env:HOI4_USER_DIR = "$env:USERPROFILE\Documents\Paradox Interactive\Hearts of Iron IV"
```

> Linux 上用 Proton 运行 HOI4 时，玩家目录通常在
> `~/.steam/steam/steamapps/compatdata/394360/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Hearts of Iron IV`，
> 请显式设置 `HOI4_USER_DIR`。

## 自检

```powershell
$S = "<skills>/hoi4-modding/scripts"
& python "$S\new_mod.py" "$env:TEMP\DemoMod" --name "Demo" --prefix DM --tag LUX
& python "$S\hoi4_lint.py" "$env:TEMP\DemoMod"
```

预期：生成成功，`errors=0 warnings=0`。

## 共享边界

- 本技能**不包含任何游戏本体文件/贴图/文本**，只有原创笔记、脚本和代码片段；可自由分享。
- `references/deep-dive.md` 提到一个可选的本地知识库路径；不存在时技能仍可独立工作（以 cheatsheet 为准）。
- 游戏更新（如 1.20）后需要更新：`documentation/*.md` 结构、`reference/` 数据、以及本技能里的 1.19 差异条目。

## 更新方法

直接修改技能目录内的文件；若同时维护了知识库项目，修改后同步 `references/deep-dive.md` 的路径索引。

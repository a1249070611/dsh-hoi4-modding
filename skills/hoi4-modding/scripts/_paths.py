"""跨平台路径探测（HOI4 游戏目录 / 玩家数据目录）。

优先级：
  1. 环境变量 HOI4_GAME / HOI4_USER_DIR
  2. 各平台常见安装位置
  3. 返回 None（调用方自行决定回退或报错）

注意：Linux 上通过 Proton 运行的 HOI4，玩家数据通常在
`~/.steam/steam/steamapps/compatdata/394360/pfx/drive_c/users/steamuser/Documents/Paradox Interactive/Hearts of Iron IV`，
本模块只探测原生路径；Proton 用户请显式设置 HOI4_USER_DIR。
"""

from __future__ import annotations

import os
from pathlib import Path

STEAM_REL = Path("steamapps") / "common" / "Hearts of Iron IV"
USER_REL = Path("Paradox Interactive") / "Hearts of Iron IV"


def find_game_dir() -> Path | None:
    env = os.environ.get("HOI4_GAME")
    if env:
        p = Path(env).expanduser()
        if p.is_dir():
            return p

    home = Path.home()
    candidates: list[Path] = []
    if os.name == "nt":
        for drive in ("C:", "D:", "E:", "F:", "G:"):
            for base in ("Steam", "SteamLibrary", "Program Files (x86)/Steam", "Program Files/Steam"):
                candidates.append(Path(f"{drive}/{base}") / STEAM_REL)
    elif os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        candidates.append(home / "Library/Application Support/Steam" / STEAM_REL)
    else:
        candidates += [
            home / ".steam/steam" / STEAM_REL,
            home / ".local/share/Steam" / STEAM_REL,
        ]
    for p in candidates:
        if p.is_dir() and ((p / "hoi4.exe").exists() or (p / "hoi4").exists()):
            return p
    for p in candidates:
        if p.is_dir():
            return p
    return None


def find_user_dir() -> Path | None:
    env = os.environ.get("HOI4_USER_DIR")
    if env:
        return Path(env).expanduser()

    home = Path.home()
    candidates: list[Path] = []
    if os.name == "nt":
        candidates.append(home / "Documents" / USER_REL)
    elif os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        candidates.append(home / "Documents" / USER_REL)
    else:
        candidates += [
            home / ".local/share" / USER_REL,
            home / "Documents" / USER_REL,
        ]
    for p in candidates:
        if p.is_dir():
            return p
    return candidates[0] if candidates else None


if __name__ == "__main__":
    print("game:", find_game_dir())
    print("user:", find_user_dir())

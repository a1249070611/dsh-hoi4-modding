"""把工作区里的示例 Mod 安装到 HOI4 玩家数据目录，并可选写入 dlc_load.json 启用。

为什么需要它：游戏只扫描 `Documents/Paradox Interactive/Hearts of Iron IV/mod/`，
开发目录里的 Mod 必须「安装」（复制 or 建 .mod 指向开发目录）才能被启动器看到。

用法：
  # 预览（不写盘）
  python tools/install_mod.py example_mods/hello_hoi4 --dry-run

  # 安装为「目录副本」并启用
  python tools/install_mod.py example_mods/hello_hoi4 --yes --enable

  # 安装为「链接式」：只写 .mod，path 指向工作区（改代码不用重新安装）
  python tools/install_mod.py example_mods/hello_hoi4 --yes --link

  # 卸载
  python tools/install_mod.py example_mods/hello_hoi4 --uninstall --yes

注意：写入玩家数据目录不属于本工作区，可能需要你在终端里以正常权限运行；
DSH 沙箱下会被拒绝并提示，这属于预期行为。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

try:
    from _paths import find_user_dir
except Exception:  # 单独拷贝本文件时退化
    def find_user_dir():
        env = os.environ.get("HOI4_USER_DIR")
        return Path(env) if env else Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"

DEFAULT_USER_DIR = find_user_dir() or Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"


def read_descriptor(mod_dir: Path) -> str:
    descriptor = mod_dir / "descriptor.mod"
    if not descriptor.exists():
        raise SystemExit(f"找不到 {descriptor}，请确认这是 Mod 根目录")
    return descriptor.read_text(encoding="utf-8-sig")


def install(mod_dir: Path, user_dir: Path, link: bool, enable: bool, dry_run: bool, force: bool) -> int:
    mod_dir = mod_dir.resolve()
    name = mod_dir.name
    target = user_dir / "mod" / name
    mod_file = user_dir / "mod" / f"{name}.mod"
    descriptor = read_descriptor(mod_dir)

    if target.exists() and not force and not link:
        print(f"[!] 目标已存在：{target}（加 --force 覆盖）")
        return 2

    print(f"安装 Mod   : {name}")
    print(f"  源目录   : {mod_dir}")
    print(f"  目标目录 : {target if not link else '(链接式，不复制)'}")
    print(f"  描述文件 : {mod_file}")
    print(f"  启用     : {'是' if enable else '否'}")
    if dry_run:
        print("\n[dry-run] 未写入任何文件。")
        return 0

    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "mod").mkdir(parents=True, exist_ok=True)

    if not link:
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(mod_dir, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests/_scratch"))
        path_value = target
    else:
        path_value = mod_dir
        if any(ord(ch) > 127 for ch in str(mod_dir)):
            print("[!] 警告：--link 的 path 含非 ASCII 字符（如中文）。HOI4/启动器对非 ASCII 路径兼容性差，")
            print("    建议去掉 --link，用默认的复制安装（安装到玩家 mod 目录，路径为 ASCII）。")

    # .mod 文件：在 descriptor 基础上补 path（去掉可能存在的旧 path 行）
    lines = [ln for ln in descriptor.splitlines() if not ln.strip().startswith("path")]
    lines.append(f'path="{path_value.as_posix()}"')
    mod_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if enable:
        entry = f"mod/{name}.mod"
        dlc_load = user_dir / "dlc_load.json"
        data = {"enabled_mods": [], "disabled_dlcs": []}
        if dlc_load.exists():
            backup = dlc_load.with_suffix(".json.bak")
            shutil.copy2(dlc_load, backup)
            try:
                data = json.loads(dlc_load.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"[!] {dlc_load} 不是合法 JSON，已跳过启用")
                data = None
        if data is not None:
            enabled = data.get("enabled_mods", [])
            if entry not in enabled:
                enabled.append(entry)
            data["enabled_mods"] = enabled
            dlc_load.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"[+] 已启用：{entry}（原文件备份为 dlc_load.json.bak）")

    print("\n完成。重启游戏（或启动器）后在 playset 里确认 Mod 已勾选。")
    print("提示：改完代码若用 --link 模式，无需重新安装，直接重启游戏即可。")
    return 0


def uninstall(mod_dir: Path, user_dir: Path, dry_run: bool) -> int:
    name = mod_dir.resolve().name if mod_dir.exists() else mod_dir.name
    target = user_dir / "mod" / name
    mod_file = user_dir / "mod" / f"{name}.mod"
    dlc_load = user_dir / "dlc_load.json"

    print(f"卸载 Mod：{name}")
    if dry_run:
        print(f"  将删除 {target}（若存在）与 {mod_file}，并从 dlc_load.json 移除")
        return 0

    if target.exists():
        shutil.rmtree(target)
        print(f"  已删除 {target}")
    if mod_file.exists():
        mod_file.unlink()
        print(f"  已删除 {mod_file}")
    if dlc_load.exists():
        try:
            data = json.loads(dlc_load.read_text(encoding="utf-8"))
            entry = f"mod/{name}.mod"
            data["enabled_mods"] = [m for m in data.get("enabled_mods", []) if m != entry]
            dlc_load.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
            print("  已从 dlc_load.json 移除启用项")
        except json.JSONDecodeError:
            print(f"[!] {dlc_load} 解析失败，跳过")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="HOI4 Mod 安装/卸载工具")
    ap.add_argument("mod", type=Path, help="Mod 目录（含 descriptor.mod）")
    ap.add_argument("--user-dir", type=Path, default=DEFAULT_USER_DIR)
    ap.add_argument("--link", action="store_true", help="只写 .mod 并把 path 指向开发目录（不复制）")
    ap.add_argument("--enable", action="store_true", help="写入 dlc_load.json 启用")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true", help="确认执行写盘操作")
    ap.add_argument("--force", action="store_true", help="目标已存在时覆盖")
    args = ap.parse_args(argv)
    args.user_dir = args.user_dir.resolve()

    if args.uninstall:
        return uninstall(args.mod, args.user_dir, args.dry_run)
    if not args.dry_run and not args.yes:
        print("这会写入玩家数据目录，请加 --yes 确认，或先用 --dry-run 预览。")
        return 2
    return install(args.mod, args.user_dir, args.link, args.enable, args.dry_run, args.force)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PermissionError as exc:
        print(f"[权限不足] {exc}\n请在不启用 DSH 沙箱的终端中运行，或先把 Mod 目录手动复制到玩家 mod 目录。")
        raise SystemExit(3)

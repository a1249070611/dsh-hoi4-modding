"""从开源平台同步作者维护的知识库。

定位：知识库以作者维护的那份为准，不定期发布到开源平台。插件不打包知识库，
而是在需要时从远端拉取 → 本地缓存 → 建索引。

三个设计取舍：

1. **只同步知识，不同步原版索引。** 远端仓库放 markdown 笔记与参考文档（约 1 MB），
   不放 131 MB 的 kb.sqlite——那份是从游戏安装目录索引出来的派生物，换台机器重跑就有，
   而且绑死路径与行号。

2. **用 tarball 一次性下载，不依赖 git 客户端。** 用户机器上不一定装了 git。
   GitHub 的 `codeload` 地址可以直接拿 tar.gz；自建可用 mirror 覆盖。

3. **过期判断只看 manifest。** 每小时不必重新下载 1 MB，只需拉一个几百字节的
   manifest.json 比对 version 与 sha256。

网络不可用时回退到上次缓存，并把「这是旧数据」写进返回，不静默。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any

CONFIG_REL = os.path.join("knowledge", "remote.json")
CACHE_ROOT = os.path.join(os.path.expanduser("~"), ".kiant-hoi4-modkit", "remote")
TIMEOUT = 20
UA = {"User-Agent": "kiant-hoi4-modkit/3.1 (+local tool)"}


def config_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", CONFIG_REL))


def load_config() -> dict[str, Any] | None:
    p = config_path()
    if not os.path.isfile(p):
        return None
    try:
        cfg = json.load(open(p, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not (cfg.get("repo") or cfg.get("mirror")):
        return None
    return cfg


def cache_dir(cfg: dict[str, Any]) -> str:
    key = (cfg.get("repo") or cfg.get("mirror") or "remote").replace("/", "_").replace(":", "_")
    return os.path.join(CACHE_ROOT, key[-60:])


def state_path(cfg: dict[str, Any]) -> str:
    return os.path.join(cache_dir(cfg), ".sync-state.json")


def read_state(cfg: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.load(open(state_path(cfg), encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _get(url: str, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - 用户配置的地址
        return resp.read()


def _raw_url(cfg: dict[str, Any], rel: str) -> str:
    repo, branch = cfg["repo"], cfg.get("branch", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel.lstrip('/')}"


def _tarball_url(cfg: dict[str, Any]) -> str:
    if cfg.get("mirror"):
        return cfg["mirror"]
    repo, branch = cfg["repo"], cfg.get("branch", "main")
    return f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"


def fetch_manifest(cfg: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """返回 (manifest, error)。manifest 缺省时视为"仓库没提供版本信息"。"""
    rel = cfg.get("manifest", "manifest.json")
    try:
        if rel.startswith("file://"):
            data = open(rel[7:], "rb").read()
        elif os.path.isfile(rel):
            # 本地镜像或测试：manifest 直接给文件路径
            data = open(rel, "rb").read()
        elif rel.startswith(("http://", "https://")):
            data = _get(rel)
        else:
            data = _get(_raw_url(cfg, rel))
        return json.loads(data.decode("utf-8")), ""
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def status(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg if cfg is not None else load_config()
    if not cfg:
        return {
            "configured": False,
            "hint": "还没有配置远端知识库。编辑 knowledge/remote.json 填入 repo（如 owner/name）后，"
            "kiant_hoi4_kb_sync action=pull 会把作者维护的知识拉到本地。",
        }
    state = read_state(cfg)
    out: dict[str, Any] = {
        "configured": True,
        "repo": cfg.get("repo") or cfg.get("mirror"),
        "branch": cfg.get("branch", "main"),
        "paths": cfg.get("paths", ["knowledge/notes", "references"]),
        "cache_dir": cache_dir(cfg),
        "cached_files": sum(
            1
            for _b, _d, fs in os.walk(cache_dir(cfg))
            for f in fs
            if not f.startswith(".")
        ),
        "local_version": state.get("version") or None,
        "synced_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(state["synced_at"]))
        if state.get("synced_at")
        else None,
    }
    man, err = fetch_manifest(cfg)
    if man is None:
        out["remote_version"] = None
        out["remote_error"] = err
        out["stale"] = None
        out["note"] = "拿不到远端 manifest（离线或路径不对）。可以照用本地缓存，但无法判断是否过期。"
    else:
        out["remote_version"] = man.get("version")
        out["remote_error"] = ""
        out["stale"] = bool(man.get("version")) and man.get("version") != out["local_version"]
        out["remote_files"] = man.get("file_count")
        out["remote_built_at"] = man.get("built_at")
    return out


def pull(cfg: dict[str, Any] | None = None, force: bool = False) -> dict[str, Any]:
    """下载 → 解压到缓存 → 只保留 cfg['paths'] 里的目录 → 写 state。"""
    cfg = cfg if cfg is not None else load_config()
    if not cfg:
        return {"ok": False, "error": "未配置知识库仓库，先编辑 knowledge/remote.json"}

    st = status(cfg)
    if not force and st.get("stale") is False:
        return {"ok": True, "skipped": True, "message": "已是最新版本，未重新下载",
                "local_version": st.get("local_version")}

    url = _tarball_url(cfg)
    dest = cache_dir(cfg)
    tmp = tempfile.mkdtemp(prefix="modkit-remote-")
    try:
        if url.startswith("file://"):
            blob = open(url[7:], "rb").read()
        elif os.path.isfile(url):
            blob = open(url, "rb").read()
        else:
            blob = _get(url, timeout=max(TIMEOUT, 60))
    except (urllib.error.URLError, OSError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        state = read_state(cfg)
        if state:
            hint = "网络不可用。本地缓存仍在（版本 %s），检索继续用它，但内容可能是旧的。" % state.get("version")
        else:
            hint = "网络不可用，而且本地还没有任何缓存。检索会只剩原版索引；恢复网络后重跑一次 pull。"
        return {
            "ok": False,
            "error": f"下载失败：{type(exc).__name__}: {exc}",
            "used_cache": bool(state),
            "cached_version": state.get("version"),
            "hint": hint,
        }

    digest = hashlib.sha256(blob).hexdigest()
    tar_path = os.path.join(tmp, "kb.tar.gz")
    with open(tar_path, "wb") as fh:
        fh.write(blob)

    stage = os.path.join(tmp, "stage")
    os.makedirs(stage, exist_ok=True)
    try:
        with tarfile.open(tar_path, "r:gz") as tf:
            for member in tf.getmembers():
                # 解压时去掉顶层目录（GitHub tarball 的 owner-repo-sha/）
                parts = member.name.split("/", 1)
                if len(parts) < 2 or not parts[1]:
                    continue
                member.name = parts[1]
                if not (member.isfile() or member.isdir()):
                    continue
                if member.name.startswith("/") or ".." in member.name.split("/"):
                    continue
                tf.extract(member, stage, filter="data")
    except (tarfile.TarError, OSError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        return {"ok": False, "error": f"解压失败：{type(exc).__name__}: {exc}"}

    keep = cfg.get("paths") or ["knowledge/notes", "references"]
    # stage-then-switch：先把新内容装进 dest 旁边的暂存目录，确认有货之后
    # 再换装。之前直接 rmtree(dest) 再复制——paths 与仓库布局对不上时
    # copied 为 0、报错返回，而旧缓存已经删了，离线知识库凭空蒸发。
    staging = dest + ".staging"
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)
    copied = 0
    for rel in keep:
        src = os.path.join(stage, rel)
        if not os.path.isdir(src):
            continue
        for base, _d, files in os.walk(src):
            for f in files:
                if not f.endswith((".md", ".txt", ".json", ".csv")):
                    continue
                s = os.path.join(base, f)
                d = os.path.join(staging, os.path.relpath(s, stage))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                copied += 1
    shutil.rmtree(tmp, ignore_errors=True)

    if not copied:
        # 旧缓存原封不动，用户离线检索照常可用
        shutil.rmtree(staging, ignore_errors=True)
        return {
            "ok": False,
            "error": f"下载成功但 paths 里没有可索引的文件：{keep}",
            "hint": "检查 remote.json 的 paths 是否与仓库实际布局一致。旧缓存未动。",
        }

    # 换装：旧缓存先挪到 .old，staging 顶上；rename 失败（如目录被占用）则回滚
    old = dest + ".old"
    shutil.rmtree(old, ignore_errors=True)
    had_old = os.path.isdir(dest)
    if had_old:
        os.rename(dest, old)
    try:
        os.rename(staging, dest)
    except OSError:
        if had_old and not os.path.isdir(dest):
            os.rename(old, dest)  # 回滚，保住旧缓存
        shutil.rmtree(staging, ignore_errors=True)
        return {
            "ok": False,
            "error": "缓存目录换装失败（目录可能被占用），旧缓存已恢复。",
        }
    shutil.rmtree(old, ignore_errors=True)

    man, _err = fetch_manifest(cfg)
    state = {
        "version": (man or {}).get("version") or digest[:12],
        "sha256": digest,
        "synced_at": time.time(),
        "files": copied,
        "source": url,
    }
    with open(state_path(cfg), "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)

    return {
        "ok": True,
        "version": state["version"],
        "files": copied,
        "cache_dir": dest,
        "sha256": digest[:16],
        "next": "跑一次 kiant_hoi4_kb_build action=build，新增的源名为 remote。",
    }


def as_source(cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """把缓存目录包装成一个知识源；缓存不存在时返回 None。"""
    cfg = cfg if cfg is not None else load_config()
    if not cfg:
        return None
    d = cache_dir(cfg)
    if not os.path.isdir(d) or not any(f for _b, _d, f in os.walk(d)):
        return None
    return {"name": "remote", "path": d, "kind": "notes"}

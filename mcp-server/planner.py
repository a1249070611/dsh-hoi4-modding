"""Plan tracking for a mod project.

Two files, one source of truth:
  <mod>/.modkit/plan.json   machine-readable, drives `next`
  <mod>/ROADMAP.md          human-readable, survives in git history

The point is not project management theatre. It is that a long mod build has an
order that matters — scaffolding before content, localisation before preview,
validation before release — and a plan file keeps an agent from losing that order
across sessions.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

STATUS = ("pending", "active", "done", "blocked", "skipped")
ICON = {"pending": "[ ]", "active": "[~]", "done": "[x]", "blocked": "[!]", "skipped": "[-]"}


def _paths(mod_root: str) -> tuple[str, str]:
    base = os.path.join(mod_root, ".modkit")
    return os.path.join(base, "plan.json"), os.path.join(mod_root, "ROADMAP.md")


def _load(mod_root: str) -> dict:
    pj, _ = _paths(mod_root)
    if os.path.isfile(pj):
        try:
            return json.load(open(pj, "r", encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"mod": os.path.basename(mod_root), "created": _now(), "steps": []}


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def _save(mod_root: str, plan: dict) -> str:
    pj, rm = _paths(mod_root)
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    plan["updated"] = _now()
    with open(pj, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, ensure_ascii=False, indent=2)
    with open(rm, "w", encoding="utf-8") as fh:
        fh.write(_to_markdown(plan))
    return pj


def _to_markdown(plan: dict) -> str:
    steps = plan.get("steps", [])
    done = sum(1 for s in steps if s.get("status") == "done")
    total = len(steps)
    lines = [
        f"# {plan.get('mod', 'mod')} 开发计划",
        "",
        f"进度：{done}/{total}（{round(done / total * 100) if total else 0}%）"
        f" · 更新于 {plan.get('updated', '')}",
        "",
        "> 由 dsh-hoi4-modding 生成。改 plan.json 后重新生成即可，不要手改本文件的结构。",
        "",
    ]
    for step in steps:
        icon = ICON.get(step.get("status", "pending"), "[ ]")
        lines.append(f"- {icon} **{step['id']}** {step.get('title', '')}")
        if step.get("accept"):
            lines.append(f"    - 验收：{step['accept']}")
        if step.get("depends"):
            lines.append(f"    - 依赖：{', '.join(step['depends'])}")
        if step.get("note"):
            lines.append(f"    - 备注：{step['note']}")
    return "\n".join(lines) + "\n"


def _resolve_next(plan: dict) -> dict | None:
    done_ids = {s["id"] for s in plan.get("steps", []) if s.get("status") in {"done", "skipped"}}
    for step in plan.get("steps", []):
        if step.get("status") in {"done", "skipped", "blocked"}:
            continue
        if all(dep in done_ids for dep in step.get("depends", [])):
            return step
    return None


def _summary(plan: dict) -> dict:
    steps = plan.get("steps", [])
    counts: dict[str, int] = {}
    for step in steps:
        counts[step.get("status", "pending")] = counts.get(step.get("status", "pending"), 0) + 1
    total = len(steps)
    done = counts.get("done", 0)
    nxt = _resolve_next(plan)
    return {
        "mod": plan.get("mod"),
        "updated": plan.get("updated"),
        "progress": f"{done}/{total}",
        "percent": round(done / total * 100) if total else 0,
        "by_status": counts,
        "next": {"id": nxt["id"], "title": nxt.get("title"), "accept": nxt.get("accept")} if nxt else None,
        "steps": [
            {"id": s["id"], "title": s.get("title"), "status": s.get("status", "pending"),
             "depends": s.get("depends", [])}
            for s in steps
        ],
    }


DEFAULT_STEPS = [
    ("s1", "建立模组骨架", "descriptor.mod 与外层 .mod 齐全，启动器能看到 mod", []),
    ("s2", "定义核心设计", "写清国家/时间线/核心机制，落到 ROADMAP 备注", ["s1"]),
    ("s3", "实现内容", "国策/事件/决议/科技按设计落地", ["s2"]),
    ("s4", "补齐本地化", "英文与中文都无缺键、无乱码", ["s3"]),
    ("s5", "静态校验清零", "kiant_hoi4_validate_mod deep 模式 0 error", ["s4"]),
    ("s6", "游戏内验证", "error.log 无新增错误，关键内容实际可达", ["s5"]),
    ("s7", "兼容性评估", "覆盖范围清晰，无 replace_path，加载顺序已注明", ["s6"]),
    ("s8", "打包发布", "版本号、工坊缩略图、更新日志齐备", ["s7"]),
]


def plan_action(
    mod_root: str,
    action: str = "status",
    steps: list | None = None,
    step_id: str = "",
    status: str = "",
    title: str = "",
    note: str = "",
) -> dict[str, Any]:
    mod_root = os.path.abspath(mod_root)
    plan = _load(mod_root)

    if action == "init":
        if plan.get("steps") and not steps:
            return {"ok": False, "message": "计划已存在，改用 action=status 查看或 action=reset 重建"}
        items = steps or DEFAULT_STEPS
        plan["steps"] = []
        for idx, item in enumerate(items, 1):
            if isinstance(item, (tuple, list)) and len(item) == 4:
                sid, title_, accept, depends = item
                plan["steps"].append(
                    {"id": sid, "title": title_, "status": "pending",
                     "depends": list(depends), "accept": accept, "note": ""}
                )
            elif isinstance(item, str):
                plan["steps"].append(
                    {"id": f"s{idx}", "title": item, "status": "pending", "depends": [],
                     "accept": "", "note": ""}
                )
            else:
                plan["steps"].append(
                    {
                        "id": item.get("id") or f"s{idx}",
                        "title": item.get("title", ""),
                        "status": item.get("status", "pending"),
                        "depends": item.get("depends", []),
                        "accept": item.get("accept", ""),
                        "note": item.get("note", ""),
                    }
                )
        plan["created"] = plan.get("created") or _now()
        path = _save(mod_root, plan)
        out = _summary(plan)
        out.update({"ok": True, "plan_file": path, "roadmap": _paths(mod_root)[1]})
        return out

    if action == "reset":
        plan = {"mod": os.path.basename(mod_root), "created": _now(), "steps": []}
        path = _save(mod_root, plan)
        return {"ok": True, "message": "已清空计划", "plan_file": path}

    if action == "add":
        if not title:
            return {"ok": False, "message": "action=add 需要 title"}
        new_id = step_id or f"s{len(plan.get('steps', [])) + 1}"
        plan.setdefault("steps", []).append(
            {"id": new_id, "title": title, "status": status or "pending",
             "depends": [], "accept": "", "note": note}
        )
        _save(mod_root, plan)
        return {"ok": True, "added": new_id, **_summary(plan)}

    if action == "update":
        if not step_id:
            return {"ok": False, "message": "action=update 需要 step_id"}
        if status and status not in STATUS:
            return {"ok": False, "message": f"status 只能是 {STATUS}"}
        for step in plan.get("steps", []):
            if step["id"] == step_id:
                if status:
                    step["status"] = status
                if note:
                    step["note"] = note
                if title:
                    step["title"] = title
                _save(mod_root, plan)
                return {"ok": True, "updated": step_id, **_summary(plan)}
        return {"ok": False, "message": f"没有步骤 {step_id}"}

    # status (default)
    if not plan.get("steps"):
        return {
            "ok": False,
            "message": "还没有计划。用 action=init 生成默认八阶段，或传 steps 自定义。",
            "default_steps": [{"id": i, "title": t, "accept": a, "depends": d} for i, t, a, d in DEFAULT_STEPS],
        }
    return {"ok": True, **_summary(plan)}

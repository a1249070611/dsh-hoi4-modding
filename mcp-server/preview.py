"""Static HTML preview of a mod, no game process involved.

Renders focus trees with real coordinates and prerequisite edges, plus cards for
events / decisions / ideas with localisation already resolved. The output is one
self-contained file: no CDN, no assets, no JS framework — double-click and look.
"""

from __future__ import annotations

import html
import os
import time
from typing import Any

COL_W = 208
ROW_H = 116
NODE_W = 176
NODE_H = 84
PAD = 48

SEV_COLOR = {"error": "#c0392b", "warn": "#b8860b", "info": "#2c6fa8"}


def _esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _loc(loc: dict, key: str, fallback: str = "") -> str:
    if key in loc:
        return loc[key]
    return fallback or key


# --------------------------------------------------------------------------- #
# Focus trees
# --------------------------------------------------------------------------- #

def resolve_positions(focuses: list[dict]) -> dict[str, tuple[int, int]]:
    """把每个国策的 (x, y) 还原成绝对格子坐标。

    这里的关键是 relative_position_id：它的意思是「我的 x/y 是相对某个锚点的偏移」，
    不是绝对坐标。原版 10625 个国策里有 10984 处用它（103%，超过 100% 是有跨文件
    引用别国国策当锚点的情况），德国、日本这些大树的覆盖率是 100%。

    只读 x/y 直接画会怎样：整棵树的节点仍然各自「有位置」，但行列关系全乱——
    因为一个 x=6 的节点可能是「绝对第 6 列」，也可能是「锚点右边 6 格」，
    两者差着整个锚点的偏移量。表现出来就是节点重叠、连线横穿。

    递归解算，带环检测：mod 里 anchor 互相引用（A 相对 B、B 相对 A）是常见手误，
    不设防会无限递归直接爆栈。
    """
    raw: dict[str, dict] = {}
    for f in focuses:
        fid = f.get("id")
        if fid:
            raw[fid] = f

    memo: dict[str, tuple[int, int]] = {}

    def resolve(fid: str, trail: frozenset[str]) -> tuple[int, int]:
        if fid in memo:
            return memo[fid]
        f = raw.get(fid)
        if f is None:
            return (0, 0)
        x, y = _int(f.get("x")), _int(f.get("y"))
        anchor = f.get("rel") or ""
        # 自引用 / 环：就地当绝对坐标处理，不递归。
        if anchor and anchor != fid and anchor not in trail:
            ax, ay = resolve(anchor, trail | {fid})
            x, y = ax + x, ay + y
        memo[fid] = (x, y)
        return (x, y)

    return {fid: resolve(fid, frozenset()) for fid in raw}


def _render_focus(focuses: list[dict], loc: dict) -> str:
    usable = [f for f in focuses if f.get("id") and not f.get("shared")]
    if not usable:
        return '<p class="empty">没有国策定义。用 <code>kiant_hoi4_scaffold</code> kind=focus 生成一个。</p>'

    # 解算必须用**全集**（含 shared_focus）：shared_focus 就是给整棵树当公共
    # 锚点设计的（原版大树的主流用法）。之前在这里先过滤再解算，锚定到
    # shared 的国策查不到锚点、全部按 (0,0) 起算，一整片节点挤在画布左上角。
    # 渲染时才把 shared 排除（它自己不画）。
    placed = resolve_positions(focuses)
    xs = [p[0] for p in placed.values()]
    ys = [p[1] for p in placed.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = PAD * 2 + (max_x - min_x) * COL_W + NODE_W
    height = PAD * 2 + (max_y - min_y) * ROW_H + NODE_H

    pos: dict[str, tuple[int, int]] = {}
    for fid, (gx, gy) in placed.items():
        px = PAD + (gx - min_x) * COL_W
        py = PAD + (gy - min_y) * ROW_H
        pos[fid] = (px, py)

    edges: list[str] = []
    for f in usable:
        for prereq in f.get("prereq") or []:
            if prereq not in pos:
                continue
            x1, y1 = pos[prereq]
            x2, y2 = pos[f["id"]]
            ax, ay = x1 + NODE_W // 2, y1 + NODE_H
            bx, by = x2 + NODE_W // 2, y2
            mid = (ay + by) // 2
            edges.append(
                f'<path d="M{ax},{ay} C{ax},{mid} {bx},{mid} {bx},{by}" '
                f'fill="none" stroke="#9aa8b8" stroke-width="2"/>'
            )

    nodes: list[str] = []
    for f in usable:
        x, y = pos[f["id"]]
        title = _loc(loc, f["id"], f["id"])
        desc = loc.get(f"{f['id']}_desc", "")
        missing = f["id"] not in loc
        cls = "node missing" if missing else "node"
        nodes.append(
            f'<div class="{cls}" style="left:{x}px;top:{y}px" title="{_esc(desc[:200])}">'
            f'<div class="nid">{_esc(f["id"])}</div>'
            f'<div class="ntitle">{_esc(title)}</div>'
            f"</div>"
        )

    legend = (
        '<div class="legend">'
        f'<span><i class="sw" style="background:#4a6fa5"></i>国策 {len(usable)} 个</span>'
        f'<span><i class="sw" style="background:#c0392b"></i>缺本地化 '
        f'{sum(1 for f in usable if f["id"] not in loc)} 个</span>'
        '<span class="dim">坐标按 x/y 等比还原，缩放比例非游戏内原尺寸</span>'
        "</div>"
    )

    return (
        legend
        + f'<div class="tree" style="width:{width}px;height:{height}px">'
        + f'<svg class="edges" width="{width}" height="{height}">' + "".join(edges) + "</svg>"
        + "".join(nodes)
        + "</div>"
    )


# --------------------------------------------------------------------------- #
# Cards
# --------------------------------------------------------------------------- #

def _render_events(events: list[dict], loc: dict) -> str:
    if not events:
        return '<p class="empty">没有事件。</p>'
    out = ['<div class="cards">']
    for ev in events:
        eid = ev.get("id", "")
        title = _loc(loc, ev.get("title") or f"{eid}.t", eid)
        desc = _loc(loc, ev.get("desc") or f"{eid}.d", "")
        opts = ev.get("options") or []
        opt_html = "".join(
            f'<li>{_esc(_loc(loc, o, o))}</li>' for o in opts
        ) or '<li class="dim">无显式选项（回退到 id.a/id.b）</li>'
        out.append(
            '<article class="card">'
            f'<header><code>{_esc(eid)}</code></header>'
            f'<h3>{_esc(title)}</h3>'
            f'<p>{_esc(desc[:400])}</p>'
            f'<ul class="opts">{opt_html}</ul>'
            f'<footer>{_esc(ev.get("file", ""))}:{_esc(ev.get("line", ""))}</footer>'
            "</article>"
        )
    out.append("</div>")
    return "".join(out)


def _render_decisions(decisions: list[dict], categories: list[dict], loc: dict) -> str:
    if not decisions:
        return '<p class="empty">没有决议。</p>'
    by_cat: dict[str, list[dict]] = {}
    for dec in decisions:
        by_cat.setdefault(dec.get("category", "未分类"), []).append(dec)
    cat_names = {c["id"]: c for c in categories}
    out: list[str] = []
    for cat, items in by_cat.items():
        cat_title = _loc(loc, cat, cat)
        out.append(f'<section class="group"><h3>{_esc(cat_title)} <code>{_esc(cat)}</code></h3><div class="cards">')
        for dec in items:
            did = dec.get("id", "")
            out.append(
                '<article class="card narrow">'
                f'<header><code>{_esc(did)}</code></header>'
                f'<h4>{_esc(_loc(loc, did, did))}</h4>'
                f'<p>{_esc(loc.get(f"{did}_desc", "")[:300])}</p>'
                f'<footer>{_esc(dec.get("file", ""))}:{_esc(dec.get("line", ""))}</footer>'
                "</article>"
            )
        out.append("</div></section>")
    return "".join(out)


def _render_ideas(ideas: list[dict], loc: dict) -> str:
    if not ideas:
        return '<p class="empty">没有国家精神。</p>'
    out = ['<table class="tbl"><thead><tr><th>ID</th><th>名称</th><th>说明</th><th>槽位</th></tr></thead><tbody>']
    for idea in ideas:
        iid = idea.get("id", "")
        out.append(
            "<tr>"
            f"<td><code>{_esc(iid)}</code></td>"
            f"<td>{_esc(_loc(loc, iid, iid))}</td>"
            f"<td>{_esc(loc.get(f'{iid}_desc', '')[:160])}</td>"
            f"<td>{_esc(idea.get('slot', ''))}</td>"
            "</tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def _render_defs_table(kind: str, items: list[dict]) -> str:
    if not items:
        return ""
    rows = "".join(
        f"<tr><td><code>{_esc(i.get('id', ''))}</code></td>"
        f"<td>{_esc(i.get('file', ''))}:{_esc(i.get('line', ''))}</td></tr>"
        for i in items
    )
    return (
        f"<details><summary>{_esc(kind)}（{len(items)}）</summary>"
        f'<table class="tbl"><tbody>{rows}</tbody></table></details>'
    )


def _render_issues(issues: list[dict]) -> str:
    if not issues:
        return '<p class="ok">没有发现结构性问题。</p>'
    out = ['<table class="tbl issues"><thead><tr><th>级别</th><th>位置</th><th>问题</th><th>建议</th></tr></thead><tbody>']
    for i in issues:
        sev = i.get("level", "info")
        where = i.get("file") or ""
        if i.get("line"):
            where += f":{i['line']}"
        out.append(
            "<tr>"
            f'<td><span class="sev" style="background:{SEV_COLOR.get(sev, "#666")}">{_esc(sev)}</span></td>'
            f"<td class=\"mono\">{_esc(where or i.get('kind', ''))}</td>"
            f"<td>{_esc(i.get('message', ''))}</td>"
            f"<td class=\"dim\">{_esc(i.get('hint', ''))}</td>"
            "</tr>"
        )
    out.append("</tbody></table>")
    return "".join(out)


def _render_coverage(defs: dict, loc: dict) -> str:
    rows: list[str] = []
    for kind, items in sorted(defs.items()):
        if not isinstance(items, list):
            continue
        need = 0
        have = 0
        for item in items:
            ident = item.get("id") or ""
            if not ident:
                continue
            keys = [ident]
            if kind in {"focus", "idea", "decision", "decision_category"}:
                keys.append(f"{ident}_desc")
            for key in keys:
                need += 1
                if key in loc:
                    have += 1
        pct = round(have / need * 100) if need else 100
        rows.append(
            f"<tr><td>{_esc(kind)}</td><td>{len(items)}</td>"
            f"<td>{have}/{need}</td>"
            f'<td><div class="bar"><span style="width:{pct}%"></span></div>{pct}%</td></tr>'
        )
    return (
        '<table class="tbl"><thead><tr><th>类型</th><th>数量</th><th>本地化覆盖</th><th></th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


CSS = """
*{box-sizing:border-box}
body{margin:0;font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
     color:#1c2733;background:#f5f7fa}
header.top{background:#fff;border-bottom:1px solid #dde3ea;padding:20px 28px}
header.top h1{margin:0 0 4px;font-size:20px;letter-spacing:.2px}
header.top .meta{color:#5b6b7c;font-size:13px}
.wrap{padding:0 28px 60px}
nav{position:sticky;top:0;background:#f5f7fa;padding:14px 0 10px;z-index:5;
    border-bottom:1px solid #e3e8ee;margin-bottom:18px}
nav a{display:inline-block;padding:6px 14px;margin-right:6px;border-radius:6px;
      color:#33475b;text-decoration:none;background:#e9eef4;font-size:13px}
nav a:hover{background:#d9e2ec}
h2{font-size:16px;margin:28px 0 12px;padding-bottom:6px;border-bottom:1px solid #e3e8ee}
.cards{display:flex;flex-wrap:wrap;gap:12px}
.card{background:#fff;border:1px solid #e1e7ee;border-radius:8px;padding:14px 16px;
      width:340px;box-shadow:0 1px 2px rgba(20,40,70,.04)}
.card.narrow{width:280px}
.card header code{font-size:11px;color:#7b8a99}
.card h3{margin:6px 0 8px;font-size:15px}
.card h4{margin:6px 0;font-size:14px}
.card p{margin:0 0 8px;color:#48596b;font-size:13px}
.card footer{margin-top:8px;font-size:11px;color:#93a1af;font-family:ui-monospace,monospace}
.opts{margin:0;padding-left:18px;font-size:12px;color:#33475b}
.empty{color:#8497a8;font-style:italic}
.ok{color:#1f7a4d}
.dim{color:#8497a8;font-size:12px}
.tree{position:relative;margin:14px 0;background:#fff;border:1px solid #e1e7ee;
      border-radius:8px;overflow:auto}
.edges{position:absolute;left:0;top:0;pointer-events:none}
.node{position:absolute;width:176px;height:84px;background:#eef3f9;border:1px solid #b9c7d6;
      border-radius:6px;padding:8px 10px;overflow:hidden}
.node.missing{background:#fdf0ee;border-color:#e0a49c}
.nid{font:10px ui-monospace,monospace;color:#7b8a99;white-space:nowrap;overflow:hidden;
     text-overflow:ellipsis}
.ntitle{font-size:13px;font-weight:600;margin-top:6px;color:#1c2733;
        display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.legend{display:flex;gap:18px;align-items:center;font-size:12px;color:#5b6b7c;margin-top:8px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}
.tbl{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e1e7ee;
     border-radius:8px;overflow:hidden;font-size:13px}
.tbl th{background:#eef3f9;text-align:left;padding:9px 12px;font-weight:600;color:#33475b}
.tbl td{padding:8px 12px;border-top:1px solid #eef1f5;vertical-align:top}
.tbl tr:hover td{background:#fafcfe}
.mono,.tbl code{font-family:ui-monospace,Consolas,monospace;font-size:12px}
.sev{color:#fff;padding:1px 7px;border-radius:10px;font-size:11px}
.bar{display:inline-block;width:70px;height:7px;background:#e6ecf3;border-radius:4px;
     vertical-align:middle;margin-right:8px;overflow:hidden}
.bar span{display:block;height:100%;background:#4a6fa5}
details{margin:8px 0}
summary{cursor:pointer;color:#33475b;font-size:13px;padding:4px 0}
.group{margin-bottom:18px}
.group h3{font-size:14px;color:#33475b;margin:14px 0 8px}
code{background:#eef3f9;padding:1px 5px;border-radius:3px;font-size:12px}
"""


def render(
    mod_root: str,
    out_path: str,
    name: str,
    version: str,
    definitions: dict,
    loc: dict,
    issues: list[dict],
    stats: dict | None = None,
) -> dict[str, Any]:
    started = time.time()
    sections = {
        "focus": _render_focus(definitions.get("focus", []), loc),
        "events": _render_events(definitions.get("event", []), loc),
        "decisions": _render_decisions(
            definitions.get("decision", []),
            definitions.get("decision_category", []),
            loc,
        ),
        "ideas": _render_ideas(definitions.get("idea", []), loc),
        "coverage": _render_coverage(definitions, loc),
        "issues": _render_issues(issues),
    }

    extras = "".join(
        _render_defs_table(kind, items)
        for kind, items in sorted(definitions.items())
        if kind
        not in {"focus", "event", "decision", "decision_category", "idea"}
        and isinstance(items, list)
    )

    counts = {
        "error": sum(1 for i in issues if i.get("level") == "error"),
        "warn": sum(1 for i in issues if i.get("level") == "warn"),
    }

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(name)} · 离线预览</title>
<style>{CSS}</style></head><body>
<header class="top">
  <h1>{_esc(name)}</h1>
  <div class="meta">
    版本 {_esc(version)} · 生成于 {time.strftime("%Y-%m-%d %H:%M")} ·
    错误 <b style="color:#c0392b">{counts["error"]}</b> ·
    警告 <b style="color:#b8860b">{counts["warn"]}</b>
    {f" · 文件 {stats['files']}" if stats and stats.get("files") else ""}
  </div>
</header>
<div class="wrap">
<nav>
  <a href="#focus">国策树</a>
  <a href="#events">事件</a>
  <a href="#decisions">决议</a>
  <a href="#ideas">国家精神</a>
  <a href="#coverage">本地化覆盖</a>
  <a href="#issues">问题清单</a>
  <a href="#more">其它定义</a>
</nav>

<h2 id="focus">国策树</h2>
{sections["focus"]}

<h2 id="events">事件</h2>
{sections["events"]}

<h2 id="decisions">决议</h2>
{sections["decisions"]}

<h2 id="ideas">国家精神</h2>
{sections["ideas"]}

<h2 id="coverage">本地化覆盖</h2>
{sections["coverage"]}

<h2 id="issues">问题清单</h2>
{sections["issues"]}

<h2 id="more">其它定义</h2>
{extras or '<p class="empty">无</p>'}

<p class="dim" style="margin-top:36px">
  这是一个静态快照，不反映运行时行为（AI、触发条件求值、平衡性）。界面外观与游戏内不完全一致。
</p>
</div></body></html>"""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return {
        "ok": True,
        "path": out_path,
        "bytes": len(doc.encode("utf-8")),
        "sections": {k: (len(v) > 60) for k, v in sections.items()},
        "seconds": round(time.time() - started, 3),
        "note": "双击打开即可，无需游戏与网络。",
    }

#!/usr/bin/env python3
"""Error book & solution pool retrieval.

Two reference directories, two different jobs:

    91_error-book/   already-verified answers   ("I hit this, here's the fix")
    92_solutions/    unverified ideas           ("maybe try this, no idea if it works")

The difference matters at retrieval time, so it is kept in the data model:
error entries carry symptom_class + severity, solution entries carry a status
that decides how much trust to extend.

Why an in-memory scan instead of the SQLite knowledge base: you reach for the
error book *while something is broken*, which is exactly when you least want to
depend on having built an index. Thirty-odd small files read in ~5ms, so just
read them.
"""

from __future__ import annotations

import os
import re
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCES = os.path.join(os.path.dirname(HERE), "references")

KINDS: dict[str, dict[str, str]] = {
    "error": {
        "dir": "91_error-book",
        "prefix": "EB",
        "noun": "错题本",
        "trust": "已实证，可直接照做",
    },
    "solution": {
        "dir": "92_solutions",
        "prefix": "SOL",
        "noun": "方案库",
        "trust": "未验证，必须自己确认前提成立",
    },
}

# Section weights: what a modder types is a symptom, so symptoms outrank prose.
SECTION_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("title", 6.0),
    ("症状", 5.0),
    ("错误做法", 2.0),
    ("根因", 3.0),
    ("标准化方案", 3.0),
    ("预防", 1.0),
    ("验证", 1.0),
)

_ID_RE = re.compile(r"\b(EB|SOL)-(\d{3})\b", re.I)
_CJK = re.compile(r"[\u4e00-\u9fff]")
_SPLIT = re.compile(r"[\s,，、/|()（）\[\]{}<>《》:：;；!！?？\"'“”‘’·]+")


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def _read(path: str) -> str:
    try:
        # utf-8-sig：Windows 记事本保存的条目带 BOM，不剥的话 front matter
        # 的开头判断（text.startswith("---")）恒 False，id/status 全部丢失，
        # lint 还会跟着报一堆假问题。sig 对无 BOM 文件行为不变。
        with open(path, "r", encoding="utf-8-sig") as fh:
            return fh.read()
    except Exception:
        return ""


def _front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end]
    body = text[end + 4 :]
    meta: dict[str, Any] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key.strip()] = [v.strip() for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = val.strip("'\"")
    return meta, body


def _sections(body: str) -> dict[str, str]:
    """Split on '## ' headings. Preamble lands under 'title', minus the H1 line
    that merely repeats the filename."""
    out: dict[str, str] = {}
    current = "title"
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if buf:
                out[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        elif not (current == "title" and line.startswith("# ")):
            buf.append(line)
    if buf:
        out[current] = "\n".join(buf).strip()
    return out


def _load(kind: str) -> list[dict[str, Any]]:
    spec = KINDS[kind]
    folder = os.path.join(REFERENCES, spec["dir"])
    if not os.path.isdir(folder):
        return []
    items: list[dict[str, Any]] = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        path = os.path.join(folder, name)
        text = _read(path)
        meta, body = _front_matter(text)
        secs = _sections(body)
        stem = name[:-3]
        eid = str(meta.get("id") or stem.split("-")[0] + "-" + (stem.split("-")[1] if "-" in stem else ""))
        if not _ID_RE.search(eid):
            eid = stem
        title = str(meta.get("title") or "")
        if not title:
            for line in body.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
        title = re.sub(r"^(EB|SOL)-\d{3}\s*", "", title).strip() or stem
        items.append(
            {
                "id": eid.upper(),
                "title": title,
                "file": name,
                "abspath": path,
                "path": os.path.relpath(path, os.path.dirname(REFERENCES)).replace("\\", "/"),
                "symptom_class": str(meta.get("symptom_class") or ""),
                "severity": str(meta.get("severity") or ""),
                "status": str(meta.get("status") or ""),
                "source": str(meta.get("source") or ""),
                "verified_on": str(meta.get("verified_on") or ""),
                "related": meta.get("related") if isinstance(meta.get("related"), list) else [],
                "meta": meta,
                "sections": secs,
                "body": body,
            }
        )
    return items


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #

def _terms(query: str) -> list[tuple[str, float, int]]:
    """Split into (gram, weight, group) triples, grouped by the whitespace token
    they came from.

    A Chinese phrase rarely appears verbatim, so each CJK token also emits its
    2-grams tagged with the same group id. Scoring then asks, per group, "how
    much of this word did we find?" — a single stray 2-gram is a fragment, two
    or more means the phrase is really there.
    """
    out: list[tuple[str, float, int]] = []
    for gi, raw in enumerate(_SPLIT.split(query or "")):
        t = raw.strip().lower()
        if not t:
            continue
        out.append((t, 1.0, gi))
        if _CJK.search(t) and len(t) > 3:
            grams = {t[i : i + 2] for i in range(len(t) - 1)}
            for g in sorted(grams):
                out.append((g, 0.4, gi))
    return out


def _count(hay: str, term: str) -> int:
    if not hay or not term:
        return 0
    hay = hay.lower()
    if _CJK.search(term):
        return hay.count(term)
    # ASCII terms: require word-ish boundary so 'loc' does not match 'local'
    return len(re.findall(r"(?<![a-z0-9_])" + re.escape(term) + r"(?![a-z0-9_])", hay))


def _score(item: dict[str, Any], terms: list[tuple[str, float, int]]) -> tuple[float, list[str], int]:
    """Returns (score, why, groups_found).

    `groups_found` decides relevance, and the rule is a *coverage ratio* rather
    than a fixed count: a long Chinese phrase never appears verbatim, so for
    each whitespace token we ask what share of its 2-grams landed here. Two of
    six grams is coincidence (「坦克设计器槽位」reaching an icon-sizing entry via
    「坦克」+「槽位」); five of six means the phrase is really there.
    """
    secs = item["sections"]
    fields: list[tuple[str, str, float]] = [("标题", item["title"], SECTION_WEIGHTS[0][1])]
    for heading, weight in SECTION_WEIGHTS[1:]:
        if heading in secs:
            fields.append((heading, secs[heading], weight))
    other = "\n".join(v for k, v in secs.items() if k not in {h for h, _ in SECTION_WEIGHTS[1:]})
    if other:
        fields.append(("正文", other, 1.0))

    total = 0.0
    per_group: dict[int, dict[str, Any]] = {}
    for term, tweight, gi in terms:
        if not term:
            continue
        hit_fields: list[str] = []
        for label, text, weight in fields:
            n = _count(text, term)
            if n:
                total += weight * min(n, 3) * tweight
                hit_fields.append(label)

        g = per_group.setdefault(
            gi, {"token": "", "whole": False, "grams": 0, "total": 0, "fields": [], "hits": []}
        )
        if tweight >= 1.0:
            g["token"] = term
            g["whole"] = bool(hit_fields)
        else:
            g["total"] += 1
            if hit_fields:
                g["grams"] += 1
                g["hits"].append(term)
        for f in hit_fields:
            if f not in g["fields"]:
                g["fields"].append(f)

    MIN_GRAMS = 2
    MIN_COVERAGE = 0.5

    why: list[str] = []
    groups_found = 0
    for gi in sorted(per_group):
        g = per_group[gi]
        coverage = (g["grams"] / g["total"]) if g["total"] else 0.0
        if not (g["whole"] or (g["grams"] >= MIN_GRAMS and coverage >= MIN_COVERAGE)):
            continue
        groups_found += 1
        # Never label a fragment match with the full phrase — that reads as
        # "the whole thing matched" when only pieces did.
        if g["whole"]:
            label = g["token"]
        else:
            label = f"片段 {int(coverage * 100)}% " + "/".join(g["hits"][:3])
        why.append(f"{label} → {'/'.join(g['fields'][:3])}")

    # exact id mention is decisive
    for term, _w, _gi in terms:
        if _ID_RE.fullmatch(term.upper()) and term.upper() == item["id"]:
            total += 100.0
            groups_found += 1
            why.insert(0, f"ID 精确命中 {term.upper()}")
            break
    return total, why[:5], groups_found


def _snippet(item: dict[str, Any], terms: list[tuple[str, float, int]], width: int = 150) -> str:
    secs = item["sections"]
    best, best_hits, best_label = "", 0, ""
    for label, text in secs.items():
        if not text:
            continue
        hits = sum(_count(text, t) for t, _w, _g in terms if t)
        if hits > best_hits:
            best, best_hits, best_label = text, hits, label
    if not best:
        best = item["body"]
        best_label = "正文"
    flat = _flatten(best)
    low = flat.lower()
    pos = 0
    for term, _w, _g in terms:
        if not term:
            continue
        p = low.find(term)
        if p >= 0:
            pos = max(0, p - width // 3)
            break
    out = flat[pos : pos + width]
    if pos > 0:
        out = "…" + out
    if pos + width < len(flat):
        out += "…"
    return f"[{best_label}] {out}" if best_label not in ("正文", "title") else out


def _flatten(text: str) -> str:
    """Strip the markdown scaffolding that makes a snippet unreadable: fenced
    blocks, headings, table pipes, emphasis markers."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    keep: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("---"):
            continue
        if s.startswith("|"):
            # table rows: keep the cells, drop the separator rows
            if set(s) <= set("|-: "):
                continue
            s = " · ".join(c.strip() for c in s.strip("|").split("|") if c.strip())
        s = re.sub(r"^[-*+]\s+", "", s)
        s = re.sub(r"^>\s*", "", s)
        keep.append(s)
    out = " ".join(keep)
    out = re.sub(r"\*\*(.+?)\*\*", r"\1", out)
    out = re.sub(r"`([^`]*)`", r"\1", out)
    return re.sub(r"\s+", " ", out).strip()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def _preview(item: dict[str, Any], terms: list[tuple[str, float]], score: float, why: list[str]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": item["id"],
        "title": item["title"],
        "file": item["path"],
    }
    if item["symptom_class"]:
        row["symptom_class"] = item["symptom_class"]
    if item["severity"]:
        row["severity"] = item["severity"]
    if item["status"]:
        row["status"] = item["status"]
    if item["source"]:
        row["source"] = item["source"]
    row["snippet"] = _snippet(item, terms) if terms else _headline(item)
    if why:
        row["matched"] = why
    if score:
        row["score"] = round(score, 1)
    return row


def _headline(item: dict[str, Any], width: int = 150) -> str:
    """No query → lead with the symptom, which is what the reader wants first."""
    for label in ("症状", "它想解决什么", "title"):
        text = item["sections"].get(label, "")
        if text:
            flat = _flatten(text)
            if flat:
                return f"[{label}] {flat[:width]}{'…' if len(flat) > width else ''}"
    flat = _flatten(item["body"])
    return flat[:width] + ("…" if len(flat) > width else "")


def search(
    query: str = "",
    kind: str = "error",
    symptom_class: str = "",
    severity: str = "",
    status: str = "",
    limit: int = 6,
) -> dict[str, Any]:
    if kind not in KINDS:
        return {"ok": False, "message": f"kind 只能是 {list(KINDS)}"}
    items = _load(kind)
    if not items:
        return {
            "ok": False,
            "message": f"没找到 {KINDS[kind]['dir']}/ 目录，插件可能不完整。",
        }

    def _keep(it: dict[str, Any]) -> bool:
        if symptom_class and symptom_class not in it["symptom_class"]:
            return False
        if severity and severity != it["severity"]:
            return False
        if status and status != it["status"]:
            return False
        return True

    pool = [it for it in items if _keep(it)]
    terms = _terms(query)
    scored: list[tuple[float, list[str], dict[str, Any]]] = []
    dropped = 0
    for it in pool:
        if terms:
            sc, why, found = _score(it, terms)
            if found == 0:
                if sc > 0:
                    dropped += 1
                continue
        else:
            sc, why = 0.0, []
        scored.append((sc, why, it))
    scored.sort(key=lambda x: (-x[0], x[2]["id"]))

    hits = [_preview(it, terms, sc, why) for sc, why, it in scored[: max(1, limit)]]
    out: dict[str, Any] = {
        "ok": True,
        "kind": kind,
        "noun": KINDS[kind]["noun"],
        "trust": KINDS[kind]["trust"],
        "total_entries": len(items),
        "searched": len(pool),
        "count": len(hits),
        "hits": hits,
    }
    if not hits and terms:
        out["hint"] = (
            "没命中。换你**实际看到的现象**描述（报错原文、界面上的错字），别写原因。"
            "错题本按症状组织，不按原因组织。"
            if kind == "error"
            else "没命中。可以不带 query 列出全部条目，再用 status 过滤。"
        )
        out["next"] = "kiant_hoi4_solutions" if kind == "error" else "kiant_hoi4_kb_search"
        if dropped:
            out["note"] = f"另有 {dropped} 条只是字面碎片命中（如「能不」），已丢弃，不作推荐。"
    elif hits:
        out["next"] = "kiant_hoi4_error_book action=get id=<命中的 id> 拿完整方案"
    return out


def get(kind: str = "error", entry_id: str = "", section: str = "") -> dict[str, Any]:
    if kind not in KINDS:
        return {"ok": False, "message": f"kind 只能是 {list(KINDS)}"}
    want = (entry_id or "").strip().upper()
    if not want:
        return {"ok": False, "message": "需要 id，例如 EB-003 或 SOL-012"}
    for it in _load(kind):
        if it["id"] == want:
            body = it["body"]
            if section:
                matched = [v for k, v in it["sections"].items() if section in k]
                if not matched:
                    return {
                        "ok": False,
                        "message": f"{want} 里没有含「{section}」的小节",
                        "sections": list(it["sections"]),
                    }
                body = "\n\n".join(matched)
            return {
                "ok": True,
                "id": it["id"],
                "title": it["title"],
                "file": it["path"],
                "symptom_class": it["symptom_class"],
                "severity": it["severity"],
                "status": it["status"],
                "related": it["related"],
                "sections": list(it["sections"]),
                "body": body,
                "trust": KINDS[kind]["trust"],
            }
    ids = [it["id"] for it in _load(kind)]
    return {"ok": False, "message": f"没有 {want} 这一条", "known": ids}


def list_entries(kind: str = "error", **filters: str) -> dict[str, Any]:
    return search(query="", kind=kind, limit=999, **filters)


def stats() -> dict[str, Any]:
    out: dict[str, Any] = {"ok": True}
    for kind in KINDS:
        items = _load(kind)
        bucket: dict[str, dict[str, int]] = {}
        key = "symptom_class" if kind == "error" else "status"
        alt = "severity" if kind == "error" else "source"
        for it in items:
            bucket.setdefault(it[key] or "(未标)", {}).setdefault(it[alt] or "(未标)", 0)
            bucket[it[key] or "(未标)"][it[alt] or "(未标)"] += 1
        out[kind] = {
            "noun": KINDS[kind]["noun"],
            "dir": KINDS[kind]["dir"],
            "count": len(items),
            "by_" + key: bucket,
            "ids": [it["id"] for it in items],
        }
    return out


def lint() -> dict[str, Any]:
    """Cheap integrity pass: ids unique, filename agrees with id, links resolve."""
    problems: list[dict[str, str]] = []
    for kind in KINDS:
        items = _load(kind)
        seen: dict[str, str] = {}
        ids = {it["id"] for it in items}
        for it in items:
            if it["id"] in seen:
                problems.append(
                    {"kind": kind, "id": it["id"], "issue": f"编号重复：{seen[it['id']]} 与 {it['file']}"}
                )
            seen[it["id"]] = it["file"]
            if not it["file"].upper().startswith(it["id"]):
                problems.append(
                    {"kind": kind, "id": it["id"], "issue": f"文件名没以编号开头：{it['file']}"}
                )
            for rel in it["related"]:
                target = rel.split("#")[0].strip()
                if not target or target.startswith(("http://", "https://")):
                    continue
                # related paths are written relative to references/, not to the
                # entry's own folder — that is the convention used across the
                # whole library, so honour it rather than "fixing" it locally.
                base = REFERENCES
                if "*" in target:
                    import glob as _glob
                    if _glob.glob(os.path.join(base, target)):
                        continue
                    problems.append(
                        {"kind": kind, "id": it["id"], "issue": f"related 通配符没匹配到文件：{target}"}
                    )
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                    problems.append(
                        {"kind": kind, "id": it["id"], "issue": f"related 指向不存在的文件：{target}"}
                    )
            if kind == "solution" and not it["status"]:
                problems.append({"kind": kind, "id": it["id"], "issue": "缺 status 标记"})
        idx = os.path.join(REFERENCES, KINDS[kind]["dir"], "_index.md")
        if os.path.isfile(idx):
            text = _read(idx)
            missing = sorted(i for i in ids if f"{i}.md" not in text and i not in text)
            for m in missing:
                problems.append({"kind": kind, "id": m, "issue": "总索引里没有列出"})
    return {"ok": not problems, "problems": problems, "count": len(problems)}

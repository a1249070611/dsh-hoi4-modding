"""Code generators for HOI4 content, plus localisation file repair."""

from __future__ import annotations

import os
from typing import Any

BOM = b"\xef\xbb\xbf"

SD = {
    "mod": None,
    "focus": "common/national_focus",
    "event": "events",
    "tech": "common/technologies",
    "idea": "common/ideas",
    "decision": "common/decisions",
    "scripted_effect": "common/scripted_effects",
    "scripted_trigger": "common/scripted_triggers",
    "character": "common/characters",
    "country_history": "history/countries",
    "gfx_sprite": "interface",
    "on_action": "common/on_actions",
}

MOD_DIRS = [
    "common/national_focus",
    "common/ideas",
    "common/decisions",
    "common/technologies",
    "common/scripted_effects",
    "common/scripted_triggers",
    "common/characters",
    "common/on_actions",
    "events",
    "history/countries",
    "history/units",
    "localisation/english",
    "gfx/interface",
    "interface",
]


def _safe(name: str, fallback: str) -> str:
    cleaned = "".join(c if (c.isalnum() or c in "_-.") else "_" for c in name.strip())
    return cleaned or fallback


def build_mod_skeleton(mod_path: str, display_name: str, tag: str, version: str) -> dict[str, bytes]:
    mod_id = os.path.basename(os.path.normpath(mod_path))
    outer = (
        f'version="{version}"\n'
        f"tags={{\n\t\"Gameplay\"\n}}\n"
        f'name="{display_name}"\n'
        f'supported_version="1.19.*"\n'
        f'path="mod/{mod_id}"\n'
    )
    inner = (
        f'version="{version}"\n'
        f"tags={{\n\t\"Gameplay\"\n}}\n"
        f'name="{display_name}"\n'
        f'supported_version="1.19.*"\n'
    )
    loc = (
        f"l_english:\n"
        f' {tag}:0 "{display_name}"\n'
        f' {tag}_DEF:0 "Our nation."\n'
        f' {tag}_ADJ:0 "Our"\n'
    )
    files: dict[str, bytes] = {
        os.path.join(os.path.dirname(os.path.abspath(mod_path)), mod_id + ".mod"): outer.encode("utf-8"),
        os.path.join(os.path.abspath(mod_path), "descriptor.mod"): inner.encode("utf-8"),
        os.path.join(os.path.abspath(mod_path), "localisation/english", f"{mod_id}_l_english.yml"): BOM
        + loc.encode("utf-8"),
    }
    return files


def gen_focus(tag: str, name: str, x: int, y: int, icon: str) -> str:
    fid = f"{tag}_{name}"
    return f"""focus_tree = {{
\tid = {tag.lower()}_focus_tree
\tcountry = {{
\t\tfactor = 0
\t\tmodifier = {{
\t\t\tadd = 10
\t\t\ttag = {tag}
\t\t}}
\t}}
\tdefault = no

\tfocus = {{
\t\tid = {fid}
\t\ticon = {icon}
\t\tcost = 10
\t\tx = {x}
\t\ty = {y}
\t\tcompletion_reward = {{
\t\t\tadd_political_power = 50
\t\t}}
\t}}
}}
"""


def gen_event(namespace: str, tag: str, idx: int, kind: str) -> tuple[str, list[str]]:
    eid = f"{namespace}.{idx}"
    body = f"""add_namespace = {namespace}

{kind} = {{
\tid = {eid}
\ttitle = {eid}.t
\tdesc = {eid}.d
\tpicture = GFX_report_event_generic_army
\tis_triggered_only = yes

\timmediate = {{
\t\tset_country_flag = {tag}_event_{idx}_fired
\t}}

\toption = {{
\t\tname = {eid}.a
\t\tadd_political_power = 25
\t}}
}}
"""
    keys = [f"{eid}.t", f"{eid}.d", f"{eid}.a"]
    return body, keys


def gen_tech(tag: str, name: str) -> tuple[str, list[str]]:
    base = f"{tag}_{name}"
    folder = f"{base}_folder"
    body = f"""technologies = {{

\t{base}_1 = {{
\t\tstart_year = 1936
\t\tresearch_cost = 1.0
\t\tfolder = {{
\t\t\tname = {folder}
\t\t\tposition = {{ x = 0 y = 0 }}
\t\t}}
\t\tpath = {{
\t\t\tleads_to_tech = {base}_2
\t\t\tresearch_cost_coeff = 1
\t\t}}
\t\tcategories = {{
\t\t\tindustry
\t\t}}
\t\tai_will_do = {{ factor = 1 }}
\t}}

\t{base}_2 = {{
\t\tstart_year = 1939
\t\tresearch_cost = 1.5
\t\tfolder = {{
\t\t\tname = {folder}
\t\t\tposition = {{ x = 0 y = 2 }}
\t\t}}
\t\tpath = {{
\t\t\tleads_to_tech = {base}_3
\t\t\tresearch_cost_coeff = 1
\t\t}}
\t\tdependencies = {{
\t\t\t{base}_1 = 1
\t\t}}
\t\tcategories = {{
\t\t\tindustry
\t\t}}
\t\tai_will_do = {{ factor = 1 }}
\t}}

\t{base}_3 = {{
\t\tstart_year = 1942
\t\tresearch_cost = 2.0
\t\tfolder = {{
\t\t\tname = {folder}
\t\t\tposition = {{ x = 0 y = 4 }}
\t\t}}
\t\tdependencies = {{
\t\t\t{base}_2 = 1
\t\t}}
\t\tcategories = {{
\t\t\tindustry
\t\t}}
\t\tai_will_do = {{ factor = 1 }}
\t}}

}}
"""
    keys = []
    for stage in range(1, 4):
        keys += [f"{base}_{stage}", f"{base}_{stage}_desc"]
    return body, keys


def gen_decision(tag: str, name: str) -> tuple[str, list[str]]:
    cat = f"{tag}_decisions"
    did = f"{tag}_{name}"
    body = f"""{cat} = {{
\ticon = GFX_decision_generic_political_rally
\tallowed = {{
\t\talways = yes
\t}}
\tvisible = {{
\t\talways = yes
\t}}
\tavailable = {{
\t\talways = yes
\t}}

\t{did} = {{
\t\ticon = GFX_decision_generic_political_rally
\t\tcost = 50
\t\tdays_remove = 30
\t\tavailable = {{
\t\t\talways = yes
\t\t}}
\t\tcomplete_effect = {{
\t\t\tadd_stability = 0.05
\t\t}}
\t\tai_will_do = {{
\t\t\tfactor = 1
\t\t}}
\t}}
}}
"""
    return body, [cat, f"{cat}_desc", did, f"{did}_desc"]


def gen_idea(tag: str, name: str) -> tuple[str, list[str]]:
    iid = f"{tag}_{name}"
    body = f"""ideas = {{
\tcountry = {{
\t\t{iid} = {{
\t\t\tpicture = GFX_idea_generic_build_infrastructure
\t\t\tmodifier = {{
\t\t\t\tstability_factor = 0.05
\t\t\t}}
\t\t}}
\t}}
}}
"""
    return body, [iid, f"{iid}_desc"]


def gen_scripted_effect(tag: str, name: str) -> tuple[str, list[str]]:
    sid = f"{tag}_{name}"
    body = f"""{sid} = {{
\tadd_political_power = 25
\tset_country_flag = {sid}_done
}}
"""
    return body, []


def gen_scripted_trigger(tag: str, name: str) -> tuple[str, list[str]]:
    tid = f"{tag}_{name}_trigger"
    body = f"""{tid} = {{
\thas_country_flag = {tag}_{name}_done
}}
"""
    return body, []


def gen_character(tag: str, name: str) -> tuple[str, list[str]]:
    cid = f"{tag}_{name}"
    body = f"""characters = {{
\t{tag} = {{
\t\t{cid} = {{
\t\t\tname = {cid}_name
\t\t\tportraits = {{
\t\t\t\tcivilian = {{
\t\t\t\t\tlarge = "GFX_portrait_{cid}"
\t\t\t\t}}
\t\t\t}}
\t\t\tcountry_leader = {{
\t\t\t\tideology = despotism
\t\t\t\ttraits = {{ }}
\t\t\t\texpire = "1965.1.1"
\t\t\t\tid = -1
\t\t\t}}
\t\t}}
\t}}
}}
"""
    return body, [f"{cid}_name"]


def gen_country_history(tag: str, capital: int) -> tuple[str, list[str]]:
    body = f"""capital = {capital}

set_politics = {{
\truling_party = neutrality
\telections_allowed = yes
}}

set_popularities = {{
\tdemocratic = 25
\tfascism = 15
\tcommunism = 20
\tneutrality = 40
}}

# 需要先在 common/ideas 里定义 TAG_idea，否则会报 could not find
# add_ideas = {{ {tag}_starting_idea }}

# oob 指向 history/units/<文件名>.txt，没有该文件时不要启用
# oob = "{tag}_1936"
"""
    return body, []


def gen_gfx_sprite(name: str) -> str:
    return f"""spriteTypes = {{
\tspriteType = {{
\t\tname = GFX_{name}
\t\ttexturefile = "gfx/interface/{name}.dds"
\t}}
}}
"""


def gen_on_action(tag: str, name: str) -> str:
    return f"""on_actions = {{
\ton_startup = {{
\t\teffect = {{
\t\t\tset_variable = {{ {tag}_{name}_started = yes }}
\t\t}}
\t}}
}}
"""


def loc_stub(keys: list[str], lang: str = "english") -> str:
    lines = [f"l_{lang}:"]
    for key in keys:
        lines.append(f' {key}:0 "TODO {key}"')
    return "\n".join(lines) + "\n"


def scaffold(
    mod_path: str,
    kind: str,
    name: str = "",
    tag: str = "TAG",
    namespace: str = "",
    x: int = 0,
    y: int = 0,
    icon: str = "",
    capital: int = 1,
    force: bool = False,
    display_name: str = "",
    version: str = "0.1.0",
) -> dict[str, Any]:
    mod_path = os.path.abspath(mod_path)
    tag = _safe(tag, "TAG").upper()
    name = _safe(name, "content")
    language = "english"

    writes: dict[str, bytes] = {}

    if kind == "mod":
        for d in MOD_DIRS:
            os.makedirs(os.path.join(mod_path, d), exist_ok=True)
        writes.update(
            build_mod_skeleton(mod_path, display_name or os.path.basename(mod_path), tag, version)
        )
        return _commit(mod_path, writes, force)

    if not os.path.isdir(mod_path):
        raise FileNotFoundError(f"mod 文件夹不存在：{mod_path}（先用 kind=\"mod\" 生成骨架）")

    loc_keys: list[str] = []
    merge_ok: set[str] = set()

    if kind == "loc":
        target = os.path.join(mod_path, "localisation", language, f"{tag.lower()}_{name}_l_{language}.yml")
        stub = BOM + loc_stub([name] if name != "content" else ["MY_KEY"], language).encode("utf-8")
        if os.path.isfile(target):
            # 文件已存在时绝不能整个重写——merge_ok 的语义是「允许覆盖」，
            # 之前直接把 stub 塞进 writes 并标 merge_ok，第二次跑 kind=loc
            # 会把用户写好的全部词条清掉只剩一行 TODO。这里改成合并：
            # 解析已有键，只追加缺失的。
            try:
                existing = open(target, "rb").read().decode("utf-8-sig")
            except UnicodeDecodeError:
                return {
                    "ok": False,
                    "message": f"{target} 不是合法 UTF-8，先跑 kiant_hoi4_fix_localisation 再补键。",
                }
            new_keys = [name] if name != "content" else ["MY_KEY"]
            missing = [k for k in new_keys if f" {k}:" not in existing]
            if missing:
                if not existing.endswith("\n"):
                    existing += "\n"
                existing += "\n".join(f' {k}:0 "TODO {k}"' for k in missing) + "\n"
                writes[target] = BOM + existing.encode("utf-8")
                merge_ok.add(target)
            else:
                return {
                    "ok": True,
                    "created": [],
                    "skipped_existing": [os.path.basename(target)],
                    "mod_path": mod_path,
                    "message": "文件已存在且键都在，没有改动。",
                }
        else:
            writes[target] = stub
        return _commit(mod_path, writes, force, merge_ok)

    folder = SD.get(kind)
    if folder is None:
        raise ValueError(f"未知 kind: {kind}；可选 {sorted(SD) + ['loc']}")

    if kind == "focus":
        content = gen_focus(tag, name, x, y, icon or "GFX_focus_generic_industry_2")
        filename = f"{tag.lower()}_{name}.txt"
        loc_keys = [f"{tag}_{name}", f"{tag}_{name}_desc"]
    elif kind == "event":
        ns = _safe(namespace or tag.lower(), "mymod")
        content, loc_keys = gen_event(ns, tag, 1, "country_event")
        filename = f"{ns}_events.txt"
    elif kind == "tech":
        content, loc_keys = gen_tech(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "decision":
        content, loc_keys = gen_decision(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "idea":
        content, loc_keys = gen_idea(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "scripted_effect":
        content, loc_keys = gen_scripted_effect(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "scripted_trigger":
        content, loc_keys = gen_scripted_trigger(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "character":
        content, loc_keys = gen_character(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    elif kind == "country_history":
        content, loc_keys = gen_country_history(tag, capital)
        filename = f"{tag} - {tag}.txt"
    elif kind == "gfx_sprite":
        content = gen_gfx_sprite(name)
        filename = "mymod_sprites.gfx"
    elif kind == "on_action":
        content = gen_on_action(tag, name)
        filename = f"{tag.lower()}_{name}.txt"
    else:  # pragma: no cover - guarded above
        raise ValueError(kind)

    target = os.path.join(mod_path, folder, filename)
    writes[target] = content.encode("utf-8")

    if loc_keys:
        loc_path = os.path.join(mod_path, "localisation", language, f"{tag.lower()}_{name}_l_{language}.yml")
        if os.path.isfile(loc_path):
            existing = open(loc_path, "rb").read().decode("utf-8-sig")
            missing = [k for k in loc_keys if f" {k}:" not in existing]
            if missing:
                if not existing.endswith("\n"):
                    existing += "\n"
                existing += "\n".join(f' {k}:0 "TODO {k}"' for k in missing) + "\n"
                writes[loc_path] = BOM + existing.encode("utf-8")
                merge_ok.add(loc_path)
        else:
            writes[loc_path] = BOM + loc_stub(loc_keys, language).encode("utf-8")
            merge_ok.add(loc_path)

    return _commit(mod_path, writes, force, merge_ok)


def _commit(mod_path: str, writes: dict[str, bytes], force: bool, merge_ok: set[str] | None = None) -> dict[str, Any]:
    created: list[str] = []
    skipped: list[str] = []
    merge_ok = merge_ok or set()
    for path, data in writes.items():
        if os.path.exists(path) and not force and path not in merge_ok:
            skipped.append(os.path.relpath(path, os.path.dirname(mod_path)).replace("\\", "/"))
            continue
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
        created.append(os.path.relpath(path, os.path.dirname(mod_path)).replace("\\", "/"))
    return {
        "created": created,
        "skipped_existing": skipped,
        "mod_path": mod_path,
        "next": "跑一遍 kiant_hoi4_validate_mod 确认没有缺本地化或语法错误。",
    }


# --------------------------------------------------------------------------- #
# Localisation repair
# --------------------------------------------------------------------------- #

def fix_localisation(mod_path: str, dry_run: bool = True) -> dict[str, Any]:
    mod_path = os.path.abspath(mod_path)
    loc_root = os.path.join(mod_path, "localisation")
    if not os.path.isdir(loc_root):
        return {"ok": False, "message": "没有 localisation 文件夹"}

    changed: list[dict] = []
    for base, _dirs, files in os.walk(loc_root):
        for name in files:
            if not name.lower().endswith(".yml"):
                continue
            path = os.path.join(base, name)
            raw = open(path, "rb").read()
            relpath = os.path.relpath(path, mod_path).replace("\\", "/")

            had_bom = raw.startswith(BOM)
            body = raw[3:] if had_bom else raw
            encoding_used = "utf-8"
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                for enc in ("gb18030", "cp1252"):
                    try:
                        text = body.decode(enc)
                        encoding_used = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    changed.append(
                        {"file": relpath, "action": "skipped", "reason": "无法用 utf-8/gb18030 解码，需手工处理"}
                    )
                    continue

            if had_bom and encoding_used == "utf-8":
                continue

            changed.append(
                {
                    "file": relpath,
                    "action": "would_rewrite" if dry_run else "rewritten",
                    "added_bom": not had_bom,
                    "converted_from": None if encoding_used == "utf-8" else encoding_used,
                }
            )
            if not dry_run:
                with open(path, "wb") as fh:
                    fh.write(BOM + text.encode("utf-8"))

    return {
        "ok": True,
        "dry_run": dry_run,
        "files_touched": len([c for c in changed if c.get("action") != "skipped"]),
        "detail": changed,
        "hint": "dry_run=false 才会真正写回；改写前建议先提交一次版本控制。",
    }

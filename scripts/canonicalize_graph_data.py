"""Канонизация docs/graph_data.json (одноразовый).

Применяет детерминированные правила к текущему graph_data.json и
перезаписывает его. Использует только data.json + effect_tags.json +
graph_mech_edges.json. После этого шага файл полностью воспроизводится
build_graph_data.py.

Правила:
  nodes:   sort by id
           color   = tag_to_color[первый тег] (tag_to_color = все теги
                     из effect_tags.json, отсортированные, round-robin
                     по 7 цветам палитры)
           font    = {"color": "white"} (const)
           shape   = "dot" (const)
           size    = round(10 + 40*log10(cit+1)/log10(max_cit+1)),
                     clamp 10..50, cit=None -> 0
           title   = "{name}<br>Grade: {grade}<br>Связей: {degree}"
  edges-tag: все пары (i<j) по sorted(id) с тегами(i) ∩ тегами(j) ≠ ∅
             from,to = sorted pair
             title   = "теги: " + ", ".join(sorted(inter))
             width   = 1.0 + 0.5 * len(inter)
             color   = "#2ecc71" (const)
  edges-mech: из graph_mech_edges.json как есть
  Выход: 2-space indent, ensure_ascii=False, trailing newline.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
TAGS = ROOT / "docs" / "effect_tags.json"
MECH = ROOT / "docs" / "graph_mech_edges.json"
OUT = ROOT / "docs" / "graph_data.json"

PALETTE = ["#1abc9c", "#2ecc71", "#3498db", "#9b59b6",
           "#e67e22", "#e74c3c", "#f39c12"]
TAG_COLOR = "#2ecc71"


def build_tag_to_color(tags_map):
    all_tags = sorted({t for ts in tags_map.values() for t in ts})
    return {tag: PALETTE[i % len(PALETTE)] for i, tag in enumerate(all_tags)}


def generate() -> dict:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    tags_map = json.loads(TAGS.read_text(encoding="utf-8"))
    mech = json.loads(MECH.read_text(encoding="utf-8"))["edges"]

    tag_to_color = build_tag_to_color(tags_map)

    by_id = {rec["id"]: rec for rec in data}
    ids = sorted(by_id.keys())

    # citations range for size scaling
    cits = [(rec.get("citations") or 0) for rec in data]
    max_cit = max(cits) if cits else 0
    log_max = math.log10(max_cit + 1) if max_cit > 0 else 1.0

    def size_of(cit):
        c = cit or 0
        s = 10 + 40 * (math.log10(c + 1) / log_max)
        s = round(s)
        return max(10, min(50, s))

    # degree from tag-edges + mech-edges
    deg = {i: 0 for i in ids}
    tag_edges = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            inter = sorted(set(tags_map.get(a, [])) & set(tags_map.get(b, [])))
            if not inter:
                continue
            tag_edges.append({
                "color": TAG_COLOR,
                "from": a,
                "title": "теги: " + ", ".join(inter),
                "to": b,
                "width": 1.0 + 0.5 * len(inter),
            })
            deg[a] += 1
            deg[b] += 1

    mech_edges = []
    for e in mech:
        mech_edges.append({
            "color": e.get("color", "#3498db"),
            "from": e["from"],
            "title": e["title"],
            "to": e["to"],
            "width": e.get("width", 2),
        })
        deg[e["from"]] += 1
        deg[e["to"]] += 1

    nodes = []
    for i in ids:
        rec = by_id[i]
        first_tags = tags_map.get(i, [])
        color = tag_to_color[first_tags[0]] if first_tags else PALETTE[0]
        nodes.append({
            "color": color,
            "font": {"color": "white"},
            "id": i,
            "label": rec["name"],
            "shape": "dot",
            "size": size_of(rec.get("citations")),
            "title": f"{rec['name']}<br>Grade: {rec.get('grade')}<br>"
                     f"Связей: {deg.get(i, 0)}",
        })

    edges = tag_edges + mech_edges
    nodes.sort(key=lambda n: n["id"])
    edges.sort(key=lambda e: (e["from"], e["to"]))

    return {"nodes": nodes, "edges": edges}


def main() -> int:
    graph = generate()
    text = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(f"[OK] canonicalized {OUT}: "
          f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Строит docs/interactions_graph.json — граф связей для interactions.html.

Два режима:
  supplements  — только добавки между собой (synergy / antagonist / interaction)
  drugs        — добавки + лекарственные классы (только interactions)

Матчер: точное совпадение 'with' с id/именем добавки,
или начало фразы 'Название ...'. Пустые with игнорируются.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
OUT_JSON = ROOT / "docs" / "interactions_graph.json"

# Добавки, которые не являются узлами-целями (пропускаем)
SKIP_TARGETS = {"", "—", "-", "нет"}


def build_lookup(data: list[dict]) -> dict[str, str]:
    """name (lowercase) → id. Плюс сам id."""
    lookup = {}
    for c in data:
        lookup[c["id"].lower()] = c["id"]
        lookup[c["name"].lower()] = c["id"]
    return lookup


def match_supplement(with_str: str, lookup: dict[str, str]) -> str | None:
    """Точное совпадение или фраза начинается с названия добавки."""
    low = (with_str or "").lower().strip()
    if not low or low in SKIP_TARGETS:
        return None
    # точное
    if low in lookup:
        return lookup[low]
    # фраза начинается с названия: "кальций и магний", "витамин d (при ...)"
    for key, cid in lookup.items():
        if low.startswith(key + " ") or low.startswith(key + "(") or low == key:
            return cid
    return None


def main() -> int:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    lookup = build_lookup(data)

    supp_edges: list[dict] = []
    drug_edges: list[dict] = []
    unmatched = Counter()

    for c in data:
        for i in c.get("interactions") or []:
            w = (i.get("with") or "").strip()
            if not w or w in SKIP_TARGETS:
                continue
            target = match_supplement(w, lookup)
            edge = {
                "from": c["id"],
                "to": target if target else w,
                "severity": i.get("severity", "medium"),
                "note": (i.get("note") or "")[:200],
                "type": "interaction",
            }
            if target:
                supp_edges.append(edge)
            else:
                drug_edges.append(edge)
                unmatched[w] += 1

        for s in c.get("synergists") or []:
            target = match_supplement(s, lookup)
            if target and target != c["id"]:
                supp_edges.append({
                    "from": c["id"],
                    "to": target,
                    "severity": "low",
                    "note": "",
                    "type": "synergy",
                })

        for a in c.get("antagonists") or []:
            target = match_supplement(a, lookup)
            if target and target != c["id"]:
                supp_edges.append({
                    "from": c["id"],
                    "to": target,
                    "severity": "medium",
                    "note": "",
                    "type": "antagonist",
                })

    # дедупликация неориентированных рёбер
    def dedup(edges: list[dict]) -> list[dict]:
        # приоритет: antagonist > synergy > interaction
        priority = {"antagonist": 3, "synergy": 2, "interaction": 1}
        by_pair: dict[tuple, dict] = {}
        for e in edges:
            key = tuple(sorted([e["from"], e["to"]]))
            old = by_pair.get(key)
            if not old or priority.get(e["type"], 0) > priority.get(old["type"], 0):
                by_pair[key] = e
        return list(by_pair.values())

    supp_unique = dedup(supp_edges)
    drug_unique = dedup(drug_edges)

    # ноды для режима добавок
    used_supp_ids = set()
    for e in supp_unique:
        used_supp_ids.add(e["from"])
        used_supp_ids.add(e["to"])
    nodes_supp = [
        {"id": c["id"], "label": c["name"], "grade": c.get("grade"), "code": c.get("code")}
        for c in data
        if c["id"] in used_supp_ids
    ]

    # ноды для режима лекарств
    used_drug_ids = set()
    for e in drug_unique:
        used_drug_ids.add(e["from"])
        used_drug_ids.add(e["to"])
    nodes_drug = [
        {"id": c["id"], "label": c["name"], "kind": "supplement",
         "grade": c.get("grade"), "code": c.get("code")}
        for c in data
        if c["id"] in used_drug_ids
    ]
    drug_names = {e["to"] for e in drug_unique if e["to"] not in {c["id"] for c in data}}
    for name in sorted(drug_names):
        nodes_drug.append({"id": name, "label": name, "kind": "drug"})

    out = {
        "supplements": {"nodes": nodes_supp, "edges": supp_unique},
        "drugs": {"nodes": nodes_drug, "edges": drug_unique},
    }
    OUT_JSON.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"[ok] {OUT_JSON}")
    print(f"  supplements: {len(nodes_supp)} нод, {len(supp_unique)} рёбер")
    print(f"  drugs:       {len(nodes_drug)} нод, {len(drug_unique)} рёбер")
    print(f"\n  Топ-5 лекарств по частоте:")
    for name, n in unmatched.most_common(5):
        print(f"    {n:3d}× {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
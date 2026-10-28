"""Собирает публичный API из docs/data.json.

Артефакты:
    docs/api/v1/supplements.json — карточки + метаданные
    docs/api/v1/index.json       — метаданные + список ID + статистика
    docs/api/v1/interactions.json — плоский список связей (FIX-41, D2-01)
    docs/api/v1/graph.json       — узлы и рёбра графа связей (FIX-41, D2-01)

Запуск:
    python scripts/build_api.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
OUT_DIR = ROOT / "docs" / "api" / "v1"

# Матчер «with» → id добавки живёт в build_interactions_graph.py: там он
# уже отлажен на графе сайта (точное совпадение или начало фразы) и
# отсекает пустые цели. Дублировать его здесь — гарантированно разойтись.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_interactions_graph import (  # noqa: E402
    SKIP_TARGETS, build_lookup, match_supplement,
)

SOURCE = "https://github.com/DeadSno/brain-25-evidence"
SITE = "https://deadsno.github.io/brain-25-evidence"
LICENSE = "CC BY 4.0"

PUBLIC_FIELDS = [
    "id", "category", "grade", "verdict", "code",
    "about", "who_needs", "onset", "myths",
    "food_sources", "guidelines", "how_to_choose",
    "dosage", "course", "caution", "upper_limit",
    "effects", "mechs", "interactions", "key_sources",
    "scienceIndex", "rct", "metaCount", "citations",
]


def slim(card: dict) -> dict:
    out = {}
    for k in PUBLIC_FIELDS:
        if k in card:
            out[k] = card[k]
    return out


def dedup(edges: list[dict]) -> list[dict]:
    """Оставляет одно ребро на пару узлов — с более сильным типом связи.

    Та же логика, что в build_interactions_graph.py (там dedup объявлен
    внутри main, поэтому импортировать его нельзя). Приоритет:
    antagonist > synergy > interaction; при равенстве остаётся первое.
    """
    priority = {"antagonist": 3, "synergy": 2, "interaction": 1}
    kept: dict[tuple[str, str], dict] = {}
    for e in edges:
        key = tuple(sorted((e["from"], e["to"])))
        prev = kept.get(key)
        if prev is None or priority.get(e["type"], 0) > priority.get(prev["type"], 0):
            kept[key] = e
    return list(kept.values())


def build_relations(d: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Собирает связи: плоский список для interactions.json и узлы/рёбра для graph.json.

    Источник — docs/data.json: поля interactions («с чем», важность, пояснение),
    synergists и antagonists. Цель «with» резолвится в id добавки тем же
    матчером, что и граф сайта; нерезолвленная цель остаётся узлом-лекарством.
    """
    supp_nodes = {}
    for c in d:
        cid = c.get("id")
        if cid:
            supp_nodes[cid] = {
                "id": cid,
                "label": c.get("name") or cid,
                "kind": "supplement",
                "grade": c.get("grade"),
                "code": c.get("code"),
            }

    lookup = build_lookup(d)
    rows = []
    for c in d:
        cid = c.get("id")
        if not cid:
            continue
        cname = c.get("name") or cid

        for item in (c.get("interactions") or []):
            with_str = (item.get("with") or "").strip()
            if not with_str or with_str in SKIP_TARGETS:
                continue
            rows.append({
                "from": cid,
                "from_name": cname,
                "with": with_str,
                "target": match_supplement(with_str, lookup),
                "type": "interaction",
                "severity": item.get("severity") or "medium",
                "note": item.get("note") or "",
            })

        for field, edge_type, severity in (
            ("synergists", "synergy", "low"),
            ("antagonists", "antagonist", "medium"),
        ):
            for raw in (c.get(field) or []):
                with_str = (raw or "").strip()
                if not with_str or with_str in SKIP_TARGETS:
                    continue
                target = match_supplement(with_str, lookup)
                if target == cid:
                    continue
                rows.append({
                    "from": cid,
                    "from_name": cname,
                    "with": with_str,
                    "target": target,
                    "type": edge_type,
                    "severity": severity,
                    "note": "",
                })

    edges = dedup([
        {
            "from": r["from"],
            "to": r["target"] or r["with"],
            "type": r["type"],
            "severity": r["severity"],
            "note": r["note"],
        }
        for r in rows
    ])

    drug_ids = sorted({e["to"] for e in edges if e["to"] not in supp_nodes})
    used = {e["from"] for e in edges} | {e["to"] for e in edges}
    nodes = [n for nid, n in supp_nodes.items() if nid in used]
    nodes += [{"id": drug_id, "label": drug_id, "kind": "drug"} for drug_id in drug_ids]
    return rows, nodes, edges


def main() -> int:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()

    grades = Counter(c.get("grade") for c in d if c.get("grade"))

    # Атомарные категории: "Спорт/Когниция" → Спорт, Когниция
    cats_atomic = Counter()
    cats_combined = Counter()
    for c in d:
        cat = c.get("category")
        if not cat:
            continue
        cats_combined[cat] += 1
        if isinstance(cat, str):
            for part in cat.split("/"):
                part = part.strip()
                if part:
                    cats_atomic[part] += 1

    supplements = [slim(c) for c in d]

    payload = {
        "version": "v1",
        "generated_at": now,
        "count": len(supplements),
        "license": LICENSE,
        "source": SOURCE,
        "site": SITE,
        "schema": {
            "id": "string (русский)",
            "category": "string (может содержать '/')",
            "grade": "A|B|C|D",
            "verdict": "работает|зависит от контекста|не подтверждено",
            "code": "-1|0|1",
            "effects": "string[]",
            "mechs": "[[механизм, эффект, сила]]",
            "interactions": "[{with, severity, note}]",
            "key_sources": "[{pmid, doi, title, year, journal}]",
            "scienceIndex": "int",
        },
        "supplements": supplements,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "supplements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rows, nodes, edges = build_relations(d)

    interactions_payload = {
        "version": "v1",
        "generated_at": now,
        "count": len(rows),
        "license": LICENSE,
        "source": SOURCE,
        "site": SITE,
        "schema": {
            "from": "id добавки, у которой описана связь",
            "from_name": "название добавки",
            "with": "контрагент в том виде, как в данных",
            "target": "id добавки или null, если контрагент — лекарство/класс",
            "type": "interaction|synergy|antagonist",
            "severity": "low|medium|high",
            "note": "пояснение из данных (может быть пустым)",
        },
        "interactions": rows,
    }
    (OUT_DIR / "interactions.json").write_text(
        json.dumps(interactions_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    graph_payload = {
        "version": "v1",
        "generated_at": now,
        "count_nodes": len(nodes),
        "count_edges": len(edges),
        "license": LICENSE,
        "source": SOURCE,
        "site": SITE,
        "schema": {
            "nodes": "[{id, label, kind: supplement|drug, grade?, code?}]",
            "edges": "[{from, to, type: interaction|synergy|antagonist, severity, note}]",
        },
        "nodes": nodes,
        "edges": edges,
    }
    (OUT_DIR / "graph.json").write_text(
        json.dumps(graph_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    index_payload = {
        "version": "v1",
        "generated_at": now,
        "count": len(supplements),
        "license": LICENSE,
        "source": SOURCE,
        "endpoints": {
            "supplements": "/api/v1/supplements.json",
            "interactions": "/api/v1/interactions.json",
            "graph": "/api/v1/graph.json",
            "full_data": "/data.json",
        },
        "stats": {
            "grades": dict(grades),
            "categories_atomic": dict(cats_atomic.most_common()),
            "categories_combined": dict(cats_combined.most_common()),
            "categories_atomic_count": len(cats_atomic),
        },
        "ids": [c["id"] for c in supplements],
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    size_kb = (OUT_DIR / "supplements.json").stat().st_size / 1024
    print(f"[OK] docs/api/v1/supplements.json — {len(supplements)} карточек, {size_kb:.1f} KB")
    print(f"[OK] docs/api/v1/index.json")
    print(f"[OK] docs/api/v1/interactions.json — {len(rows)} связей")
    print(f"[OK] docs/api/v1/graph.json — {len(nodes)} узлов, {len(edges)} рёбер")
    print(f"     Грейды: {dict(grades)}")
    print(f"     Атомарных категорий: {len(cats_atomic)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
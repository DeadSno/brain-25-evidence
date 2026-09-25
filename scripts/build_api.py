"""Собирает публичный API из docs/data.json.

Артефакты:
    docs/api/v1/supplements.json — карточки + метаданные
    docs/api/v1/index.json       — метаданные + список ID + статистика

Запуск:
    python scripts/build_api.py
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
OUT_DIR = ROOT / "docs" / "api" / "v1"

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

    index_payload = {
        "version": "v1",
        "generated_at": now,
        "count": len(supplements),
        "license": LICENSE,
        "source": SOURCE,
        "endpoints": {
            "supplements": "/api/v1/supplements.json",
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
    print(f"     Грейды: {dict(grades)}")
    print(f"     Атомарных категорий: {len(cats_atomic)}")
    print(f"     Составных категорий: {len(cats_combined)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
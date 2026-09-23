"""Создать papers_slim.json для Streamlit Cloud.

Убирает abstract (тяжёлое поле), оставляет нужные для дашборда поля.
~5 MB vs 90 MB полного papers.json.

Выход:
  data/papers/papers_slim.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "papers" / "papers_slim.json"

KEEP_FIELDS = (
    "pmid", "title", "journal", "year", "doi",
    "design", "species", "sjr_quartile", "sjr_score",
    "is_retracted", "pubtype", "language",
    "scimago_publisher", "scimago_country",
    "is_preprint", "preprint_server", "pmcid",
)


def main() -> int:
    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    slim = {}
    for pmid, p in papers.items():
        slim[pmid] = {k: p.get(k) for k in KEEP_FIELDS if k in p}

    OUT.write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"[OK] {OUT} — {len(slim)} papers, {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
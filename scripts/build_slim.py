"""Создать slim-JSON для Streamlit Cloud.

- papers_slim.json:   papers.json без abstract (~5-8 MB)
- supplements_slim.json:  data.json с полями для UI

Выход:
  data/papers/papers_slim.json
  data/supplements_slim.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
SUPPLEMENTS = ROOT / "docs" / "data.json"
OUT_PAPERS = ROOT / "data" / "papers" / "papers_slim.json"
OUT_SUPPLEMENTS = ROOT / "data" / "supplements_slim.json"

PAPER_FIELDS = (
    "pmid", "title", "journal", "year", "doi",
    "design", "species", "sjr_quartile", "sjr_score",
    "is_retracted", "pubtype", "language",
    "scimago_publisher", "scimago_country",
    "is_preprint", "preprint_server", "pmcid",
)


def main() -> int:
    # Papers
    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    slim = {pmid: {k: p.get(k) for k in PAPER_FIELDS if k in p}
            for pmid, p in papers.items()}
    OUT_PAPERS.write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] {OUT_PAPERS} — {len(slim)} papers, "
          f"{OUT_PAPERS.stat().st_size/1024/1024:.1f} MB")

    # Supplements
    if SUPPLEMENTS.exists():
        suppl = json.loads(SUPPLEMENTS.read_text(encoding="utf-8"))
        # data.json может быть dict или list — оставляем как есть
        OUT_SUPPLEMENTS.write_text(
            json.dumps(suppl, ensure_ascii=False), encoding="utf-8"
        )
        n = len(suppl) if isinstance(suppl, (list, dict)) else 0
        print(f"[OK] {OUT_SUPPLEMENTS} — {n} записей, "
              f"{OUT_SUPPLEMENTS.stat().st_size/1024:.0f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
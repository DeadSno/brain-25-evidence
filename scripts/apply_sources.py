"""Переносит curated PMIDs из reports/sources_candidates.json в docs/data.json.

Использование:
    python scripts/apply_sources.py                   # dry-run, показать diff
    python scripts/apply_sources.py --apply           # записать изменения
    python scripts/apply_sources.py --apply --force   # перезаписать существующие key_sources

Формат ключа key_sources в карточке: список словарей
    {pmid, title, year, journal, pubtype, source}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
CANDIDATES_JSON = ROOT / "reports" / "sources_candidates.json"


def _slim(entry: dict) -> dict:
    """Оставляем только то, что нужно карточке (без score/resolved_name)."""
    return {
        "pmid": entry["pmid"],
        "title": entry.get("title", "?"),
        "year": entry.get("year", 0),
        "journal": entry.get("journal", "?"),
        "pubtype": list(entry.get("pubtype") or []),
        "source": entry.get("source", "curated"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply curated sources to data.json")
    parser.add_argument("--apply", action="store_true",
                        help="записать изменения (по умолчанию dry-run)")
    parser.add_argument("--force", action="store_true",
                        help="перезаписать существующие key_sources")
    args = parser.parse_args()

    if not CANDIDATES_JSON.exists():
        print(f"[!] нет {CANDIDATES_JSON}. "
              f"Сначала: python scripts/search_sources.py --all-missing",
              file=sys.stderr)
        return 1
    if not DATA_JSON.exists():
        print(f"[!] нет {DATA_JSON}", file=sys.stderr)
        return 1

    candidates: dict[str, list[dict]] = json.loads(
        CANDIDATES_JSON.read_text(encoding="utf-8"))
    data: list[dict] = json.loads(DATA_JSON.read_text(encoding="utf-8"))

    added = replaced = skipped = 0
    no_candidates: list[str] = []

    for card in data:
        cid = card.get("id")
        if not cid:
            continue
        if cid not in candidates:
            no_candidates.append(cid)
            continue

        new_sources = [_slim(e) for e in candidates[cid]]
        old_sources = card.get("key_sources") or []
        old_pmids = [s.get("pmid") for s in old_sources]
        new_pmids = [s["pmid"] for s in new_sources]

        if old_sources and old_pmids == new_pmids:
            print(f"  {cid:25s} | без изменений ({len(new_sources)})")
            continue

        if old_sources and not args.force:
            print(f"  {cid:25s} | уже есть {len(old_sources)} key_sources — "
                  f"пропуск (--force для перезаписи)")
            skipped += 1
            continue

        if old_sources:
            print(f"  {cid:25s} | {len(old_sources)} → {len(new_sources)}")
            replaced += 1
        else:
            print(f"  {cid:25s} | 0 → {len(new_sources)}")
            added += 1

        for e in new_sources:
            types = ", ".join(e["pubtype"]) or "—"
            print(f"      + {e['pmid']} ({e['year']}) {types}")

        if args.apply:
            card["key_sources"] = new_sources

    if no_candidates:
        print(f"\n[!] карточек без candidates: {len(no_candidates)} "
              f"(первая: {no_candidates[0]})", file=sys.stderr)

    print(f"\nИтого: +{added} новых, {replaced} перезаписано, {skipped} пропущено")

    if args.apply:
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print("[dry-run] Изменения не записаны. Флаг --apply для записи.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
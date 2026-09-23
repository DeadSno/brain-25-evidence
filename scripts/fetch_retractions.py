"""A3.5.1b: Retractions через CrossRef batch — все retractions одним списком.

Скачивает все retracted DOI из CrossRef (~30k), сверяет с нашими DOI.

Использование:
    python scripts\\fetch_retractions_batch.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.config import MAILTO

UNPAYWALL = ROOT / "data" / "papers" / "unpaywall.json"
OUT = ROOT / "data" / "papers" / "retractions.json"

BASE = "https://api.crossref.org/works"
ROWS = 1000


def http_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25-retract/1.0 ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def fetch_all_retractions() -> dict[str, dict]:
    """Все retracted works из CrossRef через cursor pagination."""
    retracted = {}
    cursor = "*"
    page = 0

    while True:
        page += 1
        params = {
            "filter": "update-type:retraction",
            "rows": ROWS,
            "cursor": cursor,
            "select": "DOI,title,publisher,type,created,update-to",
            "mailto": MAILTO,
        }
        url = f"{BASE}?{urllib.parse.urlencode(params)}"
        try:
            data = http_get(url)
        except Exception as e:
            print(f"  [ERROR page {page}] {type(e).__name__}: {e}", file=sys.stderr)
            break

        items = data.get("message", {}).get("items", [])
        if not items:
            break

        for item in items:
            doi = (item.get("DOI") or "").lower()
            if not doi:
                continue
            title = (item.get("title") or [""])[0][:200]
            created = item.get("created", {}).get("date-parts", [[None]])[0]
            retracted[doi] = {
                "title": title,
                "publisher": item.get("publisher"),
                "type": item.get("type"),
                "year": created[0] if created else None,
            }

        print(f"  page {page}: +{len(items)} (total {len(retracted)})")

        cursor = data.get("message", {}).get("next-cursor")
        if not cursor or len(items) < ROWS:
            break

        time.sleep(0.3)

    return retracted


def main() -> int:
    print("Скачиваю ВСЕ retractions из CrossRef...")
    retracted_all = fetch_all_retractions()
    print(f"\nВсего retractions в CrossRef: {len(retracted_all)}\n")

    # Сверяем с нашими DOI
    unpaywall = json.loads(UNPAYWALL.read_text(encoding="utf-8"))
    our_dois = {d.lower() for d in unpaywall.keys()}

    matched = {}
    for doi in our_dois:
        if doi in retracted_all:
            matched[doi] = retracted_all[doi]

    # Сохраняем в формате совместимом с прошлым скриптом
    out = {}
    for doi in our_dois:
        out[doi] = {
            "is_retracted": doi in retracted_all,
            "retraction": retracted_all.get(doi),
            "status": "ok",
        }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {OUT}")
    print(f"     Наших DOI:        {len(our_dois)}")
    print(f"     Из них отозвано:  {len(matched)} ({len(matched)/len(our_dois)*100:.2f}%)")
    print()
    print("Топ-5 отозванных:")
    for doi, info in list(matched.items())[:5]:
        print(f"  {doi} ({info.get('year')}) — {(info.get('title') or '')[:70]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
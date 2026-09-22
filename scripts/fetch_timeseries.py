"""Time series: публикации по годам (PubMed esearch).

Для каждой карточки — esearch по term с фильтром по году.
Сохраняет data/timeseries/pubmed.json.

Rate limit: 3 req/s без API key. 94 × 10 = 940 запросов ~5 мин.

Использование:
    python scripts\\fetch_timeseries.py --source pubmed
    python scripts\\fetch_timeseries.py --source pubmed --years 2015-2025
    python scripts\\fetch_timeseries.py --source pubmed --only "Креатин"
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import SUPPLEMENTS, MAILTO  # noqa: E402

OUT_DIR = ROOT / "data" / "timeseries"
TERMS_FILE = ROOT / "docs" / "data_pubmed_terms.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
RATE_DELAY = 0.35  # ~3 req/s без API key


def esearch_count(term: str, year: int) -> int | None:
    """Количество публикаций за год. None при ошибке."""
    params = {
        "db": "pubmed",
        "term": f"({term}) AND {year}[dp]",
        "retmode": "json",
        "rettype": "count",
        "tool": "brain25-timeseries",
        "email": MAILTO,
    }
    url = f"{ESEARCH}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        return int(data["esearchresult"]["count"])
    except Exception as e:
        print(f"    [ERROR] {year}: {e}", file=sys.stderr)
        return None


def fetch_for_card(name: str, term: str, years: list[int]) -> dict[str, int | None]:
    result = {}
    for y in years:
        n = esearch_count(term, y)
        result[str(y)] = n
        print(f"  {name:20} {y}: {n}")
        time.sleep(RATE_DELAY)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="pubmed", choices=["pubmed"])
    ap.add_argument("--years", default="2015-2025",
                    help="Диапазон лет: YYYY-YYYY или список 2015,2018,2020")
    ap.add_argument("--only", default=None, help="Только одна карточка (для теста)")
    args = ap.parse_args()

    # Парсим годы
    if "-" in args.years and "," not in args.years:
        a, b = args.years.split("-")
        years = list(range(int(a), int(b) + 1))
    else:
        years = [int(x) for x in args.years.split(",")]

    terms = json.loads(TERMS_FILE.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "pubmed.json"

    # Существующие данные — докачиваем только новое
    existing = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else {}

    if args.only:
        cards = [(args.only, terms.get(args.only) or SUPPLEMENTS.get(args.only))]
        if not cards[0][1]:
            print(f"[ERROR] '{args.only}' нет ни в terms, ни в config", file=sys.stderr)
            return 1
    else:
        # Объединяем ключи из обоих источников
        all_ids = sorted(set(terms.keys()) | set(SUPPLEMENTS.keys()))
        cards = [(cid, terms.get(cid) or SUPPLEMENTS.get(cid)) for cid in all_ids]
        cards = [(cid, t) for cid, t in cards if t]

    total = len(cards) * len(years)
    print(f"Карточек: {len(cards)}, лет: {len(years)}, всего запросов: {total}")
    print(f"Оценка времени: ~{total * RATE_DELAY / 60:.1f} мин\n")

    done = 0
    for cid, term in cards:
        # Пропускаем если уже всё есть
        cached = existing.get(cid, {})
        missing_years = [y for y in years if str(y) not in cached]
        if not missing_years:
            print(f"  {cid:20} [cached]")
            done += len(years)
            continue

        print(f"— {cid}")
        fresh = fetch_for_card(cid, term, missing_years)
        existing[cid] = {**cached, **fresh}
        done += len(missing_years)

        # Сохраняем после каждой карточки (устойчиво к падению)
        out_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"\n[OK] {out_file}")
    print(f"     Карточек: {len(existing)}")
    print(f"     Лет:      {len(years)}")


if __name__ == "__main__":
    sys.exit(main())
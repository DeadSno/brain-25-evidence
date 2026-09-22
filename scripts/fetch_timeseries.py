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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import SUPPLEMENTS, MAILTO  # noqa: E402
from src.wiki_map import WIKI_RU  # noqa: E402

OUT_DIR = ROOT / "data" / "timeseries"
TERMS_FILE = ROOT / "docs" / "data_pubmed_terms.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
RATE_DELAY = 0.35  # ~3 req/s без API key
WIKI_API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "ru.wikipedia/all-access/user/{title}/monthly/{start}/{end}"
)
WIKI_DELAY = 0.1  # Wikimedia разрешает 100 req/s
OPENALEX_WORK = "https://api.openalex.org/works/pmid:{pmid}"
OPENALEX_CITES = "https://api.openalex.org/works"
OPENALEX_DELAY = 0.15  # polite pool, 10 req/s лимит


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


def fetch_wiki_for_card(name: str, wiki_title: str, months: list[str]) -> dict[str, int | None]:
    """Просмотры ru.wikipedia по месяцам. months = ['2015-01', '2015-02', ...]."""
    result: dict[str, int | None] = {}
    if not months:
        return result

    start = months[0].replace("-", "") + "01"
    end = months[-1].replace("-", "") + "01"
    url = WIKI_API.format(
        title=urllib.parse.quote(wiki_title, safe=""),
        start=start,
        end=end,
    )
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25-timeseries/1.0 ({MAILTO})"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        for item in data.get("items", []):
            # timestamp = "2020010100" → "2020-01"
            ts = item["timestamp"]
            key = f"{ts[:4]}-{ts[4:6]}"
            result[key] = item["views"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  {name:20} wiki: no article '{wiki_title}'")
        else:
            print(f"  {name:20} wiki: HTTP {e.code}", file=sys.stderr)
    except Exception as e:
        print(f"  {name:20} wiki: {type(e).__name__}: {e}", file=sys.stderr)
    return result


def openalex_work_id(pmid: str) -> str | None:
    """PMID → OpenAlex Work ID (например 'W1234567890')."""
    url = OPENALEX_WORK.format(pmid=pmid) + f"?mailto={MAILTO}&select=id"
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25/1.0 ({MAILTO})"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        wid = data.get("id")  # "https://openalex.org/W1234567890"
        return wid.rsplit("/", 1)[-1] if wid else None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"    [HTTP {e.code}] work_id pmid={pmid}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"    [ERROR work_id] {type(e).__name__}: {e}", file=sys.stderr)
        return None


def openalex_citations_by_year(work_id: str) -> dict[str, int]:
    """Распределение цитирующих работ по годам для одного Work ID."""
    url = (
        f"{OPENALEX_CITES}?filter=cites:{work_id}"
        f"&group_by=publication_year&mailto={MAILTO}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25/1.0 ({MAILTO})"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        out: dict[str, int] = {}
        for g in data.get("group_by", []):
            year = str(g.get("key", ""))
            if year.isdigit() and 2000 <= int(year) <= 2030:
                out[year] = g.get("count", 0)
        return out
    except urllib.error.HTTPError as e:
        print(f"    [HTTP {e.code}] cites {work_id}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"    [ERROR cites] {type(e).__name__}: {e}", file=sys.stderr)
        return {}


def make_months(years: list[int]) -> list[str]:
    """[2015, 2016] → ['2015-01', ..., '2016-12']."""
    return [f"{y}-{m:02d}" for y in years for m in range(1, 13)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="pubmed", choices=["pubmed", "wiki", "citations"])
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
    out_file = OUT_DIR / f"{args.source}.json"

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
    # ── WIKI ────────────────────────────────────────────────
    if args.source == "wiki":
        months = make_months(years)
        done = 0
        for cid in sorted(WIKI_RU.keys()):
            wiki_title = WIKI_RU[cid]
            cached = existing.get(cid, {})
            missing = [m for m in months if m not in cached]
            if not missing:
                print(f"  {cid:20} [cached]")
                done += len(months)
                continue

            print(f"— {cid} ({wiki_title})")
            fresh = fetch_wiki_for_card(cid, wiki_title, missing)
            existing[cid] = {**cached, **fresh}
            done += len(missing)
            time.sleep(WIKI_DELAY)

            out_file.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(f"\n[OK] {out_file}")
        print(f"     Карточек: {len(existing)}, месяцев: {len(months)}")
        return 0

    # ── CITATIONS (OpenAlex: цитаты по годам) ────────────────
    if args.source == "citations":
        data_json = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
        years_set = {str(y) for y in years}

        for c in data_json:
            cid = c["id"]
            cached = existing.get(cid, {})
            # Если для всех лет уже есть — пропускаем
            if cached and all(y in cached for y in years_set):
                print(f"  {cid:20} [cached]")
                continue

            sources = c.get("key_sources") or []
            pmids = [str(s["pmid"]) for s in sources if s.get("pmid")]
            if not pmids:
                print(f"  {cid:20} [no key_sources]")
                existing[cid] = {y: 0 for y in years_set}
                out_file.write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                continue

            print(f"— {cid} ({len(pmids)} sources)")
            total_by_year: dict[str, int] = {y: 0 for y in years_set}

            for pmid in pmids:
                wid = openalex_work_id(pmid)
                time.sleep(OPENALEX_DELAY)
                if not wid:
                    continue
                cites = openalex_citations_by_year(wid)
                time.sleep(OPENALEX_DELAY)
                for y, n in cites.items():
                    if y in total_by_year:
                        total_by_year[y] += n
                print(f"    PMID {pmid} → {wid}: {sum(cites.values())} цитат")

            existing[cid] = {**cached, **total_by_year}

            out_file.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

        print(f"\n[OK] {out_file}")
        print(f"     Карточек: {len(existing)}")
        print(f"     Лет:      {len(years)}")
        return 0

    # ── PUBMED ──────────────────────────────────────────────
    done = 0
    for cid, term in cards:
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

        out_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"\n[OK] {out_file}")
    print(f"     Карточек: {len(existing)}")
    print(f"     Лет:      {len(years)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
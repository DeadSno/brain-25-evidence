"""A3.2.2: Unpaywall — OA-статус + прямые ссылки на PDF.

Прогоняет все DOI из papers.json. Rate limit 10 req/s.
Кэш: повторный запуск докачивает только новое.

Выход:
  data/papers/unpaywall.json  — {doi: {is_oa, oa_status, pdf, url, host, version, license}}

Использование:
    python scripts\\fetch_unpaywall.py --limit 5     # тест
    python scripts\\fetch_unpaywall.py               # полный
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

from src.config import MAILTO  # noqa: E402

PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "papers" / "unpaywall.json"

API = "https://api.unpaywall.org/v2/{doi}?email={email}"
RATE_DELAY = 0.11  # ~9 req/s, чуть ниже лимита 10


def fetch_one(doi: str) -> dict | None:
    url = API.format(doi=urllib.parse.quote(doi), email=MAILTO)
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25-unpaywall/1.0 ({MAILTO})"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"is_oa": False, "status": "not_found"}
        return {"is_oa": False, "status": f"http_{e.code}"}
    except Exception as e:
        return {"is_oa": False, "status": f"error_{type(e).__name__}"}

    best = data.get("best_oa_location") or {}
    return {
        "is_oa": bool(data.get("is_oa")),
        "oa_status": data.get("oa_status"),          # gold / hybrid / bronze / green / closed
        "pdf": best.get("url_for_pdf"),
        "url": best.get("url"),
        "host": best.get("host_type"),                # repository / publisher
        "version": best.get("version"),               # publishedVersion / acceptedVersion / submittedVersion
        "license": best.get("license"),
        "journal_is_oa": data.get("journal_is_oa"),
        "journal_in_doaj": data.get("journal_is_in_doaj"),
        "year": data.get("year"),
        "title": (data.get("title") or "")[:150],
    }


def main() -> int:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Только N DOI (для теста)")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--workers", type=int, default=10, help="Параллельных потоков")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    dois = sorted({p["doi"] for p in papers.values() if p.get("doi")})
    print(f"Уникальных DOI: {len(dois)}")

    cache: dict = {}
    if OUT.exists() and not args.reset:
        cache = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"Кэш: {len(cache)}")

    todo = [d for d in dois if d not in cache]
    if args.limit:
        todo = todo[: args.limit]
    print(f"К обработке: {len(todo)}")
    print(f"Потоков:     {args.workers}")
    print(f"Оценка:      ~{len(todo) / args.workers * 0.5 / 60:.1f} мин\n")

    if not todo:
        print("[OK] Всё обработано")
        return 0

    t0 = time.time()
    done = 0
    n_oa = sum(1 for v in cache.values() if v.get("is_oa"))

    def task(doi: str) -> tuple[str, dict | None]:
        return doi, fetch_one(doi)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(task, d): d for d in todo}
        for fut in as_completed(futures):
            doi, result = fut.result()
            if result:
                cache[doi] = result
                if result.get("is_oa"):
                    n_oa += 1
            done += 1

            if done % 500 == 0:
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(
                    json.dumps(cache, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(todo) - done) / rate if rate else 0
                print(f"[{done}/{len(todo)}] OA: {n_oa} ({n_oa/done*100:.1f}%) · "
                      f"{rate:.1f} req/s · ETA {eta/60:.1f} мин")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    n_total = len(cache)
    n_oa_total = sum(1 for v in cache.values() if v.get("is_oa"))
    print(f"\n[OK] {OUT}")
    print(f"     Всего DOI: {n_total}")
    print(f"     OA:        {n_oa_total} ({n_oa_total/n_total*100:.1f}%)")
    print(f"     Время:     {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""A3.6.1: Финансирование из CrossRef funders.

Для каждого DOI из papers → api.crossref.org/works/{doi} → поле 'funder'.
Собираем funders с DOI (если есть), name, award.

Выход:
  data/papers/funders.json — {doi: [{name, doi, award}...]}

Использование:
    python scripts\\fetch_funders.py --limit 20
    python scripts\\fetch_funders.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from src.config import MAILTO  # noqa: E402
except ImportError:
    MAILTO = "brain25-evidence@users.noreply.github.com"

PAPERS = ROOT / "data" / "papers" / "papers.json"
OUT = ROOT / "data" / "papers" / "funders.json"
API = "https://api.crossref.org/works/{doi}?mailto={mailto}"


def fetch_one(doi: str) -> dict:
    url = API.format(doi=urllib.parse.quote(doi, safe=""), mailto=MAILTO)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"brain25-funders/1.0 ({MAILTO})"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"status": f"http_{e.code}", "funders": []}
    except Exception as e:
        return {"status": f"err_{type(e).__name__}", "funders": []}

    msg = data.get("message", {})
    funders = []
    for f in msg.get("funder") or []:
        funders.append({
            "name": (f.get("name") or "")[:200],
            "doi": f.get("DOI"),
            "award": (f.get("award") or [])[:5],
        })

    return {"status": "ok", "funders": funders}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=15)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    dois = sorted({(p.get("doi") or "").lower().strip()
                   for p in papers.values() if p.get("doi")})
    dois = [d for d in dois if d.startswith("10.")]
    print(f"DOIs с papers: {len(dois)}")

    cache: dict = {}
    if OUT.exists() and not args.reset:
        cache = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"В кэше:       {len(cache)}")

    todo = [d for d in dois if d not in cache]
    if args.limit:
        todo = todo[: args.limit]
    print(f"К обработке:  {len(todo)}")
    print(f"Воркеров:     {args.workers}")
    print(f"Оценка:       ~{len(todo) / 40 / 60:.0f} мин\n")

    if not todo:
        print("[OK] Всё проверено")
        return _summary(cache)

    t0 = time.time()
    done = 0
    ok = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(fetch_one, d): d for d in todo}
        for fut in as_completed(futures):
            doi = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": f"err_{type(e).__name__}", "funders": []}
            cache[doi] = result
            done += 1
            if result.get("status") == "ok":
                ok += 1

            if done % 500 == 0:
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2),
                               encoding="utf-8")
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(todo) - done) / rate if rate else 0
                print(f"[{done}/{len(todo)}] ok={ok} · "
                      f"{rate:.1f} req/s · ETA {eta/60:.1f} мин")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cache, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n[OK] {OUT} — {len(cache)} DOI за {time.time() - t0:.0f}s")
    return _summary(cache)


def _summary(cache: dict) -> int:
    ok = sum(1 for v in cache.values() if v.get("status") == "ok")
    with_funders = sum(1 for v in cache.values() if v.get("funders"))
    print(f"\nУспешных запросов:   {ok} / {len(cache)}")
    print(f"С funders:           {with_funders} ({with_funders/max(len(cache),1)*100:.1f}%)")

    names = Counter()
    for v in cache.values():
        for f in v.get("funders") or []:
            if f.get("name"):
                names[f["name"]] += 1

    print(f"\nТоп-20 funders:")
    for name, cnt in names.most_common(20):
        print(f"  {cnt:5d}× {name[:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
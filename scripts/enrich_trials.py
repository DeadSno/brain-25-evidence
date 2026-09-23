"""A3.5.7: Обогащение NCT через ClinicalTrials.gov API v2.

Читает data/papers/trials_links.json {pmid: [NCT...]} (формат: "NCT12345678"
или "NCT:NCT12345678"), собирает уникальные NCT, обогащает.

Выход:
  data/papers/trials_enriched.json

Использование:
    python scripts\\enrich_trials.py --limit 5
    python scripts\\enrich_trials.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
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

TRIALS_LINKS = ROOT / "data" / "papers" / "trials_links.json"
OUT = ROOT / "data" / "papers" / "trials_enriched.json"
API = "https://clinicaltrials.gov/api/v2/studies/{nct}"


def fetch_one(nct: str) -> dict:
    url = API.format(nct=nct)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"brain25-trials/1.0 ({MAILTO})",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"status": f"http_{e.code}"}
    except Exception as e:
        return {"status": f"err_{type(e).__name__}"}

    proto = data.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
    cond_mod = proto.get("conditionsModule", {})
    design_mod = proto.get("designModule", {})
    arms_mod = proto.get("armsInterventionsModule", {})
    contacts_mod = proto.get("contactsLocationsModule", {})

    enrollment_info = design_mod.get("enrollmentInfo") or {}
    lead = sponsor_mod.get("leadSponsor") or {}
    collaborators = sponsor_mod.get("collaborators") or []

    interventions = [
        {"type": iv.get("type"), "name": (iv.get("name") or "")[:200]}
        for iv in (arms_mod.get("interventions") or [])[:10]
    ]

    countries = sorted({
        loc.get("country") for loc in (contacts_mod.get("locations") or [])
        if loc.get("country")
    })

    return {
        "status": "ok",
        "brief_title": (ident.get("briefTitle") or "")[:300],
        "official_title": (ident.get("officialTitle") or "")[:500],
        "acronym": ident.get("acronym"),
        "study_type": design_mod.get("studyType"),
        "phase": (design_mod.get("phases") or [None])[0],
        "enrollment": enrollment_info.get("count"),
        "enrollment_type": enrollment_info.get("type"),
        "lead_sponsor": {
            "name": (lead.get("name") or "")[:200],
            "class": lead.get("class"),
        },
        "collaborators": [
            {"name": (c.get("name") or "")[:200], "class": c.get("class")}
            for c in collaborators[:5]
        ],
        "conditions": (cond_mod.get("conditions") or [])[:5],
        "interventions": interventions,
        "start_date": (status_mod.get("startDateStruct") or {}).get("date"),
        "completion_date": (status_mod.get("completionDateStruct") or {}).get("date"),
        "overall_status": status_mod.get("overallStatus"),
        "countries": countries[:10],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    if not TRIALS_LINKS.exists():
        print(f"[ERROR] {TRIALS_LINKS} не найден", file=sys.stderr)
        print("        Сначала: python scripts\\fetch_trials_links.py --fulltexts")
        return 1

    links = json.loads(TRIALS_LINKS.read_text(encoding="utf-8"))

    ncts: set[str] = set()
    for lst in links.values():
        for item in lst:
            nct = item.split(":", 1)[-1] if ":" in item else item
            if nct.startswith("NCT") and len(nct) == 11:
                ncts.add(nct)

    ncts_sorted = sorted(ncts)
    print(f"Всего PMID с trials: {len(links)}")
    print(f"Уникальных NCT:      {len(ncts_sorted)}")

    cache: dict = {}
    if OUT.exists() and not args.reset:
        cache = json.loads(OUT.read_text(encoding="utf-8"))
        print(f"В кэше:              {len(cache)}")

    todo = [n for n in ncts_sorted if n not in cache]
    if args.limit:
        todo = todo[: args.limit]

    print(f"К обработке:         {len(todo)}")
    print(f"Воркеров:            {args.workers}\n")

    if not todo:
        print("[OK] Всё обогащено")
        return _print_summary(cache)

    t0 = time.time()
    done = 0
    ok = 0
    err = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(fetch_one, nct): nct for nct in todo}
        for fut in as_completed(futures):
            nct = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": f"err_{type(e).__name__}"}
            cache[nct] = result
            done += 1
            if result.get("status") == "ok":
                ok += 1
            else:
                err += 1

            if done % 50 == 0:
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(
                    json.dumps(cache, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed else 0
                eta = (len(todo) - done) / rate if rate else 0
                print(f"[{done}/{len(todo)}] ok={ok} err={err} · "
                      f"{rate:.1f} nct/s · ETA {eta/60:.1f} мин")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[OK] {OUT} — {len(cache)} NCT за {time.time() - t0:.0f}s")
    return _print_summary(cache)


def _print_summary(cache: dict) -> int:
    if not cache:
        return 0

    ok = sum(1 for v in cache.values() if v.get("status") == "ok")
    print(f"\nУспешно обогащено: {ok} / {len(cache)} ({ok/len(cache)*100:.1f}%)")

    sponsors = Counter()
    for v in cache.values():
        s = v.get("lead_sponsor", {})
        if s.get("name"):
            sponsors[(s["name"], s.get("class"))] += 1

    print(f"\nТоп-15 лид-спонсоров:")
    for (name, cls), cnt in sponsors.most_common(15):
        print(f"  {cnt:3d}× [{cls or '?':12s}] {name[:70]}")

    classes = Counter(
        v.get("lead_sponsor", {}).get("class")
        for v in cache.values() if v.get("status") == "ok"
    )
    print(f"\nКлассы спонсоров:")
    for cls, cnt in classes.most_common():
        print(f"  {cls or '?':20s}: {cnt}")

    phases = Counter(
        v.get("phase") for v in cache.values() if v.get("status") == "ok"
    )
    print(f"\nФазы:")
    for ph, cnt in phases.most_common():
        print(f"  {ph or '?':15s}: {cnt}")

    stypes = Counter(
        v.get("study_type") for v in cache.values() if v.get("status") == "ok"
    )
    print(f"\nТипы исследований:")
    for st, cnt in stypes.most_common():
        print(f"  {st or '?':20s}: {cnt}")

    statuses = Counter(
        v.get("overall_status") for v in cache.values() if v.get("status") == "ok"
    )
    print(f"\nСтатусы:")
    for st, cnt in statuses.most_common(8):
        print(f"  {st or '?':20s}: {cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
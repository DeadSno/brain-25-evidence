"""Обновляет wiki pageviews + citations в docs/data.json.

Метрики:
  wiki      — сумма просмотров статьи ru.wikipedia за последние 12 месяцев
  citations — сумма cited_by_count по всем key_sources карточки (OpenAlex)

Использование:
    python scripts/fetch_metrics.py --only wiki
    python scripts/fetch_metrics.py --only citations
    python scripts/fetch_metrics.py --all --dry-run     # показать, что изменится
    python scripts/fetch_metrics.py --all --apply       # записать

Отчёт: reports/metrics_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.wiki_map import WIKI_RU  # noqa: E402

DATA_JSON = ROOT / "docs" / "data.json"
REPORT_JSON = ROOT / "reports" / "metrics_report.json"

UA = "brain-25-evidence/1.0 (deadsno1613@gmail.com)"
WIKI_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "ru.wikipedia/all-access/user/{title}/monthly/{start}/{end}"
)
OPENALEX_URL = "https://api.openalex.org/works"

# Период для wiki: последние 12 полных месяцев
WIKI_START = "2025090100"
WIKI_END = "2026090100"


def _get(url: str, retries: int = 3, timeout: int = 20) -> tuple[int, dict | None]:
    """GET с retry. Возвращает (status, json или None)."""
    last_exc = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code == 404:
                return 404, None
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return e.code, None
        except (urllib.error.URLError, TimeoutError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return 0, None
    return 0, None


# ---------------- wiki ----------------

def fetch_wiki(title: str) -> tuple[int, int | None]:
    """Возвращает (status, views). 404 — статьи нет."""
    url = WIKI_URL.format(title=urllib.parse.quote(title, safe=""), start=WIKI_START, end=WIKI_END)
    status, data = _get(url)
    if status != 200 or not data:
        return status, None
    views = sum(int(m.get("views", 0)) for m in data.get("items", []))
    return 200, views


# ---------------- citations ----------------

def fetch_citations(pmids: list[str]) -> tuple[int, int | None, int]:
    """Сумма cited_by_count по всем PMID. Возвращает (status, total, found_count)."""
    if not pmids:
        return 200, 0, 0
    # OpenAlex фильтр: pmid:123|456|789
    filt = "pmid:" + "|".join(pmids)
    mail = UA.split("(")[1].rstrip(")") if "(" in UA else ""
    url = (
        f"{OPENALEX_URL}?filter={urllib.parse.quote(filt, safe='|:')}"
        f"&per-page=50"
        f"&mailto={mail}"
    )
    status, data = _get(url)
    if status != 200 or not data:
        return status, None, 0
    results = data.get("results", [])
    total = sum(int(r.get("cited_by_count", 0)) for r in results)
    return 200, total, len(results)


# ---------------- main ----------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", choices=["wiki", "citations"],
                    help="какие метрики обновлять")
    ap.add_argument("--all", action="store_true", help="все метрики")
    ap.add_argument("--dry-run", action="store_true", help="не записывать")
    ap.add_argument("--apply", action="store_true", help="записать в data.json")
    args = ap.parse_args()

    if args.all:
        metrics = ["wiki", "citations"]
    elif args.only:
        metrics = args.only
    else:
        ap.print_help()
        return 1

    if args.apply and args.dry_run:
        print("[!] --apply и --dry-run вместе не имеют смысла")
        return 1

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    print(f"Карточек: {len(data)}. Метрики: {metrics}")
    if not args.apply:
        print("[dry-run] файл не будет изменён\n")

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "dry_run": not args.apply,
        "cards": {},
        "totals": {"ok": 0, "changed": 0, "missing": 0, "error": 0},
    }

    for c in data:
        cid = c["id"]
        changes: dict = {}

        if "wiki" in metrics:
            title = WIKI_RU.get(cid)
            if title is None:
                changes["wiki"] = {"status": "no_mapping"}
                report["totals"]["missing"] += 1
            else:
                status, views = fetch_wiki(title)
                old = c.get("wiki")
                if status == 404:
                    changes["wiki"] = {"status": "404", "title": title}
                    report["totals"]["missing"] += 1
                elif status != 200:
                    changes["wiki"] = {"status": f"http_{status}", "title": title}
                    report["totals"]["error"] += 1
                else:
                    changes["wiki"] = {"status": "ok", "old": old, "new": views}
                    if old != views:
                        report["totals"]["changed"] += 1
                        if args.apply:
                            c["wiki"] = views
                    else:
                        report["totals"]["ok"] += 1
                time.sleep(0.4)

        if "citations" in metrics:
            pmids = [s["pmid"] for s in c.get("key_sources") or []]
            if not pmids:
                changes["citations"] = {"status": "no_sources"}
                report["totals"]["missing"] += 1
            else:
                status, total, found = fetch_citations(pmids)
                old = c.get("citations")
                if status != 200:
                    changes["citations"] = {"status": f"http_{status}"}
                    report["totals"]["error"] += 1
                else:
                    changes["citations"] = {
                        "status": "ok", "old": old, "new": total,
                        "pmids_total": len(pmids), "pmids_found": found,
                    }
                    if old != total:
                        report["totals"]["changed"] += 1
                        if args.apply:
                            c["citations"] = total
                    else:
                        report["totals"]["ok"] += 1
                time.sleep(0.4)

        report["cards"][cid] = changes
        parts = []
        for k, v in changes.items():
            if v["status"] == "ok":
                parts.append(f"{k}: {v.get('old')} → {v.get('new')}")
            else:
                parts.append(f"{k}: {v['status']}")
        print(f"  {cid:30s} | " + " | ".join(parts))

    REPORT_JSON.parent.mkdir(exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nИтого: ok={report['totals']['ok']} "
          f"changed={report['totals']['changed']} "
          f"missing={report['totals']['missing']} "
          f"error={report['totals']['error']}")
    print(f"Отчёт: {REPORT_JSON}")

    if args.apply:
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print("[dry-run] data.json не изменён. Добавьте --apply для записи.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Пересчитывает rct, metaCount, scienceIndex для 81 карточки.

Методика (2026-09):
    base = pubmed_term без AND (outcome)
    metaCount   = (base) AND dietary supplements[mh] AND meta-analysis[pt]
    rct         = (base) AND dietary supplements[mh] AND randomized controlled trial[pt]
    scienceIndex = rct + 5 × metaCount

Использование:
    python scripts/recalc_science_index.py --dry-run
    python scripts/recalc_science_index.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
TERMS_JSON = ROOT / "docs" / "data_pubmed_terms.json"
REPORT = ROOT / "reports" / "science_index_report.json"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
MAILTO = "brain25-evidence@users.noreply.github.com"
UA = "brain-25-evidence/1.0"

BASE_RE = re.compile(r"^(.*?)\s+AND\s+\(", re.IGNORECASE)

# Явные базовые запросы для карточек, где regex отрезает лишнее
# (составные запросы с 2+ AND-группами)
EXPLICIT_BASE = {
    "Клюква": "(Vaccinium macrocarpon OR cranberry supplementation) AND (urinary tract infection)",
    # добавляется по результатам диагностики
}


def base_from_term(term: str, card_id: str = "") -> str | None:
    """base_query: явный из EXPLICIT_BASE или всё до первого ` AND (`."""
    if card_id and card_id in EXPLICIT_BASE:
        return EXPLICIT_BASE[card_id]
    m = BASE_RE.match(term)
    if not m:
        return None
    return m.group(1).strip()


def esearch_count(term: str, retries: int = 3) -> int | None:
    q = urllib.parse.quote(term)
    url = (
        f"{EUTILS}?db=pubmed&term={q}"
        f"&retmode=json&retmax=0"
        f"&email={urllib.parse.quote(MAILTO)}&tool=brain25_recalc"
    )
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return int(data["esearchresult"]["count"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    terms = json.loads(TERMS_JSON.read_text(encoding="utf-8"))

    print(f"Карточек: {len(data)}. Запросов: {len(terms)}. "
          f"Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": not args.apply,
        "cards": {},
        "totals": {"ok": 0, "changed": 0, "no_base": 0, "error": 0},
    }

    for c in data:
        cid = c["id"]
        term = terms.get(cid)
        if not term:
            print(f"  {cid:30s} | нет запроса")
            report["totals"]["no_base"] += 1
            report["cards"][cid] = {"status": "no_term"}
            continue

        base = base_from_term(term, cid)
        if not base:
            print(f"  {cid:30s} | не удалось извлечь base")
            report["totals"]["no_base"] += 1
            report["cards"][cid] = {"status": "no_base", "term": term}
            continue

        ma_q = f"({base}) AND meta-analysis[pt]"
        rct_q = f"({base}) AND randomized controlled trial[pt]"

        ma = esearch_count(ma_q)
        time.sleep(0.4)
        rct = esearch_count(rct_q)
        time.sleep(0.4)

        if ma is None or rct is None:
            print(f"  {cid:30s} | ошибка запроса (MA={ma}, RCT={rct})")
            report["totals"]["error"] += 1
            report["cards"][cid] = {"status": "error", "base": base}
            continue

        new_si = rct + 5 * ma
        old_si = c.get("scienceIndex")
        old_ma = c.get("metaCount")
        old_rct = c.get("rct")

        status = "ok" if old_si == new_si else "changed"
        if status == "changed":
            report["totals"]["changed"] += 1
        else:
            report["totals"]["ok"] += 1

        report["cards"][cid] = {
            "status": status,
            "old": {"rct": old_rct, "meta": old_ma, "si": old_si},
            "new": {"rct": rct, "meta": ma, "si": new_si},
            "base": base,
        }

        print(f"  {cid:30s} | РКИ: {old_rct}→{rct} | MA: {old_ma}→{ma} | SI: {old_si}→{new_si}")

        if args.apply:
            c["rct"] = rct
            c["metaCount"] = ma
            c["scienceIndex"] = new_si
            c["pubmed_term"] = term

    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nИтого: ok={report['totals']['ok']} "
          f"changed={report['totals']['changed']} "
          f"no_base={report['totals']['no_base']} "
          f"error={report['totals']['error']}")
    print(f"Отчёт: {REPORT}")

    if args.apply:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = DATA_JSON.with_suffix(f".json.bak-{ts}")
        shutil.copy2(DATA_JSON, backup)
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Бэкап:   {backup.name}")
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print("[dry-run] данные не записаны. Добавьте --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""Извлекает Hedges' g из abstracts МА для всех 81 карточки.

Использует src.extract_g.candidates(). Выбирает:
  1) первого кандидата с CI (более точная оценка)
  2) иначе — первого без CI
  3) если кандидатов нет — оставляет hedges_g = null

Пишет в data.json: hedges_g, hedges_g_ci, hedges_g_outcome, hedges_g_pmid.
Плюс сохраняет всех кандидатов в docs/hedges_g_all.json (для отладки).

Использование:
    python scripts/fetch_hedges_g.py            # dry-run
    python scripts/fetch_hedges_g.py --apply    # записать
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import extract_g  # noqa: E402

DATA_JSON = ROOT / "docs" / "data.json"
TERMS_JSON = ROOT / "docs" / "data_pubmed_terms.json"
ALL_JSON = ROOT / "docs" / "hedges_g_all.json"
REPORT = ROOT / "reports" / "hedges_g_report.json"


def base_from_term(term: str) -> str:
    import re
    m = re.match(r"^(.*?)\s+AND\s+\(", term, re.IGNORECASE)
    return m.group(1).strip() if m else term


def pick_best(cands: list[dict]) -> dict | None:
    if not cands:
        return None
    # приоритет 1: узкий CI (width < 1.0) — самый точный
    tight = [c for c in cands if c.get("ci") and abs(c["ci"][1] - c["ci"][0]) < 1.0]
    if tight:
        return tight[0]
    # приоритет 2: любой с CI
    with_ci = [c for c in cands if c.get("ci")]
    if with_ci:
        return with_ci[0]
    # приоритет 3: без CI
    return cands[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    terms = json.loads(TERMS_JSON.read_text(encoding="utf-8"))

    print(f"Карточек: {len(data)}. Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": not args.apply,
        "cards": {},
        "totals": {"found": 0, "with_ci": 0, "no_candidates": 0, "error": 0},
    }
    all_cands: dict[str, list] = {}

    for i, c in enumerate(data, 1):
        cid = c["id"]
        term = terms.get(cid)
        if not term:
            print(f"[{i:2d}/81] {cid:25s} | нет запроса")
            report["totals"]["no_candidates"] += 1
            report["cards"][cid] = {"status": "no_term"}
            continue

        base = base_from_term(term)
        try:
            cands = extract_g.candidates(cid, base)
        except Exception as e:
            print(f"[{i:2d}/81] {cid:25s} | ОШИБКА: {type(e).__name__}: {e}")
            report["totals"]["error"] += 1
            report["cards"][cid] = {"status": "error", "error": str(e)}
            time.sleep(1)
            continue

        all_cands[cid] = [
            {"pmid": x["pmid"], "g": x["g"], "ci": x.get("ci"),
             "outcome": x.get("outcome")}
            for x in cands
        ]

        best = pick_best(cands)
        if not best:
            print(f"[{i:2d}/81] {cid:25s} | нет g в abstracts")
            report["totals"]["no_candidates"] += 1
            report["cards"][cid] = {"status": "no_candidates"}
            continue

        has_ci = bool(best.get("ci"))
        if has_ci:
            report["totals"]["with_ci"] += 1
        report["totals"]["found"] += 1

        old_g = c.get("hedges_g")
        new_g = best["g"]
        changed = old_g != new_g

        report["cards"][cid] = {
            "status": "ok",
            "old_g": old_g,
            "new_g": new_g,
            "ci": best.get("ci"),
            "outcome": best.get("outcome"),
            "pmid": best["pmid"],
            "candidates_count": len(cands),
        }

        ci_str = f" [{best['ci'][0]}, {best['ci'][1]}]" if has_ci else ""
        changed_str = " ← changed" if changed else ""
        print(f"[{i:2d}/81] {cid:25s} | g={new_g}{ci_str}"
              f" | {len(cands)} канд.{changed_str}")

        if args.apply:
            c["hedges_g"] = new_g
            c["hedges_g_ci"] = best.get("ci")
            c["hedges_g_outcome"] = best.get("outcome") or ""
            c["hedges_g_pmid"] = best["pmid"]

    # сохраняем всех кандидатов
    ALL_JSON.write_text(
        json.dumps(all_cands, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n{'='*60}")
    print(f"Найдено g:       {report['totals']['found']}/81")
    print(f"Из них с CI:     {report['totals']['with_ci']}")
    print(f"Без кандидатов:  {report['totals']['no_candidates']}")
    print(f"Ошибок:          {report['totals']['error']}")
    print(f"\nОтчёт: {REPORT}")
    print(f"Все кандидаты: {ALL_JSON}")

    if args.apply:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = DATA_JSON.with_suffix(f".json.bak-{ts}")
        shutil.copy2(DATA_JSON, backup)
        DATA_JSON.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n[OK] Бэкап: {backup.name}")
        print(f"[OK] Записано: {DATA_JSON}")
    else:
        print(f"\n[dry-run] данные не записаны. Добавьте --apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
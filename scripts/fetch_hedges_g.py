"""Извлекает Hedges' g из abstracts МА для всех 81 карточки.

Использует scripts.extract_g.candidates().

Алгоритм (двухпроходный):
  Проход 1 — для каждой карточки собрать кандидатов (81 esearch+efetch).
  Проход 2 — сортируем карточки по числу кандидатов (по возрастанию),
             идём по ним и присваиваем PMID с учётом used_pmids:
              1) уникальный кандидат с узким CI (width < 1.0)
              2) уникальный с любым CI
              3) уникальный без CI
              4) fallback: все PMID заняты — берём любой, помечаем reused_shared

Один PMID = одна карточка (устраняет cross-matching network-МА).

Пишет в data.json: hedges_g, hedges_g_ci, hedges_g_outcome, hedges_g_pmid.
Плюс сохраняет всех кандидатов в docs/hedges_g_all.json (для отладки).

Использование:
    python scripts/fetch_hedges_g.py            # dry-run
    python scripts/fetch_hedges_g.py --apply    # записать
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
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
    m = re.match(r"^(.*?)\s+AND\s+\(", term, re.IGNORECASE)
    return m.group(1).strip() if m else term


def pick_best(cands: list[dict], used_pmids: set[str]) -> tuple[dict | None, bool]:
    """Выбирает лучшего кандидата с учётом уже использованных PMID.

    Возвращает (candidate, reused_shared).
    reused_shared=True — если пришлось взять уже занятый PMID (fallback).
    """
    if not cands:
        return None, False

    unique = [c for c in cands if c["pmid"] not in used_pmids]
    if unique:
        tight = [c for c in unique if c.get("ci") and abs(c["ci"][1] - c["ci"][0]) < 1.0]
        if tight:
            return tight[0], False
        with_ci = [c for c in unique if c.get("ci")]
        if with_ci:
            return with_ci[0], False
        return unique[0], False

    # все PMID заняты — fallback
    with_ci = [c for c in cands if c.get("ci")]
    return (with_ci[0] if with_ci else cands[0]), True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    terms = json.loads(TERMS_JSON.read_text(encoding="utf-8"))

    print(f"Карточек: {len(data)}. Режим: {'APPLY' if args.apply else 'dry-run'}\n")

    # ── Проход 1: собрать кандидатов для всех карточек (81 запрос) ────
    print("Проход 1/2: сбор кандидатов...\n")
    cands_by_id: dict[str, list[dict]] = {}
    errors: dict[str, str] = {}
    for i, c in enumerate(data, 1):
        cid = c["id"]
        term = terms.get(cid)
        if not term:
            cands_by_id[cid] = []
            continue
        base = base_from_term(term)
        try:
            cands_by_id[cid] = extract_g.candidates(cid, base)
        except Exception as e:
            errors[cid] = f"{type(e).__name__}: {e}"
            cands_by_id[cid] = []
        print(f"  [{i:2d}/81] {cid:25s} | {len(cands_by_id[cid])} канд."
              + (f" | ОШИБКА: {errors[cid]}" if cid in errors else ""))
    print()

    # ── Проход 2: присвоение PMID (сначала карточки с малым выбором) ──
    print("Проход 2/2: присвоение g...\n")
    order = sorted(data, key=lambda c: len(cands_by_id[c["id"]]))
    used_pmids: set[str] = set()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": not args.apply,
        "cards": {},
        "totals": {
            "found": 0, "with_ci": 0, "no_candidates": 0,
            "error": 0, "reused_shared": 0,
        },
    }
    all_cands: dict[str, list] = {}

    for idx, c in enumerate(order, 1):
        cid = c["id"]
        cands = cands_by_id[cid]

        if cid in errors:
            print(f"[{idx:2d}/81] {cid:25s} | ОШИБКА: {errors[cid]}")
            report["totals"]["error"] += 1
            report["cards"][cid] = {"status": "error", "error": errors[cid]}
            continue

        if not terms.get(cid):
            print(f"[{idx:2d}/81] {cid:25s} | нет запроса")
            report["totals"]["no_candidates"] += 1
            report["cards"][cid] = {"status": "no_term"}
            continue

        all_cands[cid] = [
            {"pmid": x["pmid"], "g": x["g"], "ci": x.get("ci"),
             "outcome": x.get("outcome")}
            for x in cands
        ]

        best, reused = pick_best(cands, used_pmids)
        if not best:
            print(f"[{idx:2d}/81] {cid:25s} | нет g в abstracts")
            report["totals"]["no_candidates"] += 1
            report["cards"][cid] = {"status": "no_candidates"}
            continue

        used_pmids.add(best["pmid"])
        if reused:
            report["totals"]["reused_shared"] += 1

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
            "reused_shared": reused,
        }

        ci_str = f" [{best['ci'][0]}, {best['ci'][1]}]" if has_ci else ""
        flags = ""
        if changed:
            flags += " ← changed"
        if reused:
            flags += " ⚠ shared"
        print(f"[{idx:2d}/81] {cid:25s} | g={new_g}{ci_str}"
              f" | {len(cands)} канд.{flags}")

        if args.apply:
            c["hedges_g"] = new_g
            c["hedges_g_ci"] = best.get("ci")
            c["hedges_g_outcome"] = best.get("outcome") or ""
            c["hedges_g_pmid"] = best["pmid"]

    # ── Сохранение ────────────────────────────────────────────────────
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
    print(f"Найдено g:        {report['totals']['found']}/81")
    print(f"Из них с CI:      {report['totals']['with_ci']}")
    print(f"Без кандидатов:   {report['totals']['no_candidates']}")
    print(f"Ошибок:           {report['totals']['error']}")
    print(f"Переиспользовано: {report['totals']['reused_shared']}")
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
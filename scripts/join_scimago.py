"""A3.5.5: Присоединить SCImago к papers.

Добавляет каждому paper:
  - sjr_quartile      — Q1/Q2/Q3/Q4
  - sjr_score         — SJR числовой
  - scimago_h_index   — H-индекс журнала
  - scimago_publisher — издатель
  - scimago_country   — страна

Матчинг по нормализованному названию журнала.
Не делает API-запросов — работает с локальным SCImago.

Использование:
    python scripts\\join_scimago.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAPERS = ROOT / "data" / "papers" / "papers.json"
SCIMAGO = ROOT / "data" / "journals" / "scimago.json"


def norm_title(t: str) -> str:
    """Нормализация названия журнала для матчинга."""
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"\s*\([^)]*\)", "", t)     # убрать скобки (...)
    t = re.sub(r"[^\w\s]", "", t)          # убрать всю пунктуацию
    t = re.sub(r"\s+", " ", t).strip()
    # убрать "the " в начале
    if t.startswith("the "):
        t = t[4:]
    return t


def main() -> int:
    if not PAPERS.exists():
        print(f"[ERROR] {PAPERS} не найден", file=sys.stderr)
        return 1
    if not SCIMAGO.exists():
        print(f"[ERROR] {SCIMAGO} не найден", file=sys.stderr)
        print(f"       Сначала запусти: python scripts\\fetch_scimago.py")
        return 1

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    scimago = json.loads(SCIMAGO.read_text(encoding="utf-8"))

    # Индексируем SCImago по нормализованному названию
    by_title_norm: dict[str, dict] = {}
    for title, rec in scimago.get("by_title", {}).items():
        key = norm_title(title)
        if key:
            by_title_norm[key] = rec

    print(f"SCImago журналов: {len(by_title_norm)}")
    print(f"Papers всего:     {len(papers)}\n")

    matched = 0
    total = 0
    seen_journals: set[str] = set()

    for pmid, p in papers.items():
        total += 1
        journal = p.get("journal")
        if not journal:
            continue
        seen_journals.add(journal)
        key = norm_title(journal)
        rec = by_title_norm.get(key)
        if rec:
            p["sjr_quartile"] = rec.get("quartile")
            p["sjr_score"] = rec.get("sjr")
            p["scimago_h_index"] = rec.get("h_index")
            p["scimago_publisher"] = rec.get("publisher")
            p["scimago_country"] = rec.get("country")
            matched += 1
        else:
            p.setdefault("sjr_quartile", None)

    PAPERS.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] {PAPERS}")
    print(f"     Всего papers:       {total}")
    print(f"     Уникальных журналов: {len(seen_journals)}")
    print(f"     Сматчено с SCImago:  {matched} ({matched / total * 100:.1f}%)")
    print()

    # Распределение квартилей
    q = Counter(p.get("sjr_quartile") for p in papers.values())
    print("Распределение по квартилям:")
    for k, v in q.most_common():
        label = k if k else "(не найдено)"
        pct = v / total * 100
        print(f"  {label:15}: {v:6d} ({pct:.1f}%)")

    # Топ-5 издателей
    pub = Counter(
        p.get("scimago_publisher") for p in papers.values()
        if p.get("scimago_publisher")
    )
    print("\nТоп-10 издателей:")
    for name, n in pub.most_common(10):
        print(f"  {n:6d}× {name}")

    # Топ-5 стран
    countries = Counter(
        p.get("scimago_country") for p in papers.values()
        if p.get("scimago_country")
    )
    print("\nТоп-10 стран:")
    for name, n in countries.most_common(10):
        print(f"  {n:6d}× {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
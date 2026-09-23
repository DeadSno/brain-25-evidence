"""Анализ funders из data/processed/xml_meta.json.

Топ-фандеры, страны, COI.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "data" / "processed" / "xml_meta.json"


def main() -> int:
    meta = json.loads(META.read_text(encoding="utf-8"))

    # 1. Топ funders (нормализованные)
    funders = Counter()
    for r in meta.values():
        for src in r.get("funding_sources", []):
            # Нормализация
            name = re.sub(r"\s+", " ", src).strip()
            if len(name) > 3 and len(name) < 200:
                funders[name] += 1

    print("=== ТОП-25 FUNDERS (Europe PMC XML) ===")
    for name, n in funders.most_common(25):
        print(f"{n:5}  {name[:80]}")

    # 2. Страны авторов
    countries = Counter()
    for r in meta.values():
        for c in r.get("countries", []):
            countries[c] += 1

    print(f"\n=== ТОП-20 СТРАН (по affiliations) ===")
    for c, n in countries.most_common(20):
        print(f"{n:5}  {c}")

    # 3. COI
    with_coi = sum(1 for r in meta.values() if r.get("has_coi"))
    with_fund = sum(1 for r in meta.values() if r.get("has_funding"))
    total = len(meta)
    print(f"\n=== SUMMARY ===")
    print(f"Всего статей:  {total}")
    print(f"С funding:     {with_fund} ({with_fund/total*100:.1f}%)")
    print(f"С COI:         {with_coi} ({with_coi/total*100:.1f}%)")

    # 4. По годам — funding rate
    print(f"\n=== FUNDING RATE ПО ГОДАМ ===")
    by_year: dict[str, list[bool]] = {}
    for r in meta.values():
        y = r.get("year", "")
        if y and y.isdigit():
            by_year.setdefault(y, []).append(r.get("has_funding", False))
    for y in sorted(by_year.keys()):
        vals = by_year[y]
        rate = sum(vals) / len(vals) * 100 if vals else 0
        if len(vals) >= 20:
            print(f"{y}:  {len(vals):4} статей, {rate:5.1f}% с funding")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
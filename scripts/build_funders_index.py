"""Готовит docs/funders.json для страницы funders.html.

Вход:
    data/processed/funders_top.csv
    data/processed/countries_top.csv
    data/processed/xml_meta.json

Выход:
    docs/funders.json
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNDERS_CSV = ROOT / "data" / "processed" / "funders_top.csv"
COUNTRIES_CSV = ROOT / "data" / "processed" / "countries_top.csv"
META = ROOT / "data" / "processed" / "xml_meta.json"
OUT = ROOT / "docs" / "funders.json"


def load_csv(path: Path, limit: int = 30) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append({"name": row["funder"] if "funder" in row else row["country"],
                         "n": int(row["papers"])})
    return rows


def funding_by_year(meta: dict) -> list[dict]:
    by_year: dict[str, list[bool]] = {}
    for r in meta.values():
        y = r.get("year", "")
        if y and y.isdigit() and len(y) == 4:
            by_year.setdefault(y, []).append(r.get("has_funding", False))
    out = []
    for y in sorted(by_year):
        vals = by_year[y]
        if len(vals) < 20:
            continue
        total = len(vals)
        with_f = sum(vals)
        out.append({
            "year": int(y),
            "total": total,
            "with_funding": with_f,
            "rate": round(with_f / total * 100, 1),
        })
    return out


def main() -> int:
    meta = json.loads(META.read_text(encoding="utf-8"))

    funders = load_csv(FUNDERS_CSV, limit=30)
    countries = load_csv(COUNTRIES_CSV, limit=30)
    years = funding_by_year(meta)

    total = len(meta)
    with_fund = sum(1 for r in meta.values() if r.get("has_funding"))
    with_coi = sum(1 for r in meta.values() if r.get("has_coi"))

    # Отношение Китай vs США (по фандерам из топа)
    china_funders = [
        "National Natural Science Foundation of China",
        "National Key R&D Program of China",
        "China Postdoctoral Science Foundation",
        "Ministry of Science and Technology of China",
        "Ministry of Education of China",
        "CAMS Innovation Fund for Medical Sciences",
        "China Agriculture Research System of MOF and MARA",
    ]
    usa_funders_prefix = "NIH"  # NIH, NIH — NCI, NIH — NIDDK...

    china_n = sum(f["n"] for f in funders if f["name"] in china_funders)
    usa_n = sum(f["n"] for f in funders
                if f["name"].startswith("NIH")
                or f["name"].startswith("National Institutes of Health"))

    out = {
        "summary": {
            "total_papers": total,
            "with_funding": with_fund,
            "funding_rate": round(with_fund / total * 100, 1),
            "with_coi": with_coi,
            "coi_rate": round(with_coi / total * 100, 1),
            "china_funders_papers": china_n,
            "usa_funders_papers": usa_n,
            "china_vs_usa": round(china_n / usa_n, 2) if usa_n else None,
        },
        "funders": funders,
        "countries": countries,
        "by_year": years,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    size_kb = OUT.stat().st_size / 1024
    print(f"[OK] {OUT} — {size_kb:.1f} KB")
    print(f"  Funders:   {len(funders)}")
    print(f"  Countries: {len(countries)}")
    print(f"  Years:     {len(years)}")
    print(f"  Summary:   funding={out['summary']['funding_rate']}%, "
          f"china_vs_usa={out['summary']['china_vs_usa']}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
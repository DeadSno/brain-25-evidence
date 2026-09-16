import json, sys, pathlib
from pathlib import Path

files = sorted(pathlib.Path("data/raw/pubmed").glob("*_catalog.json"))
print(f"найдено каталогов: {len(files)}\n")

for f in files[:3]:  # первые 3 добавки
    id_name = f.name.replace("_catalog.json", "")
    c = json.loads(f.read_text(encoding="utf-8"))
    cochrane_count = sum(1 for x in c if x.get("cochrane"))
    recent = sum(1 for x in c if int(x.get("year") or 0) >= 2020)
    print(f"=== {id_name} ===")
    print(f"  всего МА: {len(c)} | Cochrane: {cochrane_count} | ≥2020: {recent}")
    print(f"  ТОП-5 по приоритету (Cochrane → год → n):")
    top = sorted(c, key=lambda x: (not x["cochrane"], -(int(x["year"] or 0)), -(x["n_studies"] or 0)))[:5]
    for x in top:
        n = f"n={x['n_studies']}" if x["n_studies"] else "n=?"
        coc = "★COCHRANE" if x["cochrane"] else ""
        print(f"    [{x['year']}] {coc:12s} {n:6s} {x['title'][:85]}")
    print()

"""Квартальный аудит устаревших key_sources в data.json.

Проверяет все PMIDs старше 5 лет, группирует по карточкам.
Запуск: python scripts/audit_stale.py
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
REPORT = ROOT / "reports" / "audit_stale_report.json"

CUR_YEAR = datetime.now(timezone.utc).year
AGE_LIMIT = 5

d = json.loads(DATA.read_text(encoding="utf-8"))

all_old = []
cards_with_only_old = []
cards_mixed = []

for c in d:
    ks = c.get("key_sources") or []
    if not ks:
        continue
    fresh = [k for k in ks if (k.get("year") or 0) >= CUR_YEAR - AGE_LIMIT]
    old = [k for k in ks if (k.get("year") or 0) < CUR_YEAR - AGE_LIMIT]

    if not fresh:
        cards_with_only_old.append({
            "id": c["id"],
            "pmids": [{"pmid": k.get("pmid"), "year": k.get("year"),
                       "title": (k.get("title") or "")[:80]} for k in old],
        })
    elif old:
        cards_mixed.append({
            "id": c["id"],
            "old_pmids": [{"pmid": k.get("pmid"), "year": k.get("year")} for k in old],
        })

    for k in old:
        all_old.append({
            "card": c["id"],
            "pmid": k.get("pmid"),
            "year": k.get("year"),
            "age": CUR_YEAR - (k.get("year") or 0),
            "title": (k.get("title") or "")[:80],
        })

report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "current_year": CUR_YEAR,
    "age_limit": AGE_LIMIT,
    "totals": {
        "cards": len(d),
        "old_pmids": len(all_old),
        "cards_only_old": len(cards_with_only_old),
        "cards_mixed": len(cards_mixed),
    },
    "only_old": cards_with_only_old,
    "mixed": cards_mixed,
    "all_old_pmids": sorted(all_old, key=lambda x: -x["age"]),
}

REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"[OK] {REPORT}")
print(f"\nВсего карточек: {len(d)}")
print(f"PMIDs старше {AGE_LIMIT} лет: {len(all_old)}")
print(f"Карточек только со старыми: {len(cards_with_only_old)}")
print(f"Карточек со смешанными: {len(cards_mixed)}")

if cards_with_only_old:
    print(f"\n⚠️ Требуют замены (только старые):")
    for c in cards_with_only_old[:10]:
        print(f"  {c['id']}: {[p['year'] for p in c['pmids']]}")
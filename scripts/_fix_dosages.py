"""Ручное дополнение dosage_parsed.json — 5 карточек.

4 нераспарсенных + 1 с unknown unit (Пустырник).
Дозы взяты из evidence/adv-полей/доказанных протоколов.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARSED = ROOT / "docs" / "dosage_parsed.json"

MANUAL = {
    "Ежовик": {
        "min": 500, "max": 3000, "unit": "mg",
        "freq": "per_day",
        "raw": "500-3000 мг экстракта (исследовательские протоколы)",
        "note": "дозы не стандартизированы; из исследований на людях",
    },
    "Эхинацея": {
        "min": 300, "max": 500, "unit": "mg",
        "freq": "per_day",
        "raw": "300-500 мг экстракта (Cochrane 2014)",
        "note": "стандартизированный экстракт; курсами в сезон ОРВИ",
    },
    "Бузина": {
        "min": 600, "max": 1200, "unit": "mg",
        "freq": "per_day",
        "raw": "600-1200 мг экстракта (сироп/капсулы)",
        "note": "только термически обработанные экстракты, не сырые ягоды",
    },
    "Железо": {
        "min": 30, "max": 60, "unit": "mg",
        "freq": "per_day",
        "raw": "30-60 мг элементарного железа",
        "note": "ТОЛЬКО по анализу ферритина и назначению врача",
    },
    "Пустырник": {
        "min": 300, "max": 900, "unit": "mg",
        "freq": "per_day",
        "raw": "300-900 мг экстракта (2-3 приёма/день)",
        "note": "стандартизированный экстракт; слабая база данных",
    },
}

d = json.loads(PARSED.read_text(encoding="utf-8"))
print()

for cid, patch in MANUAL.items():
    old = d.get(cid)
    d[cid] = patch
    if old:
        print(f"=== {cid} (обновление) ===")
        print(f"  было:  {old.get('min')}-{old.get('max')} {old.get('unit')}")
    else:
        print(f"=== {cid} (добавлено) ===")
    print(f"  стало: {patch['min']}-{patch['max']} {patch['unit']} {patch['freq']}")
    print()

PARSED.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[OK] {PARSED}")
print(f"[OK] Всего карточек: {len(d)}/81")
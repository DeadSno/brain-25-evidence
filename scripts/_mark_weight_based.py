"""Помечает карточки с доза-от-веса в dosage_parsed.json.

Флаг weight_based: true + per_kg: {min, max, unit}.
"""
import json
from pathlib import Path

PARSED = Path("docs/dosage_parsed.json")
d = json.loads(PARSED.read_text(encoding="utf-8"))

# Карточки с дозой от веса (г/кг/сут или мг/кг/сут)
WEIGHT_BASED = {
    "Креатин":       {"min": 0.03, "max": 0.05, "unit": "g/kg", "note": "спорт — 0.03 г/кг, при загрузке 0.3 г/кг 5-7 дней"},
    "Кофеин":        {"min": 3, "max": 6, "unit": "mg/kg", "note": "3-6 мг/кг за 30-60 мин до нагрузки"},
    "BCAA":          {"min": 0.05, "max": 0.1, "unit": "g/kg", "note": "0.05-0.1 г/кг перед тренировкой"},
    "Сывороточный протеин": {"min": 1.6, "max": 2.2, "unit": "g/kg", "note": "общая норма белка 1.6-2.2 г/кг/сут"},
    "L-карнитин":    {"min": 0.02, "max": 0.04, "unit": "g/kg", "note": "0.02-0.04 г/кг/сут"},
    "Бета-аланин":   {"min": 0.065, "max": 0.08, "unit": "g/kg", "note": "0.065-0.08 г/кг/сут курсами"},
}

for cid, info in WEIGHT_BASED.items():
    if cid in d:
        d[cid]["weight_based"] = True
        d[cid]["per_kg"] = {k: v for k, v in info.items() if k != "note"}
        d[cid]["weight_note"] = info["note"]
        print(f"✅ {cid}: {info['min']}-{info['max']} {info['unit']}")

PARSED.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\n[OK] Помечено карточек: {len(WEIGHT_BASED)}")
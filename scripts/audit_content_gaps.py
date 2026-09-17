"""Аудит пробелов в контенте data.json — какие поля не заполнены и у кого."""
import json
from collections import Counter, defaultdict
from pathlib import Path

DATA = json.loads(
    Path(__file__).resolve().parents[1].joinpath("docs/data.json").read_text(encoding="utf-8")
)

BASE_FIELDS = ["verdict", "effects", "dosage", "course", "caution"]
ADV_FIELDS = [
    "about", "who_needs", "onset", "myths",
    "food_sources", "guidelines", "how_to_choose",
]
ALL_FIELDS = BASE_FIELDS + ADV_FIELDS

print(f"Всего БАДов: {len(DATA)}\n")

# 1. По каждому полю: сколько пустых
print("=== Пробелы по полям ===")
for f in ALL_FIELDS:
    empty = [s["id"] for s in DATA if not (s.get(f) or "")]
    tag = "BASE" if f in BASE_FIELDS else "ADV "
    print(f"  [{tag}] {f:20s} пусто у {len(empty):2d}/{len(DATA)}  {empty[:3]}")

# 2. По каждой карточке: сколько полей заполнено
print("\n=== Распределение по числу заполненных полей ===")
buckets = Counter()
for s in DATA:
    filled = sum(1 for f in ALL_FIELDS if (s.get(f) or ""))
    buckets[filled] += 1
for k in sorted(buckets, reverse=True):
    print(f"  заполнено {k:2d}/12 полей — {buckets[k]:2d} БАДов")

# 3. Кто полностью пустой из adv (все 7 adv = пусто)
print("\n=== Полностью пустые по ADV (топ-20) ===")
empty_adv = [
    s["id"] for s in DATA
    if not any(s.get(f) for f in ADV_FIELDS)
]
print(f"  Всего: {len(empty_adv)}")
print(f"  {empty_adv[:20]}")

# 4. Кто частично заполнен (1-6 adv из 7) — редкие случаи
print("\n=== Частично заполненные ADV (1-6 полей) ===")
partial = []
for s in DATA:
    adv_filled = sum(1 for f in ADV_FIELDS if (s.get(f) or ""))
    if 0 < adv_filled < len(ADV_FIELDS):
        partial.append((s["id"], adv_filled))
print(f"  Всего: {len(partial)}")
for sid, n in partial[:15]:
    print(f"    {sid:25s} {n}/7")
"""Диагностика: у кого ТОЛЬКО старые PMIDs (>5 лет) в key_sources."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))

CARDS = [
    "B12","L-Теанин","Ежовик","Фосфатидилсерин","Alpha-GPC","CDP-холин",
    "Гуперзин А","Ресвератрол","Тирозин","Таурин","CoQ10","Пикногенол",
    "Готу кола","Валериана","Бета-аланин","L-цитруллин","Бузина","Зверобой",
    "5-HTP","Триптофан","Глюкозамин + хондроитин","Биотин","Гиалуроновая кислота",
    "Клюква","Пустырник","Боярышник","Бета-глюканы овса","Рибофлавин",
    "Лютеин + зеаксантин","Инозитол","Альфа-липоевая кислота","D-манноза",
    "Мака","Хром","Астаксантин","Расторопша","Лактоферрин","SAMe","Йохимбин",
    "Пажитник","Чёрный тмин","Трибулус","NMN","Кордицепс","Рейши","Хлорофилл",
    "Сывороточный протеин","Глутамин","Босвеллия","Витамин K2","Кверцетин",
]

CUR_YEAR = 2026
AGE_LIMIT = 5

by_id = {c["id"]: c for c in DATA}

groups = {"all_old": [], "mixed": [], "has_fresh": [], "no_ks": []}

print("=" * 70)
print("Разбор по возрасту key_sources")
print("=" * 70)

for cid in CARDS:
    c = by_id.get(cid)
    if not c:
        continue
    ks = c.get("key_sources") or []
    if not ks:
        groups["no_ks"].append(cid)
        print(f"\n{cid}: ❌ нет key_sources")
        continue

    fresh = [ks_ for ks_ in ks if (ks_.get("year") or 0) >= CUR_YEAR - AGE_LIMIT]
    old = [ks_ for ks_ in ks if (ks_.get("year") or 0) < CUR_YEAR - AGE_LIMIT]

    line = f"\n{cid}: всего {len(ks)}"
    line += f" | свежих {len(fresh)} | старых {len(old)}"
    print(line)

    for k in ks:
        year = k.get("year") or "?"
        mark = "✅" if year != "?" and year >= CUR_YEAR - AGE_LIMIT else "⚠️"
        print(f"    {mark} {year}  PMID {k.get('pmid')}  {(k.get('title') or '')[:70]}")

    if not fresh:
        groups["all_old"].append(cid)
    elif len(fresh) == len(ks):
        groups["has_fresh"].append(cid)
    else:
        groups["mixed"].append(cid)

print("\n" + "=" * 70)
print("СВОДКА")
print("=" * 70)
print(f"\n🔴 Все key_sources старые (нужна замена): {len(groups['all_old'])}")
for cid in groups["all_old"]:
    print(f"    {cid}")
print(f"\n🟡 Смешанные (1+ свежий есть): {len(groups['mixed'])}")
for cid in groups["mixed"]:
    print(f"    {cid}")
print(f"\n🟢 Только свежие: {len(groups['has_fresh'])}")
print(f"\n⚫ Без key_sources: {len(groups['no_ks'])}")
for cid in groups["no_ks"]:
    print(f"    {cid}")
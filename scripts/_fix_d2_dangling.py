"""D2 follow-up: фикс ma_top3 + проверка упоминаний старых источников в текстах."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
d = json.loads(DATA.read_text(encoding="utf-8"))

REMOVED = {
    "Гуперзин А": ["18425924", "19370686", "23235666"],
    "Пикногенол": ["22513958", "31585179"],
    "Валериана": ["17054208", "20347389", "17517355"],
    "Зверобой": ["28064110"],
    "Глюкозамин + хондроитин": ["15846645", "29713967"],
    "Мака": ["20691074", "21840656"],
    "Пажитник": ["24438170"],
    "Кордицепс": ["25519252", "26457607", "28137532"],
    "Рейши": ["27045603", "22696372"],
    "Глутамин": ["25199493", "11687112"],
}

# Старые годы для этих карточек (годы удалённых PMIDs)
# При проверке ищем упоминания типа "Cochrane 2007", "МА 2008" и т.д.
YEARS_BY_CARD = {}
for cid, pmids in REMOVED.items():
    c = next((x for x in d if x["id"] == cid), None)
    # Годы мы знаем из диагностики
    years_map = {
        "Гуперзин А": [2008, 2009, 2012],
        "Пикногенол": [2012, 2019],
        "Валериана": [2006, 2007, 2010],
        "Зверобой": [2017],
        "Глюкозамин + хондроитин": [2005, 2018],
        "Мака": [2010, 2011],
        "Пажитник": [2014],
        "Кордицепс": [2014, 2015, 2017],
        "Рейши": [2012, 2016],
        "Глутамин": [2001, 2014],
    }
    YEARS_BY_CARD[cid] = years_map.get(cid, [])

ADV = ["about", "who_needs", "onset", "myths",
       "food_sources", "guidelines", "how_to_choose"]

by_id = {c["id"]: c for c in d}

print("=" * 70)
print("1. ma_top3 — удалённые PMIDs")
print("=" * 70)

found_ma = False
for cid, pmids in REMOVED.items():
    c = by_id.get(cid)
    if not c:
        continue
    new_top3 = []
    changed = False
    for k in c.get("ma_top3") or []:
        if str(k.get("pmid")) in pmids:
            print(f"  ⚠️  {cid}.ma_top3: удалённый PMID {k.get('pmid')}")
            changed = True
        else:
            new_top3.append(k)
    if changed:
        found_ma = True
        # Заменяем первый удалённый на первый свежий из key_sources
        ks = c.get("key_sources") or []
        ks_pmids = {str(x.get("pmid")) for x in ks}
        top3_pmids = {str(x.get("pmid")) for x in new_top3}
        for k in ks:
            if str(k.get("pmid")) not in top3_pmids:
                new_top3.insert(0, {
                    "pmid": k.get("pmid"),
                    "title": k.get("title", ""),
                    "year": k.get("year", 0),
                })
                break
        c["ma_top3"] = new_top3[:3]
        print(f"     → стало: {[x.get('pmid') for x in c['ma_top3']]}")

if not found_ma:
    print("  ✅ всё чисто")

print("\n" + "=" * 70)
print("2. Упоминания старых лет в adv-полях")
print("=" * 70)

found_years = False
for cid, years in YEARS_BY_CARD.items():
    c = by_id.get(cid)
    if not c:
        continue
    for f in ADV:
        v = str(c.get(f) or "")
        for y in years:
            if re.search(rf'\b{y}\b', v):
                # Контекст
                idx = v.find(str(y))
                snippet = v[max(0, idx-40):idx+40]
                print(f"  ⚠️  {cid}.{f}: упомянут {y}")
                print(f"       …{snippet}…")
                found_years = True

if not found_years:
    print("  ✅ нет упоминаний удалённых годов")

# Сохраняем если были изменения
if found_ma:
    import shutil
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copy2(DATA, DATA.with_suffix(f".json.bak-{ts}"))
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n[OK] ma_top3 исправлен, бэкап {ts}")
else:
    print("\n[SKIP] Изменений не требуется")
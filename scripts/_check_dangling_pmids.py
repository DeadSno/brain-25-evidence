"""Проверка: adv-поля и mechs ссылаются на удалённые PMIDs?"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))

# PMIDs, которые мы удалили в D2 (свежие убрали, старые оставили)
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

ADV = ["about", "who_needs", "onset", "myths",
       "food_sources", "guidelines", "how_to_choose"]

by_id = {c["id"]: c for c in DATA}

print("=" * 70)
print("Проверка ссылок на удалённые PMIDs в adv-полях и mechs")
print("=" * 70)

for cid, removed in REMOVED.items():
    c = by_id.get(cid)
    if not c:
        continue
    hits = []
    for f in ADV:
        v = str(c.get(f) or "")
        for pmid in removed:
            if pmid in v:
                hits.append(f"adv.{f}: ссылка на {pmid}")
    # mechs — массив массивов строк
    for i, m in enumerate(c.get("mechs") or []):
        m_str = " ".join(str(x) for x in m)
        for pmid in removed:
            if pmid in m_str:
                hits.append(f"mechs[{i}]: ссылка на {pmid}")
    # ma_top3
    for k in c.get("ma_top3") or []:
        if str(k.get("pmid")) in removed:
            hits.append(f"ma_top3: PMID {k.get('pmid')}")

    if hits:
        print(f"\n⚠️  {cid}:")
        for h in hits:
            print(f"     {h}")

print("\n" + "=" * 70)
print("Также проверим: adv-поля ссылаются на PMIDs вне key_sources")

# Второй тип проверки — вообще любая ссылка на PMID в adv-полях
# должна быть среди key_sources карточки
import re
PMID_RE = re.compile(r'\b(\d{7,8})\b')

orphans = []
for c in DATA:
    ks_pmids = {str(k.get("pmid")) for k in (c.get("key_sources") or [])}
    for f in ADV:
        v = str(c.get(f) or "")
        for match in PMID_RE.finditer(v):
            pmid = match.group(1)
            # PMID начинается с 1-4 для современных
            if pmid[0] in "1234" and pmid not in ks_pmids:
                orphans.append((c["id"], f, pmid))

if orphans:
    print(f"\n⚠️  adv-поля ссылаются на PMIDs вне key_sources ({len(orphans)}):")
    for cid, f, pmid in orphans[:30]:
        print(f"     {cid}.{f}: PMID {pmid}")
    if len(orphans) > 30:
        print(f"     … ещё {len(orphans) - 30}")
else:
    print("\n✅ Все PMIDs в adv-полях присутствуют в key_sources")
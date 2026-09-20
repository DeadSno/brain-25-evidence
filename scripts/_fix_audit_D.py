"""Группа D аудита — косметика.

D2 (дубли): BCAA — убрать дубль Cochrane 2015
D3 (формулировки): Омега-3, L-карнитин
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

PATCHES = {
    # D2: дубль Cochrane в key_sources
    "BCAA": {
        "_drop_ks": ["26377410"],  # старая версия Cochrane 2015
    },
    # D3: формулировки
    "Омега-3": {
        "guidelines": "EFSA: DHA для мозга и зрения. AHA: рыба 2 раза в неделю. Cochrane: на ССЗ-события — «little or no effect» (не «скромный»).",
    },
    "L-карнитин": {
        "onset": "Нейропатия — курсы 6-12 мес; СД2-маркеры — 12-24 нед; мгновенного эффекта нет.",
    },
}

d = json.loads(DATA.read_text(encoding="utf-8"))

print(f"Правок: {len(PATCHES)}\n")
for cid, patch in PATCHES.items():
    c = next((x for x in d if x["id"] == cid), None)
    if not c:
        print(f"❌ {cid}")
        continue
    print(f"=== {cid} ===")
    if "_drop_ks" in patch:
        ks = c.get("key_sources") or []
        print(f"  key_sources было: {[x.get('pmid') for x in ks]}")
        ks = [x for x in ks if str(x.get("pmid")) not in patch["_drop_ks"]]
        c["key_sources"] = ks
        print(f"  key_sources стало: {[x.get('pmid') for x in ks]}")
        print(f"  -удалён дубль: {patch['_drop_ks']}")
    for f, v in patch.items():
        if f.startswith("_"):
            continue
        print(f"  [{f}] было: {str(c.get(f))[:80]}…")
        print(f"  [{f}] стало: {v[:80]}…")
        c[f] = v
    print()

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(DATA, DATA.with_suffix(f".json.bak-{ts}"))
DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[OK] Бэкап: {DATA.with_suffix(f'.json.bak-{ts}').name}")
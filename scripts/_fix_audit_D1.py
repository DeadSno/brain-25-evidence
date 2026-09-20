"""Группа D1 аудита — замена 5 устаревших PMIDs.

По результатам refresh_pmids.py:
- Кофеин: -20464765 (2010) +36870101 (2023, сон)
- Родиола: -21036578 (2011) +41080184 (2025, endurance)
- Куркумин: -23076948 (2012) +35935936 (2022, arthritis)
- NAC: -22972094 (2012) +38555190 (2024, COPD)
- Мелатонин: -24802882 (2014) +40662882 (2025, ICU)
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

NEW_SOURCES = {
    "36870101": {
        "pmid": "36870101",
        "title": "The effect of caffeine on subsequent sleep: A systematic review and meta-analysis.",
        "year": 2023,
        "journal": "Sleep medicine reviews",
        "pubtype": ["Journal Article", "Meta-Analysis", "Systematic Review"],
        "source": "curated",
    },
    "41080184": {
        "pmid": "41080184",
        "title": "The effect of Rhodiola rosea supplementation on endurance performance and related biomarkers.",
        "year": 2025,
        "journal": "Frontiers in nutrition",
        "pubtype": ["Journal Article", "Systematic Review"],
        "source": "curated",
    },
    "35935936": {
        "pmid": "35935936",
        "title": "Efficacy and Safety of Curcumin and Curcuma longa Extract in the Treatment of Arthritis: A Systematic Review and Meta-analysis.",
        "year": 2022,
        "journal": "Frontiers in immunology",
        "pubtype": ["Journal Article", "Meta-Analysis", "Systematic Review"],
        "source": "curated",
    },
    "38555190": {
        "pmid": "38555190",
        "title": "N-acetylcysteine Treatment in Chronic Obstructive Pulmonary Disease (COPD) and Chronic Bronchitis.",
        "year": 2024,
        "journal": "Archivos de bronconeumologia",
        "pubtype": ["Journal Article", "Meta-Analysis"],
        "source": "curated",
    },
    "40662882": {
        "pmid": "40662882",
        "title": "Melatonin Use in the ICU: A Systematic Review and Meta-Analysis.",
        "year": 2025,
        "journal": "Critical care medicine",
        "pubtype": ["Journal Article", "Meta-Analysis", "Systematic Review"],
        "source": "curated",
    },
}

PATCHES = {
    "Кофеин":   {"remove": ["20464765"], "add": ["36870101"]},
    "Родиола":  {"remove": ["21036578"], "add": ["41080184"]},
    "Куркумин": {"remove": ["23076948"], "add": ["35935936"]},
    "NAC":      {"remove": ["22972094"], "add": ["38555190"]},
    "Мелатонин":{"remove": ["24802882"], "add": ["40662882"]},
}

d = json.loads(DATA.read_text(encoding="utf-8"))
print()

for cid, patch in PATCHES.items():
    c = next((x for x in d if x["id"] == cid), None)
    if not c:
        print(f"❌ {cid}")
        continue
    ks = c.get("key_sources") or []
    print(f"=== {cid} ===")
    print(f"  было: {[x.get('pmid') for x in ks]}")
    ks = [x for x in ks if str(x.get("pmid")) not in patch["remove"]]
    for p in patch["add"]:
        if p in NEW_SOURCES:
            ks.append(NEW_SOURCES[p])
    c["key_sources"] = ks
    print(f"  стало: {[x.get('pmid') for x in ks]}\n")

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(DATA, DATA.with_suffix(f".json.bak-{ts}"))
DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[OK] Бэкап: {DATA.with_suffix(f'.json.bak-{ts}').name}")
print(f"[OK] Записано: {DATA}")
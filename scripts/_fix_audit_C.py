"""Группа C аудита — обновление key_sources.

Магний: - 16856052 (2006) + 35184264 (2023, сон) + 38970118 (2024, мышцы)
Витамин D: - 24729336/24953955 (2014) + 42161415 (2026) + 39993397 (2025)
B9: - 20927767 (2010, дубль)
Витамин C: без изменений (свежих МА нет)
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"

NEW_SOURCES = {
    "35184264": {
        "pmid": "35184264",
        "title": "The Role of Magnesium in Sleep Health: a Systematic Review of Available Literature.",
        "year": 2023,
        "journal": "Biological trace element research",
        "pubtype": ["Journal Article", "Systematic Review"],
    },
    "38970118": {
        "pmid": "38970118",
        "title": "Effects of magnesium supplementation on muscle soreness in different type of physical activities.",
        "year": 2024,
        "journal": "Journal of translational medicine",
        "pubtype": ["Journal Article", "Systematic Review"],
    },
    "42161415": {
        "pmid": "42161415",
        "title": "Calcium, vitamin D, or combined supplementation to prevent fractures and falls: systematic review and meta-analysis.",
        "year": 2026,
        "journal": "BMJ (Clinical research ed.)",
        "pubtype": ["Journal Article", "Systematic Review", "Meta-Analysis"],
    },
    "39993397": {
        "pmid": "39993397",
        "title": "Vitamin D supplementation to prevent acute respiratory infections: systematic review and meta-analysis.",
        "year": 2025,
        "journal": "The lancet. Diabetes & endocrinology",
        "pubtype": ["Journal Article", "Systematic Review", "Meta-Analysis"],
    },
    "39077939": {
        "pmid": "39077939",
        "title": "Vitamin D supplementation for women during pregnancy.",
        "year": 2024,
        "journal": "The Cochrane database of systematic reviews",
        "pubtype": ["Journal Article", "Systematic Review", "Meta-Analysis"],
    },
}

PATCHES = {
    "Магний": {
        "remove_pmids": ["16856052"],
        "add_pmids": ["35184264", "38970118"],
    },
    "Витамин D": {
        "remove_pmids": ["24729336", "24953955"],
        "add_pmids": ["42161415", "39993397", "39077939"],
    },
    "B9": {
        "remove_pmids": ["20927767"],
        "add_pmids": [],
    },
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

    ks = [x for x in ks if str(x.get("pmid")) not in patch["remove_pmids"]]
    for p in patch["add_pmids"]:
        if p in NEW_SOURCES:
            ks.append(NEW_SOURCES[p])
    c["key_sources"] = ks
    print(f"  стало: {[x.get('pmid') for x in ks]}\n")

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
shutil.copy2(DATA, DATA.with_suffix(f".json.bak-{ts}"))
DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[OK] Бэкап: {DATA.with_suffix(f'.json.bak-{ts}').name}")
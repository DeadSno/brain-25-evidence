# scripts/enrich_doi_pmc.py
"""Preprint из DOI prefix + PMC ID из index.json.

DOI префиксы препринтов:
  10.1101  — bioRxiv, medRxiv
  10.21203 — Research Square
  10.31219 — OSF Preprints
  10.2139  — SSRN
  10.48550 — arXiv
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
PMC_INDEX = ROOT / "data" / "pmc" / "index.json"

PREPRINT_PREFIXES = {
    "10.1101": "biorxiv/medrxiv",
    "10.21203": "research-square",
    "10.31219": "osf",
    "10.2139": "ssrn",
    "10.48550": "arxiv",
    "10.31234": "psyarxiv",
}

papers = json.loads(PAPERS.read_text(encoding="utf-8"))

# PMC index → {pmid: {pmcid, ...}} или список
pmc_map: dict = {}
if PMC_INDEX.exists():
    idx = json.loads(PMC_INDEX.read_text(encoding="utf-8"))
    if isinstance(idx, list):
        for item in idx:
            if isinstance(item, dict) and item.get("pmid"):
                pmc_map[str(item["pmid"])] = item.get("pmcid")
    elif isinstance(idx, dict):
        pmc_map = idx
print(f"PMC index: {len(pmc_map)} записей")

counts = Counter()
preprint_counts = Counter()

for pmid, p in papers.items():
    doi = (p.get("doi") or "").lower()
    is_preprint = False
    server = None
    for prefix, srv in PREPRINT_PREFIXES.items():
        if doi.startswith(prefix + "/"):
            is_preprint = True
            server = srv
            break
    p["is_preprint"] = is_preprint
    p["preprint_server"] = server

    pmcid = pmc_map.get(str(pmid)) or pmc_map.get(pmid)
    p["pmcid"] = pmcid

    counts["total"] += 1
    if is_preprint:
        preprint_counts[server] += 1
        counts["preprint"] += 1
    if pmcid:
        counts["pmc"] += 1

PAPERS.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n[OK] {PAPERS}")
print(f"     Всего:      {counts['total']}")
print(f"     Препринты:  {counts['preprint']} ({counts['preprint']/counts['total']*100:.2f}%)")
for srv, cnt in preprint_counts.most_common():
    print(f"       {srv}: {cnt}")
print(f"     PMC:        {counts['pmc']} ({counts['pmc']/counts['total']*100:.1f}%)")
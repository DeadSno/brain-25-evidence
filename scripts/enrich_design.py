# scripts/enrich_design.py
"""Определить study design из publication types.

Пишет: design = 'rct'|'meta-analysis'|'systematic-review'|'review'|
                 'observational'|'case_report'|'in_vitro'|'other'
"""
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"

RCT = {"randomized controlled trial", "controlled clinical trial",
       "clinical trial, phase i", "clinical trial, phase ii",
       "clinical trial, phase iii", "clinical trial, phase iv",
       "clinical trial"}
MA = {"meta-analysis"}
SR = {"systematic review"}
REVIEW = {"review", "research support, n.i.h., extramural", "research support, non-u.s. gov't"}
OBS = {"observational study", "comparative study", "evaluation study",
       "multicenter study", "validation study", "clinical study"}
CASE = {"case reports"}

papers = json.loads(PAPERS.read_text(encoding="utf-8"))
counts = Counter()

for p in papers.values():
    pubtype = p.get("pubtype") or []
    if isinstance(pubtype, str):
        pubtype = [pubtype]
    pt = {t.lower().strip() for t in pubtype}

    if pt & MA:
        design = "meta-analysis"
    elif pt & SR:
        design = "systematic-review"
    elif pt & RCT:
        design = "rct"
    elif pt & CASE:
        design = "case-report"
    elif pt & OBS:
        design = "observational"
    elif pt & REVIEW:
        design = "review"
    else:
        design = "other"

    p["design"] = design
    counts[design] += 1

PAPERS.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"[OK] {PAPERS}")
print(f"\nРаспределение по design:")
total = len(papers)
for d, cnt in counts.most_common():
    print(f"  {d:20s}: {cnt:6d} ({cnt/total*100:.1f}%)")
"""A3.5.2: ClinicalTrials mapping — NCT IDs из abstracts + full texts."""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
PMC_TEXT = ROOT / "data" / "pmc" / "text"
OUT = ROOT / "data" / "papers" / "trials_links.json"

NCT_RE = re.compile(r"\b(NCT\d{8})\b")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fulltexts", action="store_true")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    links: dict = {}
    all_ncts: Counter = Counter()

    for pmid, p in papers.items():
        text = p.get("abstract") or ""
        ncts = set(NCT_RE.findall(text))
        if ncts:
            links[pmid] = sorted(ncts)
            for n in ncts:
                all_ncts[n] += 1

    if args.fulltexts and PMC_TEXT.exists():
        for txt in PMC_TEXT.glob("*.txt"):
            pmid = txt.stem
            content = txt.read_text(encoding="utf-8", errors="ignore")
            ncts = set(NCT_RE.findall(content))
            if ncts:
                existing = set(links.get(pmid, []))
                merged = sorted(existing | ncts)
                links[pmid] = merged
                for n in ncts:
                    if n not in existing:
                        all_ncts[n] += 1

    OUT.write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {OUT}")
    print(f"     Papers с NCT: {len(links)} / {len(papers)} ({len(links)/len(papers)*100:.1f}%)")
    print(f"     Уникальных NCT: {len(all_ncts)}")
    print(f"\nТоп-5 NCT:")
    for nct, cnt in all_ncts.most_common(5):
        print(f"  {nct}: {cnt}")


if __name__ == "__main__":
    sys.exit(main())
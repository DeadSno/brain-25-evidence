"""A3.5.3: Sample sizes из abstracts (и full texts).

Regex n=NNN, participants=NNN, NNN subjects, NNN patients."""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
PMC_TEXT = ROOT / "data" / "pmc" / "text"
OUT = ROOT / "data" / "papers" / "sample_sizes.json"

# Несколько паттернов
PATTERNS = [
    re.compile(r"\bn\s*=\s*(\d{2,7})\b"),
    re.compile(r"\bN\s*=\s*(\d{2,7})\b"),
    re.compile(r"\b(\d{2,7})\s+(?:participants|subjects|patients|volunteers|individuals|adults|children)\b"),
    re.compile(r"\btotal\s+of\s+(\d{2,7})\b"),
    re.compile(r"\b(\d{2,7})\s+(?:men|women)\b"),
]


def extract(text: str) -> list[int]:
    sizes = []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            try:
                n = int(m.group(1))
                if 5 <= n <= 5_000_000:
                    sizes.append(n)
            except Exception:
                pass
    return sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fulltexts", action="store_true")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    out: dict = {}
    all_sizes: list[int] = []

    for pmid, p in papers.items():
        text = (p.get("abstract") or "")
        sizes = extract(text)
        if sizes:
            out[pmid] = {
                "abstract": {"min": min(sizes), "max": max(sizes), "all": sizes[:10]},
            }
            all_sizes.extend(sizes)

    if args.fulltexts and PMC_TEXT.exists():
        for txt in PMC_TEXT.glob("*.txt"):
            pmid = txt.stem
            content = txt.read_text(encoding="utf-8", errors="ignore")
            sizes = extract(content)
            if sizes:
                if pmid in out:
                    out[pmid]["fulltext"] = {"min": min(sizes), "max": max(sizes), "all": sizes[:20]}
                else:
                    out[pmid] = {"fulltext": {"min": min(sizes), "max": max(sizes), "all": sizes[:20]}}
                all_sizes.extend(sizes)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {OUT}")
    print(f"     Papers с N: {len(out)} / {len(papers)}")
    print(f"     Всего найдено N: {len(all_sizes)}")

    if all_sizes:
        import statistics
        sorted_sizes = sorted(all_sizes)
        n = len(sorted_sizes)
        print(f"\nРаспределение N:")
        print(f"  Медиана: {statistics.median(sorted_sizes):.0f}")
        print(f"  25%:     {sorted_sizes[n//4]}")
        print(f"  75%:     {sorted_sizes[3*n//4]}")
        print(f"  Максимум: {sorted_sizes[-1]}")


if __name__ == "__main__":
    sys.exit(main())
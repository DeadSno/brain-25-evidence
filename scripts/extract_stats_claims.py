"""A3.5.4: Statistical claims из abstracts (p-values, CI, effect sizes)."""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
PMC_TEXT = ROOT / "data" / "pmc" / "text"
OUT = ROOT / "data" / "papers" / "stats_claims.json"

P_VALUE_RE = re.compile(r"\bp\s*[<=>]\s*0?\.(\d{2,4})\b", re.IGNORECASE)
CI_RE = re.compile(r"\b(95\s*%?\s*(?:confidence interval|CI))\b", re.IGNORECASE)
EFFECT_RE = re.compile(r"\b(hedges'?\s*g|cohen'?s?\s*d|odds\s+ratio|risk\s+ratio|hazard\s+ratio|OR|RR|HR)\b", re.IGNORECASE)
SIG_RE = re.compile(r"\b(significant(?:ly)?|non-?significant|no\s+significant)\b", re.IGNORECASE)


def extract(text: str) -> dict:
    p_values = P_VALUE_RE.findall(text)
    # Нормализуем: 05 → 0.05
    p_values = ["0." + p for p in p_values]

    has_ci = bool(CI_RE.search(text))
    effects = [m.group(0).lower() for m in EFFECT_RE.finditer(text)]
    sig = [m.group(0).lower() for m in SIG_RE.finditer(text)]

    return {
        "p_values": p_values[:20],
        "has_ci": has_ci,
        "effects": list(set(effects))[:10],
        "significance_terms": list(set(sig))[:5],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fulltexts", action="store_true")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    out: dict = {}
    stats = {
        "with_p": 0,
        "with_ci": 0,
        "with_effects": 0,
        "p_distribution": Counter(),
    }

    def process(pmid, text, src):
        if not text:
            return
        r = extract(text)
        if pmid not in out:
            out[pmid] = {}
        out[pmid][src] = r
        if r["p_values"]:
            stats["with_p"] += 1
            for p in r["p_values"][:3]:
                stats["p_distribution"][p] += 1
        if r["has_ci"]:
            stats["with_ci"] += 1
        if r["effects"]:
            stats["with_effects"] += 1

    for pmid, p in papers.items():
        process(pmid, p.get("abstract") or "", "abstract")

    if args.fulltexts and PMC_TEXT.exists():
        for txt in PMC_TEXT.glob("*.txt"):
            process(txt.stem, txt.read_text(encoding="utf-8", errors="ignore"), "fulltext")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {OUT}")
    print(f"     Papers с данными: {len(out)}")
    print(f"     С p-value: {stats['with_p']}")
    print(f"     С 95% CI: {stats['with_ci']}")
    print(f"     С effect size: {stats['with_effects']}")
    print(f"\nТоп-10 p-values (как публикуют):")
    for p, n in stats["p_distribution"].most_common(10):
        print(f"  p={p}: {n}")


if __name__ == "__main__":
    sys.exit(main())
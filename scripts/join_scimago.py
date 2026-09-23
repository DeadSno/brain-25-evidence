"""A3.5.5: Присоединить SCImago к papers.

Стратегия матчинга (по очереди):
  1. journal (в papers) → NLM by_abbrev → full title → SCImago by_title
  2. journal → NLM by_abbrev → ISSN → SCImago by_issn
  3. journal (lower) → SCImago by_title напрямую (для полных названий)

Добавляет: sjr_quartile, sjr_score, scimago_h_index, scimago_publisher,
scimago_country.

Использование:
    python scripts\\join_scimago.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "data" / "papers" / "papers.json"
SCIMAGO = ROOT / "data" / "journals" / "scimago.json"
NLM = ROOT / "data" / "journals" / "nlm_catalog.json"


def norm_title(t: str) -> str:
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"\s*\([^)]*\)", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t.startswith("the "):
        t = t[4:]
    return t


def norm_abbrev(t: str) -> str:
    """'Int J Mol Sci' → 'int j mol sci'. Убираем точки, лишние пробелы."""
    if not t:
        return ""
    t = t.lower().strip().rstrip(".")
    t = re.sub(r"\s+", " ", t)
    return t


def main() -> int:
    if not PAPERS.exists():
        print(f"[ERROR] {PAPERS} не найден", file=sys.stderr)
        return 1
    if not SCIMAGO.exists():
        print(f"[ERROR] {SCIMAGO} не найден", file=sys.stderr)
        return 1
    if not NLM.exists():
        print(f"[ERROR] {NLM} не найден. Запусти: python scripts\\fetch_nlm_catalog.py", file=sys.stderr)
        return 1

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    scimago = json.loads(SCIMAGO.read_text(encoding="utf-8"))
    nlm = json.loads(NLM.read_text(encoding="utf-8"))

    # SCImago по нормализованному названию
    scimago_by_title_norm: dict = {}
    for title, rec in scimago.get("by_title", {}).items():
        scimago_by_title_norm[norm_title(title)] = rec

    scimago_by_issn = scimago.get("by_issn", {})
    nlm_by_abbrev = nlm.get("by_abbrev", {})

    print(f"SCImago: {len(scimago_by_title_norm)} названий, {len(scimago_by_issn)} ISSN")
    print(f"NLM:     {len(nlm_by_abbrev)} аббревиатур")
    print(f"Papers:  {len(papers)}\n")

    matched = 0
    total = 0
    seen_journals: set[str] = set()
    match_method = Counter()

    for pmid, p in papers.items():
        total += 1
        journal = p.get("journal")
        if not journal:
            p["sjr_quartile"] = None
            continue
        seen_journals.add(journal)
        rec = None
        method = None

        # 1. Аббревиатура → NLM → full title → SCImago
        nlm_rec = nlm_by_abbrev.get(norm_abbrev(journal))
        if nlm_rec:
            rec = scimago_by_title_norm.get(norm_title(nlm_rec["title"]))
            if rec:
                method = "abbrev→nlm→title"

            # 2. Аббревиатура → NLM → ISSN → SCImago
            if not rec:
                for issn_key in (nlm_rec.get("issn_print"), nlm_rec.get("issn_online")):
                    if not issn_key:
                        continue
                    issn_clean = issn_key.replace("-", "")
                    rec = scimago_by_issn.get(issn_clean)
                    if rec:
                        method = "abbrev→nlm→issn"
                        break

        # 3. Прямой матч по полному названию (для уже полных названий)
        if not rec:
            rec = scimago_by_title_norm.get(norm_title(journal))
            if rec:
                method = "title"

        if rec:
            p["sjr_quartile"] = rec.get("quartile")
            p["sjr_score"] = rec.get("sjr")
            p["scimago_h_index"] = rec.get("h_index")
            p["scimago_publisher"] = rec.get("publisher")
            p["scimago_country"] = rec.get("country")
            matched += 1
            match_method[method] += 1
        else:
            p.setdefault("sjr_quartile", None)

    PAPERS.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[OK] {PAPERS}")
    print(f"     Всего papers:       {total}")
    print(f"     Уникальных журналов: {len(seen_journals)}")
    print(f"     Сматчено:            {matched} ({matched / total * 100:.1f}%)")
    print(f"\nМетод матчинга:")
    for m, cnt in match_method.most_common():
        print(f"  {m:25s}: {cnt:6d}")

    q = Counter(p.get("sjr_quartile") for p in papers.values())
    print(f"\nКвартили:")
    for k in ["Q1", "Q2", "Q3", "Q4", "-", None]:
        v = q.get(k, 0)
        if v:
            label = k if k else "(не найдено)"
            print(f"  {label:15}: {v:6d} ({v / total * 100:.1f}%)")

    pub = Counter(
        p.get("scimago_publisher") for p in papers.values()
        if p.get("scimago_publisher")
    )
    print(f"\nТоп-10 издателей:")
    for name, n in pub.most_common(10):
        print(f"  {n:6d}× {name}")

    countries = Counter(
        p.get("scimago_country") for p in papers.values()
        if p.get("scimago_country")
    )
    print(f"\nТоп-10 стран:")
    for name, n in countries.most_common(10):
        print(f"  {n:6d}× {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
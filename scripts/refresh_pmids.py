"""Предлагает свежие PMIDs для устаревших key_sources.

Для указанных карточек делает esearch по pubmed_term + фильтр
'meta-analysis[pt] OR systematic review[pt]' за последние 5 лет.

Использование:
    python scripts/refresh_pmids.py              # dry-run
    python scripts/refresh_pmids.py Магний       # одна карточка
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
TERMS_JSON = ROOT / "docs" / "data_pubmed_terms.json"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAILTO = "brain25-evidence@users.noreply.github.com"

# Карточки с устаревшими PMIDs (D1 аудита)
TARGETS = ["Кофеин", "Родиола", "Куркумин", "NAC", "Мелатонин"]


def _get(url: str, retries: int = 3) -> str:
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": "brain25-evidence/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError(f"Failed: {url}")


def esearch(term: str, retmax: int = 10) -> list[str]:
    q = urllib.parse.quote(term)
    url = (f"{EUTILS}/esearch.fcgi?db=pubmed&term={q}"
           f"&retmode=json&retmax={retmax}&sort=relevance"
           f"&email={urllib.parse.quote(MAILTO)}")
    raw = _get(url)
    return json.loads(raw).get("esearchresult", {}).get("idlist", [])


def esummary(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}
    ids = ",".join(pmids)
    url = (f"{EUTILS}/esummary.fcgi?db=pubmed&id={ids}&retmode=json"
           f"&email={urllib.parse.quote(MAILTO)}")
    raw = _get(url)
    res = json.loads(raw).get("result", {})
    out = {}
    for p in pmids:
        info = res.get(p, {})
        out[p] = {
            "title": info.get("title", "?"),
            "year": (info.get("pubdate") or "?")[:4],
            "journal": info.get("fulljournalname", "?"),
            "pubtype": info.get("pubtype", []),
        }
    return out


def base_from_term(term: str) -> str:
    import re
    m = re.match(r"^(.*?)\s+AND\s+\(", term, re.IGNORECASE)
    return m.group(1).strip() if m else term


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("card", nargs="?", help="одна карточка")
    args = ap.parse_args()

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    terms = json.loads(TERMS_JSON.read_text(encoding="utf-8"))

    targets = [args.card] if args.card else TARGETS

    for cid in targets:
        c = next((x for x in data if x["id"] == cid), None)
        if not c:
            print(f"\n❌ {cid} не найдена")
            continue

        print(f"\n{'='*70}")
        print(f"### {cid}")
        print(f"{'='*70}")
        print("Текущие key_sources:")
        for ks in (c.get("key_sources") or []):
            print(f"  {ks.get('year')}  PMID {ks.get('pmid')}  {ks.get('title','')[:70]}")

        term = terms.get(cid, "")
        base = base_from_term(term)

        # Ищем свежие МА за последние 5 лет
        q = f'({base}) AND (meta-analysis[pt] OR systematic review[pt]) AND 2021:2026[dp]'
        print(f"\nEsearch: {q[:120]}…")
        pmids = esearch(q, retmax=5)
        time.sleep(0.5)

        if not pmids:
            print("  ⚠️ Не найдено свежих МА")
            continue

        meta = esummary(pmids)
        print(f"\nКандидаты (5 свежих):")
        for p in pmids:
            info = meta.get(p, {})
            types = ", ".join(info.get("pubtype", []))[:60]
            print(f"  PMID {p} ({info['year']}) [{types}]")
            print(f"    {info['title'][:90]}")
            print(f"    {info['journal'][:80]}")
        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
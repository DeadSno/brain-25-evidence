"""Поиск свежих PMIDs для 14 карточек с устаревшими key_sources.

Для каждой карточки: esearch по pubmed_term + фильтр МА/SR 2021-2026.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))
TERMS = json.loads((ROOT / "docs" / "data_pubmed_terms.json").read_text(encoding="utf-8"))

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAILTO = "brain25-evidence@users.noreply.github.com"

TARGETS = [
    "Гуперзин А", "Тирозин", "Пикногенол", "Валериана", "Зверобой",
    "5-HTP", "Глюкозамин + хондроитин", "Боярышник", "Мака", "Пажитник",
    "Кордицепс", "Рейши", "Хлорофилл", "Глутамин",
]


def _get(url, retries=3):
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
    raise RuntimeError(url)


def esearch(term, retmax=8):
    q = urllib.parse.quote(term)
    url = (f"{EUTILS}/esearch.fcgi?db=pubmed&term={q}"
           f"&retmode=json&retmax={retmax}&sort=relevance"
           f"&email={urllib.parse.quote(MAILTO)}")
    return json.loads(_get(url)).get("esearchresult", {}).get("idlist", [])


def esummary(pmids):
    if not pmids:
        return {}
    url = (f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(pmids)}"
           f"&retmode=json&email={urllib.parse.quote(MAILTO)}")
    res = json.loads(_get(url)).get("result", {})
    return {p: {
        "title": res.get(p, {}).get("title", "?")[:90],
        "year": (res.get(p, {}).get("pubdate") or "?")[:4],
        "journal": res.get(p, {}).get("fulljournalname", "?")[:60],
        "pubtype": res.get(p, {}).get("pubtype", []),
    } for p in pmids}


def base_from_term(term):
    import re
    m = re.match(r"^(.*?)\s+AND\s+\(", term, re.IGNORECASE)
    return m.group(1).strip() if m else term


by_id = {c["id"]: c for c in DATA}

for cid in TARGETS:
    c = by_id.get(cid)
    if not c:
        print(f"\n❌ {cid} — нет карточки")
        continue
    term = TERMS.get(cid, "")
    if not term:
        print(f"\n❌ {cid} — нет pubmed_term")
        continue
    base = base_from_term(term)

    print(f"\n{'='*70}")
    print(f"### {cid}")
    print(f"{'='*70}")
    print(f"Текущие: {[k.get('pmid') for k in (c.get('key_sources') or [])]}")

    q = f'({base}) AND (meta-analysis[pt] OR systematic review[pt]) AND 2021:2026[dp]'
    print(f"Query: {q[:110]}…")
    pmids = esearch(q, retmax=6)
    time.sleep(0.5)

    if not pmids:
        print("  ⚠️ Свежих МА/SR НЕТ — оставляем старые")
        continue

    meta = esummary(pmids)
    for p in pmids:
        info = meta.get(p, {})
        print(f"  ✅ {info['year']}  PMID {p}  [{', '.join(info['pubtype'])[:40]}]")
        print(f"     {info['title']}")
    time.sleep(0.5)
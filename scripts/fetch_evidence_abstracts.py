"""Готовит заготовки reports/evidence/{id}.md с abstracts из PubMed.

Не заполняет adv-поля — только тянет top-3 MA + abstracts.

Использование:
    python scripts/fetch_evidence_abstracts.py --name "B1"
    python scripts/fetch_evidence_abstracts.py --all   # все из _drafts.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DRAFTS = ROOT / "docs" / "_drafts.json"
TERMS = ROOT / "docs" / "data_pubmed_terms.json"
EVIDENCE = ROOT / "reports" / "evidence"

EMAIL = "brain25-evidence@users.noreply.github.com"
HEADERS = {"User-Agent": f"brain-25-evidence/1.0 (mailto:{EMAIL})"}

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def esearch(query: str, n: int = 5) -> list[str]:
    r = requests.get(ESEARCH, params={
        "db": "pubmed", "term": query, "retmode": "json",
        "retmax": n, "sort": "relevance",
        "tool": "brain-25-evidence", "email": EMAIL,
    }, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]


def efetch_abstracts(pmids: list[str]) -> dict[str, dict]:
    """Возвращает {pmid: {title, journal, year, abstract}}."""
    if not pmids:
        return {}
    r = requests.get(EFETCH, params={
        "db": "pubmed", "id": ",".join(pmids),
        "retmode": "xml", "rettype": "abstract",
        "tool": "brain-25-evidence", "email": EMAIL,
    }, headers=HEADERS, timeout=60)
    r.raise_for_status()

    from xml.etree import ElementTree as ET
    root = ET.fromstring(r.text)

    out = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        if pmid_el is None:
            continue
        pmid = pmid_el.text

        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()) if title_el is not None else ""

        journal_el = art.find(".//Journal/Title")
        journal = journal_el.text if journal_el is not None else ""

        year_el = art.find(".//PubDate/Year")
        year = year_el.text if year_el is not None else ""

        abstract_parts = []
        for ab in art.findall(".//Abstract/AbstractText"):
            label = ab.get("Label", "")
            text = "".join(ab.itertext())
            if label:
                abstract_parts.append(f"[{label}] {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        out[pmid] = {
            "title": title,
            "journal": journal,
            "year": year,
            "abstract": abstract,
        }
    return out


def make_skeleton(name: str, query: str) -> str:
    """Создаёт markdown-заготовку."""
    ma_query = f'({query}) AND ("meta-analysis"[pt] OR "systematic review"[pt])'
    pmids = esearch(ma_query, n=3)
    time.sleep(0.4)
    abstracts = efetch_abstracts(pmids)

    lines = [
        f"# Evidence check: {name}",
        "",
        "- grade: _TBD_",
        "- verdict: _TBD_",
        "- scienceIndex: _TBD_ | metaCount: _TBD_",
        "- key_sources: _TBD_",
        "",
        "## Поля карточки (для сверки с abstracts)",
        "",
        "### about",
        "_TBD_",
        "",
        "### who_needs",
        "_TBD_",
        "",
        "### onset",
        "_TBD_",
        "",
        "### myths",
        "_TBD_",
        "",
        "### food_sources",
        "_TBD_",
        "",
        "### guidelines",
        "_TBD_",
        "",
        "### how_to_choose",
        "_TBD_",
        "",
        "## Abstracts (PubMed)",
        "",
    ]

    for pmid in pmids:
        a = abstracts.get(pmid, {})
        if not a:
            continue
        lines.append(f"### PMID [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
        lines.append(f"**{a['title']}** — _{a['journal']}, {a['year']}_")
        lines.append("")
        lines.append(f"> {a['abstract'][:2500]}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="Имя добавки (например, B1)")
    ap.add_argument("--all", action="store_true", help="Все из _drafts.json")
    args = ap.parse_args()

    if not args.name and not args.all:
        ap.print_help()
        return 1

    terms = json.loads(TERMS.read_text(encoding="utf-8"))

    if args.all:
        drafts = json.loads(DRAFTS.read_text(encoding="utf-8"))
        names = [d["name"] for d in drafts]
    else:
        names = [args.name]

    EVIDENCE.mkdir(parents=True, exist_ok=True)

    for name in names:
        query = terms.get(name)
        if not query:
            print(f"[SKIP] {name}: нет в data_pubmed_terms.json")
            continue
        print(f"[{name}] Тяну top-3 MA...")
        try:
            md = make_skeleton(name, query)
            out = EVIDENCE / f"{name}.md"
            out.write_text(md, encoding="utf-8")
            print(f"  [OK] {out}")
        except Exception as e:
            print(f"  [ERR] {name}: {e}")
        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
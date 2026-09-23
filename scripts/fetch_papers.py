"""A3.1: Papers entity — все PMIDs по 94 добавкам.

Делает 3 запроса на добавку + 2 батч-запроса на метаданные/абстракты.
Кэшируется: повторный прогон докачивает только новое.

Выход:
  data/papers/papers.json          — все уникальные статьи (метаданные + abstract)
  data/papers/paper_supplement.json — {pmid: [supplement_ids]}
  data/papers/stats.json           — агрегаты (журналы, авторы, pubtype, годы)

Использование:
    python scripts\\fetch_papers.py --limit 5             # тест на 5 добавках
    python scripts\\fetch_papers.py --only "Креатин"      # одна добавка
    python scripts\\fetch_papers.py                       # все 94
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import SUPPLEMENTS, MAILTO  # noqa: E402

OUT_DIR = ROOT / "data" / "papers"
TERMS_FILE = ROOT / "docs" / "data_pubmed_terms.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

RATE_DELAY = 0.34  # ~3 req/s без API key
BATCH = 200
RETMAX = 500  # максимум PMIDs на добавку

PUBTYPE_WHITELIST = {
    "Meta-Analysis", "Systematic Review", "Randomized Controlled Trial",
    "Review", "Clinical Trial", "Journal Article",
}


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"brain25-papers/1.0 ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def esearch_pmids(term: str, retmax: int = RETMAX) -> list[str]:
    """PMID список по запросу (сортировка по relevance)."""
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "retmode": "json",
        "sort": "relevance",
        "tool": "brain25-papers",
        "email": MAILTO,
    }
    url = f"{ESEARCH}?{urllib.parse.urlencode(params)}"
    try:
        data = json.loads(http_get(url))
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"    [esearch ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return []


def esummary_batch(pmids: list[str]) -> dict:
    """Метаданные для батча PMIDs. Возвращает {pmid: {...}}."""
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        "tool": "brain25-papers",
        "email": MAILTO,
    }
    url = f"{ESUMMARY}?{urllib.parse.urlencode(params)}"
    try:
        data = json.loads(http_get(url))
        result = data.get("result", {})
        out = {}
        for pmid in result.get("uids", []):
            item = result.get(pmid, {})
            authors = []
            for a in item.get("authors", []):
                name = a.get("name")
                if name:
                    authors.append(name)
            pubtypes = [p for p in item.get("pubtype", []) if p in PUBTYPE_WHITELIST]
            doi = None
            for aid in item.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value")
                    break
            out[pmid] = {
                "title": item.get("title", "").rstrip("."),
                "authors": authors[:10],  # первые 10, чтобы не раздувать
                "journal": item.get("source", ""),
                "year": _parse_year(item.get("pubdate", "")),
                "pubtype": pubtypes,
                "doi": doi,
            }
        return out
    except Exception as e:
        print(f"    [esummary ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return {}


def efetch_abstracts_batch(pmids: list[str]) -> dict:
    """Абстракты для батча PMIDs. Возвращает {pmid: abstract_text}."""
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool": "brain25-papers",
        "email": MAILTO,
    }
    url = f"{EFETCH}?{urllib.parse.urlencode(params)}"
    try:
        xml_bytes = http_get(url, timeout=60)
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        print(f"    [efetch ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return {}

    out = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//MedlineCitation/PMID")
        if pmid_el is None or not pmid_el.text:
            continue
        pmid = pmid_el.text.strip()
        abstract_el = art.find(".//Article/Abstract")
        if abstract_el is None:
            out[pmid] = ""
            continue
        parts = []
        for at in abstract_el.findall("AbstractText"):
            label = at.get("Label", "")
            text = "".join(at.itertext()).strip()
            if not text:
                continue
            parts.append(f"{label}: {text}" if label else text)
        out[pmid] = "\n\n".join(parts)
    return out


def _parse_year(pubdate: str) -> int | None:
    if not pubdate:
        return None
    # "2026 Jan-Feb" / "2026" / "2025 Dec 15"
    parts = pubdate.split()
    for p in parts[:1]:
        if p.isdigit() and 1900 <= int(p) <= 2100:
            return int(p)
    return None


def fetch_one(name: str, term: str) -> tuple[list[str], dict, dict]:
    """(pmids, meta, abstracts) для одной добавки."""
    print(f"— {name}")
    pmids = esearch_pmids(term)
    print(f"    esearch: {len(pmids)} PMIDs")
    time.sleep(RATE_DELAY)

    if not pmids:
        return [], {}, {}

    meta: dict = {}
    abstracts: dict = {}
    total_batches = (len(pmids) + BATCH - 1) // BATCH

    for i in range(0, len(pmids), BATCH):
        batch = pmids[i:i+BATCH]
        bn = i // BATCH + 1
        meta.update(esummary_batch(batch))
        time.sleep(RATE_DELAY)
        abstracts.update(efetch_abstracts_batch(batch))
        time.sleep(RATE_DELAY)
        print(f"    batch {bn}/{total_batches}: +{len(batch)} (meta={len(meta)}, abs={len(abstracts)})")

    return pmids, meta, abstracts


def build_stats(papers: dict, paper_supp: dict) -> dict:
    journals = Counter()
    authors = Counter()
    pubtypes = Counter()
    years = Counter()

    for pmid, p in papers.items():
        if p.get("journal"):
            journals[p["journal"]] += 1
        for a in p.get("authors", []):
            authors[a] += 1
        for pt in p.get("pubtype", []):
            pubtypes[pt] += 1
        if p.get("year"):
            years[str(p["year"])] += 1

    return {
        "total_papers": len(papers),
        "with_abstract": sum(1 for p in papers.values() if p.get("abstract")),
        "top_journals": journals.most_common(30),
        "top_authors": authors.most_common(30),
        "by_pubtype": dict(pubtypes),
        "by_year": dict(sorted(years.items())),
        "supplements_count": len(paper_supp),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Ограничить число добавок (для теста)")
    ap.add_argument("--only", type=str, default=None, help="Одна добавка")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    papers_file = OUT_DIR / "papers.json"
    supp_file = OUT_DIR / "paper_supplement.json"

    # Загружаем кэш
    papers: dict = json.loads(papers_file.read_text(encoding="utf-8")) if papers_file.exists() else {}
    paper_supp: dict = json.loads(supp_file.read_text(encoding="utf-8")) if supp_file.exists() else {}

    terms = json.loads(TERMS_FILE.read_text(encoding="utf-8"))

    # Список добавок
    if args.only:
        if args.only not in terms:
            print(f"[ERROR] {args.only} нет в data_pubmed_terms.json", file=sys.stderr)
            return 1
        cards = [(args.only, terms[args.only])]
    else:
        all_ids = sorted(set(terms.keys()) | set(SUPPLEMENTS.keys()))
        cards = [(cid, terms.get(cid) or SUPPLEMENTS.get(cid)) for cid in all_ids]
        cards = [(cid, t) for cid, t in cards if t]

    if args.limit:
        cards = cards[: args.limit]

    print(f"Добавок: {len(cards)}")
    print(f"Кэш: papers={len(papers)}, links={sum(len(v) for v in paper_supp.values())}")
    print(f"Оценка: ~{len(cards) * 3 * RATE_DELAY / 60:.1f} мин на esearch + батчи\n")

    done = 0
    for i, (name, term) in enumerate(cards, 1):
        # Уже обработан?
        if name in paper_supp and paper_supp[name]:
            print(f"[{i}/{len(cards)}] {name}: [cached] ({len(paper_supp[name])} PMIDs)")
            done += 1
            continue

        print(f"[{i}/{len(cards)}]", end=" ")
        try:
            pmids, meta, abstracts = fetch_one(name, term)
        except Exception as e:
            print(f"  [FATAL] {name}: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        if not pmids:
            paper_supp[name] = []
            supp_file.write_text(json.dumps(paper_supp, ensure_ascii=False, indent=2), encoding="utf-8")
            continue

        # Мерджим
        for pmid in pmids:
            m = meta.get(pmid, {})
            a = abstracts.get(pmid, "")
            if pmid in papers:
                # Уже есть — только обновляем abstract если был пустой
                if not papers[pmid].get("abstract") and a:
                    papers[pmid]["abstract"] = a
            else:
                papers[pmid] = {
                    "pmid": pmid,
                    "title": m.get("title", ""),
                    "authors": m.get("authors", []),
                    "journal": m.get("journal", ""),
                    "year": m.get("year"),
                    "pubtype": m.get("pubtype", []),
                    "doi": m.get("doi"),
                    "abstract": a,
                }

        paper_supp[name] = pmids
        done += 1

        # Сохраняем после каждой добавки
        papers_file.write_text(json.dumps(papers, ensure_ascii=False, indent=2), encoding="utf-8")
        supp_file.write_text(json.dumps(paper_supp, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"    → всего уникальных papers: {len(papers)}")

    # Статистика
    stats = build_stats(papers, paper_supp)
    stats_file = OUT_DIR / "stats.json"
    stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[OK] {papers_file} — {papers_file.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"[OK] {supp_file} — {supp_file.stat().st_size / 1024:.0f} KB")
    print(f"[OK] {stats_file}")
    print(f"\nВсего papers: {stats['total_papers']}")
    print(f"С abstract:   {stats['with_abstract']}")
    print(f"Добавок:      {stats['supplements_count']}")
    print(f"\nТоп-5 журналов:")
    for j, n in stats["top_journals"][:5]:
        print(f"  {n:4d}× {j}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
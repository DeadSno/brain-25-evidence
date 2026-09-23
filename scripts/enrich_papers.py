"""A3.4.2: Дообогащение papers.json — MeSH, keywords, language, affiliation.

Через efetch XML (esummary эти поля НЕ отдаёт).

Использование:
    python scripts\\enrich_papers.py --limit 200
    python scripts\\enrich_papers.py
    python scripts\\enrich_papers.py --reset
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import MAILTO  # noqa: E402

PAPERS = ROOT / "data" / "papers" / "papers.json"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
RATE_DELAY = 0.4     # efetch тяжелее esummary
BATCH = 100          # XML большой — уменьшаем батч


def http_get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": f"brain25-enrich/1.0 ({MAILTO})"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def efetch_enriched(pmids: list[str]) -> dict:
    """Один батч efetch XML → dict {pmid: {mesh, keywords, language, affiliation}}."""
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",   # возвращает полный MedlineCitation
        "tool": "brain25-enrich",
        "email": MAILTO,
    }
    url = f"{EFETCH}?{urllib.parse.urlencode(params)}"
    try:
        xml_bytes = http_get(url)
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        return {}

    out: dict = {}
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//MedlineCitation/PMID")
        if pmid_el is None or not pmid_el.text:
            continue
        pmid = pmid_el.text.strip()

        # MeSH
        mesh = []
        for mh in art.findall(".//MeshHeadingList/MeshHeading"):
            d = mh.find("DescriptorName")
            if d is not None and d.text:
                mesh.append(d.text.strip())

        # Keywords
        keywords = []
        for kw in art.findall(".//KeywordList/Keyword"):
            if kw.text:
                keywords.append(kw.text.strip())

        # Language
        lang_el = art.find(".//Article/Language")
        language = lang_el.text.strip() if lang_el is not None and lang_el.text else "unknown"

        # Affiliation (первого автора)
        affil = ""
        for a in art.findall(".//AuthorList/Author"):
            aff = a.find("AffiliationInfo/Affiliation")
            if aff is not None and aff.text:
                affil = aff.text.strip()
                break

        out[pmid] = {
            "mesh": mesh[:30],
            "keywords": keywords[:20],
            "language": language,
            "author_affiliation": affil[:300],
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    papers = json.loads(PAPERS.read_text(encoding="utf-8"))
    pmids = sorted(papers.keys())

    if not args.reset:
        todo = [p for p in pmids if not papers[p].get("mesh")]
    else:
        todo = pmids[:]

    if args.limit:
        todo = todo[: args.limit]

    print(f"Всего papers:     {len(pmids)}")
    print(f"Без enrichment:   {len(todo)}")
    est = len(todo) / BATCH * (RATE_DELAY + 3) / 60   # +3 сек на обработку XML
    print(f"Оценка:           ~{est:.1f} мин\n")

    if not todo:
        print("[OK] Всё уже обогащено")
        return 0

    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    t0 = time.time()
    n_ok = 0

    for i, batch in enumerate(batches, 1):
        enriched = efetch_enriched(batch)
        for pmid, fields in enriched.items():
            papers[pmid].update(fields)
            n_ok += 1
        for pmid in batch:
            if pmid not in enriched:
                papers[pmid].setdefault("mesh", [])
                papers[pmid].setdefault("keywords", [])
                papers[pmid].setdefault("language", "unknown")
                papers[pmid].setdefault("author_affiliation", "")

        if i % 10 == 0:
            PAPERS.write_text(
                json.dumps(papers, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(batches) - i) / rate if rate else 0
            print(f"[{i}/{len(batches)}] enriched={n_ok} · "
                  f"{rate:.2f} batch/s · ETA {eta/60:.1f} мин")

        time.sleep(RATE_DELAY)

    PAPERS.write_text(
        json.dumps(papers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    size_mb = PAPERS.stat().st_size / 1024 / 1024
    print(f"\n[OK] {PAPERS} ({size_mb:.1f} MB)")
    print(f"     Обогащено: {n_ok} из {len(todo)}")
    print(f"     Время:     {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
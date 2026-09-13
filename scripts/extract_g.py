"""Кандидаты Hedges' g из абстрактов PubMed (данные цикла 4)."""
import re
import requests

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
G_RE = re.compile(r"(?:SMD|Hedges['’]?s?\s*g|Cohen['’]?s?\s*d|standardized mean "
                  r"difference)\s*(?:=|:)?\s*(-?\d+\.\d+)", re.I)
CI_RE = re.compile(r"95%\s*CI[^0-9-]*(-?\d+\.\d+)\s*(?:to|–|-|,)\s*(-?\d+\.\d+)", re.I)


def ma_pmids(query: str, n: int = 5) -> list[str]:
    r = requests.get(ESEARCH, params={"db": "pubmed", "retmode": "json", "retmax": n,
                                      "term": f"({query}) AND meta-analysis[pt]"}, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"].get("idlist", [])


def abstract(pmid: str) -> str:
    r = requests.get(EFETCH, params={"db": "pubmed", "id": pmid,
                                     "rettype": "abstract", "retmode": "xml"}, timeout=30)
    r.raise_for_status()
    return " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", r.text, re.S))


def year_of(pmid: str) -> str:
    """Год публикации из PubMed-записи (для очереди; не трогает candidates())."""
    r = requests.get(EFETCH, params={"db": "pubmed", "id": pmid,
                                     "rettype": "abstract", "retmode": "xml"}, timeout=30)
    r.raise_for_status()
    m = re.search(r"<PubMedPubDate PubStatus=\"pubmed\">.*?<Year>(\d{4})</Year>", r.text, re.S)
    if m:
        return m.group(1)
    m = re.search(r"<Year>(\d{4})</Year>", r.text)
    return m.group(1) if m else "?"


def candidates(sid: str, query: str) -> list[dict]:
    out = []
    for pmid in ma_pmids(query):
        text = abstract(pmid)
        m = G_RE.search(text)
        if not m:
            continue
        ci = CI_RE.search(text)
        out.append({"id": sid, "pmid": pmid, "g": float(m.group(1)),
                    "ci": [float(ci.group(1)), float(ci.group(2))] if ci else None,
                    "snippet": text[max(0, m.start() - 80):m.end() + 80]})
    return out
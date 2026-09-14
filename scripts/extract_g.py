"""Кандидаты Hedges' g из абстрактов PubMed (данные цикла 4)."""
import html
import re
import requests

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
G_RE = re.compile(r"(?:SMD|Hedges['’]?s?\s*g|Cohen['’]?s?\s*d|standardized mean "
                  r"difference)\s*(?:=|:)?\s*(-?\d+\.\d+)", re.I)
CI_RE = re.compile(
    r"(?:(?:95\s*%\s*)?(?:confidence\s+interval|C\.?\s*I\.?)"
    r"|(?:confidence\s+interval|C\.?\s*I\.?)\s*95\s*%"
    r"|95\s*%)"
    r"[^0-9+-]{0,12}"
    r"([+-]?\d+(?:\.\d+)?)\s*(?:to|–|-|,|;)\s*([+-]?\d+(?:\.\d+)?)",
    re.I)
TAG_RE = re.compile(r"<[^>]+>")

# Ключевые слова исхода: текст ИЗ АБСТРАКТА (окно вокруг g), не из запроса.
OUTCOME_TERMS = [
    "depression", "depressive", "anxiety", "pain", "fatigue", "mood",
    "memory", "attention", "sleep", "stress", "cognition", "cognitive",
    "insomnia", "quality of life", "well-being", "nausea", "headache",
    "glucose", "hba1c", "waist circumference", "disability", "concentration",
    "vigilance", "executive function", "visual memory",
    "hemoglobin", "glyc", "a1c", "ferritin", "acetate", "crp",
    "interleukin", "cortisol", "cholesterol", "triglyceride", "insulin",
    "testosterone", "homocysteine", "blood pressure", "bone",
    "strength", "power", "performance", "endurance", "exercis",
    "sleep onset", "sleep quality", "sleep latency",
    "triglycerides", "cardiovascular", "diarrhea", "bowel",
    "wound", "immune", "immunity", "collagen", "osteoarthritis",
    "bone mineral density", "bone density",
]


def _clean_text(text: str) -> str:
    """HTML-теги и entities из AbstractText → текст для G/CI/исхода."""
    return html.unescape(TAG_RE.sub(" ", text))


def ma_pmids(query: str, n: int = 5) -> list[str]:
    r = requests.get(ESEARCH, params={"db": "pubmed", "retmode": "json", "retmax": n,
                                      "term": f"({query}) AND meta-analysis[pt]"}, timeout=30)
    r.raise_for_status()
    return r.json()["esearchresult"].get("idlist", [])


def abstract(pmid: str) -> str | None:
    r = requests.get(EFETCH, params={"db": "pubmed", "id": pmid,
                                     "rettype": "abstract", "retmode": "xml"}, timeout=30)
    if r.status_code in (400, 404):
        return None  # efetch-глюк конкретного id: пропустить PMID, не валить пересборку
    r.raise_for_status()
    raw = " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", r.text, re.S))
    return _clean_text(raw)


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


def _is_range(text: str, g_end: int) -> bool:
    """SMD = x to y (диапазон), а не точечный эффект → отсечь как ложный g."""
    tail = text[g_end:g_end + 60]
    return bool(re.match(r"\s*(?:to|–|-)\s*[+-]?\d+\.\d+", tail))


def _outcome(text: str, g_start: int) -> str:
    """Исход из абстракта: термин из OUTCOME_TERMS, ближайший к g в окне ±220."""
    lo, hi = max(0, g_start - 220), min(len(text), g_start + 220)
    window = text[lo:hi]
    low = window.lower()
    best, best_d = "", None
    for term in OUTCOME_TERMS:
        i = 0
        while True:
            i = low.find(term, i)
            if i < 0:
                break
            d = abs(i - (g_start - lo))
            if best_d is None or d < best_d:
                best_d, best = d, term
            i += 1
    return best


def _paired_ci(text: str, g_start: int, g_end: int):
    """Парный CI: только тот, что ПРИМЫКАЕТ к g (после — в пределах 100,
    до — в пределах 25 символов). Чужой CI из абстракта → None. Нет CI → None."""
    lo, hi = max(0, g_start - 120), min(len(text), g_end + 160)
    window = text[lo:hi]
    for m in CI_RE.finditer(window):
        before = lo + m.start()
        after = lo + m.end()
        if g_end <= before <= g_end + 100:
            return [float(m.group(1)), float(m.group(2))]
        if g_start - 25 <= after <= g_start:
            return [float(m.group(1)), float(m.group(2))]
    return None


def candidates(sid: str, query: str) -> list[dict]:
    out = []
    seen: set[str] = set()
    for pmid in ma_pmids(query):
        if pmid in seen:
            continue
        seen.add(pmid)
        text = abstract(pmid)
        if text is None:
            continue
        m = G_RE.search(text)
        if not m:
            continue
        if _is_range(text, m.end()):
            continue
        g = float(m.group(1))
        ci = _paired_ci(text, m.start(), m.end())
        out.append({
            "id": sid, "pmid": pmid, "g": g,
            "ci": ci,
            "outcome": _outcome(text, m.start()),
            "snippet": text[max(0, m.start() - 80):m.end() + 80],
        })
    return out
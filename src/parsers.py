"""Сборщики данных: PubMed, OpenAlex."""
import time
import requests
import pandas as pd

from .config import SUPPLEMENTS, COG, EN, MAILTO, OUTCOME

EUTILS   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
OPENALEX = "https://api.openalex.org/works"


def pubmed_count(term: str) -> int:
    r = requests.get(EUTILS, params={"term": term, "retmode": "json",
                                     "email": MAILTO}, timeout=15)
    r.raise_for_status()
    time.sleep(0.35)
    return int(r.json()["esearchresult"]["count"])


def collect_pubmed() -> pd.DataFrame:
    """Полный сбор PubMed. v1.2: outcome зависит от категории добавки."""
    rows = []
    for name, q in SUPPLEMENTS.items():
        outcome = OUTCOME.get(name, COG)
        base = f"({q}) AND ({outcome})"
        rows.append({
            "добавка": name,
            "всего_публикаций": pubmed_count(base),
            "rct":            pubmed_count(f"{base} AND randomized controlled trial[pt]"),
            "мета_анализы":   pubmed_count(f"{base} AND meta-analysis[pt]"),
        })
        print(f"{name}: собрано")
    return pd.DataFrame(rows)


def openalex_count(query: str) -> int:
    try:
        r = requests.get(OPENALEX, params={"search": query, "per-page": 1,
                                           "mailto": MAILTO}, timeout=8)
        r.raise_for_status()
        time.sleep(0.35)
        return int(r.json()["meta"]["count"])
    except Exception:
        return -1


def collect_openalex(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["name_en"] = df["добавка"].map(EN)
    df["openalex_works"] = [openalex_count(f"{en} cognition") for en in df["name_en"]]
    return df

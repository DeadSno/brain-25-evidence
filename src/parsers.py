"""Сборщики данных: PubMed, OpenAlex, Wildberries."""
import re
import time
import requests
import pandas as pd

from . import config                      # модуль целиком → config.OUTCOME_V12 доступен
from .config import (SUPPLEMENTS, COG, EN, NORM,
                     WB_QUERY, MAILTO, OUTCOME_V12)

EUTILS   = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
OPENALEX = "https://api.openalex.org/works"
WB_SEARCH = "https://search.wb.ru/exactmatch/ru/common/v4/search"

GARDEN = re.compile(r"семен|сажен|рассад|грунт|агрофирм|аэлит|цвето|растен|огород", re.I)
UNIT_RE = {
    "г":    re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:грамм|граммов|г|g|гр)\b", re.I),
    "капс": re.compile(r"(\d+)\s*(?:капсул|капс|caps|capsules|таблеток|табл|таб)\b", re.I),
}


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
        # ← ИСПРАВЛЕНО: name (не sup), OUTCOME_V12 (не config.OUTCOME_V12)
        outcome = OUTCOME_V12.get(name, COG)
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


def wb_search(query: str, n: int = 12) -> pd.DataFrame:
    r = requests.get(WB_SEARCH,
                     params={"appType": 1, "curr": "rub", "dest": -1257786,
                             "query": query, "resultset": "catalog",
                             "sort": "popular", "spp": 30},
                     timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    data = r.json()
    items = data.get("products", data.get("data", {}).get("products", []))[:n]
    rows = []
    for it in items:
        sizes = it.get("sizes", [])
        if not sizes or "price" not in sizes[0]:
            continue
        price_kop = sizes[0]["price"].get("product", sizes[0]["price"].get("basic", 0))
        rows.append({"артикул": it.get("id"), "бренд": it.get("brand", ""),
                     "название": it.get("name", ""), "цена_руб": round(price_kop / 100)})
    return pd.DataFrame(rows)


def parse_units(name: str, unit: str):
    m = UNIT_RE[unit].search(name)
    if not m:
        return None
    val = float(m.group(1).replace(",", "."))
    return int(val) if val.is_integer() else val


def collect_wb_prices() -> pd.DataFrame:
    """Сбор цен WB. v1.2: новые добавки уже должны быть в WB_QUERY."""
    rows = []
    for sup, (q, unit) in WB_QUERY.items():
        try:
            offers = wb_search(q)
        except Exception as e:
            print(f"⚠️ {sup}: {type(e).__name__}")
            continue
        for _, o in offers.iterrows():
            if GARDEN.search(o["название"]):
                continue
            units = parse_units(o["название"], unit)
            if not units or units <= 0:
                continue
            rows.append({"добавка": sup, "продукт": f"{o['бренд']} {o['название']}",
                         "единиц_в_упаковке": units, "цена_упаковки": o["цена_руб"],
                         "норма_мес": NORM[sup], "источник": f"WB арт.{o['артикул']}",
                         "дата": time.strftime("%Y-%m-%d")})
        time.sleep(1.0)
    return pd.DataFrame(rows)
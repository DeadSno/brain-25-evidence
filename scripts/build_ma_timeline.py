"""v2.7-C1+C2: таймлайн мета-анализов PubMed по годам.

C1: Для каждой добавки из docs/data.json esearch по запросу, который считает
    scienceIndex (SUPPLEMENTS + OUTCOME/COG из src/config.py, фильтр
    meta-analysis[pt]) с retmax=100 → esummary пачками по 50 → год
    публикации (pubdate → year) для каждого МА → кэш
    data/processed/ma_years.json: {id: {year: count}}.

C2: docs/data_ma_timeline.json: [{year: 2015..2026, total: int,
    top: [{id, name, diff}]}] — top-5 добавок по приросту относительно
    предыдущего года.

Сон 0.4 c между запросами (PubMed без API-key). Сеть может отвечать
429/таймаутами — годы НЕ выдумываем. Добавки с ошибкой пропускаются.
Если не прошла НИ ОДНА (полный ноль) — кэш/агрегат не коммитим.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import SUPPLEMENTS, OUTCOME, COG, MAILTO  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
CACHE_PATH = ROOT / "data" / "processed" / "ma_years.json"
AGGREGATE_PATH = ROOT / "docs" / "data_ma_timeline.json"
PRICE_HIST = ROOT / "data" / "processed" / "price_history.csv"
PRICE_DOC = ROOT / "docs" / "data_price_history.json"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
SLEEP = 0.4
RETRIES = 3
MAX_YEAR = 2026
MIN_YEAR = 2010  # реально earliest for supplements; range output 2015-2026


def _get(url: str, params: dict) -> requests.Response:
    last = None
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code in (429, 500, 502, 503):
                last = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r
        except requests.RequestException as e:
            last = f"{type(e).__name__}"
        time.sleep(SLEEP * (attempt + 1))
    raise RuntimeError(f"PubMed недоступен: {last}")


def ma_query(name: str) -> str | None:
    q = SUPPLEMENTS.get(name)
    if not q:
        return None
    outcome = OUTCOME.get(name, COG)
    return f"({q}) AND ({outcome}) AND meta-analysis[pt]"


def search_pmids(term: str) -> list[str]:
    r = _get(ESEARCH, params={
        "db": "pubmed", "term": term, "retmode": "json",
        "retmax": 100, "email": MAILTO, "tool": "brain25ma_timeline",
    })
    return r.json()["esearchresult"].get("idlist", [])


def summaries(pmids: list[str]) -> dict:
    if not pmids:
        return {}
    year_counts: dict[int, int] = {}
    for i in range(0, len(pmids), 50):
        batch = pmids[i:i + 50]
        r = _get(ESUMMARY, params={
            "db": "pubmed", "retmode": "json",
            "id": ",".join(batch), "email": MAILTO,
        })
        result = r.json().get("result", {})
        for pmid in batch:
            rec = result.get(pmid)
            if not rec:
                continue
            m = re.search(r"(\d{4})", rec.get("pubdate") or "")
            if m:
                y = int(m.group(1))
                if MIN_YEAR <= y <= MAX_YEAR + 5:
                    year_counts[y] = year_counts.get(y, 0) + 1
        time.sleep(SLEEP)
    return year_counts


def build_timeline(cache: dict, id_name: dict,
                   start: int = 2015, end: int = MAX_YEAR) -> list[dict]:
    rows = []
    for year in range(start, end + 1):
        sy = str(year)
        sprev = str(year - 1)
        total = 0
        diffs = []
        for sid, years in cache.items():
            c = years.get(sy, 0)
            total += c
            prev = years.get(sprev, 0)
            diff = c - prev
            if c > 0:
                diffs.append({"id": sid, "name": id_name.get(sid, sid), "diff": int(diff)})
        diffs.sort(key=lambda d: d["diff"], reverse=True)
        rows.append({"year": year, "total": int(total), "top": diffs[:5]})
    return rows


def build_price_history_doc() -> dict:
    """C4: id → последние 90 точек цены из data/processed/price_history.csv.

    CSV может быть пустым/отсутствует — тогда честный пустой объект:
    в браузере спарклайн покажет фолбэк «история копится с v2.1…».
    """
    out: dict[str, list] = {}
    if not PRICE_HIST.exists():
        return out
    with open(PRICE_HIST, encoding="utf-8") as f:
        text = f.read()
    import csv
    import io
    for row in csv.DictReader(io.StringIO(text)):
        sid = (row.get("id") or "").strip()
        d = (row.get("date") or "").strip()
        med = row.get("median") or ""
        if not sid or not d or not med:
            continue
        try:
            p = float(med)
        except ValueError:
            continue
        if p > 0:
            out.setdefault(sid, []).append([d, round(p, 1)])
    for sid, pts in out.items():
        pts.sort(key=lambda x: x[0])
        out[sid] = pts[-90:]
    return out


def main() -> None:
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    id_name = {s["id"]: s["name"] for s in data}
    total = len(data)
    ok = 0
    cache: dict = {}

    for s in data:
        name = s["name"]
        sid = s["id"]
        q = ma_query(name)
        if not q:
            print(f"{name}: нет запроса — пропуск")
            continue
        try:
            pmids = search_pmids(q)
            time.sleep(SLEEP)
            years = summaries(pmids)
            time.sleep(SLEEP)
        except RuntimeError as e:
            print(f"⚠️ {name}: {e}")
            continue
        if years:
            cache[sid] = {str(y): c for y, c in years.items()}
            ok += 1
        n_ma = sum(years.values()) if years else 0
        print(f"{name}: {len(pmids)} PMIDs -> {n_ma} MA across {len(years)} year(s)")

    if ok == 0:
        print("\nНЕ ОДНА добавка не прошла — НЕ коммитим кэш/агрегат.")
        print("Нужна проверка человеком (сеть PubMed?); скрипт готов к повтору.")
        sys.exit(1)

    cache_text = json.dumps(cache, ensure_ascii=False, indent=2) + "\n"
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(cache_text, encoding="utf-8")
    print(f"\n✅ Кэш: {CACHE_PATH} ({ok}/{total} добавок)")

    timeline = build_timeline(cache, id_name)
    AGGREGATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    AGGREGATE_PATH.write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"✅ Агрегат: {AGGREGATE_PATH} ({len(timeline)} год(ов) → [{timeline[0]['year']}..{timeline[-1]['year']}])")

    price_doc = build_price_history_doc()
    PRICE_DOC.parent.mkdir(parents=True, exist_ok=True)
    PRICE_DOC.write_text(
        json.dumps(price_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    n_rows = sum(len(v) for v in price_doc.values())
    print(f"✅ Спарклайн-агрегат: {PRICE_DOC} (id={len(price_doc)}, строк={n_rows})")


if __name__ == "__main__":
    main()

"""v2.6.1: автотоп-3 мета-анализов PubMed (ma_top3) + price_date из price_history.

Для каждой добавки: esearch top-3 записи с фильтром meta-analysis[pt] по запросу
из src/config.py (SUPPLEMENTS — тот же, что считает scienceIndex) → esummary →
ma_top3: [{"pmid", "title", "year"}]. Сон 0.4 c между запросами (регламент
PubMed 3 req/s без API-key). Один прогон, результат коммитится.

price_date: последняя строка data/processed/price_history.csv по id; если
файла/строк нет — "дата неизвестна" (честно, без выдумок).

Сеть может блокировать PubMed: 429/обрывы НЕ выдумываем pmid/title — пишем
пустой список и отражаем количество в отчёте. Если получено 0 добавок —
массив ma_top3 в data.json не коммитим (нужна проверка человеком).

Запуск:
    python scripts/build_key_sources.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import SUPPLEMENTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data.json"
PRICE_HIST = ROOT / "data" / "processed" / "price_history.csv"

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
SLEEP = 0.4
RETRIES = 3


def _get(url: str, params: dict) -> requests.Response:
    """GET с 2 повторами на 429/таймаут/обрыв (P-стоп: 429 ≠ бито, просто дорого)."""
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


def top3_ma(query: str) -> list[str]:
    r = _get(ESEARCH, params={"db": "pubmed", "retmode": "json", "retmax": 3,
                              "term": f"({query}) AND meta-analysis[pt]"})
    return r.json()["esearchresult"].get("idlist", [])


def summaries(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    r = _get(ESUMMARY, params={"db": "pubmed", "retmode": "json",
                               "id": ",".join(pmids)})
    result = r.json()["result"]
    out = []
    for pmid in pmids:
        rec = result.get(pmid)
        if not rec:
            continue
        title = (rec.get("title") or "").strip()
        if not title:
            continue
        m = re.search(r"(\d{4})", rec.get("pubdate") or "")
        out.append({"pmid": pmid, "title": title,
                    "year": int(m.group(1)) if m else None})
    return out


def price_dates() -> dict[str, str]:
    """id → последняя дата из price_history.csv (последняя строка побеждает)."""
    out: dict[str, str] = {}
    if not PRICE_HIST.exists():
        return out
    with open(PRICE_HIST, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("id"):
                out[row["id"]] = row.get("date") or ""
    return {k: v for k, v in out.items() if v}


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    pdates = price_dates()
    ok = 0
    for s in data:
        name = s["name"]
        s["price_date"] = pdates.get(s["id"], "дата неизвестна")
        q = SUPPLEMENTS.get(name)
        if not q:
            s["ma_top3"] = []
            continue
        try:
            pmids = top3_ma(q)
            time.sleep(SLEEP)
            s["ma_top3"] = summaries(pmids)
            time.sleep(SLEEP)
        except RuntimeError as e:
            print(f"⚠️ {name}: {e}")
            s["ma_top3"] = []
            continue
        if s["ma_top3"]:
            ok += 1
        print(f"{name}: {len(s['ma_top3'])}")

    # ma_top3 добавляем в data.json только в случае хотя бы одного живого ответа:
    # ничего не выдумываем, пустые списки оставляем честными (0 = ещё не собрано).
    if ok:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(f"done: {ok}/{len(data)} карточек получили ma_top3")
    if ok == 0:
        print("РЕЗУЛЬТАТ 0 — НЕ КОММИТИТЬ data.json, нужна проверка человеком (живой прогон)")


if __name__ == "__main__":
    main()
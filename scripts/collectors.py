"""Коллекторы цен v2: Wildberries и Ozon через JSON-API (без HTML)."""
from __future__ import annotations
import json, random, time
from dataclasses import dataclass
from typing import Any, Iterator
from urllib.parse import quote
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0 Safari/537.36"}
WB_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
OZON_URL = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"


class CollectorError(RuntimeError):
    """Источник недоступен после ретраев."""


@dataclass
class Offer:
    name: str
    price_rub: float
    source: str


def _get(url: str, params: dict, timeout: int = 20, retries: int = 3) -> Any:
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code == 429:
                time.sleep(45 * 2 ** i + random.uniform(0, 5))
                continue
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:
            if i == retries - 1:
                raise CollectorError(f"{url}: {e}") from e
            time.sleep(10 * 2 ** i)
    raise CollectorError(f"{url}: 429 после {retries} попыток")


def _rub(value: Any, kopecks: bool = False) -> float:
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        value = float(digits) if digits else 0.0
    return round(float(value) / (100.0 if kopecks else 1.0), 1)


def collect_wb(query: str, limit: int = 8) -> list[Offer]:
    data = _get(WB_URL, {"appType": 1, "curr": "rub", "dest": -1257786,
                         "query": query, "resultset": "catalog", "sort": "popular"})
    out = []
    for p in (data.get("data") or {}).get("products", [])[:limit]:
        price = _rub(p.get("salePriceU") or p.get("priceU") or 0, kopecks=True)
        if price > 0:
            out.append(Offer(p.get("name", ""), price, "wb"))
    return out


def _walk(obj: Any) -> Iterator[tuple[str, float]]:
    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("title") or obj.get("productName")
        raw = obj.get("price") or obj.get("cardPrice") or obj.get("priceString")
        if name and raw is not None:
            p = _rub(raw)
            if p > 0:
                yield str(name), p
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)
    elif isinstance(obj, str) and obj[:1] in "[{":
        try:
            yield from _walk(json.loads(obj))
        except ValueError:
            pass


def collect_ozon(query: str, limit: int = 8) -> list[Offer]:
    out = []
    data = _get(OZON_URL, {"url": f"/search/?text={quote(query)}"})
    for name, price in _walk(data):
        out.append(Offer(name, price, "ozon"))
        if len(out) >= limit:
            break
    return out

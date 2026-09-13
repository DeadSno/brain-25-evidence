"""Коллекторы цен v2: Wildberries (v5→v4→старый→basket-CDN) и Ozon через JSON-API."""
from __future__ import annotations
import csv, json, random, re, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0 Safari/537.36"}
WB_HOME = "https://www.wildberries.ru/"
WB_URL_V5 = "https://search.wb.ru/exactmatch/ru/common/v5/search"
WB_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
OZON_URL = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
WB_PARAMS = {"appType": 1, "curr": "rub", "dest": -1257786,
             "resultset": "catalog", "sort": "popular"}
HISTORY_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "prices_wb_history.csv"

# watchdog: все эндпоинты WB мертвы (выставляет collect_wb)
WB_DEAD: bool = False

# circuit breaker: последовательные CollectorError на семейство
DEAD_LIMIT = 3
_FAIL: dict[str, int] = {}


def _failing(family: str) -> bool:
    _FAIL[family] = _FAIL.get(family, 0) + 1
    return _FAIL[family] >= DEAD_LIMIT


def family_dead(family: str) -> bool:
    return _FAIL.get(family, 0) >= DEAD_LIMIT


def _family_ok(family: str) -> None:
    _FAIL.pop(family, None)


def reset_breakers() -> None:
    _FAIL.clear()


def circuit_dead() -> list[str]:
    return sorted(f for f, c in _FAIL.items() if c >= DEAD_LIMIT)

# кэш id по поисковому запросу (для basket-CDN ступени)
_ID_CACHE: dict[str, list[int]] = {}


class CollectorError(RuntimeError):
    """Источник недоступен после ретраев."""


@dataclass
class Offer:
    name: str
    price_rub: float
    source: str


_SESSION = None


def warmup(session: "requests.Session") -> None:
    """Прогрев: главная WB для cookie-сессии x-wb-* (анти-бот)."""
    try:
        session.get(WB_HOME, timeout=20,
                    headers={"Accept": "text/html,application/xhtml+xml,*/*",
                             "Accept-Language": "ru-RU,ru;q=0.9",
                             "Referer": WB_HOME})
    except requests.RequestException:
        pass


def get_session() -> "requests.Session":
    """Одна тёплая WB-сессия на процесс; создаётся только в реальном _get."""
    global _SESSION
    if _SESSION is None:
        s = requests.Session()
        s.headers.update({
            "User-Agent": UA["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": WB_HOME,
        })
        warmup(s)
        _SESSION = s
    return _SESSION


def _get(url: str, params: dict, timeout: int = 20, retries: int = 3) -> Any:
    session = get_session()
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=timeout)
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


def _offers_and_ids(data: Any, limit: int) -> tuple[list[Offer], list[int]]:
    offs, ids = [], []
    for p in (data.get("data") or {}).get("products", [])[:limit]:
        if p.get("id"):
            ids.append(p["id"])
        price = _rub(p.get("salePriceU") or p.get("priceU") or 0, kopecks=True)
        if price > 0:
            offs.append(Offer(p.get("name", ""), price, "wb"))
    return offs, ids


def _seed_cache() -> None:
    """Доси́д из v1.x истории: запрос → WB арт. (колонка источник)."""
    if _ID_CACHE or not HISTORY_CSV.exists():
        return
    from src.config import WB_QUERY
    q_by_name = {name: q for name, (q, _u) in WB_QUERY.items()}
    text = HISTORY_CSV.read_text(encoding="utf-8-sig")
    for row in csv.DictReader(text.splitlines()):
        q = q_by_name.get(row.get("добавка") or "")
        m = re.search(r"(\d+)", row.get("источник") or "")
        if q and m:
            _ID_CACHE.setdefault(q, []).append(int(m.group(1)))


def _basket_url(pid: int, basket: int) -> str:
    vol, part = pid // 100000, pid // 1000
    return (f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/"
            f"{pid}/info/ru/card.json")


def _basket_get(url: str) -> Any:
    try:
        r = get_session().get(url, timeout=10)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def _basket_offer(pid: int) -> Offer | None:
    """Ступень 4: card.json по кэшированному id (эмпирическая формула vol/part)."""
    for b in range(1, 41):
        data = _basket_get(_basket_url(pid, b))
        if not data:
            continue
        for sz in data.get("sizes") or []:
            price = ((sz.get("price") or {}).get("product")
                     or (sz.get("price") or {}).get("total"))
            if price:
                name = data.get("title") or data.get("subject") or f"арт.{pid}"
                return Offer(str(name), _rub(price, kopecks=True), "wb-cdn")
    return None


def _old_wb(query: str, limit: int) -> list[Offer]:
    """Старый HTML-коллектор v1.2 (src.parsers.wb_search) — без дублирования кода."""
    from src.parsers import wb_search
    out = []
    df = wb_search(query, n=limit)
    for _, o in df.iterrows():
        out.append(Offer(str(o.get("название", "")), float(o.get("цена_руб", 0)), "wb"))
    return out


def _dead() -> list[Offer]:
    global WB_DEAD
    WB_DEAD = True
    return []


def collect_wb(query: str, limit: int = 8) -> list[Offer]:
    _seed_cache()
    params = {**WB_PARAMS, "query": query}
    if not family_dead("wb_search"):
        for url in (WB_URL_V5, WB_URL):
            try:
                data = _get(url, params)
            except CollectorError:
                if _failing("wb_search"):
                    break
                continue
            _family_ok("wb_search")
            offs, ids = _offers_and_ids(data, limit)
            if ids:
                _ID_CACHE.setdefault(query, []).extend(ids)
            if offs:
                return offs
    if not family_dead("wb_html"):
        try:
            offs = _old_wb(query, limit)
            if offs:
                _family_ok("wb_html")
                return offs
        except Exception:
            _failing("wb_html")
    for pid in _ID_CACHE.get(query, [])[:limit]:
        off = _basket_offer(pid)
        if off:
            return [off]
    return _dead()


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
    if family_dead("ozon"):
        raise CollectorError("ozon: circuit open (3 подряд)")
    out = []
    try:
        data = _get(OZON_URL, {"url": f"/search/?text={quote(query)}"})
    except CollectorError:
        _failing("ozon")
        raise
    _family_ok("ozon")
    for name, price in _walk(data):
        out.append(Offer(name, price, "ozon"))
        if len(out) >= limit:
            break
    return out

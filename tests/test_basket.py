"""Тест ступени 4 (basket-CDN): формула по кэшированным id (2 образца, без сети)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collectors as C

CARD_4219394 = {"title": "Prime Kraft Креатин моногидрат 200г",
                "sizes": [{"price": {"product": 55600, "total": 59000}}]}
CARD_13257465 = {"title": "Креатин 300г",
                 "sizes": [{"price": {"product": 132500, "total": 139900}}]}


def test_formula_two_ids(monkeypatch):
    urls = []
    def fake_get(url, params=None, **kw):
        urls.append(url)
        import json
        return json.loads(json.dumps(
            CARD_4219394 if "4219394" in url else CARD_13257465))
    monkeypatch.setattr(C, "_basket_get", lambda url: fake_get(url))
    off42 = C._basket_offer(4219394)
    assert off42 and off42.price_rub == 556.0 and "Pr" in off42.name
    off13 = C._basket_offer(13257465)
    assert off13 and off13.price_rub == 1325.0
    assert any(f"/vol{4219394//100000}/part{4219394//1000}/4219394/" in u for u in urls)
    assert any(f"/vol{13257465//100000}/part{13257465//1000}/13257465/" in u for u in urls)


def test_collect_wb_basket_fallback(monkeypatch):
    C.WB_DEAD = False; C._ID_CACHE.clear()
    monkeypatch.setattr(C, "_get", lambda *a, **k: (_ for _ in ()).throw(C.CollectorError("x")))
    monkeypatch.setattr(C, "_old_wb", lambda *a, **k: (_ for _ in ()).throw(Exception("y")))
    C._ID_CACHE["креатин"] = [4219394]
    monkeypatch.setattr(C, "_basket_offer", lambda pid: C.Offer("test", 123.0, "wb-cdn"))
    offs = C.collect_wb("креатин")
    assert offs and offs[0].price_rub == 123.0 and not C.WB_DEAD

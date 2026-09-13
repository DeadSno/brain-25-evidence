"""Слои L2+L3: fixture-replay API и гарды цен."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import requests
import collectors as C
from update_prices import jump_ok, median_price

WB_FIXTURE = {"data": {"products": [
    {"name": "Креатин моногидрат 300г", "salePriceU": 46900, "priceU": 59900},
    {"name": "Креатин 200г", "salePriceU": 35000}]}}
OZON_FIXTURE = {"widgetStates": {"w1": '{"items": ['
                '{"name": "Креатин банка", "price": "1 234 ₽"}]}'}}


def test_wb_fixture_replay(monkeypatch):
    monkeypatch.setattr(C, "_get", lambda *a, **k: WB_FIXTURE)
    offs = C.collect_wb("креатин")
    assert [o.price_rub for o in offs] == [469.0, 350.0]
    assert all(o.source == "wb" for o in offs)


def test_ozon_fixture_replay(monkeypatch):
    monkeypatch.setattr(C, "_get", lambda *a, **k: OZON_FIXTURE)
    offs = C.collect_ozon("креатин")
    assert offs[0].price_rub == 1234.0 and offs[0].source == "ozon"


def test_median_and_divergence():
    assert median_price(100, 110)[0] == 105
    assert median_price(100, 200)[2] is True
    assert median_price(None, 90) == (90, "ozon", False)
    assert median_price(None, None)[0] is None


def test_jump_guard():
    assert jump_ok(500, 600) and not jump_ok(500, 5000)
    assert jump_ok(None, 10)


def test_warmup_calls_session_get(monkeypatch):
    calls = []

    class FakeResp:
        status_code = 200
        cookies = {}

        def json(self):
            return {"data": {"products": []}}

        def raise_for_status(self):
            return None

    monkeypatch.setattr(requests.Session, "get",
                        lambda self, url, **kw: calls.append(url) or FakeResp())
    monkeypatch.setattr(C, "_old_wb", lambda *a, **k: [])
    C.collect_wb("креатин")
    assert calls and calls[0] == C.WB_HOME
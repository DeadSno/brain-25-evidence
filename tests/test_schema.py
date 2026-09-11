import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "data.json"

REQUIRED = {
    "id": str, "name": str, "code": int, "verdict": str,
    "category": str, "scienceIndex": int, "metaCount": int,
    "effects": list,
}
ALLOWED_CODE = {-1, 0, 1}
VERDICTS = {1: "работает", 0: "зависит от контекста", -1: "не подтверждено"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_schema_fields_and_types():
    for s in load():
        for key, typ in REQUIRED.items():
            assert key in s, f"{s.get('id')}: нет поля {key}"
            assert isinstance(s[key], typ), f"{s['id']}: {key} должен быть {typ.__name__}"


def test_ids_unique():
    ids = [s["id"] for s in load()]
    dup = {i for i in ids if ids.count(i) > 1}
    assert not dup, f"дубликаты id: {dup}"


def test_verdict_consistency():
    for s in load():
        assert s["code"] in ALLOWED_CODE, f"{s['id']}: код {s['code']} вне {-1,0,1}"
        assert s["verdict"] == VERDICTS[s["code"]], f"{s['id']}: вердикт не совпадает с кодом"


def test_ranges_sane():
    for s in load():
        assert s["scienceIndex"] >= 0 and s["metaCount"] >= 0
        if s.get("price") is not None:
            assert 0 < s["price"] < 100000, f"{s['id']}: подозрительная цена {s['price']}"
        if s.get("dosagePerKg") is not None:
            assert s["dosagePerKg"] > 0 and s["dosageMax"] > 0, f"{s['id']}: битая дозировка"


def test_no_zero_science_index():
    for s in load():
        assert s["scienceIndex"] > 0, f"{s['id']}: scienceIndex=0 — не попадёт на график"
"""F4.3: радар профиля — значения ∈ [0,100] (перцентиль по базе 81 карточки).

Референсная реализация pctile() из script.js — проверяется как контракт.
"""
import json
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parents[1] / "docs" / "data.json").read_text(encoding="utf-8"))
BASE = len(DATA)
assert BASE == 81, f"ожидаем 81 карточку в базе, получено {BASE}"


def _pctile(x, arr):
    """Референсная функция: перцентиль позиции x в arr (как в script.js)."""
    vals = sorted(v if v is not None else 0 for v in arr)
    target = x if x is not None else 0
    lo, hi = 0, len(vals) - 1
    while lo <= hi:
        mid = (lo + hi) >> 1
        if vals[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if lo == 0:
        return 0
    return round((lo / (len(vals) - 1)) * 100)


def _prof(s):
    """Профиль добавки s — 4 оси радара по script.js (нормировано по базе)."""
    raw = [
        s.get("scienceIndex") or 0,
        s.get("metaCount") or 0,
        s.get("reviews") or 0,
        s.get("trends") or 0,
    ]
    arrays = [
        [x.get("scienceIndex") or 0 for x in DATA],
        [x.get("metaCount") or 0 for x in DATA],
        [x.get("reviews") or 0 for x in DATA],
        [x.get("trends") or 0 for x in DATA],
    ]
    vals = []
    for i in range(4):
        vals.append(_pctile(raw[i], arrays[i]))
    return vals


def test_all_supplements_radar_in_0_100():
    for s in DATA:
        prof = _prof(s)
        for i, v in enumerate(prof):
            assert 0 <= v <= 100, f"{s['id']} axis {i} = {v}, expected [0,100]"


def test_kofein_radar_values():
    cof = next(s for s in DATA if s["id"] == "Кофеин")
    prof = _prof(cof)
    labels = ["scienceIndex", "metaCount", "reviews", "trends"]
    for i, v in enumerate(prof):
        assert 0 <= v <= 100, f"Кофеин {labels[i]} = {v}"
        assert v > 0, f"Кофеин {labels[i]} = 0 — likely bug in normalization"


def test_empty_supplement_radar():
    """Добавка с нулевыми метриками (BCAA: scienceIndex=5, metaCount=0) — значения ≥0."""
    bcaa = next(s for s in DATA if s["id"] == "BCAA")
    prof = _prof(bcaa)
    assert all(0 <= v <= 100 for v in prof)
    assert prof[1] == 0, f"BCAA metaCount pctile должен быть 0 (metaCount=0)"

"""v2.7-C6: schema-тесты таймлайна мета-анализов (Пульс науки) и спарклайна.

Проверяем docs/data_ma_timeline.json (C2-агрегат) и data/processed/ma_years.json
(C1-кэш), плюс связку index.html ↔ science2.js.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGG = ROOT / "docs" / "data_ma_timeline.json"
CACHE = ROOT / "data" / "processed" / "ma_years.json"
DATA = ROOT / "docs" / "data.json"
INDEX = ROOT / "docs" / "index.html"
SCIENCE2 = ROOT / "docs" / "science2.js"
PRICE_DOC = ROOT / "docs" / "data_price_history.json"

YEARS = list(range(2015, 2027))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_aggregate_exists_and_is_list():
    rows = load(AGG)
    assert isinstance(rows, list) and len(rows) == len(YEARS)


def test_aggregate_years_monotonic():
    rows = load(AGG)
    years = [r["year"] for r in rows]
    assert years == YEARS, f"годы не монотонны 2015→2026: {years}"


def test_aggregate_schema_per_row():
    for r in load(AGG):
        assert isinstance(r["total"], int) and r["total"] >= 0, f"{r['year']}: total<0"
        assert isinstance(r.get("top"), list) and len(r["top"]) <= 5
        diffs = [t["diff"] for t in r["top"]]
        assert diffs == sorted(diffs, reverse=True), "top не отсортирован по diff"
        for t in r["top"]:
            assert isinstance(t, dict)
            assert t["id"] and isinstance(t["name"], str)
            assert isinstance(t["diff"], int)
            assert isinstance(r["total"], int)


def test_aggregate_totals_match_cache():
    cache = load(CACHE)
    rows = load(AGG)
    for r in rows:
        y = str(r["year"])
        total = sum(v.get(y, 0) for v in cache.values())
        assert r["total"] == total, f"{r['year']}: агрегат {r['total']} ≠ кэш {total}"


def test_cache_schema():
    cache = load(CACHE)
    ids = {s["id"] for s in load(DATA)}
    assert cache, "кэш пуст"
    for sid, years in cache.items():
        assert sid in ids, f"id {sid} нет в data.json"
        assert isinstance(years, dict) and years
        for ys, cnt in years.items():
            assert int(ys) >= 2010 and int(ys) <= 2031, f"{sid}: год вне диапазона {ys}"
            assert isinstance(cnt, int) and cnt > 0


def test_index_connects_science2_once():
    html = INDEX.read_text(encoding="utf-8")
    assert html.count("science2.js") == 1
    assert '<script src="science2.js" defer></script>' in html


def test_science2_exposes_pulse_and_spark():
    js = SCIENCE2.read_text(encoding="utf-8")
    assert "data_ma_timeline.json" in js
    assert "data_price_history.json" in js
    assert "maTimelineBox" in js
    assert "ecoSpark" in js
    assert "история копится с v2.1" in js


def test_price_history_doc_schema():
    if not PRICE_DOC.exists():
        return
    doc = load(PRICE_DOC)
    assert isinstance(doc, dict), "data_price_history.json не dict"
    for sid, pts in doc.items():
        assert isinstance(sid, str) and sid, "пустой id в data_price_history.json"
        assert isinstance(pts, list), f"{sid}: не массив"
        for d, p in pts:
            assert isinstance(d, str) and len(d) == 10, f"{sid}: дата {d!r}"
            assert isinstance(p, (int, float)) and p > 0, f"{sid}: цена {p!r}"
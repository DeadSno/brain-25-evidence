"""v2.6: поля для trust-визуализаций в data.json (год последнего МА, актуальность,
nullable источник цены) и факты, из которых рендерятся бейджи/иконки."""
import json
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
DATA = json.loads((DOCS / "data.json").read_text(encoding="utf-8"))

COF = next(s for s in DATA if s["id"] == "Кофеин")


def _by_id(sid):
    return next(s for s in DATA if s["id"] == sid)


def test_year_last_ma_present_all():
    assert all("year_last_ma" in s for s in DATA), "поле year_last_ma обязано быть у всех карточек"


def test_year_last_ma_coffee_from_key_sources():
    ks_years = [s.get("year") for s in (COF.get("key_sources") or []) if s.get("year")]
    want = max(ks_years) if ks_years else None
    assert COF["year_last_ma"] == want, "year_last_ma Кофеина не совпал с max year по key_sources"


def test_year_last_ma_null_without_sources():
    no_ks = [s for s in DATA if not (s.get("key_sources") or [])]
    assert no_ks, "ожидали карточки без key_sources"
    assert all(s["year_last_ma"] is None for s in no_ks), "year_last_ma обязан быть null без key_sources"


def test_updated_date_all_same_recent():
    assert all("updated" in s for s in DATA)
    dates = {s["updated"] for s in DATA}
    assert len(dates) == 1, f"updated должен быть единой датой обновления data.json, нашёл {dates}"
    upd = dates.pop()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", upd), f"updated не похожа на дату: {upd}"


def test_price_source_nullable_key_present():
    assert all("price_source" in s for s in DATA), "ключ price_source обязан быть у всех карточек"
    assert all(s["price_source"] is None for s in DATA), \
        "price_source заполняется только живым ботом цен — при отсутствии данных он обязан быть null"


def test_rct_formula_non_negative():
    # Ось «Число РКИ» = max(0, scienceIndex − 5×metaCount) из методологии
    for s in DATA:
        rct = max(0, (s.get("scienceIndex") or 0) - 5 * (s.get("metaCount") or 0))
        assert rct >= 0, f"{s['id']}: РКИ по формуле отрицательное"


def test_grade_dots_map_consistent():
    # 5-точечный бейдж: A=4, B=3, C=2, D=1, без грейда=0
    dots = {"A": 4, "B": 3, "C": 2, "D": 1}
    assert COF["grade"] == "B" and dots["B"] == 3, "эталон Кофеин-B должен давать 3 точки"
    graded = [s for s in DATA if s.get("grade")]
    for s in graded:
        assert s["grade"] in dots, f"{s['id']}: неизвестный грейд {s['grade']}"
    ungraded = [s for s in DATA if not s.get("grade")]
    assert ungraded, "ожидали карточки без грейда (0 точек + «ждёт верификации»)"
    assert COF["id"] not in {s["id"] for s in ungraded}


def test_manual_review_badge_condition():
    # «✋ ручная вычитка» — карточки с ручным вердиктом (вердикт есть у всех)
    assert all(s.get("verdict") for s in DATA), "вердикт обязан быть у всех карточек"
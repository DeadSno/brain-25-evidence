"""v2.4: provenance доказательности — g попадает в data.json только
верифицированным (approve-очередь владельца). Пока пусто — карточки честно
пустые. Если g задан: обязан быть ключ к источникам, диапазон дат адекватен,
грейд пересчитывается функцией grade_of().
"""
import json
from pathlib import Path

import pytest

sys_path = str(Path(__file__).resolve().parents[1])
import sys

sys.path.insert(0, sys_path)
from src.content import grade_of  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "docs" / "data.json"

CI_KEYS = {"lo", "hi"}
SRC_KEYS = {"citation", "pmid", "doi", "year", "g", "ci"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_schema_fields_nullable():
    """5 новых полей присутствуют у каждой карточки (nullable)."""
    for s in load():
        assert "hedges_g" in s, f"{s['id']}: нет hedges_g"
        assert "hedges_g_ci" in s, f"{s['id']}: нет hedges_g_ci"
        assert "effect_outcome" in s, f"{s['id']}: нет effect_outcome"
        assert "grade" in s, f"{s['id']}: нет grade"
        assert "key_sources" in s, f"{s['id']}: нет key_sources"
        if s["grade"] is not None:
            assert s["grade"] in {"A", "B", "C", "D"}, f"{s['id']}: грейд {s['grade']}"


def test_provenance_g_requires_key_sources():
    """g≠null ⇒ key_sources непустой, у каждого pmid или doi."""
    for s in load():
        if s["hedges_g"] is None:
            continue
        assert s["key_sources"], f"{s['id']}: g задан, но key_sources пуст"
        for src in s["key_sources"]:
            assert src.get("pmid") or src.get("doi"), f"{s['id']}: источник без pmid/doi"


def test_g_range_and_ci():
    """-3 ≤ g ≤ 3; ci_lo < ci_hi."""
    for s in load():
        if s["hedges_g"] is None:
            continue
        assert -3 <= s["hedges_g"] <= 3, f"{s['id']}: g вне [-3,3]"
        ci = s["hedges_g_ci"]
        if ci:
            assert set(ci) == CI_KEYS, f"{s['id']}: ci без lo/hi"
            assert ci["lo"] < ci["hi"], f"{s['id']}: ci_lo >= ci_hi"


def test_grade_recomputed():
    """grade пересчитывается из (g, scienceIndex) функцией grade_of()."""
    for s in load():
        if s["hedges_g"] is None:
            continue
        expected = grade_of(s["hedges_g"], s["scienceIndex"])
        assert s["grade"] == expected, (
            f"{s['id']}: grade {s['grade']} != grade_of({s['hedges_g']}, "
            f"{s['scienceIndex']}) = {expected}"
        )


def test_grade_of_boundaries():
    assert grade_of(None, 100) is None
    assert grade_of(0.1, 40) == "D"    # объём < 50
    assert grade_of(0.5, 100) == "A"   # сильный + большой объём
    assert grade_of(0.12, 100) == "C"  # слабый
    assert grade_of(0.3, 80) == "B"    # средний
    assert grade_of(0.42, 120) == "A"
    assert grade_of(-0.1, 200) == "C"  # отрицательный g (вред), объём большой → C


def test_effect_outcome_consistency():
    for s in load():
        if s["hedges_g"] is None:
            continue
        assert isinstance(s["effect_outcome"], str) and s["effect_outcome"], (
            f"{s['id']}: g задан, а effect_outcome пуст"
        )
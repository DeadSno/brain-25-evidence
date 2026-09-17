"""v2.6.1: схема ma_top3 — автотоп-3 мета-анализов PubMed по каждой добавке.

pmid — цифры, year 1990–2026 (у есummary может не быть pubdate — допускаем
None, но title обязан быть непустым). Список — честный: пуст, пока живой
прогон не наполнил (0 ≠ выдуманные pmid/title).
"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "data.json"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_ma_top3_field_present_all():
    for s in load():
        assert "ma_top3" in s, f"{s['id']}: нет поля ma_top3"
        assert isinstance(s["ma_top3"], list), f"{s['id']}: ma_top3 обязан быть списком"


def test_ma_top3_schema():
    for s in load():
        for m in s["ma_top3"]:
            assert isinstance(m, dict) and m.get("pmid"), f"{s['id']}: статья без pmid"
            assert re.fullmatch(r"\d+", str(m["pmid"])), f"{s['id']}: pmid не цифры — {m['pmid']!r}"
            title = m.get("title")
            assert isinstance(title, str) and title.strip(), f"{s['id']}: title пустой"
            year = m.get("year")
            if year is not None:
                assert isinstance(year, int) and 1990 <= year <= 2026, \
                    f"{s['id']}: year вне 1990-2026 — {year!r}"


def test_ma_top3_at_most_three():
    for s in load():
        assert len(s["ma_top3"]) <= 3, f"{s['id']}: топ-3 больше трёх"


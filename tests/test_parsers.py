import pytest
from src import parsers


def test_parse_units_grams():
    assert parsers.parse_units("Креатин моногидрат 500 г", "г") == 500


def test_parse_units_caps():
    assert parsers.parse_units("Омега-3 90 капсул", "капс") == 90


def test_set_is_not_dose():
    assert parsers.parse_units("Ресвератрол 2 шт", "капс") is None


def test_mg_is_not_grams():
    assert parsers.parse_units("Кофеин 200 мг", "г") is None


def test_garden_filter():
    assert parsers.GARDEN.search("Аэлита Бакопа семена 3 шт")
    assert not parsers.GARDEN.search("NOW Bacopa 300mg 60 капсул")


@pytest.mark.network
def test_wb_alive():
    df = parsers.wb_search("креатин моногидрат", n=5)
    assert {"артикул", "название", "цена_руб"} <= set(df.columns)
    assert (df["цена_руб"] > 0).all()
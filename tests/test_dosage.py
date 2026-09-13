"""Предохранители доз (вариант б, S7): парсер 5 добавок, monthly=ручной, units."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dosage as D
from src.parsers import parse_units
from update_prices import monthly, units_median
import collectors as C


def test_parse_five_supplements():
    assert D.DOSE_PER_DAY["Креатин"] == 4.0
    assert D.DOSE_PER_DAY["Коллаген"] == 7.5
    assert D.DOSE_PER_DAY["Имбирь"] == 1.0
    assert D.DOSE_PER_DAY["Мелатонин"] == 1.0
    assert D.DOSE_PER_DAY["Глицин"] == 2.0
    assert D.DOSE_FLAGS["Креатин"] == "parsed:г"
    assert D.DOSE_FLAGS["Мелатонин"] == "default:30/30"


def test_parse_grams_day():
    assert D.parse_grams_day("3-5 г/сут (моногидрат)") == 4.0
    assert D.parse_grams_day("1 г/сут сухого корня") == 1.0
    assert D.parse_grams_day("капсулы 500 мг") is None


def test_monthly_matches_manual():
    assert D.monthly(1708, 300, "Креатин") == 1708 / 300 * 4.0 * 30
    assert monthly(1708, 300, "Креатин") == D.monthly(1708, 300, "Креатин")
    assert D.monthly(500, 90, "Омега-3") == round(500 / 90 * 30, 1)


def test_units_per_offer():
    assert parse_units("UltraSupps Креатин 300 г, банка", "г") == 300
    assert parse_units("Омега-3 1000 мг 90 капс", "капс") == 90
    assert units_median([C.Offer("Креатин 300 г", 1, "wb"),
                         C.Offer("Креатин 500 г", 1, "wb")], "г") == 400
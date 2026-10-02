"""Тесты src/config.py — конфигурация проекта (QA_AUDIT P2-19).

Модуль не был покрыт ни одним тестом, хотя из него берутся PubMed-запросы
для scripts/fetch_metrics.py. Ошибка в SUPPLEMENTS или OUTCOME означает молчаливо
неверную выдачу, поэтому проверяем и наличие, и форму, и согласованность
с реальными карточками data.json.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config  # noqa: E402

DATA_IDS = {c["id"] for c in json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))}


# ── MAILTO ──────────────────────────────────────────────────────────────────

def test_mailto_is_valid_email():
    assert isinstance(config.MAILTO, str)
    assert "@" in config.MAILTO and "." in config.MAILTO.split("@")[-1]
    assert " " not in config.MAILTO, "в MAILTO есть пробелы — письмо уйдёт криво"


def test_mailto_no_crlf_injection():
    """MAILTO попадает в заголовок письма. \r\n в значении позволяет
    добавить произвольные заголовки (header injection)."""
    assert "\r" not in config.MAILTO
    assert "\n" not in config.MAILTO


# ── COG ─────────────────────────────────────────────────────────────────────

def test_cog_is_nonempty_string():
    assert isinstance(config.COG, str)
    assert len(config.COG) > 10


def test_cog_has_query_operators():
    """Для PubMed строка должна содержать операторы, иначе запрос слишком широкой."""
    assert " OR " in config.COG
    assert config.COG.count("(") == config.COG.count(")"), "скобки в COG не сбалансированы"


# ── SUPPLEMENTS ────────────────────────────────────────────────────────────

def test_supplements_is_nonempty_dict():
    assert isinstance(config.SUPPLEMENTS, dict)
    assert len(config.SUPPLEMENTS) > 50, "SUPPLEMENTS подозрительно мал"


def test_supplements_keys_and_values_are_str():
    for k, v in config.SUPPLEMENTS.items():
        assert isinstance(k, str) and k.strip(), f"ключ не строка: {k!r}"
        assert isinstance(v, str) and v.strip(), f"{k!r} -> пустой поисковый термин"


def test_supplements_keys_exist_in_data_json():
    """Ключ SUPPLEMENTS, которого нет в data.json, — опечатка: запрос уйдёт
    в никуда и молча ничего не вернёт."""
    missing = sorted(set(config.SUPPLEMENTS) - DATA_IDS)
    assert not missing, f"ключи SUPPLEMENTS, отсутствующие в data.json: {missing}"


def test_supplements_has_no_case_mismatch():
    """Отдельно от точного совпадения: 'L-теанин' != 'L-Теанин'. Словарь
    Python регистрозависимый, такое расхождение невидимо глазом."""
    lower = {i.lower() for i in DATA_IDS}
    suspicious = sorted(k for k in config.SUPPLEMENTS if k not in DATA_IDS and k.lower() in lower)
    assert not suspicious, f"регистр не совпадает с data.json: {suspicious}"


# ── OUTCOME / DEFAULT_OUTCOME ──────────────────────────────────────────────

def test_outcome_is_nonempty_dict():
    assert isinstance(config.OUTCOME, dict)
    assert len(config.OUTCOME) > 0


def test_outcome_values_are_parenthesised_queries():
    """Каждый исход — готовая PubMed-строка в скобках, иначе OR из разных
    блоков смешается операторами AND предыдущего уровня."""
    for k, v in config.OUTCOME.items():
        assert isinstance(v, str) and v.strip(), f"{k!r}: пустой исход"
        assert v.startswith("(") and v.endswith(")"), f"{k!r}: исход без внешних скобок: {v!r}"


def test_outcome_keys_exist_in_data_json():
    missing = sorted(set(config.OUTCOME) - DATA_IDS)
    assert not missing, f"ключи OUTCOME, отсутствующие в data.json: {missing}"


def test_default_outcome_is_valid_query():
    assert isinstance(config.DEFAULT_OUTCOME, str)
    assert config.DEFAULT_OUTCOME.startswith("(") and config.DEFAULT_OUTCOME.endswith(")")
    assert config.DEFAULT_OUTCOME.count("(") == config.DEFAULT_OUTCOME.count(")")


def test_default_outcome_equals_cog():
    """DEFAULT_OUTCOME объявлен как копия COG. Расхождение означало бы, что
    карточки без явного исхода считаются по разным определениям «когниция»."""
    assert config.DEFAULT_OUTCOME == config.COG


@pytest.mark.parametrize("key", sorted(config.SUPPLEMENTS))
def test_supplements_entry_parsable(key):
    """Параметризация по всем 74 записям: ловит пустое значение в любой."""
    term = config.SUPPLEMENTS[key]
    assert term.strip()
    assert "\n" not in term
    assert len(term) <= 120, f"{key!r}: подозрительно длинный запрос ({len(term)})"

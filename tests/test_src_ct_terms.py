"""Тесты src/ct_terms.py — поисковые термины ClinicalTrials.gov (QA_AUDIT P2-20).

Модуль не был покрыт. Используется scripts/fetch_metrics.py: по каждой карточке
ищется соответствующее исследование. Ошибка в ключе = молчаливо нулевая
выдача по этой добавке, которую никто не заметит, потому что скрипт не падает.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import ct_terms  # noqa: E402

DATA_IDS = {c["id"] for c in json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))}


def test_ct_terms_is_nonempty_dict():
    assert isinstance(ct_terms.CT_TERMS, dict)
    assert len(ct_terms.CT_TERMS) > 50, "словарь подозрительно мал"


def test_ct_terms_keys_and_values_are_nonempty_str():
    for k, v in ct_terms.CT_TERMS.items():
        assert isinstance(k, str) and k.strip(), f"ключ не строка: {k!r}"
        assert isinstance(v, str) and v.strip(), f"{k!r}: пустой термин"


def test_ct_terms_no_keyboard_typos():
    """Ключ, которого нет в data.json, — опечатка: запрос уйдёт в никуда.
    Именно так нашёлся баг в PRIOR_G (L-теанин vs L-Теанин)."""
    unknown = sorted(set(ct_terms.CT_TERMS) - DATA_IDS)
    assert not unknown, f"ключи CT_TERMS, отсутствующие в data.json: {unknown}"


def test_ct_terms_no_case_mismatch():
    lower = {i.lower() for i in DATA_IDS}
    suspicious = sorted(k for k in ct_terms.CT_TERMS if k not in DATA_IDS and k.lower() in lower)
    assert not suspicious, f"регистр ключа не совпадает с data.json: {suspicious}"


def test_ct_terms_are_ascii():
    """ClinicalTrials.gov ищет по-английски. Кириллица в поле query.intr
    даёт нулевую выдачу без всякой ошибки."""
    for k, v in ct_terms.CT_TERMS.items():
        bad = [ch for ch in v if ord(ch) > 0x2FFF or 0x0400 <= ord(ch) <= 0x04FF]
        assert not bad, f"{k!r}: не-ASCII символы в поисковом термине: {''.join(bad)!r}"


def test_ct_terms_no_booleans_as_operators():
    """Допустимы только операторы OR/AND в верхнем регистре и скобки.
    Строчное 'or' в PubMed-синтаксисе не распознаётся как оператор."""
    for k, v in ct_terms.CT_TERMS.items():
        assert not re.search(r"\s(or|and)\s", v), f"{k!r}: строчный оператор: {v!r}"
        assert v.count("(") == v.count(")"), f"{k!r}: скобки не сбалансированы"


def test_ct_terms_no_leading_trailing_whitespace():
    for k, v in ct_terms.CT_TERMS.items():
        assert v == v.strip(), f"{k!r}: пробелы по краям термина"


def test_ct_terms_coverage_above_70_percent():
    """Не все 130 карточек обязаны иметь термин (мелкие аминокислоты и
    микроэлементы в ClinicalTrials не ищутся), но покрытие ниже 70 % означает,
    что модуль устарел и данные по половине добавок молча теряются."""
    coverage = len(set(ct_terms.CT_TERMS) & DATA_IDS) / len(DATA_IDS)
    assert coverage >= 0.70, (
        f"покрытие {coverage:.0%} (< 70 %): в CT_TERMS нет "
        f"{len(DATA_IDS - set(ct_terms.CT_TERMS))} карточек"
    )


def test_ct_terms_known_entries_correct():
    """Якорные значения: если их поменяют местами, выдача потеряет смысл."""
    assert ct_terms.CT_TERMS["Креатин"] == "creatine"
    assert ct_terms.CT_TERMS["Кофеин"] == "caffeine"
    assert "vitamin D" in ct_terms.CT_TERMS["Витамин D"]
    assert "Ginkgo" in ct_terms.CT_TERMS["Гинкго"]
    assert "OR" in ct_terms.CT_TERMS["Омега-3"], "многосинонимные запросы должны использовать OR"


@pytest.mark.parametrize("key", sorted(ct_terms.CT_TERMS))
def test_ct_terms_entry_is_usable_query(key):
    """Параметризация по всем 94 записям."""
    term = ct_terms.CT_TERMS[key]
    assert term.strip()
    assert "\n" not in term and "\t" not in term
    assert len(term) <= 90, f"{key!r}: подозрительно длинный query.intr ({len(term)})"
    assert not term.startswith("OR"), f"{key!r}: запрос начинается с оператора"

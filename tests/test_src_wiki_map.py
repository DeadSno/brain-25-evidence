"""Тесты src/wiki_map.py — названия статей ru.wikipedia (QA_AUDIT P2-21).

Модуль не был покрыт. Используется scripts/fetch_metrics.py. Специфика
ru.wikipedia: имя статьи пишется С ПОДЧЁРКИВАНИЯМИ, и если в названии есть
пробел, Wikimedia отвечает 404 — молча, без исключения. Поэтому проверяем
формат имени, а не только наличие ключа.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import wiki_map  # noqa: E402

MAP = wiki_map.WIKI_RU
DATA_IDS = {c["id"] for c in json.loads((ROOT / "docs" / "data.json").read_text(encoding="utf-8"))}


def test_map_is_nonempty_dict():
    assert isinstance(MAP, dict)
    assert len(MAP) > 50, "словарь подозрительно мал"


def test_map_keys_are_real_card_ids():
    unknown = sorted(set(MAP) - DATA_IDS)
    assert not unknown, f"ключи WIKI_RU, отсутствующие в data.json: {unknown}"


def test_map_no_case_mismatch():
    lower = {i.lower() for i in DATA_IDS}
    suspicious = sorted(k for k in MAP if k not in DATA_IDS and k.lower() in lower)
    assert not suspicious, f"регистр ключа не совпадает с data.json: {suspicious}"


@pytest.mark.parametrize("key", sorted(MAP))
def test_map_article_name_uses_underscores(key):
    """ru.wikipedia отдаёт 404 на имя с пробелом. Пробелы заменяют на '_'."""
    title = MAP[key]
    assert isinstance(title, str) and title.strip(), f"{key!r}: пустое имя статьи"
    assert " " not in title, f"{key!r}: в имени статьи есть пробел — будет 404: {title!r}"


@pytest.mark.parametrize("key", sorted(MAP))
def test_map_article_name_has_no_cyrillic_punctuation(key):
    """Кавычки и типографские символы в URL-имени ломают запрос."""
    title = MAP[key]
    for ch in '"\'«»…№#?&=/\\':
        assert ch not in title, f"{key!r}: недопустимый символ {ch!r} в имени статьи"


@pytest.mark.parametrize("key", sorted(MAP))
def test_map_article_name_no_leading_trailing_underscore(key):
    title = MAP[key]
    assert title == title.strip(), f"{key!r}: пробелы по краям"
    assert not title.startswith("_") and not title.endswith("_"), f"{key!r}: подчёркивание по краю"


def test_map_no_duplicate_targets_that_look_wrong():
    """Две карточки, указывающие на одну статью, — нормально (синонимы).
    Но полное совпадение имён при разных карточках стоит увидеть глазами."""
    # не падаем: это предупреждение-информация, а не ошибка
    by_target = {}
    for k, v in MAP.items():
        by_target.setdefault(v, []).append(k)
    dupes = {t: ks for t, ks in by_target.items() if len(ks) > 1}
    assert all(len(ks) <= 4 for t, ks in dupes.items()), f"подозрительно много синонимов: {dupes}"


def test_map_coverage_above_65_percent():
    coverage = len(set(MAP) & DATA_IDS) / len(DATA_IDS)
    assert coverage >= 0.65, (
        f"покрытие {coverage:.0%} (< 65 %): без статьи "
        f"{len(DATA_IDS - set(MAP))} карточек"
    )


def test_map_known_entries_correct():
    assert MAP["Креатин"] == "Креатин"
    assert MAP["Омега-3"] == "Омега-3-ненасыщенные_жирные_кислоты"
    assert MAP["Витамин D"] == "Витамин_D"
    assert MAP["B12"] == "Витамин_B12"

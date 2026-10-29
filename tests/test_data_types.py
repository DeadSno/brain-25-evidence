"""Типы полей wiki/ongoing в данных (DATA-05, FIX-41).

Оба поля — счётчики: `wiki` — просмотры ru.wikipedia за 12 месяцев,
`ongoing` — число активных исследований. Поэтому допустимы ровно два
состояния: `int` (число) и `null` (данных нет) — как у `hedges_g`.

До FIX-41 в 40 карточках `wiki` и в 36 карточках `ongoing` вместо `null`
лежала строка «Нет данных». Тихо, но неверно: `docs/script.js:1147` и
`docs/trends.html:798` зовут `.toLocaleString(LOCALE)` и печатали
заглушку там, где ожидается число, `script.js:1126` сравнивал строку с
нулём, а `script.js:1411` выносил её в таблицу сравнения.

Почему гейт на тип, а не на значение: значения обновляет
`scripts/fetch_metrics.py` (сеть), типы — нет. Тест ловит возврат
строки-заглушки, а не изменение метрик.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA_RU = ROOT / "docs" / "data.json"
DATA_EN = ROOT / "docs" / "data_en.json"

FIELDS = ("wiki", "ongoing")

#: Сколько карточек имели число на момент FIX-41. Числа меняются только
#: вместе с пересчётом метрик (fetch_metrics.py) — тогда обновите их здесь.
BASELINE_WITH_NUMBER = {"wiki": 90, "ongoing": 94}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _en_cards() -> list[dict]:
    """docs/data_en.json — оверлей {_meta, supplements: {id: {...}}}."""
    data = _load(DATA_EN)
    assert isinstance(data, dict), "data_en.json должен быть объектом"
    supplements = data.get("supplements")
    assert isinstance(supplements, dict), "в data_en.json нет объекта supplements"
    return list(supplements.values())


def _is_number(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@pytest.fixture(scope="module")
def ru_cards() -> list[dict]:
    data = _load(DATA_RU)
    assert isinstance(data, list), "docs/data.json должен быть списком карточек"
    return data


def test_ru_wiki_ongoing_are_int_or_null(ru_cards: list[dict]) -> None:
    """Для каждой карточки: тип int или NoneType. Строк быть не может."""
    bad = []
    for card in ru_cards:
        for field in FIELDS:
            if field not in card:
                continue
            value = card[field]
            if value is None:
                continue
            if not _is_number(value):
                bad.append(f"{card['id']}: {field} = {value!r} ({type(value).__name__})")
            elif value < 0:
                bad.append(f"{card['id']}: {field} = {value} (отрицательный счётчик)")
    assert not bad, (
        "Поля wiki/ongoing — счётчики, допустимы только int и null "
        "(«нет данных» = null, см. DATA-05):\n  " + "\n  ".join(bad)
    )


def test_en_overlay_has_no_string_placeholders() -> None:
    """EN-оверлей полей не содержит; если добавит — только int или null."""
    bad = []
    for card in _en_cards():
        for field in FIELDS:
            if field not in card:
                continue
            value = card[field]
            if value is None or _is_number(value):
                continue
            bad.append(f"{card.get('id') or card.get('name')}: {field} = {value!r}")
    assert not bad, (
        "В EN-оверлее появились нечисловые wiki/ongoing — заглушка не "
        "переводится, и тип должен остаться int/null:\n  " + "\n  ".join(bad)
    )


def test_number_of_cards_with_value_is_stable(ru_cards: list[dict]) -> None:
    """Нормализация не должна молча стереть данные: числа остались числами."""
    for field, expected in BASELINE_WITH_NUMBER.items():
        with_number = sum(1 for c in ru_cards if _is_number(c.get(field)))
        assert with_number == expected, (
            f"{field}: карточек с числом {with_number}, ожидалось {expected}. "
            f"Если метрики пересчитаны (scripts/fetch_metrics.py) — обновите "
            f"BASELINE_WITH_NUMBER; если число упало само — данные потеряны."
        )


def test_normalize_check_reports_clean() -> None:
    """`scripts/normalize_wiki_ongoing.py --check` — тот же инвариант в CI."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "normalize_wiki_ongoing.py"), "--check"],
        capture_output=True, text=True, cwd=str(ROOT), encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"типы wiki/ongoing разъехались.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

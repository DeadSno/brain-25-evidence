"""Распределение грейдов на странице == распределение в данных.

Контекст. `tests/test_integration_api_db.py` уже проверяет, что грейды в API и
в DuckDB совпадают. Но между этими двумя слоями есть третий — текст
`docs/methodology.html`, — который никто не проверял. Из-за этого расхождение
пережило зелёный прогон: страница показывала A 8 / B 40 / C 42 / D 13
(сумма 103) с заголовком «130 добавок», тогда как в `data.json` было
A 8 / B 45 / C 52 / D 25 (сумма 130).

Хуже всего, что расходилось именно число «не подтверждено»: 13 на странице
против 25 в данных, то есть доля неподтверждённых добавок была занижена
почти вдвое — на странице, чья работа состоит в том, чтобы доказывать
честность проекта.

Тест закрывает именно этот разрыв: он связывает текст страницы с источником
правды, чтобы числа на methodology.html нельзя было обновить «на глаз».
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "docs" / "data.json"
METHODOLOGY = ROOT / "docs" / "methodology.html"

GRADES = ("A", "B", "C", "D")

# «A (работает отлично):</b> 8 добавок (6.2%)»
_ROW = re.compile(
    r"\b(?P<grade>[ABCD])\s*\([^)]*\)\s*:?\s*</b>\s*"
    r"(?P<count>\d+)\s+добав\w*\s*\((?P<pct>[\d.,]+)\s*%\)"
)


def _data_grades():
    """Реальное распределение по источнику правды."""
    cards = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    counts = Counter(c["grade"] for c in cards if c.get("grade"))
    missing = [g for g in GRADES if g not in counts]
    assert not missing, f"в data.json нет грейдов {missing}"
    return counts, len(cards)


def _page_grades():
    """Числа, напечатанные на странице."""
    html = METHODOLOGY.read_text(encoding="utf-8")
    block = re.search(r"Распределение грейдов.{0,900}?</ul>", html, re.S)
    assert block, "на methodology.html не найден блок «Распределение грейдов»"
    rows = {m.group("grade"): (int(m.group("count")), m.group("pct"))
            for m in _ROW.finditer(block.group(0))}
    assert set(rows) == set(GRADES), f"на странице грейды {sorted(rows)}"
    return rows


def test_page_counts_match_data_json():
    """Числа карточек на странице == числа в data.json."""
    counts, total = _data_grades()
    rows = _page_grades()
    for g in GRADES:
        assert rows[g][0] == counts[g], (
            f"methodology.html: грейд {g} показан как {rows[g][0]}, "
            f"в data.json — {counts[g]}"
        )
    assert sum(v[0] for v in rows.values()) == total, (
        f"сумма на странице {sum(v[0] for v in rows.values())}, "
        f"а карточек в data.json {total}"
    )


def test_page_percentages_match_data_json():
    """Проценты на странице посчитаны от общего числа карточек."""
    counts, total = _data_grades()
    rows = _page_grades()
    for g in GRADES:
        expected = counts[g] / total * 100
        shown = float(rows[g][1].replace(",", "."))
        assert abs(shown - expected) < 0.1, (
            f"methodology.html: грейд {g} показан как {shown}%, "
            f"по data.json {expected:.1f}% ({counts[g]} из {total})"
        )


def test_page_percentages_sum_to_100():
    """Проценты складываются в 100 — иначе база расчёта не 130."""
    rows = _page_grades()
    total = sum(float(v[1].replace(",", ".")) for v in rows.values())
    assert abs(total - 100.0) < 0.5, f"сумма процентов на странице {total}%"


def test_page_header_states_card_total():
    """Заголовок называет тот же размер каталога, что и данные.

    Именно здесь была подмена: «(130 добавки)» над суммой 103.
    """
    _, total = _data_grades()
    html = METHODOLOGY.read_text(encoding="utf-8")
    head = re.search(r"Распределение грейдов\s*\((\d+)\s+добав\w*\)", html)
    assert head, "в заголовке блока нет количества добавок"
    assert int(head.group(1)) == total, (
        f"заголовок обещает {head.group(1)} добавок, в data.json — {total}"
    )


def test_every_card_has_grade():
    """Каждая карточка грейдирована — иначе сумма грейдов < 130."""
    cards = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    assert all(c.get("grade") for c in cards), "есть карточки без грейда"
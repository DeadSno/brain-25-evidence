"""Гейт на индикатор фокуса (A11Y-P2-03).

Находка reports/audits/a11y.md:22 утверждала, что одна ссылка в
docs/trends.html осталась без индикатора фокуса. Перемер 16.10.2026 её не
подтвердил: `*:focus-visible` в docs/style.css:270 покрывает вообще все
элементы, а `outline:none` / `outline:0` не встречаются ни разу - ни в CSS,
ни в разметке. Находка закрыта как ложная.

Но сама находка полезна: она показала, что индикатор фокуса держится на
одной строке, и потерять его можно не заметив - тесты на это не смотрели.
Поэтому ценность этого гейта не в разборе прошлого, а в том, что следующий,
кто случайно снимет контур, увидит это на CI, а не на клавиатуре.

Что ловится:
  * исчезновение или сужение универсального правила;
  * `outline:none` в CSS или в разметке (классический способ убить фокус);
  * `:focus:not(:focus-visible){outline:none}` - «спрятать фокус для мыши»,
    который вместе с мышью убивает и клавиатуру;
  * возврат правила внутрь @media/@supports, где оно перестаёт работать.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "docs" / "style.css"

COMMENT = re.compile(r"/\*.*?\*/", re.S)
# outline без значения - это не подавление, вырезаем
OUTLINE_NONE = re.compile(r"outline\s*:\s*(?:none|0)\b")
GLOBAL_RULE = re.compile(r"\*:focus-visible\s*\{([^}]*)\}")
MOUSE_ONLY_RESET = re.compile(r":focus\s*:not\s*\(\s*:focus-visible\s*\)")

# Минимальная толщина контура: WCAG 2.4.11 (Focus Appearance, AA) требует
# не менее 2px по периметру. Меньше - формально не индикатор.
MIN_OUTLINE_PX = 2


def _css_without_comments() -> str:
    return COMMENT.sub(" ", CSS.read_text(encoding="utf-8"))


def _html_files() -> list[Path]:
    docs = ROOT / "docs"
    return sorted(p for p in docs.rglob("*.html"))


def _brace_depth_at(css: str, pos: int) -> int:
    """Вложен ли фрагмент в @media/@supports. Считаем только незакрытые скобки."""
    return css[:pos].count("{") - css[:pos].count("}")


def test_global_focus_visible_rule_exists() -> None:
    """Универсальное правило обязано быть и задавать видимый контур."""
    css = _css_without_comments()
    matches = GLOBAL_RULE.findall(css)
    assert matches, (
        "Правило *:focus-visible пропало из docs/style.css. Без него ни один "
        "элемент не покажет фокус с клавиатуры - вернуть его нужно явно, "
        "а не рассчитывая на браузерное умолчание (оно разное и убрано "
        "во многих темах)."
    )
    body = matches[0]
    assert "outline" in body, (
        f"*:focus-visible задаёт {body.strip()!r} - без outline это не "
        "индикатор фокуса."
    )
    width = re.search(r"outline\s*:\s*(\d+(?:\.\d+)?)px", body)
    assert width, (
        f"В *:focus-visible толщина контура не в пикселях: {body.strip()!r}. "
        "Гейт не может проверить WCAG 2.4.11 по нечитаемому значению."
    )
    assert float(width.group(1)) >= MIN_OUTLINE_PX, (
        f"Контур фокуса {width.group(1)}px тоньше минимума {MIN_OUTLINE_PX}px "
        "(WCAG 2.4.11 Focus Appearance)."
    )
    assert "outline-offset" in body, (
        "Без outline-offset контур рисуется вплотную к границе элемента и на "
        "светлом фоне сливается с ним."
    )


def test_focus_rule_is_top_level() -> None:
    """Правило внутри @media перестаёт быть универсальным."""
    css = _css_without_comments()
    m = GLOBAL_RULE.search(css)
    assert m is not None
    assert _brace_depth_at(css, m.start()) == 0, (
        "*:focus-visible оказался вложен в @media/@supports. На узких "
        "вьюпортах или в браузере без поддержки контейнера элементы останутся "
        "без индикатора фокуса."
    )


def test_outline_is_not_suppressed_in_css() -> None:
    """outline:none в CSS - это всегда осознанное решение, здесь его нет."""
    css = _css_without_comments()
    bad = [m.group(0) for m in OUTLINE_NONE.finditer(css)]
    assert not bad, (
        f"В docs/style.css появилось подавление контура: {bad}. Универсальное "
        "*:focus-visible тут же перестаёт работать. Если элемент декоративный, "
        "сделайте его нефокусируемым (tabindex=\"-1\"), а не снимайте контур."
    )


def test_outline_is_not_suppressed_in_markup() -> None:
    """То же в разметке: inline-стиль перекрывает таблицу стилей."""
    offenders = []
    for path in _html_files():
        text = path.read_text(encoding="utf-8")
        for m in OUTLINE_NONE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            offenders.append(f"{path.relative_to(ROOT)}:{line}")
    assert not offenders, (
        f"В разметке найдено outline:none/0: {offenders[:20]}. Inline-стиль "
        "перекрывает *:focus-visible, и элемент теряет индикатор фокуса."
    )


def test_no_mouse_only_focus_reset() -> None:
    """:focus:not(:focus-visible){outline:none} убивает и клавиатуру тоже."""
    css = _css_without_comments()
    bad = [m.group(0) for m in MOUSE_ONLY_RESET.finditer(css)]
    assert not bad, (
        f"Найден сброс фокуса «только для мыши»: {bad}. Селектор не различает "
        "источник фокуса в поддерживаемых браузерах, поэтому индикатор "
        "пропадает и при навигации с клавиатуры."
    )


def test_focus_gate_covers_all_pages() -> None:
    """Сами тесты не должны молча схлопнуться до нуля файлов."""
    files = _html_files()
    assert len(files) >= 140, (
        f"Проверено всего {len(files)} HTML-страниц. Гейт на разметке "
        "перестал бы работать при смене пути или сбое обхода."
    )
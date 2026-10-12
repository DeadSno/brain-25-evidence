"""Гейт на фиксированные min-width в docs/style.css (I18N-P1-05).

Аудит reports/audits/i18n.md:20 требовал заменить все жёсткие min-width на
адаптивные min(Npx, 100%), потому что фиксированная ширина мешает узким
раскладкам и длинным переводам. Замер 2026-10-12 показал, что из трёх
предложенных мест НИ ОДНО не переполнялось ни на одном вьюпорте, а одно
было by design:

  #controls input/select  был 150px   -> стал min(150px, 100%)
  #search                 был 250px   -> стал min(250px, 100%)
  #compareResult table    520px      -> оставлено, это отзывчивая таблица

То есть правки не сдвинули ни одного пикселя. Ценность не в правках, а в
том, что решение зафиксировано и не размылось: следующий, кто увидит
min-width:300px, должен либо обосновать его, либо сделать адаптивным.

Комментарии вырезаются перед разбором. Без этого тест падал бы на
собственных пояснениях вида «было min-width:150px» - то есть поощрял бы
вычеркнуть объяснение вместо самой правки.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / "docs" / "style.css"

COMMENT = re.compile(r"/\*.*?\*/", re.S)
MIN_WIDTH = re.compile(r"min-width\s*:\s*([^;}]+)")

# Единственные фиксированные ненулевые ширины, которые в проекте остались.
# Новое значение сюда не добавляют молча: это делается вместе с причиной.
ALLOWED_FIXED = {
    "44px": (
        "минимальная площадь тап-таргета (WCAG 2.5.8), требование a11y, "
        "а не ширина макета. Применяется к кнопкам, чипам и иконкам."
    ),
    "520px": (
        "таблица сравнения внутри контейнера с overflow-x:auto: колонки "
        "сохраняют читаемую ширину, прокручивается только таблица. Проверка "
        "пары таблица/контейнер - test_table_scroll_container_is_paired."
    ),
}

# Место, где живут оба правила форм-контролов. min(..., 100%) здесь
# обязателен: он не даёт контролу вылезти за страницу, если он окажется в
# колонке уже заявленной ширины.
CONTROLS_RULE = "#controls input,#controls select{flex:1;min-width:min(150px,100%)}"
SEARCH_RULE = "#search { min-width: min(250px, 100%); flex: 1 1 250px; }"

TOUCH_TARGET_PX = 44


def _css_without_comments() -> str:
    return COMMENT.sub(" ", CSS.read_text(encoding="utf-8"))


def _fixed_widths() -> dict[str, int]:
    """Фиксированные ненулевые min-width в пикселях -> сколько раз встретились."""
    found: dict[str, int] = {}
    for raw in MIN_WIDTH.findall(_css_without_comments()):
        value = raw.strip().rstrip("!").strip()
        if "min(" in value or "max(" in value:
            continue  # адаптивное значение, ровно то, чего требует аудит
        if "0" in value.split():
            continue  # сброс: min-width:0 снимает автоматический размер флекс-элемента
        match = re.fullmatch(r"(\d+)px", value)
        if match:
            px = f"{match.group(1)}px"
            found[px] = found.get(px, 0) + 1
    return found


def test_no_unjustified_fixed_min_width() -> None:
    """Каждое фиксированное min-width должно быть в списке с причиной."""
    found = _fixed_widths()
    unknown = set(found) - set(ALLOWED_FIXED)
    assert not unknown, (
        "Появилось фиксированное min-width без обоснования: "
        f"{sorted(unknown)} (все найденные: {found}). "
        "Либо сделайте его адаптивным min(Npx, 100%), либо внесите значение "
        "в ALLOWED_FIXED вместе с причиной - иначе возврат долга будет "
        "выглядеть как обычное оформление."
    )


def test_allowed_widths_are_actually_used() -> None:
    """Запись в ALLOWED_FIXED не должна протухать незамеченной."""
    found = _fixed_widths()
    missing = set(ALLOWED_FIXED) - set(found)
    assert not missing, (
        f"ALLOWED_FIXED перечисляет {sorted(missing)}, которых в style.css "
        "больше нет. Удалите запись вместе с причиной, иначе гейт разрешает "
        "значение, которого никто не проверяет."
    )


def test_touch_target_width_is_not_reduced() -> None:
    """44px - это WCAG 2.5.8, а не вкусовое. Уменьшать нельзя."""
    widths = sorted(int(px[:-2]) for px in _fixed_widths() if px.endswith("px"))
    touch = [px for px in widths if px <= 80]
    assert touch, "Тап-таргеты перестали задаваться min-width - проверьте стили"
    assert min(touch) >= TOUCH_TARGET_PX, (
        f"Минимальная ширина тап-таргета упала до {min(touch)}px при "
        f"требуемых {TOUCH_TARGET_PX}px (WCAG 2.5.8)."
    )


def test_form_controls_are_clamped_to_their_container() -> None:
    """Оба правила форм-контролов обязаны быть адаптивными (I18N-P1-05)."""
    css = _css_without_comments()
    assert CONTROLS_RULE in css, (
        "Правило #controls input вернулось к фиксированной ширине. "
        "Фиксированный min-width у флекс-элемента не даёт ему сжаться "
        "до размера контейнера."
    )
    assert SEARCH_RULE in css, (
        "Правило #search вернулось к фиксированной ширине."
    )


def test_table_scroll_container_is_paired() -> None:
    """Таблица с фиксированной шириной обязана быть в прокручиваемом контейнере.

    Порознь обе половины выглядят безобидно: таблица без overflow
    раздувает страницу горизонтальной прокруткой, контейнер без таблицы
    ничего не делает. Вместе - это отзывчивая таблица.
    """
    css = _css_without_comments()
    assert "#compareResult table{min-width:520px}" in css
    assert "#compareResult{overflow-x:auto}" in css, (
        "Контейнер таблицы сравнения потерял overflow-x:auto, а таблица "
        "осталась фиксированной ширины 520px. Страница начнёт "
        "прокручиваться вбок."
    )
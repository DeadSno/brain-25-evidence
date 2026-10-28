"""Физические CSS-свойства в разметке запрещены — только логические.

Зачем этот тест
---------------
Интерфейс двуязычный (русский/английский), значит рано или поздно
появится `dir="rtl"`. Физическое `margin-left: 12px` в RTL не
переворачивается: отступ останется слева, и полоса уедет не с той
стороны. Страница при этом не падает и не ломается — она просто
выглядит неправильно, и заметить это можно только в RTL-рендере,
которого в проекте нет.

Свойства `margin-inline-start`, `inset-inline-end` и прочие логические
работают в обоих направлениях по построению, поэтому проверка решается
статически, без браузера.

Что проверяется
---------------
Объявления CSS в `docs/*.html` — и в блоках `<style>`, и в атрибутах
`style="..."` (в `index.html` есть `style="...padding-left:1.2rem..."`,
и только сканирование `<style>` его пропустило бы). Плюс отдельные
`.css`-файлы в `docs/`.

Что НЕ проверяется
------------------
* `docs/sup/` — 131 сгенерированная страница генератором, физические
  свойства там изначально заведены осознанно; правка идёт в генераторе,
  а не в выводе.
* `docs/style.css` — общий файл, используется всеми 76 снапшотами.
  Перевод на логические свойства там затрагивает раскладку каждой
  страницы разом и требует пересъёмки всего набора; это отдельная
  задача, не эта.
* `docs/vendor/` — сторонний CSS, переписывать нельзя.
* `legacy.css` — в проекте такого файла нет; имя оставлено в
  исключениях, чтобы при появлении файла его не пришлось вспоминать.

Ратчет
------
`KNOWN_DEBT` — список известных нарушений. Тест зелёный, пока
нарушения не выходят за этот список, и падает, если список перестал
совпадать с реальностью или вырос. Декларация `DEBT_BUDGET` держит
потолок: при починке страниц он уменьшается, но никогда не
увеличивается. Так долг виден числом и не может тихо вернуться.

Состояние на 2026-10-14: долг закрыт полностью, `KNOWN_DEBT` пуст,
`DEBT_BUDGET = 0`. Открытым остаётся `docs/style.css` — см. выше.
Механизм ратчета оставлен: вернуть долг можно только явной правкой
теста, и она видна в diff.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

#: Файлы вне области действия гейта.
SKIP_DIRS = ("sup", "vendor", "adr", "api", "bpmn", "briefs", "dev", "icons")
#: Имена файлов вне области действия гейта.
#: `style.min.css` — сгенерированная копия `style.css` (FIX-44, csso-cli):
#: гейт смотрит на исходники, а минифицированный файл повторяет те же
#: объявления, только в одну строку, и править его вручную нельзя.
SKIP_FILES = ("style.css", "style.min.css", "legacy.css")

#: Физическое свойство -> логическая замена.
#: Важно: `padding-left` -> `padding-inline-START`, а НЕ `padding-inline`.
#: `padding-inline` ставит обе оси сразу, то есть добавляет отступ ещё и
#: справа — в LTR это не 0 расхождений, а вдвое больший отступ.
#: То же с `border-left` -> `border-inline-start`, а не `border-inline`.
LOGICAL_REPLACEMENT = {
    "margin-left": "margin-inline-start",
    "margin-right": "margin-inline-end",
    "padding-left": "padding-inline-start",
    "padding-right": "padding-inline-end",
    "border-left": "border-inline-start",
    "border-right": "border-inline-end",
    "left": "inset-inline-start",
    "right": "inset-inline-end",
}

#: Ключи - начала имён физических свойств, значение - подсказка.
#: Суффиксы вида `-color`/`-width`/`-style` допускаются:
#: `border-left-color` -> `border-inline-start-color`.
_BASE_PROPS = "|".join(sorted(LOGICAL_REPLACEMENT, key=len, reverse=True))

DECL_RE = re.compile(
    rf"(?<![\w-])({_BASE_PROPS})(?![\w])(?:-[a-z]+)?\s*:",
    re.IGNORECASE,
)
#: CSS-комментарии: `border-left` внутри комментария не объявление.
COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
#: Скрипты: `left:` внутри строки JS не объявление CSS. Вырезаем,
#: сохраняя переводы строк, чтобы номера строк не поехали.
SCRIPT_RE = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.S | re.I)

#: Известный долг: {(файл, свойство): сколько раз}.
#: Был 9 страниц / 31 объявление; закрыт 2026-10-14 (Batch 8A, 1b).
#: Пустой словарь — осознанно, а не «не нашли»: сканер проверен на
#: заведомо грязном состоянии и там нашёл ровно 19 пар.
KNOWN_DEBT: dict[tuple[str, str], int] = {}

#: Потолок долга. Уменьшается по мере починки, не растёт. Долг закрыт — 0.
DEBT_BUDGET = 0


def _filler(text: str) -> str:
    """Заменяет текст на пробелы, сохраняя число переводов строк."""
    out = []
    for ch in text:
        out.append("\n" if ch == "\n" else " ")
    return "".join(out)


def _scan_text(text: str) -> list[tuple[int, str]]:
    """Возвращает [(номер строки, физическое свойство)]."""
    text = SCRIPT_RE.sub(lambda m: m.group(1) + _filler(m.group(2)) + m.group(3), text)
    text = COMMENT_RE.sub(lambda m: _filler(m.group(0)), text)

    found: list[tuple[int, str]] = []
    for match in DECL_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        found.append((line, match.group(1).lower()))
    return found


def _iter_targets() -> list[Path]:
    targets: list[Path] = []
    for path in sorted(DOCS.glob("*.html")):
        targets.append(path)
    for path in sorted(DOCS.rglob("*.css")):
        rel = path.relative_to(DOCS)
        if rel.parts[0] in SKIP_DIRS or path.name in SKIP_FILES:
            continue
        targets.append(path)
    return targets


def _collect() -> dict[tuple[str, str], int]:
    actual: dict[tuple[str, str], int] = {}
    for path in _iter_targets():
        text = path.read_text(encoding="utf-8")
        for _line, prop in _scan_text(text):
            key = (path.name, prop)
            actual[key] = actual.get(key, 0) + 1
    return actual


def test_no_physical_css_properties() -> None:
    """Вне KNOWN_DEBT физических свойств быть не должно."""
    actual = _collect()

    unexpected = {
        key: count for key, count in actual.items() if key not in KNOWN_DEBT
    }
    stale = {key for key in KNOWN_DEBT if key not in actual}

    assert not unexpected and not stale, (
        "Физические CSS-свойства вне списка известного долга.\n"
        "Замена: margin-left -> margin-inline-start, "
        "margin-right -> margin-inline-end,\n"
        "  padding-left -> padding-inline-start (НЕ padding-inline: "
        "тот ставит обе оси),\n"
        "  padding-right -> padding-inline-end, "
        "border-left -> border-inline-start,\n"
        "  border-right -> border-inline-end, left -> inset-inline-start, "
        "right -> inset-inline-end.\n"
        + "\n".join(
            f"  {name}:{prop} x{count} -> {LOGICAL_REPLACEMENT[prop]}"
            for (name, prop), count in sorted(unexpected.items())
        )
        + (
            "\nПротухшие записи KNOWN_DEBT (нарушения уже исправлены, "
            "уберите их из списка):\n"
            + "\n".join(f"  {name}:{prop}" for name, prop in sorted(stale))
            if stale
            else ""
        )
    )


def test_known_debt_shrinks_only() -> None:
    """Долг не может вырасти сверх потолка, зафиксированного при ревизии."""
    assert len(KNOWN_DEBT) <= DEBT_BUDGET, (
        f"Долг вырос: записей {len(KNOWN_DEBT)}, потолок {DEBT_BUDGET}. "
        "Новые физические свойства не добавляются — только переводятся "
        "существующие на логические."
    )
    for key in KNOWN_DEBT:
        assert key[1] in LOGICAL_REPLACEMENT, f"Неизвестное свойство в долге: {key}"


def test_logical_replacements_are_side_specific() -> None:
    """Страховка от шорткатов, которые ставят обе оси сразу."""
    for physical, replacement in LOGICAL_REPLACEMENT.items():
        if physical in ("margin", "padding", "border"):
            continue
        assert not replacement.endswith("-inline"), (
            f"{physical} -> {replacement} ставит обе оси и в LTR даёт "
            "двойной отступ. Нужен вариант -start/-end."
        )

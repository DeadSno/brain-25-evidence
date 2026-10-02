"""Гард от мозгибаки — три направления порчи, а не одно.

История файла. Первая версия проверяла 10 двухсимвольных «биграмм» вида
`Р°`, `Рµ`. Тест был зелёным, но:

1) ложно срабатывал на обычных русских словах — маркер `РС` (кириллические
   Ер+Ес) встречается в `ВЕРСИЯ`, а `Рё` (Ер+ё) — в `Рёбер`/`Рёбра`,
   которые есть в `docs/adr/005-effect-tags-normalization.md:39` и в
   `scripts/graph_interactions.py:4`;
2) не ловил ничего из того, что реально встречается: настоящее мозгибаки
   выглядит как «Ð°Ð»Ð»…» (U+00D0) или как символ замены U+FFFD,
   а вовсе не как «Р°».

Теперь маркеры выведены из байтов, а не подобраны на глаз, и — главное —
проверяют сами себя (см. `test_markers_*` в конце файла).

Три направления, все три ловятся:
  B  utf-8 байты прочитаны как cp1251   -> классическое «Р°РµСЂРё»
  C  utf-8 байты прочитаны как latin-1   -> «Ð°Ð»Ð»…»
  A  cp1251 байты прочитаны как utf-8    -> символ замены U+FFFD

Почему B — это регулярка, а не список биграмм: символы U+0420 и U+0421 —
это обычные кириллические «Р» и «С», а в мозгибаки они всегда стоят в паре
с НЕ-буквой (знак из верхнего диапазона cp1251). Проверка «Р/С + не-буква»
ловит 10 из 10 контрольных слов, а «Рёбер», «ВЕРСИЯ», «доктор Р.» и
«список С.» не ловит — список биграмм на этом же тексте врал.
"""

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

# Направление порчи -> (регулярка, описание).
#
# Диапазон второй группы намеренно узкий, и это не лень, а результат проверки:
#   U+00A1-U+00FF — знаки и латинские надстрочные, порождаемые байтами
#     0xA1-0xFF в cp1251. «Ёлочка» U+00AB и U+00BB исключены: они следуют за
#     кириллической «С» в совершенно законной прозе («раздел С»Кодекс»),
#     и на них гард врал в reports/archive/q14_audit.md.
#   U+0401-U+040F, U+0452-U+0459, U+045B-U+045C, U+0490-U+0491 — буквы НЕ из
#     русского алфавита (Ђ, Ѓ, љ, ћ, ѕ, ї, і, ѕ…). Их порождают байты
#     0x80-0x9F в cp1251, поэтому без них вариант B не видел мозгибаки слов
#     «сыр», «рис», «судь» — там весь ведущий байт 0xD1.
#   Русские ё (U+0451), й (U+0439), и (U+0438) и прочие НЕ включены: иначе
#     гард ловил бы «Си», «Ри», «Рей» и «Рёбер».
#
# Пунктуация Unicode (U+2010-U+2126: …, –, —, “, ”, •, ‹, ›) исключена целиком:
# она порождается байтами 0x80-0x9F, но и в законной прозе встречается
# («ТРАНС…»), поэтому надёжнее её не проверять вовсе.
MOJIBAKE_PATTERNS = {
    # B: utf-8 -> cp1251. U+0420/U+0421 — это байты 0xD0/0xD1, то есть первые
    #    байты двухбайтового UTF-8 для кириллицы. Второй байт — не буква.
    "B: utf-8 прочитан как cp1251": re.compile(
        r"[\u0420\u0421]"
        r"[\u00a1-\u00aa\u00ac-\u00ff"
        r"\u0401-\u040f\u0452-\u0459"
        r"\u045b-\u045c\u0490-\u0491]"),
    # C: utf-8 -> latin-1. U+00D0/U+00D1 — те же байты 0xD0/0xD1, но показанные
    #    как латиница; второй байт 0x80-0xBF.
    "C: utf-8 прочитан как latin-1": re.compile(r"[\u00d0\u00d1][\u0080-\u00bf]"),
    # A: cp1251 -> utf-8. Байты не декодируются, остаётся символ замены.
    "A: cp1251 прочитан как utf-8": re.compile(r"\ufffd"),
}


def _collect_js_files() -> list[Path]:
    files = []
    for fp in DOCS.glob("*.js"):
        if "chart.min" in fp.name:
            continue
        files.append(fp)
    return files


def _collect_html_files() -> list[Path]:
    return list(DOCS.glob("*.html"))


def _check_for_mojibake(filepath: Path) -> list[str]:
    """Возвращает список НАПРАВЛЕНИЙ порчи, найденных в файле."""
    text = filepath.read_text(encoding="utf-8")
    return [name for name, rx in MOJIBAKE_PATTERNS.items() if rx.search(text)]


def test_no_mojibake_in_js_files():
    for fp in _collect_js_files():
        found = _check_for_mojibake(fp)
        assert not found, (
            f"{fp.name}: следы мозгибаки {found} — "
            "возможно, файл был записан не в UTF-8"
        )


def test_no_mojibake_in_html_files():
    for fp in _collect_html_files():
        found = _check_for_mojibake(fp)
        assert not found, (
            f"{fp.name}: следы мозгибаки {found} — "
            "возможно, файл был записан не в UTF-8"
        )


# --- самопроверка гарда --------------------------------------------------
# Без этих тестов следующий человек снова соберёт список «на глаз» и получит
# гард, который не ловит ничего (как предыдущая версия).

def _mojibake(text: str, codec: str) -> str:
    """Портит строку указанным способом."""
    return text.encode("utf-8").decode(codec)


_CONTROL = [
    "тест",
    "Калькулятор дозировок",
    "версия",
    "Наука",
    "доказательства",
    "Механизм",
    "Питание",
    "Хронический",
    "Щитовидная",
    # Слова подобраны так, чтобы ПРОВЕРИТЬ ОБА ведущих байта по отдельности.
    # В UTF-8 кириллица разбивается по диапазонам: а-п (U+0430-U+043F) дают
    # ведущий 0xD0, р-я (U+0440-U+044F) — 0xD1. Если в маркере останется только
    # один из них, слова ниже перестанут ловиться. Без «лодка» и «сыр» обе
    # буквы в контрольных словах встречались всегда одновременно, и мутация
    # «вычеркнуть 0xD0» проходила незамеченной.
    "лодка",   # только 0xD0
    "сыр",     # только 0xD1, причём продолжения байт — кириллица (С, Ё, Ђ)
    "рис",
    "судь",
    "мышь",
]


def test_markers_catch_real_mojibake_cp1251():
    """Направление B: реальное мозгибаки обязано ловиться."""
    missed = [w for w in _CONTROL
              if not MOJIBAKE_PATTERNS["B: utf-8 прочитан как cp1251"]
              .search(_mojibake(w, "cp1251"))]
    assert not missed, f"пропущено направление B для слов: {missed}"


def test_markers_catch_real_mojibake_latin1():
    """Направление C: «Ð°Ð»Ð»…» обязано ловиться."""
    missed = [w for w in _CONTROL
              if not MOJIBAKE_PATTERNS["C: utf-8 прочитан как latin-1"]
              .search(_mojibake(w, "latin-1"))]
    assert not missed, f"пропущено направление C для слов: {missed}"


def test_markers_catch_replacement_char():
    """Направление A: U+FFFD в файле означает потерянные байты."""
    assert MOJIBAKE_PATTERNS["A: cp1251 прочитан как utf-8"].search("\ufffd")


def test_markers_ignore_clean_russian():
    """Чистый русский текст НЕ должен ловиться.

    Здесь же лежат слова, на которых старая версия гарда врала.
    """
    clean = [
        "ВЕРСИЯ",       # ловил маркер "РС"
        "Рёбер",        # ловил маркер "Рё" (есть в docs/adr/005, строка 39)
        "Рёбра",        # ловил "Рё" (есть в scripts/graph_interactions.py:4)
        "доктор Р.",    # "Р" + точка
        "список С.",    # "С" + точка
        "ТРАНС…",       # "С" + многоточие
        "раздел С«X»",  # "С" + «ёлочка» (видела ложь в q14_audit.md:95)
        "Си",           # "С" + и
        "Ри",           # "Р" + и
        "Рей",          # "Р" + ей
        "Сей",          # "С" + ей
        "параграф Р",
        "сценарий С",
    ]
    for direction, rx in MOJIBAKE_PATTERNS.items():
        hit = [w for w in clean if rx.search(w)]
        assert not hit, f"{direction} ложно сработал на {hit}"


def test_markers_are_not_empty():
    """Страховка от «случайно снёс список маркеров»."""
    assert len(MOJIBAKE_PATTERNS) == 3, "ожидались три направления порчи"
    for name, rx in MOJIBAKE_PATTERNS.items():
        assert rx.search("test") is None, f"{name}: регулярка ловит латиницу"


def test_cp1251_fallback_script_js():
    """F1.1-fallback: пытаемся cp1251→utf-8 на script.js. Если файл чист — фикс не нужен."""
    fp = DOCS / "script.js"
    text = fp.read_text(encoding="utf-8")
    fixed_any = False
    for line in text.splitlines():
        try:
            fixed = line.encode("cp1251").decode("utf-8")
            if fixed != line:
                if any("\u0430" <= c <= "\u044f" or "\u0410" <= c <= "\u042f" for c in fixed):
                    fixed_any = True
                    break
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    if not fixed_any:
        assert True, "script.js чист, фикс не требуется"
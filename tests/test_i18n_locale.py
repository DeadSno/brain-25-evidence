"""Локаль формата берётся из разметки, а не вписана в код (I18N-P2-04).

Проблема
--------
В скриптах и разметке было 9 вхождений литерала `ru-RU`:
`toLocaleString('ru-RU')` в script.js и trends.html (8 штук) плюс
`new Intl.DateTimeFormat('ru-RU', ...)` в science2.js. Каждое из них —
отдельное место, которое при переводе страницы легко забыть: меняешь
`lang="en"` в <html>, текст вокруг становится английским, а числа
остаются русскими. Разъезд виден только на странице с числами.

Решение
-------
Все девять мест используют константу `LOCALE`, объявленную в каждом
файле как `document.documentElement.lang || 'ru'`. Дальше локаль
меняется в одном месте — в атрибуте lang.

`ru-RU` и `ru` для Intl дают одинаковый результат, поэтому поведение
при русском языке не изменилось.

Что проверяется
---------------
1. В первоклассном JS и HTML нет литералов локалей вида `xx-YY`.
   Вендор пропускается: chart.js не наш код и переводить его не нужно.
2. Где LOCALE используется, он обязан быть объявлен — иначе страница
   падает на ReferenceError, а это заметят только те, у кого
   отработала именно эта ветка.
3. Объявление читает <html lang>, а не содержит зашитую локаль:
   иначе константа существует, но задача не решена.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

#: BCP-47 в виде xx-YY или xx-Yyyy-ZZ. Проверяем только такие: одиночный
#: `ru` в разметке — это lang, а не хардкод формата.
LOCALE_LITERAL = re.compile(r"""['"]([a-z]{2,3}-[A-Z]{2,3}(?:-[A-Z]{2,4})?)['"]""")

DECL = re.compile(r"const\s+LOCALE\s*=\s*document\.documentElement\.lang\s*\|\|\s*'([a-z]{2})'")


def _sources() -> list[tuple[str, str]]:
    """Первоклассные JS и HTML. Вендор исключён."""
    out: list[tuple[str, str]] = []
    for p in sorted(DOCS.rglob("*")):
        if not p.is_file() or p.suffix not in {".js", ".html"}:
            continue
        if p.parent.name == "vendor":
            continue
        text = p.read_text(encoding="utf-8")
        if "LOCALE" not in text and not LOCALE_LITERAL.search(text):
            continue
        out.append((p.relative_to(ROOT).as_posix(), text))
    return out


def _strip_comments(text: str) -> str:
    """Комментарии объясняют правку и сами содержат литерал.

    Без этого тест падал бы на собственном пояснении — то есть
    поощрял бы удалять объяснение вместо хардкода.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def test_no_hardcoded_locale_literals():
    offenders = []
    for name, text in _sources():
        for m in LOCALE_LITERAL.finditer(_strip_comments(text)):
            offenders.append(f"{name}: {m.group(1)}")
    assert not offenders, (
        f"Локаль вписана литералом в {len(offenders)} местах:\n"
        + "\n".join(f"  {o}" for o in offenders)
        + "\nОбъяви const LOCALE = document.documentElement.lang || 'ru' "
          "и используй её."
    )


def test_locale_is_declared_wherever_it_is_used():
    undeclared = [
        name for name, text in _sources()
        if re.search(r"\bLOCALE\b", _strip_comments(text)) and not DECL.search(text)
    ]
    assert not undeclared, (
        f"LOCALE используется, но не объявлена через <html lang>: "
        f"{', '.join(undeclared)}. Без объявления страница падает "
        f"на ReferenceError — но только там, где отработала ветка."
    )


def test_locale_declaration_reads_the_document_language():
    """Константа должна брать язык из разметки, а не зашивать его."""
    for name, text in _sources():
        if re.search(r"\bLOCALE\b", _strip_comments(text)):
            assert DECL.search(text), (
                f"{name}: LOCALE объявлена не из document.documentElement. "
                "Константа существует, но задача не решена — язык всё ещё "
                "зашит в код."
            )
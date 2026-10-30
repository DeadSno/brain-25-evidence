"""В английском режиме на страницах не остаётся русского текста (FIX-75).

Проблема
--------
FIX-74 перевёл весь интерфейс на английский, но проверка была ручной:
Playwright открывал 14 страниц с ``localStorage['lang'] = 'en'`` и считал
кириллические слова. Ручная проверка не защищает от регрессии — достаточно
добавить абзац в ``docs/faq.html`` без ``data-i18n-text``, и русский текст
вернётся на английскую страницу, причём обнаружится это уже после релиза.

Решение
-------
Гейт работает без браузера и без сервера: он должен попадать в быстрый
прогон ``-m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"``,
а не в браузерные маркеры. Английский режим имитируется статически по
разметке: ``applyI18n`` в ``docs/i18n.js`` переписывает textContent у всех
элементов с ``data-i18n-text`` и атрибуты у ``data-i18n-title`` /
``-aria-label`` / ``-placeholder`` / ``-alt`` / ``-tooltip``. Значит,
содержимое таких элементов и сами переводимые атрибуты в EN-режиме не
видны — их не проверяем. Всё остальное обязано либо не содержать
кириллицы, либо приходить из ``docs/*.json``.

Белый список
------------
Названия добавок, эффекты, категории, механизмы, дозировки, формы выпуска
и вердикты не переводятся по решению владельца — это данные, а не
интерфейс. Поэтому кириллические слова, встречающиеся в строковых
значениях ``docs/*.json``, считаются допустимыми. Список собирается из
данных автоматически (сравнение регистронезависимое: ``first_cap()`` в
``scripts/build_sup.py`` делает «известных» → «Известных»), так что
добавление новой добавки в ``data.json`` не требует правки теста.

Проверки
--------
1. ``test_no_russian_text_in_english_mode`` — скан 14 страниц: текст и
   переводимые атрибуты вне ``data-i18n-*`` без кириллицы (кроме данных).
2. ``test_english_dictionary_has_no_russian`` — ни одно значение словаря
   ``en`` не содержит русских слов вне данных: иначе на английской
   странице появится русская фраза «легально».
3. ``test_markup_keys_have_both_translations`` — каждый ключ из разметки
   есть и в ``ru``, и в ``en``: забытый ключ рендерится как сам ключ
   (``sup.h2Dosage`` вместо текста), и это видно только глазами.
4. ``test_script_keys_have_both_translations`` — то же для ключей из
   ``t("…")`` в скриптах и инлайновых скриптах страниц: там опечатка в
   ключе не ловится вообще ничем, потому что fallback — сам ключ.

Исключения, зафиксированные явно
---------------------------------
* ``#themeBtn`` — текст и ``aria-label`` кнопки ставит скрипт темы через
  ``t("theme.light"/"theme.dark")`` / ``t("a11y.themeToLight"/…ToDark")``
  (прецедент — ``applyTheme()`` в ``docs/404.html``). Статический русский
  ``aria-label`` из разметки убран в FIX-75, но видимый текст кнопки
  остаётся русским до выполнения скрипта, поэтому поддерево исключено.
* ``docs/google4a9d23e35c6c3e23.html`` — служебная страница подтверждения
  владения для Google Search Console, не часть сайта.
* ``docs/offline.html`` — в списке есть, хотя ``#langSelect`` на ней нет:
  страница показывает текст до загрузки i18n.js, тест проверяет её
  разметку, а не поведение переключателя.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
I18N = DOCS / "i18n.js"

#: Все RU-страницы для сканирования (docs/*.html + docs/sup/*.html).
_RU_PAGES = sorted(
    str(p.relative_to(DOCS).as_posix())
    for p in list(DOCS.glob("*.html")) + list((DOCS / "sup").glob("*.html"))
    if p.name not in {"google4a9d23e35c6c3e23.html"}
)

#: Все EN-страницы для сканирования (docs/en/*.html + docs/en/sup/*.html).
_EN_PAGES = sorted(
    "en/" + str(p.relative_to(DOCS / "en").as_posix())
    for p in list((DOCS / "en").glob("*.html")) + list((DOCS / "en" / "sup").glob("*.html"))
    if p.name not in {"google4a9d23e35c6c3e23.html"}
)

#: Все страницы вместе (RU + EN).
PAGES = _RU_PAGES + _EN_PAGES

CYR = re.compile(r"[А-Яа-яЁё]+")

#: Элементы, содержимое которых пользователь не читает как текст страницы.
INVISIBLE_TAGS = frozenset(
    {"script", "style", "head", "svg", "textarea", "title", "code", "pre"}
)

#: Атрибуты, которые видит пользователь или скринридер, и их i18n-маркер.
ATTR_MARKERS = {
    "title": "data-i18n-title",
    "aria-label": "data-i18n-aria-label",
    "placeholder": "data-i18n-placeholder",
    "alt": "data-i18n-alt",
    "data-tooltip": "data-i18n-tooltip",
}

#: Все i18n-маркеры разметки.
MARKERS = ("data-i18n-text",) + tuple(ATTR_MARKERS.values())

#: Поддеревья, которые целиком перерисовывает JS после загрузки.
JS_OWNED_IDS = frozenset({"themeBtn"})

#: Служебные файлы вне интерфейса.
SKIP_FILES = frozenset({"google4a9d23e35c6c3e23.html"})

#: `t("key")` / `t('key')` в скриптах; `\b` не даёт поймать `format(`.
_CALL_KEY = re.compile(r"""\bt\(\s*["']([^"']+)["']""")


# ─────────────────────────── белый список ───────────────────────────


def _walk_strings(node, out: list[str]) -> None:
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for key, value in node.items():
            out.append(key)
            _walk_strings(value, out)
    elif isinstance(node, list):
        for value in node:
            _walk_strings(value, out)


@lru_cache(maxsize=1)
def data_tokens() -> frozenset[str]:
    """Кириллические слова из docs/*.json — то, что не переводится."""
    strings: list[str] = []
    for path in sorted(DOCS.glob("*.json")):
        _walk_strings(json.loads(path.read_text(encoding="utf-8")), strings)
    tokens: set[str] = set()
    for value in strings:
        tokens.update(word.lower() for word in CYR.findall(value))
    return frozenset(tokens)


def unknown_words(text: str) -> list[str]:
    """Русские слова строки, которых нет в данных (в нижнем регистре)."""
    tokens = data_tokens()
    return sorted({w for w in CYR.findall(text) if w.lower() not in tokens})


# ─────────────────────── словарь docs/i18n.js ───────────────────────


def _strip_js_comments(text: str) -> str:
    """Убирает // и /* */, не задевая содержимое строковых литералов."""
    out: list[str] = []
    i, size = 0, len(text)
    quote = ""
    while i < size:
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < size:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            newline = text.find("\n", i)
            i = size if newline < 0 else newline
            continue
        if text.startswith("/*", i):
            close = text.find("*/", i + 2)
            i = size if close < 0 else close + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _dict_block(text: str, name: str) -> str:
    """Возвращает `{...}` словаря name, считая вложенность вне строк."""
    start = text.index("\n  %s: {" % name)
    start = text.index("{", start)
    depth = 0
    quote = ""
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise AssertionError("в docs/i18n.js не найден блок словаря %r" % name)


@lru_cache(maxsize=1)
def dictionaries() -> dict[str, dict[str, str]]:
    """Словари ru/en из docs/i18n.js — разбор в чистом Python.

    В словаре `ru` есть комментарии (`// common`), поэтому JSON.parse
    невозможен: снимаем комментарии сканером, вырезаем блок и убираем
    висячие запятые перед `}`/`]`.
    """
    clean = _strip_js_comments(I18N.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for name in ("ru", "en"):
        block = re.sub(r",(\s*[}\]])", r"\1", _dict_block(clean, name))
        result[name] = json.loads(block)
    return result


# ────────────────────────────── скан ──────────────────────────────


class PageScan(HTMLParser):
    """Собирает видимый текст и переводимые атрибуты вне data-i18n-*."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool]] = []
        self.texts: list[tuple[int, str]] = []
        self.attrs: list[tuple[int, str, str]] = []

    def _hidden(self) -> bool:
        return any(hidden for _, hidden in self._stack)

    def _open(self, tag: str, attrs) -> None:
        pairs = [(name, value) for name, value in attrs if name]
        names = {name for name, _ in pairs}
        element_id = dict(pairs).get("id")
        hidden = (
            tag in INVISIBLE_TAGS
            or "data-i18n-text" in names
            or element_id in JS_OWNED_IDS
        )
        self._stack.append((tag, hidden))
        if hidden:
            return
        for name, value in pairs:
            marker = ATTR_MARKERS.get(name)
            if not marker or not value or marker in names:
                continue
            if CYR.search(value):
                self.attrs.append((self.getpos()[0], name, value))

    def handle_starttag(self, tag, attrs):
        self._open(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._open(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                return

    def handle_data(self, data):
        if self._hidden():
            return
        if CYR.search(data):
            self.texts.append((self.getpos()[0], data.strip()))


def page_offenders(page: str) -> list[str]:
    scan = PageScan()
    scan.feed((DOCS / page).read_text(encoding="utf-8"))
    scan.close()
    found: list[str] = []
    for line, text in scan.texts:
        words = unknown_words(text)
        if words:
            found.append(
                "%s:%d текст %r → нет в данных: %s"
                % (page, line, text[:160], ", ".join(words))
            )
    for line, name, value in scan.attrs:
        words = unknown_words(value)
        if words:
            found.append(
                "%s:%d атрибут %s=%r → нет в данных: %s"
                % (page, line, name, value[:160], ", ".join(words))
            )
    return found


# ────────────────────────────── тесты ──────────────────────────────


@pytest.mark.parametrize("page", _RU_PAGES)
def test_no_russian_text_in_english_mode(page: str) -> None:
    """В EN-режиме на RU-странице нет русского текста, кроме данных."""
    found = page_offenders(page)
    assert not found, (
        "на странице %s остался русский текст вне data-i18n-* "
        "(оберните его в data-i18n-text и добавьте ключ в docs/i18n.js):\n%s"
        % (page, "\n".join(found))
    )


def page_offenders_strict(page: str) -> list[str]:
    """Как page_offenders, но без белого списка data_tokens: любая кириллица — ошибка."""
    scan = PageScan()
    scan.feed((DOCS / page).read_text(encoding="utf-8"))
    scan.close()
    found: list[str] = []
    for line, text in scan.texts:
        words = sorted(set(CYR.findall(text)))
        if words:
            found.append(
                "%s:%d текст %r → кириллица: %s"
                % (page, line, text[:160], ", ".join(words))
            )
    for line, name, value in scan.attrs:
        words = sorted(set(CYR.findall(value)))
        if words:
            found.append(
                "%s:%d атрибут %s=%r → кириллица: %s"
                % (page, line, name, value[:160], ", ".join(words))
            )
    return found


@pytest.mark.parametrize("page", _EN_PAGES)
def test_no_russian_in_en_pages(page: str) -> None:
    """На EN-странице нет русского текста вне data-i18n-* (кроме данных)."""
    found = page_offenders(page)
    assert not found, (
        "на EN-странице %s остался русский текст вне data-i18n-* "
        "(оберните в data-i18n-text или добавьте перевод в i18n.js):\n%s"
        % (page, "\n".join(found))
    )


def test_english_dictionary_has_no_russian() -> None:
    """Значения словаря en не содержат русских слов вне данных."""
    found = []
    for key, value in sorted(dictionaries()["en"].items()):
        words = unknown_words(value)
        if words:
            found.append("en[%r] = %r → %s" % (key, value[:160], ", ".join(words)))
    assert not found, "английский перевод содержит русский текст:\n" + "\n".join(found)


def test_markup_keys_have_both_translations() -> None:
    """Каждый ключ из data-i18n-* есть и в ru, и в en."""
    dicts = dictionaries()
    found = []
    for path in sorted(DOCS.rglob("*.html")):
        if path.name in SKIP_FILES:
            continue
        raw = path.read_text(encoding="utf-8")
        rel = path.relative_to(DOCS).as_posix()
        for marker in MARKERS:
            for key in sorted(set(re.findall(marker + r'="([^"]+)"', raw))):
                missing = [name for name in ("ru", "en") if key not in dicts[name]]
                if missing:
                    found.append(
                        "%s: %s=%r нет в словаре %s"
                        % (rel, marker, key, ", ".join(missing))
                    )
    assert not found, "ключи разметки без перевода:\n" + "\n".join(found)


def test_script_keys_have_both_translations() -> None:
    """Каждый ключ из t("…") в скриптах есть и в ru, и в en."""
    dicts = dictionaries()
    sources = sorted(DOCS.glob("*.js")) + sorted(DOCS.rglob("*.html"))
    found = []
    for path in sources:
        if path.name in SKIP_FILES or path.name == "i18n.js":
            continue
        rel = path.relative_to(DOCS).as_posix()
        raw = path.read_text(encoding="utf-8")
        for key in sorted(set(_CALL_KEY.findall(raw))):
            missing = [name for name in ("ru", "en") if key not in dicts[name]]
            if missing:
                found.append("%s: t(%r) нет в словаре %s" % (rel, key, ", ".join(missing)))
    assert not found, "ключи из скриптов без перевода:\n" + "\n".join(found)

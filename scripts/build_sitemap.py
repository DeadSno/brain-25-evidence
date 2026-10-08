#!/usr/bin/env python
"""Генератор docs/sitemap.xml.

Зачем он нужен: sitemap правился руками, и при генерации 130 sup-страниц
забыли про него — в файле осталось 17 URL вместо 143. Ручная правка на
таком объёме рассинхронизируется снова, поэтому список собирается
из фактического содержимого `docs/`.

Что попадает в sitemap:

- корневые контентные страницы `docs/*.html`
- все страницы `docs/sup/*.html`, включая каталог `sup/index.html`

Что НЕ попадает, и почему:

- `offline.html` — не контентная страница, а офлайн-заглушка, которую
  отдаёт сервис-воркер при отсутствии сети. В индексации ей не место
  (решение владельца, зафиксировано в исходном комментарии sitemap)
- `google*.html` — служебный файл верификации Google Search Console,
  не страница сайта

Приоритеты и changefreq взяты из исходного файла и разложены по смыслу:
главная выше разделов, разделы выше карточек, карточки — одним уровнем.

Запуск:

    python scripts/build_sitemap.py            # пересобрать docs/sitemap.xml
    python scripts/build_sitemap.py --check    # только проверить, не трогая файл

`--check` — это ровно то, что делает CI: на чистом checkout из коммита,
где индекс пуст и ни один файл не ждёт включения в коммит, поэтому
lastmod целиком берётся из истории и результат детерминирован.

Запуск с датой коммита:

    python scripts/build_sitemap.py --commit-date 2026-10-08

Нужен pre-commit хуку, и только ему. `git log` не видит незакоммиченные
правки, поэтому файл, уже поставленный в индекс, получил бы в lastmod дату
своего ПРЕДЫДУЩЕГО коммита: генерация до коммита дала бы 2026-10-07 там,
где CI после коммита посчитает 2026-10-08, и проверка упала бы на ровном
месте. Отсюда правило: файл из индекса получает дату коммита, остальные —
дату из истории. Замерено 2026-10-08.

Идемпотентность: два прогона подряд дают 0 diff по sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITEMAP = DOCS / "sitemap.xml"

BASE = "https://deadsno.github.io/brain-25-evidence/"

# Исключения. Совпадение по имени, регистронезависимо.
EXCLUDED_ROOT = {"offline.html"}
EXCLUDED_PREFIXES = ("google",)

# (путь относительно docs/, changefreq, priority).
# Порядок списка = порядок в sitemap.xml.
ROOT_PAGES: list[tuple[str, str, str]] = [
    ("index.html", "weekly", "1.0"),
    ("calculator.html", "weekly", "0.9"),
    ("trends.html", "weekly", "0.9"),
    ("map.html", "weekly", "0.8"),
    ("interactions.html", "weekly", "0.8"),
    ("graph.html", "weekly", "0.8"),
    ("atlas.html", "weekly", "0.8"),
    ("methodology.html", "monthly", "0.6"),
    ("faq.html", "monthly", "0.6"),
    ("glossary.html", "monthly", "0.5"),
    ("feedback.html", "monthly", "0.4"),
    ("support.html", "monthly", "0.3"),
]

# Каталог секции добавок — вузел над карточками, поэтому выше их.
SUP_INDEX = ("sup/index.html", "weekly", "0.9")
SUP_CARD = ("monthly", "0.7")

HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!--
  Сгенерировано scripts/build_sitemap.py. Правь генератор, не этот файл:
  ручная правка здесь уже расходилась с фактическим содержимым docs/
  (17 URL при 143 существующих).

  {count} страниц: {n_root} корневых + {n_sup} в docs/sup/
  (каталог + карточки).

  offline.html намеренно не указан — это не контентная страница, а
  офлайн-заглушка, которую сервис-воркер отдаёт при отсутствии сети.
  google*.html — служебный файл верификации Google Search Console.

  lastmod берётся из даты последнего коммита файла (git log, короткий
  формат), а не из даты запуска генератора: иначе пересборка sitemap
  объявила бы весь сайт свежим. Для файлов вне git подставляется
  дата сборки.
-->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""


def _staged_docs_paths() -> set[str]:
    """Пути под docs/, уже поставленные в индекс и ждущие коммита.

    Нужны, чтобы отличить «файл изменён, но ещё не закоммичен» от «файл
    лежит в коммите». Первые получают дату коммита (см. `--commit-date`),
    вторые — дату из истории. Ключи — пути относительно docs/, как их
    ожидает collect().
    """
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "--", "docs/"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if out.returncode != 0:
        return set()
    staged: set[str] = set()
    for line in out.stdout.splitlines():
        name = line.strip().replace("\\", "/")
        if name.startswith("docs/"):
            staged.add(name[len("docs/"):])
    return staged


def _last_commit_date(rel_to_docs: str, fallback: str) -> str:
    """Дата последнего коммита файла. Для файлов вне git — fallback."""
    # Главная страница в sitemap значится пустым loc (её canonical — с
    # косой чертой), но путь к файлу от этого не становится docs/: такой
    # pathspec означал бы «любой файл в docs», и lastmod главной двигался бы
    # от правки чего угодно, включая сам sitemap.xml. Тогда каждый коммит,
    # чинящий sitemap, делает его снова устаревшим — проверено 2026-10-08.
    # Поэтому путь строим от имени файла, а не от loc.
    if not rel_to_docs:
        rel_to_docs = "index.html"
    path = f"docs/{rel_to_docs}"
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return fallback
    value = out.stdout.strip()
    if not out.returncode == 0 or not value:
        return fallback
    return value


def _entry(loc: str, lastmod: str, changefreq: str, priority: str) -> str:
    return (
        "  <url>\n"
        f"    <loc>{BASE}{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>\n"
    )


def collect() -> list[tuple[str, str, str, str]]:
    """Список (loc, source, changefreq, priority) — в порядке sitemap.xml.

    `source` — путь относительно docs/, по которому берётся lastmod. Он
    совпадает с loc у всех страниц, КРОМЕ главной: у неё loc пустой (см.
    ниже), а дата нужна по файлу docs/index.html. Держать оба поля
    отдельно — единственный способ не превратить lastmod главной в
    самоссылку.

    Порядок разделов и приоритеты заданы ROOT_PAGES и SUP_INDEX; сами
    карточки берутся из каталога и сортируются по имени, чтобы два
    прогона давали байт-в-байт одинаковый файл.
    """
    collected: list[tuple[str, str, str, str]] = []

    for name, changefreq, priority in ROOT_PAGES:
        if not (DOCS / name).is_file():
            raise SystemExit(f"Нет контентной страницы: docs/{name}")
        # У главной canonical — с косой чертой, а не /index.html
        # (`docs/index.html`, `<link rel="canonical">`). В sitemap пишем
        # тот же адрес, что в canonical: два разных написания одной
        # страницы Google считает двумя URL.
        loc = "" if name == "index.html" else name
        collected.append((loc, name, changefreq, priority))

    sup_dir = DOCS / "sup"
    if not sup_dir.is_dir():
        raise SystemExit("Нет каталога docs/sup/")

    cards = sorted(
        p.name
        for p in sup_dir.glob("*.html")
        if p.name != "index.html"
    )
    if not cards:
        raise SystemExit("docs/sup/ пуст — список карточек пуст")

    index_name, index_freq, index_priority = SUP_INDEX
    collected.append((index_name, index_name, index_freq, index_priority))

    changefreq, priority = SUP_CARD
    for name in cards:
        collected.append((f"sup/{name}", f"sup/{name}", changefreq, priority))

    return collected


def render(commit_date: str | None = None) -> str:
    """Текст sitemap.xml.

    `commit_date` — дата, которую получают файлы, уже лежащие в индексе
    (см. `--commit-date`). Без неё генерация полностью опирается на
    историю git и детерминирована: это и есть режим CI.
    """
    entries = collect()
    today = commit_date or date.today().isoformat()
    n_sup = sum(1 for loc, _src, _f, _p in entries if loc.startswith("sup/"))
    n_root = len(entries) - n_sup

    staged = _staged_docs_paths() if commit_date else set()

    chunks = [
        HEADER.format(count=len(entries), n_root=n_root, n_sup=n_sup)
    ]
    for loc, source, changefreq, priority in entries:
        # Файл из индекса ещё не имеет коммита — `git log` вернул бы дату
        # его ПРЕДЫДУЩЕЙ правки, и sitemap разошёлся бы с CI сразу после
        # коммита. Поэтому для индекса берём дату коммита.
        if source in staged:
            lastmod = today
        else:
            lastmod = _last_commit_date(source, today)
        chunks.append(_entry(loc, lastmod, changefreq, priority))
    chunks.append("</urlset>\n")
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="не записывать файл, только сообщить о расхождении",
    )
    parser.add_argument(
        "--commit-date",
        metavar="YYYY-MM-DD",
        help=(
            "дата коммита для файлов, уже добавленных в индекс; "
            "нужно pre-commit хуку, не нужно CI"
        ),
    )
    args = parser.parse_args()

    if args.check and args.commit_date:
        print(
            "FAIL: --check и --commit-date вместе не имеют смысла — "
            "проверка должна быть детерминированной"
        )
        return 1

    if args.commit_date:
        try:
            date.fromisoformat(args.commit_date)
        except ValueError:
            print(f"FAIL: не дата: {args.commit_date}")
            return 1

    content = render(args.commit_date)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    count = content.count("<loc>")

    if args.check:
        if not SITEMAP.is_file():
            print(f"FAIL: нет {SITEMAP.relative_to(ROOT)}")
            return 1
        current = SITEMAP.read_text(encoding="utf-8")
        if current == content:
            print(f"OK: sitemap совпадает с генератором ({count} URL)")
            return 0
        cur_count = current.count("<loc>")
        print(
            f"FAIL: sitemap разошёлся с генератором — "
            f"в файле {cur_count} URL, генератор даёт {count}"
        )
        return 1

    SITEMAP.write_text(content, encoding="utf-8", newline="\n")
    print(f"Записан {SITEMAP.relative_to(ROOT)}: {count} URL, sha256 {digest[:16]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
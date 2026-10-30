#!/usr/bin/env python
"""Генератор docs/sitemap.xml.

Зачем он нужен: sitemap правился руками, и при генерации 130 sup-страниц
забыли про него — в файле осталось 17 URL вместо 143. Ручная правка на
таком объёме рассинхронизируется снова, поэтому список собирается
из фактического содержимого `docs/`.

Что попадает в sitemap:

- корневые контентные страницы `docs/*.html` (RU) и их EN-копии `docs/en/*.html`
- все страницы `docs/sup/*.html` (RU) и их EN-копии `docs/en/sup/*.html`,
  включая каталог `sup/index.html`

Что НЕ попадает, и почему:

- `offline.html` / `docs/en/offline.html` — не контентная страница, а
  офлайн-заглушка, которую отдаёт сервис-воркер при отсутствии сети.
  В индексации ей не место (решение владельца, зафиксировано в исходном
  комментарии sitemap).
- `google*.html` — служебный файл верификации Google Search Console,
  не страница сайта.
- `404.html` / `docs/en/404.html` — служебная страница GitHub Pages,
  отдаётся только на несуществующие URL и не индексируется.

Каждая страница получает блок `<xhtml:link rel="alternate">` с trzema
языковыми версиями: ru / en / x-default (связка SEO-01, FIX-58).

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
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITEMAP = DOCS / "sitemap.xml"

BASE = "https://deadsno.github.io/brain-25-evidence"

# Исключения. Совпадение по имени, регистронезависимо.
EXCLUDED_ROOT = {"offline.html", "404.html"}
EXCLUDED_PREFIXES = ("google",)

# (путь относительно docs/, changefreq, priority).
# Порядок списка = порядок в sitemap.xml.
ROOT_PAGES: list[tuple[str, str, str]] = [
    ("index.html", "weekly", "1.0"),
    # v5.6.5 (A-2): Project Hactar — единая страница со связями, калькулятором
    # и сравнением. До сих пор её в sitemap не было вовсе, поэтому краулер
    # её не видел.
    ("hactar.html", "weekly", "0.9"),
    ("trends.html", "weekly", "0.9"),
    # v5.6.5 (A-2): calculator.html, map.html, interactions.html и compare.html
    # выведены — все четыре стали страницами-редиректами на hactar.html.
    # Редирект в sitemap не место: поисковику нужен конечный адрес, а не
    # 0-секундный мета-рефреш, иначе обе вкладки конкурируют за один и тот
    # же контент. То же и для graph.html / atlas.html, выведенных раньше.
    ("methodology.html", "monthly", "0.6"),
    ("faq.html", "monthly", "0.6"),
    ("glossary.html", "monthly", "0.5"),
    ("feedback.html", "monthly", "0.4"),
    ("support.html", "monthly", "0.3"),
    ("privacy.html", "monthly", "0.3"),
    # v5.6.5 FIX-55 (L2-01): условия использования и лицензия на данные
    # (CC BY 4.0). Меняется редко — yearly с тем же весом, что у приватности.
    ("terms-of-use.html", "yearly", "0.3"),
]

# Каталог секции добавок — вузел над карточками, поэтому выше их.
SUP_INDEX = ("sup/index.html", "weekly", "0.9")
SUP_CARD = ("monthly", "0.7")

HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!--
  Сгенерировано scripts/build_sitemap.py. Правь генератор, не этот файл:
  ручная правка здесь уже расходилась с фактическим содержимым docs/
  (17 URL при 143 существующих).

  {count} страниц: {n_root} корневых + {n_sup} в docs/sup/ (каждая в паре
  RU + EN, т.е. {n_ru} RU + {n_en} EN).

  offline.html / 404.html намеренно не указаны — это не контентные
  страницы (офлайн-заглушка и служебная страница GitHub Pages).
  google*.html — служебный файл верификации Google Search Console.

  lastmod берётся из даты последнего коммита файла (git log, короткий
  формат), а не из даты запуска генератора: иначе пересборка sitemap
  объявила бы весь сайт свежим. Для файлов вне git подставляется
  дата сборки.
-->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
"""

_ALTERNATES = (
    '    <xhtml:link rel="alternate" hreflang="ru" href="{ru}" />\n'
    '    <xhtml:link rel="alternate" hreflang="en" href="{en}" />\n'
    '    <xhtml:link rel="alternate" hreflang="x-default" href="{ru}" />\n'
)


def _staged_docs_paths() -> set[str]:
    """Пути под docs/, уже поставленные в индекс и ждущие коммита."""
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


def _entry(loc: str, lastmod: str, changefreq: str, priority: str,
           ru_url: str, en_url: str) -> str:
    alternates = _ALTERNATES.format(ru=ru_url, en=en_url)
    loc_path = loc if loc else ""
    return (
        "  <url>\n"
        f"    <loc>{BASE}{loc_path}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        f"{alternates}"
        "  </url>\n"
    )


def _ru_en_urls(rel_to_docs: str) -> tuple[str, str]:
    """Вернуть (ru_url, en_url) для страницы по пути относительно docs/."""
    if rel_to_docs == "index.html":
        return BASE + "/", BASE + "/en/"
    return BASE + "/" + rel_to_docs, BASE + "/en/" + rel_to_docs


def _en_loc(rel_to_docs: str) -> str:
    """loc (относительно BASE) для EN-версии страницы."""
    if rel_to_docs == "index.html":
        return "en/"
    return "en/" + rel_to_docs


def collect() -> list[tuple[str, str, str, str]]:
    """Список кортежей (loc, source, changefreq, priority) — как раньше.

    `loc` — путь для <loc> (относительно BASE, "" для главной, без слэша —
    чтобы `BASE + loc` давало корректный URL, например `BASE + ""` для
    главной и `BASE + "/en/"` для EN-главной).

    `source` — путь относительно docs/ для lastmod (RU-источник).

    ru_url/en_url вычисляются в render() через _ru_en_urls(source).
    """
    collected: list[tuple[str, str, str, str]] = []

    def add(name: str, changefreq: str, priority: str) -> None:
        loc = "" if name == "index.html" else name
        collected.append((loc, name, changefreq, priority))

    for name, changefreq, priority in ROOT_PAGES:
        if not (DOCS / name).is_file():
            raise SystemExit(f"Нет контентной страницы: docs/{name}")
        add(name, changefreq, priority)

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
    add(index_name, index_freq, index_priority)

    changefreq, priority = SUP_CARD
    for name in cards:
        add(f"sup/{name}", changefreq, priority)

    return collected


def render(commit_date: str | None = None) -> str:
    """Текст sitemap.xml.

    `commit_date` — дата, которую получают файлы, уже лежащие в индексе
    (см. `--commit-date`). Без неё генерация полностью опирается на
    историю git и детерминирована: это и есть режим CI.
    """
    ru_records = collect()
    today = commit_date or date.today().isoformat()
    staged = _staged_docs_paths() if commit_date else set()

    # Раскладываем записи: каждая RU-страница порождает пару (RU + EN).
    # Каждая запись — (loc, source, changefreq, priority).
    records: list[tuple[tuple[str, str, str, str], str, str]] = []
    for loc, source, changefreq, priority in ru_records:
        ru_url, en_url = _ru_en_urls(source)
        records.append(((loc, source, changefreq, priority), ru_url, en_url))
        en_loc = "en/" if loc == "" else "en/" + loc
        records.append(((en_loc, source, changefreq, priority), ru_url, en_url))

    n_ru = len(ru_records)
    n_en = len(ru_records)
    n_sup = sum(1 for (loc, _s, _f, _p), _r, _e in records if loc.startswith("sup/"))
    n_root = len(records) - n_sup

    chunks = [
        HEADER.format(
            count=len(records),
            n_root=n_root,
            n_sup=n_sup,
            n_ru=n_ru,
            n_en=n_en,
        )
    ]
    for (loc, source, changefreq, priority), ru_url, en_url in records:
        if source in staged:
            lastmod = today
        else:
            lastmod = _last_commit_date(source, today)
        chunks.append(
            _entry(
                loc,
                lastmod,
                changefreq,
                priority,
                ru_url,
                en_url,
            )
        )
    chunks.append(
        '<!-- \u00a9 2026 Vladislav "DeadSno" Pereshivalov. '
        "Данные: CC BY 4.0 -->\n"
    )
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

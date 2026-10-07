#!/usr/bin/env python
"""Генератор docs/feed.xml (RSS 2.0).

Зачем он нужен: карточки добавок обновляются по мере правки data.json,
но у сайта не было ни одного канала syndication — читатель, который
заходил раз в месяц, не мог узнать, что карточка переписана. RSS
закрывает этот пробел тем же способом, что sitemap: список собирается
из фактического содержимого проекта, а не пишется руками.

Что попадает в ленту:

- каталог `docs/sup/index.html` — вход в раздел
- все 130 карточек `docs/sup/*.html`

Что НЕ попадает, и почему:

- корневые страницы (`atlas`, `faq`, `graph`, ...) — это статические
  разделы сайта, их содержание меняется раз в месяц и только при
  перегенерации. RSS-подписчик получает письмо на каждое изменение,
  поэтому в ленту идут только карточки, которые реально дополняются
- `offline.html` и `google*.html` — служебные файлы, их смысл в ленте
  отсутствует (те же исключения, что и в build_sitemap.py)

Даты: у карточек берётся поле `updated` из `docs/data.json` — это
единственный источник, который знает о правке данных. Для каталога
берётся дата последнего коммита файла, потому что сам каталог генерируется
build_sup.py, а не правится в data.json вручную.

Порядок записей — по убыванию `updated`, затем по `code` (порядок
карточек на сайте). Так свежие правки всегда наверху ленты, а порядок
детерминирован: два прогона подряд дают байт-в-байт одинаковый файл.

Запуск:

    python scripts/build_feed.py            # пересобрать docs/feed.xml
    python scripts/build_feed.py --check    # только проверить, не трогая файл

Идемпотентность: два прогона подряд дают 0 diff по sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

# slugify и таблицу транслитерации берём у сборщика карточек: если он
# переедет на другую схему слагов, фид подстроится автоматически, а не
# разойдётся с docs/sup/ по именам файлов.
from build_sup import slugify, text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA_PATH = DOCS / "data.json"
SUP_DIR = DOCS / "sup"
FEED = DOCS / "feed.xml"

BASE = "https://deadsno.github.io/brain-25-evidence/"

CHANNEL_TITLE = "brain-25-evidence"
CHANNEL_DESCRIPTION = "Доказательные данные о БАДах"
CHANNEL_LANG = "ru"

INDEX_TITLE = "Каталог БАДов: 130 добавок | Brain 25 Evidence"
INDEX_DESCRIPTION = (
    "Каталог из 130 БАД: название, категория, вердикт и грейд "
    "доказательности A-D. Карточка ведёт на страницу добавки с "
    "механизмами, дозировкой, взаимодействиями и источниками."
)

#: Год, которым заполняется время суток у даты из data.json. Время в
#: data.json не хранится, а RSS 2.0 требует полный RFC 822 timestamp,
#: поэтому 00:00:00 UTC — единственный честный выбор: не выдумывать
#: «время редактирования», которого нет в источнике.
MIDNIGHT_UTC = timezone(timedelta(0))


class FeedError(SystemExit):
    """Ошибка данных, останавливающая сборку."""


def _rfc822(iso_date: str) -> str:
    """'2026-09-16' -> 'Wed, 16 Sep 2026 00:00:00 +0000'."""
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise FeedError(f"Не дата в формате YYYY-MM-DD: {iso_date!r}") from exc
    return format_datetime(parsed.replace(tzinfo=MIDNIGHT_UTC))


def _card_date(rec: dict, slug: str) -> str:
    """Дата карточки из data.json. Отсутствие — повод остановиться.

    Молча подставлять дату сборки нельзя: в ленте появились бы записи
    «обновлено сегодня» для материала, который никто не трогал, и
    подписчик получал бы пустые письма.
    """
    value = rec.get("updated")
    if not value:
        raise FeedError(f"{slug}: в data.json нет поля 'updated'")
    return str(value)


def _last_commit_date(rel_to_docs: str, fallback: str) -> str:
    """Дата последнего коммита файла. Для файлов вне git — fallback."""
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
    if out.returncode != 0 or not value:
        return fallback
    return value


def collect() -> list[dict]:
    """Записи ленты в порядке вывода: свежие сверху."""
    if not DATA_PATH.is_file():
        raise FeedError(f"Нет {DATA_PATH.relative_to(ROOT)}")
    if not SUP_DIR.is_dir():
        raise FeedError("Нет каталога docs/sup/")

    records = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise FeedError("data.json: ожидался непустой список записей")

    items: list[dict] = []

    # Каталог. Дата — из git: сам каталог собирается build_sup.py.
    index_date = _last_commit_date("sup/index.html", date.today().isoformat())
    items.append(
        {
            "title": INDEX_TITLE,
            "link": f"{BASE}sup/index.html",
            "description": INDEX_DESCRIPTION,
            "date": index_date,
            "category": "каталог",
            "sort": index_date,
            "tiebreak": -1,
        }
    )

    for rec in records:
        if not isinstance(rec, dict):
            continue
        name = text(rec.get("name"))
        slug = slugify(name)
        target = SUP_DIR / f"{slug}.html"
        if not target.is_file():
            raise FeedError(
                f"{slug}: data.json обещает карточку, файла нет: "
                f"{target.relative_to(ROOT)}"
            )
        card_date = _card_date(rec, slug)
        items.append(
            {
                "title": f"{name} — БАДы, доказательства, механизмы | "
                         f"Brain 25 Evidence",
                "link": f"{BASE}sup/{slug}.html",
                "description": text(rec.get("about")),
                "date": card_date,
                "category": text(rec.get("category")),
                "sort": card_date,
                "tiebreak": rec.get("code", 0) if isinstance(rec.get("code"), int)
                            else 0,
            }
        )

    # Свежие сверху; внутри одной даты — порядок карточек на сайте.
    # reverse=True меняет и вторую сортировку, поэтому ключи инвертируются
    # вручную: иначе code шёл бы по убыванию.
    items.sort(key=lambda it: (it["sort"], -it["tiebreak"]), reverse=True)
    return items


def _item(it: dict) -> str:
    return (
        "  <item>\n"
        f"    <title>{escape(it['title'])}</title>\n"
        f"    <link>{escape(it['link'])}</link>\n"
        f"    <guid isPermaLink=\"true\">{escape(it['link'])}</guid>\n"
        f"    <description>{escape(it['description'])}</description>\n"
        f"    <category>{escape(it['category'])}</category>\n"
        f"    <pubDate>{_rfc822(it['date'])}</pubDate>\n"
        "  </item>\n"
    )


def render() -> str:
    items = collect()
    newest = max(it["date"] for it in items)

    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!--\n"
        "  Сгенерировано scripts/build_feed.py. Правь генератор, не этот\n"
        "  файл: ручная правка рассинхронизируется с docs/sup/ так же,\n"
        "  как это случилось с sitemap.\n"
        "\n"
        f"  {len(items)} записей: каталог sup/index.html + {len(items) - 1} карточек.\n"
        "\n"
        "  pubDate карточки взят из поля `updated` в docs/data.json —\n"
        "  это единственный источник, который знает о правке данных.\n"
        "  Для каталога — дата последнего коммита файла.\n"
        "\n"
        "  RSS 2.0 требует RFC 822 timestamp, а в data.json хранится\n"
        "  только дата, поэтому время подставлено 00:00:00 UTC.\n"
        "-->\n"
        '<rss version="2.0" '
        'xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        f"    <title>{escape(CHANNEL_TITLE)}</title>\n"
        f"    <link>{BASE}</link>\n"
        f"    <description>{escape(CHANNEL_DESCRIPTION)}</description>\n"
        f"    <language>{CHANNEL_LANG}</language>\n"
        f'    <atom:link href="{BASE}feed.xml" rel="self" '
        'type="application/rss+xml"/>\n'
        f"    <lastBuildDate>{_rfc822(newest)}</lastBuildDate>\n"
        f"    <generator>scripts/build_feed.py</generator>\n"
    ]
    for it in items:
        chunks.append(_item(it))
    chunks.append("</channel>\n</rss>\n")
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description="Сборка docs/feed.xml")
    parser.add_argument(
        "--check",
        action="store_true",
        help="не записывать файл, только сообщить о расхождении",
    )
    args = parser.parse_args()

    content = render()
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    count = content.count("<item>")

    if args.check:
        if not FEED.is_file():
            print(f"FAIL: нет {FEED.relative_to(ROOT)}")
            return 1
        if FEED.read_text(encoding="utf-8") == content:
            print(f"OK: фид совпадает с генератором ({count} записей)")
            return 0
        print(
            f"FAIL: фид разошёлся с генератором — в файле "
            f"{FEED.read_text(encoding='utf-8').count('<item>')} записей, "
            f"генератор даёт {count}"
        )
        return 1

    FEED.write_text(content, encoding="utf-8", newline="\n")
    print(
        f"Записан {FEED.relative_to(ROOT)}: {count} записей, "
        f"sha256 {digest[:16]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Генератор страниц раздела sup из docs/data.json (v5.6.0, этапы 1-3).

Собирает docs/sup/{slug}.html по templates/sup.html.j2 и docs/sup/index.html
по templates/sup_index.html.j2. Идемпотентен: повторный запуск даёт
байт-в-байт тот же результат.

Экранирование
-------------
Jinja2 при autoescape=True пишет апостроф как &#39; и кавычку как
&#34;, а существующие страницы используют обозначения Python
html.escape — &#x27; и &quot;. Это разница в байтах, поэтому finalize
приводит вывод к тому же виду, что и у пяти эталонных страниц.

JSON-LD выводится отдельным фильтром j: там нужно экранирование JSON,
а не HTML, иначе &gt; внутри JSON-строки испортит файл.

Идемпотентность индекса (этап 3)
--------------------------------
Каталог строится из того же словаря by_slug, что и страницы, и вывод не
содержит ни даты, ни времени генерации, ни счётчиков. Порядок карточек —
sorted() по (название, slug), а не порядок ключей в data.json: словарь
записей меняется при любом обновлении данных, и привязка к нему дала бы
diff на каждом прогоне. Категории и грейды отсортированы явно, счётчики
посчитаны из тех же карточек.

Запуск
------
    python scripts/build_sup.py --only kreatin,omega-3,vitamin-d,magniy,paba
    python scripts/build_sup.py            # все записи data.json + индекс
    python scripts/build_sup.py --skip-index   # только страницы добавок
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs/data.json"
TEMPLATE_DIR = ROOT / "templates"
OUT_DIR = ROOT / "docs/sup"
TEMPLATE_NAME = "sup.html.j2"
INDEX_TEMPLATE_NAME = "sup_index.html.j2"
INDEX_NAME = "index.html"
BASE_URL = "https://deadsno.github.io/brain-25-evidence"

NO_DATA = "нет данных"

# Транслитерация — таблица из задания v5.6.0 этап 1. Проверена на всех
# 130 именах: 0 пустых, 0 не-ASCII, 0 коллизий, все 5 существующих
# файлов воспроизводятся точно.
TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# Цвета бейджа грейда. A, B, D измерены на существующих страницах sup.
#
# v5.6.0 этап 2: решение владельца — грейд C берётся каноничным,
# из style.css:682 (`.grade.gC { background: #b45309 }`). Раньше в
# палитре его не было и подставлялся нейтральный серый.
#
# Важно: палитра sup и палитра .grade.gX в style.css РАЗНЫЕ, и это не
# опечатка. sup-цвета подобраны так, чтобы белый текст на бейдже
# читался; комментарий на style.css:413 фиксирует, что !important в
# .grade.gX перебивал sup и давал контраст 0,2-0,3. Поэтому A, B, D
# здесь остаются инлайновыми (#22c55e / #84cc16 / #ef4444), а не
# заимствуются из .grade.gX (#15803d / #4d7c0f / #b91c1c).
#
# Следствие, которое нужно проверить глазами на этапе 2: C = #b45309
# взят из ДРУГОЙ палитры, чем A/B/D. Контраст белого текста на нём
# 5.02:1 — лучше, чем на существующих бейджах (A 2.28:1, B 1.98:1,
# D 3.76:1 по комментарию style.css:693). То есть C окажется заметно
# темнее соседей в одном ряду. Владелец выбрал каноничный цвет; расхождение
# зафиксировано, а не сглажено.
GRADE_COLORS = {"A": "#22c55e", "B": "#84cc16", "C": "#b45309",
                "D": "#ef4444"}
GRADE_FALLBACK = "#888888"

#: Порядок шкалы доказательности для выпадающего фильтра в каталоге.
#: Задан явно, а не через sorted(): алфавитный A-B-C-D совпал бы с
#: порядком шкалы случайно, и смена шкалы молча переставила бы фильтр.
GRADE_ORDER = ("A", "B", "C", "D")

#: Коды вердикта data.json -> класс .verdict.vN в style.css. На главной
#: их ставит script.js (`'v' + s.code`), здесь — тот же набор.
VERDICT_CODES = (-1, 0, 1)

# Уровень силы механизма -> класс. Измерено: в paba.html значение
# «маркетинг» рендерится классом s-context, отдельного класса нет.
LEVEL_CLASS = {
    "сильно": "strong",
    "умеренно": "medium",
    "слабо": "weak",
    "контекст": "context",
    "маркетинг": "context",
}

# Строка-заглушка, которой в данных помечается отсутствие
# взаимодействий. В paba.html такая запись рендерится не карточкой,
# а одной нотой с заглавной буквой — отдельная ветка шаблона.
NO_INTERACTION_MARK = "нет данных"


def slugify(name: str) -> str:
    """Транслит по таблице задания. Пробелы и разделители -> '-',\
    повторные дефисы схлопываются, края обрезаются."""
    out = []
    for ch in (name or "").lower():
        if ch in TRANS:
            out.append(TRANS[ch])
        elif ch in "-_ ":
            out.append("-")
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    return re.sub(r"-{2,}", "-", "".join(out)).strip("-")


def text(value) -> str:
    """Сырая строка: None и пустое заменяются заглушкой."""
    if value is None:
        return NO_DATA
    s = str(value).strip()
    return s if s else NO_DATA


def html_val(value) -> str:
    """Значение для вывода в HTML.

    Обозначения — как у Python html.escape: &#x27; и &quot;.
    Именно их используют пять существующих страниц; Jinja при
    autoescape дал бы &#39; и &#34;, что отличалось бы на байт.
    """
    return html.escape(text(value), quote=True)


def json_val(value) -> Markup:
    """Значение для JSON-LD: экранирование строки JSON, а не HTML."""
    return Markup(json.dumps(text(value), ensure_ascii=False)[1:-1])


def first_cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def build_context(rec: dict, slug: str, warnings: list[str]) -> dict:
    """Переводит запись data.json в контекст шаблона."""
    grade = text(rec.get("grade"))
    color = GRADE_COLORS.get(grade)
    if color is None:
        color = GRADE_FALLBACK
        warnings.append(
            f"{slug}: нет цвета для грейда {grade!r} — подставлен "
            f"{GRADE_FALLBACK}. Проверь data.json: грейд вне A/B/C/D."
        )

    mechs = []
    for m in (rec.get("mechs") or []):
        if not isinstance(m, (list, tuple)) or len(m) < 3:
            warnings.append(f"{slug}: механизм неполный, пропущен: {m!r}")
            continue
        body, effect, level = m[0], m[1], text(m[2])
        cls = LEVEL_CLASS.get(level)
        if cls is None:
            warnings.append(
                f"{slug}: нет класса для уровня {level!r} — взят 'context'."
            )
            cls = "context"
        mechs.append((html_val(body), html_val(effect), level, cls))

    inter = []
    for it in (rec.get("interactions") or []):
        if not isinstance(it, dict):
            continue
        inter.append({
            "with": html_val(it.get("with")),
            "severity": html_val(it.get("severity")),
            "note": html_val(it.get("note")),
        })
    for it in inter:
        if it["severity"] == "critical":
            warnings.append(
                f"{slug}: уровень взаимодействия 'critical' не имеет CSS "
                f"класса на сайте — карточка останется без оформления."
            )

    no_inter = not inter or all(
        i["with"] == NO_INTERACTION_MARK for i in inter)
    note = inter[0]["note"] if inter else NO_DATA

    sources = []
    for s in (rec.get("key_sources") or []):
        if not isinstance(s, dict):
            continue
        sources.append({
            "title": html_val(s.get("title")),
            "journal": html_val(s.get("journal")),
            "year": html_val(s.get("year")),
            "pmid": html_val(s.get("pmid")),
        })

    return {
        "name": html_val(rec.get("name")),
        "slug": slug,
        "url": f"{BASE_URL}/sup/{slug}.html",
        "base_url": BASE_URL,
        "about": html_val(rec.get("about")),
        "category": html_val(rec.get("category")),
        "verdict": html_val(rec.get("verdict")),
        "grade": html_val(grade),
        "grade_color": color,
        "who_needs": html_val(rec.get("who_needs")),
        "onset": html_val(rec.get("onset")),
        "scienceIndex": html_val(rec.get("scienceIndex")),
        "rct": html_val(rec.get("rct")),
        "metaCount": html_val(rec.get("metaCount")),
        "effects": [html_val(e) for e in (rec.get("effects") or [])],
        "mechs": mechs,
        "dosage": html_val(rec.get("dosage")),
        "course": html_val(rec.get("course")),
        "upper_limit": html_val(rec.get("upper_limit")),
        "caution": html_val(rec.get("caution")),
        "myths": html_val(rec.get("myths")),
        "interactions": inter,
        "no_interactions": no_inter,
        "inter_note_cap": first_cap(note),
        "key_sources": sources,
        "how_to_choose": html_val(rec.get("how_to_choose")),
        "food_sources": html_val(rec.get("food_sources")),
        "guidelines": html_val(rec.get("guidelines")),
        # На пяти существующих страницах стоит MedicalWebPage.
        # Задание предлагало DietarySupplement — это другая схема и
        # другой байт на каждой странице, поэтому оставлена измеренная.
        "ld_type": "MedicalWebPage",
        # Отдельные значения для JSON-LD: там нужно экранирование JSON,
        # а не HTML, иначе &gt; внутри JSON-строки испортит файл.
        "name_j": json_val(rec.get("name")),
        "about_j": json_val(rec.get("about")),
        "category_j": json_val(rec.get("category")),
    }


def make_env(template_dir: Path | str = TEMPLATE_DIR) -> Environment:
    # autoescape выключен намеренно: Jinja экранирует ПОСЛЕ finalize,
    # поэтому подменить обозначения &#39; на &#x27; через finalize нельзя.
    # Экранирование делает html_val() при построении контекста.
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["j"] = lambda v: json_val(v)
    return env


def load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    for key in ("supplements", "items", "data", "records"):
        if isinstance(data.get(key), list):
            return data[key]
    raise SystemExit(f"Не найден список записей в {path}")


def collect_slugs(records: list[dict]) -> dict[str, dict]:
    """Слаг -> запись. Дубликаты транслита оставляют первую запись."""
    by_slug: dict[str, dict] = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        sl = slugify(text(rec.get("name")))
        if sl in by_slug:
            print(f"ВНИМАНИЕ: транслит {sl!r} повторяется, "
                  f"оставлена первая запись", file=sys.stderr)
            continue
        by_slug[sl] = rec
    return by_slug


def build_index_context(by_slug: dict[str, dict], warnings: list[str]) -> dict:
    """Контекст шаблона каталога sup/index.html.

    Порядок карточек — по названию, потом по слагу: сортировка по
    неэкранированным значениям, потому что у экранированных первым идёт
    амперсанд и кириллица вроде «Альфа-GPC» встала бы после «Цинк». Ключ
    слага в сортировке нужен как тай-брейкер: два одноимённых разных
    слага иначе зависали бы от порядка словаря.
    """
    raw = []
    for slug in by_slug:
        rec = by_slug[slug]
        name = text(rec.get("name"))
        category = text(rec.get("category"))
        verdict = text(rec.get("verdict"))
        grade = text(rec.get("grade"))
        code = rec.get("code")
        if code not in VERDICT_CODES:
            warnings.append(
                f"{slug}: код вердикта {code!r} вне {VERDICT_CODES} — "
                f"на карточке будет нейтральный бейдж. Проверь data.json."
            )
            code = 0
        if grade not in GRADE_ORDER:
            warnings.append(
                f"{slug}: грейд {grade!r} вне {GRADE_ORDER} — на карточке "
                f"не будет класса .grade.gX. Проверь data.json."
            )
        raw.append((name, slug, category, verdict, grade, code))

    raw.sort(key=lambda row: (row[0], row[1]))

    cards = []
    for name, slug, category, verdict, grade, code in raw:
        # hay — то, по чему ищет поле фильтра на странице. Строится из
        # сырых строк и приводится в нижний регистр, потому что сравнение
        # в браузере тоже в нижнем регистре (toLowerCase).
        hay = " ".join((name, category, verdict, grade)).lower()
        cards.append({
            "slug": slug,
            "name": html_val(name),
            "category": html_val(category),
            "verdict": html_val(verdict),
            "grade": html_val(grade),
            "code": code,
            "hay": html_val(hay),
        })

    cat_counts = Counter(row[2] for row in raw)
    categories = [{"name": html_val(name), "count": n}
                  for name, n in sorted(cat_counts.items())]

    grade_counts = Counter(row[4] for row in raw)
    grades = [{"value": g, "count": grade_counts.get(g, 0)}
              for g in GRADE_ORDER if grade_counts.get(g, 0)]

    return {
        "cards": cards,
        "categories": categories,
        "grades": grades,
        "total": len(cards),
        "url": f"{BASE_URL}/sup/{INDEX_NAME}",
        "base_url": BASE_URL,
    }


def build_index(env: Environment, by_slug: dict[str, dict],
                out_dir: Path, dry_run: bool) -> tuple[Path, int]:
    """Пишет docs/sup/index.html. Возвращает путь и размер в байтах."""
    warnings: list[str] = []
    tpl = env.get_template(INDEX_TEMPLATE_NAME)
    ctx = build_index_context(by_slug, warnings)
    blob = tpl.render(**ctx).encode("utf-8")
    for w in warnings:
        print(f"  {w}", file=sys.stderr)
    path = out_dir / INDEX_NAME
    if not dry_run:
        path.write_bytes(blob)
    return path, len(blob)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", default="",
                    help="список slug через запятую, например "
                         "kreatin,omega-3,vitamin-d,magniy,paba")
    ap.add_argument("--data", default=str(DATA_PATH))
    ap.add_argument("--template-dir", default=str(TEMPLATE_DIR))
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--dry-run", action="store_true",
                    help="считать, ничего не записывая")
    ap.add_argument("--skip-index", action="store_true",
                    help="не собирать sup/index.html (когда правят только "
                         "страницы добавок)")
    args = ap.parse_args(argv)

    data_path = Path(args.data)
    out_dir = Path(args.out)
    env = make_env(args.template_dir)
    tpl = env.get_template(TEMPLATE_NAME)

    records = load_records(data_path)

    only = [s.strip() for s in args.only.split(",") if s.strip()]
    by_slug = collect_slugs(records)

    targets = only or sorted(by_slug)
    missing = [s for s in only if s not in by_slug]
    for s in missing:
        print(f"ОШИБКА: slug {s!r} не найден в data.json", file=sys.stderr)
    if missing:
        return 1

    warnings: list[str] = []
    written = 0
    total_bytes = 0

    for sl in targets:
        rec = by_slug[sl]
        warnings = []
        ctx = build_context(rec, sl, warnings)
        html = tpl.render(**ctx)
        path = out_dir / f"{sl}.html"
        blob = html.encode("utf-8")
        for w in warnings:
            print(f"  {w}", file=sys.stderr)
        if not args.dry_run:
            path.write_bytes(blob)
        written += 1
        total_bytes += len(blob)
        print(f"  {rec.get('name'):20s} -> sup/{sl}.html  {len(blob):,} байт")

    if args.skip_index:
        print("  sup/index.html: пропущен (--skip-index)")
    else:
        _idx_path, idx_bytes = build_index(env, by_slug, out_dir, args.dry_run)
        print(f"  {'КАТАЛОГ':20s} -> sup/{INDEX_NAME}  {idx_bytes:,} байт")
        written += 1
        total_bytes += idx_bytes

    print()
    print(f"  записей в data.json: {len(records)}, "
          f"уникальных slug: {len(by_slug)}")
    print(f"  сгенерировано: {written}, всего {total_bytes:,} байт"
          f"{' (пробный запуск, файлы не тронуты)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
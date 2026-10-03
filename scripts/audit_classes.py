#!/usr/bin/env python3
"""
Инвентаризация классов и id: HTML / JS / CSS — основа для переименования.

Зачем
----
Перед переименованием конфликтующих классов (`.btn`, `.tab`, `#graph`,
`#sidebar`, `.layout`) нужно точно знать, где каждое имя живёт. Пока класс
значится на 12 страницах и упоминается в JS, переименование — это правка
разметки плюс правка скриптов, и ошибка в любом из двух мест ломает страницу
молча: селектор просто перестаёт совпадать.

Что делает
---------
Для каждой страницы docs/ собирает три среза и сводит их в одну таблицу:

  1. HTML   — все значения из class="..." и id="..." (с числом вхождений)
  2. JS     — классы и id, упомянутые в ПОДКЛЮЧЁННЫХ этой страницей скриптах:
              querySelector / querySelectorAll / matches / closest / $$
              / classList.* / getElementsByClassName / getElementById.
              Подключённые, а не все подряд: `tracker.js` есть не везде, и его
              упоминания не должны считаться «используются на этой странице».
  3. CSS    — селекторы из локальных <style> страницы и из style.css.
              Третьесторонние либы (vis-network, chart.js) НЕ разбираются
              намеренно: см. «Известные ложные срабатывания».

Отдельно печатаются КОНФЛИКТЫ: имя встречается на 2+ страницах и имеет
РАЗНЫЕ локальные правила. Именно такие имена ломаются при попытке вынести
правило в общий style.css — локальное перебивает глобальное по каскаду.

Известные ложные срабатывания (и почему их не чиним «в лоб»)
------------------------------------------------------------
1. **vis-network** создаёт классы в рантайме (`.vis-network`, `.vis-tooltip`,
   `.vis-popup` и т.д.). В HTML их нет, но в CSS (`interactions`, `atlas`)
   правила есть. Это не сирота, а нормальный режим работы библиотеки.
   Помечаются `runtime`, и в ЭТАП 3 не считаются нарушением.
2. **Шаблонные строки и склейка селекторов** — `q('.card' + id)`. Регулярка
   поймает только литеральную часть; такие места видно как «JS без HTML»,
   и их надо читать глазами. Скрипт честно пишет, что это эвристика.

Запуск
------
    python scripts/audit_classes.py                 # таблица + конфликты в stdout
    python scripts/audit_classes.py --md out.md     # то же в файл
    python scripts/audit_classes.py --orphans       # только подозрительные

Модуль используется тестом tests/test_no_orphan_classes.py, поэтому функции
верхнего уровня возвращают данные, а не только печатают.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STYLE_CSS = DOCS / "style.css"

#: Классы, которые создаёт vis-network в рантайме. Их нет в HTML по построению,
#: и отсутствие не является ошибкой.
RUNTIME_CLASSES = re.compile(r"^vis-")

#: Скрипты, которые подключаются как сервис-воркер, а не как страничный JS.
#: Их классы не принадлежат DOM страницы.
NOT_PAGE_JS = {"sw.js"}


# ─────────────────────────────── CSS ───────────────────────────────

def parse_css(css: str, chain: tuple = ()) -> list:
    """Разобрать CSS в дерево. Индексный сканер, а не регулярка по `{}`.

    Регулярка ломается на вложенных блоках и на `@media`: теряется контекст
    запроса, а для этого отчёта контекст важен — два одинаковых правила под
    разными `@media` это разные правила. Сканер пропускает вложенный блок
    целиком и ведёт цепочку `@`-ок.
    """
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    items: list = []
    i, n, start = 0, len(css), 0
    while i < n:
        if css[i] == "{":
            sel = " ".join(css[start:i].split())
            depth, j = 0, i
            while j < n:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            body = css[i + 1:j]
            end = j + 1 if j < n else n
            if sel.startswith("@"):
                items.append(("at", sel, chain + (sel,),
                              parse_css(body, chain + (sel,))))
            else:
                items.append(("rule", sel, " ".join(body.split()), chain))
            i = start = end
            continue
        i += 1
    return items


def flatten_css(items: list) -> list:
    """-> [(selector, body, chain), ...] для листовых правил."""
    out = []
    for kind, sel, a, b in items:
        if kind == "at":
            out.extend(flatten_css(b))
        else:
            out.append((sel, a, b))
    return out


def tokens(sel: str) -> list:
    """Все классы и id, которых касается селектор.

    `.btn.calc` -> ['.btn', '.calc'];  `#graph` -> ['#graph'];
    `.sb-links > a:hover` -> ['.sb-links'];  `[class*="legend"]` -> ['legend'].
    Вложенность и класс-атрибут разбираются, потому что на этом стояла
    прошлая миграция: разбор только по `class="..."` называл `.btn.calc`
    «уникальным», хотя `.btn` есть на 12 страницах.
    """
    out = []
    for compound in re.split(r"[ >,+~]", sel):
        compound = compound.strip()
        if not compound:
            continue
        for m in re.finditer(r'\[class[*^]?="([^"]+)"\]', compound):
            out.append("." + m.group(1))       # подстрочный матч -> как класс
        core = re.sub(r"\[[^\]]*\]", "", compound)
        for m in re.finditer(r"([.#])([\w-]+)", core):
            out.append(m.group(1) + m.group(2))
    return out


def norm_body(body: str) -> str:
    """Нормализовать тело правила для сравнения «одинаковое / разное»."""
    d = {}
    for part in body.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip().lower()] = " ".join(v.split())
    return ";".join(f"{k}:{v}" for k, v in sorted(d.items()))


def bare(token: str) -> str:
    """`.btn` -> `btn`, `#graph` -> `graph`.

    Ключи хранятся БЕЗ префикса. Первая версия скрипта держала HTML-ключи как
    `btn`, а CSS-токены как `.btn`, и они не соединялись никогда: имя, которое
    есть и в разметке, и в CSS, считалось «CSS без HTML». На проверке это дало
    287 ложных сирот, включая `.btn`. Соединение идёт только по голому имени;
    префикс возвращается для показа и для определения kind.
    """
    return token.lstrip(".#")


# ─────────────────────────────── HTML ───────────────────────────────

ATTR_RE = re.compile(r"""\b(class|id)\s*=\s*(["'])(.*?)\2""", re.S)
SCRIPT_SRC_RE = re.compile(r"""<script[^>]*\bsrc\s*=\s*(["'])(.*?)\1""", re.I)
STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
SCRIPT_BLOCK_RE = re.compile(r"<script(?![^>]*\bsrc)[^>]*>(.*?)</script>", re.S | re.I)


def parse_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    classes: dict = defaultdict(int)
    ids: dict = defaultdict(int)
    for m in ATTR_RE.finditer(text):
        target = classes if m.group(1) == "class" else ids
        for tok in m.group(3).split():
            target[tok] += 1

    scripts = []
    for m in SCRIPT_SRC_RE.finditer(text):
        src = m.group(2).split("?")[0]
        if src.startswith(("http://", "https://", "//")):
            scripts.append(("cdn", src))
            continue
        scripts.append(("file", (path.parent / src).resolve()))
    for m in SCRIPT_BLOCK_RE.finditer(text):
        scripts.append(("inline", m.group(1)))

    local_css = [b for b in STYLE_BLOCK_RE.findall(text)]
    return {
        "path": path,
        "rel": path.relative_to(DOCS).as_posix(),
        "classes": dict(classes),
        "ids": dict(ids),
        "scripts": scripts,
        "local_css": local_css,
    }


# ──────────────────────────────── JS ────────────────────────────────

#: ЧТЕНИЕ: селекторы, которые обязаны что-то найти в разметке.
JS_READS = [
    re.compile(r"""(?:querySelectorAll|querySelector|closest|matches|getElementsByClassName)\s*\(\s*(['"`])(.+?)\1"""),
    re.compile(r"""\$\$?\s*\(\s*(['"`])(.+?)\1"""),
]
#: ЧТЕНИЕ по id: getElementById и локальный хелпер `$`.
#: script.js:6 — `const $ = id => document.getElementById(id)`. Раньше ловился
#: только spelled-out вызов, и из подсчёта выпадали 3 обращения к сайдбару
#: (`$('sidebar')` в atlas.html:510, 516, 610). Из-за этого PREPARE_RENAME
#: утверждал «0 чтений из JS», а на деле их 12. Проверено перед правкой: все
#: 147 вызовов `$(...)` в проекте принимают id-подобный аргумент, ни одного
#: селектора, так что трактовка безопасна.
JS_BY_ID = [
    re.compile(r"""getElementById\s*\(\s*(['"])(.+?)\1"""),
    re.compile(r"""(?<![\\\w$])\$\(\s*(['"])([A-Za-z][\w-]*)\1"""),
]

#: ЗАПИСЬ: classList.add/remove/replace — класс СОЗДАЁтся, его нет в HTML по
#: построению. Пример: `documentElement.classList.add('dark')`.
JS_WRITES = [
    re.compile(r"""classList\.(?:add|remove|toggle|replace)\s*\(\s*(['"])(.+?)\1"""),
]
#: classList.add('a', 'b') — несколько имён одной строкой.
JS_WRITE_MULTI = re.compile(
    r"""classList\.(?:add|remove|replace)\s*\(\s*((?:['"][^'"]*['"]\s*,\s*)+['"][^'"]*['"])""")

#: ЗАПИСЬ через className: `banner.className = 'banner ' + cls` (script.js:1040).
#: Без этого правила `.banner` считался несуществующим, хотя это единственный
#: класс, которым рисуются баннеры конфликтов на главной.
JS_CLASSNAME = re.compile(r"""\.className\s*=\s*(['"])(.+?)\1""")

#: СОЗДАНИЕ В ШАБЛОНЕ: `class="tagChip"` внутри строки JS. Так появляются
#: tagChip, chipbx, cat, srcIcon — в статической разметке их нет ни разу.
JS_CLASS_ATTR = re.compile(r"""\bclass\s*=\s*(["'])([^"']*)\1""")

#: Остаток шаблонной вставки: `g${esc(c.grade)}`. Это не класс, но статическая
#: часть ДО подстановки — настоящий префикс (`g`, `sev-`, `v`), по которому
#: строится всё семейство (gA..gD, sev-high, v0). Без фильтра такие осколки
#: попадали в таблицу как имена: замерено 5 штук вида `g${esc(c.grade)}`.
TEMPLATE_FRAG = re.compile(r"^([A-Za-z][\w-]*)\$\{.*$")

#: Строковый литерал, равный имени класса. Нужен для таблиц соответствий вида
#: `{'сильно':'t-strong', 'умеренно':'t-mod'}` (map.html:305): класс лежит
#: обычным литералом, а не в `class="..."`, и прежние разборы его не видели.
#: Ведущие и хвостовые пробелы обязательны: в trends.html класс собирается как
#: `className = 'delta' + (pubsDelta < 0 ? ' down' : '')` (строка 549), и литерал
#: там начинается с пробела — без этого `down` считался мёртвым, хотя рисуется
#: при каждом падении показателя.
JS_LITERAL = re.compile(r"""['"]([\w -]*\w[\w -]*)['"]""")

#: ДИНАМИЧЕСКАЯ СБОРКА имени класса. В этом проекте форма везде одна:
#:     '<span class="grade g' + s.grade        (script.js:36)  -> gA, gB, gC
#:     '<div  class="verdict v' + esc(s.code)  (script.js:572) -> v0, v1, v-1
#:     '<div  class="sev sev-' + esc(i.sev)    (script.js:129) -> sev-high
#:     `... class="t-${kind}"`                                -> t-mkt, t-mod
#: Первый шаблон ловит «слово, закрывающая кавычка, плюс» — именно та форма,
#: которая здесь используется. Первая версия требовала кавычку ПЕРЕД словом и
#: поэтому не видела ни одного из этих классов: перед `sev-` стоит пробел
#: (часть значения атрибута), а не кавычка.
#: Ложные срабатывания возможны на обычной склейке строк (`'РФИ' + x`); они
#: лишь ОТВОДЯТ имя от флага «сирота», то есть ведут в безопасную сторону, а
#: собранные динамически имена печатаются отдельным списком для чтения глазами.
JS_DYNAMIC = [
    re.compile(r"""([A-Za-z][\w-]*)['"`]\s*\+"""),
    re.compile(r"""([A-Za-z][\w-]*)\$\{"""),
]


def parse_js(text: str) -> dict:
    """-> {reads, writes, created, ids, dynamic, literals}.

    Разделение чтения и записи — не косметика. `querySelector('.dark')` ищет
    элемент, которого нет, если класс ставится только скриптом; но
    `classList.add('dark')` этот класс СОЗДАЁТ, и отсутствие его в разметке
    нормально. Если считать записи сиротами, тест завалит живые классы
    (замерено: 88 на первой модели) и будет вручную игнорироваться, как любой
    неверный тест.
    """
    reads, writes, created, ids = set(), set(), set(), set()
    for rx in JS_READS:
        for m in rx.finditer(text):
            for t in tokens(m.group(2)):
                (ids if t.startswith("#") else reads).add(bare(t))
    for m in JS_BY_ID[0].finditer(text):
        ids.add(bare(m.group(2)))
    for rx in JS_BY_ID[1:]:
        for m in rx.finditer(text):
            ids.add(bare(m.group(2)))
    for rx in JS_WRITES:
        for m in rx.finditer(text):
            for tok in m.group(2).split():
                writes.add(bare(tok))
    for m in JS_WRITE_MULTI.finditer(text):
        for lit in re.findall(r"""['"]([^'"]*)['"]""", m.group(1)):
            for tok in lit.split():
                writes.add(bare(tok))
    for m in JS_CLASSNAME.finditer(text):
        for tok in m.group(2).split():
            if TEMPLATE_FRAG.match(tok):
                continue
            writes.add(bare(tok))

    dynamic = set()
    for m in JS_CLASS_ATTR.finditer(text):
        for tok in m.group(2).split():
            frag = TEMPLATE_FRAG.match(tok)
            if frag:
                # `g${...}` -> префикс `g`; сам осколок классом не является.
                dynamic.add(frag.group(1))
                continue
            if tok and not tok.startswith(("#", "{", "$")):
                created.add(bare(tok))
    for rx in JS_DYNAMIC:
        for m in rx.finditer(text):
            dynamic.add(m.group(1))

    literals = set()
    for m in JS_LITERAL.finditer(text):
        for tok in m.group(1).split():
            if tok and not tok.startswith(("#", "$")):
                literals.add(bare(tok))

    return {"reads": reads, "writes": writes, "created": created,
            "ids": ids, "dynamic": dynamic, "literals": literals}


# ──────────────────────────── сборка данных ────────────────────────────

def collect(include_sup: bool = True) -> dict:
    pages = sorted(DOCS.glob("*.html"))
    if include_sup:
        pages += sorted(DOCS.glob("sup/*.html"))

    parsed = [parse_page(p) for p in pages]

    # --- CSS ---
    # Ключи everywhere — голые имена (см. bare()). Префикс теряется, поэтому
    # источник префикса запоминаем отдельно: у класса он всегда `.`, у id `#`.
    global_css = flatten_css(parse_css(STYLE_CSS.read_text(encoding="utf-8")))
    css_rules = defaultdict(list)        # голое имя -> [(source, selector, body, chain)]
    for sel, body, chain in global_css:
        for t in tokens(sel):
            css_rules[bare(t)].append(("style.css", sel, body, chain))
    for pg in parsed:
        for i, block in enumerate(pg["local_css"]):
            for sel, body, chain in flatten_css(parse_css(block)):
                for t in tokens(sel):
                    css_rules[bare(t)].append(
                        (f"{pg['rel']} <style> #{i + 1}", sel, body, chain))

    # --- JS (по подключённым файлам; один файл читается один раз) ---
    js_cache: dict = {}
    js_reads = defaultdict(lambda: defaultdict(set))
    js_writes = defaultdict(lambda: defaultdict(set))
    js_created = defaultdict(lambda: defaultdict(set))
    js_ids = defaultdict(lambda: defaultdict(set))
    js_literals = defaultdict(lambda: defaultdict(set))
    dyn_prefixes: set = set()
    for pg in parsed:
        for kind, val in pg["scripts"]:
            if kind == "inline":
                source, text, where = "<inline>", val, "inline"
            elif kind == "cdn":
                continue                      # третья сторона: не наш код
            else:
                if not val.exists() or val.name in NOT_PAGE_JS:
                    continue
                source = val.name
                if val not in js_cache:
                    js_cache[val] = val.read_text(encoding="utf-8",
                                                  errors="replace")
                text, where = js_cache[val], source
            info = parse_js(text)
            dyn_prefixes |= info["dynamic"]
            for n in info["reads"]:
                js_reads[n][pg["rel"]].add(source)
            for n in info["writes"]:
                js_writes[n][pg["rel"]].add(source)
            for n in info["created"]:
                js_created[n][pg["rel"]].add(source)
            for n in info["ids"]:
                js_ids[n][pg["rel"]].add(source)
            for n in info["literals"]:
                js_literals[n][pg["rel"]].add(source)

    return {
        "pages": parsed,
        "css_rules": css_rules,
        "js_reads": js_reads, "js_writes": js_writes,
        "js_created": js_created, "js_ids": js_ids,
        "js_literals": js_literals,
        "dyn_prefixes": dyn_prefixes,
        "js_cache": js_cache,
    }


def build_rows(data: dict) -> dict:
    """-> {голое имя: {...}} по всем именам, где-либо встречающимся."""
    html_classes = defaultdict(lambda: defaultdict(int))
    html_ids = defaultdict(lambda: defaultdict(int))
    for pg in data["pages"]:
        for c, n in pg["classes"].items():
            html_classes[c][pg["rel"]] += n
        for i, n in pg["ids"].items():
            html_ids[i][pg["rel"]] += n

    dyn = data["dyn_prefixes"]
    rows = {}
    universe = (set(html_classes) | set(html_ids) | set(data["css_rules"])
                | set(data["js_reads"]) | set(data["js_writes"])
                | set(data["js_created"]) | set(data["js_ids"]))
    for name in universe:
        hc = dict(html_classes.get(name, {}))
        hi = dict(html_ids.get(name, {}))
        rules = data["css_rules"].get(name, [])
        local = [(src, sel, body, ch) for src, sel, body, ch in rules
                 if src != "style.css"]
        reads = dict(data["js_reads"].get(name, {}))
        writes = dict(data["js_writes"].get(name, {}))
        created = dict(data["js_created"].get(name, {}))
        jids = dict(data["js_ids"].get(name, {}))
        lits = dict(data["js_literals"].get(name, {}))
        # Динамика по ТОЧНОМУ совпадению префикса. Раньше проверялось только
        # `name.startswith(prefix + "-")`, и этого не хватало: классы `v0`, `gA`,
        # `v1` собираются как `v` + код без разделителя, поэтому префикс `v`
        # должен матчиться и сам по себе.
        is_dynamic = any(name == p or name.startswith(p)
                         for p in dyn)
        # Имя может быть и классом, и id (`.tab` и `id="tab"`). Если где-то
        # оно упомянуто с `#`, считаем его id — иначе потеряем getElementById.
        is_id = bool(hi) or any("#" + name in r[1] for r in rules) or bool(jids)
        token = ("#" if is_id else ".") + name

        # Класс СЧИТАЕТСЯ используемым, если он есть в разметке, создан скриптом
        # (classList / className / шаблон / литерал) либо собирается динамически.
        # Иначе живые классы объявляются сиротами — на первой модели их было 88.
        used = bool(hc or hi or writes or created or lits or is_dynamic)
        rows[name] = {
            "token": token, "name": name,
            "kind": "id" if is_id else "class",
            "html": hc, "html_ids": hi,
            "html_total": sum(hc.values()) + sum(hi.values()),
            "html_pages": sorted(set(hc) | set(hi)),
            "js": reads, "js_writes": writes, "js_created": created,
            "js_ids": jids, "js_literals": lits,
            "js_any": bool(reads or writes or created or jids or lits),
            "js_reads_any": bool(reads),
            "dynamic": is_dynamic,
            "used": used,
            "css_rules": len(rules),
            "css_global": sum(1 for r in rules if r[0] == "style.css"),
            "css_local": len(local),
            "local_rules": local,
            "runtime": bool(RUNTIME_CLASSES.match(name)),
        }
    return rows


def find_conflicts(rows: dict) -> list:
    """Имя на 2+ страницах с РАЗНЫМИ локальными правилами.

    Требуется различие тел, а не сам факт локальных правил на нескольких
    страницах: одинаковые правила — это дубли, их можно выносить в общий
    style.css (как и было в шагах 1-3 миграции). Конфликт — это когда
    страницы задают одноимённому классу РАЗНОЕ, и вынос перекрасит соседа.
    """
    out = []
    for name, r in rows.items():
        if r["kind"] != "class" or len(r["html_pages"]) < 2:
            continue
        if not r["local_rules"]:
            continue
        by_src = defaultdict(set)
        for src, sel, body, _chain in r["local_rules"]:
            by_src[src].add(norm_body(body))
        variants = {v for s in by_src.values() for v in s}
        # Условие — РАЗНЫЕ СТРАНИЦЫ задают одноимённому классу разное.
        # Одной страницы недостаточно: у неё и так бывает два тела (база плюс
        # правило внутри @media), и это не конфликт, а обычная медиа-адаптация.
        # Без этой проверки `.links` и `.card` попадали в список с одной
        # страницей offline — замерено, 2 ложных конфликта из 21.
        pages = sorted({src.split()[0] for src in by_src})
        if len(pages) < 2 or len(variants) < 2:
            continue
        out.append({
            "token": r["token"], "variants": len(variants), "pages": pages,
            "sample": {src: sorted(b)[0] for src, b in list(by_src.items())[:4]},
            "html_total": r["html_total"], "js_any": r["js_any"],
        })
    out.sort(key=lambda x: (-len(x["pages"]), -x["html_total"]))
    return out


def orphans(rows: dict) -> tuple:
    """-> (класс в CSS без HTML, селектор в JS без HTML), без runtime.

    `used` учитывает создание классов скриптом и динамическую сборку, поэтому
    сюда попадает только то, что действительно никем не используется.
    """
    css_only, js_only = [], []
    for name, r in rows.items():
        if r["runtime"] or r["kind"] != "class" or r["used"]:
            continue
        if r["css_rules"]:
            css_only.append(r)
        # Ошибка — только ЧТЕНИЕ селектора: скрипт ищет то, чего нет. Записи
        # classList и шаблоны отсеяны выше через `used`.
        if r["js_reads_any"]:
            js_only.append(r)
    css_only.sort(key=lambda r: -r["css_rules"])
    js_only.sort(key=lambda r: (-len(r["js"]), -r["css_rules"]))
    return css_only, js_only


# ─────────────────────────────── вывод ───────────────────────────────

def render(rows: dict, conflicts: list, css_only: list, js_only: list,
           n_pages: int) -> str:
    L = []
    A = L.append
    A("# Аудит классов и id — HTML / JS / CSS\n")
    A(f"Страниц разобрано: **{n_pages}** · имён учтено: **{len(rows)}**")
    A("")
    A("## Конфликты: имя на 2+ страницах с разными локальными правилами\n")
    A("| Имя | Страниц | Вариантов | Вхождений HTML | В JS | Где конфликтует |")
    A("|---|---:|---:|---:|---|---|")
    for c in conflicts:
        A(f"| `{c['token']}` | {len(c['pages'])} | {c['variants']} | "
          f"{c['html_total']} | {'да' if c['js_any'] else 'нет'} | "
          f"{', '.join(p.replace('.html','') for p in c['pages'][:6])} |")
    A("")
    A("## Подозрительные: CSS без HTML\n")
    A("| Имя | Правил CSS | Где объявлено |")
    A("|---|---:|---|")
    for r in css_only[:40]:
        srcs = sorted({s for s, _, _, _ in r["local_rules"]}) or ["style.css"]
        A(f"| `{r['token']}` | {r['css_rules']} | "
          f"{', '.join(x.replace('.html','') for x in srcs[:3])} |")
    A("")
    A("## Подозрительные: селектор в JS без HTML (ошибка)\n")
    A("| Имя | Где ищется | Правил CSS |")
    A("|---|---|---:|")
    for r in js_only[:40]:
        where = sorted({s for v in r["js"].values() for s in v})
        pages = sorted({p.replace('.html', '') for p in r["js"]})[:4]
        A(f"| `{r['token']}` | {', '.join(where)} на {', '.join(pages)} | "
          f"{r['css_rules']} |")
    A("")
    A("## Полная таблица\n")
    A("| Имя | Тип | Вхождений HTML | Страниц | Правил CSS (из них локальных) "
      "| JS: селектор | JS: id-lookup |")
    A("|---|---|---:|---:|---:|---|---|")
    for t in sorted(rows, key=lambda x: (-rows[x]["html_total"], x)):
        r = rows[t]
        A(f"| `{r['token']}` | {r['kind']} | {r['html_total']} | "
          f"{len(r['html_pages'])} | {r['css_rules']} ({r['css_local']}) | "
          f"{'да' if r['js'] else '—'} | {'да' if r['js_ids'] else '—'} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", help="записать отчёт в файл")
    ap.add_argument("--orphans", action="store_true",
                    help="только подозрительные имена")
    args = ap.parse_args(argv)

    data = collect()
    rows = build_rows(data)
    conflicts = find_conflicts(rows)
    css_only, js_only = orphans(rows)

    if args.orphans:
        print(f"CSS без HTML: {len(css_only)}")
        for r in css_only:
            print(f"  {r['token']:32s} {r['css_rules']:3d} правил")
        print(f"JS без HTML: {len(js_only)}")
        for r in js_only:
            print(f"  {r['token']:32s} {r['css_rules']:3d} правил")
        return 0

    text = render(rows, conflicts, css_only, js_only, len(data["pages"]))
    if args.md:
        Path(args.md).write_text(text, encoding="utf-8")
        print(f"wrote {args.md}")
    else:
        sys.stdout.write(text)
    print(f"names={len(rows)} conflicts={len(conflicts)} "
          f"css_only={len(css_only)} js_only={len(js_only)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

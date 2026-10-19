"""Согласованность SEO-метатегов между <title>, meta description, og:* и twitter:*.

Находки: `reports/audits/seo.md` — MKT-P2-06 (`og:description` ≠ `meta description`
на 10 из 13 страниц) и MKT-P2-07 (`twitter:title`/`twitter:description` отсутствовали
на 8 страницах и устарели ещё на 5). Обе сняты 15.10.2026, батч 9C (зарегистрированы
под свободными номерами MKT-P2-09/MKT-P2-10 — коллизия ID описана в аудите).
Третья находка, MKT-P2-11 (`twitter:image` отсутствовал на 8 страницах), закрыта
тем же гейтом: тег обязан присутствовать и совпадать с `og:image`.

Что показал замер перед правкой (13 контентных страниц):
  - `og:description` расходился с `<meta name="description">` у 10 страниц,
    причём og-версии были короче и чисто маркетинговые («Какие добавки усиливают
    или ослабляют друг друга.»), а meta — информативные и в диапазоне 120–160
    символов. То есть каноничной была meta, а og её терял.
  - `twitter:title`/`twitter:description` отсутствовали у 8 (atlas, calculator,
    index, interactions, map, privacy, support, trends) и расходились с
    каноническими значениями ещё у 5 (faq, feedback, glossary, graph,
    methodology) — там стояли рукописные сокращения вроде
    «FAQ — частые вопросы о БАДах».
  - `twitter:image` отсутствовал у тех же 8 страниц, при том что `og:image`
    стоял на всех 13. Ровно тот же почерк долга: `og:image` пристегнули в своё
    время (`MKT-P2-03`, 144/144), а копию в Twitter-блок забыли.

Чем обосновано решение: направление выбрано по уже принятому в репозитории
прецеденту — коммит `b0a15fd` («og:title matches title on 13 pages») сделал
`og:title` копией `<title>`. Здесь та же логика распространена на описание и на
Twitter, но не в обратную сторону: подгонять meta description под короткие
og-формулировки означало бы выбросить осмысленные 130–160-символьные описания,
которые, в отличие от og, попадают в сниппеты Google. Итог — один источник
правды на страницу: `<title>` и `<meta name="description">`, а og/twitter
должны быть их дословными копиями.

Ловушка проверки. Первый измеряющий скрипт показал расхождение `og:description`
у `map.html`, хотя побайтовое сравнение repr() дало полное равенство всех трёх
значений. Причина — не в разметке: сравнение шло по подстроке, найденной
отдельными регулярками с разной жадностью к пробелам. Поэтому гейт ниже не
сравнивает «сырые куски текста», а сначала разбирает `<meta>` в список
(name/property → content) независимо от порядка атрибутов, и только потом
сравнивает значения. Регексп `.*` по разметке здесь дал бы ровно тот ложный
«долг», ради устранения которого гейт и написан.

Два файла в `docs/` намеренно вне охвата. Исключение объявлено явно, чтобы
новая страница не прошла молча: если появится HTML, которого нет ни в списке
контентных, ни в списке исключений, `test_page_inventory_is_classified` упадёт.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "docs"

# Контентные страницы сайта. Список зафиксирован явно, а не вычисляется
# glob'ом: 13 страниц из `reports/audits/seo.md` и из коммитов dcee970
# («Schema.org on 13 pages»), b0a15fd, 42f4323. Новую страницу добавляют сюда
# вместе с решением про SEO-теги, а не молча.
CONTENT_PAGES = (
    "atlas.html",
    "calculator.html",
    "compare.html",
    "faq.html",
    "feedback.html",
    "glossary.html",
    "graph.html",
    "index.html",
    "interactions.html",
    "map.html",
    "methodology.html",
    "privacy.html",
    "support.html",
    "trends.html",
)

# Вне охвата — с причиной. Новое значение сюда не добавляют молча: это делается
# вместе с записью, почему страница не участвует в проверке.
EXCLUDED_PAGES = {
    "offline.html": "заглушка PWA, которую отдаёт service worker офлайн; "
                    "SEO-теги в ней не выводятся by design",
    "google4a9d23e35c6c3e23.html": "файл верификации Google Search Console — "
                                  "мета-теги туда не пишутся никогда",
}

# Канон: какие теги обязаны быть и чему равны.
REQUIRED_TAGS = ("og:title", "og:description", "og:image",
                 "twitter:title", "twitter:description", "twitter:image")
CANONICAL = {"og:title": "title", "og:description": "description",
             "twitter:title": "title", "twitter:description": "description"}

# Картинка — отдельное зеркало: `twitter:image` копирует `og:image`, а не
# `<title>`/`<meta name="description">`. Держать её в CANONICAL нельзя: там
# значения сравниваются с двумя текстовыми канонами, и проверка потребовала бы
# картинку, равную заголовку.
IMAGE_MIRRORS = {"twitter:image": "og:image"}

META_RE = re.compile(r"<meta\s+([^>]*?)\s*/?>", re.IGNORECASE)
ATTR_RE = re.compile(r"""([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
LD_RE = re.compile(
    r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
HREF_RE = re.compile(r"""<a\b[^>]*?\shref\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)


def _meta_map(html: str) -> dict[str, str]:
    """Разбирает <meta> в {name/property: content}, порядок атрибутов не важен.

    Ключ приводится к нижнему регистру, дубликаты схлопываются в последний —
    проверка дублей отдельная (test_required_tags_present_once).
    """
    out: dict[str, str] = {}
    for tag in META_RE.finditer(html):
        attrs: dict[str, str] = {}
        for m in ATTR_RE.finditer(tag.group(1)):
            attrs[m.group(1).lower()] = m.group(2) if m.group(2) is not None else m.group(3)
        key = attrs.get("name") or attrs.get("property")
        if key:
            out[key.lower()] = attrs.get("content", "")
    return out


def _title(html: str) -> str | None:
    m = TITLE_RE.search(html)
    return m.group(1).strip() if m else None


def _read(name: str) -> str:
    path = ROOT / name
    assert path.exists(), (
        f"{name} есть в CONTENT_PAGES/EXCLUDED_PAGES, но файла нет. "
        f"Удаление страницы — это изменение охвата гейта: либо уберите её из "
        f"списка, либо верните файл. Иначе проверка молча перестанет её видеть."
    )
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pages() -> dict[str, dict[str, str | None]]:
    parsed: dict[str, dict[str, str | None]] = {}
    for name in CONTENT_PAGES:
        html = _read(name)
        meta = _meta_map(html)
        parsed[name] = {
            "title": _title(html),
            "description": meta.get("description"),
            **{tag: meta.get(tag) for tag in REQUIRED_TAGS},
        }
    return parsed


def test_page_inventory_is_classified() -> None:
    """Ни одна страница docs/*.html не должна остаться без решения.

    Новая страница, добавленная мимо обоих списков, — самый частый способ
    вернуть этот долг: она выглядит «не охваченной», а на деле не проверена.
    """
    on_disk = {p.name for p in ROOT.glob("*.html")}
    classified = set(CONTENT_PAGES) | set(EXCLUDED_PAGES)
    unclassified = on_disk - classified
    assert not unclassified, (
        f"Страницы в docs/ не отнесены ни к контентным, ни к исключениям: "
        f"{sorted(unclassified)}. Добавьте их в CONTENT_PAGES (если у них есть "
        f"SEO-теги) или в EXCLUDED_PAGES с причиной — иначе они выпадут из "
        f"проверки, и MKT-P2-06/07 вернутся тихо."
    )
    missing = classified - on_disk
    assert not missing, f"Классифицированы несуществующие файлы: {sorted(missing)}"


@pytest.mark.parametrize("name", CONTENT_PAGES)
def test_required_tags_present_once(name: str, pages: dict) -> None:
    """Каждый канонический тег присутствует ровно один раз и не пуст."""
    page = pages[name]
    problems = []
    if not page["title"]:
        problems.append("<title> пуст или отсутствует")
    if not page["description"]:
        problems.append('<meta name="description"> пуст или отсутствует')
    for tag in REQUIRED_TAGS:
        value = page[tag]
        if not value:
            problems.append(f"{tag} пуст или отсутствует")
    html = _read(name).lower()
    for tag in REQUIRED_TAGS:
        # og:* пишутся через property=, остальные — через name=. Считать только
        # name= нельзя: проверка дублей молча давала 0 для всех og-тегов, то
        # есть проверяла их наличие, но не повторяемость.
        attr = "property" if tag.startswith("og:") else "name"
        count = html.count(f'<meta {attr}="{tag}"')
        if count > 1:
            problems.append(f"{tag} встречается {count} раз — движок возьмёт первый")
        elif count == 0:
            problems.append(f"{tag} не найден по <meta {attr}=… — форма тега изменилась")
    assert not problems, (
        f"{name}: " + "; ".join(problems) + ". Канон страницы — <title>, "
        f'<meta name="description"> и og:image в <head>; og:* и twitter:* '
        f"обязаны быть их дословными копиями (см. докстринг модуля)."
    )


@pytest.mark.parametrize("name", CONTENT_PAGES)
def test_og_and_twitter_match_canonical(name: str, pages: dict) -> None:
    """og/twitter — дословные копии канона, а не рукописные сокращения.

    Расхождение почти всегда выглядит как «устаревший текст»: страницу правили,
    а производный тег забыли. Обратное (meta подогнали под og) здесь ловится
    тем же ассертом — и оно ровно настолько же неверно.
    """
    page = pages[name]
    mismatches = []
    for tag, canonical_key in {**CANONICAL, **IMAGE_MIRRORS}.items():
        canonical = page[canonical_key]
        actual = page[tag]
        if actual != canonical:
            mismatches.append(
                f"{tag}\n"
                f"      ожидается (= {canonical_key}): {canonical!r}\n"
                f"      фактически:                  {actual!r}"
            )
    assert not mismatches, (
        f"{name}: SEO-теги разошлись с каноном страницы.\n    "
        + "\n    ".join(mismatches)
        + "\n  Либо приведите тег к канону, либо (если изменился сам канон) — "
          "к нему все сразу. Правка только одного из двух зеркал возвращает "
          "долг при следующем же обновлении страницы."
    )


@pytest.mark.parametrize("name", CONTENT_PAGES)
def test_description_is_not_placeholder(name: str, pages: dict) -> None:
    """Описание не должно выродиться в пустышку после копирования.

    Копирование канона в og/twitter — механическая операция, и её естественная
    ошибка — скопировать не то (заглушку, обрезанную строку, значение из
    соседней страницы). Проверка ловит пустое и односимвольное, остальное —
        глазами на превью в соцсетях.
    """
    value = pages[name]["description"] or ""
    assert len(value.strip()) >= 30, (
        f"{name}: описание короче 30 символов ({value!r}). После копирования "
        f"канона в og/twitter такое значение размножится по трём тегам сразу."
    )


def _top_level_jsonld_descriptions(html: str) -> list[str]:
    """Значения description на верхнем уровне объектов JSON-LD.

    Только верхний уровень: description вложенных узлов (на карточках —
    ``about.Drug``) описывает вещество, а не страницу, и каноном для него
    не является. Считать все description подряд значило бы требовать от
    описания вещества равенства с описанием страницы.
    """
    found: list[str] = []
    for block in LD_RE.findall(html):
        try:
            obj = json.loads(block.strip())
        except json.JSONDecodeError as exc:
            raise AssertionError(f"блок JSON-LD не разбирается: {exc}") from exc
        for item in obj if isinstance(obj, list) else [obj]:
            if isinstance(item, dict) and isinstance(item.get("description"), str):
                found.append(item["description"])
    return found


ALL_PAGES = sorted(
    p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.html")
)

# Страницы без JSON-LD. Раньше тест ниже скипался со словами «проверка не
# применима», и в обычном прогоне это выглядело как успех — ровно та ловушка,
# из-за которой скипы перестают читать. Теперь отсутствие разметки допустимо
# ТОЛЬКО для явного списка: compare.html (собирается из data.json без
# статического текста), google4a9d23e35c6c3e23.html (подтверждение владения
# поисковиком) и offline.html (служебная страница service worker). Появление
# новой страницы без разметки — падение, а не скип.
NO_JSONLD_PAGES = frozenset({
    "compare.html",
    "google4a9d23e35c6c3e23.html",
    "offline.html",
})


@pytest.mark.parametrize("name", ALL_PAGES)
def test_jsonld_description_mirrors_meta(name: str) -> None:
    """JSON-LD description — копия meta description, а не вторая редакция.

    Находка `SEO-P2-01`. Раньше в шаблоне карточек стояло
    `"description": "{{ about_j }}"`, то есть сырое поле about, тогда как
    meta description собиралось из about + числа грейда и обрезалось по
    DESC_MAX. На 94 страницах из 144 структурированные данные расходились с
    мета-описанием: на 91 оно было урезанным префиксом, а на трёх
    (lavanda, molibden, sulforafan) обрезание делало meta короче JSON-LD.

    Канон тот же, что у og/twitter после MKT-P2-09/10: один источник правды
    на страницу. Правка мета-описания не должна расходиться с разметкой.
    """
    html = (ROOT / name).read_text(encoding="utf-8")
    descriptions = _top_level_jsonld_descriptions(html)
    if not descriptions:
        assert name in NO_JSONLD_PAGES, (
            f"{name}: нет JSON-LD, и страницы нет в NO_JSONLD_PAGES. "
            f"Либо добавьте разметку, либо обоснуйте исключение в списке."
        )
        return
    meta = _meta_map(html).get("description")
    bad = [d for d in descriptions if d != meta]
    assert not bad, (
        f"{name}: {len(descriptions)} JSON-LD description, из них "
        f"{len(bad)} не равны <meta name=\"description\">.\n    "
        + "\n    ".join(
            f"JSON-LD: {d[:120]!r}\n      meta:   {(meta or '')[:120]!r}" for d in bad
        )
    )


@pytest.mark.parametrize("name", ALL_PAGES)
def test_jsonld_is_parseable(name: str) -> None:
    """Каждый блок ld+json обязан разбираться json.loads.

    Регрессия из `SEO-P2-01`: многострочный литерал в `{% set %}` шаблона
    каталога вставлял реальный перевод строки внутрь JSON-строки, и
    разметка переставала быть JSON — при этом страница продолжала
    отображаться, а ошибку видели только поисковики.
    """
    html = (ROOT / name).read_text(encoding="utf-8")
    for block in LD_RE.findall(html):
        try:
            json.loads(block.strip())
        except json.JSONDecodeError as exc:
            pytest.fail(f"{name}: блок application/ld+json не разбирается: {exc}")


@pytest.mark.parametrize("name", ALL_PAGES)
def test_no_bare_sup_catalog_link(name: str) -> None:
    """Ссылки ровно на каталог `/sup/` — нерабочие.

    Находка `SEO-P2-03`: на главной была одна ссылка на `/sup/` вместо
    `sup/index.html`. На момент закрытия таких ссылок в `docs/` не
    осталось ни одной, но руками `href="/sup/"` написать легко, и
    страница-пример не нужна: адрес без имени файла отдаёт 404 на
    GitHub Pages, а каталог сам по себе не является целью ссылки.
    """
    html = (ROOT / name).read_text(encoding="utf-8")
    bare = []
    for i, line in enumerate(html.splitlines(), 1):
        for m in HREF_RE.finditer(line):
            href = (m.group(1) if m.group(1) is not None else m.group(2)) or ""
            if href.rstrip("/").endswith("/sup") or href in {"sup", "./sup", "/sup"}:
                bare.append(f"{name}:{i} -> {href!r}")
    assert not bare, (
        "Ссылки на каталог sup без имени файла (будут 404):\n    "
        + "\n    ".join(bare)
        + "\n  Правильный адрес каталога — sup/index.html (с ../ с карточки)."
    )


def test_excluded_pages_still_exist() -> None:
    """Исключения должны быть живыми, иначе список врёт.

    Если заглушку или файл верификации удалили, оставленная причина станет
    неверной, а следующий человек будет искать несуществующую страницу.
    """
    for name, reason in EXCLUDED_PAGES.items():
        assert (ROOT / name).exists(), (
            f"{name} в EXCLUDED_PAGES, но файла нет. Причина исключения "
            f"({reason}) больше не действует — уберите запись."
        )
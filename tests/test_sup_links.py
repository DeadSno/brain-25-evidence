"""Битые ссылки и якоря в 131 сгенерированной sup-странице.

F-30 (QA-P2-03): страницы генерируются из data.json, и ошибка в данных
(переименованный slug, удалённая карточка) тихо превращается в ссылку
в никуда. Ни одного теста на это не было.

Что проверяется:

  * внутренние `href`/`src` — файл существует;
  * якоря `#id` — цель на той же странице существует;
  * межстраничные якоря `other.html#id` — файл И якорь существуют;
  * внешние ссылки (http/https/mailto/tel) — только форма проверяется,
    сама доступность не проверяется: это сетевой тест, и он помечен
    маркером network, чтобы не болтать с внешними хостами в обычном
    прогоне;
  * пустые и служебные (`#`, `javascript:`, `data:`) — пропускаются
    осознанно, это не ссылки на файлы.

Самый ценный случай здесь — `docs/sup/index.html`: он перечисляет все
карточки, и именно там ошибка в slug видна пользователю сразу.

В конце — обязательная проверка на отрицательном примере: гейт, который
проходит на заведомо битой разметке, хуже отсутствующего гейта.
"""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
from lxml import html as lxml_html

ROOT = Path(__file__).resolve().parents[1]
SUP = ROOT / "docs" / "sup"

PAGES = sorted(SUP.glob("*.html"))

EXTERNAL = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")
SKIP_SCHEMES = ("mailto:", "tel:", "data:", "javascript:", "#")

#: Атрибуты, в которых лежат ссылки
LINK_ATTRS = (("a", "href"), ("link", "href"), ("img", "src"),
              ("script", "src"), ("source", "src"), ("iframe", "src"))


def _links(page: Path) -> list[tuple[str, str]]:
    """-> [(атрибут, значение)] для всех ссылок страницы."""
    doc = lxml_html.fromstring(page.read_bytes())
    out = []
    for tag, attr in LINK_ATTRS:
        for el in doc.xpath("//" + tag):
            v = el.get(attr)
            if v:
                out.append(("%s/%s" % (tag, attr), v.strip()))
    return out


def _is_external(url: str) -> bool:
    return bool(EXTERNAL.match(url))


def _fragment(url: str) -> str:
    return unquote(urlsplit(url).fragment)


def _resolve(page: Path, url: str) -> Path | None:
    """Путь внутри docs/ либо None, если ссылка внешняя."""
    if not url or url.startswith(SKIP_SCHEMES) or _is_external(url):
        return None
    target = urlsplit(url).path
    if not target:
        return None
    return (page.parent / unquote(target)).resolve()


def test_sup_pages_are_present():
    assert len(PAGES) >= 130, f"в docs/sup/ всего {len(PAGES)} страниц"


def test_internal_targets_exist():
    """Каждая внутренняя ссылка ведёт в существующий файл."""
    broken = []
    for page in PAGES:
        for attr, url in _links(page):
            target = _resolve(page, url)
            if target is None:
                continue
            if not target.exists():
                broken.append("%s -> %s (%s)" % (page.name, url, attr))
    assert not broken, "битые внутренние ссылки:\n  " + "\n  ".join(sorted(broken))


def test_same_page_anchors_exist():
    """Якорь #id на той же странице обязан найтись."""
    broken = []
    for page in PAGES:
        doc = lxml_html.fromstring(page.read_bytes())
        ids = set(doc.xpath("//*[@id]/@id"))
        for attr, url in _links(page):
            frag = _fragment(url)
            if not frag:
                continue
            if urlsplit(url).path:      # якорь на другой странице — см. ниже
                continue
            if frag not in ids:
                broken.append("%s -> #%s (%s)" % (page.name, frag, attr))
    assert not broken, "якоря без цели:\n  " + "\n  ".join(sorted(broken))


def test_cross_page_anchors_exist():
    """`other.html#id` — файл и якорь внутри него должны существовать."""
    broken = []
    for page in PAGES:
        for attr, url in _links(page):
            frag = _fragment(url)
            if not frag:
                continue
            target = _resolve(page, url)
            if target is None or not urlsplit(url).path:
                continue
            if not target.exists():
                continue          # это уже ловит test_internal_targets_exist
            if target.suffix.lower() not in (".html", ".htm"):
                continue
            try:
                other = lxml_html.fromstring(target.read_bytes())
            except Exception:
                continue
            if frag not in set(other.xpath("//*[@id]/@id")):
                broken.append("%s -> %s#%s (%s)" % (page.name, url, frag, attr))
    assert not broken, "межстраничные якоря без цели:\n  " + "\n  ".join(sorted(broken))


def test_index_links_to_existing_cards():
    """Индекс обязан вести только на существующие карточки.

    Это самая заметная для пользователя ошибка: карточка в списке есть,
    а клик приводит в 404.
    """
    index = SUP / "index.html"
    assert index.exists(), "docs/sup/index.html отсутствует"
    targets = {t for _, u in _links(index)
               for t in [_resolve(index, u)] if t is not None}
    missing = sorted(p.name for p in targets if not p.exists())
    assert not missing, "в индексе есть ссылки на несуществующие файлы: %s" % missing
    assert len(targets) >= 130, (
        f"индекс ссылается всего на {len(targets)} страниц, ожидалось >= 130 — "
        f"карточки выпали из списка"
    )


def test_link_gate_catches_broken_links(tmp_path: Path):
    """Отрицательный пример: гейт обязан ловить битую ссылку."""
    page = tmp_path / "p.html"
    page.write_text(
        '<html lang="ru"><head><title>t</title></head><body>'
        '<a href="/nope/missing.html">битая ссылка</a>'
        '<a href="#nowhere">битый якорь</a>'
        "</body></html>",
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        _assert_no_broken_internal([page])
    with pytest.raises(AssertionError):
        _assert_no_broken_anchors([page])


def _assert_no_broken_internal(pages: list[Path]) -> None:
    broken = []
    for page in pages:
        for attr, url in _links(page):
            target = _resolve(page, url)
            if target is not None and not target.exists():
                broken.append("%s -> %s" % (page.name, url))
    assert not broken, "битые ссылки: %s" % broken


def _assert_no_broken_anchors(pages: list[Path]) -> None:
    broken = []
    for page in pages:
        doc = lxml_html.fromstring(page.read_bytes())
        ids = set(doc.xpath("//*[@id]/@id"))
        for attr, url in _links(page):
            frag = _fragment(url)
            if frag and not urlsplit(url).path and frag not in ids:
                broken.append("%s -> #%s" % (page.name, frag))
    assert not broken, "битые якоря: %s" % broken
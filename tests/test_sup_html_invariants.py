"""Инварианты HTML на 131 сгенерированной sup-странице.

F-29 (QA-P1-03): страниц много, а проверки их формы не было — прогон
молча ловил только исключение при разборе, но не «страница кривая».

Полного HTML5-валидатора здесь нет намеренно: `html5lib` не установлен,
а ставить зависимость ради проверки каркаса смысла нет. Ниже перечислены
инварианты — те, что в этом проекте действительно ломались:

  1. один <html>, один <head>, один <h1> — иначе сломан каркас
     документа, и всё дальнейшее (снапшоты, парсеры, карта сайта)
     опирается на неверное дерево;
  2. непустой <title> и <meta name="description"> — страница без них
     выпадает из сниппета;
  3. html/@lang задан и равен "ru" — иначе скринридер читает русский
     текст иностранным голосом, а псевдолокализация (i18n-аудит)
     не имеет опоры;
  4. id уникальны — дубли ломают якоря вида #id и пары label/for;
  5. амперсанд экранирован.

Пункт 5 сделан по исходнику, а не по разобранному дереву, и это важно:
lxml ДЕКОДИРУЕТ &amp; в &, поэтому по .text корректно экранированный
вывод выглядит сломанным — на этом обманулись 15 страниц при первой
попытке проверки. Скрипты и стили вырезаются: внутри легален `&&`.

Экранирование держится на автоэкранировании Jinja в
templates/sup.html.j2:154 (`{{ s.journal }}`); появление `|safe` на
этой строке тест поймает.

Проверка проходит на всех страницах, а 12 из них содержат корректные
`&amp;` в названиях журналов — то есть тест не зелёный вхолостую:
он стоит на реальном тексте, который сломается первым.
"""
import re
from pathlib import Path

import pytest
from lxml import html as lxml_html

ROOT = Path(__file__).resolve().parents[1]
SUP = ROOT / "docs" / "sup"

SCRIPTISH = re.compile(r"<(script|style)\b.*?</\1\s*>", re.I | re.S)
# «&», за которым не начинается корректная сущность: amp, &#38; или &#x26;
AMP = re.compile(r"&(?!(?:[a-zA-Z][a-zA-Z0-9]{1,30}|#\d{1,5}|#x[0-9a-fA-F]{1,6});)")

EXPECTED_LANG = "ru"
TITLE_SUFFIX = "Brain 25 Evidence"
# 131 страница из аудита QA-P1-03. Порог, а не точное число: добавление
# карточки не должно ронять тест, а молчащая пустая папка — должна.
MIN_PAGES = 130

PAGES = sorted(SUP.glob("*.html"))


def test_sup_pages_are_present():
    """Аудит писал про 131 страницу. Мало — значит сборка отвалилась."""
    assert len(PAGES) >= MIN_PAGES, (
        f"в docs/sup/ всего {len(PAGES)} страниц, ожидалось >= {MIN_PAGES}. "
        f"Возможно, сборка sup не запускалась — тогда проверки ниже "
        f"проверяют пустоту, а не сайт."
    )
    assert "index.html" in {p.name for p in PAGES}


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_document_frame(page: Path):
    """Каркас документа и метаданные — по одному экземпляру, все заполнены."""
    raw = page.read_bytes()
    doc = lxml_html.fromstring(raw)
    src = page.read_text(encoding="utf-8")

    assert len(doc.xpath("//html")) == 1, f"{page.name}: не один <html>"
    assert len(doc.xpath("//head")) == 1, f"{page.name}: не один <head>"

    h1s = doc.xpath("//h1")
    assert len(h1s) == 1, f"{page.name}: <h1> встречается {len(h1s)} раз, ждали 1"
    assert "".join(h1s[0].itertext()).strip(), f"{page.name}: пустой <h1>"

    title = "".join(doc.xpath("//title/text()") or []).strip()
    assert title, f"{page.name}: пустой <title>"
    assert TITLE_SUFFIX in title, (
        f"{page.name}: в <title> нет {TITLE_SUFFIX!r}: {title[:80]!r}"
    )

    desc = doc.xpath('//meta[@name="description"]/@content')
    assert desc, f'{page.name}: нет <meta name="description">'
    assert desc[0].strip(), f"{page.name}: пустой description"

    lang = doc.xpath("/html/@lang")
    assert lang, f"{page.name}: у <html> нет @lang"
    assert lang[0].strip() == EXPECTED_LANG, (
        f"{page.name}: @lang={lang[0]!r}, ожидалось {EXPECTED_LANG!r}"
    )

    ids = doc.xpath("//*[@id]/@id")
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"{page.name}: повторяющиеся id: {dupes}"

    bad = AMP.findall(SCRIPTISH.sub("", src))
    assert not bad, (
        f"{page.name}: неэкранированный & в разметке (найдено {len(bad)}). "
        f"Обычно это `|safe` в шаблоне вместо автоэкранирования Jinja."
    )


def test_ampersand_check_is_not_vacuous():
    """Страховка гейта: проверка №5 обязана быть в состоянии сработать.

    Гейт, который зелёный потому, что regex ничего не находит, хуже
    отсутствующего гейта: он закрывает задачу в отчёте. Здесь мы убеждаемся,
    что тот же regex находит `&` в заведомо битой строке.
    """
    assert AMP.findall("a & b"), "AMP не ловит одиночный & — проверка вышла из строя"
    assert AMP.findall("текст &ещё"), "AMP не ловит & перед буквой"
    assert not AMP.findall("&amp;"), "AMP считает корректную сущность ошибкой"
    assert not AMP.findall("&#8212;"), "AMP считает числовую сущность ошибкой"
    assert not AMP.findall("&nbsp;"), "AMP считает именованную сущность ошибкой"

    # 12 страниц реально содержат &amp; — значит набор не пустой.
    with_amp = [p.name for p in PAGES if "&amp;" in p.read_text(encoding="utf-8")]
    assert with_amp, (
        "ни одна страница не содержит &amp; — проверка экранирования "
        "проверяет пустоту. Ожидаются названия журналов вида "
        "'Diabetes, obesity & metabolism'"
    )
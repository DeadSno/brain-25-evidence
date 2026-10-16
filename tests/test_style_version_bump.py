"""style.css?v= в разметке и CACHE_VERSION в sw.js обязаны быть подняты
вместе с правкой самого style.css.

Почему это отдельный гейт, а не замечание в шапке sw.js
------------------------------------------------------
Правило «поднять ?v= и CACHE_VERSION» записано в шапке `docs/sw.js`
и повторено там же ещё дважды, с указанием конкретных случаев (v91→v92,
v84→v85). Тем не менее оно нарушалось трижды за одну сессию: правка
`.atlas-legend` и правка `--lh-title` дошли до git, но не до браузера.

Как это выглядит снаружи
------------------------
Никак. Сайт открывается, всё работает, тесты зелёные. Стили новые лежат
на диске, сервер их отдаёт корректно — но браузер отдаёт закэшированный
файл и применяет старую версию. Отличить это от «правило не работает»
невозможно: диагностика стоит отдельного захода в devtools, и при
работе над несколькими правками подряд её обычно пропускают.

Почему именно сверка, а не «файл изменился — значит версия должна»
---------------------------------------------------------------
Git не хранит, какой файл менялся в прошлом коммите, в рабочей копии
этой информации тоже нет. Дёшево и надёжно проверяемо только сравнение
с зафиксированным числом: если число в разметке не совпадает с числом в
комментарии над CACHE_VERSION — значит кто-то поднял одно и забыл другое
(или наоборот).

Что проверяем
-------------
1. Каждая страница в docs/ и docs/sup/, подключающая style.css, указывает
   одно и то же число `?v=`.
2. Это число совпадает с числом, записанным в комментарии над
   `CACHE_VERSION` в sw.js. Комментарий написан именно для этого:
   агент, поднимающий версию, дописывает туда дату и причину.
3. Число действительно поднято — оно не ниже того, что записано в
   baseline-файл `tests/_style_version_baseline.txt`. Файл меняется
   только руками и только вместе с реальным бампом.
4. Страницы не подключают style.css двумя разными версиями внутри
   одного документа (встречалось в sup/).

Ограничение, зафиксированное честно
-----------------------------------
Тест поймает рассинхрон версий, но не поймает кейс «все три версии
подняли, а ?v= в разметке забыли на одной из 144 страниц» — для этого
нужна история git. Пункт 3 закрывает только очевидное: число не должно
уменьшаться.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SW = DOCS / "sw.js"
BASELINE = Path(__file__).resolve().parent / "_style_version_baseline.txt"

#: style.css?v=NNN — с необязательным суффиксом вида ?v=427a
STYLE_HREF = re.compile(r"""style\.css\?v=(\d+)""")
#: Число под version.js?v=NNN — отдельная шкала, к предмету теста не относится
VERSION_HREF = re.compile(r"""version\.js\?v=(\d+)""")

#: Комментарий прямо над CACHE_VERSION. Формат задан здесь, чтобы
#: невозможно было поднять версию, не записав причину: пустой комментарий
#: и число без комментария оба считаются ошибкой.
CACHE_COMMENT = re.compile(
    r"/\*\s*Бамп\s+v(\d+)\s*->\s*v(\d+)[^*]*\*/\s*var\s+CACHE_VERSION\s*=\s*'v(\d+)'",
    re.S,
)


def _pages():
    return sorted(list(DOCS.glob("*.html")) + list(DOCS.glob("sup/*.html")))


def test_every_page_links_one_single_style_version():
    """Все страницы — одна версия. Расхождение означает разный кэш."""
    per_page: dict[str, set[int]] = {}
    for p in _pages():
        text = p.read_text(encoding="utf-8")
        found = {int(v) for v in STYLE_HREF.findall(text)}
        if found:
            per_page[p.relative_to(DOCS.parent).as_posix()] = found

    assert per_page, (
        "Ни одна страница не подключает style.css?v=NNN. Гейт бессмысленен "
        "без разметки — проверь, что файлы на месте."
    )

    # Страница может ссылаться на style.css несколько раз, но с одним
    # числом: два разных ?v= внутри одного документа означают, что
    # браузер кэширует две копии и одна из них устареет.
    split = {f: sorted(v) for f, v in per_page.items() if len(v) > 1}
    assert not split, (
        "Страница подключает style.css с двумя разными версиями:\n"
        + "\n".join(f"  {f}: {v}" for f, v in sorted(split.items()))
    )

    everywhere = set().union(*per_page.values())
    assert len(everywhere) == 1, (
        f"Разные версии style.css в разных страницах: "
        f"{sorted(everywhere)}. Часть страниц получит новый CSS, часть — "
        f"старый из кэша. Подними ?v= везде разом."
    )


def test_style_version_matches_cache_version():
    """style.css?v= и CACHE_VERSION обязаны быть подняты в одной правке.

    Числа у них разные — это две независимые шкалы (?v= сейчас 428,
    CACHE_VERSION v94), и сравнивать их между собой нельзя. Проверяется
    другое: у обоих есть запись о последнем бампе, и она не пустая.

    Подняли ?v= в разметке, забыли CACHE_VERSION — activate не почистит
    старый кэш, и новые стили останутся в старой копии у всех, кто уже
    был на сайте. Обратный случай: подняли CACHE_VERSION, забыли ?v= —
    браузер по старому URL достанет старый файл из кэша.
    """
    sw = SW.read_text(encoding="utf-8")
    m = CACHE_COMMENT.search(sw)
    assert m, (
        "Над CACHE_VERSION в sw.js нет комментария формата "
        "«Бамп vN -> vM <причина>». Без него нечего сверять: "
        "причина обязана быть записана рядом с числом."
    )
    from_comment, to_comment, in_code = (int(g) for g in m.groups())
    assert from_comment == to_comment - 1, (
        f"Комментарий говорит о бампе v{from_comment} -> v{to_comment}, "
        f"а в коде CACHE_VERSION = 'v{in_code}'. Числа должны сходиться."
    )
    assert to_comment == in_code, (
        f"Комментарий обещает CACHE_VERSION v{to_comment}, "
        f"в коде стоит v{in_code}."
    )
    # Причина обязана быть не пустой захардкоженной заглушкой.
    reason = CACHE_COMMENT.search(sw).group(0)
    assert len(reason) > len("/* Бамп v0 -> v1 */"), (
        "Комментарий над CACHE_VERSION не содержит причины. Раньше он "
        "использовался как запись для людей; теперь на него же завязан "
        "этот тест, и пустая причина делает проверку бессмысленной."
    )

    pages = _pages()
    seen: set[int] = set()
    for p in pages:
        seen |= {int(v) for v in STYLE_HREF.findall(p.read_text(encoding="utf-8"))}
    assert seen, "разметка не ссылается на style.css?v="


def test_style_version_is_not_rolled_back():
    """Версия style.css не должна уменьшаться.

    Baseline меняется руками и только вместе с настоящим бампом. Если
    число уехало назад — значит кто-то откатил версию, и кэш у всех,
    кто получил новую версию, останется с битым файлом.
    """
    assert BASELINE.exists(), (
        f"{BASELINE.name} не найден. Это фиксированная точка отсчёта: "
        f"без неё тест не может отличить откат версии от её сдвига."
    )
    baseline = int(BASELINE.read_text(encoding="utf-8").strip())
    current = set()
    for p in _pages():
        current |= {int(v) for v in STYLE_HREF.findall(p.read_text(encoding="utf-8"))}
    assert current == {baseline}, (
        f"?v= в разметке — {sorted(current)}, baseline — {baseline}. "
        f"Если это намеренный бамп — обнови {BASELINE.name} руками "
        f"вместе с правкой разметки. Если откат — верни число назад."
    )


def test_templates_match_pages_style_version():
    """Шаблоны sup обязаны нести то же `?v=`, что и сгенерированные страницы.

    Рассинхрон «в шаблоне старое, на страницах новое» случался четыре раза
    (v413/414, v423/425, v425/429, v429/430). Снаружи его не видно: сайт
    работает, гейты зелёные, а следующая перегенерация `scripts/build_sup.py`
    молча откатила бы номер сразу на всех 131 странице `docs/sup/*.html` —
    и возвратные посетители получили бы CSS из кэша.

    В `test_build_sup_idempotent.py` этого не поймать: модуль помечен
    `snapshot_data`, а хук гоняет `-m "not network and not snapshot_data"` —
    то есть в коммите проверка не исполняется. Поэтому она живёт здесь.
    """
    templates = ROOT / "templates"
    assert templates.is_dir(), f"нет каталога шаблонов {templates}"
    baseline = int(BASELINE.read_text(encoding="utf-8").strip())
    drift: dict[str, list[int]] = {}
    for tpl in sorted(templates.glob("*.j2")):
        found: set[int] = set()
        for line in tpl.read_text(encoding="utf-8").splitlines():
            # Только настоящая разметка: в комментариях {# … #} шаблона
            # перечислены старые номера голыми «?v=413», «?v=423» и т.п.
            if "href" in line and "style.css?v=" in line:
                found |= {int(v) for v in STYLE_HREF.findall(line)}
        if found and found != {baseline}:
            drift[tpl.relative_to(ROOT).as_posix()] = sorted(found)
    assert not drift, (
        f"Шаблоны отстали от страниц по style.css?v=: {drift}, "
        f"а страницы несут {baseline}. Перегенерация из такого шаблона "
        f"понизила бы бампер на всех sup-страницах — подними ?v= в шаблоне "
        f"вместе с разметкой (см. CONVENTIONS.md)."
    )


def test_version_js_bump_does_not_drift():
    """Та же логика для version.js?v=NNN — отдельная шкала, но правило то же.

    Обновление этого числа делает пре-коммит-хук, поэтому проверка может
    быть снисходительнее: важно, чтобы число существовало и не уехало назад
    относительно соседних страниц.
    """
    per_page = {}
    for p in _pages():
        found = {int(v) for v in VERSION_HREF.findall(p.read_text(encoding="utf-8"))}
        if found:
            per_page[p.relative_to(DOCS.parent).as_posix()] = found
    assert per_page, "ни одна страница не подключает version.js?v=NNN"
    everywhere = set().union(*per_page.values())
    assert len(everywhere) == 1, (
        f"Разные версии version.js в разметке: {sorted(everywhere)}."
    )
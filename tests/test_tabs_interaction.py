"""Клик по вкладкам действительно переключает: interactions и trends.

Зачем файл существует. Расхождение селектора в JS с разметкой не видно
ни на одном снимке: класс в разметке и CSS-правило меняются
согласованно, вычисленные стили те же, эталон совпадает побайтово.
Ломается только `querySelectorAll` — обработчик не навешивается, и
кнопка молча становится мёртвой. Так было в v5.4.0 с dataset.tab (см.
reports/archive/v51/RENAME_TAB.md, раздел 3.1 — файл переехал из
reports/ при консолидации v5.6.3, commit 9ac8d4d), и тогда вывод
«снапшоты зелёные, значит всё в порядке» оказался ложью.

На сайте ДВЕ разные реализации вкладок, путать их нельзя:

  interactions (docs/interactions.html:284-289): `.tr-tabs` с
  role="tablist", кнопки `[role="tab"]` с data-mode, класс состояния
  `active`, aria-selected + roving tabindex, панели role="tabpanel".
  Всё пересчитывает setMode (docs/interactions.html:423-443); класса
  `active` в исходной разметке кнопок нет — его ставит только JS
  (docs/interactions.html:430, начальный вызов :474).

  trends (docs/trends.html:375-379): `.tr-tabs` без ARIA, кнопки
  `.tr-tab` с data-tab, класс состояния `on` (в разметке уже стоит,
  docs/trends.html:376). Переключает setTab (docs/trends.html:500-504).

Главная проверка — не «элемент нашёлся», а «клик перенёс состояние на
другую вкладку и снял его с прежней». Остальные проверки защищают от
тихой подмены: счёт и состав вкладок, согласованность aria-selected /
tabindex с активной вкладкой, видимость активной панели, отсутствие
старых селекторов.

Ожидание вместо таймаутов. Фиксированный `wait_for_timeout` после
загрузки проверяет, что сервер быстрый, а не что UI готов. Вместо него
`wait_for_function` по признаку готовности:

  interactions — появился `.tr-tabs [role="tab"].active`: класс ставит
  только setMode при загрузке (docs/interactions.html:474);

  trends — `#kpiPubs2025` перестал быть «—»: renderStats заполняет KPI
  в конце initApp (docs/trends.html:496, 515), а обработчики вкладок
  вяжутся ДО него (docs/trends.html:485-486), то есть заполненный KPI
  означает: клик уже будет перехвачен. Это важно, потому что на trends
  вкладки оживают только после загрузки data_index.json и
  timeseries.json (docs/trends.html:453-460) — событие `load` этой
  гарантии не даёт: fetch() на него не ждётся.

Запуск:
    python -m pytest tests/test_tabs_interaction.py -q

Гейт RUN_TABS удалён в v5.6.5 (tests/conftest.py). Сервер :8000 поднимает
autouse-фикстура live_server в tests/conftest.py из docs/ (если там уже
не отдаётся docs этого репозитория — сверка по sha256 style.css). Тестам
нужен живой сервер и браузеры Playwright; обычный `pytest -q` собирает их
в общий прогон (~8-10 мин), а для быстрого прогона без браузера —
`-m "not (tabs or graph)"`.
"""
import hashlib
import os
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.tabs

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright не установлен")

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("SNAPSHOT_BASE_URL",
                          "http://localhost:8000").rstrip("/")

#: Firefox не добавлен — 1.2% трафика РФ, тот же отказ, что и в снапшотах.
BROWSERS = ("chromium", "webkit")

#: Мин. высота кнопки: базовое правило `button { min-height: 44px }`
#: (docs/style.css:361) покрывает вкладки обеих страниц; свои правила
#: (docs/style.css:2521 для [role="tab"], docs/trends.html:74 для
#: .tr-tab) min-height не переопределяют. 44 px — порог WCAG 2.5.8.
#: Замерено 2026-10-18 на обоих движках: ровно 44 у всех вкладок.
MIN_TAB_HEIGHT = 44

#: Страница, селектор вкладок, ключ dataset (без "data-"), класс
#: состояния, какая вкладка активна по умолчанию, какую кликаем, счёт и
#: состав вкладок, старые селекторы (обязаны отсутствовать), JS-признак
#: готовности страницы.
PAGES = (
    {
        # v5.6.5 (H-1): interactions.html стал страницей-редиректом на
        # hactar.html, поэтому вкладки проверяются на hactar.html.
        # H-9: вкладок две — «Обзор» (сводка стека, дозы, сравнение,
        # где купить) и «Связи»; калькулятор и сравнение стали
        # секциями «Обзора», отдельных вкладок больше нет.
        "page": "hactar",
        # Селектор самого JS: docs/hactar.html (setMode).
        "tabs": '.hactar-tabs [role="tab"]',
        "attr": "mode",          # data-mode на кнопках вкладок
        "state": "active",       # класс состояния
        "first": "overview",     # default
        "second": "links",
        "n_tabs": 2,             # разметка: docs/hactar.html
        "modes": ("overview", "links"),
        # #int-graph / .int-layout остались только в мёртвом <style>
        # (docs/interactions.html), элементов с ними нет;
        # .tr-tab заменён на [role="tab"].
        "old_absent": ("#int-graph", ".int-layout", ".tr-tab"),
        # setMode отработал при загрузке: класс ставит только он.
        "ready_js": "() => !!document.querySelector("
                    "'.hactar-tabs [role=\"tab\"].active')",
    },
    {
        "page": "trends",
        # Селектор самого JS: docs/trends.html:485, :502.
        "tabs": ".tr-tab",
        "attr": "tab",           # data-tab: docs/trends.html:376-378
        "state": "on",           # класс состояния: docs/trends.html:502
        "first": "growth",       # в разметке: docs/trends.html:376
        "second": "wiki",
        "n_tabs": 3,             # разметка: docs/trends.html:376-378
        "modes": ("growth", "wiki", "citations"),
        # Имена до переименования .tab -> .tr-tab (v5.4.1) не должны
        # вернуться ни на trends, ни где-либо ещё.
        "old_absent": (".tab", ".tabs"),
        # initApp отработал: renderStats заполнил KPI
        # (docs/trends.html:496, :515). Обработчики вкладок вяжутся до
        # него (docs/trends.html:485-486), значит клик перехвачен.
        "ready_js": "() => document.getElementById('kpiPubs2025')"
                    ".textContent !== '—'",
    },
)

#: Снимок состояния вкладок и панелей — сериализуемый словарь.
#: `attr` приходит как ключ dataset: "mode" на interactions, "tab" на
#: trends — по data-атрибуту своей страницы (см. PAGES).
SNAP_JS = """({sel, attr}) => ({
    tabs: [...document.querySelectorAll(sel)].map(t => ({
        mode: t.dataset[attr],
        cls: t.className,
        aria: t.getAttribute('aria-selected'),
        tabindex: t.getAttribute('tabindex'),
        w: Math.round(t.getBoundingClientRect().width),
        h: Math.round(t.getBoundingClientRect().height),
    })),
    panels: [...document.querySelectorAll('[data-panel]')].map(p => ({
        name: p.dataset.panel,
        cls: p.className,
        hidden: p.hidden,
        display: getComputedStyle(p).display,
    })),
})"""

#: Клик по вкладке по значению её data-атрибута. Селектор ищется в
#: браузере, а не строкой на Python: если разъедутся написание
#: атрибута и значение, упадёт наш собственный код проверки, а не
#: молча «повезёт».
CLICK_JS = """({sel, attr, want}) => {
    const el = [...document.querySelectorAll(sel)]
        .find(e => e.dataset[attr] === want);
    if (!el) return false;
    el.click();
    return true;
}"""


def _check_server() -> None:
    """Сервер обязан отдавать файлы ИМЕННО ЭТОГО репозитория.

    Иначе тест проверял бы чужую копию проекта: правка в docs/ не попала
    бы на страницу, тест снял бы старое состояние и рапортовал бы
    зелёным. Та же защита, что в test_visual_snapshots.py, — сверка
    хэша style.css.
    """
    try:
        with urllib.request.urlopen(f"{BASE_URL}/style.css", timeout=10) as resp:
            served = resp.read()
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
        pytest.skip(
            f"Нет {BASE_URL} ({exc}). Запусти: "
            f"python -m http.server 8000 --directory docs  (из корня репозитория)"
        )
    local = (ROOT / "docs" / "style.css").read_bytes()
    if hashlib.sha256(served).hexdigest() != hashlib.sha256(local).hexdigest():
        pytest.skip(
            f"{BASE_URL} отдаёт ЧУЖУЮ копию проекта (style.css не совпал с "
            f"{ROOT / 'docs' / 'style.css'}). Тест проверял бы не тот код, "
            f"который меняется. Запусти сервер из этого репозитория или "
            f"укажи SNAPSHOT_BASE_URL."
        )


def _launch(pw, engine):
    """Запустить движок. Отдельная функция только ради skip-сообщения.

    `pw` передаётся снаружи, а не создаётся здесь: второй
    `sync_playwright()` в одной сессии падает с «Sync API inside the
    asyncio loop», поэтому общий экземпляр живёт в
    tests/conftest.py::playwright_instance.
    """
    try:
        return getattr(pw, engine).launch()
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
        pytest.skip(f"{engine} не запускается: {exc}. "
                    f"Поставь: playwright install {engine}")


@pytest.fixture(scope="session")
def pw(playwright_instance):
    """Один Playwright на всю сессию — общий для всех браузерных модулей.

    Свой `sync_playwright()` здесь больше не открывается: второй такой
    контекст в одной сессии падает с «Sync API inside the asyncio loop»
    (измерено: 90 errors при `-m "tabs or graph or mobile375"`). Общий
    экземпляр живёт в tests/conftest.py::playwright_instance.
    """
    return playwright_instance


def _open_page(browser, cfg):
    """Открыть страницу и дождаться готовности вкладок (см. ready_js)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/{cfg['page']}.html", wait_until="load")
    page.wait_for_function(cfg["ready_js"])
    return ctx, page


def _click_tab(page, cfg):
    """Кликнуть по вкладке cfg['second']; упасть, если её нет."""
    hit = page.evaluate(CLICK_JS, {
        "sel": cfg["tabs"], "attr": cfg["attr"], "want": cfg["second"]})
    if not hit:
        pytest.fail(
            f"не нашлась кнопка с data-{cfg['attr']}={cfg['second']!r} по "
            f"селектору {cfg['tabs']} — клик невозможен, проверять "
            f"переключение не на чем")


def _is_active(tab, state):
    """Есть ли класс состояния у вкладки (как отдельный токен класса).

    Подстрочная проверка `state in cls` ловит чужие классы, в названии
    которых встретились те же буквы (например, «on» внутри «only»),
    поэтому className разбивается на токены.
    """
    return state in tab["cls"].split()


#: 4 пары: движок × страница.
TAB_CASES = [(b, p) for b in BROWSERS for p in PAGES]


@pytest.fixture(scope="session", params=TAB_CASES,
                ids=lambda bp: f"{bp[0]}-{bp[1]['page']}")
def tab_case(request, pw):
    """Состояние вкладок до клика и после него — один проход на пару.

    Параметризация живёт на фикстуре, а не через
    `@pytest.mark.parametrize` на тестах: пометка одноимённого аргумента
    перекрыла бы фикстуру, и тест получил бы сырой tuple. Навигация и
    нажатие происходят ровно один раз на пару, результат записывается и
    читается остальными проверками.
    """
    engine, cfg = request.param
    _check_server()
    browser = _launch(pw, engine)
    ctx, page = _open_page(browser, cfg)
    try:
        before = page.evaluate(SNAP_JS, {"sel": cfg["tabs"],
                                         "attr": cfg["attr"]})
        before["old"] = {s: len(page.query_selector_all(s))
                         for s in cfg["old_absent"]}
        _click_tab(page, cfg)
        after = page.evaluate(SNAP_JS, {"sel": cfg["tabs"],
                                        "attr": cfg["attr"]})
        yield {"engine": engine, "cfg": cfg, "before": before, "after": after}
    finally:
        ctx.close()
        browser.close()


#: Страница с ARIA-вкладками и панелями — только interactions.
@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def int_case(request, pw):
    """Глубокий снимок interactions: aria-selected/tabindex и панели.

    Отдельная фикстура, а не флаг в tab_case: assertions должны
    утверждать что-то на КАЖДОМ прогоне, а не молча пропускать страницу
    без ARIA. Trends таких атрибутов и панелей не имеет вовсе
    (docs/trends.html:376-378 — голые кнопки), поэтому его глубокая
    проверка не имеет предмета.
    """
    engine = request.param
    cfg = PAGES[0]  # interactions
    _check_server()
    browser = _launch(pw, engine)
    ctx, page = _open_page(browser, cfg)
    try:
        before = page.evaluate(SNAP_JS, {"sel": cfg["tabs"],
                                         "attr": cfg["attr"]})
        _click_tab(page, cfg)
        after = page.evaluate(SNAP_JS, {"sel": cfg["tabs"],
                                        "attr": cfg["attr"]})
        yield {"engine": engine, "cfg": cfg, "before": before, "after": after}
    finally:
        ctx.close()
        browser.close()


# ── 6 проверок на пару движок × страница = 24 ──


def test_selector_finds_all_tabs(tab_case):
    """Селектор находит все кнопки вкладок — счёт верный.

    interactions: 4 кнопки (docs/interactions.html:285-288), селектор
    `.tr-tabs [role="tab"]` — тот же, что у самого JS
    (docs/interactions.html:427, :445). trends: 3 кнопки
    (docs/trends.html:376-378), селектор `.tr-tab` — тот же, что у
    setTab (docs/trends.html:502). Если селектор в JS разошёлся с
    разметкой, querySelectorAll вернёт меньше кнопок или пусто.
    """
    d = tab_case
    got = len(d["before"]["tabs"])
    assert got == d["cfg"]["n_tabs"], (
        f"{d['cfg']['page']} / {d['engine']}: {d['cfg']['tabs']} нашёл "
        f"{got} кнопок, ожидалось {d['cfg']['n_tabs']}")


def test_selector_finds_expected_modes(tab_case):
    """Найдены именно те вкладки, которыми различает обработчик.

    Атрибуты — это то, чем setMode/setTab отличают одну вкладку от
    другой (docs/interactions.html:428, :447; docs/trends.html:486,
    :502): data-mode=graph|mech|sups|drugs на interactions
    (docs/interactions.html:285-288), data-tab=growth|wiki|citations на
    trends (docs/trends.html:376-378). Пустое или чужое значение
    означает, что клик по вкладке уйдёт в несуществующий режим.
    """
    d = tab_case
    modes = [t["mode"] for t in d["before"]["tabs"]]
    assert None not in modes, (
        f"{d['cfg']['page']}: у части вкладок нет data-{d['cfg']['attr']}: "
        f"{modes} — обработчик не сможет определить, какой режим открыть")
    assert set(modes) == set(d["cfg"]["modes"]), (
        f"{d['cfg']['page']}: состав вкладок {modes}, ожидался "
        f"{sorted(d['cfg']['modes'])}")


def test_default_active_tab(tab_case):
    """По умолчанию активна первая вкладка: graph на interactions, growth на trends.

    На interactions класса `active` в разметке кнопок нет — его ставит
    только setMode при загрузке (docs/interactions.html:430, начальный
    вызов :474, default 'graph' :415-418). То есть эта проверка заодно
    доказывает, что JS-обработчик дошёл до вкладок. На trends класс `on`
    стоит прямо в разметке (docs/trends.html:376), и проверка фиксирует
    разметку; что JS его переключает — доказывает следующий тест.
    """
    d = tab_case
    state = d["cfg"]["state"]
    active = [t["mode"] for t in d["before"]["tabs"]
              if _is_active(t, state)]
    assert active == [d["cfg"]["first"]], (
        f"{d['cfg']['page']} / {d['engine']}: до клика активны {active}, "
        f"ожидалась только {d['cfg']['first']!r} — класс состояния "
        f".{state} не в порядке")


def test_click_switches_active_tab(tab_case):
    """ГЛАВНАЯ ПРОВЕРКА: клик переносит класс состояния на другую вкладку.

    Именно её отсутствие в v5.4.0 скрывало поломку: страница выглядела
    правильно, а кнопка ничего не делала, потому что обработчик
    навешивался на селектор, которого в разметке больше не было
    (docs/interactions.html:445-449; docs/trends.html:485-486).
    """
    d = tab_case
    state = d["cfg"]["state"]
    by_mode = {t["mode"]: t for t in d["after"]["tabs"]}
    got_new = by_mode.get(d["cfg"]["second"])
    assert got_new is not None, (
        f"{d['cfg']['page']}: вкладка {d['cfg']['second']!r} исчезла из "
        f"{d['cfg']['tabs']} после клика")
    assert _is_active(got_new, state), (
        f"{d['cfg']['page']} / {d['engine']}: клик по "
        f"data-{d['cfg']['attr']}={d['cfg']['second']!r} не поставил "
        f".{state} (className={got_new['cls']!r}) — обработчик стал no-op: "
        f"его селектор разошёлся с разметкой")
    got_old = by_mode.get(d["cfg"]["first"])
    assert got_old is not None and not _is_active(got_old, state), (
        f"{d['cfg']['page']}: .{state} остался на {d['cfg']['first']!r} "
        f"(className={got_old and got_old['cls']!r}) — две вкладки "
        f"выглядят активными, переключение превратилось в залипание")
    actives = [t["mode"] for t in d["after"]["tabs"] if _is_active(t, state)]
    assert actives == [d["cfg"]["second"]], (
        f"{d['cfg']['page']}: после клика активны {actives}, ровно одна "
        f"ожидалась: {d['cfg']['second']!r}")


def test_old_selectors_absent(tab_case):
    """Старые селекторы не должны остаться в разметке как элементы.

    На interactions #int-graph и .int-layout дожили только в мёртвом
    <style> (docs/interactions.html:101-148) — ни одного элемента; класс
    .tr-tab заменён на [role="tab"] (docs/interactions.html:285-288), и
    остаток .tr-tab дал бы вкладкам двойную стилизацию: CSS-правило
    .tr-tab (docs/style.css:1074) применялось бы к одним кнопкам, а
    .tr-tabs [role="tab"] (docs/style.css:2521) — к другим. На trends
    актуальны классы v5.4.1 `.tr-tab`; возврат старых имён .tab/.tabs
    означал бы откат переименования.
    """
    d = tab_case
    for sel, got in d["before"]["old"].items():
        assert got == 0, (
            f"{d['cfg']['page']}: старый селектор {sel} нашёл {got} "
            f"элементов — переименование не доведено до конца")


def test_tab_geometry(tab_case):
    """Вкладка имеет ненулевую геометрию и держит минимальные 44 px.

    Высота 44 px задаётся базовым правилом `button { min-height: 44px }`
    (docs/style.css:361) и является порогом WCAG 2.5.8; правила вкладок
    (docs/style.css:2521, docs/trends.html:74) min-height не
    переопределяют. Схлопнувшаяся или мелкая кнопка не видна ни на одном
    снимке как регрессия селектора — она просто станет меньше.
    Замер 2026-10-18: у всех вкладок ровно 44 px на обоих движках.
    """
    d = tab_case
    for t in d["before"]["tabs"]:
        assert t["w"] > 0 and t["h"] >= MIN_TAB_HEIGHT, (
            f"{d['cfg']['page']}: вкладка {t['mode']!r} имеет геометрию "
            f"{t['w']}x{t['h']} px (нужно ширина > 0, высота >= "
            f"{MIN_TAB_HEIGHT})")


# ── 2 проверки на движок (interactions) = 4 ──


def test_aria_selected_and_tabindex_track_active(int_case):
    """aria-selected и tabindex согласованы с активной вкладкой.

    Разворачивается отдельно от классов, потому что aria-selected — это
    не просто «атбут есть»: он управляет и цветом (атрибутный селектор
    docs/style.css:2533-2538), и клавиатурой. roving tabindex (у
    активной 0, у остальных -1, docs/interactions.html:431-432) —
    единственный способ добраться до вкладок с клавиатуры по WAI-ARIA
    tabs pattern; без него Tab застревает на первой кнопке. Начальная
    разметка — docs/interactions.html:285-288, пересчёт —
    docs/interactions.html:427-433.
    """
    d = int_case
    state = d["cfg"]["state"]
    for label, snap, want in (("до клика", d["before"], d["cfg"]["first"]),
                              ("после клика", d["after"], d["cfg"]["second"])):
        for t in snap["tabs"]:
            active = _is_active(t, state)
            assert t["aria"] in ("true", "false"), (
                f"interactions / {d['engine']}: {label} aria-selected у "
                f"{t['mode']!r} = {t['aria']!r} — атрибут пропал")
            assert t["tabindex"] in ("0", "-1"), (
                f"interactions / {d['engine']}: {label} tabindex у "
                f"{t['mode']!r} = {t['tabindex']!r} — roving tabindex сломан")
            assert (t["aria"] == "true") == active == (t["tabindex"] == "0"), (
                f"interactions / {d['engine']}: {label} вкладка {t['mode']!r}"
                f": класс={t['cls']!r}, aria-selected={t['aria']!r}, "
                f"tabindex={t['tabindex']!r} — три признака активности "
                f"разошлись, клавиатурщик попадёт не на ту вкладку")
        selected = [t["mode"] for t in snap["tabs"] if t["aria"] == "true"]
        assert selected == [want], (
            f"interactions / {d['engine']}: {label} aria-selected=true у "
            f"{selected}, ожидалась только {want!r}")


def test_panel_follows_active_tab(int_case):
    """Панель активной вкладки показана, остальные скрыты — до и после клика.

    Панели: docs/interactions.html:292 (panel-graph, class="active" в
    разметке), :315, :335, :353. setMode переключает и класс, и
    свойство hidden (docs/interactions.html:434-437); CSS держит
    видимость на классе: `[data-panel] { display: none }` /
    `[data-panel].active { display: block }` (docs/style.css:2548-2549).
    Проверяются оба признака плюс вычисленный display: так ловится и
    расхождение JS с разметкой, и случай, когда [hidden] перебит
    авторским CSS — класс остался, а панель видна насквозь.
    """
    d = int_case
    for label, snap, want in (("до клика", d["before"], d["cfg"]["first"]),
                              ("после клика", d["after"], d["cfg"]["second"])):
        panels = {p["name"]: p for p in snap["panels"]}
        assert set(panels) == set(d["cfg"]["modes"]), (
            f"interactions / {d['engine']}: {label} панели "
            f"{sorted(panels)}, ожидался по одной на каждую вкладку "
            f"{sorted(d['cfg']['modes'])}")
        for name, p in panels.items():
            if name == want:
                assert ("active" in p["cls"].split()
                        and not p["hidden"]
                        and p["display"] != "none"), (
                    f"interactions / {d['engine']}: {label} панель "
                    f"{name!r} должна быть видимой (class={p['cls']!r}, "
                    f"hidden={p['hidden']}, display={p['display']!r})")
            else:
                assert ("active" not in p["cls"].split()
                        and p["hidden"]
                        and p["display"] == "none"), (
                    f"interactions / {d['engine']}: {label} панель "
                    f"{name!r} должна быть скрытой (class={p['cls']!r}, "
                    f"hidden={p['hidden']}, display={p['display']!r})")

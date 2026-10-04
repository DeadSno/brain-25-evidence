"""Вкладки переключаются кликом, а не только выглядят как переключаемые.

Зачем этот файл существует. При переименовании `.tab` -> `.tr-tab`
(v5.4.1) наибольшая опасность — расхождение селектора в JS с разметкой.
Тогда страница выглядит РОВНО ТАК ЖЕ: класс в разметке и CSS-правила
переименованы согласованно, значит вычисленные стили те же, значит
визуальный эталон совпадает побайтово. Расхождение проявляется только
в `querySelectorAll` — вернёт пустой список, обработчик `click` не
навесится, и кнопка станет мёртвой.

Именно так ломалось в v5.4.0: инверсия семантики переменной дала клик,
который ничего не делал, при полностью зелёных снимках. Тогда вывод был
«снапшоты зелёные, значит всё в порядке» — а порядка не было.

Поэтому здесь главная проверка не «элемент нашёлся», а «клик перенёс класс
состояния на другой элемент». Остальные проверки защищают от тихой
подмены: что фон и шрифт пришли от правила класса, а не от того, что
элемент с классом нашёлся, и что атрибут переключения на месте — при
переименовании класса однажды уже чуть не потерялся `dataset.tab`
(подробности в reports/RENAME_TAB.md, раздел 3.1).

Стоимость прогона. Нажатий 4: по одному на пару движок × страница.
Состояние «до» и «после» снимается в одной фикстуре, и остальные
проверки читают записанный результат. Нажатий 42 было бы медленнее в
десять раз ради того же вывода; расхождение всё равно проявилось бы в
проверках 6 и 7, а не в самом факте нажатия.

Запуск:
    python -m http.server 8000 --directory docs   (из корня репозитория)
    $env:RUN_TABS="1"; pytest -q -m tabs

Без RUN_TABS тесты сняты настройкой в tests/conftest.py — они требуют
живого сервера и браузеров Playwright, а обычный `pytest -q` должен
оставаться быстрым и работать в CI без сервера.
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

#: Имя класса вкладки и контейнера после v5.4.1.
TAB = ".tr-tab"
TABS = ".tr-tabs"
#: До v5.4.1. Проверяются как «должно исчезнуть».
OLD_TAB = ".tab"
OLD_TABS = ".tabs"

#: Страница, класс состояния, атрибут переключения, значения для клика,
#: ожидаемое число кнопок, ожидаемое число кнопок по атрибуту.
PAGES = (
    ("interactions", "active", "data-mode", "supplements", "drugs", 2, 2),
    ("trends", "on", "data-tab", "growth", "wiki", 3, 3),
)

#: Мин. высота кнопки — из правила `.preset, .tr-tab { min-height: 44px }`
#: в style.css. Проверяется как нижняя граница, а не точное число.
MIN_TAB_HEIGHT = 44


def _check_server() -> None:
    """Сервер обязан отдавать файлы ИМЕННО ЭТОГО репозитория.

    Иначе тест проверял бы чужую копию проекта: правка в docs/ не попала
    бы на страницу, тест снял бы старое состояние и рапортовал бы зелёным.
    Та же защита, что в test_visual_snapshots.py, — сверка хэша style.css.
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


def _bg_signature(page, selector):
    """Фон кнопки как пара (backgroundColor, backgroundImage).

    Проверять только `backgroundColor` нельзя: у активной вкладки фон
    задан градиентом, а градиент живёт в `background-image`, и
    `backgroundColor` для него возвращает `rgba(0, 0, 0, 0)`. Такая
    проверка проходила бы только потому, что первой по счётной вкладке
    оказывалась неактивная, и падала бы на здоровой странице, если бы
    порядок изменился. Пара отражает оба случая: непрозрачный цвет у
    неактивной и градиент у активной.
    """
    return page.eval_on_selector(
        selector,
        "el => { const cs = getComputedStyle(el);"
        " return [cs.backgroundColor, cs.backgroundImage] }")


def _has_visible_background(sig):
    """Есть ли хоть какой-то видимый фон."""
    color, image = sig
    return color != ("rgba(0, 0, 0, 0)") or image != "none"


#: Состояния фона, которые означают «правило не применилось».
NO_BACKGROUND = ("rgba(0, 0, 0, 0)", "none")


def _capture(page, state_cls, data_attr, second):
    """Снимок состояния вкладок в виде обычного словаря (сериализуемо)."""
    names = page.eval_on_selector_all(TAB, "els => els.map(e => e.className)")
    by_attr = page.eval_on_selector_all(
        TAB, "els => els.map(e => e.getAttribute('" + data_attr + "'))")
    return {
        "names": names,
        "by_attr": by_attr,
        "count": len(names),
        "count_old": len(page.query_selector_all(OLD_TAB)),
        "tabs_count": len(page.query_selector_all(TABS)),
        "tabs_count_old": len(page.query_selector_all(OLD_TABS)),
        "by_attr_count": len(page.query_selector_all("[" + data_attr + "]")),
        "box": page.eval_on_selector(
            TAB, "el => { const r = el.getBoundingClientRect();"
                 " return [Math.round(r.width), Math.round(r.height)] }"),
    }


def _click_second(page, data_attr, second):
    """Нажать на вкладку по значению атрибута.

    Селектор достаётся в браузере, а не строкой на стороне Python: если
    разъедутся написание атрибута и значение, упадёт наш собственный код
    проверки, а не страница.
    """
    hit = page.evaluate(
        """({sel, attr, want}) => {
            const el = [...document.querySelectorAll(sel)]
                .find(e => e.getAttribute(attr) === want);
            if (!el) return false;
            el.click();
            return true;
        }""", {"sel": TAB, "attr": data_attr, "want": second})
    if not hit:
        pytest.fail(
            f"не нашлась кнопка с {data_attr}={second!r} по селектору {TAB} — "
            f"клик невозможен, проверять переключение не на чем")


def _launch(pw, engine):
    """Запустить движок. Отдельная функция только ради skip-сообщения.

    `pw` передаётся снаружи, а не создаётся здесь: `sync_playwright().start()`
    без удержания объекта контекста отдаёт драйвер сборщику мусора, и
    следующая фикстура падает с «Sync API inside the asyncio loop». Поэтому
    `with sync_playwright()` живёт в самой фикстуре.
    """
    try:
        return getattr(pw, engine).launch()
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
        pytest.skip(f"{engine} не запускается: {exc}. "
                    f"Поставь: playwright install {engine}")


@pytest.fixture(scope="session")
def pw():
    """Один Playwright на всю сессию.

    Отдельный `sync_playwright()` на каждую фикстуру не работает: после
    первых четырёх teardown следующий падает с «Sync API inside the
    asyncio loop». Один экземпляр на сессию — тот же приём, что и в
    test_visual_snapshots.py.
    """
    with playwright_api.sync_playwright() as p:
        yield p


#: 4 пары: движок × страница.
TAB_CASES = [(b,) + p for b in BROWSERS for p in PAGES]


@pytest.fixture(scope="session", params=TAB_CASES,
                ids=lambda p: f"{p[0]}-{p[1]}")
def tab_case(request, pw):
    """Состояние вкладок до клика и после него — один проход на пару.

    Параметризация живёт на фикстуре, а не через `@pytest.mark.parametrize`
    на тестах: пометка одноимённого аргумента перекрыла бы одноимённую
    фикстуру, и тест получил бы сырой tuple вместо словаря. Навигация и
    нажатие происходят ровно один раз на пару, результат записывается и
    читается остальными проверками.
    """
    # request.param = (движок,) + PAGES[i], поэтому 8 значений, а не 7.
    engine, page_name, state_cls, data_attr, first, second, n_tabs, \
        n_by_attr = request.param
    _check_server()
    browser = _launch(pw, engine)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    try:
        page.goto(f"{BASE_URL}/{page_name}.html", wait_until="load")
        page.wait_for_timeout(400)
        before = _capture(page, state_cls, data_attr, second)
        _click_second(page, data_attr, second)
        page.wait_for_timeout(350)
        after_classes = page.eval_on_selector_all(
            TAB,
            "els => els.map(e => [e.getAttribute('" + data_attr + "'),"
            " e.className])")
        yield {
            "engine": engine,
            "page": page_name,
            "state_cls": state_cls,
            "data_attr": data_attr,
            "first": first,
            "second": second,
            "n_tabs": n_tabs,
            "n_by_attr": n_by_attr,
            "before": before,
            "after": {k: v for k, v in after_classes},
            # фон и шрифт берём ПОСЛЕ клика: у активной вкладки свой фон
            "bg": _bg_signature(page, TAB),
            "font": page.eval_on_selector(
                TAB, "el => getComputedStyle(el).fontSize"),
        }
    finally:
        ctx.close()
        browser.close()


@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def engine_only(request, pw):
    """Движок для проверок, не привязанных к конкретной странице."""
    engine = request.param
    browser = _launch(pw, engine)
    yield {"engine": engine, "browser": browser}
    browser.close()


# ── 10 проверок на пару движок × страница = 40 ──

def test_tab_selector_finds_buttons(tab_case):
    """Переименованный селектор находит все кнопки вкладок."""
    assert tab_case["before"]["count"] == tab_case["n_tabs"], (
        f"{tab_case['page']}: {TAB} нашёл "
        f"{tab_case['before']['count']} кнопок, ожидалось {tab_case['n_tabs']}")


def test_old_selector_absent_from_markup(tab_case):
    """Старый класс `.tab` не должен остаться ни на одной кнопке."""
    assert tab_case["before"]["count_old"] == 0, (
        f"{tab_case['page']}: старый {OLD_TAB} ещё встречается в разметке — "
        f"переименование не доведено до конца")


def test_container_renamed(tab_case):
    """Контейнер переименован в `.tr-tabs`, старый `.tabs` не остался.

    Контейнер проверяется отдельно от вкладок: если переименовать только
    кнопки, разметка соберётся, но `flex` перестанет применяться, и ряд
    вкладок развалится. Снапшот это поймает, а тест — точнее.
    """
    b = tab_case["before"]
    assert b["tabs_count"] == 1, (
        f"{tab_case['page']}: {TABS} нашёл {b['tabs_count']} контейнеров, "
        f"ожидался 1")
    assert b["tabs_count_old"] == 0, (
        f"{tab_case['page']}: старый {OLD_TABS} ещё есть — flex-раскладка "
        f"контейнера перестанет применяться")


def test_tab_geometry(tab_case):
    """Кнопка имеет ненулевую геометрию и держит минимальные 44 px.

    Высота 44 px — не украшение: она задаётся правилом
    `.preset, .tr-tab { min-height: 44px }` и является порогом WCAG 2.5.8.
    Съехавший селектор оставил бы кнопку ниже порога, и это не видно ни
    на одном снимке — вкладки просто стали бы мельче.
    """
    w, h = tab_case["before"]["box"]
    assert w > 0 and h > 0, f"{tab_case['page']}: геометрия {w}x{h} px"
    assert h >= MIN_TAB_HEIGHT, (
        f"{tab_case['page']}: высота вкладки {h} px < {MIN_TAB_HEIGHT} px — "
        f"правило класса не применилось")


def test_state_class_present_before_click(tab_case):
    """До клика у одной вкладки есть класс состояния."""
    state = tab_case["state_cls"]
    assert any(state in c for c in tab_case["before"]["names"]), (
        f"{tab_case['page']}: до клика нет .{state} в "
        f"{tab_case['before']['names']}")


def test_click_switches_state(tab_case):
    """ГЛАВНАЯ ПРОВЕРКА: клик переносит класс состояния на другую вкладку.

    Именно её не было в проекте, и именно её отсутствие скрывало поломку
    с `dataset.tab`: страница выглядела правильно, а кнопка не работала.
    """
    state = tab_case["state_cls"]
    got = tab_case["after"].get(tab_case["second"], "")
    assert state in got, (
        f"{tab_case['page']} / {tab_case['engine']}: клик по "
        f"{tab_case['data_attr']}={tab_case['second']!r} не поставил .{state}; "
        f"className={got!r}. Селектор обработчика разошёлся с разметкой — "
        f"клик стал no-op.")


def test_click_clears_previous_state(tab_case):
    """Клик снимает класс состояния с прежней вкладки — переключение, а не залипание."""
    state = tab_case["state_cls"]
    got = tab_case["after"].get(tab_case["first"])
    assert got is not None, (
        f"{tab_case['page']}: вкладка {tab_case['first']!r} исчезла из "
        f"{TAB} после клика")
    assert state not in got, (
        f"{tab_case['page']}: .{state} остался на {tab_case['first']!r} "
        f"(className={got!r}) — две вкладки выглядят активными")


def test_computed_background_applied(tab_case):
    """Фон посчитан браузером, то есть правило класса действительно совпало.

    Проверка на вычисленные значения, а не на наличие класса: класс в
    разметке есть и при съехавшем селекторе, а вот совпадение правил —
    нет. Различает «переименовали» и «сломали раскладку».

    Сравнивается пара (backgroundColor, backgroundImage), потому что у
    активной вкладки фон — градиент, а градиент живёт в background-image,
    и один только backgroundColor для него прозрачен. Первая версия этой
    проверки смотрела лишь на цвет: на здоровой странице она проходила
    только потому, что первой оказывалась неактивная вкладка. См.
    `_bg_signature`.
    """
    sig = tuple(tab_case["bg"])
    assert sig != NO_BACKGROUND and _has_visible_background(sig), (
        f"{tab_case['page']}: фон прозрачен ({sig}) — правило класса не "
        f"применилось")


def test_computed_font_size_from_rule(tab_case):
    """Размер шрифта задан правилом класса, а не базовым 16 px.

    Обе страницы задают свой кегль в правиле вкладки (`.9rem` и `.92rem`),
    поэтому 16 px означало бы, что селектор не совпал.
    """
    assert tab_case["font"] != "16px", (
        f"{tab_case['page']}: шрифт 16 px — правило класса не применилось")


def test_data_attribute_intact(tab_case):
    """Атрибут переключения цел и не был переименован вместе с классом.

    Отдельная проверка потому, что `.tab` и `data-tab` выглядят
    одинаково, а ведут себя по-разному: замена `.tab` в `dataset.tab`
    ломает чтение атрибута, и вкладки перестают переключаться при
    полностью зелёном снимке. На `trends.html` такой вход ровно один.
    """
    values = tab_case["before"]["by_attr"]
    assert all(values), (
        f"{tab_case['page']}: пустой {tab_case['data_attr']} у части вкладок: "
        f"{values}")
    assert len(values) == tab_case["n_tabs"], (
        f"{tab_case['page']}: {tab_case['data_attr']} прочитан у "
        f"{len(values)} кнопок из {tab_case['n_tabs']}")


# ── 1 проверка на движок = 2 ──

def test_selector_by_data_attribute_counts(engine_only):
    """Селектор по атрибуту находит ровно нужное число кнопок.

    На обеих страницах сразу: атрибут — это то, чем обработчик различает
    вкладки, и его поломка выглядит как «кнопки есть, но ничего не
    происходит». Проверяется на каждом движке, потому что разбор
    атрибутов у WebKit и Chromium — независимый код.
    """
    _check_server()
    browser = engine_only["browser"]
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    try:
        for page_name, _s, data_attr, _f, _sec, _n, n_by_attr in PAGES:
            page.goto(f"{BASE_URL}/{page_name}.html", wait_until="load")
            page.wait_for_timeout(300)
            got = len(page.query_selector_all("[" + data_attr + "]"))
            assert got == n_by_attr, (
                f"{page_name} / {engine_only['engine']}: селектор "
                f"[{data_attr}] нашёл {got} кнопок, ожидалось {n_by_attr}")
    finally:
        ctx.close()
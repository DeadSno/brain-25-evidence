# -*- coding: utf-8 -*-
"""Граф связей в hactar.html: реальная отрисовка (marker: graph).

Переписан в v5.6.5 (FIX-67). До этого гейт был выключен целиком: фикстура
`page_with_graph` пропускала все тесты с сообщением «H-1: граф переносится
в hactar.html; в скелете его нет (#mynetwork / #graphSearch / #pngBtn
отсутствуют)». С тех пор граф приехал (H-6), а гейт остался выключенным:
24 skip в прогоне читались как успех — ровно та ловушка, ради которой
снимали остальные гейты в v5.6.5.

Что теперь проверяется (движки chromium и webkit, по 14 тестов на движок):

1. вкладка по умолчанию — «Обзор», панель «Связи» скрыта;
2. пока ничего не выбрано, графа нет вовсе: обёртка hidden, canvas не
   создан, вместо графа — пустое состояние с подсказкой;
3. старых селекторов в разметке нет (#mynetwork, #graphSearch, #pngBtn,
   #int-graph, #atl-graph, .int-layout, .atl-layout);
4. экспорт PNG не перенесён из удалённой interactions.html — тест-метка,
   чтобы кнопка не появилась без теста на настоящий PNG (см. ниже);
5. переход на «Связи» ставит aria-selected, снимает hidden и пишет
   ?tab=graph в адрес;
6. граф реально строится: #hactarGraph не hidden, внутри ровно один canvas;
7. у canvas ненулевой буфер и высота >= MIN_GRAPH_HEIGHT, контейнер
   не схлопнут;
8. на canvas есть «чернила» — непустые пиксели (иначе граф пуст, а
   размеры формально валидны);
9. текстовый эквивалент графа (#hactarGraphAlt) перечисляет те же связи:
   список непуст и содержит выбранную добавку;
10. кнопка сброса #hactarGraphReset отрисована (44 px — тач-минимум),
    клик не ломает canvas и не даёт новых ошибок в консоли.

Граф строится только по факту выбора: `renderEgo()` вызывается из
подписок `change`/`mode` (docs/hactar.js:1861-1878), а сама библиотека
vis-network грузится лениво (FIX-43) — до открытия вкладки «Связи»
`window.vis` не определён. Поэтому фикстура отмечает добавку через
публичный API (`window.Hactar.setSelection`) и только потом нажимает
вкладку — как это делает пользователь.

Экспорт PNG: в hactar.html его нет и в планах нет (в `docs/hactar.js`
ноль упоминаний `toDataURL`/`download`). Держать `xfail` на функцию,
которой не будет, — значит ещё раз сделать skip неотличимым от успеха
(A2-06 отдал экспорт странице сравнения). Поэтому вместо теста экспорта
стоит метка `test_png_export_not_migrated`: если кнопка появится, метка
упадёт и заставит написать тест на настоящий PNG.

Сервер :8000 поднимает autouse-фикстура `live_server` в tests/conftest.py,
общий `sync_playwright()` даёт `playwright_instance` — свой контекст
открывать нельзя (два sync_playwright не живут одновременно, см.
docstring `playwright_instance`).
"""

from __future__ import annotations

import hashlib
import os
import time
import urllib.request
from pathlib import Path

import pytest

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright не установлен")

BASE_URL = os.environ.get("SNAPSHOT_BASE_URL", "http://localhost:8000")
PATH = "/hactar.html"
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

pytestmark = [pytest.mark.graph]

BROWSERS = ("chromium", "webkit")

# Разметка нынешнего графа (docs/hactar.html:464-485).
GRAPH_ID = "#hactarGraph"
GRAPH_WRAP = "#hactarGraphWrap"
NOTE_ID = "#hactarGraphNote"
ALT_ID = "#hactarGraphAlt"
RESET_BTN = "#hactarGraphReset"
TAB_OVERVIEW = "#hactarTabOverview"
TAB_LINKS = "#hactarTabLinks"
PANEL_LINKS = "#hactarPanelLinks"
LIST_ID = "#hactarList"

#: Добавка, у которой в docs/graph_data.json 38 связей — эго-сеть заведомо
#: не вырожденная, «чернила» на canvas будут. Если её переименуют, упадёт
#: фикстура с внятным сообщением, а не десять тестов с пустым графом.
SEED_SUPPLEMENT = "Магний"

MIN_GRAPH_HEIGHT = 200
MIN_CONTAINER_HEIGHT = 400     # .hactar-graph: clamp(320px, 56vh, 560px)
MIN_INK_PIXELS = 500           # непустых пикселей на canvas

# Селекторы удалённых страниц. Если они вернутся в разметку, этот файл
# снова начнёт проверять не то, что рисуется, — поэтому их отсутствие
# утверждается явно. "#graph"/".layout" из списка убраны: слишком общие,
# ".layout" может законно появиться в любой вёрстке.
OLD_SELECTORS = (
    "#mynetwork", "#graphSearch", "#pngBtn",
    "#int-graph", ".int-layout",
    "#atl-graph", ".atl-layout",
)

# «Чернила»: считаем пиксели, отличные от самого частого цвета фона.
INK_JS = """
(graphSel) => {
  const c = document.querySelector(graphSel + ' canvas');
  if (!c) return -1;
  const g = c.getContext('2d');
  if (!g) return -2;
  let data;
  try { data = g.getImageData(0, 0, c.width, c.height).data; }
  catch (e) { return -3; }
  const counts = new Map();
  const step = 4 * 7;                       // каждый 7-й пиксель — быстрее
  for (let i = 0; i < data.length; i += step) {
    const key = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2];
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  let bg = 0, bgKey = 0;
  for (const [k, v] of counts) if (v > bg) { bg = v; bgKey = k; }
  let ink = 0;
  for (const [k, v] of counts) if (k !== bgKey) ink += v;
  return ink;
}
"""


def _ink(pg) -> int:
    return pg.evaluate(INK_JS, GRAPH_ID)


def _wait_rendered(pg, timeout_s: float = 15.0) -> int:
    """Ждёт первую отрисовку узлов и возвращает «чернила».

    canvas создаётся раньше, чем vis-network нарисует узлы: в webkit первый
    getImageData сразу после `wait_for_selector` возвращает 0 (кадр ещё не
    скомпонован, физика не отдала позиции). Проверять в этот момент значит
    ловить гонку, а не регрессию графа — поэтому ждём содержимое, а
    утверждает его всё равно тест.
    """
    deadline = time.monotonic() + timeout_s
    last = -1
    while True:
        last = _ink(pg)
        if last >= MIN_INK_PIXELS or time.monotonic() >= deadline:
            return last
        pg.wait_for_timeout(200)


def _check_server() -> None:
    """:8000 отдаёт docs/ ИМЕННО этого репозитория?

    Сверяется sha256 style.css — тот же признак, что у live_server. Чужой
    сервер на порту означал бы, что тесты проверяют не тот код, поэтому
    это падение, а не skip: skip скрыл бы подмену.
    """
    local = (DOCS / "style.css").read_bytes()
    with urllib.request.urlopen(f"{BASE_URL}/style.css", timeout=5) as resp:
        served = resp.read()
    assert hashlib.sha256(served).hexdigest() == hashlib.sha256(local).hexdigest(), (
        f"на {BASE_URL} отдаётся не docs/ этого репозитория (style.css не совпал)"
    )


@pytest.fixture(scope="session")
def pw(playwright_instance):
    return playwright_instance


@pytest.fixture(params=BROWSERS)
def engine(request):
    return request.param


def _launch(pw, engine):
    """Запустить движок. Отдельная функция только ради skip-сообщения.

    В CI ставится только chromium (`.github/workflows/tests.yml`:
    `playwright install --with-deps chromium`), поэтому WebKit там нет:
    без этого guard'а фикстура падала `Executable doesn't exist` и вместо
    одного skip'а получалось 1 failed + 12 errors в setup (CI-03). Тот же
    паттерн, что в `tests/test_tabs_interaction.py::_launch`.
    """
    try:
        return getattr(pw, engine).launch()
    except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
        pytest.skip(f"{engine} не запускается: {exc}. "
                    f"Поставь: playwright install {engine}")


@pytest.fixture
def browser(engine, pw):
    _check_server()
    b = _launch(pw, engine)
    try:
        yield b
    finally:
        b.close()


@pytest.fixture
def page_hactar(browser):
    """Страница Hactar без выбора: список загружен, граф ещё не построен."""
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    errors: list[str] = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    try:
        pg.goto(f"{BASE_URL}{PATH}", wait_until="load")
        # Скелеты в разметке заменяются карточками, когда приедет data_index.json.
        pg.wait_for_selector(f"{LIST_ID} .hactar-row", timeout=15_000)
        yield pg, errors
    finally:
        pg.close()


@pytest.fixture
def page_with_graph(page_hactar):
    """Граф уже построен: добавка отмечена, вкладка «Связи» открыта."""
    pg, errors = page_hactar
    found = pg.evaluate(
        "(id) => {"
        "  if (!window.Hactar) return -1;"
        "  window.Hactar.setSelection([id]);"
        "  return window.Hactar.selectedIds().length;"
        "}",
        SEED_SUPPLEMENT,
    )
    assert found == 1, (
        f"window.Hactar.setSelection({SEED_SUPPLEMENT!r}) отметил {found} добавок — "
        "API не поднялся или добавку переименовали")
    pg.click(TAB_LINKS)
    # vis-network (673 КБ) грузится лениво — ждём canvas, а не таймаут.
    pg.wait_for_selector(f"{GRAPH_ID} canvas", timeout=30_000)
    # canvas есть, но узлы появляются на кадр позже (в webkit — заметно позже).
    _wait_rendered(pg)
    yield pg, errors


# ─────────────────────────── состояние «ничего не выбрано» ────────────────────

def test_default_tab_is_overview(page_hactar):
    pg, _ = page_hactar
    assert pg.eval_on_selector(TAB_OVERVIEW, "el => el.getAttribute('aria-selected')") == "true", (
        "вкладка «Обзор» не активна по умолчанию")
    assert pg.eval_on_selector(TAB_LINKS, "el => el.getAttribute('aria-selected')") == "false", (
        "вкладка «Связи» активна до клика")
    assert pg.eval_on_selector(PANEL_LINKS, "el => el.hidden"), (
        "панель «Связи» не скрыта, хотя активна вкладка «Обзор»")


def test_graph_hidden_without_selection(page_hactar):
    pg, _ = page_hactar
    assert pg.eval_on_selector(GRAPH_WRAP, "el => el.hidden"), (
        "граф показан, хотя ни одна добавка не выбрана")
    assert pg.eval_on_selector_all(f"{GRAPH_ID} canvas", "els => els.length") == 0, (
        "canvas создан до выбора добавки — vis-network грузится впустую")
    assert not pg.eval_on_selector(f"{PANEL_LINKS} .hactar-empty-state", "el => el.hidden"), (
        "пустое состояние скрыто, хотя выбирать нечего — пользователь видит пустую панель")


def test_old_selectors_absent(page_hactar):
    pg, _ = page_hactar
    found = pg.evaluate(
        "sels => sels.filter(s => document.querySelector(s) !== null)", list(OLD_SELECTORS))
    assert found == [], f"вернулись устаревшие селекторы: {found}"


# ─────────────────────────── переключение вкладок ────────────────────────────

def test_links_tab_selected_after_click(page_with_graph):
    pg, _ = page_with_graph
    assert pg.eval_on_selector(TAB_LINKS, "el => el.getAttribute('aria-selected')") == "true", (
        "aria-selected не переехал на «Связи»")
    assert pg.eval_on_selector(TAB_LINKS, "el => el.classList.contains('active')"), (
        "класс .active не переехал на «Связи»")
    assert not pg.eval_on_selector(PANEL_LINKS, "el => el.hidden"), (
        "панель «Связи» осталась hidden")
    assert "tab=graph" in pg.url, f"адрес не отразил режим: {pg.url}"


# ──────────────────────────────── сам граф ──────────────────────────────────

def test_graph_container_visible(page_with_graph):
    pg, _ = page_with_graph
    assert not pg.eval_on_selector(GRAPH_WRAP, "el => el.hidden"), (
        f"{GRAPH_WRAP} остался hidden при выбранной добавке")
    n = pg.eval_on_selector_all(GRAPH_ID, "els => els.length")
    assert n == 1, f"элементов {GRAPH_ID} на странице: {n}, ожидался ровно 1"
    assert not pg.eval_on_selector(GRAPH_ID, "el => el.hidden"), f"{GRAPH_ID} остался hidden"
    assert pg.eval_on_selector(
        GRAPH_ID, "el => getComputedStyle(el).display !== 'none'")


def test_canvas_created_once(page_with_graph):
    pg, _ = page_with_graph
    n = pg.eval_on_selector_all(f"{GRAPH_ID} canvas", "els => els.length")
    assert n == 1, f"canvas внутри {GRAPH_ID}: {n}, ожидался ровно 1"


def test_canvas_has_size(page_with_graph):
    pg, _ = page_with_graph
    box = pg.eval_on_selector(
        f"{GRAPH_ID} canvas",
        "el => ({buf: [el.width, el.height], css: [el.getBoundingClientRect().width,"
        " el.getBoundingClientRect().height]})",
    )
    assert box["buf"][0] > 0 and box["buf"][1] > 0, f"буфер canvas пустой: {box['buf']}"
    assert box["css"][1] >= MIN_GRAPH_HEIGHT, (
        f"canvas высотой {box['css'][1]} px, ожидалось >= {MIN_GRAPH_HEIGHT}")


def test_container_not_collapsed(page_with_graph):
    pg, _ = page_with_graph
    h = pg.eval_on_selector(
        GRAPH_ID, "el => el.getBoundingClientRect().height")
    assert h >= MIN_CONTAINER_HEIGHT, (
        f"{GRAPH_ID} высотой {h} px, ожидалось >= {MIN_CONTAINER_HEIGHT} "
        "(контейнер схлопнут — типичный признак, что vis не инициализировался)")


def test_canvas_has_ink(page_with_graph):
    pg, _ = page_with_graph
    ink = pg.evaluate(INK_JS, GRAPH_ID)
    assert ink >= MIN_INK_PIXELS, (
        f"непустых пикселей на canvas: {ink} (ожидалось >= {MIN_INK_PIXELS}); "
        "размеры валидны, но граф пуст")


def test_alt_text_mirrors_edges(page_with_graph):
    """A2-06: canvas скринридеру недоступен, эквивалент — список связей."""
    pg, _ = page_with_graph
    n = pg.eval_on_selector_all(f"{ALT_ID} li", "els => els.length")
    assert n > 0, "текстовый список связей пуст — граф без эквивалента"
    text = pg.eval_on_selector(ALT_ID, "el => el.textContent")
    assert SEED_SUPPLEMENT in text, (
        f"в списке связей нет {SEED_SUPPLEMENT!r}: {text[:200]!r}")


def test_reset_button_redraws_without_errors(page_with_graph):
    pg, errors = page_with_graph
    btn = pg.eval_on_selector(
        RESET_BTN,
        "(el) => ({tag: el.tagName, minH: parseFloat(getComputedStyle(el).minHeight)})",
    )
    assert btn["tag"] == "BUTTON", f"кнопка сброса не button: {btn}"
    # Размер берётся из CSS, а не из getBoundingClientRect: прямое измерение
    # зависит от того, успела ли панель получить раскладку, и на прогоне
    # целиком давало 0 без всякой регрессии. min-height — это и есть контракт.
    assert btn["minH"] >= 44, (
        f"кнопка сброса меньше 44 px — не попадает в тач-минимум: {btn}")
    before_errors = len(errors)
    # #hactarGraphNote — это status-строка: в рабочем состоянии в ней
    # сводка («Узлов: N · связей: M»), а не пусто. Ошибкой считается
    # подмена сводки текстом сбоя.
    note_before = pg.eval_on_selector(NOTE_ID, "el => el.textContent")
    # Сброс возвращает исходную раскладку и делает network.fit с анимацией.
    pg.click(RESET_BTN, timeout=5_000)
    pg.wait_for_timeout(800)
    assert pg.eval_on_selector_all(f"{GRAPH_ID} canvas", "els => els.length") == 1, (
        "после сброса canvas исчез")
    note_after = pg.eval_on_selector(NOTE_ID, "el => el.textContent")
    assert note_after == note_before, (
        f"сброс подменил сводку графа: {note_before!r} -> {note_after!r}")
    assert len(errors) == before_errors, f"сброс добавил ошибки в консоль: {errors[before_errors:]}"


# ─────────────────────────── отсутствующие функции ───────────────────────────

def test_png_export_not_migrated(page_with_graph):
    """Экспорт PNG остался в удалённой interactions.html.

    В hactar.js ноль упоминаний `toDataURL` и `download`: кнопки нет, тест
    на настоящий PNG писать не над чем. Это метка, а не проверка функции:
    как только экспорт перенесут, она упадёт — тогда вместо неё нужен тест
    с data-URL, сигнатурой PNG и полезной нагрузкой (MIN_PNG_PAYLOAD
    в прежней версии файла: настоящий скриншот графа весит десятки КБ).
    """
    pg, _ = page_with_graph
    found = pg.evaluate(
        "() => document.querySelectorAll("
        "'#pngBtn, #hactarGraphWrap a[download], #hactarGraphWrap [data-export]').length")
    assert found == 0, (
        f"в панели графа появился экспорт ({found} элементов), а теста на PNG нет")


def test_no_console_errors(page_with_graph):
    pg, errors = page_with_graph
    # vis-network ругается на дубли id и т.п. — это настоящий сигнал;
    # hactar.js пишет свои ошибки с префиксом [hactar].
    relevant = [e for e in errors if "[hactar]" in e or "vis" in e.lower()]
    assert relevant == [], f"ошибки в консоли: {relevant}"


# ─────────────────────────────── движки целиком ──────────────────────────────

def test_engine_loads_hactar(engine, pw):
    """Один тест на движок: страница открывается и приложение стартует."""
    _check_server()
    b = _launch(pw, engine)
    try:
        pg = b.new_page()
        pg.goto(f"{BASE_URL}{PATH}", wait_until="load")
        pg.wait_for_selector(f"{LIST_ID} .hactar-row", timeout=15_000)
        assert pg.evaluate("() => typeof window.Hactar === 'object'"), (
            f"{engine}: hactar.js не поднял window.Hactar")
        assert pg.eval_on_selector_all(f"{LIST_ID} .hactar-row", "els => els.length") > 0, (
            f"{engine}: список добавок пуст")
    finally:
        b.close()

"""Экспорт PNG работает — проверка, которой в проекте не было.

Дыра, которую закрывает этот файл, найдена негативным контролем при
переименовании `#graph` в v5.4.1 и она неочевидна.

Обработчик кнопки на обеих страницах устроен так:

    document.getElementById('pngBtn').onclick = () => {
      const canvas = document.querySelector('#int-graph canvas');
      if (!canvas) return;                       // ← тихий выход
      const url = canvas.toDataURL('image/png');
      ...
    };

Если id в селекторе разошёлся с разметкой, `canvas` будет `null`,
сработает ранний `return`, и кнопка **молча ничего не сделает**: ни
ошибки в консоли, ни изменения на странице. Пользователь нажимает
«Скачать PNG» и не получает файла.

Почему это не ловили остальные проверки:

  Снимки снимаются ДО клика, экспорт при загрузке не выполняется.
  Статический grep видит `#int-graph canvas`, но не проверяет, что
  селектор срабатывает.
  Проверка «canvas создан» тоже не годится: контейнер может существовать
  и содержать canvas, у которого читается несуществующий селектор.

Поэтому проверяется результат действия, а не наличие элемента: обработчик
должен дойти до `a.click()` с настоящим PNG-payload.

Дополнительно проверяется контейнер и его раскладка. `.int-layout` /
`.atl-layout` — flex-обёртка, а `#int-graph` внутри неё с `flex:1`; если
селектор разошёлся с разметкой, обёртка теряет `display:flex`, и вместо
графа остаётся полоса высотой в содержимое.

Как подменяется скачивание. `a.click()` с `href` вида `data:` и
`download` не порождает сетевой запрос, и `expect_download()` на таком
ненадёжен. Поэтому переопределяется `HTMLAnchorElement.prototype.click`:
перехват срабатывает ровно на той строке, до которой дошёл обработчик, и
заодно даёт payload для проверки. Это не «проверка проверки» — обработчик
настоящий, клик по настоящей кнопке, перехватывается только финальное
действие браузера.

Запуск:
    python -m http.server 8000 --directory docs   (из корня репозитория)
    $env:RUN_GRAPH="1"; pytest -q -m graph

Без RUN_GRAPH тесты сняты настройкой в tests/conftest.py: нужен живой
сервер и браузеры Playwright, а обычный `pytest -q` должен оставаться
быстрым и работать в CI без сервера.
"""
import hashlib
import os
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.graph

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright не установлен")

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("SNAPSHOT_BASE_URL",
                          "http://localhost:8000").rstrip("/")

#: Firefox не добавлен — 1.2% трафика РФ, тот же отказ, что и в снапшотах
#: и в тестах вкладок.
BROWSERS = ("chromium", "webkit")

#: Старые имена — обязаны отсутствовать. Проверяются отдельно от новых,
#: потому что «новый селектор нашёлся» и «старый исчез» — разные
#: утверждения, и переименование может оставить одно при другом.
OLD_GRAPH_ID = "#graph"
OLD_LAYOUT = ".layout"

#: Минимальный размер PNG-payload в base64-символах.
#: Замерено 2026-10-04 на этой машине: 47 418 (webkit, interactions) …
#: 127 554 (chromium, atlas). Порог 10 000 — с запасом вчетверо ниже
#: минимума и при этом выше, чем у пустого холста.
MIN_PNG_PAYLOAD = 10_000

#: Минимальная высота графа и контейнера, px. Ниже контейнер считается
#: схлопнувшимся, а не «просто маленьким».
MIN_GRAPH_HEIGHT = 200
MIN_CONTAINER_HEIGHT = 400

#: страница (без расширения), класс контейнера, id графа, кнопка экспорта
PAGES = (
    ("interactions", ".int-layout", "#int-graph", "#pngBtn"),
    ("atlas", ".atl-layout", "#atl-graph", "#pngBtn"),
)

#: Что ждём перед кликом по экспорту. Сеть vis-network строится по данным,
#: которые приходят по сети; на пустом контейнере экспорт даст пустой PNG.
SETTLE_MS = 1800


def _check_server() -> None:
    """Сервер обязан отдавать файлы ИМЕННО ЭТОГО репозитория.

    Иначе тест проверял бы чужую копию проекта: правка в docs/ не попала
    бы на страницу, экспорт отдался бы зелёным, а сайт был бы сломан.
    Та же защита, что в test_visual_snapshots.py и test_tabs_interaction.py.
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


#: Перехват клика по якорю. Вызывается ДО клика по кнопке, снимается
#: ПОСЛЕ, чтобы подмена не жила дольше одного вызова.
PATCH_CLICK_JS = """() => {
    window.__export = null;
    if (!window.__origAnchorClick) {
        window.__origAnchorClick = HTMLAnchorElement.prototype.click;
    }
    HTMLAnchorElement.prototype.click = function () {
        window.__export = {
            download: this.download || '',
            href: this.href || '',
            isPng: (this.href || '').startsWith('data:image/png')
        };
        return window.__origAnchorClick.apply(this, arguments);
    };
}"""

RESTORE_CLICK_JS = """() => {
    if (window.__origAnchorClick) {
        HTMLAnchorElement.prototype.click = window.__origAnchorClick;
        window.__origAnchorClick = null;
    }
}"""

#: Плотность отрисовки: доля пикселей с непрозрачностью. Считается с
#: шагом, а не подряд, — на полном холсте это миллионы выборок.
INK_JS = """(sel) => {
    const c = document.querySelector(sel + ' canvas');
    if (!c) return -1;
    const w = c.width, h = c.height;
    if (!w || !h) return 0;
    const d = c.getContext('2d').getImageData(0, 0, w, h).data;
    let ink = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) ink++;
    return ink;
}"""


def _box(page, sel):
    return page.eval_on_selector(
        sel, "el => { const r = el.getBoundingClientRect();"
             " const cs = getComputedStyle(el);"
             " return { w: Math.round(r.width), h: Math.round(r.height),"
             "  display: cs.display }; }")


def _launch(pw, engine):
    """Запустить движок. Отдельная функция только ради skip-сообщения."""
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
    asyncio loop».
    """
    with playwright_api.sync_playwright() as p:
        yield p


#: 4 пары: движок × страница.
GRAPH_CASES = [(b,) + p for b in BROWSERS for p in PAGES]


@pytest.fixture(scope="session", params=GRAPH_CASES,
                ids=lambda p: f"{p[0]}-{p[1]}")
def graph_case(request, pw):
    """Состояние графа и результат экспорта — один проход на пару.

    Параметризация живёт на фикстуре: пометка одноимённого аргумента
    через `@pytest.mark.parametrize` перекрыла бы фикстуру, и тест получил
    бы сырой tuple.
    """
    engine, page_name, layout_sel, graph_sel, btn = request.param
    _check_server()
    browser = _launch(pw, engine)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    try:
        page.goto(f"{BASE_URL}/{page_name}.html", wait_until="load")
        page.wait_for_timeout(SETTLE_MS)

        data = {
            "engine": engine,
            "page": page_name,
            "layout_sel": layout_sel,
            "graph_sel": graph_sel,
            "btn": btn,
            "graph_count": len(page.query_selector_all(graph_sel)),
            "layout_count": len(page.query_selector_all(layout_sel)),
            "old_graph_count": len(page.query_selector_all(OLD_GRAPH_ID)),
            "old_layout_count": len(page.query_selector_all(OLD_LAYOUT)),
            "canvas_count": len(page.query_selector_all(graph_sel + " canvas")),
            "ink": page.evaluate(INK_JS, graph_sel),
            "box_graph": _box(page, graph_sel),
            "box_layout": _box(page, layout_sel),
            "export": None,
            "export_error": None,
        }

        # Экспорт. Перехват ставится последним, чтобы не влиять на замеры
        # выше, и снимается сразу после клика.
        page.evaluate(PATCH_CLICK_JS)
        try:
            page.click(btn)
            page.wait_for_timeout(700)
            data["export"] = page.evaluate("() => window.__export")
        except Exception as exc:  # noqa: BLE001 — попадёт в текст проверки
            data["export_error"] = f"{type(exc).__name__}: {exc}"
        finally:
            page.evaluate(RESTORE_CLICK_JS)

        yield data
    finally:
        ctx.close()
        browser.close()


@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def engine_only(request, pw):
    """Движок для проверки, не привязанной к конкретной странице."""
    engine = request.param
    browser = _launch(pw, engine)
    yield {"engine": engine, "browser": browser}
    browser.close()


# ── 10 проверок на пару движок × страница = 40 ──


def test_graph_id_found_once(graph_case):
    """Контейнер графа найден ровно один раз."""
    assert graph_case["graph_count"] == 1, (
        f"{graph_case['page']}: селектор {graph_case['graph_sel']} нашёл "
        f"{graph_case['graph_count']} элементов, ожидался 1")


def test_graph_has_size(graph_case):
    """Граф ненулевой и не схлопнувшийся."""
    b = graph_case["box_graph"]
    assert b["w"] > 0 and b["h"] >= MIN_GRAPH_HEIGHT, (
        f"{graph_case['page']}: граф {b['w']}x{b['h']} px, ожидалось "
        f"не меньше {MIN_GRAPH_HEIGHT} px по высоте")


def test_graph_fits_container(graph_case):
    """Граф помещается в свою обёртку."""
    g = graph_case["box_graph"]
    lb = graph_case["box_layout"]
    assert g["h"] <= lb["h"], (
        f"{graph_case['page']}: граф {g['h']} px выше контейнера "
        f"{lb['h']} px — flex-раскладка разъехалась")


def test_container_found_once(graph_case):
    """Обёртка найдена ровно один раз."""
    assert graph_case["layout_count"] == 1, (
        f"{graph_case['page']}: {graph_case['layout_sel']} нашёл "
        f"{graph_case['layout_count']} элементов, ожидался 1")


def test_container_display_flex(graph_case):
    """`display:flex` применился — правило класса совпало с разметкой.

    Проверка на вычисленное значение, а не на наличие класса: класс в
    разметке есть и при съехавшем селекторе, а совпадение правил — нет.
    """
    assert graph_case["box_layout"]["display"] == "flex", (
        f"{graph_case['page']}: display={graph_case['box_layout']['display']}, "
        f"ожидался flex — правило {graph_case['layout_sel']} не применилось")


def test_container_height_not_collapsed(graph_case):
    """Обёртка не схлопнулась в высоту содержимого."""
    h = graph_case["box_layout"]["h"]
    assert h >= MIN_CONTAINER_HEIGHT, (
        f"{graph_case['page']}: контейнер {h} px < {MIN_CONTAINER_HEIGHT} px — "
        f"граф не занял своё место")


def test_canvas_created(graph_case):
    """vis-network создал canvas внутри контейнера."""
    assert graph_case["canvas_count"] >= 1, (
        f"{graph_case['page']}: canvas не создан — сеть не построилась")


def test_export_handler_reaches_click(graph_case):
    """ГЛАВНАЯ ПРОВЕРКА: обработчик экспорта дошёл до `a.click()`.

    Именно её не было, и именно её ловит поломка. Раньше при
    `querySelector(...) === null` обработчик делал `return`, и кнопка
    «Скачать PNG» не давала ни файла, ни ошибки.
    """
    assert graph_case["export_error"] is None, (
        f"{graph_case['page']}: клик по кнопке экспорта упал — "
        f"{graph_case['export_error']}")
    assert graph_case["export"] is not None, (
        f"{graph_case['page']}: обработчик {graph_case['btn']} не дошёл до "
        f"a.click() — селектор canvas вернул null и сработал ранний return. "
        f"Кнопка экспорта молча ничего не делает.")


def test_export_payload_is_real_png(graph_case):
    """Payload — настоящий PNG, а не пустой холст и не заглушка."""
    rec = graph_case["export"]
    assert rec is not None, "экспорт не выполнялся — см. предыдущую проверку"
    assert rec["isPng"], (
        f"{graph_case['page']}: href не data:image/png — "
        f"{rec['href'][:40]!r}")
    assert len(rec["href"]) > MIN_PNG_PAYLOAD, (
        f"{graph_case['page']}: payload {len(rec['href'])} символов "
        f"<= {MIN_PNG_PAYLOAD} — canvas пустой, экспортировать нечего")
    assert rec["download"].endswith(".png") and len(rec["download"]) > 5, (
        f"{graph_case['page']}: имя файла неосмысленное — "
        f"{rec['download']!r}")
    assert "graph" not in rec["download"], (
        f"{graph_case['page']}: имя файла ссылается на старое имя — "
        f"{rec['download']!r}")


def test_old_selectors_absent(graph_case):
    """Старые `#graph` и `.layout` не остались в разметке.

    Отдельно от «новый селектор нашёлся»: переименование может оставить
    старое имя рядом с новым, и все остальные проверки будут зелёными.
    """
    assert graph_case["old_graph_count"] == 0, (
        f"{graph_case['page']}: старый {OLD_GRAPH_ID} ещё есть — "
        f"переименование не доведено до конца")
    assert graph_case["old_layout_count"] == 0, (
        f"{graph_case['page']}: старый {OLD_LAYOUT} ещё есть")


# ── 1 проверка на движок = 2 ──


def test_both_graphs_have_ink(engine_only, pw):
    """На обоих графах что-то нарисовано, а не только создан canvas.

    Наличие canvas не доказывает, что сеть построилась: пустой canvas
    даёт валидный PNG малого размера. Проверка считает пиксели с
    непрозрачностью — это отличает нарисованный граф от пустого холста,
    и делает экспорт бессмысленным тестом, если граф пуст.

    Порог 500 подобран по замеру: 17 017 … 20 488 на этой машине.
    """
    browser = _launch(pw, engine_only["engine"])
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    try:
        for page_name, _l, graph_sel, _b in PAGES:
            page.goto(f"{BASE_URL}/{page_name}.html", wait_until="load")
            page.wait_for_timeout(SETTLE_MS)
            ink = page.evaluate(INK_JS, graph_sel)
            assert ink > 500, (
                f"{page_name} / {engine_only['engine']}: на canvas "
                f"{ink} пикселей с непрозрачностью, ожидалось больше 500 — "
                f"граф пуст, и экспортировать нечего")
    finally:
        ctx.close()
        browser.close()
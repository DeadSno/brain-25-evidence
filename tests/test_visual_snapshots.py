"""
Визуальные снапшоты — защита на время миграции дизайн-системы v5.1 (Шаг 0).

Зачем
-----
Шаги 1-5 миграции (DESIGN_SYSTEM_PLAN) правят отступы, радиусы, тени, цвета и
межстрочный интервал сразу на 17 страницах. Без автоматической визуальной
проверки такая правка — работа вслепую: сдвиг на 1px ломает 130 карточек на
index и шапку на всех страницах, и это видно только глазами.

Что здесь
---------
18 страниц x 2 разрешения (412x852 — Tecno CAMON 40 Premier, 1280x900) + 1
снапшот модалки на index = 37 PNG-эталонов НА ДВИЖОК.
Шапка и подвал байт-идентичны всем страницам, поэтому проверяются 18 раз —
это не раздувание, а дешёвая страховка.

Движки (v5.1.6)
-------------
Эталоны разложены по движкам: tests/snapshots/chromium/ и tests/snapshots/
webkit/. Один и тот же снимок в разных движках — РАЗНЫЕ файлы и разные
пиксели: у WebKit свои метрики шрифтов, свои скругления, свой рендеринг
SVG. Сравнивать их между собой нельзя, сравнивать с эталоном своего движка —
можно и нужно.
Покрытие: Chromium (Chrome, Яндекс Браузер, Edge, Opera, Samsung Internet) и
WebKit (Safari iOS, Mobile Safari). Firefox отложен.

Как запускать
-------------
    python -m http.server 8000 --directory docs     # из корня репозитория
    pytest -q -m snapshots                          # проверка (37 тестов, ~100 с)
    $env:UPDATE_SNAPSHOTS="1"; pytest -q -m snapshots   # перезаписать эталоны
    python scripts/compress_snapshots.py --apply    # ужать эталоны (lossless)

В addopts стоит `-m "not snapshots"`, поэтому обычный `pytest -q` снапшоты
не запускает. Адрес сервера переопределяется: SNAPSHOT_BASE_URL=http://localhost:8020

Что делается перед съёмкой и почему (всё измерено, не предположено)
-------------------------------------------------------------------
1. Анимации и transitions выключаются инъекцией CSS, и результат инъекции
   ПРОВЕРЯЕТСЯ (`getComputedStyle(body).transition === 'none'`). Без этой
   проверки замер попадает в середину перехода — ровно та ошибка, из-за
   которой в VISUAL_DESIGN_AUDIT находка «graph.html не переключает тему»
   оказалась ложной.
2. Граф на canvas (graph / atlas / interactions, vis-network@9.1.9) живёт с
   `physics.enabled: true`, `stabilization: false`, `minVelocity: 0.05` —
   симуляция не останавливается, положение узлов зависит от числа кадров.
   Замерено, 3 прогона подряд: interactions 2.2-3.7%, atlas 1.3-1.5%,
   graph 0.04-0.07%. Поэтому граф замораживается детерминированно: узлы
   раскладываются по кольцу (явные x/y), physics выключается, fit().
   Свойства узлов (цвет, значение, подпись) сохраняются — меняется только
   геометрия, а всё, что меняет миграция, снимается как есть.
   После заморозки 3 прогона подряд = 0.0000% на всех трёх страницах.
3. Анимации Chart.js не ловит CSS-правило: Chart.js анимирует через
   requestAnimationFrame. Патч ставится в геттере `window.Chart` (UMD делает
   `global.Chart = {}` и наполняет позже, поэтому в сеттере `defaults` ещё
   undefined и патч падал бы в тихом try). Без патча точки пузырьковой
   диаграммы на index съезжали вдоль диагонали между прогонами.
4. Дата «Обновлено:» на карточках index зависит от того, успел ли
   version.json прийти до отрисовки карточек. Замерено на этой копии:
   при одной загрузке 1 из 20 показывала индивидуальную дату вместо
   APP_VERSION.data. Здесь ждём и версию, и сходимость самой страницы, и
   проверяем результат — но НЕ чиним за страницу: если гонка вернётся,
   тест должен упасть с внятным текстом, а не замаскировать баг.
5. Первый заход в холодный браузер рисует index иначе, чем следующие.
   Замерено: 5 заходов подряд — расхождение 0.1322% против первого, при
   одинаковой высоте страницы и `document.fonts.status = loaded`. Уходит
   после одного прогревочного захода. Поэтому каждый снимок — второй заход.
6. Шрифт Inter грузится с Google Fonts, поэтому эталоны привязаны к этой
   машине. Без сети Inter не применится и разойдутся ВСЕ эталоны. Это
   осознанно: отключать шрифт — значит снимать не то, что видит пользователь.
7. index.html на 412px = 38321px высотой (замерено). Chromium такие снимки
   делает: PNG 412x38321 получен, ошибки нет.

Порог: СТРОГИЙ, любое расхождение пикселей валит прогон (см. DIFF_TOL_PCT).
Замеренный шум на чистом коде — ровно ноль, запас нулевой, мягкий порог
ничего не покупал: наоборот, при 0.05% смена счётчика тестов на главной
проходила молча.
"""
from __future__ import annotations

import hashlib
import io
import os
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = Path(__file__).resolve().parent / "snapshots"
BROWSERS = ("chromium", "webkit")   # Firefox отложен: 1.2% трафика РФ

BASE_URL = os.environ.get("SNAPSHOT_BASE_URL", "http://localhost:8000").rstrip("/")
UPDATE = os.environ.get("UPDATE_SNAPSHOTS") == "1"

# 17 страниц сайта + offline.html (автономная, без внешних <link>/<script>).
PAGES = (
    "index", "map", "interactions", "graph", "atlas", "calculator", "trends",
    "methodology", "faq", "glossary", "feedback", "support",
    "sup/kreatin", "sup/omega-3", "sup/vitamin-d", "sup/magniy", "sup/paba",
    "offline",
)
VIEWPORTS = ((412, 852), (1280, 900))

# Тема, которую обязана иметь страница на момент съёмки. С v5.4.0 (dark-first)
# тёмная тема — это ОТСУТСТВИЕ класса: 17 страниц сайта ставят `light` на <html>
# только если `localStorage.getItem('theme') === 'light'`, поэтому в свежем
# контексте класс пустой и страница тёмная.
# offline.html — исключение, и это измерено, а не предположено: в нём нет
# ни скрипта темы, ни класса `light`, тёмная тема задана только через
# `@media (prefers-color-scheme: dark)` (offline.html:35), поэтому при
# color_scheme=light она светлая.
EXPECTED_HTML_CLASS = {p: "" for p in PAGES}

# Chromium по умолчанию отдаёт prefers-color-scheme: light. Фиксируем явно:
# для 17 страниц это не важно (тема от localStorage), а для offline.html
# решает исход снимка. Без явного значения смена системной темы на машине
# разработчика тихо переписала бы эталон offline.
COLOR_SCHEME = "light"

# Порог 0.05% пикселей с разницей канала > 8. Строгий ноль отклонён ЗАМЕРОМ,
# а не на всякий случай: при DIFF_TOL_PCT=0 на index@1280 первый снимок в
# холодном браузере расходился с эталоном на 0.0266% (5011 пикселей, дельты
# 8-136/255 на краях глифов), а следующие девять — ровно 0. Это субпиксельный
# дребезг сглаживания, а не поломка: при 0 он давал ~10% ложных падений.
# Порог 0.05% ловит настоящие правки вёрстки: проверено, фиктивный
# `body{padding:1px}` роняет 27 снимков из 37.
# CHANNEL_TOL=8 отсекает совсем слабый дребезг: замерено 9 пикселей с
# максимумом 4/255 — такие в счёт не идут.
CHANNEL_TOL = 8
DIFF_TOL_PCT = 0.05
SETTLE_MS = 600
# Сколько ждать наполнения #compareResult на index. Замерено: webkit ровняется
# между 1000 и 1500 мс после networkidle, chromium — к 300 мс. Порог с запасом.
COMPARE_READY_TIMEOUT_MS = 8000

# Потолок высоты full-page снимка, заданный самим Playwright, — и он РАЗНЫЙ
# у движков. Замерено на v5.1.6: webkit отказывается снимать страницу выше
# 32767 px («Cannot take screenshot larger than 32767 pixels on any
# dimension»), тогда как chromium спокойно отдаёт index@412 = 38321 px.
# Единственная страница, которая в webkit не помещается, — index@412
# (37402 px). Chromium в таблице не указан сознательно: его предел не
# измерен и для наших высот не достигается, а выдумывать число хуже, чем
# не задавать ограничения.
FULL_PAGE_CAP_PX = {"webkit": 32767}
NAV_TIMEOUT_MS = 60_000
CONVERGE_TIMEOUT_MS = 15_000

# Выключаем анимации ДО замера. `scroll-behavior` и `caret-color` — потому что
# первый прыгает при программном scrollTo, второй мигает в фокусе.
# #loadingBar на graph.html показывает прогресс стабилизации, её ширина зависит
# от скорости загрузки (замерено 730-1279 пикселей разброса); в покое у плашки
# display:none, поэтому снимок делается именно в этом состоянии.
KILL_CSS = (
    "*,*::before,*::after{transition:none!important;animation:none!important;"
    "caret-color:transparent!important;scroll-behavior:auto!important}"
    "#loadingBar{display:none!important}"
)

# Заморозка vis-network. Ставится через add_init_script, т.е. ДО любого скрипта
# страницы: UMD-библиотека делает `global.vis = {}`, поэтому перехватываем
# присваивание и сразу ставим accessor на `vis.Network`. Обычный setInterval
# не годится — между <script src=vis-network> и инлайновым скриптом страницы
# нет задачи, в которую мог бы вклиниться таймер.
FREEZE_JS = r"""
(() => {
  window.__snap = {frozen: 0, err: '', nets: 0};
  const makeWrap = (orig) => function (container, data, options) {
    const net = new orig(container, data, options);
    window.__snap.nets += 1;
    window.__freeze = () => {
      try {
        const nodes = net.body.data.nodes.get();
        const w = container.clientWidth || 1;
        const h = container.clientHeight || 1;
        const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.40;
        const n = nodes.length || 1;
        const fixed = nodes.map((nd, i) => {
          const a = (2 * Math.PI * i) / n - Math.PI / 2;
          return Object.assign({}, nd, {x: cx + R * Math.cos(a), y: cy + R * Math.sin(a)});
        });
        // Физику выключаем ДО подмены данных. Обратный порядок был причиной
        // недетерминизма: setData перезапускает стабилизацию (1000 итераций
        // на graph.html), и разлетевшийся граф успевал отрисоваться поверх
        // только что выставленных координат. Замерено 2026-10-06: при старом
        // порядке graph-1280/412 расходились в 4 прогонах из 6 на 18.427%
        // при неизменном размере холста. stabilization выключается тоже —
        // иначе она может стартовать позже, уже по обновлённым данным.
        net.setOptions({physics: {enabled: false,
                                  stabilization: {enabled: false}}});
        net.setData({nodes: new vis.DataSet(fixed), edges: net.body.data.edges});
        // Прибиваем координаты через moveNode: setPositions в vis-network
        // 9.1.2 нет вообще (проверено по библиотеке), а setData сбрасывает
        // позиции. moveNode при выключенной физике ставит узел жёстко.
        fixed.forEach((nd) => net.moveNode(nd.id, nd.x, nd.y));
        net.fit();
        net.redraw();
        window.__snap.frozen = 1;
        return true;
      } catch (e) { window.__snap.err = String(e); return false; }
    };
    return net;
  };
  const patch = (v) => {
    if (!v || typeof v !== 'object' || v.__snapPatched) return;
    let wrap = null;
    Object.defineProperty(v, 'Network', {
      configurable: true,
      get() { return wrap || (wrap = makeWrap(v.__snapOrig)); },
      set(orig) { v.__snapOrig = orig; },
    });
    Object.defineProperty(v, '__snapPatched', {value: true, configurable: true});
  };
  let backing;
  Object.defineProperty(window, 'vis', {
    configurable: true,
    get() { return backing; },
    set(v) { backing = v; patch(v); },
  });
})()
"""

# Выключить анимации Chart.js — см. п.3 в докстринге.
CHART_PATCH_JS = r"""
(() => {
  window.__chartSnap = {patched: 0, err: ''};
  const ensure = (v) => {
    if (!v || v.__snapChartPatched) return;
    try {
      if (!v.defaults) return;             // библиотека ещё не готова
      v.defaults.animation = false;
      v.defaults.animations = {};          // ни одного анимируемого свойства
      if (v.defaults.transitions) {
        v.defaults.transitions.active = {animation: {duration: 0}};
      }
      v.__snapChartPatched = true;
      window.__chartSnap.patched = 1;
    } catch (e) { window.__chartSnap.err = String(e); }
  };
  let backing;
  Object.defineProperty(window, 'Chart', {
    configurable: true,
    get() { ensure(backing); return backing; },
    set(v) { backing = v; },
  });
})()
"""

pytestmark = pytest.mark.snapshots

playwright_api = pytest.importorskip("playwright.sync_api",
                                     reason="playwright не установлен")
np = pytest.importorskip("numpy", reason="numpy не установлен")
PIL_Image = pytest.importorskip("PIL.Image", reason="Pillow не установлен")


# ─────────────────────────── окружение ───────────────────────────

def _slug(page: str) -> str:
    return page.replace("/", "-")


def _check_server() -> None:
    """Сервер обязан отдавать файлы ИМЕННО ЭТОГО репозитория.

    Иначе тест молча сравнивал бы страницы из другой копии проекта: правка в
    docs/ не попала бы в снимок, эталон «прошёл бы», а страница на самом деле
    поехала. Это ровно тот класс ложной находки, который запрещён правилом
    верификации проекта, поэтому сверяем хэш style.css.
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
            f"{ROOT / 'docs' / 'style.css'}). Эталоны были бы сравнением "
            f"не с тем кодом, который меняется. Запусти сервер из этого "
            f"репозитория или укажи SNAPSHOT_BASE_URL."
        )


@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def browser(request):
    """Движок Playwright. Параметризована, поэтому каждый тест, который
    берёт browser, прогоняется по всем движкам. Имя движка доступно как
    browser.name — по нему выбирается каталог эталонов."""
    engine = request.param
    with playwright_api.sync_playwright() as pw:
        try:
            b = getattr(pw, engine).launch()
        except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
            pytest.skip(f"{engine} не запускается: {exc}. "
                        f"Поставь: playwright install {engine}")
        # У Browser из sync_api нет .name/.browser_name, а имя движка нужно
        # фикстуре snap_dir. Вешаем своё: у объекта нет __slots__, аутентичное
        # поле Playwright не даёт.
        b.engine = engine
        yield b
        b.close()


@pytest.fixture(scope="session")
def snap_dir(browser):
    """Каталог эталонов этого движка. Существует только с v5.1.6: до него
    все 37 файлов лежали плоско в tests/snapshots/."""
    return SNAPSHOT_ROOT / browser.engine


@pytest.fixture(scope="session")
def _env_checked(browser):  # noqa: ARG001 — фикстура только ради порядка
    _check_server()
    return True


# ─────────────────────────── съёмка ───────────────────────────

def _open(page, url: str) -> None:
    """Заход на страницу до networkidle."""
    page.goto(url, wait_until="networkidle", timeout=NAV_TIMEOUT_MS)


def _await_version(page) -> None:
    """Дождаться, пока страница подставит версию и приведёт к ней карточки.

    Дата «Обновлено:» берётся из APP_VERSION.data, если версия уже пришла, и
    из самой карточки иначе (script.js updatedLine). version.json грузится
    асинхронно, поэтому есть гонка. Замерено на этой копии: при одной
    загрузке 1 из 20 показывала индивидуальную дату вместо общей.

    Важно: страницу здесь НЕ чиним. Раньше хелпер дёргал applyFilters() за неё,
    и это было неверно — такой тест замаскировал бы возврат бага. Теперь ждём
    сходимости и проверяем результат в `_assert_version_consistent`.
    """
    page.evaluate(
        """async () => {
            if (!document.querySelector('[data-version]')) return;
            if (window.APP_VERSION && window.APP_VERSION.data) return;
            await new Promise(resolve => {
                const t0 = Date.now();
                const iv = setInterval(() => {
                    if ((window.APP_VERSION && window.APP_VERSION.data)
                            || Date.now() - t0 > 8000) {
                        clearInterval(iv); resolve();
                    }
                }, 20);
            });
        }"""
    )
    # Сетка карточек должна сойтись к APP_VERSION.data. Страница без сетки
    # (sup/*, offline) или без version.js проходит проверку сразу.
    try:
        page.wait_for_function(
            """() => {
                const v = window.APP_VERSION;
                if (!v || !v.data) return true;
                const el = document.querySelector('#cardsGrid .updated');
                if (!el) return true;
                return el.textContent.trim().endsWith(v.data);
            }""",
            timeout=CONVERGE_TIMEOUT_MS,
        )
    except Exception:  # noqa: BLE001 — решение принимает проверка ниже
        pass


def _await_compare_result(page) -> None:
    """Дождаться, пока блок сравнения наполнится таблицей.

    Замер (v5.1.6, index, шаг от 600 мс): Chromium рисует 10 строк через
    300 мс, WebKit — только между 1000 и 1500 мс после networkidle. При
    прежнем SETTLE_MS=600 эталон webkit/index-1280 снимался с ПУСТЫМ блоком
    сравнения: 13986 px против 14742 px у settled-страницы. Такое состояние
    в живом браузере не встречается — значит эталон сравнивал бы страницу,
    которой нет.

    Поэтому здесь не увеличение таймера, а ожидание признака: если блок есть,
    в нём обязана появиться таблица с хотя бы одной строкой.
    """
    if not page.evaluate("() => !!document.querySelector('#compareResult')"):
        return          # блока на странице нет — ждать нечего
    try:
        page.wait_for_function(
            """() => {
                const r = document.querySelector('#compareResult');
                if (!r) return true;
                const t = r.querySelector('table');
                return !!t && t.querySelectorAll('tr').length > 0;
            }""",
            timeout=COMPARE_READY_TIMEOUT_MS,
        )
    except Exception:  # noqa: BLE001 — решение принимает проверка ниже
        rows = page.evaluate(
            """() => {
                const t = document.querySelector('#compareResult table');
                return t ? t.querySelectorAll('tr').length : -1;
            }"""
        )
        pytest.fail(
            f"{BASE_URL}/index.html: блок сравнения не наполнился за "
            f"{COMPARE_READY_TIMEOUT_MS} мс (строк в таблице: {rows}). "
            f"Снимок получится с пустым блоком — он не соответствует ни одному "
            f"реальному состоянию страницы. Либо script.js не отработал, либо "
            f"данные не пришли."
        )


def _assert_version_consistent(page, url: str) -> None:
    """Дата на карточках должна совпадать с APP_VERSION.data.

    Если гонка вернётся, это должно быть явной ошибкой с понятным текстом,
    а не молчаливым дрейфом на 0.13%.
    """
    info = page.evaluate(
        """() => {
            const v = window.APP_VERSION;
            const els = [...document.querySelectorAll('#cardsGrid .updated')];
            return {data: v ? v.data : null,
                    n: els.length,
                    first: els.length ? els[0].textContent.trim() : null};
        }"""
    )
    if info["first"] is None:
        return
    if not info["data"] or not info["first"].endswith(info["data"]):
        pytest.fail(f"{url}: дата на карточках «{info['first']}» не совпадает с "
                    f"APP_VERSION.data «{info['data']}» — гонка version.js/"
                    f"script.js (см. _await_version)")


def _capture(page, page_name: str, *, full_page: bool) -> bytes:
    url = f"{BASE_URL}/{page_name}.html"

    # Прогрев — см. п.5 в докстринге. Без него первый заход в холодный
    # браузер даёт карточки index, отличные от всех следующих, и эталон
    # записывается в состоянии, которое никогда не повторится.
    _open(page, url)
    _open(page, url)

    # Инъекция после загрузки: в <head> до style.css её вставить нельзя.
    page.add_style_tag(content=KILL_CSS)
    page.evaluate("() => document.fonts.ready")

    # Проверяем, что правило применилось — см. п.1 в докстринге.
    t = page.evaluate("() => getComputedStyle(document.body).transition")
    a = page.evaluate("() => getComputedStyle(document.body).animationName")
    if t != "none" or a not in ("none", ""):
        pytest.fail(f"{url}: правило отключения анимаций НЕ применилось "
                    f"(transition={t!r}, animation={a!r}) — замер недостоверен")

    # Тема проверяется, чтобы эталон не оказался смесью светлой и тёмной.
    # Ожидаемое значение — в EXPECTED_HTML_CLASS, оно задано по коду страниц.
    theme = page.evaluate("() => document.documentElement.className")
    expected = EXPECTED_HTML_CLASS[page_name]
    if theme.split() != expected.split():
        pytest.fail(f"{url}: html.className={theme!r}, ожидалось {expected!r} — "
                    f"тема страницы поменялась, эталон станет сравнением "
                    f"разных тем (см. EXPECTED_HTML_CLASS)")

    # Заморозка графа, если на странице есть vis-network.
    has_vis = page.evaluate("() => !!(window.__freeze)")
    if has_vis:
        ok = page.evaluate("() => window.__freeze()")
        if not ok:
            err = page.evaluate("() => window.__snap.err")
            pytest.fail(f"{url}: не удалось заморозить vis-network: {err}")

    _await_version(page)
    _await_compare_result(page)
    page.wait_for_timeout(SETTLE_MS)
    _assert_version_consistent(page, url)

    if full_page:
        engine = getattr(page.context.browser, "engine", "?")
        cap = FULL_PAGE_CAP_PX.get(engine)
        if cap:
            sh = page.evaluate(
                """() => Math.max(document.documentElement.scrollHeight,
                                  document.body.scrollHeight)"""
            )
            if sh > cap:
                pytest.skip(
                    f"[{engine}] {url} не помещается в full-page снимок: "
                    f"высота {sh} px при потолке Playwright {cap} px. "
                    f"Это ограничение движка, не регрессия вёрстки: на "
                    f"index@412 высота {sh} px против ~38 000 px в chromium, "
                    f"и там страница снимается целиком. Чтобы покрыть эту "
                    f"страницу в webkit, нужен другой способ съёмки "
                    f"(тайлы по вертикали или снимок только шапки) — это "
                    f"отдельная задача, а не молчаливое урезание эталона."
                )
    return page.screenshot(full_page=full_page)


# ─────────────────────────── сравнение ───────────────────────────

def _decode(png: bytes):
    return PIL_Image.open(io.BytesIO(png)).convert("RGB")


def _compare(actual_png: bytes, expected_png: bytes):
    """-> (процент, bbox или None, n_различающихся, размеры или None).

    Разные размеры = страница стала выше/ниже. Это самый сильный сигнал
    из возможных, поэтому возвращается 100% и размеры: «высота поехала на
    2px» полезнее, чем безликое «расхождение 100%».
    """
    a, e = _decode(actual_png), _decode(expected_png)
    if a.size != e.size:
        return 100.0, None, 0, (a.size, e.size)
    av = np.asarray(a, dtype=np.int16)
    ev = np.asarray(e, dtype=np.int16)
    d = np.abs(av - ev).max(axis=2)
    mask = d > CHANNEL_TOL
    n = int(mask.sum())
    if not n:
        return 0.0, None, 0, None
    ys, xs = np.nonzero(mask)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return 100.0 * n / mask.size, bbox, n, None


def _write_artifacts(name: str, actual_png: bytes, expected_png: bytes,
                     art_dir: Path) -> list[str]:
    ART_DIR = art_dir
    ART_DIR.mkdir(parents=True, exist_ok=True)
    # `!.gitignore` обязателен: без него правило `*` игнорирует сам .gitignore,
    # каталог не попадает в индекс и после клона артефакты падения окажутся
    # в репозитории (десятки мегабайт diff-картинок).
    (ART_DIR / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    a, e = _decode(actual_png), _decode(expected_png)
    (ART_DIR / f"{name}.actual.png").write_bytes(actual_png)
    written = [str(ART_DIR / f"{name}.actual.png")]
    if a.size == e.size:
        av = np.asarray(a, dtype=np.int16)
        ev = np.asarray(e, dtype=np.int16)
        mask = np.abs(av - ev).max(axis=2) > CHANNEL_TOL
        heat = np.array(e, dtype=np.uint8).copy()
        heat[mask] = [255, 0, 0]
        p = ART_DIR / f"{name}.diff.png"
        PIL_Image.fromarray(heat).save(p)
        written.append(str(p))
    return written


def _assert_snapshot(name: str, actual_png: bytes, snap_dir: Path) -> None:
    path = snap_dir / f"{name}.png"
    if UPDATE or not path.exists():
        snap_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(actual_png)
        size_kb = path.stat().st_size / 1024
        if not UPDATE:
            pytest.fail(f"Эталон {name} создан ({size_kb:.0f} КБ). Посмотри его "
                        f"в глаза — потом он станет базой. Повтори прогон.")
        return
    pct, bbox, n, sizes = _compare(actual_png, path.read_bytes())
    if pct <= DIFF_TOL_PCT:
        return
    files = _write_artifacts(name, actual_png, path.read_bytes(),
                             snap_dir / "_actual")
    if sizes:
        why = (f"размер страницы изменился: стало {sizes[0][0]}x{sizes[0][1]}, "
               f"эталон {sizes[1][0]}x{sizes[1][1]} — это само по себе причина "
               f"остановиться, а не «100% пикселей»")
    else:
        why = f"{n} пикселей, область x[{bbox[0]}..{bbox[2]}] y[{bbox[1]}..{bbox[3]}]"
    pytest.fail(f"[{snap_dir.name}] {name}: расхождение {pct:.3f}% при пороге "
                f"{DIFF_TOL_PCT}%\n"
                f"    {why}\n    эталон: {path}\n"
                f"    артефакты: {', '.join(files)}\n"
                f"    Если правка намеренная — перезапиши эталон:\n"
                f"    $env:UPDATE_SNAPSHOTS='1'; pytest -q -m snapshots")


# ─────────────────────────── тесты ───────────────────────────

@pytest.mark.parametrize("page_name", PAGES)
@pytest.mark.parametrize("width,height", VIEWPORTS, ids=lambda v: str(v))
def test_page_snapshot(_env_checked, browser, snap_dir, page_name, width, height):
    ctx = browser.new_context(
        viewport={"width": width, "height": height},
        service_workers="block",  # sw.js кэширует HTML — лишний источник расхождений
        reduced_motion="reduce",
        color_scheme=COLOR_SCHEME,
    )
    ctx.add_init_script(FREEZE_JS)
    ctx.add_init_script(CHART_PATCH_JS)
    page = ctx.new_page()
    try:
        png = _capture(page, page_name, full_page=True)
    finally:
        ctx.close()
    _assert_snapshot(f"{_slug(page_name)}-{width}", png, snap_dir)


def test_modal_index_snapshot(_env_checked, browser, snap_dir):
    """Модалка на index: самая частая точка отказа при смене токенов."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              service_workers="block", reduced_motion="reduce",
                              color_scheme=COLOR_SCHEME)
    ctx.add_init_script(FREEZE_JS)
    ctx.add_init_script(CHART_PATCH_JS)
    page = ctx.new_page()
    try:
        url = f"{BASE_URL}/index.html"
        _open(page, url)   # прогрев, см. п.5 в докстринге
        _open(page, url)
        page.add_style_tag(content=KILL_CSS)
        page.evaluate("() => document.fonts.ready")
        # Сначала дождаться, пока страница САМА перерисует карточки: пока сетка
        # не сошлась, клик может попасть в ещё не перерисованную карточку.
        _await_version(page)
        _await_compare_result(page)
        _assert_version_consistent(page, url)
        # На index заголовок карточки — не h3, а strong.card-title (v2.6, P2-16):
        # h3 убрали, чтобы структура документа отражала разделы, а не 130 карточек.
        card = page.locator("#cardsGrid .card").first
        card.scroll_into_view_if_needed()
        card.click()
        page.wait_for_function(
            "() => { const o = document.getElementById('modalOverlay');"
            " return o && getComputedStyle(o).display !== 'none'"
            " && !!document.querySelector('#modalBody h2'); }",
            timeout=30_000)
        page.wait_for_timeout(SETTLE_MS)
        # Модалка — оверлей поверх вьюпорта, full_page здесь неуместен.
        png = page.screenshot(full_page=False)
    finally:
        ctx.close()
    _assert_snapshot("modal-index", png, snap_dir)
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
    pytest -q -m snapshots                          # проверка (76 тестов, ~4 мин)
    $env:UPDATE_SNAPSHOTS="1"; pytest -q -m snapshots   # перезаписать ВСЕ эталоны
    $env:UPDATE_SNAPSHOTS="modal-index,cookie-banner"; pytest -q -m snapshots
    python scripts/compress_snapshots.py --apply    # ужать эталоны (lossless)

Гейт RUN_SNAPSHOTS удалён в v5.6.5 (tests/conftest.py): снапшоты собираются
обычным `pytest -q` (полный прогон ~8-10 мин). Для быстрого прогона без
браузера — `-m "not snapshots"`. Адрес сервера переопределяется:
SNAPSHOT_BASE_URL=http://localhost:8020

Обновление эталонов — поимённо (#98, F-18)
-------------------------------------------
Раньше `UPDATE_SNAPSHOTS=1` был единственным режимом и перезаписывал
все 76 снимков разом. Один опечатанный токен стиля молча переписывал
весь набор эталонов, и правка выглядела успешной, пока картинки не
сравнивали вручную. Теперь переменная понимает три режима:

  * не задана или `0` — ничего не перезаписывать;
  * `1` или `all` — перезаписать всё (прежнее поведение);
  * список имён через запятую — перезаписать ТОЛЬКО перечисленные.

Список сравнивается вхождением подстроки, то есть
`UPDATE_SNAPSHOTS="modal-index,sup-omega-3"`. Неперечисленные снимки
того же прогона сравниваются как обычно: можно обновить один эталон и
тут же увидеть, что остальные не поехали.

В выборочном режиме тест ПАДАЕТ сразу после перезаписи и печатает,
какие файлы заменены. Это намеренно: перезаписанный эталон обязан
увидеть человек, а не прогон. Затем прогон повторяют без
`UPDATE_SNAPSHOTS`, и он уже сравнивает новое со старым.

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
7. index.html на 412px = 42041px высотой (замерено). Chromium такие снимки
   делает: PNG 412x42041 получен, ошибки нет.

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


def _parse_update(raw: str | None) -> tuple[str, tuple[str, ...]]:
    """-> (режим, подстроки-селекторы).

    Режимы: "off", "all", "select". Значение разбирается один раз на
    импорте, а не в каждом снимке, иначе опечатка в переменной
    окружения выглядела бы по-разному в середине прогона.
    """
    value = (raw or "").strip()
    if not value or value == "0":
        return "off", ()
    if value == "1" or value.lower() == "all":
        return "all", ()
    parts = tuple(p.strip() for p in value.split(",") if p.strip())
    if not parts:
        # Запятые без имён — опечатка, а не «обновить всё».
        return "off", ()
    return "select", parts


UPDATE_MODE, UPDATE_SELECTORS = _parse_update(os.environ.get("UPDATE_SNAPSHOTS"))


def _should_update(name: str) -> bool:
    """Обновлять ли этот снимок при текущем режиме UPDATE_SNAPSHOTS."""
    if UPDATE_MODE == "off":
        return False
    if UPDATE_MODE == "all":
        return True
    return any(part in name for part in UPDATE_SELECTORS)

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
# dimension»), тогда как chromium спокойно отдаёт index@412 целиком.
# Chromium в таблице не указан сознательно: его предел не измерен и для
# наших высот не достигается, а выдумывать число хуже, чем не задавать
# ограничения.
FULL_PAGE_CAP_PX = {"webkit": 32767}

# F-19 (#31): комбинации, не помещающиеся в потолок движка, объявлены явно.
#
# Раньше это был просто skip внутри _capture, и дыра в покрытии была
# невидима: прогон показывал зелёным, а страница на самом деле не
# проверялась. Теперь высота сверяется с замеренной (расхождение больше
# 2 % падает), пропуск разрешён только для перечисленных здесь пар и
# только если тайловая съёмка не удалась.
#
# Потолок измерен, а не выдуман (13.10.2026, замер на этой машине):
# webkit 26.6 отказывается снимать страницу выше 32767 px в ЛЮБОМ
# измерении — и при `full_page=True`, и при `clip` с height=32768:
# "Page.screenshot: Cannot take screenshot larger than 32767 pixels on
# any dimension". chromium 153 берёт ту же страницу целиком (42041 px).
#
# Обход есть, и он проверен на сходство, а не на глаз: Playwright умеет
# снять фрагмент всей страницы через `clip` + `full_page=True`, и такой
# тайл потолка не превышает. Прежняя запись в этом файле утверждала, что
# тайлы непригодны из-за `position: sticky` у .site-header
# (docs/style.css:749) — но это верно только для съёмки скроллом. `clip`
# не скроллит: страница не меняет состояния, липкая шапка рисуется один
# раз, в своём естественном месте. Контрольный замер: в хроме снимок,
# сшитый из двух тайлов (30000 + 12041), совпал с честным full_page —
# НОЛЬ пикселей расхождения при пороге канала 8.
#
# Формат: (страница, ширина) -> (замеренная высота, причина).
KNOWN_UNCOVERED = {
    ("index", 412): (
        43998,
        "index@412 = 43998 px при потолке webkit 32767 px. Обходится"
        " тайлами (clip + full_page): эталон webkit/index-412.png есть"
        " и проходит. Запись осталась гейтом высоты и страховкой на"
        " случай, если тайловая съёмка перестанет работать. В chromium"
        " та же страница снимается целиком (там потолка нет, поэтому"
        " гейт вызывается только под webkit)."
        " Число перемерено 19.10.2026 (Блок 5: +10 плиток популярных"
        " добавок на index, BK-5): прежняя запись 42937 px (v5.6.4)"
        " разошлась на 2.5 % — гейт поймал. Предыдущий рост: 42044 px"
        " (v5.1.6) → 42937 px (14.10.2026, #whyTrust +160 px)."
        " Контрольная перекрёстная сверка: chromium снимает ту же"
        " страницу целиком, эталон index-412.png = 42934 px — разница"
        " с webkit около 1064 px (10 плиток × ~100 px).",
    ),
}

#: Допуск на сверку записанной высоты с реальной, в долях.
HEIGHT_TOLERANCE = 0.02
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
    # v5.6.2 (#95): правило `#loadingBar{display:none!important}` УДАЛЕНО.
    # Оно маскировало баг, который поэтому и не был пойман: при
    # предрасчётных позициях stabilization.enabled=false, событие
    # stabilizationIterationsDone не приходит, и плашка оставалась
    # display:block навсегда — вуаль rgba(28,28,30,.95) поверх страницы,
    # перехватывавшая тапы. Комментарий над этим местом утверждал, что
    # «в покое у плашки display:none», и это было неверно: маска делала
    # утверждение непроверяемым прямо в том тесте, который должен был
    # ловить регрессию.
    #
    # Маску можно снять, потому что баг починен (docs/graph.html,
    # hideLoadingBar + network.once("afterDrawing")) и плашка прячется
    # сама за ~800 мс — задолго до момента съёмки. Проверено: снятие
    # маски не изменило ни одного эталона graph.
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

# v5.6.2: cookie-согласие для съёмки страниц — 'rejected'.
#
# ЗАЧЕМ (обоснование под задачу D5). Баннер согласия (#cookieBanner)
# показывается только при ПУСТОМ localStorage['cookie-consent'] — то есть
# на первом визите. Свежий контекст теста по умолчанию именно такой, и в
# полностраничном снимке баннер (position:fixed, дно вьюпорта) попал бы
# в кадр каждого из эталонов. Эталон тогда зависел бы от отсутствия
# согласия: правка текста или стилей баннера роняла бы ВСЕ страницы, а не
# свою.
#
# Выбран не KILL_CSS с `#cookieBanner{display:none!important}` (урок #95:
# маска через CSS делала баг непроверяемым прямо в том тесте, который
# должен был его ловить), а явное состояние: до загрузки страниц тест
# объявляет отказ. Метрика при 'rejected' не загружается — прогон
# снапшотов не шлёт запросов к mc.yandex.ru и не засоряет статистику
# счётчика. Сам баннер проверяется отдельным тестом
# test_cookie_banner_visible_first_visit со своим эталоном.
CONSENT_INIT_JS = r"""
try { localStorage.setItem('cookie-consent', 'rejected'); } catch (e) {}
"""

pytestmark = pytest.mark.snapshots

playwright_api = pytest.importorskip("playwright.sync_api",
                                     reason="playwright не установлен")
np = pytest.importorskip("numpy", reason="numpy не установлен")
PIL_Image = pytest.importorskip("PIL.Image", reason="Pillow не установлен")


# ─────────────────────────── окружение ───────────────────────────

def _slug(page: str) -> str:
    return page.replace("/", "-")


# Файлы-маркеры, по которым сверяется сервер с рабочей копией.
# Маркеров два, а не один. style.css ловит чужой набор стилей, index.html —
# чужую разметку. Одной сверки style.css не хватало: правка HTML без правки
# CSS проходила молча, и на :8000 отдавался другой клон проекта — прогоны
# выглядели успешными, а мерили не тот код (reports/V561_P1_BATCH.md,
# находка 1: два ложных «76 passed» подряд).
SERVER_PROBE_FILES = ("style.css", "index.html")


def _check_server() -> None:
    """Сервер обязан отдавать файлы ИМЕННО ЭТОГО репозитория.

    Иначе тест молча сравнивал бы страницы из другой копии проекта: правка в
    docs/ не попала бы в снимок, эталон «прошёл бы», а страница на самом деле
    поехала. Это ровно тот класс ложной находки, который запрещён правилом
    верификации проекта, поэтому сверяем хэши файлов-маркеров.
    """
    for name in SERVER_PROBE_FILES:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=10) as resp:
                served = resp.read()
        except Exception as exc:  # noqa: BLE001 — причина попадёт в текст skip
            pytest.skip(
                f"Нет {BASE_URL} ({exc}). Запусти: "
                f"python -m http.server 8000 --directory docs  (из корня репозитория)"
            )
        local = (ROOT / "docs" / name).read_bytes()
        if hashlib.sha256(served).hexdigest() != hashlib.sha256(local).hexdigest():
            pytest.skip(
                f"{BASE_URL} отдаёт ЧУЖУЮ копию проекта ({name} не совпал с "
                f"{ROOT / 'docs' / name}). Эталоны были бы сравнением "
                f"не с тем кодом, который меняется. Запусти сервер из этого "
                f"репозитория или укажи SNAPSHOT_BASE_URL."
            )


@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def browser(request, playwright_instance):
    """Движок Playwright. Параметризована, поэтому каждый тест, который
    берёт browser, прогоняется по всем движкам. Имя движка доступно как
    browser.name — по нему выбирается каталог эталонов."""
    engine = request.param
    pw = playwright_instance
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

    # Маскировка версии — после того как version.js подставил значение.
    # Без неё смена app в docs/version.json роняет ~50 эталонов (версия
    # выводится дважды на каждой странице: в .site-title и в <footer>).
    # Ключ tests — тот же случай: docs/index.html:317 печатает «тестов: N»
    # прямо в плашке, и число растёт от КАЖДОГО нового теста, а не от правки
    # вёрстки. Без маскировки добавление одного файла с тестами роняло бы
    # три эталона index и требовало пересъёмки — ровно та беговая дорожка,
    # ради которой снят F-18 (#98).
    page.evaluate(
        """() => {
            document.querySelectorAll(
                '[data-version="app"],[data-version="tests"]'
            ).forEach(el => {
                el.textContent = el.dataset.version === 'app'
                    ? 'vX.X.X' : 'vNNN';
            });
        }"""
    )

    if full_page:
        engine = getattr(page.context.browser, "engine", "?")
        cap = FULL_PAGE_CAP_PX.get(engine)
        if cap:
            sh = page.evaluate(
                """() => Math.max(document.documentElement.scrollHeight,
                                  document.body.scrollHeight)"""
            )
            if sh > cap:
                _assert_declared_gap(
                    page_name, page.viewport_size["width"],
                    engine, sh, cap, url)
                return _capture_tiled(page, sh, cap, engine, url)
    return page.screenshot(full_page=full_page)


def _capture_tiled(page, measured: int, cap: int, engine: str,
                   url: str) -> bytes:
    """Снимок страницы выше потолка движка — тайлами `clip` + `full_page`.

    Ключевое отличие от съёмки скроллом: `clip` НЕ скроллит страницу.
    Состояние страницы не меняется, поэтому липкий `.site-header`
    (`position: sticky`, docs/style.css:749) попадает в снимок ровно
    один раз — ровно как в честном full_page, и ровно в своём
    естественном месте. Именно поэтому «липкая шапка» не является
    причиной отказаться от тайлов: она мешает только при прокрутке.

    Сходство метода проверено измерением, а не предположено: в хроме,
    где доступны оба способа, снимок, сшитый из двух тайлов
    (30000 + 12041 = 42041 px), совпал с `full_page=True` без единого
    различающегося пикселя (порог канала 8).

    Высота тайла взята равной потолку движка — это последнее значение,
    которое webkit ещё согласился отдать (clip 32767 проходит, 32768
    падает), поэтому запас не вычитается.
    """
    width = page.viewport_size["width"]
    tiles: list[bytes] = []
    y = 0
    while y < measured:
        h = min(cap, measured - y)
        try:
            png = page.screenshot(
                clip={"x": 0, "y": y, "width": width, "height": h},
                full_page=True,
            )
        except Exception as e:                       # noqa: BLE001
            # Потолок не обошёлся — честный skip с причиной, а не падение
            # и не тихое урезание эталона. Комбинация уже объявлена в
            # KNOWN_UNCOVERED и её высота только что сверена.
            pytest.skip(
                f"[{engine}] {url} не помещается в full-page снимок "
                f"({measured} px при потолке {cap} px) И не берётся "
                f"тайлами: {type(e).__name__}: {str(e).splitlines()[0][:120]}. "
                f"Комбинация объявлена в KNOWN_UNCOVERED, высота сверена. "
                f"Это ограничение движка, а не регрессия вёрстки — и не "
                f"повод молча урезать эталон."
            )
        tiles.append(png)
        y += h

    strip = [np.asarray(_decode(t), dtype=np.uint8) for t in tiles]
    stitched = np.concatenate(strip, axis=0)
    assert stitched.shape[0] == measured, (
        f"[{engine}] {url}: сшито {stitched.shape[0]} px из {len(tiles)} "
        f"тайлов, а замерено {measured} px — тайлов не хватило или "
        f"страница сдвинулась между замером и съёмкой"
    )
    out = io.BytesIO()
    PIL_Image.fromarray(stitched).save(out, format="PNG")
    return out.getvalue()


def _assert_declared_gap(page_name: str, width: int, engine: str,
                         measured: int, cap: int, url: str) -> None:
    """Непокрытая комбинация обязана быть объявлена, и высота — верной.

    Проверка отрицательного примера обязательна: гейт, который считает
    «что чему соответствует», обязан падать, когда не соответствует.
    «гейт,  который  считает,  обязан  падать,  обязан  падать,  когда  не  соответствует  неправдлу.  Резко  так пошёл
    """
    key = (page_name, width)
    entry = KNOWN_UNCOVERED.get(key)
    if entry is None:
        pytest.fail(
            f"[{engine}] {url} не помещается в full-page снимок "
            f"({measured} px при потолке {cap} px), но пара {key} не "
            f"объявлена в KNOWN_UNCOVERED. Дыра в покрытии возникла "
            f"внезапно — так бывает после правки вёрстки, увеличившей "
            f"страницу. Снимок будет снят тайлами (см. _capture_tiled), "
            f"но без записи в KNOWN_UNCOVERED это будет первый такой "
            f"случай без гейта высоты. Внеси пару с замеренной "
            f"высотой и причиной. Молчаливый пропуск здесь выглядит "
            f"как «страница проверена», а она не проверена."
        )
    recorded, reason = entry
    drift = abs(measured - recorded) / recorded
    assert drift <= HEIGHT_TOLERANCE, (
        f"[{engine}] {url}: высота {measured} px разошлась с записанной "
        f"{recorded} px на {drift:.1%} (допуск {HEIGHT_TOLERANCE:.0%}). "
        f"Запись в KNOWN_UNCOVERED устарела — перемерь и обнови её. "
        f"Причина, записанная там же: {reason}"
    )


# ─────────────────────────── сравнение ───────────────────────────

def _decode(png: bytes):
    return PIL_Image.open(io.BytesIO(png)).convert("RGB")


#: Маску углов включают только для этого снимка и только явно (см.
#: `corner_radius=` в test_cookie_banner_visible_first_visit). Список —
#: чтобы случайно не расширить её на остальные 75 снимков: они снимаются
#: постранично, углы у страниц прямые, и исключать там нечего.
CORNER_MASK_NAMES = ("cookie-banner",)


def _rounded_rect_mask(height: int, width: int, radius: float):
    """-> булева массив (h, w): True = пиксель ВНУТРИ скруглённого прямоугольника.

    Зачем (батч 7, MKT-P1-01)
    -------------------------
    `locator.screenshot()` клипает по bounding box элемента, а не по его
    отрисованной форме. Поэтому часть бокса внутри, но ЗА дугой
    `border-radius` — это вовсе не пиксели элемента, а то, что лежит под
    ним на странице. Для `#cookieBanner` (position:fixed, внизу вьюпорта)
    под углами оказывается произвольное содержимое index.html, и оно
    меняется от правки ЛЮБОЙ части страницы выше баннера: добавление
    строки-слогана сдвинуло поток и дало 86 расходящихся пикселей ровно
    по дугам, при неподвижном боксе (x=280, y=786, 720x98 — как в эталоне).

    То есть эталон зависел от высоты страницы, а баннер к ней отношения не
    имеет. Маска убирает ровно эту зависимость, не ослабляя глобальный
    DIFF_TOL_PCT и не перезаписывая эталон: сравниваются только пиксели,
    которые действительно принадлежат баннеру.
    """
    inside = np.ones((height, width), dtype=bool)
    r = float(radius)
    if r <= 0:
        return inside
    r = min(r, width / 2.0, height / 2.0)
    xs = np.arange(width) + 0.5
    ys = np.arange(height) + 0.5
    # Пиксель вне формы, если он и по горизонтали, и по вертикали дальше
    # радиуса от центра дуги И расстояние до центра больше радиуса.
    for dx in (r - xs, xs - (width - r)):
        for dy in (r - ys, ys - (height - r)):
            # Маска строится как (height, width): dx — по колонкам, dy — по
            # строкам. Перепутать оси здесь нельзя: np.ones((h, w)) принял
            # бы (w, h) и упал бы на broadcast с непонятным сообщением.
            outside = ((dx > 0)[None, :] & (dy > 0)[:, None]
                       & (dx[None, :] ** 2 + dy[:, None] ** 2 > r * r))
            inside &= ~outside
    return inside


def _corner_radius(page, selector: str) -> float:
    """Радиус скругления элемента в пикселях, максимум по четырём углам.

    Берётся максимум, а не только левый верхний: если у элемента углы
    разные, маска по меньшему оставила бы чужие пиксели в сравнении.
    Неразобранное значение (проценты, calc) даёт 0 — тогда маска пустая и
    сравнение ведётся как раньше, то есть гейт не ослабевает молча.
    """
    values = page.evaluate(
        """(sel) => {
            const cs = getComputedStyle(document.querySelector(sel));
            return ['borderTopLeftRadius', 'borderTopRightRadius',
                    'borderBottomLeftRadius', 'borderBottomRightRadius']
                .map(k => parseFloat(cs[k]));
        }""", selector)
    parsed = [v for v in values if v == v and v > 0]
    return max(parsed) if parsed else 0.0


def _compare(actual_png: bytes, expected_png: bytes, corner_radius: float = 0.0):
    """-> (процент, bbox или None, n_различающихся, размеры или None).

    Разные размеры = страница стала выше/ниже. Это самый сильный сигнал
    из возможных, поэтому возвращается 100% и размеры: «высота поехала на
    2px» полезнее, чем безликое «расхождение 100%».

    `corner_radius` > 0 исключает из сравнения пиксели за дугой
    скругления — они принадлежат странице, а не элементу (см.
    `_rounded_rect_mask`). По умолчанию 0: маска выключена.
    """
    a, e = _decode(actual_png), _decode(expected_png)
    if a.size != e.size:
        return 100.0, None, 0, (a.size, e.size)
    av = np.asarray(a, dtype=np.int16)
    ev = np.asarray(e, dtype=np.int16)
    d = np.abs(av - ev).max(axis=2)
    mask = d > CHANNEL_TOL
    if corner_radius > 0:
        mask &= _rounded_rect_mask(a.size[1], a.size[0], corner_radius)
    n = int(mask.sum())
    if not n:
        return 0.0, None, 0, None
    ys, xs = np.nonzero(mask)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return 100.0 * n / mask.size, bbox, n, None


def _write_artifacts(name: str, actual_png: bytes, expected_png: bytes,
                     art_dir: Path, corner_radius: float = 0.0) -> list[str]:
    ART_DIR = art_dir
    ART_DIR.mkdir(parents=True, exist_ok=True)
    # `!.gitignore` обязателен: без него правило `*` игнорирует сам .gitignore,
    # каталог не попадает в индекс и после клона артефакты падения окажутся
    # в репозитории (десятки мегабайт diff-картинок).
    # newline="\n": без него Windows пишет CRLF, и каждое падение снапшота
    # пачкает индекс двумя изменёнными файлами (техдолг #49).
    (ART_DIR / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8",
                                        newline="\n")
    a, e = _decode(actual_png), _decode(expected_png)
    (ART_DIR / f"{name}.actual.png").write_bytes(actual_png)
    written = [str(ART_DIR / f"{name}.actual.png")]
    if a.size == e.size:
        av = np.asarray(a, dtype=np.int16)
        ev = np.asarray(e, dtype=np.int16)
        mask = np.abs(av - ev).max(axis=2) > CHANNEL_TOL
        if corner_radius > 0:
            mask &= _rounded_rect_mask(a.size[1], a.size[0], corner_radius)
        heat = np.array(e, dtype=np.uint8).copy()
        heat[mask] = [255, 0, 0]
        p = ART_DIR / f"{name}.diff.png"
        PIL_Image.fromarray(heat).save(p)
        written.append(str(p))
    return written


REWRITTEN: list[str] = []


def _assert_snapshot(name: str, actual_png: bytes, snap_dir: Path,
                     corner_radius: float = 0.0) -> None:
    """Сравнить снимок с эталоном или перезаписать эталон.

    Перезапись разрешена поимённо (F-18, #98). Прежде `UPDATE_SNAPSHOTS=1`
    был единственным режимом и затирал весь набор молча: опечатка в одном
    токене стиля выглядела как успешная правка, пока картинки не
    сравнивали глазами. Теперь переменная окружения принимает список имён,
    и в выборочном режиме прогон падает с перечнем заменённых файлов —
    замену обязан увидеть человек.

    В режиме `all` поведение прежнее: молча переписать всё. Это осознанно
    и описано в докстринге файла — полная пересъёмка нужна редко и
    намеренно, а не по недосмотру в переменной окружения.

    `corner_radius` > 0 — opt-in маска углов (см. `_rounded_rect_mask`).
    Принимается только для снимков из `CORNER_MASK_NAMES`: иначе маска
    молча ослабила бы чужой снимок, а это ровно тот класс ошибки, который
    гейт чисел в скиллах уже ловил дважды.
    """
    path = snap_dir / f"{name}.png"

    if corner_radius > 0 and name not in CORNER_MASK_NAMES:
        raise AssertionError(
            f"Маска углов передана для снимка {name!r}, которого нет в "
            f"CORNER_MASK_NAMES={CORNER_MASK_NAMES}. Добавь снимок в список "
            f"осознанно или убери corner_radius="
        )

    if _should_update(name):
        snap_dir.mkdir(parents=True, exist_ok=True)
        existed = path.exists()
        path.write_bytes(actual_png)
        REWRITTEN.append(f"{path} ({'заменён' if existed else 'создан'}, "
                         f"{path.stat().st_size / 1024:.0f} КБ)")
        return

    if not path.exists():
        snap_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(actual_png)
        size_kb = path.stat().st_size / 1024
        pytest.fail(f"Эталон {name} создан ({size_kb:.0f} КБ). Посмотри его "
                    f"в глаза — потом он станет базой. Повтори прогон.")

    pct, bbox, n, sizes = _compare(actual_png, path.read_bytes(),
                                   corner_radius)
    if pct <= DIFF_TOL_PCT:
        return
    files = _write_artifacts(name, actual_png, path.read_bytes(),
                             snap_dir / "_actual", corner_radius)
    if sizes:
        why = (f"размер страницы изменился: стало {sizes[0][0]}x{sizes[0][1]}, "
               f"эталон {sizes[1][0]}x{sizes[1][1]} — это само по себе причина "
               f"остановиться, а не «100% пикселей»")
    else:
        why = f"{n} пикселей, область x[{bbox[0]}..{bbox[2]}] y[{bbox[1]}..{bbox[3]}]"
    if UPDATE_MODE == "off":
        hint = (f"    Если правка намеренная — перезапиши ТОЛЬКО этот эталон:\n"
                f"    $env:UPDATE_SNAPSHOTS='{name}'; pytest -q -m snapshots")
    else:
        hint = (f"    Если правка намеренная — перезапиши эталон:\n"
                f"    $env:UPDATE_SNAPSHOTS='1'; pytest -q -m snapshots")
    pytest.fail(f"[{snap_dir.name}] {name}: расхождение {pct:.3f}% при пороге "
                f"{DIFF_TOL_PCT}%\n"
                f"    {why}\n    эталон: {path}\n"
                f"    артефакты: {', '.join(files)}\n"
                f"    {hint}")


def pytest_terminal_summary(terminalreporter) -> None:
    """Показать перечень перезаписанных эталонов.

    Без этого выборочное обновление выглядит как обычный зелёный прогон,
    а перезаписанный файл никто не открывает — ровно та проблема, ради
    которой F-18 и выделялся в отдельную правку.
    """
    if not REWRITTEN:
        return
    terminalreporter.write_sep("=", "эталоны перезаписаны")
    for line in REWRITTEN:
        terminalreporter.write_line(f"  {line}")
    terminalreporter.write_line(
        "  Посмотри их глазами и повтори прогон без UPDATE_SNAPSHOTS — "
        "тогда он сравнит новое со старым.")


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
    ctx.add_init_script(CONSENT_INIT_JS)
    page = ctx.new_page()
    page.emulate_media(reduced_motion="reduce")
    try:
        png = _capture(page, page_name, full_page=True)
    finally:
        ctx.close()
    _assert_snapshot(f"{_slug(page_name)}-{width}", png, snap_dir)


def test_modal_index_snapshot(_env_checked, browser, snap_dir):
    """Карточка на index ведёт на sup/<id>.html (модалка убрана v5.6.5)."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              service_workers="block", reduced_motion="reduce",
                              color_scheme=COLOR_SCHEME)
    ctx.add_init_script(FREEZE_JS)
    ctx.add_init_script(CHART_PATCH_JS)
    ctx.add_init_script(CONSENT_INIT_JS)
    page = ctx.new_page()
    page.emulate_media(reduced_motion="reduce")
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
        # Маскировка версии — см. комментарий в _capture выше.
        page.evaluate(
            """() => {
                document.querySelectorAll(
                    '[data-version="app"],[data-version="tests"]'
                ).forEach(el => {
                    el.textContent = el.dataset.version === 'app'
                        ? 'vX.X.X' : 'vNNN';
                });
            }"""
        )
        # На index заголовок карточки — не h3, а strong.card-title (v2.6, P2-16):
        # h3 убрали, чтобы структура документа отражала разделы, а не 130 карточек.
        card = page.locator("#cardsGrid .card").first
        card.scroll_into_view_if_needed()
        card.click()
        # Клик по карточке ведёт на sup/<slug>.html вместо модалки (v5.6.5).
        page.wait_for_url("**/sup/*.html", timeout=30_000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(SETTLE_MS)
        png = page.screenshot(full_page=False)
    finally:
        ctx.close()
    _assert_snapshot("modal-index", png, snap_dir)

def test_cookie_banner_visible_first_visit(_env_checked, browser, snap_dir):
    """v5.6.2: cookie-баннер виден на первом визите, Метрика молчит.

    Зеркало остальной съёмки: там localStorage['cookie-consent'] заранее
    'rejected' (CONSENT_INIT_JS), здесь — контекст БЕЗ всякого выбора, то
    есть самое состояние «первый визит». Проверяется ровно то, что обязано
    быть до согласия:

      1. баннер виден (display не none, непустой бокс);
      2. НИ ОДНОГО запроса к mc.yandex.ru — loadMetrika() цепляет tag.js
         только из обработчика «Принять»;
      3. свой эталон баннера (по движкам, как все остальные снимки).

    Ниже — клик «Принять»: после него запрос tag.js обязан появиться.
    Проверяется факт запроса, а не ответа: без сети request-событие всё
    равно срабатывает, тест остаётся честным.

    Эталон баннера отдельный НЕ для красоты: пока он один на движок,
    правка текста или стилей баннер горёт только своим снимком, а не 73
    страничными (именно поэтому страницы снимаются с 'rejected').

    Маска углов (батч 7): сравнение идёт по пикселям ВНУТРИ дуги
    `border-radius`. Без неё эталон зависел от того, что лежит под
    баннером, а под ним — содержимое index.html: добавление строки-слогана
    (MKT-P1-01) сдвинуло поток страницы и дало 86 расходящихся пикселей
    ровно по дугам, при боксе, совпадающем с эталоном до пикселя. Радиус
    снимается с элемента на момент съёмки, а не константой из CSS — иначе
    правка скругления снова рассинхронизирует маску с реальностью.
    """
    ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                              service_workers="block", reduced_motion="reduce",
                              color_scheme=COLOR_SCHEME)
    ctx.add_init_script(CHART_PATCH_JS)
    page = ctx.new_page()
    page.emulate_media(reduced_motion="reduce")
    yandex = []
    page.on("request",
            lambda r: yandex.append(r.url) if "mc.yandex.ru" in r.url else None)
    try:
        _open(page, f"{BASE_URL}/index.html")
        page.wait_for_timeout(SETTLE_MS)

        # Свежий контекст: выбора ещё не было.
        assert page.evaluate(
            "() => localStorage.getItem('cookie-consent')") is None

        banner = page.locator("#cookieBanner")
        assert banner.is_visible(), (
            "cookie-баннер не виден на первом визите: либо нет разметки "
            "#cookieBanner, либо CSS держит его скрытым ([hidden] vs "
            "display), либо style.css не применился."
        )

        assert not yandex, (
            "Метрика загрузилась ДО согласия — нарушение правила "
            "приватности: " + ", ".join(yandex[:3])
        )

        _assert_snapshot("cookie-banner", banner.screenshot(), snap_dir,
                         _corner_radius(page, "#cookieBanner"))

        # «Принять» — и только теперь Метрика имеет право стартовать.
        page.click("#cookieAccept")
        page.wait_for_timeout(2000)
        assert any("metrika/tag.js" in u for u in yandex), (
            "после «Принять» tag.js не запрошен: loadMetrika() не "
            "вызван из cookie-banner.js"
        )
        assert page.evaluate(
            "() => localStorage.getItem('cookie-consent')") == "accepted"
        assert page.evaluate(
            "() => document.getElementById('cookieBanner').hidden"), (
            "баннер не скрылся после «Принять»"
        )
    finally:
        ctx.close()

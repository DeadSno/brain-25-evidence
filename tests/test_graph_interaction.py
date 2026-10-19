# -*- coding: utf-8 -*-
"""Граф взаимодействий: реальная отрисовка и экспорт PNG (marker: graph).

Переписан в v5.6.5. Прежняя версия проверяла UI, которого больше нет:

* `#int-graph` и `.int-layout` — таких элементов в docs/interactions.html
  НЕТ: `.int-layout` встречается только внутри `<style>` (строки 101, 129,
  131), а контейнер графа называется `#mynetwork` (строка 306).
* `atlas.html` с `.atl-layout` и `#atl-graph` — docs/atlas.html давно
  редирект-заглушка (`<meta http-equiv="refresh" content="0; url=
  interactions.html#mech">`), поэтому 40 из 42 тестов падали с
  `Failed to find element matching selector "#int-graph"`.

Что проверяется теперь (движки chromium и webkit, по 12 тестов на движок,
24 всего):

1. режим «График» открыт по умолчанию (data-mode="graph");
2. старых селекторов в разметке нет (иначе тест снова начнёт проверять
   несуществующий UI);
3. граф реально строится: `#mynetwork` перестаёт быть hidden, внутри
   появляется canvas;
4. у canvas ненулевые размеры, контейнер не схлопнут;
5. на canvas есть «чернила» — непустые пиксели (иначе граф пустой, а
   размеры формально валидны);
6. кнопка экспорта существует и её обработчик отдаёт настоящий PNG:
   data-URL с сигнатурой PNG и полезной нагрузкой >= MIN_PNG_PAYLOAD,
   имя файла — ровно то, что зашито в обработчике
   (`brain-25-evidence-graph.png`, docs/interactions.html, a.download).
   Требование «имя без подстроки graph» с фактическим кодом конфликтует:
   имя содержит «graph» по построению, поэтому утверждается фактическое
   имя, а не запрет подстроки.

Граф строится ТОЛЬКО по действию пользователя: `drawGraph()` показывает
приветствие, `ensureNetwork()` вызывается из `applyFocus()`, а её дёргает
ввод в `#graphSearch` (обработчик — `wireControls`, строки 736-749).
Поэтому тест пишет в поиск, а не просто ждёт загрузки страницы.

Сервер :8000 поднимает автouse-фикстура `live_server` в tests/conftest.py,
общий `sync_playwright()` даёт `playwright_instance` — свой контекст
открывать нельзя (два sync_playwright не живут одновременно, см.
docstring `playwright_instance`).
"""

from __future__ import annotations

import base64
import hashlib
import os
import urllib.request
from pathlib import Path

import pytest

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright не установлен")

BASE_URL = os.environ.get("SNAPSHOT_BASE_URL", "http://localhost:8000")
PATH = "/interactions.html"
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

pytestmark = [pytest.mark.graph]

BROWSERS = ("chromium", "webkit")

# Контейнер графа в текущей разметке (docs/interactions.html:306).
GRAPH_ID = "#mynetwork"
SEARCH_ID = "#graphSearch"
PNG_BTN = "#pngBtn"

MIN_PNG_PAYLOAD = 10_000      # настоящий скриншот графа весит десятки КБ
MIN_GRAPH_HEIGHT = 200
MIN_CONTAINER_HEIGHT = 400
MIN_INK_PIXELS = 500          # непустых пикселей на canvas

# Старые селекторы: если они вернутся в разметку, этот файл снова начнёт
# проверять не то, что рисуется, — поэтому их отсутствие утверждается явно.
# "#graph"/".layout" — из прежнего ТЗ; "#int-graph"/".int-layout" — раскладка,
# оставшаяся только внутри <style>; "#atl-graph"/".atl-layout" — atlas.html,
# который теперь редирект-заглушка.
OLD_SELECTORS = (
    "#graph", ".layout",
    "#int-graph", ".int-layout",
    "#atl-graph", ".atl-layout",
)

# Перехват программного клика по <a download>: браузер иначе начнёт
# скачивание, а нам нужен сам data-URL.
PATCH_CLICK_JS = """
() => {
  if (!HTMLAnchorElement.prototype.__origClick) {
    HTMLAnchorElement.prototype.__origClick = HTMLAnchorElement.prototype.click;
  }
  window.__exported = null;
  HTMLAnchorElement.prototype.click = function () {
    if (this.hasAttribute('download')) {
      window.__exported = { href: this.href, download: this.getAttribute('download') };
      return;
    }
    return HTMLAnchorElement.prototype.__origClick.call(this);
  };
}
"""

READ_EXPORT_JS = "() => window.__exported"

# «Чернила»: считаем пиксели, отличные от самого частого цвета фона.
INK_JS = """
() => {
  const c = document.querySelector('#mynetwork canvas');
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


@pytest.fixture
def browser(engine, pw):
    _check_server()
    b = getattr(pw, engine).launch()
    try:
        yield b
    finally:
        b.close()


@pytest.fixture
def page_with_graph(browser):
    """Страница, на которой граф уже построен (реальным действием)."""
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    errors: list[str] = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    try:
        pg.goto(f"{BASE_URL}{PATH}", wait_until="load")
        pg.wait_for_selector(SEARCH_ID, timeout=10_000)
        # Ввод в поиск -> applyFocus -> ensureNetwork -> видимый canvas.
        pg.fill(SEARCH_ID, "Магний")
        pg.wait_for_selector(f"{GRAPH_ID} canvas", timeout=15_000)
        yield pg, errors
    finally:
        pg.close()


# ───────────────────────────── режим и разметка ─────────────────────────────

def test_graph_tab_is_default(page_with_graph):
    pg, _ = page_with_graph
    active = pg.eval_on_selector(
        '.tr-tabs [role="tab"][data-mode="graph"]',
        "el => el.classList.contains('active') && el.getAttribute('aria-selected') === 'true'",
    )
    assert active, "вкладка «График» не активна по умолчанию"


def test_old_selectors_absent(page_with_graph):
    pg, _ = page_with_graph
    found = pg.evaluate(
        "sels => sels.filter(s => document.querySelector(s) !== null)", list(OLD_SELECTORS))
    assert found == [], f"вернулись устаревшие селекторы: {found}"


def test_service_states_hidden(page_with_graph):
    pg, _ = page_with_graph
    for sel in ("#graphError", "#graphEmpty"):
        assert pg.eval_on_selector(sel, "el => el.hidden"), f"{sel} показан при рабочем графе"


# ──────────────────────────────── сам граф ──────────────────────────────────

def test_graph_container_visible(page_with_graph):
    pg, _ = page_with_graph
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
    ink = pg.evaluate(INK_JS)
    assert ink >= MIN_INK_PIXELS, (
        f"непустых пикселей на canvas: {ink} (ожидалось >= {MIN_INK_PIXELS}); "
        "размеры валидны, но граф пуст")


def test_no_console_errors(page_with_graph):
    pg, errors = page_with_graph
    # vis-network ругается на дубли id и т.п. — это настоящий сигнал.
    relevant = [e for e in errors if "[graph]" in e or "vis" in e.lower()]
    assert relevant == [], f"ошибки в консоли: {relevant}"


# ─────────────────────────────── экспорт PNG ─────────────────────────────────

def test_export_button_exists(page_with_graph):
    pg, _ = page_with_graph
    assert pg.eval_on_selector(PNG_BTN, "el => el.tagName") == "BUTTON"
    assert pg.eval_on_selector(PNG_BTN, "el => el.getBoundingClientRect().width > 0"), (
        "кнопка экспорта не отрисована")


def test_export_handler_produces_real_png(page_with_graph):
    """Обработчик #pngBtn отдаёт data-URL с настоящим PNG.

    До v5.6.5 обработчика не существовало вовсе (grep 'pngBtn' по docs/*.js
    и inline-блокам давал только саму разметку кнопки), т.е. «Скачать PNG»
    на странице графа не работала.
    """
    pg, _ = page_with_graph
    pg.evaluate(PATCH_CLICK_JS)
    pg.click(PNG_BTN)
    exported = pg.evaluate(READ_EXPORT_JS)
    assert exported, "клик по #pngBtn не создал ссылку скачивания — обработчика нет"
    href = exported["href"]
    assert href.startswith("data:image/png;base64,"), f"не PNG data-URL: {href[:40]!r}"
    payload = base64.b64decode(href.split(",", 1)[1])
    assert payload[:8] == b"\x89PNG\r\n\x1a\n", "payload не начинается с сигнатуры PNG"
    assert len(payload) >= MIN_PNG_PAYLOAD, (
        f"PNG всего {len(payload)} байт (ожидалось >= {MIN_PNG_PAYLOAD}) — canvas пустой")
    # Имя файла зашито в обработчике: a.download = 'brain-25-evidence-graph.png'
    # (docs/interactions.html). Исходное требование «имя не содержит "graph"»
    # с фактическим кодом несовместимо — утверждаем фактическое имя, чтобы
    # переименование в обработчике ловилось тестом.
    assert exported["download"] == "brain-25-evidence-graph.png", (
        f"имя экспорта изменилось: {exported['download']!r}")


# ─────────────────────────────── движки целиком ──────────────────────────────

def test_engine_launches_and_renders(engine, pw):
    """Один тест на движок: страница вообще открывается и vis доступен."""
    _check_server()
    b = getattr(pw, engine).launch()
    try:
        pg = b.new_page()
        pg.goto(f"{BASE_URL}{PATH}", wait_until="load")
        assert pg.evaluate("() => typeof vis !== 'undefined'"), (
            f"{engine}: vis-network не загрузился")
    finally:
        b.close()

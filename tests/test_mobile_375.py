"""Проверка отсутствия горизонтального overflow на 375px (iPhone SE/8).

Запуск:
    python -m http.server 8000 --directory docs   (из корня репозитория)
    pytest -q -m mobile375

Гейт RUN_MOBILE удалён в v5.6.5 (tests/conftest.py); сервер поднимает
autouse-фикстура live_server при необходимости.

Страницы: index, interactions (2 таба, H-9), compare, map.
Проверка: document.documentElement.scrollWidth <= window.innerWidth
(нет горизонтальной прокрутки на мобильной ширине).
"""
import os
import urllib.request
from pathlib import Path

import pytest

playwright_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright не установлен")

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("SNAPSHOT_BASE_URL",
                          "http://localhost:8000").rstrip("/")

BROWSERS = ("chromium", "webkit")
VIEWPORT = {"width": 375, "height": 667}

# (страница, селектор таба для перебора, число табов или None)
CASES = [
    ("index.html", None, None),
    # interactions.html теперь редиректит на hactar.html (H-1), где 2 таба
    # с селектором .hactar-tabs [role="tab"] (H-9: «Обзор» и «Связи»).
    ("interactions.html", '.hactar-tabs [role="tab"]', 2),
    ("compare.html", None, None),
    ("map.html", None, None),
]


def _check_server() -> None:
    for name in ("style.css", "index.html"):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=10) as resp:
                served = resp.read()
        except Exception as exc:  # noqa: BLE001
            pytest.skip(
                f"Нет {BASE_URL} ({exc}). Запусти: "
                f"python -m http.server 8000 --directory docs")
        local = (ROOT / "docs" / name).read_bytes()
        import hashlib
        if hashlib.sha256(served).hexdigest() != hashlib.sha256(local).hexdigest():
            pytest.skip(
                f"{BASE_URL} отдаёт ЧУЖУЮ копию проекта ({name} не совпал). "
                f"Запусти сервер из этого репозитория.")


def _has_horizontal_overflow(page) -> bool:
    """True, если страница шире области просмотра (горизонтальный overflow)."""
    return bool(page.evaluate(
        "() => document.documentElement.scrollWidth > window.innerWidth"))


def _overflow_px(page) -> int:
    return int(page.evaluate(
        "() => document.documentElement.scrollWidth - window.innerWidth"))


@pytest.fixture(scope="session", params=BROWSERS, ids=lambda b: b)
def browser(request, playwright_instance):
    engine = request.param
    pw = playwright_instance
    try:
        b = getattr(pw, engine).launch()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"{engine} не запускается: {exc}. "
                    f"Поставь: playwright install {engine}")
    b.engine = engine
    yield b
    b.close()


@pytest.mark.mobile375
@pytest.mark.parametrize("page_name,tab_sel,n_tabs", CASES)
def test_no_horizontal_overflow(browser, page_name, tab_sel, n_tabs):
    _check_server()
    ctx = browser.new_context(viewport=VIEWPORT,
                              reduced_motion="reduce",
                              color_scheme="light")
    page = ctx.new_page()
    try:
        page.goto(f"{BASE_URL}/{page_name}", wait_until="load")
        page.wait_for_timeout(500)

        overflow = _has_horizontal_overflow(page)
        over_px = _overflow_px(page)
        assert not overflow, (
            f"{page_name} @375px: горизонтальный overflow {over_px} px "
            f"(scrollWidth={page.evaluate('document.documentElement.scrollWidth')}, "
            f"innerWidth={page.evaluate('window.innerWidth')})")

        # Для interactions — проверить все 4 таба
        if tab_sel and n_tabs:
            tabs = page.locator(tab_sel)
            for i in range(n_tabs):
                tab = tabs.nth(i)
                tab.click()
                page.wait_for_timeout(300)
                overflow = _has_horizontal_overflow(page)
                over_px = _overflow_px(page)
                assert not overflow, (
                    f"{page_name} @375px, таб {i}: горизонтальный overflow "
                    f"{over_px} px")
    finally:
        ctx.close()

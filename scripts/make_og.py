"""Создаёт docs/og.png — обложка для Хабра (780×440, светлая тема)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://deadsno.github.io/brain-25-evidence/"
OUT = Path("docs/og.png")
W, H = 780, 440

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        viewport={"width": W, "height": H},
        device_scale_factor=2,
        color_scheme="light",   # ← светлая тема
    )
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Принудительно включаем светлую тему (кнопка на сайте)
    try:
        page.click("#themeToggle", timeout=2000)
        page.wait_for_timeout(800)
    except Exception:
        pass  # если кнопка недоступна — оставляем дефолтную

    page.screenshot(path=str(OUT), clip={"x": 0, "y": 0, "width": W, "height": H})
    browser.close()

print(f"[OK] {OUT} — {OUT.stat().st_size / 1024:.0f} KB")
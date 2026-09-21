"""Создаёт docs/og.png — превью для соцсетей (1200×630)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://deadsno.github.io/brain-25-evidence/"
OUT = Path("docs/og.png")
W, H = 1200, 630

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(
        viewport={"width": W, "height": H},
        device_scale_factor=2,
    )
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(OUT), clip={"x": 0, "y": 0, "width": W, "height": H})
    browser.close()

print(f"[OK] {OUT} — {OUT.stat().st_size / 1024:.0f} KB")
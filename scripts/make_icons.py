"""Рендер PWA-иконок через Playwright: эмодзи «🧠⚖️» на фирменном фоне."""
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
ICONS = DOCS / "icons"
ICONS.mkdir(exist_ok=True)

SIZES = [192, 512]


def icon_html(size: int) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;padding:0;width:%dpx;height:%dpx;overflow:hidden}"
        "body{background:#1c1c1e;background-image:"
        "radial-gradient(%dpx %dpx at 15%% 10%%,rgba(52,152,219,.16),transparent 60%%),"
        "radial-gradient(%dpx %dpx at 85%% 20%%,rgba(155,89,182,.14),transparent 60%%),"
        "radial-gradient(%dpx %dpx at 50%% 95%%,rgba(46,204,113,.10),transparent 60%%);"
        "display:flex;align-items:center;justify-content:center}"
        "</style></head><body>"
        "<div style='font-size:%dpx;line-height:1.0;white-space:nowrap;text-align:center;"
        "filter:drop-shadow(0 4px 12px rgba(0,0,0,.45))'>"
        "🧠⚖️</div>"
        "</body></html>"
        % (size, size, size, size, size, size, size, size, int(size * 0.44))
    )


def render(size: int) -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
        page.set_content(icon_html(size), wait_until="domcontentloaded")
        page.wait_for_timeout(200)
        dest = ICONS / f"{size}.png"
        page.screenshot(path=str(dest), type="png")
        browser.close()
        print(f"  {dest}  ({size}x{size})")


if __name__ == "__main__":
    print("make_icons: рендерим иконки PWA...")
    for s in SIZES:
        render(s)
    print("make_icons: готово.")

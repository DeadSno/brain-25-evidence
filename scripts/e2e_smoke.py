"""e2e-smoke (слой L4): сайт отдаёт то, что обещает data.json."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
BASE = "http://localhost:8123"


def main() -> None:
    data = json.loads((DOCS / "data.json").read_text(encoding="utf-8"))
    n_all, n_price = len(data), sum(1 for s in data if s.get("price") is not None)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8123", "-d", str(DOCS)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.goto(f"{BASE}/index.html", wait_until="networkidle")
            cards = pg.locator(".card").count()                      # ALIGN-селектор
            assert cards == n_all, f"карточек {cards}, ожидалось {n_all}"
            bubbles = pg.evaluate("window.chart?.data?.datasets[0]?.data?.length ?? -1")
            assert bubbles == n_price, f"пузырей {bubbles}, ожидалось {n_price}"
            pg.goto(f"{BASE}/index.html#sup=Креатин", wait_until="networkidle")
            assert pg.locator("[role=dialog], .modal").first.is_visible(), "модалка не открылась"
            pg.goto(f"{BASE}/map.html?supplement=Эхинацея", wait_until="networkidle")
            assert "Эхинацея" in pg.locator("#chain").inner_text(), "атлас не открыл добавку"
            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("e2e smoke: OK")


if __name__ == "__main__":
    main()
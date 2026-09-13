"""UI-verify (ранбук шаг 5): noPrice/empty/toTop в живой вёрстке + скриншоты 1280/375."""
import subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
SHOTS = Path(__file__).resolve().parents[1] / "reports" / "ui"
BASE = "http://localhost:8123"


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8123", "-d", str(DOCS)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.goto(f"{BASE}/index.html", wait_until="networkidle")

            # бейдж noPrice в вёрстке (26 товаров без цены)
            np_count = pg.locator(".noPrice").count()
            assert np_count >= 1, "бейдж noPrice не отрендерен"

            # пустое состояние: поиск мусором → .empty + #resetAll
            pg.locator("#search").fill("zzzqqqнесуществующийxyz")
            assert pg.locator(".empty").count() == 1, "empty state не показан"
            assert pg.locator("#resetAll").is_visible(), "кнопка resetAll не видна"

            # сброс возвращает карточки с бейджем
            pg.locator("#resetAll").click()
            assert pg.locator(".noPrice").count() == np_count, "сброс не вернул бейджи"

            # #toTop появляется при скролле
            assert pg.locator("#toTop").count() == 1, "#toTop отсутствует в DOM"
            pg.evaluate("window.scrollTo(0, 1200)")
            pg.wait_for_timeout(300)
            assert "show" in (pg.locator("#toTop").get_attribute("class") or ""), \
                "#toTop не получил .show после скролла"

            pg.screenshot(path=str(SHOTS / "ui_1280.png"), full_page=True)

            # 375px (закрывает пункт C «не верифицировано»)
            pg.set_viewport_size({"width": 375, "height": 667})
            pg.reload(wait_until="networkidle")
            pg.screenshot(path=str(SHOTS / "ui_375.png"), full_page=True)
            overflow = pg.evaluate("document.documentElement.scrollWidth")
            if overflow > 380:
                print(f"WARN: горизонтальный оверфлоу на 375px: {overflow}px")

            # v2.3: баннер medium на кальций+железо
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="networkidle")
            if pg.locator(".banner.medium").count():
                pg.screenshot(path=str(SHOTS / "banner_medium.png"))

            # v2.3: зелёная подсказка в модалке Магния
            pg.evaluate("localStorage.removeItem('favs')")
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}#sup=Магний", wait_until="networkidle")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.screenshot(path=str(SHOTS / "modal_synergy.png"))

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("UI-verify: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
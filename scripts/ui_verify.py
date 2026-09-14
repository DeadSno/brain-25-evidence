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
            pg.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
            pg.wait_for_selector(".card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)

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
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.screenshot(path=str(SHOTS / "ui_375.png"), full_page=True)
            overflow = pg.evaluate("document.documentElement.scrollWidth")
            if overflow > 380:
                print(f"WARN: горизонтальный оверфлоу на 375px: {overflow}px")

            # v2.3: баннер medium на кальций+железо
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_timeout(500)
            if pg.locator(".banner.medium").count():
                pg.screenshot(path=str(SHOTS / "banner_medium.png"))

            # v2.3: зелёная подсказка в модалке Магния
            pg.evaluate("localStorage.removeItem('favs')")
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.screenshot(path=str(SHOTS / "modal_synergy.png"))

            # v2.5: новые страницы прозрачности рендерятся и скриншотятся
            for sub in ["faq", "glossary", "changelog_public"]:
                pg.goto(f"{BASE}/{sub}.html?ts={int(time.time())}", wait_until="domcontentloaded")
                pg.wait_for_selector("h1", state="attached", timeout=5000)
                pg.screenshot(path=str(SHOTS / f"v25_{sub}.png"))

            # v2.6: главная с 5-точечными бейджами и тумблером осей
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#cardsGrid .card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.set_viewport_size({"width": 1280, "height": 900})
            pg.screenshot(path=str(SHOTS / "v26_index.png"), full_page=True)
            # переключение на ось «Число РКИ» — график перерисовался без reload
            pg.click("#axisRCT")
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(SHOTS / "v26_axisRCT.png"))
            # модалка Кофеина: точки, бейджи, поделиться/сравнить
            pg.click("#axisMA")
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(SHOTS / "v26_modal.png"), full_page=True)
            pg.keyboard.press("Escape")
            # карта с trustbar
            pg.goto(f"{BASE}/map.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#chain", state="attached", timeout=5000)
            pg.screenshot(path=str(SHOTS / "v26_map.png"), full_page=True)

            # v2.6.1: экономика-блок + топ-3 МА в модалке Кофеина
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector("#cardsGrid .card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.screenshot(path=str(SHOTS / "v261_index.png"), full_page=True)
            pg.locator("#sortSelect").select_option("grade")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(SHOTS / "v261_sort_grade.png"), full_page=True)
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(SHOTS / "v261_modal_economics.png"), full_page=True)

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("UI-verify: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
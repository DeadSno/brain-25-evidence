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
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # ==================== v2.6.2: UI-фиксы ====================
            # F3.2: скриншоты ОБЕИХ тем + контраст ссылок ≥4.5:1
            def _srgb_lin(x):
                x /= 255.0
                return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

            def _contrast(c1, c2):
                def _lum(r, g, b):
                    return 0.2126 * _srgb_lin(r) + 0.7152 * _srgb_lin(g) + 0.0722 * _srgb_lin(b)
                def _parse(c):
                    c = c.strip()
                    if c.startswith("#"):
                        c = c[1:]
                        if len(c) == 3:
                            c = c[0]*2 + c[1]*2 + c[2]*2
                        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                    if c.startswith("rgb"):
                        parts = c.replace("rgba(", "").replace("rgb(", "").split(",")[:3]
                        return int(parts[0]), int(parts[1]), int(parts[2])
                    return 128, 128, 128
                r1, g1, b1 = _parse(c1)
                r2, g2, b2 = _parse(c2)
                L1, L2 = _lum(r1, g1, b1), _lum(r2, g2, b2)
                if L1 < L2:
                    L1, L2 = L2, L1
                return (L1 + 0.05) / (L2 + 0.05)

            def _effective_bg(pg_js, sel):
                """Получить effective background (идём вверх по DOM до непрозрачного)."""
                return pg_js.evaluate("""(sel) => {
                    const el = document.querySelector(sel);
                    if (!el) return null;
                    const s = getComputedStyle(el);
                    let bg = s.backgroundColor, node = el;
                    while ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && node.parentElement) {
                        node = node.parentElement;
                        bg = getComputedStyle(node).backgroundColor;
                    }
                    return {fg: s.color, bg: bg};
                }""", sel)

            for theme in ["light", "dark"]:
                pg.evaluate(f"localStorage.setItem('theme', '{theme}')")
                is_dark = theme == "dark"
                if is_dark:
                    pg.evaluate("document.body.classList.add('dark')")
                else:
                    pg.evaluate("document.body.classList.remove('dark')")
                pg.wait_for_timeout(200)
                ts2 = int(time.time())
                pg.goto(f"{BASE}/index.html?ts={ts2}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
                pg.wait_for_function("window.chart != null", timeout=5000)
                prefix = f"v262_{theme}"
                pg.screenshot(path=str(SHOTS / f"{prefix}_index.png"), full_page=True)

                # контраст ссылок: footer methodology, qaMore, trustChips chip, modal srcIcon
                selectors = [
                    f"footer a[href='methodology.html']",
                    ".qaMore",
                    ".trustChips .chip",
                ]
                for sel in selectors:
                    pair = _effective_bg(pg, sel)
                    if pair:
                        ratio = _contrast(pair["fg"], pair["bg"])
                        assert ratio >= 4.5, (
                            f"F3.2 [{theme}] {sel}: контраст {ratio:.1f}:1 < 4.5 "
                            f"(fg={pair['fg']}, bg={pair['bg']})"
                        )

                # модалка: opening KoFein and checking modal link contrast
                pg.click(".card[data-id='Кофеин']")
                pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
                pg.wait_for_timeout(300)
                pg.screenshot(path=str(SHOTS / f"{prefix}_modal.png"), full_page=True)
                pair_modal = _effective_bg(pg, "#modalBody .srcIcon")
                if pair_modal:
                    ratio_m = _contrast(pair_modal["fg"], pair_modal["bg"])
                    assert ratio_m >= 4.5, (
                        f"F3.2 [{theme}] modal srcIcon: контраст {ratio_m:.1f}:1 < 4.5 "
                        f"(fg={pair_modal['fg']}, bg={pair_modal['bg']})"
                    )
                pair_wb = _effective_bg(pg, "#modalBody .wbLink")
                if pair_wb:
                    ratio_wb = _contrast(pair_wb["fg"], pair_wb["bg"])
                    assert ratio_wb >= 4.5, (
                        f"F3.2 [{theme}] modal wbLink: контраст {ratio_wb:.1f}:1 < 4.5 "
                        f"(fg={pair_wb['fg']}, bg={pair_wb['bg']})"
                    )
                pg.keyboard.press("Escape")
                pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # F5: скриншот компактных секций доверия (3 вопроса + чипы)
            pg.goto(f"{BASE}/index.html?ts={int(time.time())}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            qa_box = pg.locator("#qaSection").bounding_box()
            trust_box = pg.locator("#trustSummary").bounding_box()
            if qa_box and trust_box:
                pg.screenshot(
                    path=str(SHOTS / "v262_trust_compact.png"),
                    clip={"x": 0, "y": qa_box["y"] - 10,
                          "width": 1280,
                          "height": qa_box["height"] + trust_box["height"] + 30}
                )
            # ==================== конец v2.6.2 ====================

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("UI-verify: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
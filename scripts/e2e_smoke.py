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
            ts = 0
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.goto(f"{BASE}/index.html", wait_until="networkidle")
            cards = pg.locator(".card").count()                      # ALIGN-селектор
            assert cards == n_all, f"карточек {cards}, ожидалось {n_all}"
            bubbles = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert bubbles == n_price, f"пузырей {bubbles}, ожидалось {n_price}"

            # v2.3: 3 вопроса в DOM
            qa = pg.locator("#qaSection .qa").count()
            assert qa == 3, f"секция «3 вопроса»: блоков {qa}, ожидалось 3"
            assert pg.locator("#qaSection").inner_text(), "секция «3 вопроса» пуста"

            # v2.3: 15 блоков в модалке + заглушка пустых блоков
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Фосфатидилсерин", wait_until="networkidle")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            nblocks = pg.locator("#modalBody .cblock").count()
            assert nblocks == 15, f"блоков полной карточки {nblocks}, ожидалось 15"
            assert pg.locator("#modalBody .cbEmpty").count() > 0, "нет заглушки «данных пока нет — проверяем»"

            # v2.3: зелёная подсказка «хорошая пара» в модалке Магния (магний+B6)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Магний", wait_until="networkidle")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function("document.getElementById('modalBody').innerText.includes('Хорошая пара')", timeout=5000)
            friends = pg.locator('[data-block-key="friends"]').inner_text()
            assert "Витамин B6" in friends, "зелёная подсказка магний+B6 не найдена"
            assert "Хорошая пара" in friends, "нет подписи «Хорошая пара»"

            # v2.3.1: контент топ-10 — у Креатина 8 edu-блоков заполнены (без заглушки)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Креатин", wait_until="networkidle")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function("document.getElementById('modalBody').innerText.includes('Самая изученная спортивная добавка')", timeout=5000)
            edu_keys = ["what", "who", "onset", "ul", "food", "official", "shop", "myths"]
            for k in edu_keys:
                txt = pg.locator(f'[data-block-key="{k}"]').inner_text()
                assert "данных пока нет" not in txt, f"edu-блок {k} Креатина остался пустым"

            # v2.3: живой баннер medium на кальций+железо в favs
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="networkidle")
            med = pg.locator(".banner.medium")
            assert med.count() == 1, "баннер medium не появился на кальций+железо"
            assert "конкурируют за всасывание" in med.inner_text(), "текст medium-баннера не тот"

            # v2.4: вкладка «Квадрант доказательности» рендерит (или честная заглушка)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="networkidle")
            n_verified = sum(1 for s in data if s.get("hedges_g") is not None)
            pg.click("#tabQuadrant")
            pg.wait_for_function("window.quadrantChart != null", timeout=5000)
            qpts = pg.evaluate("window.quadrantChart?.data?.datasets?.length ?? -1")
            assert qpts == n_verified, f"точек квадранта {qpts}, ожидалось {n_verified}"
            qnote = pg.locator("#quadrantNote").inner_text()
            assert "ждут верификации эффекта" in qnote, "нет честной заглушки «ждут верификации»"

            # v2.4: грейды A–D в DOM (карточка и модалка), когда есть верифицированный g
            with_g = [s for s in data if s.get("hedges_g") is not None and s.get("grade")]
            if with_g:
                first = with_g[0]
                ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="networkidle")
                card_grade = pg.locator(".card[data-id='" + first["id"] + "'] .grade").count()
                assert card_grade == 1, "нет грейда на карточке верифицированной добавки"
                pg.click(f".card[data-id='{first['id']}']")
                pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
                assert pg.locator("#modalBody .grade").count() >= 1, "грейд не в модалке"
                assert first["grade"] in pg.locator("#modalBody").inner_text(), "буква грейда не в модалке"

            pg.goto(f"{BASE}/map.html?supplement=Эхинацея", wait_until="networkidle")
            assert "Эхинацея" in pg.locator("#chain").inner_text(), "атлас не открыл добавку"

            # v2.5: faq/glossary/changelog_public рендерятся, футер-ссылки на них живые
            for sub in ["faq", "glossary", "changelog_public"]:
                for page in ["index.html", "map.html"]:
                    pg.goto(f"{BASE}/{page}?ts={ts}", wait_until="domcontentloaded")
                    page_html = pg.content()
                    assert f'href="{sub}.html"' in page_html, f"{page} не ссылается на {sub}.html"
                ts += 1
                pg.goto(f"{BASE}/{sub}.html?ts={ts}", wait_until="domcontentloaded")
                if sub == "faq":
                    assert pg.locator("details.qa").count() == 8, "faq: не 8 аккордеонов"
                elif sub == "glossary":
                    assert "Глоссарий" in pg.locator("h1").inner_text(), "glossary: нет h1"
                else:
                    assert "Журнал" in pg.locator("h1").inner_text(), "changelog_public: нет h1"

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("e2e smoke: OK")


if __name__ == "__main__":
    main()
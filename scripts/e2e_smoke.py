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
            pg.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
            pg.wait_for_selector(".card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            cards = pg.locator(".card").count()                      # ALIGN-селектор
            assert cards == n_all, f"карточек {cards}, ожидалось {n_all}"
            # После проверки данных:
            assert "Как мы проверяем" in pg.content() or "Открытые данные" in pg.content(), \
                "Статическая строка UTF-8 не рендерится (кракозябры?)"
            n_ma = sum(1 for s in data if (s.get("metaCount") or 0) > 0)
            # v2.6: дефолтная ось графика — «Число МА»
            bubbles = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert bubbles == n_ma, f"пузырей (ось=МА) {bubbles}, ожидалось {n_ma}"
            pg.click("#axisPrice")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_price), timeout=5000)
            pg.click("#axisMA")

            # v2.3: 3 вопроса в DOM
            qa = pg.locator("#qaSection .qa").count()
            assert qa == 3, f"секция «3 вопроса»: блоков {qa}, ожидалось 3"
            assert pg.locator("#qaSection").inner_text(), "секция «3 вопроса» пуста"

            # v2.3: 15 блоков в модалке + заглушка пустых блоков
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Фосфатидилсерин", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            nblocks = pg.locator("#modalBody .cblock").count()
            assert nblocks == 15, f"блоков полной карточки {nblocks}, ожидалось 15"
            assert pg.locator("#modalBody .cbEmpty").count() > 0, "нет заглушки «данных пока нет — проверяем»"

            # v2.3: зелёная подсказка «хорошая пара» в модалке Магния (магний+B6)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function("document.getElementById('modalBody').innerText.includes('Хорошая пара')", timeout=5000)
            friends = pg.locator('[data-block-key="friends"]').inner_text()
            assert "Витамин B6" in friends, "зелёная подсказка магний+B6 не найдена"
            assert "Хорошая пара" in friends, "нет подписи «Хорошая пара»"

            # v2.3.1: контент топ-10 — у Креатина 8 edu-блоков заполнены (без заглушки)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Креатин", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function("document.getElementById('modalBody').innerText.includes('Самая изученная спортивная добавка')", timeout=5000)
            edu_keys = ["what", "who", "onset", "ul", "food", "official", "shop", "myths"]
            for k in edu_keys:
                txt = pg.locator(f'[data-block-key="{k}"]').inner_text()
                assert "данных пока нет" not in txt, f"edu-блок {k} Креатина остался пустым"

            # v2.3: живой баннер medium на кальций+железо в favs
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".banner.medium", state="visible", timeout=5000)
            med = pg.locator(".banner.medium")
            assert med.count() == 1, "баннер medium не появился на кальций+железо"
            assert "конкурируют за всасывание" in med.inner_text(), "текст medium-баннера не тот"

            # v2.4: вкладка «Квадрант доказательности» рендерит (или честная заглушка)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#tabQuadrant", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
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
                ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id='" + first["id"] + "']", state="attached", timeout=5000)
                card_grade = pg.locator(".card[data-id='" + first["id"] + "'] .grade").count()
                assert card_grade == 1, "нет грейда на карточке верифицированной добавки"
                pg.click(f".card[data-id='{first['id']}']")
                pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
                assert pg.locator("#modalBody .grade").count() >= 1, "грейд не в модалке"
                assert first["grade"] in pg.locator("#modalBody").inner_text(), "буква грейда не в модалке"

            pg.goto(f"{BASE}/map.html?supplement=Эхинацея", wait_until="domcontentloaded")
            pg.wait_for_selector("#chain", state="attached", timeout=5000)
            assert "Эхинацея" in pg.locator("#chain").inner_text(), "атлас не открыл добавку"

            # ==================== v2.6: trust visuals ====================
            FILL = {"A": 4, "B": 3, "C": 2, "D": 1}
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Кофеин']", state="attached", timeout=5000)
            cof = next(s for s in data if s["id"] == "Кофеин")

            # B: 5 точек по грейду у Кофеина (B=3), 0 точек + «ждёт верификации» у Креатина
            assert FILL[cof["grade"]] == 3
            assert pg.locator(".card[data-id='Кофеин'] .gdots i.on").count() == FILL[cof["grade"]]
            assert pg.locator(".card[data-id='Креатин'] .gdots i.on").count() == 0
            assert "ждёт верификации" in pg.locator(".card[data-id='Креатин']").inner_text()

            # D: «Обновлено» + «ручная вычитка» на карточке
            assert "Обновлено: " + cof["updated"] in pg.locator(".card[data-id='Кофеин']").inner_text()
            assert "ручная вычитка" in pg.locator(".card[data-id='Кофеин']").inner_text()

            # C: оси X — кнопки есть, переключение перерисовывает без reload
            for a in ["Price", "MA", "RCT", "Year"]:
                assert pg.locator("#axis" + a).count() == 1, f"нет кнопки оси #axis{a}"
            n_year = sum(1 for s in data if s.get("year_last_ma"))
            pg.click("#axisYear")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_year), timeout=5000)
            pg.click("#axisMA")
            pg.wait_for_function("window.chart?.data?.datasets.length != null", timeout=5000)

            # модалка Кофеина: точки, бейджи, иконки источников (честно: цена без иконки — price_source пуст у всех)
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            assert pg.locator("#modalBody .gdots i.on").count() == 3, "в модалке нет 3 точек грейда B"
            assert "ручная вычитка" in pg.locator("#modalBody").inner_text()
            assert "Обновлено: " in pg.locator("#modalBody").inner_text()
            assert pg.locator("#modalBody a.srcIcon[href*='pubmed']").count() >= 1
            assert pg.locator("#modalBody a.srcIcon[href*='wikipedia']").count() >= 1
            assert pg.locator("#modalBody a.srcIcon[href*='wildberries'], #modalBody a.srcIcon[href*='ozon']").count() == 0

            # E: поделиться (TG/VK/копировать) и сравнить с чипами
            assert pg.locator(".shareRow a[href*='t.me/share']").count() == 1
            assert pg.locator(".shareRow a[href*='vk.com/share']").count() == 1
            assert pg.locator(".shareRow .copyLink[data-copy]").count() == 1
            same_n = sum(1 for s in data if s["id"] != "Кофеин" and s.get("category") == cof.get("category"))
            exp_chips = min(3, same_n)
            assert pg.locator(".compareChips .chipbx").count() == exp_chips, "чипы «Сравнить с» не по категории/топ-3"

            # A5: кнопка неточности в модалке; чип сравнения ведёт в #compareSection
            assert pg.locator("#modalBody a[href*='issues/new']").count() == 1
            if exp_chips:
                pg.click(".compareChips .chipbx >> nth=0")
                pg.wait_for_selector("#compareSection", state="visible", timeout=5000)
                assert pg.evaluate("document.getElementById('compareSelect1').value") == "Кофеин"
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#trustSummary", state="attached", timeout=5000)
            assert pg.locator(".trustbar").count() == 1 and "Открытые данные" in pg.locator(".trustbar").inner_text()
            assert pg.locator("#trustSummary").count() == 1 and "Как мы проверяем данные" in pg.locator("#trustSummary").inner_text()
            pg.goto(f"{BASE}/map.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#chain", state="attached", timeout=5000)
            assert "Открытые данные" in pg.locator(".trustbar").inner_text()

            # ==================== конец v2.6 ====================

            assert not errors, f"ошибки консоли: {errors}"

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
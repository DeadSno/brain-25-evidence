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

            # ==================== v2.6.1: economics ====================
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Кофеин']", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)

            # A: карточка больше не рисует «ценность»-блоки
            assert "ценность" not in pg.locator(".card[data-id='Кофеин']").inner_text()

            # B: блок «История цены» вместо экономики; canvas ИЛИ честный фолбэк (историй цен нет)
            pg.click(".card[data-id='Кофеин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function(
                "(() => { if (!document.getElementById('modalBody')) return false; "
                "const el = document.getElementById('ecoSpark'); "
                "if (!el) return false; "
                "return el.getElementsByTagName('canvas').length > 0 || "
                "el.innerText.includes('спарклайн появится') || el.dataset.state !== undefined; })()",
                timeout=5000)
            body = pg.locator("#modalBody").inner_text()
            assert "История цены" in body, "нет блока «История цены» в модалке"
            assert "ЭКОНОМИКА" not in body and "₽ за единицу эффекта" not in body, \
                "экономика-блок не демонтирован (v2.7.1)"
            assert "ценност" not in body, "в модалке осталась «ценность»"

            # C: тултип цены (priceTip) демонтирован вместе с экономика-блоком
            assert pg.locator("#modalBody .priceTip").count() == 0, "priceTip остался в модалке"

            # D: блок «Ключевые мета-анализы (топ-3 поиска)» — ≥1 ссылки + пометка до и после
            assert "Ключевые мета-анализы" in body, "нет блока топ-3 МА"
            assert pg.locator("#modalBody a[href*='pubmed.ncbi.nlm.nih.gov/']").count() >= 1, \
                "нет ссылок на PubMed в топ-3"
            vc = sum(1 for s in data if (s.get("key_sources") or []))
            note = "верифицированных добавок сейчас: " + str(vc)
            cuts = pg.locator("#modalBody").inner_text().count(note)
            assert cuts >= 2, f"пометка топ-3 не до+после списка: вхождений {cuts}"

            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # E: Креатин (без g) — экономика-причина демонтирована, блок «История цены» на месте
            pg.click(".card[data-id='Креатин']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            kb = pg.locator("#modalBody").inner_text()
            assert "Эффект ждёт верификации" not in kb, "у добавки без g осталась экономика-причина"
            assert "История цены" in kb, "у добавки без g нет блока «История цены»"
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # F: сравнение — колонка «₽ за единицу эффекта» вместо «Ценность»
            pg.select_option("#compareSelect1", label=cof["name"])
            pg.select_option("#compareSelect2", label="Креатин")
            pg.click("#compareBtn")
            cmp_txt = pg.locator("#compareResult").inner_text()
            assert "₽ за единицу эффекта" in cmp_txt, "в сравнении нет колонки стоимости эффекта"
            assert "Ценность" not in cmp_txt and "ценность" not in cmp_txt, \
                "в сравнении осталась «Ценность»"
            # ==================== конец v2.6.1 ====================

            # ==================== v2.6.2: UI-фиксы ====================

            # F1.3: JS-рендер tĩnh строки (не из HTML) — «цена не найдена» из script.js
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            assert "цена не найдена" in pg.content(), \
                "F1.3: JS-строка «цена не найдена» не рендерится (.encoding?)"

            # F2.3: категория «Спорт» — графики уважают фильтры
            n_sport = sum(1 for s in data if s.get("category") == "Спорт")
            n_sport_ma = sum(1 for s in data if s.get("category") == "Спорт" and (s.get("metaCount") or 0) > 0)
            n_sport_price = sum(1 for s in data if s.get("category") == "Спорт" and s.get("price") is not None)
            pg.locator("#categoryFilter").select_option(label="Спорт")
            pg.wait_for_timeout(300)
            sport_cards = pg.locator(".card[data-id]").count()
            assert sport_cards == n_sport, f"F2.3: карточек «Спорт» {sport_cards}, ожидалось {n_sport}"
            # пузырей на оси МА = спортивных с metaCount>0
            sport_bubbles_ma = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert sport_bubbles_ma == n_sport_ma, \
                f"F2.3: пузырей МА «Спорт» {sport_bubbles_ma}, ожидалось {n_sport_ma}"
            # переключить на цену → пузырей = спортивных с ценой
            pg.click("#axisPrice")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_sport_price), timeout=5000)
            sport_bubbles_price = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert sport_bubbles_price == n_sport_price, \
                f"F2.3: пузырей цена «Спорт» {sport_bubbles_price}, ожидалось {n_sport_price}"
            # подпись под чартом
            summary = pg.locator("#chartSummary").inner_text()
            assert f"показано {n_sport} из {n_all}" in summary, \
                f"F2.2: подпись чарта не совпадает: {summary!r}"
            # сброс фильтра
            pg.locator("#categoryFilter").select_option(index=0)
            pg.wait_for_timeout(200)

            # F4.3: радар — значения ∈ [0,100]
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            # открыть секцию сравнения, чтобы радар отрендерился
            pg.select_option("#compareSelect1", label="Кофеин")
            pg.select_option("#compareSelect2", label="Креатин")
            pg.click("#compareBtn")
            pg.wait_for_function("window.radarInstance != null", timeout=5000)
            radar_vals = pg.evaluate("""() => {
                const ds = window.radarInstance.data.datasets;
                return ds.flatMap(d => d.data);
            }""")
            assert all(0 <= v <= 100 for v in radar_vals), \
                f"F4.3: радар значения вне [0,100]: {[round(v,1) for v in radar_vals if v < 0 or v > 100]}"
            # подпись осей содержит «нормировано по базе»
            labels_text = pg.evaluate("window.radarInstance.data.labels.join(' ')")
            assert "нормировано по базе" in labels_text, \
                f"F4.3: нет подписи «нормировано по базе» на осях: {labels_text!r}"

            # F5.4: высота секции доверия #trustSummary ≤ 40% прежней
            OLD_TRUST_HEIGHT = 223.5   # измерено на main (9acbd6a) playwright 1280×900
            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#cardsGrid .card", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            trust_h = pg.locator("#trustSummary").bounding_box()["height"]
            assert trust_h <= 0.40 * OLD_TRUST_HEIGHT + 10, \
                f"F5.4: высота #trustSummary {trust_h:.1f}px > 40% ({0.40*OLD_TRUST_HEIGHT:.1f}px) прежней {OLD_TRUST_HEIGHT}px"

            # F3.2: ссылки в обеих темах ≥4.5:1 (проверка через getComputedStyle)
            def _contrast_hex(c1, c2):
                import math
                def _srgb(x):
                    x /= 255
                    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
                def _lum(r, g, b):
                    return 0.2126 * _srgb(r) + 0.7152 * _srgb(g) + 0.0722 * _srgb(b)
                def _parse(c):
                    c = c.strip()
                    if c.startswith("#"):
                        c = c[1:]
                        if len(c) == 3:
                            c = c[0]*2 + c[1]*2 + c[2]*2
                        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                    if c.startswith("rgb"):
                        inner = c.replace("rgba", "").replace("rgb", "").rstrip(")")
                        parts = [p.strip() for p in inner.replace("(", "").split(",")][:3]
                        return int(parts[0]), int(parts[1]), int(parts[2])
                    return 128, 128, 128
                r1, g1, b1 = _parse(c1)
                r2, g2, b2 = _parse(c2)
                L1, L2 = _lum(r1, g1, b1), _lum(r2, g2, b2)
                if L1 < L2:
                    L1, L2 = L2, L1
                return (L1 + 0.05) / (L2 + 0.05)

            # deferred to ui_verify for thorough multi-element check; quick smoke:
            for theme in ["light", "dark"]:
                pg.evaluate(f"localStorage.setItem('theme', '{theme}')")
                pg.wait_for_timeout(100)
                ts_theme = int(time.time())
                pg.goto(f"{BASE}/index.html?ts={ts_theme}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
                pg.wait_for_timeout(400)  # переждать transition:background .25s
                res = pg.evaluate("""() => {
                    function fg_bg(sel) {
                        const el = document.querySelector(sel);
                        if (!el) return null;
                        const s = getComputedStyle(el);
                        let bg = s.backgroundColor, node = el;
                        while ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && node.parentElement) {
                            node = node.parentElement;
                            bg = getComputedStyle(node).backgroundColor;
                        }
                        return {fg: s.color, bg: bg};
                    }
                    return {
                        methodology: fg_bg('footer a[href="methodology.html"]'),
                        qaMore: fg_bg('.qaMore'),
                        chip: fg_bg('.trustChips .chip'),
                    };
                }""")
                for name, pair in res.items():
                    if pair:
                        ratio = _contrast_hex(pair["fg"], pair["bg"])
                        assert ratio >= 4.5, \
                            f"F3.2 [{theme}] {name}: контраст {ratio:.1f}:1 < 4.5:1 (fg={pair['fg']}, bg={pair['bg']})"

            # ==================== конец v2.6.2 ====================

            assert not errors, f"ошибки консоли: {errors}"

            # v2.7.1: статическая строка титула в content (задача 3.2)
            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            assert "что работает, а что нет" in pg.content(), "v2.7.1: title missing"
            ts += 1

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

# === PART A tracker ===
            # A2: кнопка «📅 В мой курс» появляется в модалке
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Омега-3']", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            pg.click(".card[data-id='Омега-3']")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_selector("[data-tracker-btn]", state="attached", timeout=3000)
            btn = pg.locator("[data-tracker-btn]")
            assert btn.count() == 1, "кнопка «В мой курс» не появилась в модалке"
            assert "В мой курс" in btn.inner_text(), f"текст кнопки: {btn.inner_text()!r}"
            # Приватность-пометка
            assert "только в вашем браузере" in pg.locator("#modalBody").inner_text(), \
                "нет приватность-пометки под кнопкой"

            # A2: добавляем курс → прогресс обновляется
            btn.click()
            pg.wait_for_timeout(300)
            assert "В курсе" in btn.inner_text(), f"кнопка не обновилась: {btn.inner_text()!r}"
            assert "1/" in btn.inner_text(), f"прогресс не 1/N: {btn.inner_text()!r}"
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # A3: секция «Мои добавки» появилась на главной
            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#myCoursesSection", state="attached", timeout=5000)
            sec = pg.locator("#myCoursesSection")
            assert sec.is_visible(), "секция «Мои добавки» скрыта"
            assert "Омега-3" in sec.inner_text(), "Омега-3 нет в секции «Мои добавки»"
            assert "1/30" in sec.inner_text(), f"прогресс не 1/30: {sec.inner_text()!r}"

            # A3: кнопка «+ Принял» → прогресс 2/30
            pg.click("[data-tracker-take='Омега-3']")
            pg.wait_for_timeout(300)
            assert "2/30" in sec.inner_text(), f"прогресс не 2/30: {sec.inner_text()!r}"

            # A3: кнопка «убрать» → секция пуста
            pg.click("[data-tracker-remove='Омега-3']")
            pg.wait_for_timeout(300)
            assert not sec.is_visible(), "секция не скрыта после удаления курса"

            # A1: localStorage-гард — вставляем битые данные → console.warn + сброс
            pg.evaluate("""() => {
                localStorage.setItem('myCourse', JSON.stringify({
                    'bad': { 'start': 'not-a-date', 'days': 30, 'taken': [], 'note': '' },
                    'good': { 'start': '2025-09-14T00:00:00.000Z', 'days': 30, 'taken': ['2025-09-14'], 'note': '' }
                }));
            }""")
            warn_logs = []
            pg.on("console", lambda m: warn_logs.append(m.text) if m.type == "warning" else None)
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_timeout(500)
            # Битый ключ должен быть сброшен, good — сохранён
            stored = pg.evaluate("JSON.parse(localStorage.getItem('myCourse') || '{}')")
            assert "bad" not in stored, "битый ключ 'bad' не был удалён гардом"
            assert "good" in stored, "валидный ключ 'good' был удалён"

# === PART B pwa ===
            # B5/B4: manifest в head + SW регистрируется; ждём claim() на первой странице
            ts += 1; pg.goto(f"{BASE}/index.html", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            mlink = pg.locator("link[rel='manifest']").get_attribute("href")
            assert mlink and mlink.endswith("manifest.webmanifest"), f"нет link manifest: {mlink!r}"
            pg.wait_for_function(
                "() => navigator.serviceWorker && navigator.serviceWorker.controller !== null",
                timeout=10000
            )
            assert pg.evaluate("navigator.serviceWorker.controller !== null"), \
                "SW не управляет страницей (controller === null)"
            # контролируемый reload ?ts= — data.json пойдёт через SW (network-first → кэш v27-data)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            assert pg.evaluate("navigator.serviceWorker.controller !== null"), \
                "контролируемый reload: controller === null — данные пойдут мимо SW"
            # ждём, пока network-first добьёт data.json в кэш (иначе офлайн-фолбэк плавает)
            pg.wait_for_function(
                """() => caches.open('v27-data')
                       .then(c => c.keys())
                       .then(ks => ks.some(r => r.url.endsWith('/data.json')))""",
                timeout=8000,
            )

            # B3: офлайн-фолбэк data.json — reload в том же контексте (SW per-origin)
            errors.clear()
            pg.context.set_offline(True)
            try:
                pg.reload(wait_until="domcontentloaded")
                pg.wait_for_selector("#pwaOfflineBadge", state="attached", timeout=8000)
                assert pg.locator("#pwaOfflineBadge").count() == 1, "нет бейджа «офлайн-режим»"
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=8000)
                n_off = pg.locator(".card[data-id]").count()
                assert n_off == n_all, f"офлайн карточек {n_off}, ожидалось {n_all} (кэш data.json)"
                assert "Офлайн-режим" in pg.locator("#pwaOfflineBadge").inner_text()
            finally:
                pg.context.set_offline(False)
                pg.wait_for_timeout(1500)
                ts += 1
                pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
                pg.wait_for_selector(".card[data-id]", state="attached", timeout=10000)
                pg.wait_for_function("window.chart != null", timeout=10000)
                pg.wait_for_timeout(300)
                assert pg.locator("#pwaOfflineBadge").count() == 0, "бейдж не скрылся после online"
                errors.clear()
            # ==================== конец PART B pwa ====================

            # === PART C timeline (пульс науки + спарклайн) ===
            # C3: график «Пульс науки» рендерит >0 точек из data_ma_timeline.json
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#maTimelineBox", state="attached", timeout=5000)
            pg.wait_for_function(
                "() => window.maPulseData && window.maPulseData.years.length > 0",
                timeout=5000
            )
            pd = pg.evaluate("window.maPulseData")
            assert pd and len(pd["years"]) == 12, \
                f"Пульс науки: годы {pd and pd.get('years')}, ожидалось 12"
            assert all(t > 0 for t in pd["totals"]), "Пульс науки: есть total=0"
            n_points = pg.evaluate(
                "Chart.getChart('maTimelineCanvas')?.data?.datasets?.[0]?.data?.length ?? 0"
            )
            assert n_points == 12, f"Chart.js точек {n_points}, ожидалось 12"

            # C4: спарклайн — честный фолбэк при пустой истории price
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_selector("#ecoSpark", state="attached", timeout=5000)
            spark = pg.locator("#ecoSpark")
            txt = spark.inner_text()
            assert "история копится с v2.1" in txt, f"нет фолбэк-текста спарклайна: {txt!r}"
            assert spark.get_attribute("data-state") == "fallback", \
                f"спарклайн не в state=fallback: {spark.get_attribute('data-state')!r}"
            pg.keyboard.press("Escape")

            # ==================== конец PART C timeline ====================

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("e2e smoke: OK")


if __name__ == "__main__":
    main()
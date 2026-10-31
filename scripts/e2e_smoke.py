"""e2e-smoke (слой L4): сайт отдаёт то, что обещает data.json."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS = Path(__file__).resolve().parents[1] / "docs"
BASE = "http://localhost:8123"


def open_modal(pg, sid: str, ts: int) -> None:
    """Открыть модалку добавки по диплинку #sup=<id>.

    v5.6.5: клик по карточке больше не открывает модалку — он ведёт на
    sup/<id>.html (docs/script.js:803-807). Модалка открывается только
    через hash #sup=, который разбирает initApp (docs/script.js:469-470).
    """
    pg.goto(f"{BASE}/index.html?ts={ts}#sup={sid}", wait_until="domcontentloaded")
    pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)


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
            # FIX-77: в статической разметке index.html лежат 3 карточки-заглушки
            # (они видны до гидратации датасета), поэтому мгновенный подсчёт
            # ловил их, а не реальную выдачу. Ждём, пока грид дорендерится, и
            # считаем только после этого.
            pg.wait_for_function(
                "n => document.querySelectorAll('#cardsGrid .card').length === n",
                arg=n_all, timeout=15000)
            cards = pg.locator("#cardsGrid .card").count()            # ALIGN-селектор
            assert cards == n_all, f"карточек {cards}, ожидалось {n_all}"
            # После проверки данных:
            assert "Как мы проверяем" in pg.content() or "Открытые данные" in pg.content(), \
                "Статическая строка UTF-8 не рендерится (кракозябры?)"
            n_ma = sum(1 for s in data if (s.get("metaCount") or 0) > 0)
            # ось «Число РКИ» = scienceIndex - 5 × metaCount, рисуется если > 0
            # (docs/script.js:857 axisVal, ветка 'rct')
            n_rct = sum(1 for s in data
                        if max(0, (s.get("scienceIndex") or 0) - 5 * (s.get("metaCount") or 0)) > 0)
            # v2.6: дефолтная ось графика — «Число МА»
            bubbles = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert bubbles == n_ma, f"пузырей (ось=МА) {bubbles}, ожидалось {n_ma}"
            # оси X только МА/РКИ (docs/index.html:347-348), «Цена» удалена как мёртвая
            pg.click("#axisRCT")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_rct), timeout=5000)
            pg.click("#axisMA")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_ma), timeout=5000)
            # v2.3: 3 вопроса в DOM
            qa = pg.locator("#qaSection .qa").count()
            assert qa == 3, f"секция «3 вопроса»: блоков {qa}, ожидалось 3"
            assert pg.locator("#qaSection").inner_text(), "секция «3 вопроса» пуста"

            # v2.3: блоки полной карточки + заглушка пустых блоков.
            # 14, а не 15: блок «Цена» удалён в 883a53c (M9, 2026-09-17) —
            # CARD_GROUPS в docs/script.js даёт what/who/works/evidence +
            # how/onset + notwho/conflicts/friends/ul + food/official/shop/myths.
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Фосфатидилсерин", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            nblocks = pg.locator("#modalBody .cblock").count()
            assert nblocks == 14, f"блоков полной карточки {nblocks}, ожидалось 14"
            assert pg.locator("#modalBody .cbEmpty").count() > 0, "нет заглушки «данных пока нет — проверяем»"

            # v2.3: зелёная подсказка «хорошая пара» в модалке Магния (магний+B6)
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function("document.getElementById('modalBody').innerText.includes('Хорошая пара')", timeout=5000)
            friends = pg.locator('[data-block-key="friends"]').inner_text()
            assert "Витамин B6" in friends, "зелёная подсказка магний+B6 не найдена"
            assert "Хорошая пара" in friends, "нет подписи «Хорошая пара»"

                       # ==================== v2.3.1: контент топ-10 ====================
            # У Креатина 8 edu-блоков заполнены (без заглушки и без пустот)
            ts += 1
            pg.goto(f"{BASE}/index.html?ts={ts}#sup=Креатин", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.wait_for_function(
                "document.getElementById('modalBody').innerText.includes('Самая изученная спортивная добавка')",
                timeout=5000,
            )

            # Усиление A: в DOM вообще присутствует минимум 8 edu-блоков
            edu_keys = ["what", "who", "onset", "ul", "food", "official", "shop", "myths"]
            edu_total = pg.locator("[data-block-key]").count()
            assert edu_total >= len(edu_keys), (
                f"edu-блоков меньше {len(edu_keys)}: найдено {edu_total}"
            )

            # Усиление B: каждый блок не заглушка и не пустой div с пробелами
            for k in edu_keys:
                txt = pg.locator(f'[data-block-key="{k}"]').inner_text().strip()
                assert "данных пока нет" not in txt, (
                    f"edu-блок {k!r} Креатина остался заглушкой"
                )
                assert len(txt) >= 10, (
                    f"edu-блок {k!r} подозрительно короткий: {len(txt)} симв."
                )

            # v2.3: живой баннер medium на кальций+железо в favs
            pg.evaluate("localStorage.setItem('favs', JSON.stringify(['Кальций','Железо']))")
            pg.reload(wait_until="domcontentloaded")
            pg.wait_for_selector(".banner.medium", state="visible", timeout=5000)
            med = pg.locator(".banner.medium")
            assert med.count() == 1, "баннер medium не появился на кальций+железо"
            assert "конкурируют за всасывание" in med.inner_text(), "текст medium-баннера не тот"

            # v2.4: вкладка «Квадрант доказательности» рендерит (или честная заглушка).
            # v5.6.5: id #tabQuadrant в разметке нет — вкладки графика это
            # .chartTab[data-view] внутри #viewTabs (docs/index.html:480-483).
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector('.chartTab[data-view="quadrant"]', state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            n_verified = sum(1 for s in data if s.get("hedges_g") is not None)
            pg.click('.chartTab[data-view="quadrant"]')
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
                ts += 1; open_modal(pg, first["id"], ts)
                assert pg.locator("#modalBody .grade").count() >= 1, "грейд не в модалке"
                assert first["grade"] in pg.locator("#modalBody").inner_text(), "буква грейда не в модалке"

            # v5.6.5 (A-1.1): «Карта механизмов» закрыта — страница стала
            # редиректом на hactar.html?tab=graph (механизмы живут во
            # вкладке «Связи» Project Hactar). Прежняя проверка цепочки
            # «вещество → мишень → эффект» (#chain на map.html) здесь
            # больше неуместна: элемента #chain на странице больше нет.
            pg.goto(f"{BASE}/map.html?supplement=Эхинацея", wait_until="domcontentloaded")
            pg.wait_for_function("() => location.search.includes('tab=graph')", timeout=8000)
            assert "hactar.html" in pg.url and "tab=graph" in pg.url, \
                "map.html должен редиректить на hactar.html?tab=graph (A-1.1)"
            # конечная страница открылась на вкладке «Связи»
            assert pg.locator("#hactarTabLinks[aria-selected='true']").count() == 1, \
                "после редиректа map.html активна не вкладка «Связи»"
            pg.wait_for_selector("#hactarPanelLinks.active", state="visible", timeout=5000)

            # ==================== v2.6: trust visuals ====================
            FILL = {"A": 4, "B": 3, "C": 2, "D": 1}
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Кофеин']", state="attached", timeout=5000)
            cof = next(s for s in data if s["id"] == "Кофеин")

            # B: грейд-бейдж в карточке соответствует data.json.
            # v5.6.5: точек грейда (.gdots) в вёрстке больше нет — они удалены
            # в 883a53c (M9) вместе с ценой, вместо них бейдж .grade.gX
            # (docs/script.js:99-102). Прежние константы (3 точки / «ждёт
            # верификации» у Креатина) стали ложными: Кофеин теперь грейд A,
            # а Креатин получил hedges_g.
            assert pg.locator(".card[data-id='Кофеин'] .grade").count() == 1
            assert pg.locator(".card[data-id='Кофеин'] .grade.g" + cof["grade"]).count() == 1
            no_g = next(s for s in data if s.get("hedges_g") is None)
            assert pg.locator(f".card[data-id='{no_g['id']}'] .gBadge").count() == 0, \
                "у добавки без hedges_g не должно быть бейджа g"

            # D: «Обновлено» + «ручная вычитка» на карточке.
            # Дата берётся из docs/version.json (window.APP_VERSION.data), а не
            # из поля updated записи — так в updatedLine (docs/script.js).
            data_date = __import__("json").loads((DOCS / "version.json").read_text(encoding="utf-8"))["data"]
            assert "Обновлено: " + data_date in pg.locator(".card[data-id='Кофеин']").inner_text()
            assert "ручная вычитка" in pg.locator(".card[data-id='Кофеин']").inner_text()

            # C: оси X — кнопки есть, переключение перерисовывает без reload
            for a in ["MA", "RCT"]:
                assert pg.locator("#axis" + a).count() == 1, f"нет кнопки оси #axis{a}"
            assert pg.locator("#axisRow button").count() == 2, \
                "в #axisRow не ровно 2 оси — набор разъехался с docs/index.html"
            pg.click("#axisRCT")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_rct), timeout=5000)
            pg.click("#axisMA")
            pg.wait_for_function("window.chart?.data?.datasets.length === " + str(n_ma), timeout=5000)

            # модалка Кофеина: бейдж грейда, иконки источников (честно: цена без иконки — price_source пуст у всех)
            ts += 1; open_modal(pg, "Кофеин", ts)
            assert pg.locator("#modalBody .grade.g" + cof["grade"]).count() >= 1, \
                "в модалке нет бейджа грейда " + cof["grade"]
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

            # A5: кнопка неточности в модалке; чип сравнения ведёт в сравнение.
            # v5.6.5 (H-1): секции #compareSection на главной больше нет —
            # gotoCompare (docs/script.js:1267) уводит на hactar.html?tab=compare.
            assert pg.locator("#modalBody a[href*='issues/new']").count() == 1
            if exp_chips:
                pg.click(".compareChips .chipbx >> nth=0")
                pg.wait_for_function(
                    "() => location.pathname.endsWith('/hactar.html')"
                    " && location.search.includes('ids=')", timeout=8000)
                from urllib.parse import unquote
                # hactar.js нормализует tab=compare в tab=overview (закладки
                # сравнения там ещё нет), но пара ids доезжает — её и проверяем.
                assert "Кофеин" in unquote(pg.url), \
                    f"чип сравнения не передал добавку в URL: {unquote(pg.url)}"
                # возвращаемся в модалку, чтобы проверить закрытие по Escape
                ts += 1
                pg.goto(f"{BASE}/index.html?ts={ts}#sup=Кофеин", wait_until="domcontentloaded")
                pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector("#trustSummary", state="attached", timeout=5000)
            assert pg.locator(".trustbar").count() == 1 and "Открытые данные" in pg.locator(".trustbar").inner_text()
            assert pg.locator("#trustSummary").count() == 1 and "Как мы проверяем данные" in pg.locator("#trustSummary").inner_text()
            # v5.6.5 (A-1.1): map.html — редирект на hactar.html?tab=graph,
            # trustbar проверяем на конечной странице (у hactar.html он
            # свой, в .site-header).
            pg.goto(f"{BASE}/map.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_function("() => location.search.includes('tab=graph')", timeout=8000)
            assert "hactar.html" in pg.url, "map.html должен редиректить на hactar.html?tab=graph (A-1.1)"
            assert "Открытые данные" in pg.locator(".trustbar").inner_text()

            # ==================== конец v2.6 ====================

            # ==================== v2.6.1: economics ====================
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Кофеин']", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)

            # A: карточка больше не рисует «ценность»-блоки
            assert "ценность" not in pg.locator(".card[data-id='Кофеин']").inner_text()

            # B: экономика-блок и «История цены» демонтированы полностью.
            # v5.6.5: элемента #ecoSpark и текста «История цены» в коде больше
            # нет вообще (docs/script.js не содержит ни одного вхождения),
            # поэтому ждать их бессмысленно. Проверяем фактическое состояние.
            ts += 1; open_modal(pg, "Кофеин", ts)
            body = pg.locator("#modalBody").inner_text()
            assert "История цены" not in body, "блок «История цены» вернулся в модалку"
            assert pg.locator("#modalBody #ecoSpark").count() == 0, "#ecoSpark вернулся в модалку"
            assert "ЭКОНОМИКА" not in body and "₽ за единицу эффекта" not in body, \
                "экономика-блок не демонтирован (v2.7.1)"
            assert "ценност" not in body, "в модалке осталась «ценность»"

            # C: тултип цены (priceTip) демонтирован вместе с экономика-блоком
            assert pg.locator("#modalBody .priceTip").count() == 0, "priceTip остался в модалке"

            # D: блок источников (топ-3) — заголовок зависит от того, ручной
            # набор или автотоп. v5.6.5: текст «Ключевые мета-анализы» и
            # пометка «верифицированных добавок сейчас: N» заменены в i18n
            # на sources.curatedTitle / sources.autoTitle и
            # sources.curatedNote / sources.autoNote (docs/i18n.js:93-96).
            curated = bool(cof.get("key_sources"))
            title = "Проверенные источники (топ-3)" if curated else "Мета-анализы (топ-3 авто-поиска)"
            assert title in body, f"нет блока источников {title!r}"
            assert pg.locator("#modalBody a[href*='pubmed.ncbi.nlm.nih.gov/']").count() >= 1, \
                "нет ссылок на PubMed в топ-3"
            if curated:
                assert "Отобраны вручную по топ-2 МА" in body, "нет пометки о ручном отборе"
            else:
                note = f"верифицировано сейчас: {sum(1 for s in data if s.get('key_sources'))} из {n_all}"
                assert note in body, f"нет пометки автотопа: {note!r}"

            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # E: Креатин — экономика-блок демонтирован, «Истории цены» нет
            ts += 1; open_modal(pg, "Креатин", ts)
            kb = pg.locator("#modalBody").inner_text()
            assert "Эффект ждёт верификации" not in kb, "у добавки без g осталась экономика-причина"
            assert "История цены" not in kb, "блок «История цены» вернулся в модалку"
            pg.keyboard.press("Escape")
            pg.wait_for_selector("#modalOverlay", state="hidden", timeout=5000)

            # F: сравнение теперь на hactar.html (H-1, редирект);
            # функционал сравнения будет добавлен позже. compare.html
            # редиректит на hactar.html.
            pg.goto(f"{BASE}/compare.html", wait_until="domcontentloaded")
            pg.wait_for_timeout(1000)
            assert "hactar.html" in pg.url, "compare.html должен редиректить на hactar.html (H-1)"
            # ==================== конец v2.6.1 ====================

            # ==================== v2.6.2: UI-фиксы ====================

            # F1.3: JS-строка с кириллицей рендерится (не кракозябры).
            # v5.6.5: «цена не найдена» удалена вместе с ценой — берём другую
            # JS-строку из i18n: счётчик фильтра t("filter.count") =
            # "({shown} из {total})", рендерится в #countBadge.
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id]", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            badge_txt = pg.locator("#countBadge").inner_text()
            assert f"({n_all} из {n_all})" in badge_txt, \
                f"F1.3: JS-строка счётчика не рендерится по-русски: {badge_txt!r}"

            # F2.3: чип «Мышцы / спорт» — графики уважают фильтры
            import json as _json
            _tags = _json.loads((DOCS / "effect_tags.json").read_text(encoding="utf-8"))
            _muscle_ids = {cid for cid, tags in _tags.items() if "muscle" in tags}
            n_sport = sum(1 for s in data if s.get("id") in _muscle_ids)
            n_sport_ma = sum(1 for s in data if s.get("id") in _muscle_ids and (s.get("metaCount") or 0) > 0)
            n_sport_plot = sum(1 for s in data if s.get("id") in _muscle_ids and s.get("scienceIndex") is not None)
            pg.locator('.tagPreset[data-tag="muscle"]').click()
            pg.wait_for_timeout(300)
            sport_cards = pg.locator(".card[data-id]").count()
            assert sport_cards == n_sport, f"F2.3: карточек 'muscle' {sport_cards}, ожидалось {n_sport}"
            # пузырей на оси МА = спортивных с metaCount>0
            sport_bubbles_ma = pg.evaluate("window.chart?.data?.datasets?.length ?? -1")
            assert sport_bubbles_ma == n_sport_ma, \
                f"F2.3: пузырей МА «Спорт» {sport_bubbles_ma}, ожидалось {n_sport_ma}"
            # подпись под чартом
            summary = pg.locator("#chartSummary").inner_text()
            assert f"показано {n_sport} из {n_all}" in summary, \
                f"F2.2: подпись чарта не совпадает: {summary!r}"
            # сброс фильтра
            pg.locator('.tagPreset[data-tag="all"]').click()
            pg.wait_for_timeout(200)

            # F4.3: радар был на compare.html, теперь compare.html редиректит
            # на hactar.html (H-1). Проверка радара будет добавлена вместе
            # с функционалом сравнения.

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

            # v2.7.1: статическая строка титула в content (задача 3.2).
            # v5.6.5 (QA-02, FIX-04): MK2-06 (794992c5) заменил заголовок на
            # «Независимая база БАДов: доказательства, а не маркетинг»
            # (docs/index.html:310) — проверяем актуальный h1.
            pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            assert "Независимая база БАДов: доказательства, а не маркетинг" in pg.locator("h1").inner_text(), \
                "QA-02: h1 не совпадает с заголовком docs/index.html:310"
            ts += 1

            # v2.5: faq/glossary рендерятся, футер-ссылки на них живые.
            # v5.6.5: changelog_public.html удалён из docs/ (страницы нет
            # и никто на неё не ссылается) — из списка убран. h1 глоссария
            # называется «Термины доказательной медицины».
            for sub in ["faq", "glossary"]:
                # v5.6.5 (A-1.1): map.html больше не самостоятельная страница
                # (редирект на hactar.html?tab=graph) — футерные ссылки
                # проверяем на конечной странице hactar.html.
                for page in ["index.html", "hactar.html"]:
                    pg.goto(f"{BASE}/{page}?ts={ts}", wait_until="domcontentloaded")
                    page_html = pg.content()
                    assert f'href="{sub}.html"' in page_html, f"{page} не ссылается на {sub}.html"
                ts += 1
                pg.goto(f"{BASE}/{sub}.html?ts={ts}", wait_until="domcontentloaded")
                if sub == "faq":
                    # v5.6.5: аккордеонов стало 12 (было 8) — FAQ расширен.
                    n_qa = pg.locator("details.qa").count()
                    assert n_qa == 12, f"faq: аккордеонов {n_qa}, ожидалось 12"
                else:
                    assert "Термины доказательной медицины" in pg.locator("h1").inner_text(), \
                        "glossary: нет h1"

# === PART A tracker ===
            # A2: кнопка «📅 В мой курс» появляется в модалке
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".card[data-id='Омега-3']", state="attached", timeout=5000)
            pg.wait_for_function("window.chart != null", timeout=5000)
            ts += 1; open_modal(pg, "Омега-3", ts)
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

            # C4: спарклайн цены демонтирован вместе с экономика-блоком —
            # #ecoSpark в коде нет вообще (0 вхождений в docs/script.js).
            ts += 1; pg.goto(f"{BASE}/index.html?ts={ts}#sup=Магний", wait_until="domcontentloaded")
            pg.wait_for_selector("#modalOverlay", state="visible", timeout=5000)
            assert pg.locator("#ecoSpark").count() == 0, "#ecoSpark вернулся в модалку"
            assert "история копится с v2.1" not in pg.locator("#modalBody").inner_text(), \
                "вернулся фолбэк-текст спарклайна"
            pg.keyboard.press("Escape")

            # ==================== конец PART C timeline ====================

            # === v2.7.1 chunk 3: иерархия заголовков блоков ===
            # v5.6.5: блока price в карточке больше нет (883a53c), поэтому
            # сравнивать «наука ≥1.2× цена» не с чем. Проверяем, что заголовки
            # блоков рендерятся и заголовок evidence крупнее обычного h4.
            ts += 1; open_modal(pg, "Кофеин", ts)
            fs = pg.evaluate("""(() => {
              const g = k => {
                const el = document.querySelector('#modalBody .cblock[data-block-key="' + k + '"] h4');
                const f = el ? parseFloat(getComputedStyle(el).fontSize) : NaN;
                return f;
              };
              return [g('evidence'), g('how')];
            })()""")
            assert len(fs) == 2 and fs[0] > 0 and fs[1] > 0, \
                f"иерархия: не найдены h4 блоков evidence/how: {fs}"
            assert pg.locator("#modalBody .cblock[data-block-key='price']").count() == 0, \
                "блок price вернулся в карточку"
            # «Для врачей» в футере index и Hactar. v5.6.5: страницы
            # for_doctors.html в docs/ нет и ссылки на неё нет — проверяем
            # фактическое отсутствие (регрессия — если ссылка вернётся без страницы).
            assert pg.locator("footer a[href='for_doctors.html']").count() == 0, \
                "в футере index.html есть ссылка на несуществующую for_doctors.html"
            pg.keyboard.press("Escape")
            # v5.6.5 (A-1.1): map.html стал редиректом на hactar.html?tab=graph —
            # футер конечной страницы проверяем там.
            pg.goto(f"{BASE}/hactar.html?ts={ts}", wait_until="domcontentloaded")
            pg.wait_for_selector(".hactar-tabs [role='tab']", state="attached", timeout=5000)
            assert pg.locator("footer a[href='for_doctors.html']").count() == 0, \
                "в футере hactar.html есть ссылка на несуществующую for_doctors.html"

            assert not errors, f"ошибки консоли: {errors}"
            b.close()
    finally:
        srv.terminate()
    print("e2e smoke: OK")


if __name__ == "__main__":
    main()
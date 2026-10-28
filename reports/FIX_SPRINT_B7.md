# FIX-SPRINT B7 — финальный блок: упрощение навбара, хаб навигации, фокус графа, маркетинг, 404

Автор: сессия FIX-SPRINT block 7 · 2026-10-20 · ветка `v5.6.5-dev`

## Цель

Задача task: свести навигацию сайта к четырём элементам шапки, собрать
навигационный хаб на главной, довести фокус графа до продуктового уровня
(центрирование + подсветка + читаемые подписи), добавить маркетинговый блок
(CTA + цифры доверия + «где купить»), и завести страницу 404 для GitHub Pages.

## Данные

- `docs/index.html`: строка цифр `#heroStats` (130 добавок · 37 618 научных
  статей · 199 взаимодействий, числа сверены с `whoTrust`-секцией и
  duckdb), CTA-строка `.heroCta` («🎯 Подобрать добавку» →
  `a.btn.calc[href="#cardsContainer"]`, обработчик script.js 363-388 даёт
  плавную прокрутку с фокусом с учётом `prefers-reduced-motion`; «⚖ Сравнить
  3+ добавки» → `compare.html`).
- Хаб `.quick-links` — теперь 5 карточек; «Сравнение добавок» (O-04)
  без нового CSS-класса: акцент и заливка инлайном
  (`--card-accent:#a855f7` + пара стопов), `style.css` не бампался.
- 10 плиток «Популярные добавки» переставлены из `a.tile` в `div.tile`
  с внутренней ссылкой-обёрткой (вложенные `<a>` невалидны) и двумя
  reference-ссылками «🛒 Ozon / 🛒 WB» (URL-encoded поисковые URL,
  `target=_blank rel="noopener nofollow"`, `aria-label`+`title`).
- Ссылки «где купить» — словарь `i18n.js` (`shop.ozon` / `shop.wb`) не
  задействован: плитки статические, без JS.

## Навбар

- Со всех страниц удалены кнопки `c-calc · c-trends · c-links ·
  c-compare · c-map · c-bi · c-faq · c-home` (1153 строки в 145 файлах:
  12 корневых контентных + 131 sup + 2 шаблона `templates/*.j2`; atlas.html
  и graph.html — редиректы без навбара, offline.html — автономная) и
  6 индикаторов «текущей страницы» `<span class="btn c-*">` на 6 страницах.
- На `#randomBtn` добавлен `title="Удиви меня — случайная добавка"`
  (143 файла — там, где кнопка есть).
- Оставлено: «💬 Обратная связь», «💚 Поддержать», «🌞 Светлая тема»,
  «🎲 Удиви меня» (+ page-specific `#pngBtn` на interactions — был до B7).
- KNOWN_DEAD_CSS +5 (`c-calc, c-trends, c-links, c-bi, c-home`);
  `c-compare / c-map / c-faq` цветовых правил в `style.css` не имели —
  в аудит по CSS не попадают, записи не нужны.

## Граф (`interactions.html`)

- `pickPrimary(matching, query)`: точное совпадение имени → начало имени →
  первый из списка.
- `setFocusVisibility(focusNodes, dimmed, primaryId)`: primary не
  приглушается, рамка `borderWidth: 5`; узлы фокуса 0.85; внешние 0.2;
  сброс `borderWidth: 1` в `resetGraph`.
- `applyEdgeFilter`: локализованный текст ребра дублируется в `label`
  (подпись видна постоянно), плашка-фон `rgba(23,28,38,0.72)` для контраста
  в обеих темах.
- `applyFocus`: `network.focus(primary.id, {scale:0.9, animation 500ms
  easeInOutQuad})` с fallback на `fit({nodes})`.
- `ensureNetwork`: шрифт узлов vis default ~14 → 17.
- `resetGraph`: `borderWidth` сбрасывается, labels уходят вместе с
  `edgesDs.clear()`.
- Консоль чистая (0 ошибок; 1 deprecated-warning `apple-mobile-web-app-capable`
  — известный, вне B7).

## Документация

- `tests/test_no_orphan_classes.py`: `EXPECTED_PAGES` 147 → 148
  (+404.html), KNOWN_DEAD_CSS +5 c причиной по образцу записей блока 2.2.6.
- `tests/test_seo_meta_consistency.py`: `404.html` в `EXCLUDED_PAGES`
  (служебная страница, noindex) и `NO_JSONLD_PAGES`.
- `README.md`: «Страниц» 16 → 17 корневых (16 контентных + `404.html`),
  добавлена в список неиндексируемых.
- `CHANGELOG.md`: блок FIX-SPRINT B7 в v5.6.5 (Added/Changed).
- Отчёт батча: `reports/FIX_SPRINT_B7.md`.

## Инфраструктура

- `docs/404.html` (148-я страница): тёмная тема (дефолт style.css,
  `html` без `.light`), инлайн-переключатель темы по тому же
  соглашению `localStorage['theme']` (script.js не подключается),
  упрощённая шапка, поиск по каталогу: парс
  `sup/index.html` → карточки `#cardsGrid .card[href]` (name, slug,
  `data-hay` уже собраны build_sup.py — словарь в JS не дублируется),
  до 8 результатов, `aria-live`-подсказка; кубик из `sitemap.xml`;
  `disc`-дисклеймер для `test_legal_disclaimer.py`; `version.js` на борту;
  вне sitemap (ROOT_PAGES явный список, пополнений не требуется).
- Скриншоты: `reports/shots/b7_index_hero.png`,
  `b7_graph_kreatin_1280.png`, `b7_404.png`.

## Верификация

- Структурные тесты до полного прогона:
  `test_no_orphan_classes + test_seo_meta_consistency +
  test_style_version_bump` → 498 passed.
- Полный прогон `pytest -q`: см. секцию ниже.
- Навбар: 4 элемента в `nav.actions` на index / interactions / 404;
  JS-проверка в браузере: `hubCards=5, buyLinks=20, tiles=10`.
- Граф: поиск «креатин» → `dimmed=true`, canvas видим, Креатин
  центрирован (network.focus), консоль без ошибок.
- 404: поиск «сон» → 7 находок (Валериана, ГАБА, Глицин, Мелатонин,
  Мелисса, Пассифлора, Триптофан).
- Снапшоты: см. ниже.

Итоговый полный прогон и пересъёмка снапшотов:

- Полный `pytest -q`: **1982 passed, 1 warning, 525.93s (0:08:45)** —
  0 failed. (Warning — существующий UserWarning о 39 CSS-сиротах из
  `test_no_orphan_classes`, включает 5 задокументированных B7.)
- Снапшоты: `UPDATE_SNAPSHOTS=1 -m snapshots` → 76 passed (181s);
  повторный просмотр `RUN_SNAPSHOTS=1` → 76 passed (193s).
- a11y (axe): 73 passed.
- Итог: 1982 теста, 0 падений; version.json/README синхронизированы
  (tests=1982).

## Остаточное

- amount ссылок банка Ozon/WB — статические URL; i18n-перевод подписей
  «🛒 Ozon / 🛒 WB» не заводится (латиница в любой локали).
- `scale:0.9` в фокусе — абсолютный зум vis-network; для самых плотных
  хабов (Креатин, 52 связи) вид насыщенный, но подписи читаемы
  (17px узлы, 12px плашки рёбер). Если понадобится мягче — один параметр.
- Cookie-баннер (`index`, `404` подключают общий трекер? — нет: 404 не
  грузит tracker.js; баннер на 404 не показывается).
- service worker на GitHub Pages перехватывает несуществующие URL и
  отдаёт `offline.html` раньше, чем сработает 404-документ; это
  существующее поведение SW (cacheFirst), не предмет B7.

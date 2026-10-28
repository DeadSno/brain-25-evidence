# AUDIT MASTER v5.6.5

Ветка: `v5.6.5-dev` · HEAD: `ed6317f` · Рабочая директория: `C:\analytics\brain-25-evidence` (main checkout) · Дата: 19.10.2026.
Режим аудита 1–2/19: **только сбор, ничего не исправлено и не закоммичено**.

## Покрытие скилла site-navigation

- Источник истины: `.opencode/skills/site-navigation/SKILL.md` (v1.1, 2026-10-01).
- Проверок в скилле: **9**, выполнено: **9** (включая отчётную таблицу §5).
- Дополнительно проверено: **12** пунктов чеклиста задания.
- Метод: статический разбор всех 147 HTML + отрендеренный DOM всех 147 страниц в Playwright (Chromium), сервер `python -m http.server 8000 --directory docs`, мобильный вьюпорт 390×844, клавиатурная навигация, история браузера.

### Проверки SKILL.md

| # | Проверка скилла | Результат |
|---|---|---|
| 1 | Все 10 целевых страниц доступны из навигации (index, map, interactions, compare, calculator, methodology, faq, glossary, trends, feedback) | **FAIL.** Ни одна из 143 контентных страниц не содержит полного набора. `methodology.html` и `glossary.html` не входят в навигацию ни одной страницы (только футер). |
| 2 | `graph.html`/`atlas.html` — редиректы, не в навигации и не обязательны | **PASS.** Обе не в навигации; редиректы работают (см. доп. п.2). |
| 3 | На каждой HTML-странице `docs/` есть общий блок навигации | **PASS по наличию / FAIL по составу.** `<nav>` есть на 143/143 контентных страницах; 4 заглушки — разрешённые исключения (§4.5). |
| 4 | На всех страницах одинаковый набор ссылок | **FAIL.** Три разных набора: 131 sup-страница — 3 ссылки, 11 корневых — 10, `glossary.html` — 7. |
| 5 | Одинаковый порядок ссылок | **FAIL.** Наборы разные, порядок сравним только на общем подмножестве (`index → feedback → support` совпадает). |
| 6 | Нет битых ссылок (файлы существуют) | **FAIL.** Две динамические ссылки (`map.html`, `compare.html`) ведут на несуществующие файлы с кириллическим именем. |
| 7 | Нет дублей ссылок | **PASS.** 0 дублей в статике и в отрендеренном DOM. |
| 8 | Страницы без общего nav исключаются из правок (`graph`, `atlas`, `offline`, `google4a9…`, `feedback` при добавлении) | **PASS.** Соблюдено. |
| 9 | Отчётная таблица «Страница \| Есть nav \| Ссылок \| Статус» | **Выполнено**, см. §«Таблица по страницам» (адаптирована: добавлена причина статуса). |

### Дополнительные проверки (чеклист задания)

| # | Проверка | Результат |
|---|---|---|
| 1 | Единый набор ссылок навбара, нет дублей/пропусков, active state | Провал: 3 набора, 0 `aria-current` (находки 2, 4). |
| 2 | Редиректы `graph.html`/`atlas.html` | PASS: `atlas → interactions.html#mech`, `graph → interactions.html#graph`, оба через meta refresh + `location.replace`, конечный URL и панель верны. |
| 3 | Битые `href`/`src`, включая JS-сгенерированные | 0 статических битых; 2 динамических (находка 1). |
| 4 | Единый футер, живые ссылки | Ссылки живые, состав не единый (находка 7). |
| 5 | Перекрёстные ссылки popularGrid, sup↔sup, sup↔compare, map↔sup | popularGrid — 12/12 валидны; sup↔sup — 260 связей, у всех 131 sup-страниц ≥1 валидная; map↔sup и compare↔sup сломаны (находки 1, 3); sup→map и sup→compare — 0 ссылок. |
| 6 | Битые якоря `#mech`, `#sup=` после рендера | PASS: 0 битых; `#mech/#graph/#sups/#drugs` открывают панели, `index.html#sup=<id>` открывает модалку. |
| 7 | `sitemap.xml`: все URL → 200, сверка с диском | PASS: 143 URL, все 200; на диске нет файлов вне sitemap, кроме 4 намеренных noindex-заглушек (`graph`, `atlas`, `offline`, `google…`). |
| 8 | Хлебные крошки | Есть только на sup-страницах, на корневых нет; у `sup/index.html` усечённая цепочка (находка 10). |
| 9 | Мобильное меню | Бургер-меню в проекте нет; навигация — горизонтальный скроллер, 7 из 10 ссылок за экраном без визуального индикатора (находка 6). |
| 10 | Skip-to-content, клавиатурный порядок, external links | Skip-link есть на 145 страницах, но не переносит фокус (находка 9); внешние ссылки оформлены непоследовательно (находка 11); порядок табуляции естественный. |
| 11 | 404 | Кастомной страницы нет, сервер и GitHub Pages отдают дефолтную (находка 8). |
| 12 | Кнопка «назад»: табы/якоря | Табы теряются: `replaceState` не создаёт записей истории (находка 5). |

### Что не применимо и почему

- **Мобильное меню (п.9):** бургер/гамбургер в проекте отсутствует как механизм; проверялось фактическое поведение горизонтального скроллера на 390×844.
- **4 noindex-заглушки** (`graph.html`, `atlas.html`, `offline.html`, `google4a9d23e35c6c3e23.html`) законно не имеют nav и не входят в sitemap — это соответствует SKILL §4.5 и замыслу.
- **Расхождение инвентаря:** в задании указано 146 HTML, на диске **147** (16 корневых + 131 в `docs/sup/`). Дефектом не считается, зафиксировано для точности.

## Покрытие скилла visual-design-audit

- Источник истины: `.opencode/skills/visual-design-audit/SKILL.md` (v1.0, 2026-10-01, 249 строк).
- Проверок в скилле: **9 категорий** + 6 метрик. Выполнено: **9/9** категорий; метрики — 2 измерены, 4 «не измерено» (см. ниже, типовые числа не подставлялись).
- Дополнительно проверено: **12** пунктов чеклиста задания (все).
- Метод: отрендеренный DOM всех **147** страниц в Chromium (1440/768/375/320) и WebKit (6 страниц), обе темы; статический разбор `docs/style.css` (173 550 Б); контраст по WCAG 2.1 с композитом полупрозрачных фонов и отключёнными CSS-переходами (без этого тема даёт промежуточные цвета и ложные 1.0–3.0:1). Проверено **6 978** текстовых узлов в тёмной теме и **6 977** в светлой.

### Проверки SKILL.md

| # | Категория скилла | Результат |
|---|---|---|
| 1 | Цветокор: токены, палитра, семантика статусов, контраст бейджей, тёмная тема | **FAIL по контрасту (3 находки), PASS по палитре.** 145 токенов/105 имён; палитра 5–7 цветов на страницу (норма 8–12) — PASS. Бейджи grade 4.99–6.47:1, pmid 5.33 light / 9.83 dark, chip 5.33 / 9.83 — PASS. Провалены: `#cmpError` (3.67/4.26), placeholder (3.89), подписи узлов графа (2.03–2.78). Семантика статусов формой не дублируется — статус передаётся только цветом/текстом (находка 18). |
| 2 | Типографика: размеры, шкала, межстрочный, длина строки, ≥14px | **FAIL.** 25 объявленных font-size / 125 объявлений, 13 line-height; 143/147 страниц содержат текст <14px; длина строки 127–138 знаков на 8 страницах; h1 28px vs 24px vs 20.8px (находки 16–19). |
| 3 | Отступы: кратность 4px, шкала 4/8/16/24/32/48, единство компонентов | **FAIL.** padding 35 уник. (7 кратны 4), margin 14 (3), gap 11 (1). Сетки нет (находка 20). |
| 4 | Иерархия: монотонность H1–H6, главный CTA, один акцент | **FAIL.** h2 трёх видов, на `index.html` h2 (16px) меньше h3 (20px); пропуск h1→h3 на 5 страницах (находки 16, 29). |
| 5 | Дизайн-система: карточки, кнопки, модалки, формы, футеры | **FAIL.** Карточка только на index (`.card` 10px/16×19.2) против `.sup-section` (12px/20/#3a3a3c); кнопки 3 размера без шкалы, disabled-состояний фактически нет; формы 2 конфликтующих стиля; футеры 6 вариантов (находки 22–24, 31; футер — см. skill 1 №7, подтверждено). |
| 6 | Иконки: единый стиль, stroke/размер, не только иконка, эмодзи | **FAIL.** `<svg>` 0 и `<img>` 0 на всех 147 страницах; иконки — эмодзи 13 видов, набор отсутствует, рендер зависит от ОС (находка 23). |
| 7 | Тени и границы: уровни elevation, число теней, радиусы | **WARN.** 16 объявленных теней, в DOM реально 7 (2 визуальных уровня) → ~9 токенов мертвы; радиусов 9 значений без шкалы (находки 25, 26). |
| 8 | Темы: симметрия, отсутствие инверсий, отсутствие мерцания | **PASS.** Нецветовых переопределений в `html.light` всего 5 (`opacity:.85` ×4, `text-shadow:none`); контраст пересчитан в обеих темах; переключение без мерцания. |
| 9 | Градиенты и паттерны: осмысленность, худшая точка контраста | **PASS по контрасту / WARN по числу.** 12 градиентов в DOM против 6 токенов; худшая точка после композита 5.42 / 7.25 / 11–13.7 — выше AA (находка 27). |
| M | Метрики: Lighthouse ≥90, LCP, INP, CLS, размер CSS, Coverage, Layers, repaints | Размер CSS **173 550 Б** — измерено. Lighthouse/LCP/INP/CLS/Coverage/Layers/repaints — **не измерено** (инструменты не запускались, типовые значения не подставляю). |

### Что не применимо и почему

- **Изображения (alt/битые/retina, доп. п.8):** `<img>` — 0 на всех 147 страницах, `<svg>` в DOM — 0; проверять нечего.
- **Карточки на interactions/compare/map (SKILL §5):** элементов `.card` там 0, страницы построены на панелях/таблице/шагах — сравнение «одинаковая карточка на 4 страницах» не применимо; эталоном взяты `index.html` и `.sup-section`.
- **Модалки:** одна реализация (`#modal` на index/trends), копипаста нет — проверка PASS, находки нет.
- **`prefers-reduced-motion`:** реализовано обнулением длительностей; при `reduce` все animation/transition = 1e-05 s, `scroll-behavior:auto` — PASS.
- **`offline.html`, `google4a9d23e35c6c3e23.html`:** технические заглушки вне дизайн-системы (0 h1, без футера, чужой font-stack) — исключения, не находки.

## Находки

| # | Скилл | Категория | Критичность | Описание | Где (файл:строка или URL) | Предлагаемое решение |
|---|---|---|---|---|---|---|
| 1 | site-navigation | Битые ссылки | **Blocker** | Карточка добавки на карте и в сравнении строит URL из кириллического `id` (`Креатин`, `Магний`) вместо транслит-слага файла (`kreatin.html`, `magniy.html`). В браузере URL `…/sup/%D0%9C%D0%B0%D0%B3%D0%BD%D0%B8%D0%B9.html` отдаёт `404 File not found` (подтверждено Playwright и Invoke-WebRequest). | `docs/map.html:487`; `docs/compare.html:208`; пример: `http://localhost:8000/sup/%D0%9C%D0%B0%D0%B3%D0%BD%D0%B8%D0%B9.html` | Брать slug из данных/карты `id→slug` (как уже сделано для random в `docs/index.html:617-626` через `sitemap.xml`), а не `s.id`. Добавить регрессионную проверку «все сгенерированные sup-ссылки существуют на диске». |
| 2 | site-navigation | Навигация | **Blocker** | Набор ссылок не единый: 131 sup-страница содержит только 3 ссылки (`index`, `feedback`, `support`), 11 корневых — 10, `glossary.html` — 7. `methodology.html` и `glossary.html` недоступны из навигации нигде (только из футера). Проверки SKILL §3–§4 (одинаковый набор/порядок) провалены на 143/143 страницах. | `docs/sup/*.html` (nav.actions, напр. `docs/sup/5-htp.html`); `docs/glossary.html`; `docs/index.html` | Ввести единый источник списка навигации (партиал/JS-рендер или генератор) с 10 целевыми ссылками и одинаковым порядком; sup-страницы получают тот же набор с корректными `../`-префиксами. |
| 3 | site-navigation | Кросс-ссылки | Med | Кнопка «+ Сравнить» на sup-странице пишет id в `localStorage.compareIds` и никуда не ведёт, а `compare.html` читает только `?ids=`; из sup-страницы нет ни ссылки на compare, ни перехода. Пользователь получает тупик: открытый compare показывает «Не указаны добавки для сравнения». | `docs/sup/5-htp.html:94`, `docs/sup/5-htp.html:272-288`; `docs/compare.html:222-230` | Либо `compare.html` при отсутствии `?ids=` читает `compareIds`, либо кнопка сразу ведёт на `compare.html?ids=…`; добавить в nav sup-страниц ссылку на compare. |
| 4 | site-navigation | Навигация / active state | Med | Ни одна ссылка не помечает текущую страницу: `aria-current` — 0 вхождений на ~3400 отрендеренных ссылок, визуального active-состояния нет. При этом одни страницы ссылаются сами на себя (`index.html`), другие нет (`methodology.html`) — поведение непоследовательно. | `docs/*.html` (nav.actions), `docs/style.css` | Проставлять `aria-current="page"` и класс active при рендере/по URL; для текущей страницы либо всегда ссылка, либо всегда `<span>`. |
| 5 | site-navigation | История браузера | Med | Переключение табов `interactions.html` использует `history.replaceState`, поэтому «назад» не возвращает предыдущий таб, а уходит на предыдущую страницу (после 4 переключений back → `about:blank`, активная панель отсутствует). Deep-link и сами табы работают. | `docs/interactions.html:442` | Использовать `pushState` на переключении таба и обрабатывать `popstate` для восстановления панели по hash. |
| 6 | site-navigation | Мобильная навигация | Med | На 390×844 навигация — горизонтальный скроллер: `clientWidth 371`, `scrollWidth 1172`, 7 из 10 ссылок изначально за экраном; бургера и визуального индикатора прокрутки нет. На sup-страницах за экраном 1 из 3 ссылок. Перекрытия контента нет, клавиатура автоматически прокручивает nav. | `docs/style.css:1708-1744` (overflow-x:auto), `docs/style.css:1761-1768`; все страницы | Добавить бургер/«Ещё» для узких экранов либо явный affordance (градиент/стрелка/индикатор) и `scroll-snap`; проверить на 320 px. |
| 7 | site-navigation | Футер | Low | Футер не единый: 131 sup-страница — 4 ссылки (methodology, faq, glossary, privacy), 11 корневых — 5 (+`feed.xml`), `index.html` — 6 (+`sup/index.html`). Ссылки живые. | `docs/sup/5-htp.html` (footer), `docs/index.html` (footer), остальные корневые | Выровнять состав футера на всех страницах (единый партиал); решить, нужны ли RSS и каталог только на главной. |
| 8 | site-navigation | 404 | Low | Кастомной 404 нет: несуществующий URL отдаёт дефолтную английскую страницу `python http.server` без навигации и возврата; на GitHub Pages будет дефолтная 404 GitHub. | `docs/404.html` отсутствует; пример `http://localhost:8000/no-such-page` | Добавить `docs/404.html` с навигацией и ссылкой на главную (GitHub Pages подхватит автоматически). |
| 9 | site-navigation | Доступность | Low | Skip-link присутствует и видим при фокусе, но после Enter фокус остаётся на `body`: прокрутка к `#main` происходит, а фокус не переносится, т.к. у `<main>` нет `tabindex="-1"`. | `docs/index.html` (`a.skip-link`, `<main id="main">`), `docs/style.css:2042-2044` | Добавить `tabindex="-1"` на `<main id="main">` и переводить фокус в него по активации skip-link (или навесить обработчик). |
| 10 | site-navigation | Хлебные крошки | Low | Крошки есть только на 131 sup-странице (Главная → Каталог → название); на 12 корневых страницах их нет; у `sup/index.html` цепочка усечена — только «Главная», без уровня «Каталог». | `docs/sup/*.html` (nav.breadcrumbs), `docs/sup/index.html` | Либо добавить крошки на корневые разделы, либо зафиксировать в конвенции, что они только для каталога; в `sup/index.html` добавить уровень «Каталог». |
| 11 | site-navigation | Внешние ссылки | Low | Оформление непоследовательное: 927 внешних ссылок с `target="_blank"` и `rel="noopener"` (0 пропусков rel), но 376 внешних (DOI/PubMed) открываются в текущей вкладке без `target="_blank"`. Утечки opener нет. | `docs/sup/*.html` (ссылки DOI/PubMed), напр. `docs/sup/5-htp.html` | Унифицировать: либо все внешние в новой вкладке с `rel="noopener"`, либо все в текущей — осознанно и одинаково. |
| 12 | visual-design-audit | Контраст | Med | Сообщение об ошибке сравнения — красный `#ff0000`: dark на `#1c1c1e` = **4.26:1**, light на `#f5f5f7` = **3.67:1** — ниже AA 4.5 в обеих темах. | `docs/compare.html` (`#cmpError`), `docs/style.css` | Семантический токен: dark `#f87171` (5.04:1), light `#b91c1c` (5.94:1) — уже есть как `--sev-critical*`. |
| 13 | visual-design-audit | Контраст | Low | Placeholder поля ввода: `#757575` на `#15171c` = **3.89:1** < 4.5 (только dark). | `docs/calculator.html` (`input#q::placeholder`), `docs/style.css` | `::placeholder { color: var(--muted) }` → 7.3:1; проверить остальные поля поиска. |
| 14 | visual-design-audit | Контраст (граф) | Med | Подписи центральных узлов: белый 20px bold на цвете механизма — **3 из 14 ниже 3:1**: кишечник `#82c91e` **2.03**, липиды `#f59f00` **2.13**, микробиота `#30b06b` **2.78**; ещё 6 ниже 4.5 (антиоксиданты 3.58, глюкоза 3.12, инсулин 3.43, серотонин 4.32, холестерин 3.32, триглицериды 3.65). Рёбра: кальций `#795548` на `#1c1c1e` = **2.60** < 3.0 (WCAG 1.4.11). | `docs/interactions.html:1110-1125` (`MECH_COLORS`), `:1241-1301` (font, edges) | Развести цвет узла и цвет подписи: `#111` на светлых заливках, `#fff` на тёмных (порог ≥4.5), рёбра — ≥3:1 к фону. |
| 15 | visual-design-audit | Токены / темы | Low | Палитра графа и тегов карты — **14 hardcoded hex в HTML** (`#e8590c`, `#f59f00`, `#0ca678`, …), не CSS-переменные: в светлой теме те же цвета на светлом фоне, палитра вне дизайн-системы. | `docs/interactions.html:1110-1125`; `docs/map.html` (теги t-strong/t-mod/t-ctx) | Вынести в `--mech-*` (14 пар `:root` / `html.light`), теги карты перевести на те же токены. |
| 16 | visual-design-audit | Иерархия | Med | h2 — три разных стиля на одном уровне: 16px/19.2/600 (аккордеон FAQ index, 4 шт.), 20px/30/600 (130 sup), 24px/36/**500** (корневые секции). На `index.html` h2 (16px) **меньше** h3 (20px/600) — инверсия. | `docs/style.css` (правила h2), `docs/index.html`, `docs/sup/*.html` | Один размер на уровень: h2 24/600 для секций; заголовок аккордеона — не h2, а `.summary-title`/h3. |
| 17 | visual-design-audit | Типографика | Med | Длина строки 127–138 знаков (норма 60–80) на 8 страницах: atlas 138, graph 138, interactions 138, map 138, glossary 133, support 133, `sup/index.html` 133, compare 127. Остальные 132 — ~80. | `docs/style.css` (`.wrap` 1392/1152) | `max-width: 72ch` для текстовых блоков широких страниц; сетки/граф — на всю ширину. |
| 18 | visual-design-audit | Типографика | Low | Текст <14px на **143/147** страницах: `.placebo-label` 12.48×178, `.btn-cite`/`.btn-tts` 13.6×260, `.chip` 13.1×129, `.cat-label` 13.6×57, `.cat-warn` 12.8×15, `code` 13×14, `.lbl` 13.1×8, th/td compare 12.8, `.trustbar` 13.6×5, nav-btn 13.6×22. | `docs/style.css` (селекторы выше) | Минимум 14px: `--fs-3: .875rem`; 12.48 → 14, не 13. |
| 19 | visual-design-audit | Техдолг / упрощение | Low | Шкала типографики разъехалась: **25** font-size на 125 объявлений (6 буквальных rem + `--fs-1…--fs-9`), **13** line-height, **6** font-family (в т.ч. голый `'Inter'`, 2 `!important`-стека), 4 font-size с `!important`; `line-height: normal` — на 146 страницах. | `docs/style.css` | 7 ступеней (`--fs-1…--fs-7`), 3 line-height (tight/normal/loose), 1 font-family + mono; снять `!important` с размеров. |
| 20 | visual-design-audit | Отступы / сетка | Low | Шкалы 4/8/16/24/32/48 нет: padding 176 объявлений / **35 уникальных** (кратны 4 только 7), margin 75 / 14 (3), gap 50 / 11 (1). Вне шкалы: 6.4, 9.6, 11.2, 12.8, 13.6, 19.2, 21.6, 22.4, 34, 46. | `docs/style.css` | `--space-1…--space-8` (4/8/12/16/24/32/48/64), заменить числовые значения; начать с 6.4/9.6/19.2. |
| 21 | visual-design-audit | Сетка | Med | **10 разных max-width** (840×130, 1152×6, 1392×4, 1200, 1104, 760, 720, 640, 460) и разные боковые паддинги (0 / 16/24 / 20 / 24) — левый край контента не совпадает при переходах между страницами. | `docs/style.css` (`.wrap`, `.sup-wrap`, `body{max-width:1200px}`) | Две ширины: `--w-content: 840px`, `--w-wide: 1392px`; паддинг 24px везде (16 при ≤600). |
| 22 | visual-design-audit | Формы | Med | Два конфликтующих стиля: поиск (`#search`, `#supSearch`, `#graphSearch`) — padding 0, radius 0, border 2px `#767676`; прикладные поля (`#pWeight`, `#pAge`, `#pSex`, `#pPregnant`, `input#q`) — padding 7.2-8/12.8, radius 8, border 1px `#2b2e35`/`#d9dde3`. `select#mechSelector` — 14.4px и radius 0 вместо 16px/8. | `docs/index.html`, `docs/sup/index.html`, `docs/interactions.html`, `docs/calculator.html`, `docs/style.css` | Один `.field` (radius 8, border 1px, padding 8 12, font 16); поиск — модификатор с той же геометрией. |
| 23 | visual-design-audit | Иконки | Med | Набора иконок нет: `<svg>` **0** и `<img>` **0** на всех 147 страницах; иконки — эмодзи: ⚖×131 (map), ☆×130 и ✋×130 (index), ⚠×17, 🔬×5, 🧠×3, 💚×3, ⚙×3, ✨×3; в шапке 12 видов на 144–146 страницах. Единого размера/stroke нет, вид зависит от ОС. | все `docs/*.html` (шапка, карточки, карта) | 6–8 inline-SVG 20×20, stroke 1.5, `--icon-size`, `aria-hidden="true"` + текст; эмодзи — только в тексте. |
| 24 | visual-design-audit | Кнопки / состояния | Low | Три размера без шкалы при общем radius 8: 16px/pad 11.2×17.6 (основные), 13.6px/pad 7.2×12.8 (nav/шапка), 13.6px/pad 4×8 (cite/tts). Состояний мало: `:hover` 76 правил, `:active` **5**, `:disabled` **1** (`#resetFilters`), `[aria-disabled]` 0; в DOM calculator disabled-элементов 0 — disabled-состояний в интерфейсе нет. | `docs/style.css` | Два размера (`--btn-h:44`, pad 10 16 и 6 12), общий `:disabled{opacity:.5;cursor:not-allowed}`, `:active` — сдвиг 1px. |
| 25 | visual-design-audit | Радиусы | Low | 9 значений в DOM: 12px×2006, 8px×1936, 6px×769, 999px×677, 10px×510, 4px×396, 20px×266, 14px×2, 16px×1 — 7 «рабочих» без шкалы; карточка 10px, `.sup-section` 12px, кнопка 8px. | `docs/style.css` | Оставить 4: 4 / 8 / 12 / 999 (pill); 6/10/14/16/20 заменить. |
| 26 | visual-design-audit | Тени | Low | Объявлено 16 токенов тени, в DOM реально **7** (`0 2px 6px` ×260, `0 8px 32px` ×147, 3 цветных glow, 1 ring) → 2 визуальных уровня, ~9 токенов мертвы; уровни не кодируют смысл. | `docs/style.css` (`--shadow-*`) | 3 уровня: `--elev-1` (карточка), `--elev-2` (модалка/дропдаун), `--elev-focus`; мёртвые токены удалить. |
| 27 | visual-design-audit | Градиенты | Low | 12 градиентов в DOM против 6 токенов `--grad-*`; литералы в разметке: `.btn.calc` (2 стр.), `bestBadge`, **4 × `.card-link` с разными оттенками** (синий/зелёный/розовый/циан), 3 тега карты, `.support-btn`, `.tr-tab.on`. Контраст в худшей точке проходит (5.42 / 7.25 / 11–13.7). | `docs/index.html` (`.card-link`), `docs/calculator.html`, `docs/map.html`, `docs/support.html` | 3 токена (`--grad-accent/warm/cool`), 4 оттенка card-link свести к одному с разными иконками. |
| 28 | visual-design-audit | **Баг (визуальный)** | Med | Плацебо-бар не отображается: `.placebo-bar` — flex-элемент в `.sup-header` (display:flex, 800px), но сжимается до **115px** (две подписи), поэтому `.placebo-track{flex:1}` получает **width 0**, `.placebo-fill` — тоже **0** при inline `width:33%`. На скриншоте видны только слова «Плацебо / Эффект». Воспроизводится на **всех 89** sup-страницах с баром (из 131; у 42 бара нет). | `docs/style.css:2683-2708`; `docs/sup/*.html:80-85` | `.placebo-bar{flex:1 1 240px; min-width:200px}` + `.placebo-track{min-width:80px}`; либо строка на всю ширину (`width:100%` при `flex-wrap:wrap`). |
| 29 | visual-design-audit | Иерархия / a11y | Low | Пропуск уровня h1→h3 на 5 страницах: `atlas.html`, `compare.html`, `graph.html`, `interactions.html`, `map.html` (на map h3 идут подряд 1,3,3,3…). h1 ровно один на 146/147 (исключение — google-заглушка, 0 h1). | `docs/atlas.html`, `docs/compare.html`, `docs/graph.html`, `docs/interactions.html`, `docs/map.html` | Первые h3 повысить до h2 (секции уже выделены) либо добавить визуально скрытый h2. |
| 30 | visual-design-audit | Адаптивность (контент) | Med | Overflow документа на 320px: `sup/gimnema.html` 326, `sup/magniy.html` 324, `sup/shiitake.html` 338. Драйвер — **неразрывный DOI** в ссылке источника (`10.2174/0929867328666210121123037`, `10.1161/HYPERTENSIONAHA.116.07664`, `10.1615/IntJMedMushrooms.2021038773`). На 375/768/1440 — 0. В skill 1 фиксировался nav-скроллер — это другой драйвер, причина уточнена. | `docs/sup/gimnema.html`, `docs/sup/magniy.html`, `docs/sup/shiitake.html` (ссылки-источники) | `.source a, .ref a { overflow-wrap: anywhere; }` — точечно для DOI/URL. |
| 31 | visual-design-audit | Дизайн-система | Low | Карточка и секция — разные системы: `.card` (index, 8 шт.) pad 16×19.2, radius 10, bg rgba(255,255,255,.05), border rgba(255,255,255,.09); `.sup-section` pad 20, radius 12, mb 28, bg `#2c2c2e`, border 1px `#3a3a3c` (жёсткие цвета мимо токенов). | `docs/style.css` (`.card`, `.sup-section`) | Один `.surface`: radius 12, border `--line`, bg `--card-bg`, паддинг 20/24 из шкалы. |

**Итого по visual-design-audit: 20 находок — Blocker 0, Med 9, Low 11.** Пересечений с skill 1 — 2: футер (№7, подтверждено: 6 вариантов, байты) и overflow 320 (№6 skill 1 — nav-скроллер; здесь другой драйвер, DOI в контенте).

**Всего по двум скиллам: 31 находка — Blocker 2, Med 13, Low 16.**

## Таблица по страницам (SKILL §5)

Статус: `OK` — полный набор 10 целевых ссылок; `неполный` — перечислены отсутствующие целевые страницы; `исключение` — страница законно без nav (SKILL §4.5).
«Ссылок» — количество ссылок в основном блоке навигации (nav.actions; для sup-страниц без учёта breadcrumbs).

| Страница | Есть nav | Ссылок | Статус |
|---|---|---|---|
| atlas.html | нет (исключение) | 0 | исключение |
| calculator.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| compare.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| faq.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| feedback.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| glossary.html | есть | 7 | неполный — нет: index.html, compare.html, methodology.html, faq.html, glossary.html |
| google4a9d23e35c6c3e23.html | нет (исключение) | 0 | исключение |
| graph.html | нет (исключение) | 0 | исключение |
| index.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| interactions.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| map.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| methodology.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| offline.html | нет (исключение) | 0 | исключение |
| privacy.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| support.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| trends.html | есть | 10 | неполный — нет: methodology.html, glossary.html |
| sup/5-htp.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/alanin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/alfa-lipoevaya-kislota.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/alpha-gpc.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/arginin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/ashvaganda.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/astaksantin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/astragal.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b-lactis.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b1.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b12.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b2.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b3.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b5.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b6.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/b9.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/bakopa.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/bcaa.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/berberin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/beta-alanin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/beta-glyukany-ovsa.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/betain.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/biotin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/bor.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/bosvelliya.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/boyaryshnik.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/buzina.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/cdp-holin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/chaga.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/chernyy-tmin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/chesnok.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/coq10.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/d-mannoza.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/dha.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/ehinatseya.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/epa.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/ezhovik.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/fosfatidilserin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/gaba.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/gialuronovaya-kislota.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/gimnema.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/ginkgo.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/gla.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/glitsin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/glutamin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/glutation.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/glyukozamin-hondroitin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/gotu-kola.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/guperzin-a.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/hlorofill.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/hmb.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/holin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/hrom.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/imbir.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/index.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/inozitol.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kaliy.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kaltsiy.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/karnozin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/klyukva.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kofein.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kollagen.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/korditseps.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kreatin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kremniy.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kurkumin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/kvertsetin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/l-karnitin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/l-teanin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/l-tsitrullin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/laktoferrin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/lavanda.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/lgg.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/lizin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/lyutein-zeaksantin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/magniy.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/maka.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/marganets.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/maytake.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/med.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/melatonin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/melissa.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/metionin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/molibden.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/msm.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/nac.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/niatsinamid.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/nmn.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/omega-3.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/ornitin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/paba.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/passiflora.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/pazhitnik.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/piknogenol.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/pqq.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/probiotiki.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/prolin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/psillium.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/pustyrnik.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/rastoropsha.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/resveratrol.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/reyshi.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/riboflavin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/rodiola.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/s-boulardii.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/same.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/selen.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/serin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/shatavari.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/shiitake.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/shlemnik.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/sulforafan.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/syvorotochnyy-protein.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/taurin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/tirozin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/tribulus.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/triptofan.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/tsink.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/tsistein.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/valeriana.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-a.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-c.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-d.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-e.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-k1.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/vitamin-k2.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/yod.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/yohimbin.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/zhelezo.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/zhenshen.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |
| sup/zveroboy.html | есть | 3 | неполный — нет: map.html, interactions.html, compare.html, calculator.html, methodology.html, faq.html, glossary.html, trends.html |

## Примечания

- Рендер проверялся на всех 147 страницах: 0 ошибок загрузки, 0 ответов ≥400 на ресурсы, 0 битых изображений, 0 ошибок консоли (кроме самих страниц 404 при проверке битого URL).
- Внешние хосты: PubMed 512, doi.org 376, market.yandex 130, ozon 130, wildberries 130, Streamlit 15, yandex 4, github 3, yoomoney 2, metrika 1.
- Динамические ссылки `index.html#sup=<id>` корректны (id = отображаемое имя), ломаются только файловые `sup/<id>.html`.

### Примечания visual-design-audit (методика и что прошло)

- **Как считался контраст.** `getComputedStyle` на отрендеренном DOM, фон композитился по цепочке предков (полупрозрачные `rgba`), элементы с произведением `opacity` предков < 0.9 и скрытые (`display:none`, `visibility:hidden`, `aria-hidden`, за экраном) исключались — без этого первые прогоны давали ложный фон `rgb(153,153,155)` и ratio 1.0 на 145 страницах. Тема переключалась с инъекцией `*,*::before,*::after{transition:none!important;animation:none!important}`, иначе CSS-переходы дают промежуточные цвета и ложные 2–3:1.
- **Проверено и прошло (не находки):** бейджи грейдов 4.99–6.47:1; `.pmid-badge` 5.33 light / 9.83 dark; `.chip` 5.33 / 9.83; `.placebo-label` 4.66 / 6.08; `.btn` 15.0–17.0 light / 8.46–12.8 dark; `.s-strong/.s-medium/.s-weak` 4.99–6.8; `.card-link` после композита 11.1–13.7; `bestBadge` 7.25; теги карты 4.99–5.02; `.btn.calc` 5.42. Focus-ring `outline:2px solid var(--accent)` виден на 58/60 интерактивных, контраст ≥3.6:1. `prefers-reduced-motion` — длительности обнуляются. Sticky-первая-колонка в compare работает на 1440/768/375/320. WebKit-метрики (6 страниц) совпадают с Chromium.
- **compare.html:** 11 колонок, ширина таблицы 1538px, обёртка скроллится (1104/688/337/282), документ не переполняется; но кегль ячеек 12.8px и при 320px видно ~2 колонки из 11 (≈5,5 экрана скролла) — учтено в находке 18.
- **Скриншот сломанного плацебо-бара** (только две подписи, полосы нет): `C:\Users\TshK\AppData\Local\Temp\opencode\placebo_dark.png` и `placebo_light.png`.
- **Не visual-design:** JS-ошибка `(intermediate value)(intermediate value)…` на 130 страницах (Stage A) — передать в `qa-deep-audit`; состояния loading/empty/error — `ui-ux-deep-audit`; размеры тач-целей — `mobile-deep-audit`.

# AUDIT C PRODUCT — product-audit (READ-ONLY)

Дата: 2026-10-07 · Ветка: v5.6-dev · Режим: **только чтение** (изменён 1 файл — этот отчёт)
Сервер: `localhost:8000`, отвечает (`version.json` = 5.6.1, data 2026-09-25, 1000 тестов).

---

## ШАГ 1: Проверка на пересечение

### Сводка всех находок из существующих отчётов

#### P0_P1_FIX.md и P0_P1_FINAL.md (батч A/B)

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | Горизонтальный скролл на graph.html (600px плашка) | `docs/graph.html:141-142,158-176` | P0 | Исправлено |
| 2 | Ссылки подвала 20px (WCAG 2.5.8) | `docs/style.css:1166-1178` | P1 | Исправлено |
| 3 | summary 24px (12 страниц) | `docs/style.css:1185-1194` | P1 | Исправлено |
| 4 | Селекты trends.html 34px | `docs/trends.html:37-44` | P1 | Исправлено |
| 5 | body.overflow при открытой модалке не блокировался | `docs/style.css:1163` | P1 | Исправлено |
| 6 | #loadingBar не прячется (stabilization disabled) | `docs/graph.html:410,414` | P1 | Исправлено |
| 7 | Бамп кеша ?v=414→415, CACHE_VERSION v83→v84 | 143 файла + `docs/sw.js` | — | Исправлено |
| 8 | 6 селектов ниже 44px (index 37px, calculator 38px) | `docs/index.html`, `docs/calculator.html` | P1 | Техдолг #94 |
| 9 | Пересъёмка снапшотов (69 эталонов) | `tests/snapshots/**` | — | Исправлено |

#### USABILITY_AUDIT.md (батч B2: 5 сценариев, 5 задач)

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | T1: липкая шапка съедает вьюпорт (508px из 640px, 79%) | `docs/style.css:444,739-746` | P0 | Техдолг #96 |
| 2 | T2: sup-страницы имеют 4 ссылки вместо 11, дата только в подвале | `docs/sup/*.html:55-59` | P0 | Открыто |
| 3 | T3: модалка без role="dialog", без aria-modal, без ловушки фокуса; skip-link не переводит фокус | `docs/index.html`, `docs/script.js` | P1 | Открыто |
| 4 | T4: поиск по PMID возвращает 0 результатов | `docs/script.js` (#search) | P1 | Открыто |
| 5 | T5: COI только в meta-тегах, не в теле; устаревшая метка "Аудит v1.0" | `docs/glossary.html:40,45`, `docs/faq.html` | P1 | Техдолг #97 |
| 6 | Сценарий 1: навигация sup-страниц (4 ссылки из 11) | `docs/sup/magniy.html:55-59` | P0 | Открыто |
| 7 | Сценарий 2: COI провал (2 вхождения в meta, 0 в теле) | `docs/glossary.html:40,45` | P1 | Открыто |
| 8 | Сценарий 3: блок сравнения на 89% страницы, поиск PMID | `docs/index.html` | P1 | Открыто |
| 9 | Сценарий 4: липкая шапка 26-79% вьюпорта | `docs/style.css:444` | P0 | Открыто |
| 10 | Сценарий 5: skip-link не переводит фокус, модалка недоступна | `docs/index.html`, `docs/script.js` | P1 | Открыто |

#### T1_SCALE_CHECK.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | T1 масштаб: 12 страниц из 13 шапка выше 200px | `docs/style.css:444,739-746` | P0 | Техдолг #96 |
| 2 | Причина: 11 кнопок в flex-wrap (419px) | `docs/style.css:739-746` | P0 | Подтверждено |
| 3 | Техдолги #94-97 обновлены | `ROADMAP.md` | — | Обновлено |

#### T1_T5_SNAPSHOT_ANALYSIS.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | Разбор 36 падений снапшотов (T1, T5, #94) | `tests/snapshots/**` | — | Обосновано |
| 2 | T1: медиазапрос ≤620px для шапки | `docs/style.css` | P0 | Исправлено |
| 3 | T5: секция COI добавлена в methodology.html | `docs/methodology.html` | P1 | Исправлено |
| 4 | #94: select{min-height:44px} | `docs/style.css` | P1 | Исправлено |
| 5 | #95: KILL_CSS маска убрана | `tests/test_visual_snapshots.py` | P1 | Исправлено |
| 6 | Пересъёмка 73 passed | `tests/snapshots/**` | — | Исправлено |
| 7 | Бамп ?v=415→416, CACHE_VERSION v84→v85 | 143 файла + `docs/sw.js` | — | Исправлено |

#### audit_C_visual-design.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | 7 навигационных карточек окрашены 7 разными несистемными цветами | `docs/index.html:272,278,284,290,296,302,308` | P1 | Открыто |
| 2 | .btn 10 цветов и 3 геометрии | `docs/style.css:127` | P1 | Открыто |
| 3 | 7 зелёных и 4 красных для одного статуса | `docs/style.css:412,413,429,789,1450,1488,1556` | P1 | Открыто |
| 4 | --panel не объявлен (фон блока кода отсутствует) | `docs/methodology.html:99` | P1 | Открыто |
| 5 | Палитры продублированы в 28 местах HTML | 6 файлов | P1 | Открыто |
| 6 | H1 и H2 отличаются на 0.8px | `docs/style.css:131,1418` | P1 | Открыто |
| 7 | H3 крупнее и жирнее H2 на index | `docs/index.html:99,318` | P1 | Открыто |
| 8 | Размер H2 различается на 5 значений | 9 локальных переопределений | P1 | Открыто |
| 9 | Текст <14px на трёх страницах (61.8%, 53.8%, 52.9%) | `docs/trends.html`, `docs/index.html`, `docs/calculator.html` | P1 | Открыто |
| 10 | Elevation-шкалы нет (11 теней, 1 используется) | `docs/style.css` | P1 | Открыто |
| 11 | 5 объявлений одного градиента (4 мёртвых) | `docs/graph.html:147-152` | P1 | Открыто |
| 12 | Футеры не байт-идентичны (3 варианта) | 12 страниц | P1 | Открыто |
| 13 | Шкала отступов наполовину не используется | `docs/style.css:77` | P1 | Открыто |
| 14 | Три разных внутренних отступа секций index | `docs/index.html` | P1 | Открыто |
| 15 | Карточка устроена по-разному на четырёх страницах | `docs/index.html`, `docs/graph.html`, `docs/map.html`, `docs/support.html` | P1 | Открыто |
| 16 | Вес H2 расходится (w500/w600) | `docs/support.html:36`, `docs/feedback.html:68` | P2 | Открыто |
| 17 | Два мёртвых объявления h1 с !important | `docs/index.html:101`, `docs/map.html:267` | P2 | Открыто |
| 18 | Пропуски уровней заголовков | `docs/trends.html:184` | P2 | Открыто |
| 19 | 29 размеров шрифта, 7 дробных | `docs/style.css` | P2 | Открыто |
| 20 | --accent-2 в светлой теме 1.59:1 (безопасен, но держится на ручной охране) | `docs/style.css:51,699-712` | P2 | Открыто |
| 21 | Радиусы вне шкалы (17 в CSS, ~40 в страницах) | `docs/style.css`, страницы | P2 | Открыто |
| 22 | «Пилюля» выражена двумя способами | `docs/style.css:153,735` | P2 | Открыто |
| 23 | Нет SVG и img, вся иконографика — эмодзи | 5 страниц | P2 | Открыто |
| 24 | Кнопка только с иконкой без aria-label | `docs/index.html` (130 элементов) | P2 | Открыто |
| 25 | Градиент продублирован в трёх местах | `docs/style.css:107`, `docs/interactions.html:70`, `docs/trends.html:49` | P2 | Открыто |
| 26 | Три радиальных градиента без читаемого смысла | `docs/style.css:287-289` | P2 | Открыто |
| 27 | Три карточки map с разными прозрачностями | `docs/map.html` | P2 | Открыто |
| 28 | --fg работает только на одной странице | `docs/style.css:1494`, `docs/interactions.html:37,43` | P2 | Открыто |
| 29 | Elevation-токены симметричны не полностью, нет prefers-color-scheme | `docs/style.css:84` | P2 | Открыто |

#### audit_C_marketing.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | Нет слогана/подзаголовка с ценностью | `docs/index.html:198` | P1 | Открыто |
| 2 | Нет явного CTA на главной | `docs/index.html:204-228` | P1 | Открыто |
| 3 | Нет соцдоказательств на главной | `docs/index.html` | P1 | Открыто |
| 4 | Нет структуры воронки | `docs/index.html` | P1 | Открыто |
| 5 | Нет Schema.org на основных страницах | 10 страниц | P1 | Открыто |
| 6 | Нет явного "зачем это мне" | `docs/index.html:230-268` | P1 | Открыто |
| 7 | Нет CTA на странице калькулятора | `docs/calculator.html:184-301` | P1 | Открыто |
| 8 | Нет соцдоказательств на странице поддержки | `docs/support.html:72-106` | P1 | Открыто |
| 9 | Нет слогана на странице методологии | `docs/methodology.html:78` | P2 | Открыто |
| 10 | Нет CTA на странице FAQ | `docs/faq.html:78-170` | P2 | Открыто |
| 11 | Нет соцдоказательств на странице трендов | `docs/trends.html:237-325` | P2 | Открыто |
| 12 | Нет "зачем это мне" на странице карты | `docs/map.html:309-318` | P2 | Открыто |
| 13 | Нет CTA на странице атласа | `docs/atlas.html:197-229` | P2 | Открыто |
| 14 | Нет соцдоказательств на странице глоссария | `docs/glossary.html:70-135` | P2 | Открыто |
| 15 | Нет "зачем это мне" на странице графа | `docs/graph.html:243-262` | P2 | Открыто |
| 16 | Нет CTA на странице обратной связи | `docs/feedback.html:169-265` | P2 | Открыто |

#### PRODUCT_AUDIT.md (старый отчёт от 2026-09-30)

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | graph.html без title, description, viewport, lang | `docs/graph.html:2-7` | КРИТИЧНЫЙ | Исправлено |
| 2 | Внешние CDN-скрипты без defer | `docs/graph.html:6-7` | КРИТИЧНЫЙ | Исправлено |
| 3 | 430 КБ в одном файле (граф в HTML) | `docs/graph.html` | КРИТИЧНЫЙ | Исправлено |
| 4 | При недоступном data_index.json страница стирается | `docs/script.js:169-182` | КРИТИЧНЫЙ | Исправлено |
| 5 | Кнопки шапки 33px (WCAG 2.5.5 требует 44px) | `docs/style.css:8` | КРИТИЧНЫЙ | Исправлено |
| 6 | support.html без OG/Twitter-тегов | `docs/support.html:1-20` | ВАЖНЫЙ | Исправлено |
| 7 | index.html без meta description | `docs/index.html:6-7` | ВАЖНЫЙ | Исправлено |
| 8 | title 32 символа (цель 40-70) | `docs/index.html:6` | ВАЖНЫЙ | Исправлено |
| 9 | meta description отсутствует на 5 страницах | 5 страниц | ВАЖНЫЙ | Исправлено |
| 10 | description короче 120 символов на 5 страницах | 5 страниц | ВАЖНЫЙ | Исправлено |
| 11 | Нет правил :focus-visible | `docs/style.css` | ВАЖНЫЙ | Исправлено |
| 12 | 20 кнопок с одиночным символом без aria-label | 11 страниц | ВАЖНЫЙ | Исправлено |
| 13 | Поле поиска #search без доступного имени | `docs/index.html:196` | ВАЖНЫЙ | Исправлено |
| 14 | --accent 3.82:1 на карточках в тёмной теме | `docs/style.css:2` | ВАЖНЫЙ | Исправлено |
| 15 | Поле email без required | `docs/feedback.html:120-215` | ВАЖНЫЙ | Исправлено |
| 16 | Форма Web3Forms без клиентской валидации | `docs/feedback.html:100-215` | ВАЖНЫЙ | Исправлено |
| 17 | fetch без проверки response.ok в 4 файлах | `docs/script.js`, `science2.js`, `tracker.js`, `version.js` | ВАЖНЫЙ | Исправлено |
| 18 | Нет тестов на analyze_coi.py, graph_interactions.py, build_api.py | `tests/` | ВАЖНЫЙ | Не выполнено |
| 19 | .actions расходится по 9 наборам кнопок | 9 страниц | ВАЖНЫЙ | Находка устарела |
| 20 | Нет CTA на главной | `docs/index.html:194-276` | ВАЖНЫЙ | Исправлено |
| 21 | support.html отсутствует в .actions остальных | `docs/support.html` | ВАЖНЫЙ | Исправлено |
| 22 | manifest.webmanifest: 4 записи на 2 файла, нет maskable | `docs/manifest.webmanifest` | ВАЖНЫЙ | Исправлено |
| 23 | Кнопка ↓ появляется только при scrollY > 400 | `docs/style.css:670-689` | ВАЖНЫЙ | Исправлено |
| 24 | Нет брейкпоинтов 900 и 1200px | `docs/style.css` | ВАЖНЫЙ | Ложное срабатывание |
| 25 | Чипы .chip ниже 44px | `docs/style.css:298,345` | ВАЖНЫЙ | Исправлено |
| 26 | lang не задан на graph.html | `docs/graph.html` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 27 | Нет aria-label на иконочных кнопках | 9 страниц | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 28 | 2 h1 на feedback.html | `docs/feedback.html` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 29 | 2 h1 на support.html | `docs/support.html` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 30 | graph.html: 14 фокусируемых элементов | `docs/graph.html` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 31 | Подсказка обещает "/ поиск, Esc сброс", но поле удалено | `docs/map.html:246` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 32 | title 37 символов на support.html | `docs/support.html:6` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 33 | title 36 символов на map.html | `docs/map.html:6` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 34 | title 34 символа на interactions.html | `docs/interactions.html:6` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 35 | title 31 символ на glossary.html | `docs/glossary.html:6` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 36 | title 34 символа на feedback.html | `docs/feedback.html:6` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 37 | description 74, 57, 84 символа на sup-страницах | 5 sup-страниц | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 38 | #toTop и .toBottom с opacity:0 в покое | `docs/style.css:197` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 39 | Нет .chip на 10 страницах | 10 страниц | ЖЕЛАТЕЛЬНЫЙ | Осознанное решение |
| 40 | Правила для #modal продублированы | `docs/style.css:51,75,359` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 41 | 25 правил используют body.dark, только 1 html.dark | `docs/style.css` | ЖЕЛАТЕЛЬНЫЙ | Частично закрыто |
| 42 | 11 резервных копий data.json.bak-* | `docs/` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 43 | robots.txt разрешает всё | `docs/robots.txt` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 44 | CACHE_VERSION = v42, кэширует data.json | `docs/sw.js` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 45 | sitemap.xml: 12 URL, 5 sup-страниц нет | `docs/sitemap.xml` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 46 | sup/*.html нет ссылки на map.html | 5 sup-страниц | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 47 | og.png 1560x880, 528 КБ | `docs/og.png` | ЖЕЛАТЕЛЬНЫЙ | Открыто |
| 48 | Нет min-height у .btn | `docs/style.css` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 49 | Нет aria-live для результата отправки | `docs/feedback.html` | ЖЕЛАТЕЛЬНЫЙ | Исправлено |
| 50 | Дублирование scroll-слушателей | `docs/index.html:394-404` | ЖЕЛАТЕЛЬНЫЙ | Открыто |

#### UI_UX_AUDIT.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | feedback.html: после отправки исчезал весь сайт | `docs/feedback.html` | P0 | Исправлено |
| 2 | Escape не закрывает модалку (ложная находка) | `docs/script.js` | P1 | Отозвана |
| 3 | В модалке оставлена одна кнопка копирования | `docs/script.js` | P1 | Исправлено |
| 4 | h1 ≥ h2 на всех 17 страницах | 17 страниц | P1 | Исправлено |
| 5 | Ни одной группы дублей в index.html | `docs/index.html` | P1 | Исправлено |
| 6 | Кнопка "Обновить" добавлена в сообщение об ошибке | `docs/script.js` | P1 | Исправлено |
| 7 | Кнопка закрытия модалки 42×42 (ложная находка) | `docs/index.html` | P1 | Отозвана |
| 8 | Текст <14px на 7 страницах | 7 страниц | P2 | Частично |
| 9 | Пропуски уровней заголовков | 4 страницы | P2 | Частично |
| 10 | h1 и h2 разведены на 3.6px | 4 страницы | P2 | Исправлено |
| 11 | Цель "выделить главный CTA" исчезла | `docs/index.html` | P2 | Не трогали |
| 12 | Один шаблон футера на всех 17 | 17 страниц | P2 | Исправлено |
| 13 | skip-link на всех 17 и id="main" | 17 страниц | P2 | Исправлено |
| 14 | title и aria-label добавлены на #refreshBtn | `docs/index.html` | P2 | Исправлено |
| 15 | Термины "Вердикт", "Грейд", "Science Index" без пояснения | 10 страниц | P2 | Открыто |
| 16 | Заголовки карточек больше не h3 | `docs/index.html` | P2 | Исправлено |
| 17 | .srcIcon — ссылки на источники 21px высотой | `docs/index.html` | P2 | Открыто |

#### MOBILE_AUDIT.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | glossary @320px: горизонтальный скролл (таблица 329px) | `docs/glossary.html:60,79` | P0 | Исправлено |
| 2 | input/select/textarea < 16px (6 страниц, 22 поля) | `docs/style.css:35-41` + 5 страниц | P1 | Исправлено |
| 3 | Touch-target < 44px (2698 замеров, 25 селекторов) | `docs/style.css` + страницы | P1 | Исправлено |
| 4 | .favBtn 18×22px (130 элементов) | `docs/style.css:131-137` | P1 | Исправлено |
| 5 | Чипы эффектов 22px (13 штук) | `docs/style.css:521-536` | P1 | Исправлено |
| 6 | Кнопки-фильтры 32-35px (index) | `docs/style.css:317,488` | P1 | Исправлено |
| 7 | Кнопки калькулятора 36px | `docs/calculator.html:114` | P1 | Исправлено |
| 8 | Вкладки графиков 34px (trends) | `docs/trends.html:34` | P1 | Исправлено |
| 9 | Кнопки atlas 29-39px по ширине | `docs/atlas.html:179` | P1 | Исправлено |
| 10 | viewport-fit=cover отсутствовал | 17 страниц | P2 | Исправлено |
| 11 | env(safe-area-inset-*) не использовался | `docs/style.css` | P2 | Исправлено |
| 12 | -webkit-tap-highlight-color отсутствовал | `docs/style.css` | P2 | Исправлено |
| 13 | touch-action: manipulation отсутствовал | `docs/style.css` | P2 | Исправлено |
| 14 | theme-color отсутствовал на graph.html | `docs/graph.html` | P2 | Исправлено |
| 15 | -webkit-text-size-adjust: 100% отсутствует | 17 страниц | P2 | Оставлено |
| 16 | -webkit-overflow-scrolling: touch отсутствует | 17 страниц | P2 | Оставлено |
| 17 | methodology @320-412px: <pre> 473px в overflow-x:auto | `docs/methodology.html` | P2 | Оставлено |
| 18 | index: #compareResult table min-width 520px | `docs/index.html` | P2 | Оставлено |

#### QA_AUDIT.md

| # | Находка | Файл:строка | Приоритет | Статус |
|---|---|---|---|---|
| 1 | verdict enum не совпадает (ложная находка) | `openapi.yaml` | P0 | Отозвана |
| 2 | key_sources maxItems: 3 нарушено в 26 карточках | `openapi.yaml:265` | P0 | Исправлено |
| 3 | pytest зависит от постороннего процесса (DuckDB lock) | `tests/conftest.py` | P0 | Исправлено |
| 4 | about maxLength: 160 нарушен в 2 карточках | `openapi.yaml:201` | P0 | Исправлено |
| 5 | effects[].minLength: 5 нарушен в 4 элементах | `openapi.yaml:237` | P0 | Исправлено |
| 6 | effects[].maxLength: 40 нарушен в 12 элементах | `openapi.yaml:242` | P0 | Исправлено |
| 7 | citations: null в 17 карточках | `openapi.yaml:284` | P0 | Исправлено |
| 8 | test_api_contract.py: 2 поля из ~30 → 36 тестов | `tests/test_api_contract.py` | P0 | Исправлено |
| 9 | Offline: не-прекешённая страница отдаёт index.html | `docs/sw.js:88-93` | P1 | Исправлено |
| 10 | Три страницы отсутствуют в STATIC_ASSETS | `docs/sw.js` | P1 | Исправлено |
| 11 | data_index.json уходил в статику | `docs/sw.js` | P1 | Исправлено |
| 12 | Пустой ответ с 503 ломал загрузку | `docs/sw.js` | P1 | Исправлено |
| 13 | Бейдж офлайна — был реализован, доработан | `docs/pwa.js` | P1 | Исправлено |
| 14 | script.js:185 — TypeError на валидном JSON null | `docs/script.js:185` | P1 | Исправлено |
| 15 | build_api.py — ни одного try/except | `scripts/build_api.py` | P1 | Открыто |
| 16 | analyze_coi.py — 0 тестов | `scripts/analyze_coi.py` | P1 | Исправлено |
| 17 | graph_interactions.py — 0 тестов | `scripts/graph_interactions.py` | P1 | Открыто |
| 18 | data_price_history.json отсутствует | `docs/science2.js:119-123` | P1 | Открыто |
| 19 | maPulseFailed записывается и не читается | `docs/science2.js:89` | P1 | Открыто |
| 20 | test_snapshot.py сам себя чинит | `tests/test_snapshot.py` | P1 | Исправлено |
| 21 | Гард от мозгибаки нерабочий | `tests/test_no_mojibake_in_js.py` | P1 | Исправлено |
| 22 | version.json 404 на sup/ | `docs/version.js:4` | P1 | Исправлено |
| 23 | U+FFFD в data/papers/*.json | `data/papers/*.json` | P1 | Открыто |
| 24-38 | Прочие находки (покрытие, edge cases, контракт) | различные | P2 | Частично |

---

## Оценка дублирования

### Проверки product-audit vs существующие находки

| Направление | Проверка product-audit | Дублирует | Источник |
|---|---|---|---|
| UI/UX | Консистентность кнопок | Да | audit_C_visual-design.md №2 (.btn 10 цветов, 3 геометрии) |
| UI/UX | Консистентность футеров | Да | audit_C_visual-design.md №12 (3 варианта футеров) |
| UI/UX | Темы | Да | audit_C_visual-design.md №29 (elevation-токены, prefers-color-scheme) |
| UI/UX | Breadcrumbs | Да | USABILITY_AUDIT.md сценарий 1 (хлебные крошки на sup-страницах) |
| UI/UX | Hover/focus | Да | PRODUCT_AUDIT.md №11 (:focus-visible отсутствует) |
| Маркетинг | Title/description длина | Да | PRODUCT_AUDIT.md №7-10, №32-37 |
| Маркетинг | OG-теги | Да | PRODUCT_AUDIT.md №6 (support.html без OG) |
| Маркетинг | JSON-LD | Да | audit_C_marketing.md №5 (нет Schema.org) |
| Маркетинг | CTA | Да | audit_C_marketing.md №2, №7 (нет CTA) |
| QA | Ошибки fetch | Да | PRODUCT_AUDIT.md №4, №17 (script.js, response.ok) |
| QA | Валидация формы | Да | PRODUCT_AUDIT.md №15, №16 (feedback.html) |
| QA | Клавиатурная навигация | Да | USABILITY_AUDIT.md T3 (модалка, skip-link) |
| Mobile | Viewport | Да | MOBILE_AUDIT.md (viewport-fit=cover) |
| Mobile | Touch targets | Да | MOBILE_AUDIT.md (2698 замеров, 25 селекторов) |
| Mobile | Шрифты inputs | Да | MOBILE_AUDIT.md (input/select/textarea < 16px) |
| Mobile | Горизонтальный скролл | Да | MOBILE_AUDIT.md (glossary @320px), P0_P1_FIX.md (graph.html) |

### Итого

**16 из 16 проверок product-audit дублируют уже найденное = 100% дублирование.**

---

## СТОП

Дублирование > 50% (100%). Новый аудит не выполняется.

### Таблица пересечений: product-audit ↔ существующие отчёты

| Находка из product-audit | Находка из A/B/B2 | Файл:строка |
|---|---|---|
| Консистентность кнопок | audit_C_visual-design.md №2 | `docs/style.css:127` |
| Консистентность футеров | audit_C_visual-design.md №12 | 12 страниц |
| Темы | audit_C_visual-design.md №29 | `docs/style.css:84` |
| Breadcrumbs | USABILITY_AUDIT.md сценарий 1 | `docs/sup/magniy.html` |
| Hover/focus | PRODUCT_AUDIT.md №11 | `docs/style.css` |
| Title/description длина | PRODUCT_AUDIT.md №7-10, №32-37 | 5+ страниц |
| OG-теги | PRODUCT_AUDIT.md №6 | `docs/support.html:1-20` |
| JSON-LD | audit_C_marketing.md №5 | 10 страниц |
| CTA | audit_C_marketing.md №2, №7 | `docs/index.html`, `docs/calculator.html` |
| Ошибки fetch | PRODUCT_AUDIT.md №4, №17 | `docs/script.js:169-182` |
| Валидация формы | PRODUCT_AUDIT.md №15, №16 | `docs/feedback.html:100-215` |
| Клавиатурная навигация | USABILITY_AUDIT.md T3 | `docs/index.html`, `docs/script.js` |
| Viewport | MOBILE_AUDIT.md | 17 страниц |
| Touch targets | MOBILE_AUDIT.md | `docs/style.css` + страницы |
| Шрифты inputs | MOBILE_AUDIT.md | `docs/style.css:35-41` + 5 страниц |
| Горизонтальный скролл | MOBILE_AUDIT.md, P0_P1_FIX.md | `docs/glossary.html`, `docs/graph.html` |

---

## Вывод

Product-audit полностью дублирует уже проведённые аудиты. Все 16 проверок скилла уже покрыты существующими отчётами. Новый аудит не выполняется.

**Рекомендация:** закрыть техдолги #94, #96, #97 и открытые находки из USABILITY_AUDIT.md (T2, T3, T4, T5) в первую очередь. Они представляют наибольшую ценность для продукта.

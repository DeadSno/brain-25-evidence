# AUDIT MASTER v5.6.5 (RERUN)
Ветка: v5.6.5-dev · HEAD: 9048ca3 · Дата: 19.10.2026
| # | Скилл | Категория | Критичность | Описание | Где | Решение |

## 1. Owner Manual Audit (Блок 13)

| O-01 | Owner Manual Audit | Баг | — | Шапка перегружена. Оставить ТОЛЬКО: Обратная связь, Поддержать, Светлая тема, Кубик (с подписью). Убрать: Калькулятор, Тренды, Связи, Карта, BI, FAQ, Сравнение. | docs/index.html (шапка/навбар) | Убрать лишние ссылки из навбара шапки, оставить 4 целевых. |
| O-02 | Owner Manual Audit | Баг | — | Цвета ссылок (светлая тема, кубик, сравнение, карта, FAQ) не в единой палитре. | docs/*.html, docs/style.css | Привести все цветовые ссылки к одной палитре через CSS-переменные. |
| O-03 | Owner Manual Audit | Баг | — | Баг сравнения с самим собой. При переходе sup/magniy.html -> "Сравнить" -> compare.html?ids=magniy и добавлении в список, система видит `magniy` и `Магний` как разные добавки. | docs/compare.html, docs/sup/magniy.html | Привести названия/ID к единому регистру и нормализовать при записи в localStorage.compareIds. |
| O-04 | Owner Manual Audit | Баг | — | Блок "Сравнение" (Сравнить две добавки) висит на главной. Перенести в ряд: Связи, Калькулятор, Карта, Тренды, BI. Между "Сначала ответим на 3 вопроса" и "Как мы проверяем данные". | docs/index.html | Перенести блок "Сравнение" в указанный ряд на главной. |
| O-05 | Owner Manual Audit | Улучшение | — | Перепроверить грейды (A-D) в блоке "Популярные добавки" на главной. | docs/index.html (блок "Популярные добавки") | Сверить грейды карточек с данными в data.json, исправить расхождения. |
| O-06 | Owner Manual Audit | Баг | — | Убрать дублирующий блок "Сравнить две добавки" со страницы index.html. | docs/index.html | Удалить дублирующий блок сравнения с главной страницы. |
| O-07 | Owner Manual Audit | Баг | — | interactions.html#graph (Карта связей) неинформативна. При вводе "креатин" показывает непонятный граф. Требует переосмысления UI/UX. | docs/interactions.html | Переработать UI/UX графа связи: понятные узлы, подписи, фильтрация. |

## 2. Agent RERUN 1/19 (site-navigation)

| A1-01 | site-navigation | Баг | Blocker | 6 разных наборов ссылок вместо единого навбара (все 147 HTML). | все 147 HTML | Сделать единый навбар на всех страницах. |
| A1-02 | site-navigation | Баг | Blocker | graph.html/atlas.html не редирект-заглушки, имеют полный навбар. | docs/graph.html, docs/atlas.html | Сделать редирект-заглушки или убрать полный навбар. |
| A1-03 | site-navigation | Баг | Blocker | 376 DOI-ссылок без target=_blank rel=noopener (130 sup-страниц). | docs/sup/*.html (130 страниц) | Добавить target="_blank" rel="noopener noreferrer" ко всем DOI-ссылкам. |
| A1-04 | site-navigation | Баг | Med | 7 страниц со ссылкой на себя (активный state не убран). | 7 HTML-страниц | Убрать активный state с ссылки на текущую страницу. |
| A1-05 | site-navigation | Баг | Med | Футер не единый (index ≠ sup ≠ compare). | docs/index.html, docs/sup/*.html, docs/compare.html | Унифицировать футер на всех страницах. |
| A1-06 | site-navigation | Баг | Med | Кириллица URL → 404 (sup/Магний.html). | docs/sup/ | Добавить обработку кириллических URL или редирект на slug. |
| A1-07 | site-navigation | Баг | Low | Кнопка «Сравнить» без тоста/авто-перехода. | docs/sup/*.html | Добавить тост и авто-переход к сравнению при клике на «Сравнить». |
| A1-08 | site-navigation | Баг | Low | sup/index.html — 3 ссылки вместо 9. | docs/sup/index.html | Добавить недостающие 6 ссылок в навбар sup/index.html. |
| A1-09 | site-navigation | Баг | Low | glossary.html — 7 ссылок, другой набор. | docs/glossary.html | Привести набор ссылок в глоссарии к общему стандарту. |

## 3. Agent RERUN 2/19 (visual-design-audit)

| V-01 | visual-design-audit | Баг | Med | compare.html — радар профиля фиксирован 520×520 (`<div style="max-width:520px;margin:0 auto"><canvas width="520" height="520">`), на 320/375px вылезает за экран (нужен overflow-x:auto на контейнере или адаптивный размер). Нет переполнения только на 768/1440. | docs/compare.html:144 | Сделать радар адаптивным (overflow-x:auto или относительные размеры canvas). |
| V-02 | visual-design-audit | Баг | Med | compare.html — цвета линий радра hardcoded `borderColor: '#3498db'` / `'#e67e22'` (L424-425), не адаптируются под тёмную тему (фон --apanel #15171c). Контраст линий/заливки в тёмной теме не измерен статически. | docs/compare.html:424-425 | Вынести цвета линий радра в CSS-переменные темы (var(--accent)/var(--info-tx)). |
| V-03 | visual-design-audit | Баг | Med | compare.html — собственная изолированная зона токенов `:root{--apanel:#15171c;--aborder:#2b2e35;--atext:#e9eaee;--amut:#9aa0aa}` / `html.light{...}` (L39-41), не переиспользует основные --bg/--card-bg/--text/--border. При переключении темы возможны инверсии и разрыв с остальными страницами. | docs/compare.html:39-41 | Объединить зону токенов compare.html с основными CSS-переменными темы. |
| V-04 | visual-design-audit | Баг | Low | compare.html — stack-бейджи жёсткие hex вне токенов: #dc2626 (critical), #ea580c (high), #d97706 (medium), #15803d (low), #6b7280 (unknown) (L80-84). | docs/compare.html:80-84 | Заменить жёсткие hex бейджей на CSS-переменные темы. |
| V-05 | visual-design-audit | Баг | Low | compare.html — селекторы добавок инлайн-стилем `min-width:180px` каждый (L121-122), два по 180 px = 360 px > viewport 320 px (и близко к 375). Спасает только `.tableWrap{overflow-x:auto}` — горизонтальный скролл. | docs/compare.html:121-122, 68 | Сделать ширину селекторов адаптивной через проценты/max-width вместо инлайн px. |
| V-06 | visual-design-audit | Баг | Low | Кнопка «Поддержать» (.btn.c-support) цвет #7b61ff hardcoded (L1978, 2002), вне общей палитры; «Обратная связь» (.btn.c-feedback) через токен var(--inter-low)=#84cc16 (L1977, 2001). Несогласованность палитры навигации в светлой и тёмной темах — подтверждает Owner O-02. | docs/style.css:1977-1978, 2001-2002 | Привести цвет кнопки «Поддержать» к единой палитре через CSS-переменные. |
| V-07 | visual-design-audit | Баг | Low | index.html — блок «Сравнение» / quick-links инлайн-стили с жёсткими hex: border #f59e0b/#3b82f6/#10b981/#ec4899/#06b6d4, фон rgba(...) с этими же цветами, кнопка #f59e0b/color #1a1a1a. Грейд-плитки популярных добавок: background #15803d (A), #4d7c0f (B), #b91c1c (D) инлайн. Цвета вне var(--...). | docs/index.html (кнопки быстрого перехода, popularTiles) | Заменить жёсткие hex на CSS-переменные темы. |
| V-08 | visual-design-audit | Баг | Low | search-drop (новый поиск на главной): оформление на токенах (background var(--card-bg), border var(--border), box-shadow var(--shadow), border-radius var(--radius-lg)), НО `:hover` фона hardcoded `rgba(10,132,255,.08)` (L~в инлайн-стиле index.html) и `z-index: 40` литерал (инлайн). Контраст текста var(--text) на var(--card-bg) — по токенам, OK. | docs/index.html инлайн-`<style>` (.search-drop) | Заменить хардкод :hover фона и z-index на CSS-переменные. |
| V-09 | visual-design-audit | Баг | Low | Скелетоны (загрузка): `.skeleton { min-height: 170px; border-radius: var(--radius-xl); background: var(--grad-shimmer); }` (style.css L546-547), используются в interactions.html (L345, L364) и script.js (8 карточек L322-323). Фиксированная высота 170 px может не совпадать с финальным контентом → риск скачка верстки / CLS. | docs/style.css:546-547; docs/interactions.html:345,364; docs/script.js:322-323 | Привести min-height скелетонов к высоте финального контента или убрать фиксированную высоту. |
| V-10 | visual-design-audit | Баг | Low | Тост «Добавлено в сравнение»: вызов `showToast('Добавлено в сравнение')` есть на sup-страницах (напр. 5-htp.html:319), но правила `.toast` / позиционирования / контраста НЕ найдены в style.css (в CSS только `t("update.toast")` строки в script.js:1459 — иное, PWA-обновление). Оформление тоста не зафиксировано статически. | docs/sup/5-htp.html:319 (пример из 131) | Добавить правила `.toast` в style.css (позиционирование, контраст, z-index). |
| V-11 | visual-design-audit | Баг | Low | Текст < 14 px сохраняется: `.placebo-label` font-size 0.78 rem = 12.48 px (style.css L2691), compare `table.compare` font-size .9 rem / td .8 rem = 12.8 px (compare.html L49-51). Дубль старой находки visual-design #18 (текст <14px на 143/147). | docs/style.css:2691; docs/compare.html:49-51 | Увеличить размер шрифта до минимум 14 px для плацебо-метки и ячеек сравнения. |

## 4. Agent RERUN 3/19 (product-audit)

| PA-01 | product-audit | Баг | Blocker | На навбаре sup-страниц только 3 ссылки (Главная, Обратная связь, Поддержать). Пользователь со страницы добавки не может перейти на Сравнение/Калькулятор/Карту/Связи — разрыв воронки. | docs/sup/*.html (nav.actions, напр. docs/sup/magniy.html:59-69) | Вывести на навбар всех 10 целевых ссылок (как на корневых) с `../`-префиксами. | подтверждено RERUN 3/19 (находка №2 аудита 1/19) |
| PA-02 | product-audit | Баг | Med | Кнопка "+ Сравнить" на sup-странице пишет id в `localStorage.compareIds`, показывает тост, но ссылка "Перейти к сравнению →" (`.cmp-go`) изначально `display:none`, появляется только после клика. Пользователь не может перейти к сравнению одним действием. | docs/sup/magniy.html:108-109, 296-325 | Сделать `.cmp-go` видимым сразу либо повесить переход на `compare.html?ids=<id>` на саму кнопку `.cmp-add`. | подтверждено RERUN 3/19 (находка №3 аудита 1/19) |
| PA-03 | product-audit | Баг | Med | Плацебо-бар не отображается: `.placebo-bar` сжимается до 115px, `.placebo-track` получает width 0, `.placebo-fill` — width 0. На скриншоте только слова "Плацебо / Эффект". Воспроизводится на 89 страницах с баром (из 131). | docs/style.css:2683-2708; docs/sup/*.html:86-92 | `.placebo-bar{flex:1 1 240px; min-width:200px}` + `.placebo-track{min-width:80px}`. | подтверждено RERUN 3/19 (находка №28 аудита 2/19) |
| PA-04 | product-audit | Баг | Low | В калькуляторе добавление по Enter работает только по точному совпадению `id` (`c.id.toLowerCase() === v.toLowerCase()`), а не по частичному вводу (как в живом поиске на главной). Ввод "маг" + Enter — ничего не происходит. | docs/calculator.html:610-618 | Сделать добавление по Enter по первому совпадению из текущего результата поиска (`matchesQuery`), а не по точному `id`. | nouveau |
| PA-05 | product-audit | Улучшение | Low | На `compare.html` при добавлении через селекты/поиск нет тоста/обратной связи (только на sup-странице есть тост "Добавлено в сравнение"). | docs/compare.html:479-484 | Добавить тост при `addCmpId`, аналогично `docs/sup/*.html` стр. 323. | nouveau |
| PA-06 | product-audit | Доработка | Low | Радар профиля на `compare.html` работает только при ровно 2 добавках (`found.length !== 2 → canvas.hidden`), хотя можно добавить до 10. Неочевидно пользователю, почему радар пропал. | docs/compare.html:390 | Добавить подпись "Радар доступен при выборе 2 добавок" или явно скрывать/показывать с пояснением. | nouveau |
| PA-07 | product-audit | Баг | Low | Нет кастомной 404 страницы: несуществующий URL отдаёт дефолтную страницу сервера без навигации и возврата. | `docs/404.html` отсутствует | Добавить `docs/404.html` с навигацией и ссылкой на главную. | подтверждено RERUN 3/19 (находка №8 аудита 1/19) |

**Итого: 27 находок — Owner Manual Audit 7, site-navigation 9, visual-design-audit 11, product-audit 7.**

## 1b. Owner Manual Audit (продолжение, O-08..O-17)

| O-08 | Owner Manual Audit | Баг | Med | Кнопки "Цитировать" и "Прослушать" не работают. (Связано с QA-02: JS падает с TypeError в script.js). | docs/sup/*.html | Исправить JS-ошибку QA-02, затем проверить кнопки. |
| O-09 | Owner Manual Audit | Баг | Med | index.html — Кнопка "Кубик" (Random) редиректит на deadsno.github.io вместо локального относительного пути. Исправить на локальный. | docs/index.html | Заменить ссылку на локальный относительный путь. |
| O-10 | Owner Manual Audit | Улучшение | Low | index.html — Терминология. В тексте "ПОЛЕЗНО / Возможен / Не подтверждено" не совпадает с реальными надписями в UI. Привести к единому виду. | docs/index.html | Синхронизировать терминологию текста и UI. |
| O-11 | Owner Manual Audit | Улучшение | Low | index.html — Текст "Совместимость с лекарствами, а не «на всякий случай»" — кривая формулировка. Переписать понятным языком. | docs/index.html | Переписать формулировку понятным языком. |
| O-12 | Owner Manual Audit | Улучшение | Low | index.html — Сменить "Топ-3" на "Топ-10" по доказанности. | docs/index.html | Изменить "Топ-3" на "Топ-10". |
| O-13 | Owner Manual Audit | Баг | Med | sup/* (gialuronovaya-kislota и др.) — Ссылка на Ozon не открывается. Проверить корректность ссылок на магазины у всех 130 добавок. | docs/sup/*.html (130 страниц) | Проверить и исправить ссылки на магазины (Ozon и др.). |
| O-14 | Owner Manual Audit | Баг | Med | index.html — График "Доказательность" (пузырьковый). При наведении пропал тултип с названием добавки (в "Силе эффекта" работает). | docs/index.html | Восстановить тултип на графике "Доказательность". |
| O-15 | Owner Manual Audit | Улучшение | Low | support.html — Тексты "Проект делает один человек..." и "Другие способы помочь" (сообщите, добавить, поделиться). Нет реальных ссылок (кроме "Сообщите"). Добавить ссылки на форму обратной связи, на страницу сайта и т.д. | docs/support.html | Добавить реальные ссылки на форму обратной связи и страницу сайта. |
| O-16 | Owner Manual Audit | Улучшение | Low | map.html — Сгруппировать добавки по категориям (сон, спорт, сердце и т.д.), сейчас они идут единым списком, неудобно. | docs/map.html | Сгруппировать добавки по категориям. |
| O-17 | Owner Manual Audit | Баг | Low | UI — Побочные стрелки вверх/вниз (кнопки скролла) не выровнены по центру круга. Визуальный баг. | docs/*.html | Выровнять стрелки скролла по центру круга. |

**Итого Owner Manual Audit: 16 находок (O-01..O-17).**

## 4. Agent RERUN 4/19 (qa-deep-audit)

| QA-01 | qa-deep-audit | Баг | Med | 16 тестов пропущены вместо прохождения (pytest -q: 1963 passed, 16 skipped, 0 failed; ожидалось 1979 passed, 0 skipped). Все 16 пропуска из-за отсутствующей БД DuckDB (data/db/brain.duckdb не существует, нужен `python scripts/db/import_to_duckdb.py`). | tests/test_integration_api_db.py (6 тестов), tests/test_sql.py (10 тестов) | Восстановить БД DuckDB или гарантировать пропуск только при её отсутствии |

| QA-02 | qa-deep-audit | Баг | Blocker | 131 из 147 страниц имеют console.error. Все 130 sup-страниц + calculator.html: TypeError "(intermediate value)x8 ... is not a function" (Chart.js/промисы, script.js ~стр. 352). calculator.html дополнительно: "Cannot set properties of null (setting onclick)". | docs/sup/*.html (130 страниц), docs/calculator.html | Исправить JS-ошибку на всех затрагиваемых страницах |

| QA-03 | qa-deep-audit | Улучшение | Low | compare.html?ids=12345 принимает несуществующий ID, показывает чип "12345" и сообщение "Выберите минимум 2 добавки." — нет валидации существования ID в базе, сообщение вводит в заблуждение. | docs/compare.html | Добавить валидацию ID при загрузке через URL-параметр ?ids= |

| QA-04 | qa-deep-audit | Баг | Med | interactions.html при падении сети: ошибка "[mech] данные механизмов не загрузились: TypeError: Failed to fetch" (видимая в консоли и в UI), нет офлайн-фолбэка. | docs/interactions.html | Добавить обработку ошибки fetch с отображением пользователю офлайн-сообщения |

**Итого: 4 находки — qa-deep-audit 4 (Баг 3, Улучшение 1; Blocker 1, Med 2, Low 1).**

**Всего находок в отчёте: 47 (Owner Manual Audit 16, site-navigation 9, visual-design-audit 11, product-audit 7, qa-deep-audit 4).**

## Файл

`reports/AUDIT_MASTER_v565_rerun.md` (дописано в конец, находки Owner O-08..O-17 и QA-01..QA-04 добавлены к находкам навыков 1–3).

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 5. Agent RERUN 5/19 (accessibility-check)

Источник истины: .opencode/skills/accessibility-check/SKILL.md (v1.0, 2026-10-04). Проверок в скилле: 8 базовых категорий + 4 проектных. Выполнено: все на 147 HTML + 10 доп. проверок Блока 13.
Сервер: http://localhost:8000 (docs/), Playwright Chromium (browser_run_code_unsafe, browser_snapshot, browser_press_key).
Найдено: 15 (Blocker 4 / Med 9 / Low 2). Регрессии из Блока 13: 0 (все находки Блока 13 подтверждены или новые, предыдущие не отменены). Уникальных находок A11Y-01…A11Y-15 = 15; цифра 29 в прайме — ошибка, не число находок.

Находки, пересекающиеся с Owner Manual Audit / Аудитами 1/19-4/19, помечены «подтверждено RERUN 5/19».

| # | Категория | Критичность | Описание | Страница | Примечание |
|---|-----------|-------------|----------|----------|------------|
| A11Y-01 | accessibility-check | Blocker | Focusable element inside ria-hidden="true" container (кнопка внутри скрытой панели) | docs/atlas.html, docs/graph.html, docs/interactions.html | Подтверждено RERUN 5/19 |
| A11Y-02 | accessibility-check | Blocker | Страница без <h1> | docs/google4a9d23e35c6c3e23.html | Подтверждено RERUN 5/19 |
| A11Y-03 | accessibility-check | Blocker | <input type="text"> без видимого label / aria-label | docs/compare.html | Подтверждено RERUN 5/19 |
| A11Y-04 | accessibility-check | Blocker | <select> без видимого label / aria-label (2 шт.) | docs/compare.html | Подтверждено RERUN 5/19 |
| A11Y-05 | accessibility-check | Med | Пропуск уровня заголовка h1→H3 | docs/atlas.html, docs/compare.html, docs/graph.html, docs/interactions.html | Подтверждено RERUN 5/19 |
| A11Y-06 | accessibility-check | Low | Пустой заголовок H3 | docs/atlas.html, docs/graph.html, docs/interactions.html | Подтверждено RERUN 5/19 |
| A11Y-07 | accessibility-check | Med | Отсутствуют лендмарки <main>, <nav>, <header>, <footer> | docs/google4a9d23e35c6c3e23.html | Подтверждено RERUN 5/19 |
| A11Y-08 | accessibility-check | Med | Отсутствуют лендмарки <nav>, <header>, <footer> | docs/offline.html | Подтверждено RERUN 5/19 |
| A11Y-09 | accessibility-check | Med | Нет skip-to-content ссылки (#main / .skip-link) | docs/google4a9d23e35c6c3e23.html, docs/offline.html | Подтверждено RERUN 5/19 |
| A11Y-10 | accessibility-check | Med | Глобальный поиск #search: нет role="combobox" и нет aria-expanded; только sr-only <label> + placeholder | docs/index.html | Новый (Блок 13) |
| A11Y-11 | accessibility-check | Med | compare.html таблица: нет <caption>, у <th> нет scope="col" | docs/compare.html | Новый (Блок 13) |
| A11Y-12 | accessibility-check | Med | Нет тоста с aria-live="polite" для уведомления "Добавлено в сравнение" | docs/compare.html | Новый (Блок 13) |
| A11Y-13 | accessibility-check | Med | Skip-to-content: Enter на ссылке #main переключает URL, но фокус не переходит на <main> (остаётся на BODY) | docs/index.html | Новый (Блок 13, уточнение A1-09) |
| A11Y-14 | accessibility-check | Low | Калькулятор: нет отдельного объявления о добавлении добавки (aria-live="polite" охватывает только KPI-счётчики) | docs/calculator.html | Новый (Блок 13) |
| A11Y-15 | accessibility-check | Med | Граф связей (vis-network на canvas): недоступен с клавиатуры (нет фокуса/обработки клавиш на canvas) | docs/interactions.html | Новый (Блок 13) |

**Итого A11Y: 15 находок (A11Y-01..A11Y-15).**

### Дополнительно проверено (Блок 13, соответствие требованиям):
1. **Глобальный поиск**: Tab/Enter работают, Esc не обрабатывается; нет role="combobox"/aria-expanded → A11Y-10
2. **Кнопка «Сравнить»**: тост "Добавлено в сравнение" без aria-live → A11Y-12
3. **Новая шапка**: навигация с клавиатуры OK, focus-ring виден (синий outline), aria-current не найден (требует уточнения из A1-04)
4. **Калькулятор**: выбор добавки с клавиатуры OK; добавление не объявляется отдельно → A11Y-14
5. **compare.html таблица**: нет <caption>, нет scope="col" → A11Y-11
6. **Skip-to-content**: ссылка есть и фокусируема, но Enter не переносит фокус на <main> → A11Y-13
7. **Иерархия заголовков**: 1 h1 на страницу (кроме google4a9d23e35c6c3e23.html — нет h1 → A11Y-02), пропуски уровней (atlas/compare/graph/interactions → A11Y-05)
8. **Формы и кнопки**: у полей compare.html нет label → A11Y-03, A11Y-04; у всех кнопок есть доступное имя
9. **Динамический контент**: карточки sups/drugs доступны с клавиатуры (tabIndex=0, role=button, Enter/Space); граф на canvas — нет → A11Y-15
10. **Модалки/дропдауны**: калькулятор — <dialog> с showModal() (focus-trap + Esc OK); side-panel #nodeSidePanel — focus-trap на Tab, Esc закрывает, фокус возвращается на источник — OK

## 6. Agent RERUN 6/19 (mobile-deep-audit)

Источник: .opencode/skills/mobile-deep-audit/SKILL.md (v1.1, 2026-10-01). Проверено в Playwright Chromium на вьюпортах 320×568 (iPhone SE), 375×667, 390×844. Сервер http://localhost:8000 (docs/). Находки, пересекающиеся с A11Y/V/Owner, помечены «подтверждено RERUN 6/19» и не дублируются.

| # | Категория | Критичность | Описание | Страница | Примечание |
|---|-----------|-------------|----------|----------|------------|
| MB-01 | mobile-deep-audit | Blocker | Навигация шапки ломается на мобильных: ссылки навбара уходят за вьюпорт (координаты x до 1350–1517 px при вьюпорте 320 px), нет бургер-меню и нет горизонтального скролла навигации. Большинство разделов (Тренды, Связи, Сравнение, Карта, BI, FAQ, Обратная связь, Поддержать, Светлая тема) невидимы и недоступны с мобилки. | docs/index.html, docs/compare.html, docs/calculator.html, docs/interactions.html, docs/sup/*.html | Подтверждено RERUN 6/19 (пересекается с Owner O-01: шапка перегружена) |
| MB-02 | mobile-deep-audit | Med | interactions.html: 4-я вкладка «Лекарства» в табах «Режимы связей» начинается на x=349 px > вьюпорт 320 px, табы не помещаются в строку, часть скрыта за краем экрана. | docs/interactions.html | |
| MB-03 | mobile-deep-audit | Med | calculator.html: TypeError «Cannot set properties of null (setting 'onclick')» (стр. 645, 1110), калькулятор не инициализируется и не работает, в т.ч. на мобилках. | docs/calculator.html | Подтверждено RERUN 6/19 (пересекается с QA-02) |
| MB-04 | mobile-deep-audit | Low | Все страницы: используется устаревший `<meta name="apple-mobile-web-app-capable" content="yes">` без `<meta name="mobile-web-app-capable" content="yes">` (Chrome warning в консоли). | все HTML | |

**Итого mobile-deep-audit: 4 находки (Blocker 1, Med 2, Low 1).**

Регрессии из Блока 13: навигация шапки подтверждена — ломается на 320/375/390 px (MB-01); радар профиля 520×520 и селекторы 180+180=360 px > 320 px подтверждены (V-01, V-05), не дублируются.


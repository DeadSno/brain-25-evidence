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

## 7. Agent RERUN 7/19 (seo-check)

Источник истины: .opencode/skills/seo-check/SKILL.md (v1.0, 2026-10-04). Проверок в скилле: 10 базовых + 3 проектных = 13. Выполнено: все 13 на 147 HTML (docs/*.html=16, docs/sup/*.html=131).
Сервер: http://localhost:8000 не отвечает — проверка статическим парсингом html.parser (file:// Playwright недоступен, сеть не работает).
Sitemap.xml: 143 URL (12 корневых + 131 в docs/sup/). compare.html ЕСТЬ. graph.html/atlas.html НЕТ (правильно — редиректы). offline.html и google*.html намеренно не в sitemap. lastmod=2026-10-19 все. Битых ссылок в sitemap нет.
Robots.txt: Allow:/, Sitemap: https://deadsno.github.io/brain-25-evidence/sitemap.xml, не блокирует важные страницы.
Meta-теги: title (30-60 символов), description (120-160), canonical, og:title/description/image, twitter:card — presenti на всех 145 контентных страницах. lang=ru, viewport везде. h1=1 на каждой странице (кроме служебных google*/offline). JSON-LD валиден на index, calculator, interactions, всех 131 sup, trends, map, methodology, faq, glossary, feedback, support, privacy. Дубли title/description отсутствуют (все 130 sup карточек имеют уникальные title/description). Битых внутренних ссылок нет. og:image=https://deadsno.github.io/brain-25-evidence/og.png корректен.
Служебные файлы google4a9d23e35c6c3e23.html (верификация Google) и offline.html (офлайн-заглушка SW) не в sitemap по 설계, без полных мета-тегов — не являются находками SEO.

Находки, пересекающиеся с A11Y (иерархия заголовков), помечены «подтверждено RERUN 7/19».

| # | Категория | Критичность | Описание | Страница | Примечание |
|---|-----------|-------------|----------|----------|------------|
| SEO-01 | seo-check | Баг | Med | meta description длиной 103 символов (норма 120-160): «Сравнение БАДов рядом: грейд, эффекты, дозировка, безопаснос…» | docs/compare.html | |
| SEO-02 | seo-check | Баг | Med | Отсутствует JSON-LD (Schema.org) на странице сравнения (есть на index/calculator/interactions/всех sup) | docs/compare.html | |
| SEO-03 | seo-check | Улучшение | Low | Есть h1, но нет h2/h3 — пустая иерархия заголовков | docs/feedback.html | Подтверждено RERUN 7/19 (пересекается с A11Y иерархия заголовков) |
| SEO-04 | seo-check | Улучшение | Low | Есть h1, но нет h2/h3 — пустая иерархия заголовков (редирект-страница на interactions.html#mech) | docs/atlas.html | Подтверждено RERUN 7/19 (пересекается с A11Y иерархия заголовков) |
| SEO-05 | seo-check | Улучшение | Low | Есть h1, но нет h2/h3 — пустая иерархия заголовков (редирект-страница на interactions.html#graph) | docs/graph.html | Подтверждено RERUN 7/19 (пересекается с A11Y иерархия заголовков) |
| SEO-06 | seo-check | Улучшение | Low | Есть h1, но нет h2/h3 — пустая иерархия заголовков | docs/map.html | Подтверждено RERUN 7/19 (пересекается с A11Y иерархия заголовков) |

**Итого seo-check: 6 находок (Blocker 0 / Med 2 / Low 4).**

**Всего находок в отчёте: 47 + 6 = 53.**

## 8. Agent RERUN 8/19 (data-audit)

Источник истины: `C:\analytics\brain-25-evidence\.opencode\skills\data-audit\SKILL.md` (v1.0, 2026-10-04). Проверок в скилле: 5 слоёв. Выполнено: слои 1–2 (`data.json` + производные) и слой 4 (сырые `data/papers/`, `data/pmc/`); слой 3 (DuckDB) пропущен — файл занят процессом `node.exe`, скилл запрещает прямой коннект; слой 5 пропущен (RUN_EXTERNAL не задан).

Найдено: 3 (Blocker 0 / Med 3 / Low 0). Регрессии из Блока 13: 0.

Находки, пересекающиеся с Owner/A11Y/V/MB/PA/QA/SEO, отсутствуют — не дублируются.

| DA-01 | data-audit | Баг | Med | `citations = null` у записи «Омега-3». Базовая линия требует 0 (все 130 заполнены); поле не int. | docs/data.json + docs/api/v1/supplements.json (null синхронизировано) | `isinstance(citations, int)` → False; 1 запись |
| DA-02 | data-audit | Баг | Med | `forms` содержит «капсул/таблеток» у 2 записей (Лаванда, MSM). После Блока 3 должно быть «цитрат/моногидрат». | docs/data.json | 2 записи: Лаванда, MSM |
| DA-03 | data-audit | Баг | Med | Инверсия грейда: `S. boulardii`, `hedges_g = -1.63` (<= 0), но `grade = B`. Должна быть понижена (не понижена). | docs/data.json | 1 запись |

### Проверено, не находки (в норме)
- JSON валиден; 130 записей; дублей id/title/name нет; все обязательные поля (`name`, `category`, `dosage`, `grade`, `forms`, `citations`, `hedges_g`) на месте.
- Grades: A=6 / B=23 / C=52 / D=49 — совпадает с базовой линией.
- scienceIndex: все int, диапазон 2…10666, значений 0 нет.
- updated: все 130/130, формат ISO `YYYY-MM-DD`.
- Категории: 59 уникальных (сводили 79→59), опечаток не обнаружено, формат «путь через `/`» соблюдён.
- forms: заполнено 95/130 (35 пустых — не нарушение схемы, ориентира нет).
- dosage: пустых строк 0; 58 записей не строго `min-max unit` — легитимное разнообразие форм дозировки БАДов, не баг.
- Производные: `api/v1/supplements.json` (count=130, 130 записей), `data_index.json` (130), `effect_tags.json` (130 ключей), `api/v1/index.json` (count=130, сумма грейдов=130). Порядок `id` и грейды совпадают с `data.json` (0 расхождений); `generated_at` не старше `data.json`.
- Кросс-валидация: JSON-LD есть на всех 131 `sup`-странице, но поля `grade` в JSON-LD нет (только `name/description/category/url`); категория в `about.category` совпадает с `data.json`. Грейд не дублируется в JSON-LD — факт, не баг.
- Слой 4: 12 файлов `data/papers/` + 1 `data/pmc/`; U+FFFD = 18 символов (совпадает с базовой линией).

**Итого data-audit: 3 находки (DA-01..DA-03).**

**Всего находок в отчёте: 53 + 3 = 56.**

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 9. Agent RERUN 9/19 (core-web-vitals)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\core-web-vitals\SKILL.md (v1.0, 2026-10-04). Проверок в скилле: 3 (базовый workflow + 2 проектных: vis-network destroy при переключении табов interactions.html, вес карточек/данных compare.html). Выполнено: 3 — измерено на 4 ключевых страницах + статические размеры ресурсов + проверка утечек памяти.
Сервер: http://localhost:8000 (docs/), Playwright PerformanceObserver (LCP/CLS/FCP/TTFB; INP не замеряется — Event Timing API не ловит синтетические клики Playwright, по guidance скилла report as not measured).

### Измеренные CWV:
| Страница | TTFB | FCP | LCP | CLS | Оценка |
|---|---|---|---|---|---|
| docs/index.html | 32 ms | 804 ms | 804 ms | — | Good |
| docs/compare.html | 2 ms | 60 ms | 60 ms | 0.866 | **CLS POOR** |
| docs/interactions.html | 1 ms | 76 ms | 76 ms | 0.026 | Good |
| docs/sup/magniy.html | 2 ms | 44 ms | 44 ms | 0 | Good |

### Размер ресурсов (статика):
data.json 740.6 KB, vis-network 672.8 KB (defer), chart.umd-4.4.1.min.js 200.6 KB (нет defer), style.css 169.8 KB, script.js 72.3 KB, i18n.js 27.4 KB (нет defer), bootstrap 78.5 KB. Рендер-блокирующие в head index.html: i18n.js + chart.js + style.css (~397 KB).

### Утечки памяти:
vis-network (interactions.html): destroy ЕСТЬ при переключении табов (стр. 866-867, 1296, 1365-1366) НО при Retry (стр. 758-766) `network = null; nodesDs = null; edgesDs = null;` БЕЗ destroy → утечка инстанса/слушателей.
TTS (sup/*.html): speechSynthesis.speak(utterance) без onend/cancel/отчистки → накопление utterance.
loadGzJson (script.js:374) объявлен НЕ ИЗЫВАЕТСЯ — мёртвый код; данные грузятся uncompressed через fetchJson (data_index.json 86 KB).

### Дополнительно проверено (Блок 13):
- showToast: определён отдельно на каждой странице (дублирование кода), но реализован fixed+opacity → верстка не скачет, CLS не проблема (не находка).
- Граф (interactions.html): 4 таба, searchbox «Поиск по графу», рендерится без ошибок, память ~20 МБ; CPU-throttling не применим (page._client undefined в обёртке).

Найдено: 5 (Blocker 1 / Med 2 / Low 2). Регрессии из Блока 13: 1 (CLS compare.html — дропдаун поиска / скелетоны).

Находки, пересекающиеся с Owner/A11Y/V/MB/PA/QA/SEO/data, отсутствуют — не дублируются.

| # | Категория | Критичность | Описание | Страница | Примечание |
|---|-----------|-------------|----------|----------|------------|
| CWV-01 | core-web-vitals | Баг | Blocker | CLS 0.866 (POOR > 0.25) на compare.html — скачок верстки после загрузки дропдауна поиска/скелетонов. | docs/compare.html | FCP 60 ms, LCP 60 ms, CLS 0.866 (Playwright PerformanceObserver) |
| CWV-02 | core-web-vitals | Баг | Med | Утечка vis-network при Retry: `network = null` без `network.destroy()` — инстанс и слушатели остаются в памяти. | docs/interactions.html:758-766 | destroy есть только при переключении табов (стр. 866-867, 1296, 1365-1366) |
| CWV-03 | core-web-vitals | Улучшение | Low | loadGzJson (script.js:374) объявлен, но не вызывается — мёртвый код; данные грузятся uncompressed через fetchJson (data_index.json 86 KB). | docs/script.js:374 | gz-данные не используются |
| CWV-04 | core-web-vitals | Баг | Med | Рендер-блокирующие ресурсы в head index.html: i18n.js (27.4 KB, стр. 6), chart.umd-4.4.1.min.js (200.6 KB, стр. 47, нет defer), style.css (169.8 KB, стр. 64) — ~397 KB блокируют первый рендер. | docs/index.html:6, 47, 64 | добавить defer / перенести в конец тела |
| CWV-05 | core-web-vitals | Улучшение | Low | TTS: speechSynthesis.speak(utterance) без onend/cancel/отчистки — накопление utterance в памяти после прочтения. | docs/sup/*.html | добавить отчистку utterance после onend |

**Итого core-web-vitals: 5 находок (CWV-01..CWV-05).**

**Всего находок в отчёте: 56 + 5 = 61.**

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 10. Agent RERUN 10/19 (i18n-rtl-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\i18n-rtl-audit\SKILL.md (v1.0, 2026-10-04). Проверок в скилле: <html lang>, dir, pseudo-localization, hardcoded strings, покрытие словарём (compare.html + 4 таба interactions.html #graph/#mech/#sups/#drugs), RTL. Выполнено: все на 147 HTML + JS (docs/script.js, calculator.html, interactions.html, 131 docs/sup/*.html).

Найдено: 7 (Blocker 0 / Med 4 / Low 3). Регрессии из Блока 13: 1 (I18N-01 тост).

Находки, пересекающиеся с уже записанными (A11Y-12'отсутствие aria-live на тосте', V-10'нет CSS тоста', PA-05'нет тоста на compare'), не дублируются — это разные находки (доступность/оформление/отсутствие, а не захардкоженная строка без t()).

| # | Категория | Критичность | Описание | Где | Примечание |
|---|-----------|-------------|----------|-----|------------|
| I18N-01 | Баг | Med | `showToast('Добавлено в сравнение')` — захардкоженная строка, не через `t()`, ключа нет в словаре `docs/i18n.js` | все 131 `docs/sup/*.html` | Регрессия Блока 13 |
| I18N-02 | Баг | Med | Кнопки "Цитировать" / "Прослушать" (TTS) — текст кнопки и `aria-label` захардкожены, не через `t()` | все 131 `docs/sup/*.html` | Владелец O-08: кнопки не работают (JS падает, QA-02) |
| I18N-03 | Баг | Med | `compare.html:362` — `errEl.textContent = 'Добавки не найдены в базе.'` захардкожено | docs/compare.html:362 | ключа в словаре нет |
| I18N-04 | Баг | Low | `compare.html:120` — `placeholder="Поиск добавки…"` без `data-i18n-placeholder` | docs/compare.html:120 | |
| I18N-05 | Баг | Low | `compare.html:247` — `'Открыть ↗'` захардкожено (в словаре есть `common.openCard`) | docs/compare.html:247 | |
| I18N-06 | Баг | Low | `interactions.html:294` — `graphSearch` `placeholder="Поиск добавки..."` без `data-i18n-placeholder` | docs/interactions.html:294 | |
| I18N-07 | Баг | Med | `interactions.html:312,332,347,366` — "Ничего не найдено." захардкожено в HTML (ключи `int.graphEmpty`/`int.mechEmpty`/`int.supsEmpty`/`int.drugsEmpty` есть в словаре, но `data-i18n-text` на div через `textContent` затрёт кнопку Сбросить) | docs/interactions.html:312-366 | |

**Итого i18n-rtl-audit: 7 находок.**

### Проверено, не находки
- `<html lang="ru" dir="ltr">` на всех 147 HTML — OK
- RTL-правила `[dir="rtl"]` не требуются для ru-RU (русский — LTR); в style.css:2035 только комментарий
- `toLocaleString(LOCALE)` в script.js:1000 — OK
- `GRADE_LABEL` через `t("grade.A..D")` — OK
- compare.html табличные метки через `t()` с фолбэком — OK
- Плейсхолдеры index/calculator/sup/index через `data-i18n-placeholder` — OK

**Всего находок в отчёте: 61 + 7 = 68.**

## 11. Agent RERUN 11/19 (legal-compliance-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\legal-compliance-audit\SKILL.md (v1.0, 2026-10-04). Проверок в скилле: 7 разделов (медицинские дисклеймеры, атрибуция источников, cookie и трекеры, персональные данные 152-ФЗ, ФЗ «О рекламе», GDPR, отзывы). Выполнено: все 7 разделов + 8 пунктов задачи на 147 HTML (docs/*.html=16, docs/sup/*.html=131). Не заменяет юриста, не даёт юридических советов.

Найдено: 3 (Blocker 0 / Med 2 / Low 1). Регрессии из Блока 13: 0.

Находки, пересекающиеся с уже записанными в файле, отсутствуют — не дублируются.

| # | Категория | Критичность | Описание | Где | Примечание |
|---|-----------|-------------|----------|-----|------------|
| LEGAL-01 | legal-compliance-audit | Мед | Яндекс.Метрика (счётчик 112465667) установлена на 142 из 147 страниц, включая все 131 sup-страницу. В базовой линии скилла (2026-10-03) — 11 страниц. Баннер работает и сбор без согласия отсутствует, но охват трекинга резко расширен. | все HTML кроме graph.html, atlas.html, compare.html, google4a9d23e35c6c3e23.html, offline.html | Баннер и блокировка до同意 подтверждены в cookie-banner.js / metrika.js |
| LEGAL-02 | legal-compliance-audit | Мед | Нет текстового предупреждения о переходе на сторонние ресурсы (Ozon, WB, Я.Маркет) на страницах добавок. Ссылки имеют target="_blank" rel="noopener" и иконку ↗, но нет уведомления «Вы переходите на сторонний сайт». | docs/sup/*.html (131 страниц), блок shop-section | Пересекается с Owner O-13 (ссылки на магазины) — но отсутствие предупреждения о переходе — отдельная находка |
| LEGAL-03 | legal-compliance-audit | Low | Контакт для связи (email deadsno1613@gmail.com) не выведен в общий футер на всех страницах. Есть только на privacy.html и через страницу feedback.html. На страницах sup/index в футере нет email. | docs/sup/*.html, docs/index.html — футер | Контакт есть в privacy.html:202-207 и feedback.html (форма Яндекс Формы) |

### Подтверждено, не находки (в норме)

- **Cookie-баннер работает**: показывается при отсутствии cookie-consent, скрывается после клика «Принять»/«Отклонить», Метрика грузится только после «Принять» (cookie-banner.js, metrika.js).
- **Вебвизора нет**, noscript-пиксель не вставляется в разметку, данные не собираются до согласия (подтверждено в коде metrika.js).
- **privacy.html актуальна** (обновлено 10.10.2026): упоминает Яндекс.Метрику (счетчик 112465667), есть ссылки на compare.html и interactions.html, есть раздел GDPR, право отказаться (удаление ключа cookie-consent), доступ к данным через email, сроки хранения.
- **Дисклеймер «Не медицинская рекомендация» на 145 из 147 страниц** (всех, кроме google4a9d23e35c6c3e23.html — верификация Google, и offline.html — офлайн-заглушка). Есть на всех 131 sup-странице и на compare.html.
- **Скрытой рекламы / партнерских ссылок без маркировки не найдено**. trustbar «Без рекламы» на всех страницах. yoomoney.ru на 2 страницах (index, support) — платёжный виджет, не реклама.
- **GDPR**: возможность отозвать согласие есть (удаление ключа cookie-consent), доступ к персональным данным — через email deadsno1613@gmail.com (privacy.html:180-183, 202-207).

**Итого legal-compliance-audit: 3 находки (LEGAL-01..LEGAL-03).**

**Всего находок в отчёте: 68 + 3 = 71.**

## Файл

`reports/AUDIT_MASTER_v565_rerun.md` (дописан раздел 11 legal-compliance-audit, находки LEGAL-01..LEGAL-03 добавлены в конец).

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 12. Agent RERUN 12/19 (ui-ux-deep-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\ui-ux-deep-audit\SKILL.md (v1.1, 2026-10-01). Проверок в скилле: 9 (1 иерархия/типографика, 2 ритм/отступы, 3 пустые состояния, 4 loading, 5 error, 6 микроинтеракции, 7 обратная связь, 8 иерархия внимания, 9 дублирование). Выполнено: все 9 на ключевых страницах проекта (docs/index.html, docs/compare.html, docs/interactions.html, docs/calculator.html, representative docs/sup/*.html). Метод: статический разбор HTML/JS (запрос к файлу, не к памяти) с фокусом на состояния (loading/empty/error), навигацию и интуитивность, обратную связь, мобильный UX, микрокопирайтинг.

Находки, пересекающиеся с уже записанными (A1-07, PA-02, PA-05, PA-06, QA-04, V-09, V-10, I18N-01, MB-01), не дублируются.

| # | Категория | Критичность | Описание | Страница | Примечание |
|---|-----------|-------------|----------|----------|------------|
| UX-01 | ui-ux-deep-audit | Баг | Low | На главной кнопка «Сравнить» (renderCompare): при ошибке загрузки data.json скрипт завершается молчаливым `return`, в зоне результата ничего не появляется, пользователь не получает обратной связи. | docs/index.html (script.js ~1235-1247) | Нет UI-обратной связи при сбое загрузки данных сравнения. |
| UX-02 | ui-ux-deep-audit | Баг | Low | На странице сравнения при ошибке загрузки каталога data_index.json выводится «Не удалось загрузить каталог добавок» без кнопки «Повторить»/перезагрузки — тупиковое состояние. | docs/compare.html (~277-281) | На главной при аналогичном сбое загрузки есть кнопка «Повторить», здесь её нет. |
| UX-03 | ui-ux-deep-audit | Улучшение | Low | Кнопка «Кубик» (🎲) — только эмодзи без видимой текстовой подписи/тултипа (есть только aria-label), визуально unclear назначение, особенно на мобильных. | все HTML (id="randomBtn") | aria-label «Удиви меня — случайную добавку» не заменяет видимую подпись. |
| UX-04 | ui-ux-deep-audit | Улучшение | Low | На карточке добавки (sup) нет кнопки «Назад»; возврата в один клик нет, есть только хлебные крошки (Главная → Каталог → Название). | docs/sup/*.html | Хлебные крошки частично перекрывают потребность. |

**Итого ui-ux-deep-audit: 4 находки (Blocker 0 / Med 0 / Low 4).** Регрессии из Блока 13: 0.

**Всего находок в отчёте: 71 + 4 = 75.**

## Файл

`reports/AUDIT_MASTER_v565_rerun.md` (дописан раздел 12 ui-ux-deep-audit, находки UX-01..UX-04 добавлены в конец).

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 13. Agent RERUN 13/19 (project-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\project-audit\SKILL.md (v1.1, 2026-10-01). Проверок в скилле: 12. Выполнено: все 12 на весь проект.

Находки, пересекающиеся с уже записанными (QA-01 DuckDB, CWV-03 loadGzJson мёртвый код, и др.), не дублируются.

| # | Категория | Критичность | Описание | Где | Решение |
|---|-----------|-------------|----------|-----|---------|
| PRJ-01 | project-audit | Баг | Med | Три `.json.gz` файла отслеживаются в git, но не добавлены в `.gitignore` (в игноре только `.json` без `.gz`, стр. 261-266): `data/journals/nlm_catalog.json.gz` (2,1 MB), `data/papers/papers_slim.json.gz` (3,5 MB), `data/papers/stats_claims.json.gz` (0,38 MB). Большие бинарные артефакты в репозитории. | `data/journals/`, `data/papers/` | Добавить `*.json.gz` в `.gitignore`, убрать файлы из git tracking (`git rm --cached`). |
| PRJ-02 | project-audit | Улучшение | Low | Дубли старых отчётов в `reports/` рядом с текущим `AUDIT_MASTER_v565_rerun.md`: `AUDIT_MASTER.md` (66,5 KB), `AUDIT_MASTER_v565.md` (62,7 KB). Старые версии не архивированы и не удалены. | `reports/` | Архивировать в `reports/archive/` или удалить старые версии, оставить только актуальный rerun. |
| PRJ-03 | project-audit | Баг | Low | Файл с `_old` в имени нарушает п.5 скилла (файлы с `_test`/`_old`/`_bak`/`_tmp` в имени). | `logs/_idx_old.png` (3295 байт) | Переименовать или удалить. |
| PRJ-04 | project-audit | Улучшение | Low | Пустые папки не используются: `.gcourer/`, `.github/`, `lib/` (корень); `docs/api/`, `docs/reports/`; `reports/desktop-screens/`, `reports/archive/v561/`; `tests/fixtures/`, `tests/snapshots/`. | корень, `docs/`, `reports/`, `tests/` | Удалить пустые папки или заполнить. |
| PRJ-05 | project-audit | Доработка | Low | Скрипты в `scripts/` без единого префикса `build_`/`fill_`/`update_` — 89 `.py` файлов с разными префиксами: `analyze_`, `apply_`, `audit_`, `check_`, `cleanup_`, `compress_`, `dedupe_`, `enrich_`, `extract_`, `fetch_`, `fix_`, `graph_`, `join_`, `make_`, `migrate_`, `parse_`, `rebuild_`, `recalc_`, `refresh_`, `review_`, `search_`, `sync_`, `ui_verify_`, `validate_`, `verify_`, `view_`. | `scripts/` | Привести к единому префиксу или задокументировать исключения. |
| PRJ-06 | project-audit | Баг | Low | В корне репозитория артефакты сессий/диагностики, не в `.gitignore`: `_audit_script.js`, `serve_log.txt`, `snap_head_chromium.xml`, `pytest_collect.txt`, `pytest_final.txt`, `pytest_out.txt`. | корень | Добавить в `.gitignore` или перенести в `reports/_tmp_*`. |
| PRJ-07 | project-audit | Улучшение | Low | `view_catalog.py` помечен как "delete" (одноразовый скрипт, без docstring), но ещё в репозитории. | `scripts/view_catalog.py` | Удалить или задокументировать как инфраструктурный. |
| PRJ-08 | project-audit | Доработка | Low | `CONVENTIONS.md` не описывает полную структуру папок проекта — только граф (`graph_data.json`, `graph_positions.json`) и редиректы `graph.html`/`atlas.html`. Нет разделов о `scripts/`, `data/`, `tests/`, `reports/`. | `CONVENTIONS.md` | Дополнить актуальной структурой папок. |
| PRJ-09 | project-audit | Баг | Med | `Pillow` отсутствует в `requirements.txt` (только в `requirements-dev.txt`), `scripts/compress_snapshots.py:178` требует PIL — скрипт не запустится на машине с только `requirements.txt`. | `requirements.txt`, `scripts/compress_snapshots.py` | Добавить `Pillow` в `requirements.txt`. |
| PRJ-10 | project-audit | Баг | Med | Версия в `docs/version.json` (`app: 5.6.5`) не совпадает с последним тегом git (`v5.6.4`). HEAD: `v5.6.3-314-gc1b3418`. Ветка `v5.6.5-dev`, но тег `v5.6.5` не создан. | `docs/version.json` | Синхронизировать версию с тегом или создать тег `v5.6.5`. |

**Итого project-audit: 10 находок (Баг 5, Улучшение 3, Доработка 2; Blocker 0 / Med 3 / Low 7). Регрессии из Блока 13: 0.**

**Всего находок в отчёте: 75 + 10 = 85.**

## Файл

`reports/AUDIT_MASTER_v565_rerun.md` (дописан раздел 13 project-audit, находки PRJ-01..PRJ-10 добавлены в конец).

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 14. Agent RERUN 15/19 (pwa-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\pwa-audit\SKILL.md (v1.1, 2026-10-01). Проверок в скилле: 16 (15 обязательных + 1 опциональная). Выполнено: все на 147 HTML (docs/*.html=16, docs/sup/*.html=131) + docs/sw.js + docs/pwa.js + docs/manifest.webmanifest + docs/icons/*.png.

### Проверено (все пройдено, проблем не найдено):

| Проверка | Статус | Детали |
|----------|--------|--------|
| manifest.webmanifest | OK | валидный JSON, поля: name, short_name, start_url, display=standalone, icons (4: 192/512 × 2), theme_color, background_color, shortcuts |
| sw.js | OK | CACHE_VERSION = 'v111', бамплен в v110→v111 после Блока 13 |
| pwa.js | OK | регистрация через navigator.serviceWorker.register, бейдж офлайн-режима |
| Icons | OK | 192.png, 512.png, maskable-192.png, maskable-512.png |
| HTML подключение | OK | все 147 страниц имеют <link rel="manifest"> и <script src="pwa.js"> |
| meta theme-color | OK | на всех 147 страницах (light #f5f5f7, dark #1c1c1e) |
| SW стратегия | OK | cache-first для статики, network-first для data*.json, stale-while-revalidate для 125 sup/*.html |

### Специальные проверки Блока 13 (task):

1. **CACHE_VERSION**: v111, поднят в v110→v111 специально для изменений Блока 13 (compare.html, interactions.html, 131 sup-страницы в STATIC_ASSETS). ✓
2. **Кэширование страниц**: compare.html ✓ (STATIC_ASSETS стр. 323), index.html ✓ (стр. 321), calculator.html ✓ (стр. 322), interactions.html ✓ (стр. 325), sup/index.html ✓ (стр. 344), sup/magniy.html ✓ (стр. 346); остальные 125 sup/*.html — stale-while-revalidate (стр. 312-312, по дизайну).
3. **Офлайн**: offline.html ✓ (STATIC_ASSETS стр. 334, fallback для навигации), sup/magniy.html ✓ (в кэше, precached), compare.html ✓ (в кэше, precached).
4. **Регистрация SW**: pwa.js на всех 147 страницах ✓.
5. **Конфликты SW с поиском/дропдауном**: нет — data*.json через network-first (DATA_RE), API не кэшируется cache-first, ошибок регистрации SW в коде нет.
6. **<meta name="mobile-web-app-capable">**: современный вариант (без "apple-") отсутствует, только apple-mobile-web-app-capable на 5 страницах — пересекается с **MB-04** (mobile-deep-audit, Low), не дублируем.

Найдено: 0 (Blocker 0 / Med 0 / Low 0). Регрессии из Блока 13: 0.

Итого pwa-audit: 0 находок.

**Всего находок в отчёте: 85.**

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**

## 16. Agent RERUN 16/19 (docs-sync)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\docs-sync\SKILL.md (v1.1, 2026-10-01). Проверок в скилле: 6 (битые ссылки, навигация, устаревшие упоминания, дубли, форматирование). Выполнено: все 6 на docs/*.md (46 файлов) + корневые *.md (ROADMAP.md, CHANGELOG.md, CONVENTIONS.md, SKILLS_INDEX.md, README.md) + docs/api/v1/openapi.yaml.

Проверено по проверкам скилла:
1. **Битые ссылки** — все relative-ссылки в docs/*.md живы (проверены цели: nfr.md, erd.md, rtm.md, srs.md, user_stories.md, bpmn_pipeline.md, architecture_diagrams.md, data_dictionary.md, definition_of_ready.md, deployment.md, impact_analysis.md, methodology.html, faq.html, glossary.md, openapi.yaml, errors.md, sequence.md, postman_collection.json, batch_pipeline.bpmn, screenshot.png, ../ARCHITECTURE.md, ../tests/*.py). Битых не найдено.
2. **Навигация** — README.md ссылается на все ключевые артефакты (docs/srs.md, docs/rtm.md, docs/erd.md, docs/nfr.md, docs/bpmn_pipeline.md, docs/dmn.md, docs/api/v1/openapi.yaml, docs/user_stories.md, docs/adr/README.md) — все существуют.
3. **Устаревшие упоминания** — версии ниже v3.7 и числа 103/113/94/9074/5135 встречаются только в исторических разделах CHANGELOG.md и в data/processed/audit/*.md (метка карточки v3.0); актуальных ложных фактов не найдено.
4. **Дубли в docs/** — явных дублей содержимого и близких имён не обнаружено.
5. **Форматирование** — docs/*.md в LF (нет CRLF), тройные backticks парные.

Расширенные проверки задачи (ROADMAP/CHANGELOG/CONVENTIONS/SKILLS_INDEX/README/API): найдены рассинхроны документации с фактическим состоянием репозитория.

Находки, пересекающиеся с уже записанными (PRJ-10 — версия version.json vs git-тег; QA-01 — ожидаемое число тестов 1979), не дублируются — это отдельные документы (текст README, текст CHANGELOG, текст ROADMAP).

| # | Категория | Критичность | Описание | Где | Примечание |
| DOC-01 | docs-sync | Баг | Med | ROADMAP.md v5.6.5 обозначен как "следующий цикл" с остатком ~30-50 ч / 2-3 недели, но CHANGELOG.md уже содержит секцию [v5.6.5] — 2026-10-17 (батч 2 реализован), docs/version.json = app 5.6.5, тег v5.6.5 не создан (HEAD: v5.6.3-314-gc1b3418), нет v5.6.6, хотя v5.7 уже в плане. Дорожная карта не актуализирована под реальный статус v5.6.5. | ROADMAP.md, CHANGELOG.md, docs/version.json |
| DOC-02 | docs-sync | Баг | Med | ROADMAP.md v5.6.5 блок "Данные есть — показать" не отмечает выполненные пункты: "Compare 3+" и "PMID counter" реализованы (коммит 6051419 feat(ui): compare 3+ supplements + PMID counter), но в дорожной карте остались без галочки ✅. | ROADMAP.md |
| DOC-03 | docs-sync | Баг | Med | CHANGELOG.md секция [v5.6.5] неполная: описывает только батч 2 (pages-review, до коммитов 86717bd/4779efd), но не отражает ~25+ последующих коммитов v5.6.5 до HEAD c1b3418: unified navbar (1d982b6), i18n-извлечение JS-P2-02 (78d8aa3), 10 популярных тайлов (084ff83), пересборка эталонов (39b7f0b/36d6403), анимации/скелетоны (6657bd7), данные DATA-P2-09/10/11/13/14 (категории 79→59, f0903d6), заполнение форм (6240d12), shop-ссылки (417e428), человекочитаемые данные (96df864), мобильная вёрстка (9ef76b0), UX-фикс поиска (9048ca3), закрытие data-null (ed6317f), 12 фиксов аудита (45e7ed2). Ченджлог не соответствует фактическим коммитам. | CHANGELOG.md |
| DOC-04 | docs-sync | Баг | Med | README.md раздел "Статус релиза": v5.6.3 заявлена как актуальная версия (docs/version.json: app: 5.6.3), фактически version.json = app 5.6.5 и CHANGELOG содержит [v5.6.5]. Цифры тестов в README (1079 собрано, 878 passed, 2 skipped, 199 браузерных) устарели — фактически version.json tests = 1979 (подтверждено qa-deep-аудитом QA-01). | README.md |
| DOC-05 | docs-sync | Улучшение | Low | SKILLS_INDEX.md раздел "Команды": "pytest -q — все тесты (1746 passed, 237 skipped, 1983 всего)" — расходится с docs/version.json (tests: 1979). | SKILLS_INDEX.md, docs/version.json |
| DOC-06 | docs-sync | Доработка | Low | README.md раздел "Структура репозитория" описывает graph.html и atlas.html как полноценные страницы ("граф 130 узлов / 1982 связи", "атлас: хабы тегов × 130 добавок"), но по CHANGELOG v5.6.5 они стали редирект-заглушками на interactions.html (#graph / #mech). Описание не соответствует факту. | README.md |

Итого docs-sync: 6 находок (Баг 4, Улучшение 1, Доработка 1; Blocker 0 / Med 4 / Low 2). Регрессии из Блока 13: 0.

**Всего находок в отчёте: 85 + 6 = 91.**

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**


## 17. Agent RERUN 17/19 (release-check)

Источник истины: `C:\analytics\brain-25-evidence\.opencode\skills\release-check\SKILL.md` (v1.2, 2026-10-13). Проверок в скилле: 5 блоков (Git-статус, Тесты, Данные, Документация, Сообщение коммита). Выполнено: все 5.

### Результаты проверок

| # | Блок | Статус | Детали |
|---|------|--------|--------|
| 1 | Git-статус | ⚠️ не чисто | `git status --short`: modified `reports/AUDIT_MASTER_v565_rerun.md` (ожидаемо — ведётся аудит); untracked артефакты `_audit_script.js`, `pytest_collect.txt`, `pytest_final.txt`, `pytest_out.txt`, `serve_log.txt`, `reports/QA_AUDIT_RAW.json`. Нет staged `.env`/`*.key`/`*.secret`, нет файлов > 10 MB. Пересекается с PRJ-06 (артефакты в корне) — не дублируем. |
| 2 | Тесты | ✅ пройдено | `pytest -q` → 1979 passed, 0 failed, 0 skipped (492.4 с). Совпадает с `docs/version.json` (tests: 1979). QA-01 (16 skipped) более не актуальна, старая находка не удаляется. |
| 3 | Данные | ✅ пройдено | `docs/data.json`, `docs/api/v1/*.json`, `docs/effect_tags.json` — валидный JSON. |
| 4 | Документация | ⚠️ ожидаемо | `docs/version.json` (app: 5.6.5) опережает последний тег `v5.6.4`; тег `v5.6.5` не создан. Ожидаемо перед релизом. Пересекается с PRJ-10 — не дублируем. |
| 5 | Сообщение коммита | — не применимо | Коммита нет (аудит не коммитит), проверка не применима. |

### Находки

Новых находок release-check не выявлено (все потенциальные расхождения уже зафиксированы ранее: PRJ-10, PRJ-06, QA-01).

Найдено: 0 (Blocker 0 / Med 0 / Low 0). Регрессии из Блока 13: 0.

**Всего находок в отчёте: 91.**

## 18. Agent RERUN 18/19 (skill-audit)

Источник истины: `C:\analytics\brain-25-evidence\.opencode\skills\skill-audit\SKILL.md` (v1.0, 2026-10-11). Проверок в скилле: 5 (инвентаризация, актуальность чисел, структура, дубли, синхронизация). Выполнено: все 5 на 20 скиллах в `.opencode/skills/` (main checkout, incl. cyberaudit из `.gitignore`).

### Проверка 1 — Количество скиллов
Реально 20 папок на диске. SKILLS_INDEX.md: "19 проектных (в git) + 20 глобальных… в main checkout каталогов там 20". CONVENTIONS.md: "19 проектных в git (20 в main checkout) + 20 глобальных". **Совпадает.** Не находка.

### Проверка 2 — Версии скиллов
19 проектных скиллов имеют `version:` в frontmatter: v1.0 (accessibility-check, core-web-vitals, i18n-rtl-audit, legal-compliance-audit, core-web-vitals, repo-size-audit, seo-check, skill-audit, visual-design-audit), v1.1 (marketing-deep-audit, docs-sync, mobile-deep-audit, site-navigation, project-audit, pwa-audit, qa-deep-audit, product-audit, ui-ux-deep-audit), v1.2 (release-check). Нет v0.9 или устаревших версий. **Все актуальны.** Не находка.

### Проверка 3 — Противоречия (числа и команды)
Найдены 2 проблемы.

**SKILL-02 | skill-audit | Баг | Blocker | Конфликт чисел тестов внутри CONVENTIONS.md сам с собою**
Line 16: "**2002** собрано; 1764 passed + 238 skipped", "`python -m pytest -q` → `1764 passed, 238 skipped`".
Lines 41-42: 1744/237/1981 (@ 724c754) и 1746/237/1983 (@ 1277262, v5.6.5-dev).
Один и тот же файл задаёт разные числа для одного baseline. skill-audit check #2: хардкоды чисел запрещены, единственный источник — CONVENTIONS.md, но сам CONVENTIONS.md хардкодит противоречивые числа. P0 (скилл противоречит реальности). **Не дублирует DOC-05** (DOC-05 — SKILLS_INDEX.md vs docs/version.json, это — CONVENTIONS.md противоречит сам себе).

**SKILL-03 | skill-audit | Доработка | Med | Разнобой команд pytest между скиллами**
SKILLS_INDEX.md:183 — `pytest -q` (все тесты, без фильтров).
CONVENTIONS.md:264 — pre-commit gate `pytest -q -m "not network and not snapshot_data" -k "not real_docs_sitemap_is_current and not live_docs_feed_is_current"`.
CONVENTIONS.md:192 — `pytest -q -m "not network"` помечена устаревшей.
SKILLS_INDEX.md:186 — `RUN_SNAPSHOTS=1 pytest -q -m snapshots` (37 шт.).
CONVENTIONS.md:440 — `pytest -q -m snapshots -k interactions`.
Нет единой актуальной команды. P1.

### Проверка 4 — Пути
skill-audit SKILL.md:61 предписывает отчёт в `reports/audits/skills.md` — путь существует, цель жива. SKILLS_INDEX.md:229 и CONVENTIONS.md ссылаются на тот же путь. Ссылок на `docs/script.js` как на переехавший файл не найдено (одна ссылка в qa-deep-audit:138 на существующий файл). Ссылок на удалённые модалки нет. **Пути актуальны.** Не находка.

### Проверка 5 — Дубли
20 скиллов с уникальными именами. Копипасты правил (верификация, лимит находок) между скиллами не выявлено — они живут в CONVENTIONS.md. **Дубликатов нет.** Не находка.

### Проверка 6 — Структура и frontmatter (доп. проверка skill-audit)
Все 20 скиллов имеют SKILL.md с валидным frontmatter (пары `---`, поля `name:` и `description:`).

**SKILL-01 | skill-audit | Фикс | Low | cyberaudit SKILL.md без поля `version:` в frontmatter**
Frontmatter cyberaudit: name, description, license, compatibility — `version:` отсутствует. Все остальные 19 скиллов имеют `version: v1.0/v1.1/v1.2`. Версия cyberaudit указана только в SKILLS_INDEX.md:66 (3.1.5). Нарушает единообразие структуры скиллов (проверка #1 skill-audit).

### Проверка 7 — Раздутость SKILL.md (skill-audit check #3, P2)
skill-audit SKILL.md:32-33: свыше 300 строк — флаг «раздутость» (P2). CONVENTIONS.md правило #6: максимум ~250 строк.
- cyberaudit: 328 строк (vendored)
- data-audit: 343 строк
- legal-compliance-audit: 357 строк

**SKILL-04 | skill-audit | Доработка | Low | Раздутость SKILL.md (>300 строк)**
Три скилла превышают 300 строк: cyberaudit (328), data-audit (343), legal-compliance-audit (357). Превышают также конвенционный лимит ~250. Требуется рефакторинг или вынос в отдельные документы.

### Синхронизация с глобальными скиллами
Проверка через `~/.config/opencode/skills/` не выполнена (вне рабочей директории main checkout). Документы утверждают 1:1 совпадение, байт-идентичность cyberaudit подтверждена SKILLS_INDEX.md:116-118.

| # | Категория | Критичность | Описание | Где | Примечание |
|---|-----------|-------------|----------|-----|------------|
| SKILL-01 | skill-audit | Фикс | Low | cyberaudit SKILL.md без `version:` в frontmatter | `.opencode/skills/cyberaudit/SKILL.md` | Остальные 19 скиллов имеют version |
| SKILL-02 | skill-audit | Баг | Blocker | Конфликт чисел тестов внутри CONVENTIONS.md (1764/238/2002 vs 1746/237/1983) | `CONVENTIONS.md:16` vs `:41-42` | P0, не дублирует DOC-05 |
| SKILL-03 | skill-audit | Доработка | Med | Разнобой команд pytest между скиллами (нет единой актуальной) | `SKILLS_INDEX.md:183`, `CONVENTIONS.md:264/192/440` | P1 |
| SKILL-04 | skill-audit | Доработка | Low | Раздутость SKILL.md >300 строк | `cyberaudit (328)`, `data-audit (343)`, `legal-compliance-audit (357)` | P2, лимит ~250 |

**Итого skill-audit: 4 находки (Blocker 1 / Med 1 / Low 2). Регрессии из Блока 13: 0.**

**Всего находок в отчёте: 95.**

## 19. Agent RERUN 19/19 (repo-size-audit)

Источник истины: C:\analytics\brain-25-evidence\.opencode\skills\repo-size-audit\SKILL.md (v1.0, 2026-10-18). Проверок в скилле: Workflow — 3 этапа (инвентаризация, проект-анализ, отчёт); выполнено: все 6 точек задачи (размер .git, топ-10 файлов, размеры папок data/journals/tests/snapshots/docs/sup/reports, loadGzJson, мусор _tmp_/*.log/*.xml, git-история). Найдено: 2 (Blocker 0 / Med 1 / Low 1). Регрессии из Блока 13: 0.

Находки, пересекающиеся с уже записанными (PRJ-01 — .json.gz в git, PRJ-02 — дубли отчётов, PRJ-06 — корневые артефакты, CWV-03 — loadGzJson мёртвый код, QA-01 — DuckDB), не дублируются.

| # | Категория | Критичность | Описание | Где | Решение |
| REPO-01 | repo-size-audit | Улучшение | Med | .git раздут до 976,64 МБ (objects 970 МБ): в истории остались крупные бинарные JSON (scimago.json 29,55 МБ, papers_slim.json 19,63 МБ, nlm_catalog.json 13,17 МБ, stats_claims.json 7,61 МБ) — сейчас в .gitignore, но по-прежнему в pack-архивах истории; 5 711 unpacked loose objects (~328 МБ), git gc не запускался. | .git/, объекты | git gc / repack; при необходимости git filter-repo для удаления крупных артефактов из истории |
| REPO-02 | repo-size-audit | Улучшение | Low | reports/ разросся до 75,64 МБ (591 файлов) ≈ 59% от tracked-размера репозитория (127,47 МБ); основная доля — 60 отслеживаемых PNG-скриншотов (до 3,8 МБ, versioned дубли v26/v261/v262 в reports/ui/) плюс tests/snapshots 52,30 МБ (78 PNG). Вместе ~128 МБ tracked бинарных артефактов. | reports/, tests/snapshots | Перенести старые скриншот-эталон в reports/archive/ или git LFS; не расширять отслеживание |

Итого repo-size-audit: 2 находки (Улучшение 2; Blocker 0 / Med 1 / Low 1). Регрессии из Блока 13: 0.

**Всего находок в отчёте: 97.**

## Файл

`reports/AUDIT_MASTER_v565_rerun.md` (дописан раздел 19 repo-size-audit, находки REPO-01, REPO-02 добавлены в конец).

**СТОП. Ничего не фиксить в коде продукта. Не коммитить пока.**


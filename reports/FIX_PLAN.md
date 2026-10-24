# FIX PLAN v5.6.5 — полный план фиксов и улучшений (Rerun 2)

Дата: 23.10.2026. HEAD: 5cce3622. Ветка: v5.6.5-dev.

Источники: `reports/AUDIT_MASTER_v565_rerun2.md` (18 разделов, 103 867 байт) + `reports/BUGS_REGISTRY_v1.md` (старые ID со статусом «Актуально» / «Частично»).

Правило формирования: включено всё, что осталось открытым. Закрытые старые ID не включены. Деления на «блокеры / не блокеры» нет — чиним всё. Критичность A/B/C указана справочно (A = Blocker, B = Med, C = Low), порядок работы от неё не зависит.

Легенда типа: **баг** — поведение отличается от заявленного/ожидаемого (сломано, неверно, недоступно); **улучшение** — отсутствующая возможность, гигиена, косметика.

---

## 1. site-navigation

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| S1-03 | баг | B | Футер не единый: различается на index / sup / compare / 404 | docs/*.html | Закрыто (коммит b0127e77) |
| S1-04 | улучшение | C | Нет хлебных крошек ни на одной странице | docs/*.html | Закрыто (коммит 9742546e) |
| NS1-01 | баг | B | Футер `hactar.html` без ссылки «Каталог БАДов» и блока share-row | docs/hactar.html:463-484 | Закрыто (коммит 5c388252) |
| NS1-02 | баг | C | Крошки есть только на sup-страницах; на index/404/hactar/feedback нет | docs/index.html, 404.html, hactar.html, feedback.html | Закрыто (не требует исправления: index — корень, 404 — страница ошибки, крошки не несут навигационной ценности) |
| NS1-03 | улучшение | C | В редирект-заглушках остаётся полный навбар, недостижимый из-за мгновенного `location.replace` | docs/calculator.html, compare.html, interactions.html, map.html | Закрыто (коммит b0127e77) |

## 2. visual-design-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| V2-01 | улучшение | C | Тег `h6` не используется нигде | docs/*.html | Открыт |
| V2-02 | баг | B | Нет брейкпоинтов 320px и 1440px в media queries | docs/style.css | Открыт |
| V2-03 | улучшение | C | Жёсткие hex-цвета вместо CSS-переменных | docs/style.css | Открыт |
| V2-04 | баг | B | Размер шрифта 12px (ниже минимума 14px) | docs/style.css | Открыт |
| V2-05 | баг | C | У `404.html` нет site-footer | docs/404.html | Открыт |
| V2-06 | улучшение | C | 14 хардкодных hex-цветов в рендере графа связей | docs/hactar.js (renderGraph) | Открыт |
| V2-08 | баг | C | Чипы `font-size: 11.52px` (< 14px) | docs/style.css | Открыт |
| NV2-01 | баг | B | Боковая панель Hactar фиксированные 340px, промежуточного брейкпоинта нет | docs/hactar.html:33, 228 | Открыт |
| NV2-02 | баг | C | Чипы «Купить» `.72rem` + инлайн `border` выходят за границы ячейки | docs/index.html:480-490 | Открыт |
| NV2-03 | баг | C | Нет визуального состояния ошибки у полей доз (`:invalid` / `.is-invalid`) | docs/calculator.html, docs/hactar.js | Открыт |
| NV2-04 | баг | B | На 320px панель скрыта целиком, навигация по табам недоступна | docs/hactar.html:35, 228-230 | Открыт |
| NV2-05 | баг | C | Бейджи грейдов передают смысл только цветом (WCAG 1.4.1) | docs/hactar.html, docs/sup/*.html | Открыт |

## 3. product-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| P2-01 | баг | B | CTA скроллит к `#cardsContainer`, но не фокусирует `#search` | docs/index.html | Открыт |
| P2-02 | баг | C | Чипы Ozon/WB ведут на поиск магазина, не на товар | docs/index.html | Открыт |
| P2-05 | баг | C | Запрос магазина на sup включает форму выпуска, на главной — только название | docs/sup/*.html, docs/script.js | Открыт |
| NP2-01 | баг | B | «Сохранить стек» без обратной связи (нет `:active`, тоста, индикатора) | docs/hactar.html, docs/hactar.js | Открыт |
| NP2-02 | баг | C | Дубль P2-01 на Hactar-хабе: нет фокуса `#search` после скролла | docs/index.html:300 | Открыт |
| NP2-03 | баг | C | Нет deep-link'а на конкретный товар в магазине (ovBuyCell) | docs/hactar.js:1689-1690 | Открыт |
| NP2-04 | баг | B | Нет валидации доз: буквы в поле не помечаются ошибкой, расчёт идёт с мусором | docs/hactar.js, docs/calculator.html | Открыт |
| NP2-05 | улучшение | C | Редиректы старых ссылок без уведомления о переезде | docs/calculator.html, compare.html, interactions.html, map.html, graph.html, atlas.html | Открыт |

## 4. qa-deep

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| Q2-02 | баг | C | Чипы Ozon/WB с пустым атрибутом `class=""` | docs/index.html | Открыт |
| Q2-03 | баг | C | Поиск на `404.html` не редиректит на sup по Enter | docs/404.html | Открыт |
| NQ2-01 | улучшение | B | `saveSelection()` без debounce: 10 кликов = 10 записей в localStorage | docs/hactar.js:803-822 | Открыт |
| NQ2-02 | баг | C | Перезапись стека с тем же именем без уведомления | docs/hactar.js:466-480 | Открыт |
| NQ2-03 | баг | B | Проверка `bad` срабатывает только при `state.touched` — ошибка ввода не видна | docs/hactar.js:1844, 2211-2219 | Открыт |
| NQ2-04 | баг | C | Сохранение с пустым именем возвращает `false` без визуальной обратной связи | docs/hactar.js:466-468 | Открыт |
| NQ2-05 | улучшение | C | Нет уведомления при выборе 5+ добавок | docs/hactar.js (renderOverview) | Открыт |

## 5. accessibility-check

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| A2-01 | баг | B | Кнопка смены темы без `aria-label` (только эмодзи) | docs/index.html | Открыт |
| A2-03 | баг | C | Чипы Ozon/WB: `aria-label` есть, класс отсутствует | docs/index.html | Открыт |
| A2-04 | баг | B | CTA после скролла фокусирует кнопку фильтра, а не `#search` | docs/index.html | Открыт |
| A2-05 | баг | C | `summary` без `role="button"` и `aria-expanded` | docs/index.html | Открыт |
| A2-06 | баг | B | Граф `interactions.html` недоступен с клавиатуры | docs/interactions.html | Открыт |
| A2-07 | баг | C | `404.html`: навигация без `data-i18n-aria-label`, нет связи `#nfSearch`–`#nfResults` | docs/404.html | Открыт |
| A2-08 | баг | B | Чип в тёмной теме: контраст ~3.27:1 < 4.5:1 | docs/style.css | Открыт |
| NA2-01 | баг | B | Инпуты доз `.hactar-ov-dose-input` без accessible name | docs/hactar.js (renderOverview) | Открыт |
| NA2-02 | улучшение | C | Кнопки стека без `aria-label` (текст есть, доступно) | docs/hactar.js | Открыт |
| NA2-06 | улучшение | C | Управление фокусом в мобильной шторке `hactar-sidebar` не реализовано | docs/hactar.html:228-230 | Открыт |

## 6. mobile-deep-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| M2-01 | баг | B | Навбар на 320px не влезает (maxRight 536px > 320px) | docs/*.html, docs/style.css | Открыт |
| M2-02 | баг | B | `trends.html` на 320px: горизонтальный скролл (341 > 320) | docs/trends.html | Открыт |
| M2-03 | баг | B | `404.html` не адаптивна на 320px (maxRight 701px) | docs/404.html | Открыт |
| NM2-01 | баг | B | Таблица «Обзор» `min-width:420px` > 320px | docs/hactar.html:190-191 | Открыт |
| NM2-02 | баг | C | `.hactar-stack-btn` `min-height:36px` < 44px (WCAG 2.5.5) | docs/hactar.html:252 | Открыт |
| NM2-03 | баг | C | Чипы «Купить» с `white-space:nowrap` вылетают за ячейку на 320px | docs/hactar.html:220 | Открыт |

## 7. seo-check

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| SE2-01 | улучшение | C | Чипы магазинов на sup без `rel="nofollow"` | docs/sup/*.html | Открыт |
| SE2-03 | улучшение | C | На `index.html` нет SearchAction и ItemList в JSON-LD | docs/index.html | Открыт |
| SE2-04 | улучшение | C | «+ Сравнить» — не ссылка, навигация только через JS (130 страниц) | docs/sup/*.html | Открыт |
| SE2-05 | улучшение | C | 10 внешних ссылок без `rel="nofollow"` | docs/*.html | Открыт |
| NSE2-01 | баг | B | `rel="canonical"` на `hactar.html` относительный, нужен абсолютный URL | docs/hactar.html:13 | Открыт |
| NSE2-02 | баг | C | `<title>` 75 символов (> 60), обрезается в выдаче | docs/hactar.html:20 | Открыт |

## 8. data-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| D2-01 | баг | B | В `docs/api/v1/` нет `interactions.json` и `graph.json` | docs/api/v1/ | Открыт |
| D2-02 | баг | B | 5 битых PMID (не 8-значные) в `key_sources` | docs/data.json | Открыт |
| D2-03 | баг | C | 2 пустых поля `doi` (Витамин K1, PABA) | docs/data.json | Открыт |
| D2-04 | баг | B | `forms` — строка, а не массив (все 130 карточек) | docs/data.json | Открыт |
| D2-05 | баг | C | Нет полей `papers` и `safety` у всех 130 карточек | docs/data.json | Открыт |
| D2-07 | баг | C | «4 карточки Блока 6» не верифицируются (8 карточек с `updated=2026-09-25`) | docs/data.json | Открыт |
| ND2-01 | баг | B | Контракт `price` объявлен, но `price=null` везде; цены хардкожены в `PRICE_MAP` | docs/data_index.json, docs/hactar.js:2076-2104 | Открыт |
| ND2-02 | баг | B | `synergists` / `antagonists` в `data_index.json` без источника в `data.json` | docs/data_index.json, docs/data.json | Открыт |

## 9. core-web-vitals

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| C2-01 | баг | B | CLS Poor на `index.html` 0.262–0.267 > 0.25 (FOUT шрифтов) | docs/index.html, docs/style.css | Открыт |
| C2-03 | баг | B | vis-network 673 КБ грузится не лениво на каждой загрузке | docs/interactions.html | Открыт |
| C2-04 | улучшение | C | `script.js` (74 КБ) и `style.css` (178 КБ) не минифицированы | docs/script.js, docs/style.css | Открыт |
| C2-05 | улучшение | C | 5 файлов шрифтов (~560 КБ) без `rel="preload"` | docs/*.html, docs/fonts/ | Открыт |

## 10. i18n-rtl-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| I2-01 | улучшение | B | Нет механизма смены локали (`LOCALE` только из `html lang`) | docs/i18n.js | Открыт |
| I2-02 | улучшение | B | Словарь рассеян по 4 файлам (`i18n.js`, `share.js`, `science2.js`, `tracker.js`) | docs/*.js | Открыт |
| I2-03 | улучшение | C | В словаре только ключ `ru`, нет `en` | docs/i18n.js | Открыт |
| NI2-01 | баг | B | `hactar.js` не использует `t()` и не подключает `i18n.js` — все строки хардкод | docs/hactar.js, docs/hactar.html:461 | Открыт |
| NI2-02 | баг | C | На `hactar.html` всего 1 атрибут `data-i18n-*` | docs/hactar.html:286 | Открыт |

## 11. legal-compliance-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| L2-01 | баг | B | Нет страницы Terms of Use | docs/ | Открыт |
| L2-02 | баг | B | Нет лицензии на данные в HTML-страницах | docs/*.html | Открыт |
| L2-03 | баг | C | В калькуляторе нет локального предупреждения «не мед. рекомендация» | docs/calculator.html | Открыт |
| L2-04 | баг | B | Нет пометки о партнёрских (аффилиатных) ссылках на магазины | docs/index.html, docs/sup/*.html | Открыт |
| NL2-01 | баг | B | Privacy Policy не упоминает хранение выборок БАДов и стеков в localStorage | docs/hactar.js:61-62, 456; docs/privacy.html | Открыт |
| NL2-02 | баг | B | Чипы «Купить» в Hactar без раскрытия аффилиатности (ФЗ «О рекламе») | docs/hactar.js (ovBuyCell), docs/hactar.html | Открыт |

## 12. ui-ux-deep-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| U2-02 | баг | B | Ввод букв в дозу → NaN считается «в норме» (`cntOk++`) | docs/hactar.js (doseInfo) | Открыт |
| U2-03 | улучшение | C | Чипы магазинов без визуального отклика (`:active` / тост) | docs/style.css, docs/script.js | Открыт |
| U2-05 | улучшение | C | «Удиви меня» — слабая микроинтеракция | docs/script.js | Открыт |
| U2-06 | баг | C | Копирование ссылки без `.catch()` — при ошибке нет отклика | docs/share.js | Открыт |
| NU2-01 | улучшение | C | Пустой результат поиска в Hactar без CTA «Сбросить» | docs/hactar.html:325 | Открыт |

## 13. marketing-deep-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| MK2-02 | улучшение | C | > 15 кнопок на главной, нет иерархии primary/secondary | docs/index.html | Открыт |
| MK2-03 | баг | B | `twitter:title/description/image` отсутствуют на 134 из 148 страниц | docs/*.html | Открыт |
| MK2-04 | улучшение | C | Блок `heroStats` без контекста источника | docs/index.html | Открыт |
| MK2-05 | улучшение | C | «Почему этому можно верить» — канцеляризмы | docs/index.html | Открыт |
| MK2-06 | улучшение | C | УТП не сформулировано, H1 абстрактен | docs/index.html | Открыт |
| NMK2-01 | улучшение | C | H1 «Project Hactar» не объясняет, что это за инструмент | docs/hactar.html:329 | Открыт |
| NMK2-02 | улучшение | C | CTA «Сохранить стек» не читается как primary (36px, без заливки) | docs/hactar.html:334 | Открыт |

## 14. project-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| PR2-01 | улучшение | C | Нет `.editorconfig` | корень | Открыт |
| PR2-02 | улучшение | C | Нет `SECURITY.md` | корень | Открыт |
| PR2-03 | улучшение | C | Нет `CODE_OF_CONDUCT.md` | корень | Открыт |
| PR2-05 | улучшение | C | 10 скриптов в `scripts/` без модульного docstring | scripts/*.py | Открыт |
| NPR2-01 | баг | B | README: 1979 и 1982 против фактических 1989 в `version.json` | README.md:267,315,338,364 | Открыт |

## 15. pwa-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| PW2-01 | баг | B | `404.html` не подключает manifest и `pwa.js` (SW не регистрируется) | docs/404.html | Открыт |
| PW2-02 | баг | B | `404.html` не входит в `STATIC_ASSETS` | docs/sw.js:363-406 | Открыт |
| PW2-03 | баг | C | Маскабельные иконки не кэшируются SW | docs/sw.js:363-406 | Открыт |
| PW2-04 | баг | B | Кэш SW не инвалидируется при изменении `version.json` | docs/sw.js:337 | Открыт |
| PW2-05 | баг | C | Нет `theme-color` на `atlas.html`, `graph.html`, google-верификации | docs/atlas.html, graph.html, google4a9d23e35c6c3e23.html | Открыт |
| NPW2-01 | баг | B | `hactar.html` не подключает `pwa.js` — SW не регистрируется при первом визите | docs/hactar.html | Открыт |
| NPW2-02 | баг | C | iOS-меты разрежены: `apple-touch-icon` нет на 11 страницах, `capable` — на 5 из 149 | docs/*.html | Открыт |
| NPW2-03 | улучшение | C | Нет UI установки (`beforeinstallprompt` не обрабатывается) | docs/pwa.js, docs/script.js | Открыт |
| NPW2-04 | баг | C | Манифест только тёмный (`#1c1c1e`) против светлых страниц `#f5f5f7` | docs/manifest.webmanifest:12-13 | Открыт |

## 16. docs-sync

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| DS2-01 | баг | A | Число тестов расходится: version.json 1982, в README/CONVENTIONS/AGENTS 1979 | docs/version.json, README.md, CONVENTIONS.md, AGENTS.md | Открыт |
| DS2-03 | баг | C | Хеши хотфиксов не привязаны к секции `[v5.6.5]` | CHANGELOG.md | Открыт |
| NDS2-01 | баг | B | Hactar (12 коммитов 22.10) не описан: 0 упоминаний в CHANGELOG/README/ARCHITECTURE | CHANGELOG.md, README.md:227-231, ARCHITECTURE.md | Открыт |
| NDS2-02 | баг | B | Ложные факты: CONVENTIONS 1979 «совпадает с version.json», ARCHITECTURE «112 тестов» | .opencode/skills/CONVENTIONS.md:43-44, ARCHITECTURE.md:161 | Открыт |
| NDS2-03 | баг | C | CONVENTIONS:15 указывает `CACHE_VERSION = 'v113'`, фактически `v117` | .opencode/skills/CONVENTIONS.md:15 | Открыт |
| NDS2-04 | баг | C | README завышает: sitemap 143 vs 140, 12 vs 9 корневых, 17 vs 18 файлов | README.md:339,354 | Открыт |
| NDS2-05 | баг | C | README продаёт `map.html` как рабочую страницу, а это редирект | README.md:13,134,227,339 | Открыт |

## 17. release-check

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| RC2-01 | улучшение | C | Тег `v5.6.5` не создан | git tag | Открыт |
| RC2-02 | баг | B | Тег `v5.6.4` не предок HEAD: dev не содержит коммит `8476fb92` | git history | Открыт |
| RC2-03 | баг | B | Полный прогон выходит за 10 минут (`pytest.ini`), 795 с | pytest.ini | Открыт |
| NRC2-01 | баг | A | Флейк: `test_a11y_wcag22[412-852-feedback-light]` падает по `networkidle` из-за Яндекс.Форм | tests/test_a11y_axe.py:237 + docs/feedback.html:163-164 | Открыт |
| NRC2-02 | баг | B | CI не запускается: триггер `branches: [main, v5.6-dev]`, ветка `v5.6.5-dev` | .github/workflows/tests.yml:15,17 | Открыт |
| NRC2-03 | баг | B | В CI нет `playwright install`; `test_graph_interaction.py:181` даст ERROR, не skip | .github/workflows/tests.yml:57-58 + tests/test_graph_interaction.py:178-185 | Открыт |
| NRC2-04 | баг | B | Гейт графа выключен целиком: 24 skip (12 тестов × 2 движка) | tests/test_graph_interaction.py:178-202 | Открыт |
| NRC2-05 | баг | C | Хук закоммичен с режимом `100644` — на POSIX не запустится | .githooks/pre-commit | Открыт |
| NRC2-06 | баг | C | Шапка хука повреждена (строки 3–4 — байты 0x3f вместо UTF-8) | .githooks/pre-commit:3-4 | Открыт |

## 18. repo-size-audit

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| RS2-01 | улучшение | B | `.git` 1181,84 МБ; 69% истории — 1885 версий PNG-эталонов | .git/objects/pack/pack-ce4527….pack | Открыт |
| RS2-02 | улучшение | B | `tests/snapshots` 76 файлов / 53,07 МБ в индексе | tests/snapshots/ | Открыт |
| RS2-03 | улучшение | C | 3 отслеживаемых `*.json.gz` при правиле в `.gitignore:325` | git index | Открыт |
| RS2-06 | улучшение | C | `tests/snapshots/*/_actual/` вне `.gitignore` (сейчас игнорируется только `_actual`) | .gitignore:234 | Открыт |
| NRS2-01 | улучшение | B | Git LFS не настроен: 0 строк `filter=lfs`, PNG лежат обычными blob'ами | .gitattributes:5-8 | Открыт |
| NRS2-02 | улучшение | B | gc не запускался: 1023 loose-объекта 205,70 MiB + 498 недостижимых blob'ов 30,46 МБ | .git/objects | Открыт |
| NRS2-03 | баг | C | Два `.gz` — сироты, код читает только несжатые имена | data/journals/nlm_catalog.json.gz, data/papers/stats_claims.json.gz | Открыт |
| NRS2-04 | улучшение | C | 6 временных файлов прогонов в корне (0,46 МБ) | корень | Открыт |
| NRS2-05 | улучшение | C | `tests/snapshots/*/_actual/` 140 файлов / 98,72 МБ не чистятся | tests/snapshots/chromium/_actual, webkit/_actual | Открыт |

---

## Сводка

Всего пунктов: **128**.

| Разрез | Значение |
|---|---|
| Старые (из `BUGS_REGISTRY_v1.md`, статус «Актуально»/«Частично») | 72 |
| Новые (из разделов Rerun 2: NS1…NRS2) | 56 |
| Баги | 86 |
| Улучшения | 42 |
| Критичность A (Blocker) | 2 — DS2-01, NRC2-01 |
| Критичность B (Med) | 54 |
| Критичность C (Low) | 72 |

По скиллам (старых + новых):

| Скилл | Старых | Новых | Всего |
|---|---|---|---|
| 1. site-navigation | 2 | 3 | 5 |
| 2. visual-design-audit | 7 | 5 | 12 |
| 3. product-audit | 3 | 5 | 8 |
| 4. qa-deep | 2 | 5 | 7 |
| 5. accessibility-check | 7 | 3 | 10 |
| 6. mobile-deep-audit | 3 | 3 | 6 |
| 7. seo-check | 4 | 2 | 6 |
| 8. data-audit | 6 | 2 | 8 |
| 9. core-web-vitals | 4 | 0 | 4 |
| 10. i18n-rtl-audit | 3 | 2 | 5 |
| 11. legal-compliance-audit | 4 | 2 | 6 |
| 12. ui-ux-deep-audit | 4 | 1 | 5 |
| 13. marketing-deep-audit | 5 | 2 | 7 |
| 14. project-audit | 4 | 1 | 5 |
| 15. pwa-audit | 5 | 4 | 9 |
| 16. docs-sync | 2 | 5 | 7 |
| 17. release-check | 3 | 6 | 9 |
| 18. repo-size-audit | 4 | 5 | 9 |
| **Итого** | **72** | **56** | **128** |

## Порядок работы

Идём по скиллам в порядке аудита. Внутри скилла — по ID. Один ID = одна задача = один фикс.

Порядок не зависит от критичности: список сверху вниз, любой ID можно взять вне очереди по желанию.

## Не включено в план

- Старые ID со статусом «Закрыто»: S1-01, S1-02, V2-07, P2-03, P2-04, Q2-01, A2-02, M2-04, SE2-02, D2-06, C2-02, U2-01, U2-04, MK2-01, PR2-04, DS2-02 — проверены и закрыты на HEAD 5cce3622.
- MAN-01…MAN-05 (ручные наблюдения) — статус в реестре не заполнен, скилл `Manual` не входит в 18 проверок этого прогона. Требуют отдельного решения владельца.
- SK2-02 (skill-audit) — статус в реестре не заполнен, скилл не входил в этот прогон.

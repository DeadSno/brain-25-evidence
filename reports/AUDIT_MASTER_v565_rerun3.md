# AUDIT MASTER v5.6.5 (RERUN 3) — Аудит после перевода на EN. Дата: 26.10.2026. HEAD: a5e02f52.

Ветка `v5.6.5-dev`, рабочая директория `C:\analytics\brain-25-evidence`
(main checkout). Rerun 3 начат с нуля: предыдущий файл этого прогона
(WADA-01/02) перенесён в `reports/archive/AUDIT_MASTER_v565_rerun3_WADA.md`.

---

## Аудит 1/19: site-navigation

**Скилл:** `.opencode/skills/site-navigation/SKILL.md` (v1.1).
**Дата:** 26.10.2026. **HEAD:** a5e02f52. **Ветка:** v5.6.5-dev.

### Объём

| Что | Число |
|---|---|
| HTML-файлов в `docs/` (рекурсивно) | **150** |
| Из них проверено как страниц | **149** (`google4a9d23e35c6c3e23.html` — служебная верификация GSC, ссылок не содержит) |
| Корневых страниц `docs/*.html` | 19 (в т.ч. `hactar.html`, `terms-of-use.html`, 6 заглушек-редиректов) |
| Карточек `docs/sup/*.html` | 131 (130 карточек + `sup/index.html`) |
| Локальных ссылок (статически, без `<script>`) | 2833 вхождений / 150 уникальных URL |
| Внешних ссылок | 1607 |
| `<loc>` в `docs/sitemap.xml` | 141 |

### Как проверялось

1. Статический обход всех 150 файлов (`_tmp_nav_audit2.py`): разрешение
   относительных путей, существование файла, совпадение регистра букв с
   реальным именем (важно для Linux-хостинга), проверка `#якорей` по
   фактическим `id`/`name` цели, ссылки внутри `<script>` исключены
   (шаблонные строки давали ложное срабатывание).
2. Сверка header/footer поблочно: состав, порядок, подписи, дубли,
   `data-i18n-text`-ключи (`_tmp_nav_order.py`).
3. HTTP-прогон всех 150 уникальных внутренних URL против живого сервера
   `http://localhost:8000` (`_tmp_nav_http.py`, сервер отвечал
   `version.json → app 5.6.5`).
4. Живая проверка 6 редиректов и deep-link'ов Hactar в Playwright/Chromium
   (переход → фактический URL, активная вкладка `aria-selected`, видимая
   панель).
5. EN-режим: `localStorage.setItem('lang','en')` + перезагрузка на
   `index`, `sup/magniy`, `faq`, `hactar` — подписи навигации и футера
   после перевода, `href` не изменились.
6. Sitemap: разбор `<loc>`, сверка с фактическими файлами плюс
   `python scripts/build_sitemap.py --check`.

### Находки

| ID | Приоритет | Находка | Статус |
|---|---|---|---|
| NAV-01 | P2 | Футер 7 корневых страниц не содержит ссылку «💊 Каталог БАДов» | открыто |
| NAV-02 | P3 | `hactar.html` использует свои i18n-ключи навигации; EN-подписи разошлись с остальными 139 страницами | открыто |
| NAV-03 | P3 | Скилл (и ещё 5 скиллов) указывают deep-link `?tab=links`; фактический параметр — `?tab=graph` | **Закрыто** (коммит `2e78b9ab`) |
| NAV-04 | P4 | У 4 из 6 заглушек нет JS-фолбэка `window.location.replace`, у 2 есть | **Закрыто** (не требует исправления кода) |

---

#### NAV-01 — Футер 7 корневых страниц без ссылки на каталог (P2)

**Где.** `faq.html`, `glossary.html`, `methodology.html`, `privacy.html`,
`support.html`, `terms-of-use.html`, `trends.html` — блок
`<footer class="site-footer"> → <p class="links">`.

**Что не так.** Футер существует в двух вариантах:

| Вариант | Страниц | Ссылок в `p.links` |
|---|---|---|
| с «💊 Каталог БАДов» | 135 (131 карточка + `index`, `feedback`, `404`, `hactar`) | 7 (+ строка copyright с `terms-of-use.html#data-license`) |
| без каталога | **7** (список выше) | 6 (+ та же строка copyright) |

Порядок остальных ссылок идентичен, дублей нет, подписи совпадают
(сверено по `data-i18n-text`: у 7 страниц отсутствует ровно один ключ —
`footer.catalog`).

**Воспроизведено.** `docs/faq.html:293-300` — в `p.links` шесть `<a>`,
`footer.catalog` нет. В живом EN-режиме на `faq.html` футер:
`Methodology · FAQ · Glossary · Privacy · Terms of Use · RSS` — без
`Supplement Catalog`; на `index.html` и `sup/magniy.html` он есть.
Ключ `footer.catalog` в словарях присутствует в обоих языках
(`i18n.js:519` RU, `i18n.js:1713` EN — «💊 Supplement Catalog»),
то есть проблема только в отсутствующей разметке.

**Эффект.** С этих 7 страниц до каталога можно добраться только через
логотип в шапке → главная → каталог (2 перехода). Правило скилла
«у всех страниц одинаковый набор ссылок» нарушено; после перевода на EN
расхождение стало заметнее (в EN-футере пропадает единственный вход
в каталог с контентных страниц).

**Не чинил** — аудит только читает (`AGENTS.md`).

---

#### NAV-02 — Дубли i18n-ключей навигации в `hactar.html` (P3)

**Где.** `docs/hactar.html:63-71` — шапка использует `hactar.nav.feedback`,
`hactar.nav.support`, `hactar.nav.random`; остальные 139 страниц —
`index.feedback`, `index.support`, `index.random`.

**Что не так.** Ключи дублируют друг друга, и EN-переводы разъехались:

| Ключ | EN (`i18n.js`) |
|---|---|
| `index.support` (:2204) | «💚 **Support us**» |
| `hactar.nav.support` (:2347) | «💚 **Support**» |
| `index.feedback` (:2203) | «💬 Feedback» |
| `hactar.nav.feedback` (:2346) | «💬 Feedback» (совпадает) |

RU-значения идентичны, расходятся только EN.

**Воспроизведено.** Живой EN-режим: на `hactar.html` шапка
`💬 Feedback · 💚 Support`, на `index.html` / `sup/magniy.html` /
`faq.html` — `💬 Feedback · 💚 Support us`. Один и тот же пункт меню
подписан по-разному на соседних страницах.

**Эффект.** Расхождение подписей в навигации после перевода; плюс
тройное дублирование ключей — следующий перевод/правка легко разойдётся
снова.

---

#### NAV-03 — Скиллы описывают несуществующий deep-link `?tab=links` (P3) — **ЗАКРЫТО**

**Где.** `.opencode/skills/site-navigation/SKILL.md:49` и `:65`;
то же в `core-web-vitals` (:107), `mobile-deep-audit` (:111),
`product-audit` (:121), `qa-deep-audit` (:127, :131), `seo-check` (:98);
плюс комментарий `tests/test_graph_interaction.py:21`.

**Что не так.** Скилл утверждает, что вкладка «Связи» открывается как
`hactar.html?tab=links`. Фактически (`docs/hactar.js:172-189`):
`TAB_PARAM = { overview: 'overview', links: 'graph' }`, а `modeFromUrl()`
понимает только `overview` и `graph`; `links` попадает в `DEFAULT_MODE`.

**Воспроизведено (Playwright):**

| URL | Активная вкладка | Панель |
|---|---|---|
| `hactar.html?tab=links` | **Обзор** | `hactarPanelOverview` |
| `hactar.html?tab=graph` | Связи | `hactarPanelLinks` |
| `hactar.html` | Обзор | `hactarPanelOverview` |

Проверено также, что `?tab=links` **никогда** не было URL сайта: в
`git log -S"tab=links" -- docs` совпадений нет, `git grep` по `docs/`
пуст. То есть это ошибка только в документации, публичные ссылки не
сломаны.

**Эффект.** Аудиты, идущие по скиллу, будут проверять несуществующий
адрес и «находить» несуществующую вкладку; HEAD a5e02f52
(«audit and update outdated SKILL.md before Rerun 3») эту строку
пропустил.

**Закрыто (коммит `2e78b9ab`).** Во всех 6 скиллах `?tab=links` заменён
на `?tab=graph` — 8 вхождений:

| Скилл | Строки |
|---|---|
| `site-navigation` | 49, 65 + новый блок «Deep-link Hactar — только два значения» |
| `core-web-vitals` | 107 |
| `mobile-deep-audit` | 111 |
| `product-audit` | 121 |
| `qa-deep-audit` | 127, 131 |
| `seo-check` | 98 |

Плюс комментарий `tests/test_graph_interaction.py:21` (сам тест на
`:263` всегда проверял правильное `tab=graph` — расходился только
docstring). Дополнительно в `site-navigation` и `qa-deep-audit`
зафиксировано, что неизвестный параметр (включая `?tab=links`) открывает
«Обзор»: это защищает от повторного появления ошибки при следующем
редактировании скиллов.

---

#### NAV-04 — 4 из 6 заглушек без JS-фолбэка (P4, наблюдение) — **ЗАКРЫТО**

**Где.** `docs/calculator.html`, `compare.html`, `interactions.html`,
`map.html` — только `<meta http-equiv="refresh">`; у `graph.html` и
`atlas.html` дополнительно `window.location.replace('hactar.html?tab=graph')`.

**Состояние всех шести** (проверено статически и живьём):

| Файл | refresh | JS-replace | robots | canonical | sessionStorage | Фактический переход |
|---|---|---|---|---|---|---|
| calculator.html | `0;url=…?tab=overview` | — | `noindex, follow` | `…/hactar.html?tab=overview` | есть | `?tab=overview`, «Обзор» |
| compare.html | `0;url=…?tab=overview` | — | `noindex, follow` | то же | есть | `?tab=overview`, «Обзор» |
| graph.html | `0; url=…?tab=graph` | есть | `noindex, follow` | `…?tab=graph` | есть | `?tab=graph`, «Связи» |
| atlas.html | `0; url=…?tab=graph` | есть | `noindex, follow` | `…?tab=graph` | есть | `?tab=graph`, «Связи» |
| interactions.html | `0;url=…?tab=graph` | — | `noindex, follow` | `…?tab=graph` | есть | `?tab=graph`, «Связи» |
| map.html | `0;url=…?tab=graph` | — | `noindex, follow` | `…?tab=graph` | есть | `?tab=graph`, «Связи» |

**Почему не P2.** Все шесть работают: meta refresh срабатывает без JS,
а у каждой заглушки в `<body>` есть видимая CTA-ссылка на нужный
`?tab=…` — то есть даже при отключённом refresh пользователь не в тупике.
Циклических редиректов нет: переход всегда один хоп, `hactar.html`
`http-equiv="refresh"` не содержит (проверено: тег есть ровно в этих
6 файлах из 150).

**Расхождение с документацией.** SKILL.md:61-68 утверждает, что у всех
6 заглушек есть и meta refresh, и `window.location.replace()` — у 4 нет.
Форматирование тоже разное (`0;url=` против `0; url=`).

**Замечание рядом (не находка).** canonical заглушек указывает на URL
с query (`hactar.html?tab=graph`), а собственная canonical `hactar.html`
— без query. Для `noindex`-страниц это безвредно, но два разных
canonical-адреса на один контент — потенциальный источник путаницы.

**Закрыто (не требует исправления: все 6 редиректов работают через
meta refresh, JS-фолбэк избыточен).** Проверено живьём (Playwright) и
статически: у всех шести заглушек `<meta http-equiv="refresh">` стоит с
`content="0;url=…"`, то есть переход происходит до отрисовки и без
участия JS; у каждой в `<body>` есть видимая CTA-ссылка на целевой
`?tab=…` — при отключённом refresh пользователь не в тупике. Дублировать
переход через `window.location.replace()` смысла нет: у `graph.html` и
`atlas.html` он есть как наследие, но ничего не добавляет. Расхождение
с SKILL.md (обещание JS-фолбэка у всех шести) устранено в
`site-navigation/SKILL.md:61-68` коммитом `2e78b9ab`: формулировка
«`<meta http-equiv="refresh">` + `window.location.replace()`» заменена на
описание фактического поведения. Код заглушек не менялся.

---

### Где чисто (проверено, находок нет)

| Проверка | Результат |
|---|---|
| Битые локальные ссылки (файл не существует) | **0** из 2833 |
| Регистр в ссылке ≠ регистр файла (важно для Linux) | **0** |
| Абсолютные пути от корня (`/…`) — ломаются при base-path | **0** |
| Битые `#якоря` (сверка с фактическими `id`/`name`) | **0** |
| `href="#"`-заглушки | **0** |
| `http://` внешние ссылки | **0** |
| `target="_blank"` без `rel=noopener/noreferrer` | **0** (918 `nofollow noopener`, 376 `+noreferrer`, 20 `noopener nofollow`) |
| HTTP-статус всех 150 уникальных внутренних URL (localhost:8000) | **200 у всех** |
| Дубли ссылок в header | 0 |
| Дубли ссылок в footer | 0 |
| Дубли `<loc>` в sitemap | 0 |
| Ссылки на страницы-редиректы (заглушки в навигации) | **0** — ни одна из 150 страниц не ссылается на `calculator/compare/graph/atlas/interactions/map.html` |
| Циклические редиректы | нет (1 хоп) |
| Служебные страницы с нулём входящих | 8 — ровно те, что задокументированы: 6 заглушек, `offline.html`, `google4a9d…html` (и `404.html` не достижима по ссылкам, как и положено) |
| Достижимость из `index.html` | недостижимы только 9 служебных; **все 130 карточек и 10 контентных страниц достижимы** |
| EN-режим: подписи навигации/футера переведены, `href` не изменились | да (index, sup/magniy, faq, hactar) |
| Legacy `?tab=compare&ids=magniy,tsink` | → `?tab=overview&ids=magniy%2Ctsink`, ids сохранены |

### Header nav (шапка)

| Вариант | Страниц | Состав |
|---|---|---|
| `../index.html, ../feedback.html, ../support.html` | 131 | карточки `sup/*` — порядок и подписи идентичны |
| `index.html, feedback.html, support.html` | 9 | `404`, `faq`, `glossary`, `hactar`, `index`, `methodology`, `privacy`, `terms-of-use`, `trends` |
| `index.html, support.html` | 1 — `feedback.html` | своя ссылка заменена на `<span class="btn c-feedback">` (текущая страница) |
| `index.html, feedback.html` | 1 — `support.html` | то же для «Поддержать» |

Итого `<header class="top">` есть у **142** страниц: 131 карточка + 11
корневых. Без шапки 8 — ровно исключения из скилла (6 заглушек,
`offline.html`, `google4a9d…html`).

Итог: набор и порядок ссылок одинаковы на всех 142 страницах, кроме
двух законных исключений (self-link → `<span>`). Подписи в шапке
различаются только из-за NAV-02. Замечание: `<span class="btn">` на
`feedback.html`/`support.html` не помечен `aria-current="page"` —
скринридер не узнает, что это текущая страница (для a11y-аудита).

### Footer (футер)

| Вариант | Страниц | Состав |
|---|---|---|
| 7 ссылок + copyright | 131 карточка | методология, FAQ, глоссарий, приватность, условия, **каталог**, RSS |
| 7 ссылок + copyright | 4 корневые (`index`, `feedback`, `404`, `hactar`) | то же |
| 6 ссылок + copyright | **7** (`faq`, `glossary`, `methodology`, `privacy`, `support`, `terms-of-use`, `trends`) | без каталога → NAV-01 |

Порядок ссылок в пределах варианта идентичен, дублей нет, «Условия
использования» присутствует на всех 142 страницах с футером (битой
ссылки на `terms-of-use.html` после перевода не появилось), якорь
`terms-of-use.html#data-license` существует.

### Страницы: наличие nav и число ссылок

| Страница | Header nav | Footer | Локальных ссылок | Статус |
|---|---|---|---|---|
| index.html | да (3) | да (8) | 30 | ок |
| hactar.html | да (3) | да (8) | 13 | ок, NAV-02 |
| trends.html | да (3) | да (7) | 13 | NAV-01 |
| methodology.html | да (3) | да (7) | 12 | NAV-01 |
| faq.html | да (3) | да (7) | 12 | NAV-01 |
| glossary.html | да (3) | да (7) | 12 | NAV-01 |
| feedback.html | да (2, self=span) | да (8) | 14 | ок |
| support.html | да (2, self=span) | да (7) | 12 | NAV-01 |
| privacy.html | да (3) | да (7) | 15 | NAV-01 |
| terms-of-use.html | да (3) | да (7) | 15 | NAV-01 |
| 404.html | да (3) | да (8) | 14 | ок (служебная) |
| calculator/compare/graph/atlas/interactions/map.html | нет (заглушки) | нет | 1 (CTA) | ок по замыслу, NAV-04 |
| offline.html | нет (служебная) | нет | 0 | ок по замыслу |
| google4a9d23e35c6c3e23.html | нет (GSC) | нет | 0 | ок по замыслу |
| `sup/*.html` — 131 | да (3) | да (8) | 17–146 | ок; общий nav+footer есть у 131/131 |

Отсутствие nav у 8 страниц совпадает со списком исключений в скилле
(6 заглушек, `offline.html`, `google*.html`) — это не находка.

### Sitemap

| Проверка | Результат |
|---|---|
| `<loc>` в файле | 141 |
| Все `<loc>` указывают на существующий файл | **141/141** |
| Дубли | 0 |
| `terms-of-use.html` присутствует | **да** |
| `hactar.html` присутствует | **да** |
| Состав | 10 корневых (index, hactar, trends, methodology, faq, glossary, feedback, support, privacy, terms-of-use) + 131 `sup/*` + `sup/index.html` |
| Вне sitemap | 9 страниц: `404.html`, `offline.html`, `google4a9d…html`, 6 заглушек — ровно те, что задокументированы в `scripts/build_sitemap.py:14-20, 63-65, 69-90` |
| `python scripts/build_sitemap.py --check` | **OK: sitemap соответствует содержимому (141 URL)** |

Расхождение с формулировкой задания («150 HTML в sitemap»): 150 —
общее число HTML-файлов в `docs/`; 9 из них по замыслу не индексируются
(404, офлайн-заглушка, файл верификации GSC, 6 редиректов). Фактические
**141 = 150 − 9** совпадают с генератором, `--check` проходит.

### Вывод по аудиту 1/19

Битых ссылок, битых якорей, циклических редиректов и расхождений
sitemap не найдено. Навигация после перевода на EN цела: `href` не
зависят от языка, все 150 внутренних URL отвечают 200, все 6 редиректов
ведут на правильную вкладку Hactar (проверено живьём).

Чинить (когда будет решение владельца):

1. **NAV-01** — добавить `<a href="sup/index.html" data-i18n-text="footer.catalog">`
   в футер 7 страниц до `feed.xml` (порядок как на остальных 135).
2. **NAV-02** — заменить в `hactar.html` три ключа `hactar.nav.*` на
   `index.feedback` / `index.support` / `index.random` (или наоборот,
   свести дубли в `i18n.js` к одному набору).
3. ~~**NAV-03** — исправить `?tab=links` → `?tab=graph` в 6 скиллах и в
   комментарии `tests/test_graph_interaction.py:21`.~~ **Сделано** —
   коммит `2e78b9ab` (8 вхождений в 6 скиллах + комментарий теста).
4. ~~**NAV-04** — либо добавить `window.location.replace()` в 4 заглушки,
   либо поправить SKILL.md, чтобы он не обещал JS-фолбэк у всех шести.~~
   **Сделано** — выбран второй вариант: `site-navigation/SKILL.md`
   описывает фактическое поведение (meta refresh у всех шести, JS-фолбэк
   только у `graph.html`/`atlas.html`), код заглушек не менялся.

Остаются открытыми NAV-01 и NAV-02.

Код не изменялся: аудит только читает файлы, коммитов нет.

---

### Статус закрытия (AUDIT-1-FIX-2, после Rerun 3)

| ID | Статус | Чем закрыто |
|---|---|---|
| NAV-01 | открыто | — |
| NAV-02 | открыто | — |
| NAV-03 | **закрыто** | коммит `2e78b9ab`: `?tab=links` → `?tab=graph` в 6 скиллах (8 вхождений) + docstring `tests/test_graph_interaction.py:21` |
| NAV-04 | **закрыто** | код не менялся (meta refresh у всех 6, JS-фолбэк избыточен); формулировка в `site-navigation/SKILL.md` приведена к факту |

Итого по аудиту `site-navigation` (Rerun 3): **2 из 4 закрыто**,
NAV-01 и NAV-02 ждут решения владельца (правки разметки футера 7
страниц и ключей `hactar.nav.*`).

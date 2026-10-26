# AUDIT MASTER v5.6.5 (FINAL). Дата: 26.10.2026. HEAD старта: db5e6d90.

## Как читать

19 скиллов, один скилл = одна задача.

В начале каждого скилла — блок «Проверка предыдущего» (для 1/19 — «первый скилл»).

Каждая находка имеет ID и статус: открыто → закрыто (коммит <хеш>).

Все проверки — в обеих локалях (RU + EN), оба языка — столпы проекта.

Фиксы применяются ПОСЛЕ завершения всех 19 скиллов.

## Оглавление

1. [Аудит 1/19: site-navigation](#аудит-119-site-navigation)
2. Аудит 2/19: accessibility-check
3. Аудит 3/19: i18n-rtl-audit
4. Аудит 4/19: core-web-vitals
5. Аудит 5/19: seo-check
6. Аудит 6/19: pwa-audit
7. Аудит 7/19: mobile-deep-audit
8. Аудит 8/19: ui-ux-deep-audit
9. Аудит 9/19: visual-design-audit
10. Аудит 10/19: marketing-deep-audit
11. Аудит 11/19: product-audit
12. Аудит 12/19: qa-deep-audit
13. Аудит 13/19: data-audit
14. Аудит 14/19: project-audit
15. Аудит 15/19: docs-sync
16. Аудит 16/19: release-check
17. Аудит 17/19: repo-size-audit
18. Аудит 18/19: legal-compliance-audit
19. Аудит 19/19: skill-audit

---

## Аудит 1/19: site-navigation

**Проверка предыдущего:** — (это первый скилл, проверять нечего)

**Объём:** 150 HTML-страниц (`docs/*.html` = 19, `docs/sup/*.html` = 131), из них 6
редирект-заглушек → 144 живых; × 2 локали (RU `lang="ru"`, EN
`localStorage.lang='en'`). Сервер `http://localhost:8000` (version.json = 5.6.5).

**Метод.** Сплошной статический обход всех 150 страниц (3021 внутренняя ссылка:
`<a href>`, `<link href>`, `<script src>`) + рантайм-проверка в Playwright на
4 страницах в EN (`index.html`, `hactar.html`, `sup/ashvaganda.html`,
`calculator.html`). Ссылки не зависят от локали: в `docs/i18n.js` нет ни одного
присваивания `href` (`grep -c "\.href ="`, `setAttribute('href'`,
`location.href` → 0), переводятся только тексты через `data-i18n*`. Поэтому
целостность ссылок locale-инвариантна, а EN-специфика проверяется по подписям.

### Находки

| ID | Крит. | Где | Что именно | Локаль | Статус |
|---|---|---|---|---|---|
| NAV-01 | B | `docs/trends.html` | Страница-сирота: 1 входящая ссылка на весь сайт (только `index.html`). Ни в шапке, ни в футере «Трендов» нет. При этом страница в `sitemap.xml`, 64 КБ контента. Для сравнения: `methodology/faq/glossary/privacy/terms` — по 142 входящих. | RU+EN | открыто |
| NAV-02 | C | `docs/hactar.html` (шапка, бренд-чип) | В шапке висит одинокий «v»: `v<span data-version="app"></span>` (3 таких спана на странице) не заполняется, потому что `hactar.html` не подключает `version.js` (подключены `hactar.js`, `i18n.js`, `pwa.js`, `share.js`). На `index.html` тот же чип показывает «v5.6.5». Проверено в браузере: `header.innerText` = «🧠 brain-25-evidence v 💬 Feedback …» | RU+EN | открыто |
| NAV-03 | C | `docs/hactar.js:197` `modeFromUrl()` | Расхождение URL и состояния для неизвестного `?tab=`: `?tab=links` открывает «Обзор», но адрес остаётся `?tab=links` (в отличие от legacy `?tab=calc`/`?tab=compare`, которые переписываются на `?tab=overview` через `syncUrl()`). Ссылка «поделиться» врёт о вкладке. Проверено: `location.search` = `?tab=links`, `aria-selected` = `hactarTabOverview` | RU+EN | открыто |
| NAV-04 | C | `docs/privacy.html:98` | Ссылка «Сравнение» (`data-i18n-text="hactar.redirect.compare"`) ведёт на `hactar.html?tab=compare` — без `ids`. Legacy-шим переписывает адрес в `?tab=overview`, подборка пустая: пользователь жмёт «Сравнение», попадает в общий «Обзор». Остальные 130 карточек передают `&ids=<slug>` и подборка срабатывает | RU+EN | открыто |

### Проверено и в порядке (не находки)

- **Битых ссылок 0.** 3021 внутренняя ссылка на 150 страницах, включая
  `feed.xml`, `sup/index.html`, `terms-of-use.html#data-license` (id
  `data-license` в цели существует), `script.min.js`/`style.min.css`,
  `vendor/chart.umd-4.4.1.min.js`.
- **Редиректы (6) исправны:** `calculator`/`compare` → `hactar.html?tab=overview`;
  `graph`/`atlas`/`interactions`/`map` → `hactar.html?tab=graph`. У всех шести:
  `<meta http-equiv="refresh">`, `rel=canonical` на целевой URL,
  `robots="noindex, follow"`, живая CTA-ссылка в `<body>`. Циклов нет (длина
  цепочки 1). Рантайм: `calculator.html` → `/hactar.html?tab=overview`.
- **Футер единообразен:** 2 легитимных варианта — корневые 11 страниц
  (`faq · feed.xml · glossary · methodology · privacy · sup/index.html ·
  terms-of-use · terms-of-use#data-license`) и 131 карточка `sup/` (те же цели
  с `../`). Ни одной страницы с футером без ссылки на `terms-of-use.html`.
  8 страниц без футера — по назначению: 6 заглушек + `offline.html` +
  `google4a9d23e35c6c3e23.html`.
- **Шапка:** 142 страницы, подписи из словаря (`index.feedback`, `index.support`,
  `index.random`, `theme.light`, `a11y.navMain`, `a11y.langSelect`). На
  `feedback.html` нет ссылки на себя, на `support.html` — на себя: осознанно.
- **EN-шапка и EN-футер:** на `index.html`, `hactar.html?tab=graph`,
  `sup/ashvaganda.html` — `header.innerText` и `footer.innerText` дают
  **0 символов кириллицы**. Подписи: «💬 Feedback», «💚 Support us»,
  «🌞 Light theme» (`aria-label` = «Switch to light theme»), «🎲 Surprise me»,
  RU/EN-селектор. Текст кнопки темы ставит `script.js` через
  `t("theme.light")`/`t("theme.dark")`, а не `data-i18n-text`.
- **Словарь i18n полон:** 1212 ключей RU и 1212 EN, `ru-only`/`en-only` = 0;
  25 ключей, использованных в шапке/футере, присутствуют в обеих локалях.
- **Hactar deep-link:** `?tab=graph` → Links, `?tab=overview` → Overview,
  без параметра → Overview; `?tab=calc` → адрес переписан на `?tab=overview`;
  `?tab=compare&ids=melatonin` → адрес `?tab=overview&ids=melatonin`, 1
  отмеченный чекбокс; `?ids=a,b` → 2 отмеченных.
- **Sitemap:** 141 `<loc>` = 10 корневых контентных + 131 `sup/`; 0 несуществующих,
  0 заглушек, 0 дублей; `404.html`, `offline.html`,
  `google4a9d23e35c6c3e23.html` исключены осознанно; `lastmod`, `changefreq`,
  `priority` — у всех 141.

### Зафиксированные факты (вне счёта находок — это долги других скиллов)

- `hreflang` — **0 вхождений на всех 150 страницах**; `<html lang="ru">` —
  150/150 статически (SEO-01).
- В EN `<title>` остаётся русским: `index.html` → «БАДы: доказательства и
  механизмы — Brain 25 Evidence», `hactar.html` → «Project Hactar — подбор
  БАДов» (SEO-02).
- У табов Hactar есть `role="tab"` + `aria-selected`, но **нет ни одного
  `[role="tabpanel"]`** (входит в accessibility-check).
- `404.html` и `offline.html` имеют 0 входящих ссылок изнутри сайта — норма
  для служебных страниц (их отдаёт хостинг/SW).

**Статус: открыто 4 находок (A: 0, B: 1, C: 3). Код не тронут.**

# STAGE 1C — A11y + i18n + бамп + отложенное из 1B

| | |
|---|---|
| **Дата** | 10.10.2026 |
| **Ветка** | `v5.6-dev` |
| **Базовый HEAD** | `7cc36e3` (fix(stage1b)) |
| **Версия** | v5.6.1 → **v5.6.3** (`docs/version.json`) |
| **Снапшоты** | **не запускались** (§15, §17 AUDIT_MASTER) |
| **pytest** | **822 passed, 2 skipped** (базовая линия сохранена; стоп-условие «< 822» не сработало) |

Границы: правки `docs/style.css`; 144 `docs/*.html` — только бамп `?v=`; 6 отложенных
из 1B. JS-логика, данные, `a:active`, `sw.js`, `main` — не тронуты.

---

## A — Отложенное из 1B

### A1. `main h1 !important` → базовая иерархия h1–h5

**До:** `main h1 { font-size: 1.35rem !important; ... }` (`style.css:1616`) пиннил h1 = 21.6 px
на всех страницах; базовых правил для h3/h4 не было, h2 пяти размеров.

**После** (`docs/style.css`):

| Селектор | Было | Стало |
|---|---|---|
| `h1` | 1.35rem (пин) | **1.75rem = 28 px**, weight 600 |
| `h2` | пять размеров | **1.5rem = 24 px**, weight 500 |
| `h3` | только скоупы | **1.25rem = 20 px**, weight 600 |
| `h4` | только скоупы | **1.1rem = 17.6 px**, weight 600 |
| `h5` | — | **1rem = 16 px** (без изменений) |
| `main h1` | font-size 1.35rem !important | font-size **удалён** (остальные !important сохранены) |
| `@media (max-width:768px) h1` | 1.4rem | 1.75rem |

Снятие пина потребовало убрать локальные `h1 { font-size: 1.05rem !important }` в
мобильных медиазапросах `docs/index.html` и `docs/map.html` (иначе h1 = 16.8 px на
телефоне): оставлен только `line-height: 1.3`.

**Замерено (Playwright, cache-buster, 10 контрольных страниц):** иерархия
28 > 24 > 20 > 17.6 > 16 = body подтверждена на 1280 и 412. Точечное исключение —
scoped `#qaSection .qa h3 { font-size: 1rem }` (16 px) на index/faq — намеренное.
Сломанных страниц: **0 из 10** (стоп-условие «> 5» не сработало).

**Следствия базы h3 = 20 px** (инверсии h2 < h3 появились бы там, где локальный h2 был
< 20 px; все три страницы — в границе):
- `calculator.html`: `.params h2` и `.panel h2` — удалён `font-size: 1rem` (16 px → 24 px);
- `index.html`: `#chartSection h2 { font-size: 1rem !important }` — удалено (16 → 24 px);
- `map.html`: `#details h2 { font-size: 1.15rem }` — удалено (18.4 → 24 px); `.sim h4`
  `font-size: .85rem` — удалено (13.6 → базовые 17.6 px).

### A2. map.html — 80 элементов `.cat h3` @ 12/11.2 px

**До:** локальный `<style>`: `.cat h3 { font-size: .75rem }` (12 px) и в медиазапросе
`.cat h3 { font-size: .7rem }` (11.2 px) — 80 элементов.

**Решение:** `.cat h3` — это uppercase-микро-тогглы категорий в сетке мишеней, а не
обычные заголовки разделов. Приведены к **h5 = 1rem = 16 px** (не к базовым h3 20 px —
20 px раздуло бы колонку). Медиазапрос с `font-size: .7rem` удалён полностью
(заменён комментарием `v5.6.3 / A2`), `.chip`-строка сохранена.

**После:** `docs/map.html` — `.cat h3 { font-size: 1rem; ... }`, в медиазапросе — без
переопределения (осталось базовое h5).

### A3. calculator.html — второе `.empty`

**До:** два определения `.empty`: база `style.css` (`padding: var(--space-12) var(--space-4);
opacity: .8`) И локальное в `<style>` calculator.html (`opacity: .55; font-style: italic;
font-size: .85rem; padding: var(--space-2) 0`). Побеждало локальное — база была
мёртвым весом (работали только `grid-column` и `text-align`).

**После:** одно определение — в `style.css`, с поведением, которое реально используют
6 контейнеров calculator (`#selectedList`, `#confListSupp`, `#confListDrug`, `#confListSubs`,
`#synList`, `#warnList`) и JS-заглушки:
`.empty { grid-column: 1/-1; text-align: center; padding: var(--space-2) 0; opacity: .55;
font-style: italic; font-size: .875rem; }`. Локальный `.empty` из HTML удалён. Попутно
из HTML удалён `font-size: .85rem` у `.block h3` (13.6 px < body), h3 = базовые 20 px.
`html.light #selectedList .empty { opacity: 1; color: var(--muted) }` сохранён.

### A4. Шкала 26 → 6 (по карте STAGE1B_TYPOGRAPHY.md)

**До:** 26 off-scale значений, ~70 объявлений в `style.css`.

**После:** шкала сведена к 6 значениям: **0.875 / 1 / 1.1 / 1.25 / 1.5 / 1.75 rem** (+
спецприём `font-size: 0` на atlas.html — иконочный `.btn`, задокументирован).
Скриптом со строгими проверками заменено 72 строки. Ключевые свёртки:
`.95rem→1rem` (.btn, button, #compareResult table, .mech-body), `16px→1rem`
(select/input/textarea), `.75–.92rem→.875rem`, `1.02/1.05rem→1rem`, `1.15–1.35rem→1.25rem`,
`1.35–1.4rem→1.5rem`, `1.8rem→1.75rem`. Физический дубль `.9rem/0.9rem` уничтожен
(9 объявлений → .875rem). Изменено ~67 объявлений — стоп-порог «> 100» НЕ нарушен.

**Контроль:** off-scale значений в объявлениях style.css не осталось (все оставшиеся
`0.9/0.85/0.92/1.05rem` и `15px` — внутри комментариев).

### A5. index.html: инлайновый font-size #trustSummary → CSS

**До:** `<h2 style="margin:0;font-size:1rem">` внутри `#trustSummary` (h2 16 px = body).

**После:** `style="margin:0"`; h2 = базовые 24 px.

### A6. Горизонтальный скролл calculator.html на 412 px

Диагностика + A/B-тест против состояния HEAD (копия `docs` + `git show HEAD:...`
для style.css/calculator.html, сервер на 8011):

- 412 px: `document.scrollWidth == clientWidth == 397`, `body.scrollWidth == 397` — скролла
  **нет** ни в текущем состоянии, ни на HEAD. Значение `docScrollW 752` из
  STAGE1B_TYPOGRAPHY.md (стр. 135-137) **не воспроизводится**.
- Гипотеза «старое центрирование `#cookieBanner` (`left:50%` + `translateX(-50%)`)»
  проверена инъекцией старого CSS в живую страницу → `scrollWidth` остался 397,
  не подтвердилась.
- Единственный широкий элемент — лента навигации `.actions` (`overflow-x:auto` +
  `flex-wrap:nowrap` + `min-width:0` + `width:100%`, scrollWidth 1204 при clientWidth 346):
  прокручивается внутри себя **по дизайну** (v5.6.2 #96).

**Вывод:** правок A6 не потребовал, дефект уровня документа отсутствует.

---

## B — A11y

### B1. Skip-link клиппингом (P0-4)

**До:** `.skip-link { position: absolute; left: -9999px; top: 0 }` — при `dir="rtl"` документ
расширялся до 11 264 px на 144 страницах.

**После:**
```css
.skip-link { position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0;
             overflow: hidden; clip: rect(0,0,0,0); clip-path: inset(50%);
             white-space: nowrap; border: 0; }
.skip-link:focus { position: fixed; inset-inline-start: 0; top: 0; z-index: 9999;
             background: #000; color: #fff; width: auto; height: auto; margin: 0;
             clip: auto; clip-path: none; overflow: visible; padding: var(--space-2) var(--space-4);
             padding-top: env(safe-area-inset-top, 0px); font-size: .875rem;
             border-radius: 0 0 6px 0; text-decoration: none; }
```
Техника — та же, что у `.sr-only`. При `focus` элемент получает `inset-inline-start` +
`position: fixed` и появляется у края независимо от направления письма.

**Проверка (Playwright, `document.documentElement.dir='rtl'` на index/faq/calculator):**
до: sw = cw = 1265, после: sw = cw = 1265 — ширина документа НЕ растёт (не 11 264 px).
Computed `.skip-link`: width/height 1px, `clip: rect(0,0,0,0)`, `clip-path: inset(50%)`.

### B2. prefers-reduced-motion (P1-8)

Добавлен блок в конец `style.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    transition-delay: 0s !important;
    scroll-behavior: auto !important;
  }
  html { scroll-behavior: auto !important; }
}
```
**Проверка (Playwright `emulate_media`):**
`no-preference` → max animation 0.22 s, max transition 0.25 s, @keyframes = 3 (sh, popIn, fadeIn);
`reduce` → max animation/transition = **0.01 ms**, iteration-count 1 → анимации эффективно
выключены. @keyframes остаются объявленными (3), но безусловные длительности убраны.
Среда после замера возвращена в `no-preference`.

---

## C — i18n

### C1. Логические свойства (P1-13) — 26 вхождений в style.css

Аудит говорил «13 мест»; фактическая проверка по репозиторию показала
**26 вхождений** физических свойств (left/right/margin-left/padding-right) в 22 правилах.
Все заменены:

| # | Правило | Было | Стало |
|---|---|---|---|
| 1 | `label` | `margin-right` | `margin-inline-end` |
| 2 | `.card .effects span` | `margin-right` | `margin-inline-end` |
| 3 | `#modalClose` | `right: .6rem` | `inset-inline-end: .6rem` |
| 4 | `.favBtn` | `top: .5rem; right: .6rem` | `inset-inline-end: .6rem` |
| 5 | `.favBtn` | `top: 4px; right: 4px` | `inset-inline-end: 4px` |
| 6 | `.favFilter` | `margin-left` | `margin-inline-start` |
| 7 | `#toTop` | `right: 1.2rem` | `inset-inline-end: 1.2rem` |
| 8 | `.grade` | `margin-left` | `margin-inline-start` |
| 9 | `.gdots` | `margin-left` | `margin-inline-start` |
| 10 | `.vwait` | `margin-left` | `margin-inline-start` |
| 11 | `.manual-badge` | `margin-left` | `margin-inline-start` |
| 12 | `.srcIcon` | `margin-left` | `margin-inline-start` |
| 13 | блог `.entry` (cont) | `margin-left: var(--space-2)` | `margin-inline-start: var(--space-2)` |
| 14 | блог `.entry` | `right: 1.2rem` | `inset-inline-end: 1.2rem` |
| 15 | `.legend span::before` | `margin-right` | `margin-inline-end` |
| 16 | `.sb-close` | `right: -.4rem` | `inset-inline-end: -.4rem` |
| 17 | `.sb-sev` | `margin-left` | `margin-inline-start` |
| 18 | `#int-sidebar h2` | `padding-right` | `padding-inline-end` |
| 19 | `#atl-sidebar h2` | `padding-right` | `padding-inline-end` |
| 20 | `#atl-sidebar .close-x` | `right: 0` | `inset-inline-end: 0` |
| 21 | `#atl-sidebar .badge` | `margin-left` | `margin-inline-start` |
| 22 | `#atl-sidebar .mech .str` | `margin-left` | `margin-inline-start` |
| 23 | `#cookieBanner` | `position: fixed; left: 50%; transform: translateX(-50%)` | `position: fixed; inset-inline: 0; margin-inline: auto` |
| 24–25 | `#int-sidebar` / `#atl-sidebar` (идентичны, count=2) | `left: 0; right: 0; … border-left: none` | `inset-inline: 0; … border-inline-start: none` |

**Контроль (regex по style.css):** `margin-left/right`, `padding-left/right` = 0 вхождений;
`left:`/`right:` = 0 объявлений (единственное упоминание — в комментарии B1);
`inset-inline` ×11, `margin-inline` ×14, `padding-inline` ×2, `border-inline-start` ×2.

Осознанно не тронуты (вне 4 семейств аудита, документировано): физические
`border-left` в `.cgTitle`/`.mech-card`/`.inter-card`/`#int-sidebar`/`#atl-sidebar`
(визуальная полоса, зеркалится отдельно), `text-align`.

### C2. `dir` атрибут (P1-14)

`<html lang="ru">` → `<html lang="ru" dir="ltr">` в шаблонах
`templates/sup.html.j2` и `templates/sup_index.html.j2` (подготовка к i18n, не сам перевод).
131 сгенерированная страница `docs/sup/` **не перегенерирована** — граница
«144 docs/*.html (только бамп ?v=)»; она получит `dir` при ближайшем прогоне
`scripts/build_sup.py`. Зафиксировано в AUDIT_MASTER как «закрыто на уровне шаблонов».

---

## D — Бамп

### D1. style.css?v=422 → 423 (все 144 HTML)

Скрипт с подсчётом вхождений: заменено **144 файла, 144 вхождения**. Контроль:
`grep -c "style.css?v=423"` → 144, `?v=422` → 0. Не тронуты (и не содержали ссылки):
`docs/google4a9d23e35c6c3e23.html` (верификация GSC), `docs/offline.html` (не грузит style.css).
Заодно устранён дрейф шаблонов: `../style.css?v=414` → `?v=423` в обоих `.j2`.

### D2. docs/version.json

`{"app": "5.6.1", ...}` → `{"app": "5.6.3", "data": "2026-09-25", "audit": "1.0", "tests": 1023}`.
`tests` — число из `pytest --collect-only -q` (1023), синхронизировано с
`test_version_json_tests_match_collected`.

---

## Проверка (ПРОВЕРКА из задания)

1. **Desktop 1280:** h1=28 > h2=24 > h3=20 > h4=17.6 > h5=16 = body — ✅ (10 страниц).
2. **Mobile 412:** то же, все 10 страниц `sw == cw == 397`, горизонтального скролла нет — ✅.
3. **RTL (`dir="rtl"`):** ширина документа 1265 px, НЕ 11 264 — ✅.
4. **prefers-reduced-motion:** animation/transition-duration = 0.01 ms под `reduce` — ✅.
5. **Бамп:** 144 файла с `?v=423` — ✅.
6. **pytest -q:** **822 passed, 2 skipped**, 1 warning (существующий, KNOWN_DEAD_CSS) — ✅.
7. **Снапшоты:** не запускались — ✅.

## pytest

`python -m pytest --collect-only -q` → **1023 collected** (== `version.json.tests`).
`python -m pytest -q` → **822 passed, 2 skipped, 1 warning in 34.21 s** — базовая линия
сохранена, стоп-условие «< 822» не сработало. Снапшоты не запускались (§15, §17).

## Остаток (вне границы, в отчётное поле следующего этапа)

- Локальные переопределения заголовков на страницах **вне границы** (не тронуты):
  `faq.html` h2 1.125rem (замер 24 px — локальное правило на странице не срабатывает),
  `privacy.html` `.privacy-wrap h2` 1.15rem (18 px), `support.html` `.support-card h2` 1.2rem
  (19 px), `trends.html` h2 1.15rem (18 px) — все ниже новой базы h2 24 px; `trends.html`
  имеет 2× h1. Инверсий h2 < h3 на этих страницах нет (h3 отсутствуют или локально
  меньше), поэтому визуального дефекта не создано.
- Физические свойства в локальных `<style>` страниц (граница «только бамп»): map.html
  `#details h2 { padding-right: 2.2rem }`, `.list { padding-right: .4rem }` и др.
- P1-7 (`:active`) — задание 1C явно запрещает трогать `a:active`; остаётся открытой.
- 131 sup-страница без `dir` на диске — закроется при следующем `build_sup`.

## Файлы

148 файлов: 144 `docs/*.html`, `docs/style.css` (375 строк диффа), `docs/version.json`,
`templates/sup.html.j2`, `templates/sup_index.html.j2`. Плюс этот отчёт и AUDIT_MASTER (§17).
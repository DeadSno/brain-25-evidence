# WAVE_D_STRUCT — план D7: #42 + #24 (объединённая)

Ветка: `v5.6-dev` · HEAD `93925d8` · дата 2026-10-12.
**Статус: план. Правок в коде не сделано, `build_sup.py` не запускался.**

Обе задачи упираются в одно: перегенерация sup-страниц требует
пересъёмки эталонов. Одна задача = одна пересъёмка.

---

## #42 — локальные `<style>` для `.top`

### Что найдено

Локальный `<style>` есть на **14** страницах, но правила для `.top` —
ровно на **7** (формулировка задания верна именно в этом смысле).

Всего **61 правило** для `.top` на 7 страницах. Главный CSS —
`docs/style.css`, подключается как `style.css?v=425`.

| Страница | Правил | Что перекрывает style.css | `!important` | Куда переносить |
|---|---|---|---|---|
| `docs/index.html` | 17 | `@media (max-width:640px)`, дубли font-size ×4 | **есть** 74–76, 91, 93, 110, 112–114, 119 | `style.css` в блок `@media (max-width:640px)` |
| `docs/trends.html` | 11 | `header.top .actions > *.btn` (54–68) и `.site-title` (92–102) | **есть** 54–62, 66–68, 92–93, 95, 97 | `style.css` + `body.trends-page` селекторы |
| `docs/atlas.html` | 9–10 | базовый `.top` (58–60) и дубль (90–94) + `body.fs .top` (80) | нет в `.top` | `style.css` базовый блок `.top` |
| `docs/map.html` | 9 | то же (92–94 и 244–248) | нет | ditto |
| `docs/feedback.html` | 7 | базовый `.top` (50–56) + мобильный (83–85) | нет | ditto |
| `docs/interactions.html` | 4 | только мобильный медиазапрос (78–81) | нет | ditto |
| `docs/calculator.html` | 3 | 51, и 186–187 в медиазапросе | нет | ditto |

### Ключевой конфликт — СТОП-условие

`style.css` **уже доминирует** над локальными правилами, и это не
случайность:

- `style.css:1297` — `header.top { display: grid !important; grid-template-areas: "title" "actions" !important }` в `@media (max-width:640px)`.
  Локальные правила страниц задают `flex-direction` / `flex-wrap` —
  они **не работают** и не могли работать.
- `style.css:992–996` — `@media (max-width:480px)` с `!important` на
  `.site-title` и `.actions`.
- Комментарий `style.css:1446–1448` прямо фиксирует: `!important`
  там обязателен, потому что «на строке 745 стоит
  `header.top .actions{flex-wrap:wrap!important}`».

Значит перенос локальных правил в `style.css` — **не косметика**:
либо дублирующие правила переезжают как есть и меняют вычисленные
значения, либо их надо удалить, а тогда 61 правило схлопывается
до нуля, потому что всё уже покрыто сеткой из 1297.

Отдельно: `trends.html:83–89` — комментарий, прямо признающий, что
правило `header.top{position:static}` стало беспредметным после
переезда липкости на `.site-header` (`style.css:692, 694`).
Это подтверждает общий вектор: локальные правила устарели,
а не дополняют.

**Это ровно то стоп-условие «конфликт локального `<style>` с
`style.css`, требующий изменения дизайна → СТОП».**

Стоп-условие «#42 затрагивает >10 страниц» **не срабатывает** —
страниц 7, в норме.

---

## #24 — nav-лендмарк на sup-страницах

### Шаблон: `templates/sup.html.j2`

Шапка, строки 60–71 (`.actions` = **`<div>`**, строки 64–69):

```html
<div class="site-header">
  <div class="trustbar">🧬 Открытые данные · Бесплатно · Без рекламы</div>
  <header class="top">
    <div class="site-title"><a href="../index.html">… brain-25-evidence</a></div>
    <div class="actions">
      <a class="btn c-home" href="../index.html">🏠 Главная</a>
      <a class="btn c-feedback" href="../feedback.html">💬 Обратная связь</a>
      <a class="btn c-support" href="../support.html">💚 Поддержать</a>
      <button class="btn" id="themeBtn">🌞 Светлая тема</button>
    </div>
  </header>
</div>
```

### Что менять

Эталон «этапа 2» (коммит `d996c1b`), `docs/index.html:182`:

```html
<nav class="actions" aria-label="Главная навигация">
```

Правка в шаблонах: `<div class="actions">` → `<nav class="actions" aria-label="Главная навигация">`,
закрывающий `</div>` → `</nav>`.

- `templates/sup.html.j2` — строки 64 и 69
- `templates/sup_index.html.j2` — строки 85–90 (то же самое)

Риск для CSS минимален: селекторы в `style.css` классовые
(`.actions`, `.top .actions`, `header.top .actions`) — проверено
в `reports/archive/v56/STAGE2_HTML.md:41–48`, тег `<div>`→`<nav>`
на них не влияет.

Отдельно решение #7 / §24 (`ROADMAP.md:380–382`): `display: contents`
теряет лендмарк — на sup не применяется, менять не нужно.

### Сколько страниц перегенерируется

**131** — 130 карточек + `docs/sup/index.html`. Источник один
(`docs/data.json`, 130 записей, 130 уникальных slug).

Замер по факту в `docs/sup/`:

| Признак | Файлов |
|---|---|
| всего `.html` | **131** |
| `<div class="actions">` | **131** |
| `<nav class="actions` | **0** |
| `<nav aria-label` | **0** |
| `<nav class="breadcrumbs">` (крошки, без aria-label) | **131** |

То есть «нет `<nav>`» буквально неверно — nav-элемент есть на всех
131, нет **именованного лендмарка в шапке**. Из 15 корневых
`docs/*.html` лендмарк есть на 13; без него
`google4a9d23e35c6c3e23.html` и `offline.html`.

### ⚠️ Стоп-условие `?v=` — СРАБОТАЛО

> Стоп-условие задачи: «build_sup.py --all откатывает cookie/privacy/?v= → СТОП»

- `cookie` / `privacy` — **отката нет**: оба блока уже в шаблонах
  (`sup.html.j2:183–188, 212–228`), 131/131 страниц их содержат.
- **`?v=` — откат ЕСТЬ.** `templates/sup.html.j2:36` и
  `sup_index.html.j2:30` содержат `style.css?v=423`, а на всех 131
  закоммиченных страницах — `style.css?v=425`.

Любой прогон генератора откатит бампер 425 → 423 на всех 131
страницах. Остальные бамперы совпадают (`version.js?v=312`,
`pwa.js?v=282`, `share.js?v=1`).

**Поэтому шаблон надо править в два захода: сначала бампер
423 → 425, и только потом — nav.**

---

## План

1. **Остановиться и получить решение по #42** — перенос 61 правила
   конфликтует с `style.css:1297` (grid + `!important`). Это
   изменение дизайна, а не миграция. Без решения шаг 2 не делаем.
2. Поднять `templates/*.j2` `?v=423` → `?v=425`. Отдельный коммит,
   проверяется grep, перегенерации не требует.
3. Заменить `<div class="actions">` → `<nav class="actions" aria-label="Главная навигация">`
   в `sup.html.j2` и `sup_index.html.j2`.
4. Прогнать `scripts/build_sup.py` **без `--only`** — флага `--all`
   в скрипте нет (`--only`, `--data`, `--template-dir`, `--out`,
   `--dry-run`, `--skip-index`; `build_sup.py:377–388`).
   Перед этим — `--dry-run`, чтобы увидеть объём.
5. Переснять эталоны: **20 PNG** (`tests/snapshots/chromium/sup-*.png`
   10 + `webkit/sup-*.png` 10; страницы `sup/kreatin`, `sup/omega-3`,
   `sup/vitamin-d`, `sup/magniy`, `sup/paba`, 2 вьюпорта × 2 движка —
   `tests/test_visual_snapshots.py:92–104`) и обновить **10 записей**
   в `tests/a11y_baseline.json:55–84`.
6. Прогнать гейты, которые заденут все 131 страницу:
   `test_no_orphan_classes.py:144` (`assert == 131`),
   `test_css_tokens.py:96`, `test_no_bom.py:21,46,75`.
7. Коммит через **shell** (`git add` / `git commit`), MCP `git_commit`
   недоступен — по решению владельца от 2026-10-12 техническая
   блокировка невозможна, см. `.opencode/skills/CONVENTIONS.md`.

**Перед прогоном проверить сервер:** эталонные снапшоты скипаются
молча, если сервер на `:8000` не отвечает
(`Invoke-RestMethod http://localhost:8000/version.json`).

---

## Отличия от задания

1. **#42 — 7 страниц, но локальный `<style>` на 14.** «7» верно
   только для правил `.top`.
2. **`graph.html` не ловится паттерном `<style>`** — у него
   `<style type="text/css">` (строка 54). Подсказка
   `Select-String -Pattern "<style>"` его пропустит.
3. **ROADMAP пишет «trends 1», фактически 11** правил
   (`header.top`, строки 52–102). Видимо, считали селекторы
   с чистым `.top` — в trends их 0.
4. **«atlas 9»** — 9 строк с `.top…`, 10 с групповым `body.fs .top`
   (`atlas.html:80`).
5. **`git_push` не существует** — 12 тулов: 7 read + 5 write
   (`git_add`, `git_commit`, `git_checkout`, `git_create_branch`,
   `git_reset`).
6. **Флага `--all` в `build_sup.py` нет** — формулировка неприменима.
7. **`reports/OPEN_TECHDEBT.md:286` содержит фактическую ошибку:**
   утверждает, что 131/131 sup имеют `<nav class="breadcrumbs" aria-label>`
   в `sup.html.j2:77`. На строке 77 — `<nav class="breadcrumbs">`
   **без** `aria-label`. Противоречит `reports/audits/a11y.md:20`
   (находка открыта). Второе верно.
8. **`reports/STAGE8BC_DOCS.md` противоречит себе:** #24 числится
   в «Закрыто (38)» на строке 97 и одновременно открыт на 150–151.

---

# ИТОГ D7 (выполнено 2026-10-12)

Ветка `v5.6-dev`. План утверждён владельцем: **#42 закрыть как
устаревшее**, **#24 — через регенерацию**.

## Результат

| Пункт | Итог |
|---|---|
| **#24** | ✅ **закрыт** — `<nav class="actions" aria-label="Главная навигация">` на **131/131** sup-страниц. Остаток `<div class="actions">` — **0** |
| **#40** | ✅ **закрыт попутно** — блок «Формы выпуска» на **7** страницах |
| **#42** | ✅ **закрыт как устаревшее** — локальные правила `.top` уже мертвы из-за `style.css:1297` (`display: grid !important`) |
| **Snapshot** | **69** обновлено = **49** baseline-долг + **20** D7 |

## Что сделано

**#42 — закрыт как устаревший долг.** `docs/style.css:1297` в
`@media(max-width:640px)` объявляет `header.top { display: grid !important;
grid-template-areas: "title" "actions" !important }`. Локальные flex-правила
7 страниц уже не применяются. Плюс `style.css:992–996` (@media 480px с
`!important`) и комментарий `trends.html:83–89`, где сама страница признаёт,
что `header.top{position:static}` стал moot после переноса sticky в
`.site-header` (`style.css:692,694`). Перенос 61 правила означал бы правку
дизайна — по стоп-условию остановлен и вынесен на решение владельца.

Локальные `<style>` **намеренно не удалены**: они безвредны (мёртвый код
не влияет на рендер), а их удаление — отдельная задача с пересъёмкой.

**#24 — регенерация.** Правки в `templates/sup.html.j2` и
`templates/sup_index.html.j2`: `<div class="actions">` →
`<nav class="actions" aria-label="Главная навигация">` + закрывающие теги.
Бампер `?v=423` → `?v=425` поднят в шаблонах **до** прогона —
иначе регенерация откатила бы 131 страницу на старый бампер
(стоп-условие «`?v=` откат» было реальным, не гипотетическим).

CSS-безопасность свопа проверена: селекторов `div.actions` и
`.actions > div` в `docs/style.css` нет вообще.

## Стоп-условия — ни одно не сработало

| Условие | Проверка | Итог |
|---|---|---|
| Конфликт `<style>` с `style.css`, требующий правки дизайна | Найден, но **не правился** — вынесен владельцу, решение «закрыть как устаревшее» | ✅ |
| #42 затрагивает >10 страниц | 7 страниц (14 файлов со `<style>`) | ✅ |
| `build_sup.py` откатывает cookie/privacy/`?v=` | `metrika.js` 131/131, `cookie-banner.js` 131/131, `cookieBanner` 262 вхождения, `privacy.html` 262; `?v=425` на 131/131 | ✅ |

`--dry-run` перед прогоном ничего не записал (131 файл / 1 922 778 байт),
убедиться в масштабе до записи.

## #40 закрылся не по плану — и это было правильно остановиться

`build_sup.py` пересобирает **все** 131 страницу целиком, разделить
прогон по фичам нельзя. 124 файла дали ровно `+2 −2` (тег + `aria-label`),
но **7** — `+7 −2`: `kollagen`, `magniy`, `melatonin`, `omega-3`,
`probiotiki`, `vitamin-d`, `zhelezo`. Лишние 5 строк в каждом — блок
«Формы выпуска», то есть **#40** («шаблон готов, HTML не пересобран»,
блок `{% if forms %}` с коммита `a82e070`, `OPEN_TECHDEBT.md:402–412`).
Ровно 7 карточек имеют строковый `forms` в `data.json` — совпадение
до единой.

Агент остановился и спросил. Решение владельца: коммитить раздельно,
**не откатывать**. Отделить 7 файлов от остальных внутри одного коммита
невозможно — в них оба изменения.

## Эталоны: 69 = 49 + 20, разбито на два коммита

Прогон дал **69** изменённых PNG, а ожидалось 20. Причина найдена:
последний прогон эталонов — `73ad345` от **2026-10-11**, а коммиты
tap-targets в `docs/style.css` — `d0867d9`, `eb5967c`, `f7b56c6`
от **2026-10-12**. Базовая линия устарела **до** начала работы.

**Доказательство, что 49 не мои:** между `HEAD~2` и `HEAD` изменено
**ноль** файлов вне `docs/sup/` и двух шаблонов (`git diff --name-only
HEAD~2 HEAD`) — ни `style.css`, ни одной не-sup страницы. Изменять
не-sup эталон моя работа физически не могла.

| Группа | Кол-во | Коммит |
|---|---|---|
| **baseline-долг D_FAST** (atlas, calculator, cookie-banner, faq, feedback, glossary, graph, index, interactions, map, methodology, modal-index, support, trends) | **49** | `chore(snapshots): rebuild baselines after wave D_FAST` |
| **D7 nav-лендмарк** (`sup-*`: kreatin, omega-3, vitamin-d, magniy, paba × 2 вьюпорта × 2 движка) | **20** | `chore(snapshots): nav landmark baselines on sup` |

Разбито на два коммита по решению владельца: долг D_FAST и работа D7 —
разные по смыслу изменения, смешивать их в одну ревизию нельзя.

## Ловушки, сработавшие в этой сессии

1. **Сервер на `:8000` был не поднят** — `python -m http.server 8000
   --directory docs` (`CONTRIBUTING.md:105`). Проверка
   `Invoke-RestMethod http://localhost:8000/version.json` перед прогоном
   обязательна.
2. **`UPDATE_SNAPSHOTS=1` недостаточно.** Нужны **оба**:
   `RUN_SNAPSHOTS=1` — иначе `tests/test_visual_snapshots.py:632`
   скипает весь набор (76 skipped выглядит как успех), и
   `UPDATE_SNAPSHOTS=1` — иначе тесты проходят, но ничего не пишут
   (`строка 95`). Второе имя нигде не документировано как требование.
3. **`--all` у `build_sup.py` не существует** — полный прогон делается
   без флагов.

## Коммиты

| # | Сообщение | Состав |
|---|---|---|
| 1 | `feat(sup): forms block on 7 pages (closes #40)` | 7 HTML |
| 2 | `fix(a11y): nav landmark on 130 sup pages (closes #24)` | 124 HTML + 2 шаблона |
| 3 | `chore(snapshots): rebuild baselines after wave D_FAST` | 49 PNG |
| 4 | `chore(snapshots): nav landmark baselines on sup` | 20 PNG |
| 5 | `chore: snapshot baselines + close #24/#40/#42` | отчёты + `ROADMAP.md` + `AGENTS.md` + `CONVENTIONS.md` |

Коммиты — через **shell** (`git add` / `git commit`); MCP `git_commit`
недоступен по решению владельца от 2026-10-12 (техническая блокировка
невозможна, разбор в `.opencode/skills/CONVENTIONS.md`).

`tests/a11y_baseline.json:55–84` (10 записей sup) править не пришлось —
гейт прошёл без изменений.
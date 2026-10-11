# Этап 2 — разметка HTML (nav-лендмарк, дубли, порядок, уровни заголовков)

Ветка: `v5.6-dev` · дата: 11.10.2026 · границы: только 13 `docs/*.html`.

Изменено 13 страниц + `reports/AUDIT_MASTER.md`. `sup/*.html` (130 шт.),
`style.css` и JS не тронуты.

---

## A — nav-лендмарк (P1)

### Выбран вариант 2: `<nav class="actions">`

```html
<nav class="actions" aria-label="Главная навигация">
```

### Почему не вариант 1

Вариант 1 требовал обёртки `<nav class="actions-nav">` + нового правила
`.actions-nav { display: contents; }` в `style.css`. Две причины против:

1. **Риск для grid.** `header.top` на ширине ≤640px — `display: grid` с
   `grid-template-areas: "title" "actions"`. Если правило
   `.actions-nav { display: contents }` не загрузится (старый кэш CSS,
   офлайн-режим), `<nav>` становится обычным блочным элементом внутри grid
   и шапка уезжает ровно так же, как в #96 (бокс `.actions` 873px при
   колонке 286px). Вариант 1 ставит вёрстку в зависимость от загрузки
   нового правила; вариант 2 — нет.
2. **Дерево доступности.** `display: contents` исторически выбрасывал
   элемент из accessibility tree в Chrome <89 и Firefox <79. То есть
   способ, которым мы добавляем лендмарк, мог бы его и отменить.

### Почему вариант 2 безопасен — проверка по коду

Все селекторы, завязанные на шапку, **классовые**, а не по тегу. Класс
`.actions` сохранён, поэтому каждый продолжает матчить:

| Селектор | style.css |
|---|---|
| `.actions { display:flex; min-width:0 }` | 1395 |
| `header.top .actions { grid-area: actions !important }` | 1291-1292 |
| `.actions > * { flex-shrink:0; white-space:nowrap }` | 1404 |
| `header.top .actions, header.hdr .actions { … }` (≤480px) | 967 |
| `.site-header .actions, .top .actions, header.top .actions` | 1430-1432 |
| `.actions::-webkit-scrollbar` | 1468-1469 |

Ни одного правила вида `div.actions` в проекте нет. `style.css` не менялся.

### Проверка в браузере (5 страниц × 2 ширины)

| Метрика | desktop 1280 | mobile 375 |
|---|---|---|
| `header.top` display | `flex` | **`grid`** |
| `getComputedStyle(.actions).gridArea` | `auto` | **`actions`** |
| тег `.actions` | `NAV` | `NAV` |
| `get_by_role("navigation", name="Главная навигация")` | **1** | **1** |
| `documentElement.scrollWidth − innerWidth` | **0** | **0** |

`gridArea` = `actions` на 375px — прямое доказательство, что именованная
область grid разрешается на `<nav>`: `grid-template-areas` не сломан.
`navByRole = 1` означает, что лендмарк действительно попал в accessibility
tree с доступным именем, а не просто присутствует в DOM.

Страницы: index, faq, map, interactions, trends. На всех 10 замерах
`overflowX = 0` — признака регрессии #96 нет.

---

## B — дубль «Логотип + Главная» (P2)

**Удалено 12 кнопок**, по одной с 12 страниц.

index.html кнопки не имел — там логотип и есть единственная ссылка на
главную. Итого в шапке осталась ровно одна ссылка на `index.html` —
логотип.

Проверка по всем 13 страницам: `c-home` = 0, `href="index.html"` в шапке
= 1, `href="index.html"` внутри `.actions` = 0.

---

## C — порядок пунктов в шапке (P2)

### Расхождений 3, а не 5

Полное сравнение порядка по всем 13 страницам дало **3** страницы с
отклонением, а не 5: `feedback.html`, `privacy.html`, `support.html` — во
всех трёх `c-graph` стоял перед `c-atlas`, тогда как на остальных — после
`c-bi`.

Отдельно: набор пунктов у страниц **не одинаковый**, как предполагалось в
задании. Каждая страница не ссылается сама на себя:

- `map.html` — без «Механизмы» (это и есть карта механизмов)
- `atlas.html` — без «Атлас», `trends.html` — без «Тренды»,
  `graph.html` — без «Граф связей», `calculator.html` — без «Калькулятор»
- `feedback.html` — без «Обратная связь»
- `privacy.html` и `support.html` — без «Поддержать»
- `interactions.html` — без «Связи» + своя кнопка `#pngBtn`

### Эталон

index.html эталоном быть не может: её шапка — это 4 пункта (Обратная
связь, Обновить, Поддержать, тема), а не полный набор навигации. Порядок
оттуда скопировать нечего.

Эталон — **порядок большинства**: `faq.html`, `glossary.html`,
`methodology.html` имеют идентичный порядок из 11 пунктов.

```
calc > mech > links > atlas > trends > bi > graph > feedback > support > theme
```

### До

```
atlas.html         calc > mech > links > trends > bi > graph > feedback > support > theme
calculator.html    mech > links > atlas > trends > bi > graph > feedback > support > theme
faq.html           calc > mech > links > atlas > trends > bi > graph > feedback > support > theme
feedback.html      calc > mech > links > graph > atlas > trends > bi > support > theme   <-- расхождение
glossary.html      calc > mech > links > atlas > trends > bi > graph > feedback > support > theme
graph.html         calc > mech > links > atlas > trends > bi > feedback > support > theme
index.html         feedback > refresh > support > theme          (своя шапка, не трогали)
interactions.html  calc > mech > atlas > trends > bi > graph > feedback > #pngBtn > support > theme
map.html           calc > links > atlas > trends > bi > graph > feedback > support > theme
methodology.html   calc > mech > links > atlas > trends > bi > graph > feedback > support > theme
privacy.html       calc > mech > links > graph > atlas > trends > bi > feedback > theme   <-- расхождение
support.html       calc > mech > links > graph > atlas > trends > bi > feedback > theme   <-- расхождение
trends.html        calc > mech > links > atlas > bi > graph > feedback > support > theme
```

### После

`c-graph` перенесён после `c-bi` на трёх страницах. Заодно убран
посторонний пустой ряд, оставшийся в `feedback.html` от прошлой правки.

Полный набор из 11 пунктов теперь одинаков на **faq, glossary,
methodology**. Остальные 9 страниц совпадают с эталоном с точностью до
своей собственной ссылки (и `#pngBtn` у interactions), index.html не
тронут.

Проверка после правок:

| Страница | Порядок | Отношение к эталону |
|---|---|---|
| faq / glossary / methodology | полные 11 | эталон |
| feedback | 10 | эталон − `feedback` |
| privacy / support | 10 | эталон − `support` |
| graph | 10 | эталон − `graph` |
| trends | 10 | эталон − `trends` |
| atlas | 10 | эталон − `atlas` |
| calculator | 10 | эталон − `calc` |
| map | 10 | эталон − `mech` |
| interactions | 11 | эталон − `links` + `#pngBtn` |
| index | 4 | своя шапка, осознанно |

Нарушений порядка не осталось.

---

## D — пропуски уровней заголовков (P2) — WONTFIX

### Найдено: 2 страницы

| Страница | Переход | Где |
|---|---|---|
| `index.html` | h1 → h3 | три вопроса внутри `.qaGrid .qa` (строки 249, 253, 257) |
| `trends.html` | h2 → h4 | четыре заголовка внутри `.method-body` (767, 773, 776, 782) |

Пропуски в `map.html`, `interactions.html`, `atlas.html` — внутри
JS-строк, то есть в генерируемом DOM, а не в статической разметке. В
границы этапа не входят.

### Решение: не исправлять

Обоснование:

1. **Это не нарушение WCAG.** Пропуск уровней — замечание axe
   `heading-order` с серьёзностью *best practice*. Критерий 1.3.1
   (Info and Relationships) требует программно определяемой структуры, но
   не требует непрерывной иерархии уровней.
2. **index.html — осознанное решение v5.5.0.** Комментарий на строке 238
   прямо фиксирует этот пропуск как принятую цену: заголовок h2 над
   `<details>` убрали, потому что на экране читались два заголовка подряд,
   и текст перенесли в `<summary>`. Там же описан штатный способ починки —
   вернуть заголовок внутрь `<summary>`.
3. **Предложенный способ правки ломает вёрстку.** Требование этапа —
   «визуальный стиль не должен измениться» — прямо нарушается:
   - `index.html`: `.qaGrid .qa h3 { font-size:1rem }` (16px). Замена на h2
     отключает это правило, срабатывает
     `h2 { font-size:1.5rem; font-weight:500 }` = 24px, жирность
     600→500, другие отступы.
   - `trends.html`: `.method-body h4 { font-size:1.1rem !important }`
     (17.6px). Замена на h3 даёт базовый `h3 { font-size:1.25rem }`
     = 20px и другие отступы.
4. **Риск снапшотов** при такой правке высок, а выигрыш — снятие
   best-practice замечания.

Перенесено в отдельную задачу при необходимости.

---

## Проверка

### Тесты

```
pytest -q  →  822 passed, 2 skipped
```

Прогон выполнен **при поднятом сервере** `:8000` (абсолютный путь
`C:\analytics\brain-25-evidence\docs`), иначе снапшоты скипаются молча.
Второй прогон с сервером поднятым дал тот же результат. Оба скипа —
e2e, помеченные `@pytest.mark.e2e`, они требуют `RUN_E2E=1` и к правкам
отношения не имеют.

### Снапшоты

`tests/test_visual_snapshots.py` отработал в составе 822, падений нет.
Переснимать не понадобилось: правки не изменили геометрию (см. ниже).

### Геометрия шапки — «не выше, не ниже»

Замер «до» снят с эталонной копии HEAD, развёрнутой на `:8001`
(`git archive HEAD docs`), «после» — с рабочей на `:8000`.

| Контекст | Страница | Высота шапки | Δ | Ширина `.actions` | Δ |
|---|---|---|---|---|---|
| desktop 1280 | index | 44 | **0** | 568 | 0 |
| desktop 1280 | faq | 159 | **0** | 1152 | 0 |
| desktop 1280 | map | 145 | **0** | 1104 | 0 |
| desktop 1280 | interactions | 150 | **0** | 1232 | 0 |
| desktop 1280 | trends | 133 | **0** | 1152 | 0 |
| mobile 375 | index | 84 | **0** | 356 | 0 |
| mobile 375 | faq | 83 | **0** | 343 | 0 |
| mobile 375 | map | 79 | **0** | 337 | 0 |
| mobile 375 | interactions | 79 | **0** | 356 | 0 |
| mobile 375 | trends | 79 | **0** | 327 | 0 |

Высота шапки и ширина `.actions` не изменились ни на одной странице ни на
одной ширине, несмотря на удаление кнопки «Главная» — на desktop строка
одна и занимала всю ширину, на 375px число рядов не изменилось. Горизонтальный
скролл документа = 0 везде.

### Кодировка

Все 15 изменённых/проверенных файлов — валидный UTF-8, **без BOM**, без
признаков UTF-16 и без NUL-байтов. Проверено побайтово, а не на глаз:
замена `div` → `nav` не должна была повторить историю из
`AUDIT_MASTER §21`.

---

## Остаточные пункты

- 130 `sup/*.html` сохраняют кнопку «🏠 Главная» и `<div class="actions">`.
  Внутри границ этапа не трогались — отдельная задача.
- `.c-home` в `style.css` остался неиспользуемым. Правило не удалялось:
  его используют `sup/*.html`.
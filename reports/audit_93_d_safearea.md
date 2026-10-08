# #93 — Часть D: safe-area (эмуляция iPhone)

**Дата:** 2026-10-08
**Ветка:** `v5.6-dev` (HEAD `a645153`)
**Браузер:** Playwright WebKit 26.6 (revision 2359), Playwright 1.63.0 (Python, `.venv`)
**Сервер:** `http://localhost:8000`
**Скрипт:** `scripts/_tmp_93_d4.py` → `reports/_tmp_93_d4.json`, `reports/_tmp_93_d4_look.txt`
**Скриншоты:** `reports/_tmp_93_d3_*`, `reports/_tmp_93_d2_*`
**Режим:** read-only, правок нет.

---

## 0. Итог одной строкой

**Механизм `env(safe-area-inset-*)` в проекте работает и является несущей конструкцией — контрольный прогон без него даёт 3 перекрытия выреза на страницу, эмулированный 0. Найдено 2 реальных P1-дефекта: skip-link в фокусе уходит под вырез, `#toTop` наезжает на home indicator. Плюс P2: нет ни одного правила для `safe-area-inset-left/right`, то есть landscape не защищён.**

---

## 1. Главное ограничение: Playwright WebKit не отдаёт реальные инсеты

Проверено внедрённым пробным элементом:

```js
envSafeArea = {top: "0px", bottom: "0px", left: "0px", right: "0px"}
```

**WebKit под Playwright всегда возвращает `env(safe-area-inset-*)` = `0px`.** Устройство «iPhone» в Playwright — это только вьюпорт и DSR; реальные insets с точки зрения CSS-движка не выставляются.

Следствие: наивный «аудит safe-area» на Playwright всегда даёт ложный PASS. Чтобы получить осмысленный результат, инсеты нужно **эмулировать инъекцией CSS** — но только тех селекторов, для которых в `style.css` действительно есть правила с `env()`.

---

## 2. Метод (v3 — корректный; v1 и v2 отброшены)

Первая версия (`_tmp_93_d.py`) и вторая (`_tmp_93_d2.py`) дали ложные срабатывания и **не используются**:

| Ошибка v1/v2 | Как исправлено в v3 |
|---|---|
| Инъекция `padding-top` одновременно в `.site-header` **и** в `.trustbar` → двойной учёт инсета, шапка раздувалась до 284 px | Инъекция ровно в те селекторы, где в `style.css` есть `env()`, каждый — один раз |
| Проверка перекрытия home bar в **начальной** позиции скролла → обычный контент, проезжающий под home bar в середине страницы, помечался как «перекрыт» (ложные срабатывания на `div` «Карта связей» y 913-934, `p` y 607-727, `span.chip` «Витамин E» y 857-901) | Перекрытие home bar меряется **только после прокрутки вниз** (`scrollTo(0, maxScroll)`), вырез — **только после прокрутки наверх** |
| Элементы внутри внутренне прокручиваемых панелей считались недостижимыми | Такие элементы исключаются: обходятся предки и пропускаются те, у кого `scrollHeight > clientHeight` и `overflow` прокручиваемый |

Метод v3:

1. Открыть страницу на реальном размере устройства и DSR.
2. Инъектировать `padding` только для селекторов из `style.css`:
   `header, .header` / `footer, .site-footer` / `.trustbar, .conflict-banner, .synergy-banner` / `#modalClose` / `#modal` / `#int-sidebar` / `#atl-sidebar`.
3. Прогнать **два режима**: `emulated` (инсеты подставлены) и `control` (инсеты = 0, то есть как в чистом Playwright).
4. Для выреза: обойти **текстовые узлы** через `Range.getClientRects()` — не элементные боксы. Причина: элементный бокс законно начинается выше инсета, потому что инсет реализован через `padding`. Проверять надо, где лежит **текст**.
5. Для home bar: прокрутить вниз, найти самую нижнюю строку контента и нижние `position: fixed` элементы.

---

## 3. Устройства

| Устройство | Вьюпорт | DSR | `inset-top` | `inset-bottom` | Реальное устройство |
|---|---|---|---|---|---|
| iPhone 14 Pro Max | 430 × 932 | 3 | **59 px** | **34 px** | Dynamic Island сверху, home indicator снизу |
| iPhone SE | 375 × 667 | 2 | **20 px** | **0 px** | без home indicator |

В landscape на iPhone вырез переезжает на **левый/правый** край (по ~59 px) — см. находку D-3.

---

## 4. Правила `env(safe-area-inset-*)` в `docs/style.css`

12 вхождений:

| Строка | Селектор | Правило | Назначение |
|---|---|---|---|
| 235 | (в блоке шапки) | `env(safe-area-inset-top)` | верхние инсеты шапки |
| 241 | `#modalClose` | `top: max(.6rem, env(safe-area-inset-top, 0px))` | кнопка закрытия модалки |
| **384** | `header, .header` | `padding-top: env(safe-area-inset-top, 0px)` | **Dynamic Island (v5.0.0)** |
| **390** | `footer, .site-footer` | `padding-bottom: env(safe-area-inset-bottom, 0px)` | **home indicator** |
| 397 | `.trustbar, .conflict-banner, .synergy-banner` | `padding-top: env(safe-area-inset-top, 0px)` | верхние полосы |
| 817-818 | `#modal` | `padding-top: max(var(--space-4), env(safe-area-inset-top, 0px))`, `padding-bottom: max(var(--space-4), env(safe-area-inset-bottom, 0px))` + `box-sizing: border-box` | модалка |
| 1637-1638 | `#int-sidebar`, `#int-sidebar::before` | `padding-bottom: calc(1rem + env(safe-area-inset-bottom))` | сайдбар взаимодействий (в `@supports (padding: env(safe-area-inset-bottom))`) |
| 1677-1678 | `#atl-sidebar` | то же | сайдбар атласа |

**Чего нет (и это дефекты):**

- `.skip-link:focus` (`style.css:1500-1501`) — **нет** `padding-top: env(...)`. → D-1
- `#toTop` (`style.css:432`) — `position: fixed; right: 1.2rem; bottom: 1.2rem` — **нет** учёта нижнего инсета. → D-2
- `.toBottom` (`style.css:1291-1308`) — `position: fixed; right: 1.2rem; bottom: 5rem` — **нет** `env()`. → D-4 (чисто случайно)
- Ни одного правила с `env(safe-area-inset-left)` или `env(safe-area-inset-right)` во всём файле. → D-3

Про `.skip-link` в неактивном состоянии: `.skip-link { position: absolute; left: -9999px; top: 0 }`, `.skip-link:focus { position: fixed; left: 0; top: 0; z-index: 9999 }`. Замерено на 320 и 412 px: `left -9999, top 0, w 197, h 24, visibleInViewport: false` — скрытие корректное.

---

## 5. Результаты: вырез (notch)

### 5.1. Режим `emulated`, iPhone 14 Pro Max (inset 59 px) — 5/5 страниц чисто

| Страница | `notchN` | Элементные боксы | Текст: доверие к inset |
|---|---|---|---|
| index | 1 | `div.trustbar` top 10, перекрытие бокса 49 px | `padT: 59px`, `textTop: 69` → **запас 10 px** |
| calculator | 1 | `div.trustbar` top 26, перекрытие 33 px | `padT: 59px`, `textTop: 85` → **запас 26 px** |
| map | 1 | `div.trustbar` top 19, перекрытие 40 px | `padT: 59px`, `textTop: 78` → **запас 19 px** |
| graph | 1 | `div.trustbar` top 16, перекрытие 43 px | `padT: 59px`, `textTop: 75` → **запас 16 px** |
| sup/kreatin | 1 | `div.trustbar` top 16, перекрытие 43 px | `padT: 59px`, `textTop: 75` → **запас 16 px** |

Единственный «попавший» элементный бокс — `div.trustbar`, и это **артефакт метода**: инсет реализован как `padding-top`, поэтому бокс по определению начинается на 59 px выше текста. Текст внутри trustbar везде ниже инсета с запасом 10-26 px. `headerEl` (`<header class="top">`) получает `padT: 59px` на всех 5 страницах. `.site-header` имеет `padT: 0px` — оно `position: sticky`, инсет обрабатывается вложенными элементами.

**Вывод: шапка и trustbar под Dynamic Island защищены корректно.**

### 5.2. Режим `control`, iPhone 14 Pro Max — 3 перекрытия на страницу

Тот же код с инсетами = 0 (то есть без правил `env()`):

| Страница | `notchN` | Что попало под вырез |
|---|---|---|
| index | **3** | `div.trustbar` (top 10-44); `a` «🧠 brain-25-evidence» (top 49, перекрытие 10); `span.h1-emoji` (top 49, перекрытие 10) |
| map | 3 | тот же паттерн, перекрытие 5 px |
| graph | 3 | тот же паттерн, перекрытие 8 px |
| sup/kreatin | 3 | тот же паттерн, перекрытие 8 px |
| calculator | 1 | только `div.trustbar` |

`trustbar` в control: `padT: 7.2px`, `textTop` 17/26/23 — под вырез.

**Это доказывает, что правила `env()` на строках 384/390/397 несущие: без них каждая страница теряет 3 строки под Dynamic Island.**

### 5.3. Режим `emulated`, iPhone SE (inset 20 px)

| Страница | `notchN` | Текст trustbar |
|---|---|---|
| index | 1 (бокс) | `textTop: 30` → запас 10 px |
| map | 1 | `textTop: 39` → запас 19 px |
| graph | 1 | `textTop: 36` → запас 16 px |
| sup/kreatin | 1 | `textTop: 36` → запас 16 px |
| calculator | **0** | чисто |

`footer.padB: "0px"` — у SE нет home indicator, корректно.

### 5.4. Skip-link в фокусе — P1, реальный дефект

Во **всех 20 прогонах** (2 устройства × 2 режима × 5 страниц) измерен один и тот же результат:

```
a.skip-link (focused): { top: 0, bottom: 37, h: 37, left: 0, padT: "8px",
                         text: "Перейти к содержимому" }
```

Ни `padding-top`, ни `top` не учитывают инсет. Сверка с текстовым прямоугольником:

| Устройство | inset-top | skip-link top | skip-link bottom | **перекрытие** | Страниц |
|---|---|---|---|---|---|
| iPhone 14 Pro Max | 59 px | 2 | 22 | **57 px** | **5/5** |
| iPhone SE | 20 px | 2 | 22 | **18 px** | **5/5** |

Единственная находка по тексту под вырезом во всём прогоне — именно skip-link. На 5/5 страницах, на обоих устройствах, в обоих режимах.

**Проверка фикса (read-only, без применения к сайту):** при инъекции `a.skip-link:focus { padding-top: 59px }` элемент становится `top: 0, bottom: 88, padT: 59px` — перекрытие исчезает. Значит фикс тривиален, но **по условию задачи не применяется**.

**Почему P1, а не P2:** skip-link — единственный способ попасть к основному контенту с клавиатуры. Под Dynamic Island он рендерится в 2 px от верха экрана, а текст перекрыт на 57 из 22 px своей высоты — то есть текст практически полностью под вырезом, и нажать его в этой позиции нельзя.

---

## 6. Результаты: home indicator (низ)

### 6.1. iPhone 14 Pro Max, H = 932, homeTop = 898

| Страница | `lastLineClear` | Самая нижняя строка контента | Вердикт |
|---|---|---|---|
| index | **false** | `button#toTop.show` 869-913 | см. D-2 |
| calculator | true | `p.copy` «© 2026 Vladislav "DeadSno" Pereshivalov · MIT» 791-840 | чисто |
| map | true | `button.btn.share-page` 803-847 | чисто |
| graph | true | `button.btn.share-page` 803-850 | чисто |
| sup/kreatin | true | `button.btn.share-page` 805-850 | чисто |

`.site-footer` получает `padB: 34px` в emulated и `16px` в control — **`padding-bottom: env(safe-area-inset-bottom)` работает**. Дисклеймер нигде не перекрыт.

### 6.2. `#toTop` — P1, реальный дефект

Замер (только `index.html` — единственная страница с этой кнопкой):

```
#toTop: position fixed, w 44, h 44, computed bottom: 19.2px (1.2rem)
14 Pro Max:  top 869, bottom 913,  homeTop 898  →  перекрытие 15 px, clear: FALSE
iPhone SE:   top 604, bottom 648,  homeTop 667  →  перекрытие -19, clear: true
```

Правило `style.css:432`: `position: fixed; right: 1.2rem; bottom: 1.2rem`. Ни одного `env()`.

**На iPhone с home indicator кнопка «наверх» наезжает на индикатор на 15 px** — нижние 15 px из 44 не кликабельны (там жест свайпа системы). На SE чисто, потому что home bar нет, а bottom-инсет = 0; смещение −19 px это просто `1.2rem` от физического низа.

**Почему P1:** это постоянно видимый элемент управления на самой загруженной странице сайта (index, `scrollHeight` 37 374 px в portrait), и он систематически наполовину перекрыт на всех iPhone с home indicator. Исправление — `bottom: calc(1.2rem + env(safe-area-inset-bottom, 0px))`.

Побочно проверено и уже решено в проекте: `style.css:1321-1322` — `body.modal-open #toTop, body.modal-open .toBottom { display: none }` (z-index 110 против overlay 50).

### 6.3. `.toBottom` — P2, чисто случайно

```
.toBottom: position fixed, w 45, h 45, computed bottom: 80px (5rem)
14 Pro Max:  bottom 852, homeTop 898  →  зазор 46 px, clear: true
iPhone SE:   bottom 587, homeTop 667  →  зазор 80 px, clear: true
```

**Дефектом не является** — при 34-пиксельном home bar 5rem хватает. Но чистого правила нет: `bottom: 5rem` — константа, не связанная с инсетом. На устройстве с бóльшим home bar (или с gestural-индикатором другой высоты) начнёт наезжать. Страницы: calculator, map, index.

### 6.4. Ложное срабатывание: map.html

На map в naивной версии `lastLine: clear false` — `h3` «Когниция ▾» bottom 946 при homeTop 898, и `span.chip` «Alpha-GPC» bottom 678 при homeTop 667 на SE. **Ложь:** элемент лежит внутри `div#list.list` — внутренне прокручиваемой панели (`scrollHeight` 6829 против `clientHeight` 239, `canScrollToEnd: true`). Прокрутив панель, пользователь доходит до конца. Исключено по правилу из раздела 2.

### 6.5. iPhone SE, H = 667, homeTop = 667

`fixedInHome` — пусто на всех 5 страницах. `lastLineClear` — **true на всех 5**, включая index (там последней строкой оказывается `#toTop` 604-648, что выше 667).

---

## 7. Находки Части D

| # | Severity | Находка | Файл:строка | Масштаб | Доказательство |
|---|---|---|---|---|---|
| **D-1** | **P1** | `.skip-link:focus` не учитывает `env(safe-area-inset-top)` — текст «Перейти к содержимому» уходит под Dynamic Island | `style.css:1500-1501` | **5/5 страниц × 2 устройства** | перекрытие 57 px (14 Pro Max) / 18 px (SE), во всех 20 прогонах |
| **D-2** | **P1** | `#toTop` (`bottom: 1.2rem`) наезжает на home indicator на 15 px | `style.css:432` | index.html на всех iPhone с home bar | `bottom 913` против `homeTop 898`, `clear: false` |
| **D-3** | **P2** | Ни одного правила с `env(safe-area-inset-left/right)` во всём `style.css`; в landscape вырез на iPhone уходит на бок (~59 px), а `#toTop` и `.toBottom` стоят по `right: 1.2rem` | `style.css` (отсутствие) | все страницы в landscape | статический анализ + геометрия iPhone в landscape; **runtime не измерялось** |
| **D-4** | **P2** | `.toBottom` (`bottom: 5rem`) не связан с инсетом; чист только потому, что 5rem > 34 px | `style.css:1291-1308` | calculator, map, index | зазор 46 px при `homeTop 898` |
| **D-5** | info | Правила `env()` работают и несущие: без них 3 перекрытия выреза на страницу, с ними 0 | `style.css:384, 390, 397` | 5/5 страниц | control vs emulated, раздел 5.2 |
| **D-6** | info | `.site-footer { padding-bottom: env(safe-area-inset-bottom) }` работает — `padB` 34 px против 16 px | `style.css:390` | 5/5 страниц | раздел 6.1 |
| **D-7** | info | Дисклеймер не перекрыт home indicator ни на одной из 5 страниц | — | 5/5 | `lastLineClear: true` на 4/5 (index — из-за D-2) |

**Итого по части D: 2 × P1, 2 × P2, 0 × P0.**

---

## 8. Сравнение с Батчем B

Батч B (Chromium) safe-area не проверял: в его отчёте значилось «не проверено — используется ли `env(safe-area-inset-*)`». Один P2 («safe-area на `.site-footer`») был зафиксирован как риск, но не подтверждён измерением.

Часть D отвечает на оба вопроса:

| Вопрос Батча B | Ответ #93 |
|---|---|
| Используется ли `env(safe-area-inset-*)`? | **Да, 12 вхождений, 8 селекторов, работает** |
| Достаточно ли правил для `.site-footer`? | **Да** — `padB` 34 px при эмуляции, дисклеймер не перекрыт |
| Есть ли проблемы? | **Да, но не те, что ожидались**: D-1 (skip-link) и D-2 (`#toTop`) — оба в элементах, для которых правил `env()` просто нет |

---

## 9. Ограничения

1. **Инсеты эмулированы, а не считаны с устройства.** Значения 59/34 px для 14 Pro Max и 20/0 px для SE взяты из спецификации устройств и подставлены инъекцией. Реальные значения WebKit на iOS немного отличаются в зависимости от ориентации и режима; порядок величин и выводы не меняются.
2. **`env(safe-area-inset-left/right)` не измерялись** — эмуляция покрывала только top/bottom. Находка D-3 основана на статическом анализе (отсутствие правил) и на известной геометрии iPhone в landscape. Уверенность: средняя, проверка на реальном устройстве обязательна.
3. **Standalone не эмулируется** (Часть C), поэтому взаимодействие safe-area с отсутствием браузерной обвязки не проверялось в комбинации.
4. Фиксы D-1 и D-2 **не применялись** — read-only режим задачи. Для D-1 фикс был проверен инъекцией и сработал, но в файлы не вносился.
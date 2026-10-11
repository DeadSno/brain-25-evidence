# #93 — Часть C: PWA standalone

**Дата:** 2026-10-08
**Ветка:** `v5.6-dev` (HEAD `a645153`)
**Браузер:** Playwright WebKit 26.6 (revision 2359), Playwright 1.63.0 (Python, `.venv`)
**Сервер:** `http://localhost:8000`
**Скрипт:** `scripts/_tmp_93_c.py` → `reports/_tmp_93_c.json`, `reports/_tmp_93_c_look.txt`
**Скриншоты:** `reports/_tmp_93_pwa_{index,calculator,map,graph,sup_kreatin}.png` (412×915)
**Режим:** read-only, правок нет.

---

## 0. Итог одной строкой

**Manifest валиден, 4/4 иконки доступны, `display: standalone` объявлен, `viewport-fit=cover` есть на 5/5 (и на всех 144 HTML файлах сайта). Настоящий standalone-режим проверить не удалось — Playwright не умеет его эмулировать.** Части C: **PASS с оговоркой по методу**.

---

## 1. Manifest

| Проверка | Результат |
|---|---|
| URL | `http://localhost:8000/manifest.webmanifest` |
| HTTP-статус | **200** |
| Content-Type | **`application/manifest+json`** |
| Валидный JSON | **да** |

Содержимое (все обязательные поля присутствуют):

| Поле | Значение | Оценка |
|---|---|---|
| `name` | «БАДы: доказательства и механизмы» | OK |
| `short_name` | «БАДы» | OK, 4 символа — влезает под иконку |
| `description` | «Открытые данные: что работает, что нет. Верид, грейды, механизмы, взаимодействия.» | OK |
| `start_url` | `./index.html` | OK |
| `scope` | `./` | OK |
| `display` | **`standalone`** | OK — ключевое требование |
| `orientation` | `portrait-primary` | OK, но см. замечание ниже |
| `lang` | `ru` | OK |
| `dir` | `ltr` | OK (для кириллицы ltr корректно) |
| `background_color` | `#1c1c1e` | OK, совпадает с фактической заливкой |
| `theme_color` | `#1c1c1e` | OK |
| `categories` | `["health", "medical", "education"]` | OK |
| `icons` | 4 записи | OK — см. раздел 2 |

**Замечание P3:** `orientation: "portrait-primary"` запрещает landscape. При этом сам сайт в landscape работает без находок (Часть E), и на iOS это ограничение игнорируется при `display: standalone` для установленных PWA. Не блокер, но ограничение декларировано впустую.

---

## 2. Иконки

| Файл | HTTP | Content-Type | Размер, байт | `purpose` |
|---|---|---|---|---|
| `icons/192.png` | **200** | `image/png` | 26 464 | `any` |
| `icons/512.png` | **200** | `image/png` | 128 831 | `any` |
| `icons/maskable-192.png` | **200** | `image/png` | 18 844 | `maskable` |
| `icons/maskable-512.png` | **200** | `image/png` | 103 573 | `maskable` |

**4/4 доступны.** Обязательные размеры для установки — 192 и 512 — присутствуют. Наличие maskable-вариантов отдельное достоинство: без них Android обрезает иконку по кругу.

---

## 3. Service worker

| Проверка | Результат |
|---|---|
| `http://localhost:8000/sw.js` | **200**, `text/javascript` |

Регистрация SW в HTML не проверялась в этой части (вне заявленного объёма).

---

## 4. Ключевые страницы в контексте standalone

5 страниц: `index.html`, `calculator.html`, `map.html`, `graph.html`, `sup/kreatin.html`. Вьюпорт 412×915, DSR 3.

| Метрика | index | calculator | map | graph | sup/kreatin |
|---|---|---|---|---|---|
| HTTP 200 | да | да | да | да | да |
| meta viewport | `width=device-width, initial-scale=1, viewport-fit=cover` | то же | то же | то же | то же |
| `viewport-fit=cover` | **true** | **true** | **true** | **true** | **true** |
| Горизонтальный скролл | 0 | 0 | 0 | 0 | 0 |
| `display-mode` | `browser` | `browser` | `browser` | `browser` | `browser` |
| `prefers-color-scheme: dark` | false | false | false | false | false |
| `meta theme-color` | `#f5f5f7` | `#f5f5f7` | `#f5f5f7` | `#f5f5f7` | `#f5f5f7` |
| Фактический фон `body` | `rgb(28,28,30)` | `rgb(28,28,30)` | `rgb(28,28,30)` | `rgb(28,28,30)` | `rgb(28,28,30)` |
| Футер | static | static | static | static | static |
| Высота футера, px | 531 | 504 | 506 | 509 | 506 |
| `padding` футера | `24px` / `16px` | то же | то же | то же | то же |

### `viewport-fit=cover` на всём сайте

Проверено грепом по всем HTML: **`viewport-fit=cover` присутствует в 144 из 144 файлов** (13 корневых + 131 sup). Исключений нет. Это ключевое условие, чтобы `env(safe-area-inset-*)` вообще имели значение — выполнено.

### Прокрутка в standalone

Аналог «нет браузерной обвязки» — проверка, что контент не уезжает под системный UI: горизонтальный скролл 0 на всех 5, вертикальный в пределах документа, футер `position: static` (не прибит к низу и не перекрыт). Отдельная проверка нижних инсетов — Часть D.

---

## 5. Ограничение: standalone не эмулируется

**`window.matchMedia('(display-mode: standalone)').matches` возвращает `false` на всех 5 страницах; `window.matchMedia('(display-mode: browser)').matches` — `true`.**

Причина инструментальная: Playwright запускает WebKit как обычный браузерный контекст и не устанавливает PWA на домашний экран. Режим standalone задаётся на уровне iOS, а не веб-контента, и через CDP/Playwright протокол не включается. Это **не дефект сайта**.

Что сделано вместо прямой проверки — косвенные признаки, все измерены:

| Косвенный признак | Результат |
|---|---|
| `display: "standalone"` в манифесте | ✅ объявлено |
| `viewport-fit=cover` в meta viewport | ✅ 144/144 страниц |
| Правила `env(safe-area-inset-*)` в `style.css` | ✅ 12 вхождений на строках 235, 241, 384, 390, 397, 817, 818, 1637, 1638, 1677, 1678 |
| Горизонтальный скролл = 0 | ✅ 5/5 |
| Футер не перекрыт снизу | ✅ 5/5 (проверено в Части D) |

**Честный вердикт:** структурно PWA готов к standalone; фактический запуск в standalone на реальном iPhone не проверялся и в этом прогоне провере быть не мог.

---

## 6. Замечание P3: `theme-color`

На всех 13 проверенных страницах **два** тега `theme-color`:

```html
<meta name="theme-color" content="#f5f5f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1c1c1e" media="(prefers-color-scheme: dark)">
```

Проблема: сайт **тёмный по умолчанию независимо от системной темы**. Замерено: `matchMedia('(prefers-color-scheme: dark)').matches` = `false`, `html.className` = `""`, при этом `body` background = `rgb(28,28,30)`. То есть на устройстве со светлой темой ОС подложка первой отрисовки будет `#f5f5f7`, а контент отрисуется тёмным. В standalone это заметно как вспышка при запуске.

`theme_color` в манифесте при этом `= #1c1c1e` — то есть манифест и фактическая отрисовка согласованы, расходится именно light-мета. **P3**, не блокер.

---

## 7. Находки Части C

| # | Severity | Находка | Детали |
|---|---|---|---|
| C-1 | **P3** | `meta theme-color` для light-схемы `#f5f5f7` не совпадает с фактической заливкой `#1c1c1e` — вспышка при запуске в standalone на устройстве со светлой темой ОС | 144 страницы |
| C-2 | **P3** | `orientation: "portrait-primary"` в манифесте при том, что landscape полностью работоспособен (Часть E) | манифест |
| C-3 | info | Standalone-режим проверен только косвенно — Playwright не эмулирует `display-mode: standalone` | ограничение метода |
| C-4 | info | Регистрация service worker в HTML не проверялась (вне объёма части C); сам `sw.js` отдаётся 200 | — |

**P0: 0. P1: 0. P2: 0.**

---

## 8. Сравнение с Батчем B

Батч B (Chromium) PWA не проверял — в его отчёте safe-area значился в разделе «не проверено». Часть C закрывает этот пробел по манифесту, иконкам, viewport-fit и safe-area-правилам. Единственное, что осталось непроверенным, — фактический запуск из домашнего экрана на реальном iOS-устройстве; это принципиально недостижимо для headless-прогона.
---
name: mobile-deep-audit
description: Глубокий аудит мобильной адаптации на 10 разрешениях + iPhone 17 + Android 15. Только чтение и один отчёт.
license: MIT
version: v1.1
updated: 2026-10-01
project: brain-25-evidence
---

# Mobile Deep Audit

Триггер: "mobile audit", "аудит мобильной версии", "мобильная адаптация", "проверь на iPhone".


## Правило верификации находок

Прежде чем фиксить находку — воспроизведи её:
- mobile: реальный viewport в Playwright
- touch: getBoundingClientRect() с реальным кликом
- тест: мутация (сломать → тест падает)
- JS: node --check + реальный прогон
- данные: запрос к файлу, не к памяти

Если не можешь воспроизвести — находка не подтверждена,
в отчёт идёт со статусом «требует верификации».

Не «починил бы» и не «добавил бы clearRect на всякий случай» — сначала
воспроизвёл. В QA-аудите этого проекта **5 находок из 42** оказались ложными,
и все пять я бы выдала как критичные: `cv.width = ...` уже чистит canvas,
`Рёбер` не есть мозгибаки, `lib/` жив и нужен генератору отчёта.



## Лимит находок
Ориентир — 60 в отчёте. При превышении:
- группировать однотипные (130 звёзд = 1 находка, не 130)
- P0/P1 — не резать никогда
- P2 — сжимать до паттернов
Число в отчёте — что нашлось, а не что влезло.
## Специфика проекта brain-25-evidence

**Структура (актуально на 2026-09-30):**
- 12 основных HTML: index, map, interactions, graph, atlas, calculator, trends, methodology, faq, glossary, feedback, support
- 5 sup-страниц: kreatin, omega-3, vitamin-d, magniy, paba
- 1 CSS: style.css (v=391)
- 6 JS: script.js, science2.js, tracker.js, version.js, pwa.js, sw.js
- 1 PWA: manifest.webmanifest, sw.js (v51), pwa.js
- API: docs/api/v1/index.json + supplements.json
- Тесты: 727 (pytest -q)

**Структура данных:**
- docs/data.json — 130 карточек (источник правды)
- docs/data_index.json — лёгкая проекция
- docs/effect_tags.json — 18 нормализованных тегов
- data/db/brain.duckdb — аналитическая БД

**Правила проекта:**
- На каждой странице в .actions НЕТ ссылки на себя
- Единый набор кнопок на 11 основных страницах
- Футеры байт-идентичны
- Тема через html.dark + body.dark
- Тесты перед коммитом обязательны
- Файлы >30 строк — только через Python (PowerShell heredoc ломает backticks)

**Что НЕ трогать:**
- data.json вручную
- effect_tags.json вручную
- sw.js без причины
- sup/*.html при работе в других ветках

**Связанные документы:**
- docs/dev/AI_CONTEXT.md — контекст для AI
- docs/dev/ROADMAP_NEW.md — план развития
- reports/PRODUCT_AUDIT.md — свежий аудит
- reports/AUDIT_REPORT.md — аудит 2026-09-30

## Жёсткие правила

1. НИЧЕГО НЕ УДАЛЯЙ И НЕ МЕНЯЙ в проекте
2. Единственный создаваемый файл — reports/MOBILE_AUDIT.md
3. Только чтение
4. Все находки: файл:строка + цифры + фикс + приоритет
5. Лимит находок — см. раздел «Лимит находок»
6. Время обхода: 20-30 мин

## Устройства для проверки

| # | Ширина | Устройство | ОС | Приоритет |
|---|:------:|-----------|-----|:---------:|
| 1 | 320 | iPhone SE (старый) | iOS | минимум |
| 2 | 360 | Samsung A, Xiaomi, Realme | Android | **самый частый** |
| 3 | 375 | iPhone SE 2/3 | iOS | высокий |
| 4 | 390 | iPhone 12-14 | iOS | высокий |
| 5 | 393 | iPhone 15/16/17 | iOS | высокий |
| 6 | 412 | **Tecno CAMON 40, Pixel** | Android | **пользователь** |
| 7 | 430 | iPhone 15/16/17 Pro Max | iOS | высокий |
| 8 | 768 | iPad mini | iOS | средний |
| 9 | 1024 | iPad Pro | iOS | низкий |
| 10 | 1280+ | Desktop | — | контроль |

## Обход (17 страниц)

**12 основных:** index, map, interactions, graph, atlas, calculator, trends, methodology, faq, glossary, feedback, support
**5 sup:** kreatin, omega-3, vitamin-d, magniy, paba

## Что проверять на каждом разрешении

### Горизонтальный скролл
- `document.documentElement.scrollWidth === clientWidth`
- Все блоки, таблицы, модалки не выходят за viewport
- Длинные слова (`word-break`)

### Touch targets (WCAG 2.5.5)
- Все `.btn`, `<a>`, `<button>` ≥ 44×44px
- Отступы между тапами ≥ 8px
- Чекбоксы/радио ≥ 24px (Apple HIG)

### Шрифты
- **Input, select, textarea ≥ 16px** (иначе iOS зумит при фокусе!)
- Body ≥ 14px
- H1 адаптивно (не вылазит за экран)

### Модалки и попапы
- Помещаются в 100vh (не обрезаются)
- Кнопки закрытия ≥ 44px
- Фон не прокручивается при открытой модалке (body overflow hidden)

### Таблицы
- Либо адаптируются в cards
- Либо horizontal scroll внутри контейнера (не вся страница)

### Изображения
- `max-width: 100%` + `height: auto`
- aspect-ratio сохранён
- Не рвут layout

### Safe-area (iPhone 17 Dynamic Island + home bar)
- Есть `viewport-fit=cover` в meta viewport
- Есть `env(safe-area-inset-top/bottom/left/right)`
- Контент не заходит под Dynamic Island
- Кнопки не заезжают под home bar

## Android-специфика (Tecno, Samsung, Xiaomi)

- `-webkit-tap-highlight-color: transparent` — убрать серую подсветку при тапе
- `touch-action: manipulation` — убрать 300ms задержку
- `theme-color` meta — окрашивает status bar
- Fonts системные (Roboto / One UI) — не сломать кириллицу

## iOS-специфика

- `viewport-fit=cover` — обязательно для safe-area
- `-webkit-text-size-adjust: 100%` — не зумить landscape
- `-webkit-overflow-scrolling: touch` — плавный скролл (legacy, но не помешает)
- Standalone PWA: при `display: standalone` safe-area критична

## PWA в standalone режиме

Если пользователь установил как приложение:
- `display: standalone` работает
- Safe-area не обрезает контент
- Нет UI браузера (адресная строка)
- Тема (тёмная/светлая) применяется
- Splash screen (если настроен)

## Что НЕ проверять

- Цвета бренда (отдельная задача)
- Вкусовые предпочтения
- Desktop-поведение
- Скорость сети (отдельная задача)

## Формат отчёта reports/MOBILE_AUDIT.md

Структура:

    # MOBILE AUDIT — brain-25-evidence
    Дата: YYYY-MM-DD
    
    ## Сводка
    - Проверено: 17 страниц × 10 разрешений = 170 комбинаций
    - Найдено: N проблем
    - Критичных: X (ломает UX)
    - Важных: Y
    - Желательных: Z
    
    ## РАЗРЕШЕНИЕ 320px (iPhone SE)
    - [файл:строка] проблема → фикс
    
    ## РАЗРЕШЕНИЕ 360px (Samsung, Xiaomi)
    ...
    
    ## РАЗРЕШЕНИЕ 412px (Tecno CAMON 40)
    ...
    
    ## ИТОГИ
    ### КРИТИЧНОЕ
    ### ВАЖНОЕ
    ### ЖЕЛАТЕЛЬНОЕ

## Формат находки — ОБЯЗАТЕЛЬНО

Каждая находка:
- файл:строка
- при каком разрешении проблема
- что не так (с цифрами)
- как исправить

ПРИМЕРЫ ПРАВИЛЬНЫХ НАХОДОК:

"style.css:8 — .btn на 360px: height 41px. WCAG 2.5.5 требует 44px. Фикс: padding .7rem 1.1rem, min-height 44px."

"index.html:196 — input#search font-size 14px. На iOS при фокусе зум до 16px → horizontal scroll. Фикс: font-size:16px."

"docs/sup/kreatin.html:47 — .sup-header на 375px: h1 + badge переносятся некорректно, badge уходит под h1. Фикс: flex-wrap с gap .5rem."

ПРИМЕРЫ ПЛОХИХ (не включать):
- "кнопка маленькая" (без цифр)
- "неудобно" (субъективно)
- "некрасиво"

## Проверка чек-лист

После отчёта:
- [ ] Сводка в начале
- [ ] Разделы по разрешениям (10 штук)
- [ ] КРИТИЧНОЕ / ВАЖНОЕ / ЖЕЛАТЕЛЬНОЕ
- [ ] У каждой находки: разрешение + файл:строка + цифры + фикс
- [ ] Однотипные находки сгруппированы, а не перечислены поштучно
- [ ] Есть PWA standalone проверка
- [ ] Есть iPhone 17 и Tecno CAMON 40 отдельно
- [ ] Есть Android-специфика

Если чего-то не хватает — исправь отчёт до сдачи.

## Итоговая рекомендация

В конце отчёта — раздел "Что критично исправить":
- ТОП-5 проблем (по приоритету)
- Порядок фиксов
- Оценка времени

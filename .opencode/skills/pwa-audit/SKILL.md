---
name: pwa-audit
description: Проверяет состояние PWA (Progressive Web App) на сайте brain-25-evidence.
license: MIT
version: v1.1
updated: 2026-10-01
project: brain-25-evidence
---

# Проверка PWA

Триггер: "проверь PWA", "работает ли PWA", "статус PWA".


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

## Что проверять

### 1. Обязательные файлы
- `docs/manifest.webmanifest` — существует, валидный JSON
- `docs/sw.js` — Service Worker, зарегистрирован
- `docs/pwa.js` — регистрация SW в клиенте
- `docs/icons/192.png` и `docs/icons/512.png` — иконки

### 2. Манифест
- Поля: name, short_name, start_url, display, icons
- `display` = standalone или fullscreen
- 2+ иконки (192, 512)

### 3. Service Worker
- Кэширует статику (HTML, CSS, JS, JSON)
- Есть стратегия fetch (cache-first или network-first)
- Версия кэша (например, CACHE_NAME = 'v1')

### 4. Подключение
- Все HTML страницы в docs/ содержат `<link rel="manifest" href="manifest.webmanifest">`
- Все HTML содержат `<script src="pwa.js">` (или регистрацию в общем JS)
- Есть meta theme-color

### 5. Проверка через CLI
- `npx pwa-asset-generator --help` — установлен ли (опционально)
- Проверить что sw.js регистрируется через `navigator.serviceWorker.register`

## Формат отчёта

| Проверка | Статус | Детали |
|----------|--------|--------|
| manifest.webmanifest | OK / FAIL | поля |
| sw.js | OK / FAIL | что кэширует |
| pwa.js | OK / FAIL | регистрация |
| Icons | OK / FAIL | размеры |
| HTML подключение | OK / FAIL | сколько страниц |

## Если PWA не готов
Вывести список что нужно доделать с приоритетами.
---
name: data-validation
description: Проверяет целостность и консистентность данных в проекте brain-25-evidence.
license: MIT
version: v1.0
updated: 2026-09-30
project: brain-25-evidence
---

# Проверка данных

Триггер: "проверь данные", "проверь data.json", "валидация данных".


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
- 1 CSS: style.css (v=383)
- 3 JS: script.js, science2.js, tracker.js, version.js
- 1 PWA: manifest.webmanifest, sw.js (v42), pwa.js
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

### 1. Структура `docs/data.json`
- Каждая карточка имеет обязательные поля: `id`, `category`, `grade`, `verdict`, `code`
- `grade` из множества {A, B, C, D}
- `verdict` из {работает, зависит от контекста, не подтверждено}
- `code` из {-1, 0, 1}
- `effects` — список 1-3 строк
- `mechs` — список 2-4 элементов, каждый из 3 частей
- `interactions` — каждая имеет поле `with`
- `key_sources` — 1-3 источника, каждый с pmid, year, journal

### 2. Синхронизация с API
- `docs/api/v1/supplements.json` содержит столько же карточек
- `docs/api/v1/index.json` содержит корректный `count`
- Сумма `grades` в index.json == количеству в supplements.json

### 3. Синхронизация с effect_tags
- Все id из `docs/effect_tags.json` есть в `data.json`
- Все id из `data.json` есть в `effect_tags.json` (или обосновано отсутствие)

### 4. Синхронизация с DuckDB (если есть `data/db/brain.duckdb`)
- Количество в таблице `supplement` == count в API
- Все id в API есть в БД

### 5. Аномалии
- `scienceIndex` == 0 (должно быть > 0)
- `metaCount` отрицательный
- Дубли `id` в data.json
- Карточки с пустым `about`

## Формат вывода

Таблица: | Проверка | Статус | Детали |
Если всё ок: "Все проверки пройдены"
Если ошибки: список с указанием id карточки
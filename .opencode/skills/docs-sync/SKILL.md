---
name: docs-sync
description: Проверяет синхронизацию документации и артефактов в docs/.
license: MIT
version: v1.0
updated: 2026-09-30
project: brain-25-evidence
---

# Проверка документации

Триггер: "проверь документацию", "docs sync".

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
воспроизвёл. В QA-аудите этого проекта из 42 находок **5 оказались ложными**,
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
- Тесты: 722 (pytest -q)

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

### 1. Битые ссылки
Пройти все .md в `docs/`, найти ссылки вида `[текст](путь)`.
Проверить, что файл по этому пути существует.
Исключение: внешние http/https ссылки.

### 2. Навигация
Проверить, что `README.md` ссылается на все ключевые артефакты:
- docs/srs.md, docs/rtm.md, docs/erd.md, docs/nfr.md
- docs/bpmn_pipeline.md, docs/dmn.md
- docs/api/v1/openapi.yaml
- docs/user_stories.md, docs/adr/README.md

### 3. Устаревшие упоминания
- Версии ниже v3.7
- Числа: 103, 113, 94, 9074, 5135
- Названия старых батчей

### 4. Дубли в docs/
- Файлы с одинаковым содержимым
- Похожие по названию (описание_methodology vs methodology)

### 5. Форматирование
- Файлы с непарными ``` (тройные backticks)
- Файлы с CRLF в .md (должно быть LF для GitHub Pages)

## Формат вывода

| Файл | Проблема | Приоритет |
|------|----------|-----------|
| docs/X.md | битая ссылка на Y.md | высокий |
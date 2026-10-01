---
name: release-check
description: Проверяет готовность проекта к коммиту и push.
license: MIT
version: v1.1
updated: 2026-10-01
project: brain-25-evidence
---

# Проверка перед релизом

Триггер: "готов ли к коммиту", "release check", "перед push".


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

## Чек-лист

### 1. Git-статус
- `git status --short` чист или есть только ожидаемые изменения
- Нет файлов `.env`, `*.key`, `*.secret` в staged
- Нет больших файлов > 10 MB в staged

### 2. Тесты
- Все тесты проходят: `pytest -q`
- Snapshot актуален
- Newman-тесты (если менялся API)

### 3. Данные
- `data.json` валиден
- `api/v1/*.json` синхронизированы
- `effect_tags.json` синхронизирован

### 4. Документация
- Обновлена версия (если нужно)
- CHANGELOG обновлён (если есть)
- README не устарел

### 5. Сообщение коммита
- Латиница (не кириллица)
- Формат: `type(scope): description`
- Type: feat/fix/docs/chore/test/ci/data

## Формат вывода

Пройдены ли все 5 блоков.
Если нет — что именно не готово.
---
name: release-check
description: Проверяет готовность проекта к коммиту и push.
license: MIT
version: v1.0
updated: 2026-09-30
project: brain-25-evidence
---

# Проверка перед релизом

Триггер: "готов ли к коммиту", "release check", "перед push".


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
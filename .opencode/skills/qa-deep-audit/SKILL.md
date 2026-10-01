---
name: qa-deep-audit
description: Аудит QA — покрытие тестами, edge cases, offline/error/empty states. Только чтение.
license: MIT
version: v1.0
updated: 2026-09-30
project: brain-25-evidence
---

# QA Deep Audit

Триггер: "qa audit", "аудит тестирования", "проверь покрытие".


## Специфика проекта brain-25-evidence

**Структура (актуально на 2026-09-30):**
- 12 основных HTML: index, map, interactions, graph, atlas, calculator, trends, methodology, faq, glossary, feedback, support
- 5 sup-страниц: kreatin, omega-3, vitamin-d, magniy, paba
- 1 CSS: style.css (v=383)
- 3 JS: script.js, science2.js, tracker.js, version.js
- 1 PWA: manifest.webmanifest, sw.js (v42), pwa.js
- API: docs/api/v1/index.json + supplements.json
- Тесты: 171 (pytest -q). Метка `network` удалена 2026-10-01: сетевых
  тестов в проекте нет, `-m "not network"` ничего не исключал.
- Браузерные e2e (scripts/e2e_smoke.py, scripts/ui_verify.py) подключены
  к pytest как `tests/test_e2e_smoke.py` и `tests/test_ui_verify.py`,
  метка `e2e`, по умолчанию исключены. Запуск: `pytest -m e2e`

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

1. НИЧЕГО НЕ УДАЛЯЙ
2. Единственный создаваемый файл — reports/QA_AUDIT.md
3. Максимум 40 находок
4. Время: 20-30 мин

## Что проверять

### 1. Покрытие тестами
- Какие модули в scripts/ не покрыты?
- Какие функции имеют публичный интерфейс, но нет тестов?
- Какие frontend-функции не покрыты?
- Есть ли тесты на:
  - analyze_coi.py
  - graph_interactions.py
  - build_api.py
  - content.py
  - src/config.py
  - src/ct_terms.py
  - src/wiki_map.py
  # Планируется, модуля пока нет: parsers.py — общего парсера в репозитории
  # не существует (ни в src/, ни в scripts/). Проверено 2026-10-01. Если он
  # появится — добавить в этот список.

### 2. Edge cases
- Пустой массив данных
- Один элемент
- Null/undefined
- Очень длинные строки
- Очень большие числа
- Спецсимволы (кавычки, угловые скобки)
- Кириллица + латиница в одном поле

### 3. Обработка ошибок fetch
- Проверка .ok
- try/catch
- Таймауты
- Что показывается пользователю

### 4. Офлайн режим (PWA)
- Что работает офлайн?
- Что не работает?
- Понятно ли пользователю?

### 5. Валидация форм
- required поля
- Формат email/URL
- Длина
- Понятные ошибки

### 6. Обработка состояний
- Loading
- Empty
- Error
- Success

### 7. Кроссбраузерность (теоретически)
- Проверка на Chrome
- Firefox
- Safari
- Edge

### 8. Безопасность
- XSS (escape при вставке)
- CSRF (если применимо)
- Sensitive данные

## Формат находки

"scripts/analyze_coi.py — нет тестов. Функция classify_coi() имеет 4 ветки (POSITIVE/NEGATIVE/unclear/missing), ни одна не покрыта. Фикс: tests/test_analyze_coi.py с фикстурами 5 XML-файлов."

"docs/script.js:169 — fetchJson() без .ok проверки. При 404 r.json() бросит исключение, но после парсинга. Фикс: добавить `if (!r.ok) throw new Error(...)` перед .json()."

"docs/feedback.html — нет проверки длины message (minlength только в HTML). Пользователь может обойти через DevTools. Фикс: дублировать валидацию в JS."

## Формат отчёта reports/QA_AUDIT.md

    # QA AUDIT
    Дата: YYYY-MM-DD
    
    ## Сводка
    - Покрытие тестами: X модулей без тестов
    - Edge cases: Y проблем
    - Error handling: Z
    - Всего: N
    
    ## КРИТИЧНОЕ (пользователь потеряет данные)
    ## ВАЖНОЕ (баг в проде)
    ## ЖЕЛАТЕЛЬНОЕ (UX деградация)
    ## Рекомендации

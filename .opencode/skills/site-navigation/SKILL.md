---
name: site-navigation
description: Управляет навигацией сайта. Добавляет и проверяет ссылки на всех HTML страницах.
license: MIT
version: v1.0
updated: 2026-09-30
project: brain-25-evidence
---

# Навигация сайта

Триггер: "добавь ссылку на X во все страницы", "проверь навигацию", "обнови меню".


## Специфика проекта brain-25-evidence

**Структура (актуально на 2026-09-30):**
- 12 основных HTML: index, map, interactions, graph, atlas, calculator, trends, methodology, faq, glossary, feedback, support
- 5 sup-страниц: kreatin, omega-3, vitamin-d, magniy, paba
- 1 CSS: style.css (v=383)
- 3 JS: script.js, science2.js, tracker.js, version.js
- 1 PWA: manifest.webmanifest, sw.js (v42), pwa.js
- API: docs/api/v1/index.json + supplements.json
- Тесты: 143 (pytest -q -m "not network")

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

## Правила

### 1. Целевые страницы (все должны быть в навигации)
- index.html - Главная
- map.html - Карта механизмов
- interactions.html - Взаимодействия
- graph.html - Граф связей
- atlas.html - Атлас
- calculator.html - Калькулятор
- methodology.html - Методология
- faq.html - FAQ
- glossary.html - Глоссарий
- trends.html - Тренды
- feedback.html - Обратная связь

### 2. Структура навигации
Каждая HTML страница в docs/ должна иметь единый блок навигации.
Стандартный вид:

    <header>
      <nav>
        <a href="index.html">Главная</a>
        <a href="map.html">Карта механизмов</a>
        ...
      </nav>
    </header>

### 3. Проверка
- У ВСЕХ страниц одинаковый набор ссылок
- Порядок ссылок идентичен
- Нет битых ссылок (все файлы существуют)
- Нет дублей ссылок

### 4. Как добавлять ссылку
1. Прочитать одну страницу (образец) - определить структуру nav
2. Найти во всех HTML паттерн закрывающего nav
3. Вставить новую ссылку ПЕРЕД закрывающим тегом
4. НЕ дублировать если уже есть
5. Пропустить страницы: feedback.html, graph.html

### 5. Формат отчёта
Таблица: Страница | Есть nav | Ссылок | Статус

## Важно
- НЕ переписывать содержимое страниц
- НЕ менять существующие ссылки
- Только добавлять и проверять

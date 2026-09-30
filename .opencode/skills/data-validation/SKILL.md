---
name: data-validation
description: Проверяет целостность и консистентность данных в проекте brain-25-evidence.
license: MIT
---

# Проверка данных

Триггер: "проверь данные", "проверь data.json", "валидация данных".

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
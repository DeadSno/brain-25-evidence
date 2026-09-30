---
name: pwa-audit
description: Проверяет состояние PWA (Progressive Web App) на сайте brain-25-evidence.
license: MIT
---

# Проверка PWA

Триггер: "проверь PWA", "работает ли PWA", "статус PWA".

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
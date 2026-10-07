# OFFLINE_CACHE.md — cache-first для sup/*.html

## 1. Текущая стратегия sw.js (до изменений)

### STATIC_ASSETS (прекеш при install)
- 13 корневых HTML-страниц: index, calculator, map, interactions, atlas, trends, methodology, faq, glossary, feedback, graph, support, offline
- sup/index.html + 5 страниц: kreatin, magniy, omega-3, paba, vitamin-d
- Статика: manifest.webmanifest, pwa.js, version.js, script.js, style.css, effect_tags.json, effect_labels.json
- Иконки: 192.png, 512.png
- Шрифты: inter-regular/medium/semibold/bold/extrabold.woff2
- share.js?v=1

### Runtime-кэш
- networkFirstForData: data_index.json, data.json (кэшируются при первом запросе)
- cacheFirstForStatic: все остальные запросы (кэшируются при первом запросе)

### Стратегия для HTML
- Все HTML страницы шли через cacheFirstForStatic
- При повторном визите отдавалась копия с момента первого посещения
- Правки страниц не доходили до пользователей, пока они сами не сбрасывали кэш

## 2. Что изменено: было → стало

### Было
- Все sup/*.html (кроме sup/index.html) шли через cacheFirstForStatic
- При повторном визите отдавалась копия с момента первого посещения
- Правки страниц не доходили до пользователей без сброса кэша

### Стало
- sup/*.html (кроме sup/index.html) идут через staleWhileRevalidateForSup
- При первом визите: кэш пуст → запрос в сеть → ответ кэшируется
- При повторном визите: кэш отдаётся сразу (без задержки) → в фоне догружается свежая копия → заменяет кэш
- Правки страниц доходят до пользователей при следующей загрузке

### Что не тронуто
- sup/index.html: остаётся в STATIC_ASSETS, cacheFirstForStatic (каталог — точка входа, офлайн-доступность важнее свежести)
- 5 прекешенных страниц (kreatin, magniy, omega-3, paba, vitamin-d): остаются в STATIC_ASSETS, cacheFirstForStatic (их кэш чистится бампом CACHE_VERSION)

## 3. CACHE_VERSION
- Было: v81
- Стало: v82
- Причина: без бампа существующие пользователи не получат новый sw.js

## 4. Проверка offline (Playwright)

### Шаг 1: online sup/kreatin.html
- status: 200
- SW active: yes
- kreatin in cache: True

### Шаг 2: setOffline(true)
- offline mode: on

### Шаг 3: offline sup/kreatin.html
- status: 200
- url: http://localhost:8000/sup/kreatin.html
- title: Креатин — грейд, доказательства, дозировки | Brain 25 Evidence

### Шаг 4: offline sup/omega-3.html (в прекеше)
- status: 200
- url: http://localhost:8000/sup/omega-3.html
- title: Омега-3 — грейд, доказательства, дозировки | Brain 25 Evidence

### Шаг 5: offline sup/creatine.html (не в прекеше, не посещали)
- status: 200
- url: http://localhost:8000/sup/creatine.html
- title: Нет соединения в Brain 25 Evidence
- is offline page: True (содержимое offline.html)

## 5. Коммит
- Хеш: (будет указан после коммита)

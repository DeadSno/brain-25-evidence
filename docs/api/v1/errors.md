# API Error Contract

> Формальный контракт ошибок REST API Brain 25 Evidence.
> Клиенты должны уметь обрабатывать каждый HTTP-код из этого документа.

## Все возможные коды ответов

| Код | Название | Когда | Body | Действие клиента |
|:---:|----------|-------|------|------------------|
| **200** | OK | Успешный запрос | JSON | Парсить |
| **301** | Moved Permanently | HTTP → HTTPS | HTML | Идти по Location |
| **304** | Not Modified | Conditional GET | — | Использовать cache |
| **403** | Forbidden | Редко: приватные зоны | HTML | Проверить URL |
| **404** | Not Found | Endpoint не существует | HTML | Логировать, fallback на index |
| **500** | Internal Server Error | GitHub Pages лежит | HTML | Retry через 5-10 сек |
| **502** | Bad Gateway | CDN проблема | HTML | Retry через 30 сек |
| **503** | Service Unavailable | Плановое обслуживание | HTML | Retry через 60 сек |

**Кодов 400, 401, 429 нет** — API публичный, без аутентификации и rate limits.

## Формат ответа 200 OK

**Endpoint:** `GET /api/v1/index.json`

```json
{
  "version": "v1",
  "generated_at": "2026-09-26T07:00:00Z",
  "count": 130,
  "license": "CC BY 4.0",
  "stats": {
    "grades": {"A": 8, "B": 45, "C": 52, "D": 25},
    "categories_atomic_count": 59
  },
  "ids": ["Креатин", "Омега-3", "..."]
}
```

**Headers:**
```
Content-Type: application/json; charset=utf-8
Cache-Control: max-age=3600
Content-Encoding: gzip
```

## Формат ответа 404 Not Found

GitHub Pages возвращает стандартный HTML:

```html
<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
  <h1>404</h1>
  <p>File not found</p>
</body>
</html>
```

**Рекомендации клиенту:**
- Не парсить HTML как JSON (упадёт)
- Проверять `Content-Type` перед парсингом
- Логировать URL и response headers для дебага

## Стратегия retry

| Код | Retry? | Backoff | Макс попыток |
|:---:|:------:|---------|:------------:|
| 200 | Нет | — | — |
| 304 | Нет | — | — |
| 404 | Нет | — | — |
| 500 | **Да** | 5s, 15s, 45s | 3 |
| 502 | **Да** | 10s, 30s | 2 |
| 503 | **Да** | 60s | 2 |

**Пример на Python:**

```python
import time
import requests

def fetch_json(url, retries=3):
    for attempt in range(retries):
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (500, 502, 503) and attempt < retries - 1:
            time.sleep(5 * (3 ** attempt))  # 5, 15, 45
            continue
        r.raise_for_status()
    raise RuntimeError(f'Failed after {retries} retries')
```

## Сценарии клиента

| Ситуация | Действие |
|----------|----------|
| 200 + валидный JSON | Работать с данными |
| 200 + пустой body | Ошибка сервера, retry |
| 404 | Проверить URL, fallback на `/api/v1/index.json` |
| 500/502/503 | Retry с backoff |
| Timeout (>10 сек) | Retry 1 раз, потом alert |

## Контрактные гарантии

**Что гарантируем:**
- `Content-Type: application/json` для успешных ответов
- Кодировка UTF-8 без BOM
- Все поля соответствуют OpenAPI-спеке
- `count` в JSON = фактическая длина массива

**Что НЕ гарантируем:**
- Latency (best effort, обычно < 1 сек)
- 100% availability (SLA GitHub Pages ~99.9%)
- Backward compatibility между v1 и v2

## Связанные документы

- [OpenAPI spec](openapi.yaml)
- [Sequence diagrams](sequence.md)
- [NFR, раздел Доступность](../../docs/nfr.md)

## Версия

- v1.0 — 2026-09-26, 8 кодов, 3 примера

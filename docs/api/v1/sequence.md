# API Sequence Diagram — взаимодействие клиента с API

> Sequence-диаграммы основных сценариев работы с REST API.
> Дополняет [OpenAPI spec](openapi.yaml) и [Error Contract](errors.md).

## 1. Успешный запрос — список добавок

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant DNS as DNS
    participant CDN as GitHub Pages CDN
    participant FS as Static Files
    participant Cache as Browser Cache
    C->>DNS: resolve deadsno.github.io
    DNS-->>C: IP address
    C->>Cache: GET /api/v1/supplements.json (cache?)
    alt Cache hit
        Cache-->>C: 200 OK (from cache)
    else Cache miss
        C->>CDN: GET /api/v1/supplements.json
        CDN->>FS: read supplements.json
        FS-->>CDN: 660 KB JSON
        CDN-->>C: 200 OK + Cache-Control: max-age=3600
        C->>Cache: store response
    end
    C->>C: parse JSON (130 items)
    C->>C: render UI
```

## 2. Метаданные — index.json (лёгкий запрос)

```mermaid
sequenceDiagram
    autonumber
    participant LLM as LLM Agent
    participant API as API /index.json
    LLM->>API: GET /api/v1/index.json
    API-->>LLM: 200 OK (< 5 KB)
    LLM->>LLM: extract count=130, grades={A:8,B:45,C:52,D:25}
    LLM->>LLM: plan strategy (fetch supplements.json if needed)
```

## 3. Ошибка — endpoint не существует

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant CDN as GitHub Pages
    C->>CDN: GET /api/v2/unknown.json
    CDN-->>C: 404 Not Found
    Note over C,CDN: 404 — стандартный ответ GitHub Pages
```

## Сценарии и их характеристики

| # | Сценарий | Endpoint | Latency (p50) | Размер | Кэш |
|---|----------|----------|:-------------:|:------:|:---:|
| 1 | Список добавок (cache miss) | /supplements.json | ~300 ms | 660 KB | 1 час |
| 2 | Список добавок (cache hit) | — | < 10 ms | 0 B | — |
| 3 | Метаданные | /index.json | ~150 ms | 3 KB | 1 час |
| 4 | 404 | любой неверный | ~100 ms | ~1 KB | — |

## Связанные документы

- [OpenAPI 3.0 spec](openapi.yaml) — формальная спецификация
- [Error Contract](errors.md) — все возможные ошибки
- [Postman Collection](postman_collection.json) — рабочие примеры

## Версия

- v1.0 — 2026-09-26, 4 сценария, 3 диаграммы

# Error Sequence — обработка сбоев

> Sequence-диаграммы для нештатных ситуаций. Показывает fallback-цепочки и retry-логику.
> Дополняет [BPMN pipeline](bpmn_pipeline.md) и [API Error Contract](api/v1/errors.md).

## 1. EBI отдаёт 500 → каскад на NCBI

```mermaid
sequenceDiagram
    autonumber
    participant F as fetch_europepmc
    participant E as EBI Europe PMC
    participant N as NCBI efetch
    participant FS as Storage
    F->>E: GET /{PMCID}/fullTextXML
    E-->>F: 500 Internal Server Error
    Note over F: Retry 1 (2 сек)
    F->>E: GET /{PMCID}/fullTextXML
    E-->>F: 500 Internal Server Error
    Note over F: Retry 2 (4 сек)
    F->>E: GET /{PMCID}/fullTextXML
    E-->>F: 500 Internal Server Error
    Note over F: Каскад на NCBI
    F->>N: GET efetch.fcgi?id={PMCID}
    N-->>F: 200 OK (JATS XML)
    F->>FS: save {PMCID}.xml
    FS-->>F: OK
    Note over F,FS: Успех через fallback
```

**Результат:** покрытие 87% → 99.7% (см. [ADR-003](adr/003-ebi-ncbi-cascade.md)).

## 2. Общий сбой API — retry с exponential backoff

```mermaid
sequenceDiagram
    autonumber
    participant S as Script
    participant API as External API
    participant Log as Logger
    S->>API: GET request
    API-->>S: 500 Error
    S->>Log: log(attempt=1, error=500)
    Note over S: sleep 5s
    S->>API: GET request
    API-->>S: 503 Service Unavailable
    S->>Log: log(attempt=2, error=503)
    Note over S: sleep 15s
    S->>API: GET request
    API-->>S: 200 OK
    S->>Log: log(success, total_retries=2)
    S->>S: continue pipeline
```

**Backoff:** 5s → 15s → 45s (×3). Макс 3 попытки. После — fail с уведомлением.

## 3. Провал тестов — откат коммита

```mermaid
sequenceDiagram
    autonumber
    actor M as Maintainer
    participant G as Git
    participant CI as GitHub Actions
    participant T as pytest
    participant P as GitHub Pages
    M->>G: git push
    G->>CI: trigger workflow
    CI->>T: run pytest
    T-->>CI: FAIL (1 test)
    CI-->>M: notification: CI failed
    M->>G: git reset --hard HEAD~1
    Note over M,P: Production не тронут
    M->>M: fix locally
    M->>G: git push (with fix)
    G->>CI: trigger workflow
    CI->>T: run pytest
    T-->>CI: OK (138 passed)
    CI->>P: trigger rebuild
    P-->>M: live
```

**Ключевое:** production всегда на последней успешной версии. Откат — мгновенный.

## 4. Новая добавка — валидация не прошла

```mermaid
sequenceDiagram
    autonumber
    actor M as Maintainer
    participant A as LLM Agent
    participant V as validate_proposal.py
    participant D as data.json
    M->>A: brief + evidence
    A-->>M: proposal.json (5 карточек)
    M->>V: validate proposal
    V-->>M: FAIL: US-04 missing key_sources
    M->>A: fix proposal for US-04
    A-->>M: proposal.json (исправлено)
    M->>V: validate proposal
    V-->>M: OK (5/5 passed)
    M->>D: enrich + apply
    D-->>M: 130 → 135 cards
```

## 5. Cache miss — CDN fallback

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant DNS as DNS
    participant CDN as GitHub Pages
    participant Origin as Origin Server
    C->>DNS: resolve deadsno.github.io
    DNS-->>C: IP
    C->>CDN: GET /api/v1/supplements.json
    alt Cache hit
        CDN-->>C: 200 OK (cached)
    else Cache miss
        CDN->>Origin: fetch origin
        Origin-->>CDN: JSON + headers
        CDN-->>C: 200 OK (свежие данные)
    end
```

## Матрица отказов и действий

| # | Отказ | Retry? | Fallback | Уведомление |
|---|-------|:------:|----------|-------------|
| 1 | EBI 500 | 3× | NCBI | Log |
| 2 | API 5xx | 3× | — | Alert |
| 3 | Tests FAIL | — | git reset | CI notification |
| 4 | Validation FAIL | — | review + fix | Local log |
| 5 | CDN miss | — | Origin | — |

## Связанные документы

- [BPMN pipeline](bpmn_pipeline.md)
- [API Error Contract](api/v1/errors.md)
- [ADR-003: EBI → NCBI cascade](adr/003-ebi-ncbi-cascade.md)
- [NFR — Доступность](nfr.md)

## Версия

- v1.0 — 2026-09-26, 5 сценариев отказа, 5 sequence-диаграмм

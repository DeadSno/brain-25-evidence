# BPMN — бизнес-процессы проекта

> Формальные схемы бизнес-процессов в нотации BPMN 2.0.
> Рендерятся через Mermaid на GitHub.
> Основной контекст — [ARCHITECTURE.md](../ARCHITECTURE.md).

## Файлы

- **Camunda Modeler:** [`docs/bpmn/batch_pipeline.bpmn`](bpmn/batch_pipeline.bpmn) — открывается в Camunda Modeler
- **Скриншот:** [`docs/bpmn/screenshot.png`](bpmn/screenshot.png) — цветная схема из Camunda Modeler (2x)

## 1. Основной pipeline — от метаданных до публикации

```mermaid
flowchart TD
    Start([Начало: добавлена<br>новая добавка])

    subgraph M["Maintainer"]
        M1[Добавить запись<br>в config.py]
        M2[Запустить batch]
        M3[Review proposal]
        M4[Approve and merge]
    end

    subgraph S["Scheduler / CI"]
        S1[Триггер pipeline]
        S2[Запуск тестов]
        S3[Commit and Push]
    end

    subgraph P["Python Scripts"]
        P1[fetch_papers.py]
        P2[fetch_pmcids.py]
        P3[fetch_europepmc.py]
        P4[enrich_drafts.py]
        P5[apply_drafts.py]
        P6[update_all.py]
        P7[build_index.py]
        P8[build_api.py]
    end

    subgraph E["External APIs"]
        E1[(PubMed)]
        E2[(Europe PMC)]
        E3[(NCBI efetch)]
    end

    subgraph D["Storage"]
        D1[(data/papers/)]
        D2[(data/pmc/text/)]
        D3[(docs/data.json)]
        D4[(docs/api/v1/)]
    end

    Start --> M1 --> M2 --> S1
    S1 --> P1
    P1 -->|esearch| E1
    E1 -->|37618 papers| D1
    P2 -->|check PMCID| E2
    P2 -->|11176 pmcid| D2
    P3 -->|каскад fetch| E2
    P3 -.->|fallback 500| E3
    E2 -->|XML| D2
    E3 -->|XML| D2

    P4 -->|enrich| D3
    P5 -->|apply| D3

    M3 --> M4 --> P6
    P6 -->|метрики, SI| D3
    P7 -->|index| D3
    P8 -->|API| D4

    P6 --> S2
    S2 -->|OK| S3
    S3 --> End([Опубликовано])
    S2 -->|FAIL| M1

    classDef human fill:#e1f5ff,stroke:#0288d1
    classDef script fill:#fff3e0,stroke:#f57c00
    classDef external fill:#f3e5f5,stroke:#7b1fa2
    classDef storage fill:#e8f5e9,stroke:#388e3c

    class M1,M2,M3,M4 human
    class P1,P2,P3,P4,P5,P6,P7,P8 script
    class E1,E2,E3 external
    class D1,D2,D3,D4 storage
```

## 2. Ручное обновление (без CI) — резервный сценарий

```mermaid
sequenceDiagram
    autonumber
    actor M as Maintainer
    participant SH as Shell
    participant PY as Python
    participant GH as GitHub

    M->>SH: python scripts/fetch_papers.py
    SH->>PY: запуск
    PY-->>M: 37618 papers
    M->>SH: python scripts/fetch_europepmc.py
    SH->>PY: каскад EBI → NCBI
    PY-->>M: 11940 XML
    M->>SH: python scripts/enrich_drafts.py --apply
    PY-->>M: 130 карточек обновлено
    M->>SH: pytest -q
    PY-->>M: 118 passed
    M->>SH: git add + commit
    SH->>GH: push
    GH-->>M: CI запущен
    Note over GH: GitHub Actions<br>запускает тесты
    GH-->>M: ✅ Опубликовано
```

## Матрица RACI

| Задача | Maintainer | Scheduler | Python | APIs | Storage |
|--------|:----------:|:---------:|:------:|:----:|:-------:|
| Добавить добавку | **R** | I | C | — | — |
| Fetch метаданных | I | **R** | E | C | W |
| Fetch full texts | I | **R** | E | C | W |
| Обогащение карточек | **A** | R | E | — | W |
| Review proposal | **R** | I | — | — | — |
| Публикация API | I | **R** | E | — | W |
| Тесты | I | **R** | E | — | — |

**Легенда:** R — Responsible (делает), A — Accountable (отвечает), C — Consulted, I — Informed, E — Executes, W — Writes.

## События и шлюзы

| Событие | Тип | Действие |
|---------|-----|----------|
| `Новая добавка` | Start | Триггер batch |
| `Тесты FAIL` | Error | Возврат к Review |
| `EBI 500` | Escalation | Fallback на NCBI |
| `Публикация` | End | GitHub Pages rebuild |
| `Сброс failed → pending` | Timer | Ручной перезапуск fetch |

## Версия

- v1.0 — 2026-09-25, batch 17c, 130 добавок, 11940 full texts
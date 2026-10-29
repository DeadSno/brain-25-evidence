# Архитектурные диаграммы

> Формальные UML-диаграммы проекта. Рендерятся автоматически на GitHub через Mermaid.
> Основной контекст — [ARCHITECTURE.md](../ARCHITECTURE.md).

Содержание:
1. [Use Case Diagram](#1-use-case-diagram--кто-и-что-делает-с-системой)
2. [Class Diagram](#2-class-diagram--модель-данных)
3. [Sequence Diagram](#3-sequence-diagram--etl-pipeline)
4. [State Machine](#4-state-machine--жизненный-цикл-добавки)
5. [Component Diagram](#5-component-diagram--компоненты-системы)

## 1. Use Case Diagram — кто и что делает с системой

```mermaid
flowchart LR
    User([Пользователь])
    Dev([Внешний разработчик])
    Maint([Maintainer])
    LLM([LLM / Agent])
    subgraph Brain[Brain 25 Evidence]
        UC1([Просмотреть карточку])
        UC2([Фильтровать по грейду])
        UC3([Изучить механизмы])
        UC4([Проверить взаимодействия])
        UC5([Скачать полный датасет])
        UC6([Прочитать метаданные API])
        UC7([Добавить новую добавку])
        UC8([Обновить full texts])
        UC9([Обогатить данные через ETL])
        UC10([RAG по 11900 статьям])
    end
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    Dev --> UC5
    Dev --> UC6
    Maint --> UC7
    Maint --> UC8
    Maint --> UC9
    LLM --> UC6
    LLM --> UC10
```

### Акторы

| Актор | Роль | Use Cases |
|-------|------|-----------|
| Пользователь | Конечный потребитель | UC1-UC4 |
| Внешний разработчик | Интегратор API | UC5-UC6 |
| Maintainer | Владелец проекта | UC7-UC9 |
| LLM / Agent | RAG-система | UC6, UC10 |

## 2. Class Diagram — модель данных

```mermaid
classDiagram
    class Supplement {
        +string id
        +string category
        +string grade
        +string verdict
        +int code
        +string about
        +string dosage
        +int scienceIndex
        +int rct
        +int metaCount
        +int citations
    }
    class Mech {
        +string mechanism
        +string effect
        +string strength
    }
    class Interaction {
        +string with
        +string severity
        +string note
    }
    class KeySource {
        +string pmid
        +string doi
        +string title
        +int year
        +string journal
    }
    class EffectTag {
        +string tag
    }
    class Paper {
        +string pmid
        +string pmcid
        +string title
        +int year
        +string journal
    }
    class COI {
        +string coi_type
        +bool has_funding
        +bool has_pharma
    }
    Supplement "1" *-- "2..4" Mech : содержит
    Supplement "1" *-- "1..3" Interaction : имеет
    Supplement "1" *-- "1..3" KeySource : подтверждается
    Supplement "1" o-- "1..4" EffectTag : классифицируется
    KeySource ..> Paper : ссылается
    Paper "1" o-- "0..1" COI : имеет
```

## 3. Sequence Diagram — ETL pipeline

```mermaid
sequenceDiagram
    autonumber
    participant S as Scheduler
    participant F as fetch_papers
    participant P as PubMed API
    participant E as Europe PMC NCBI
    participant D as data.json
    participant A as docs api v1
    participant U as User Browser
    Note over S,U: Фаза 1 - сбор метаданных
    S->>F: trigger
    F->>P: esearch по 130 запросам
    P-->>F: 37618 papers
    F->>D: сохраняет метаданные
    Note over S,U: Фаза 2 - сбор full texts
    S->>E: fetch_europepmc
    E->>E: пробуем EBI API
    Note over E: EBI отдаёт 500
    E->>E: fallback на NCBI efetch
    E-->>D: 11940 XML (87%)
    Note over S,U: Фаза 3 - обогащение
    S->>D: enrich_drafts --apply
    D-->>D: 130 карточек
    Note over S,U: Фаза 4 - публикация
    S->>A: build_api
    A-->>U: GET api v1 supplements.json
    U->>U: рендерит UI / RAG
```

## 4. State Machine — жизненный цикл добавки

```mermaid
stateDiagram-v2
    [*] --> Draft: новая добавка в CSV
    Draft --> Enriched: enrich_drafts --apply
    Enriched --> Validated: validate_proposal OK
    Enriched --> Rejected: ошибки валидации
    Rejected --> Draft: правка proposal
    Validated --> Applied: apply_drafts
    Applied --> Published: git push + CI OK
    Applied --> Rollback: tests FAIL
    Rollback --> Draft: откат
    Published --> Stale: старше 1 года
    Stale --> Draft: пересмотр
    Published --> [*]
```

### Статусы и переходы

| Статус | Описание | Условие входа | Выход |
|--------|----------|---------------|-------|
| Draft | Черновик в _drafts.json | Добавлен в CSV | Enriched / Rejected |
| Enriched | Заполнены adv-поля | enrich_drafts --apply | Validated / Rejected |
| Validated | Прошёл validate_proposal | 0 errors | Applied |
| Rejected | Ошибки валидации | Есть errors | Draft (правка) |
| Applied | Смерджен в data.json | apply_drafts OK | Published / Rollback |
| Published | В production | git push + CI | Stale |
| Rollback | Откат из-за ошибок | tests FAIL | Draft |
| Stale | Не обновлялся > 1 года | Время | Draft |

## 5. Component Diagram — компоненты системы

```mermaid
flowchart TB
    subgraph FE[Frontend]
        HTML[Static HTML CSS JS]
        ATLAS[atlas.html]
        MAP[map.html]
        CALC[calculator.html]
    end
    subgraph APIL[API Layer]
        IDX[index.json]
        SUP[supplements.json]
    end
    subgraph ETL[ETL Pipeline]
        FETCH[fetch_papers.py]
        PMC[fetch_europepmc.py]
        ENRICH[enrich_drafts.py]
        APPLY[apply_drafts.py]
        UPD[update_all.py]
        BI[build_index.py]
        BA[build_api.py]
    end
    subgraph BIZ[Business Intelligence]
        STREAMLIT[Streamlit Dashboard]
        DUCK[DuckDB Analytics]
    end
    subgraph DATA[Data Storage]
        JSON[data.json]
        PAPERS[papers.json]
        XML[PMC XML]
        DB[(brain.duckdb)]
    end
    subgraph EXT[External APIs]
        PUBMED[(PubMed)]
        EPMC[(Europe PMC)]
        NCBI[(NCBI efetch)]
        OALEX[(OpenAlex)]
    end
    PUBMED -->|esearch| FETCH
    FETCH --> PAPERS
    EPMC -->|JATS XML| PMC
    NCBI -.->|fallback| PMC
    PMC --> XML
    PAPERS --> ENRICH
    XML --> ENRICH
    ENRICH --> APPLY
    APPLY --> JSON
    JSON --> UPD
    UPD --> BI
    BI --> JSON
    JSON --> BA
    BA --> APIL
    APIL --> HTML
    APIL --> ATLAS
    JSON --> STREAMLIT
    JSON --> DUCK
    OALEX --> FETCH
```

### Принципы архитектуры

- **Backend-less:** нет серверной логики — только статика
- **Idempotent ETL:** повторный запуск не ломает данные
- **Git as database:** вся история в git
- **Fallback chains:** EBI -> NCBI, JSON -> DuckDB
- **Separation of Concerns:** данные, логика, представление разделены

## Версия

- v1.2 — 2026-09-25, 5 диаграмм, batch 17c, 130 добавок

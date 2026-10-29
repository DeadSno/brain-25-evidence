# DFD — Data Flow Diagram

> Диаграмма потоков данных (нотация Yourdon/DeMarco).
> Показывает, как данные перемещаются между процессами, хранилищами и внешними системами.
>
> Дополняет [BPMN](bpmn_pipeline.md) (процессы) и [ERD](erd.md) (данные в покое).

## Уровень 0 — Контекстная диаграмма

```mermaid
flowchart LR
    User([Пользователь])
    Dev([Разработчик])
    Maint([Maintainer])
    Ext[/PubMed EuropePMC/]
    System[Brain 25 Evidence]
    User -->|запрос| System
    System -->|карточки| User
    Dev -->|запрос API| System
    System -->|JSON| Dev
    Maint -->|команды| System
    Ext -->|статьи| System
```

## Уровень 1 — Основные процессы

```mermaid
flowchart TB
    Maint([Maintainer])
    User([Пользователь])
    P1[P1 Fetch метаданных]
    P2[P2 Fetch full texts]
    P3[P3 Enrich карточек]
    P4[P4 Анализ COI]
    P5[P5 Публикация API]
    D1[(D1 papers.json)]
    D2[(D2 PMC XML)]
    D3[(D3 data.json)]
    D4[(D4 coi_report.json)]
    D5[(D5 API JSON)]
    Ext1[/PubMed API/]
    Ext2[/Europe PMC/]
    Ext3[/NCBI efetch/]
    Maint -->|trigger| P1
    Ext1 -->|37618 papers| P1
    P1 -->|write| D1
    Maint -->|trigger| P2
    D1 -->|read| P2
    Ext2 -->|XML| P2
    Ext3 -.->|fallback| P2
    P2 -->|write| D2
    Maint -->|trigger| P3
    D2 -->|read| P3
    D1 -->|read| P3
    P3 -->|write| D3
    Maint -->|trigger| P4
    D2 -->|read| P4
    P4 -->|write| D4
    Maint -->|trigger| P5
    D3 -->|read| P5
    P5 -->|write| D5
    D5 -->|JSON| User
```

## Уровень 2 — Процесс P3 (Enrich)

```mermaid
flowchart LR
    In1[/data.json draft/]
    In2[/proposal JSON/]
    In3[/content.py/]
    P3_1[3.1 Валидация proposal]
    P3_2[3.2 Enrich полей]
    P3_3[3.3 Merge в data.json]
    P3_4[3.4 Пересчёт метрик]
    Out[/data.json/]
    In1 --> P3_1
    In2 --> P3_1
    In3 --> P3_2
    P3_1 -->|valid| P3_2
    P3_2 --> P3_3
    P3_3 --> P3_4
    P3_4 --> Out
```

## Потоки данных — таблица

| # | Источник | Приёмник | Данные | Формат | Частота |
|---|----------|----------|--------|--------|---------|
| F1 | Maintainer | P1 | Триггер | CLI | вручную |
| F2 | PubMed API | P1 | 37 618 papers | JSON | раз в месяц |
| F3 | P1 | D1 | papers.json | JSON | после P1 |
| F4 | Europe PMC | P2 | XML | HTTP | по запросу |
| F5 | NCBI | P2 | XML (fallback) | HTTP | по запросу |
| F6 | P2 | D2 | 11 940 XML | files | после P2 |
| F7 | D2 + D1 | P3 | Full texts + metadata | mix | при обновлении |
| F8 | P3 | D3 | data.json | JSON | после enrich |
| F9 | D2 | P4 | XML для анализа | files | раз в месяц |
| F10 | D3 | P5 | data.json | JSON | при публикации |
| F11 | P5 | D5 | API JSON | JSON | при публикации |
| F12 | D5 | User | JSON | HTTP | real-time |

## Хранилища данных

| ID | Путь | Содержимое | Размер | Формат |
|----|------|-----------|--------|--------|
| D1 | data/papers/papers.json | Метаданные 37 618 статей | ~50 MB | JSON |
| D2 | data/pmc/text/*.xml | 11 940 full texts | ~1 GB | XML |
| D3 | docs/data.json | 130 карточек (истина) | 76 KB | JSON |
| D4 | reports/coi_report.json | Анализ COI | 50 KB | JSON |
| D5 | docs/api/v1/*.json | API endpoints | 660 KB | JSON |
| D6 | data/db/brain.duckdb | Аналитическая БД | ~30 MB | DuckDB |

## Внешние сущности

| Сущность | Тип | Протокол | Формат | SLA |
|----------|-----|----------|--------|-----|
| PubMed | API | HTTPS | XML | best effort |
| Europe PMC | REST | HTTPS | XML | best effort |
| NCBI efetch | REST | HTTPS | XML | best effort |
| OpenAlex | API | HTTPS | JSON | best effort |
| GitHub Pages | CDN | HTTPS | HTML/JSON | 99.9% |

## Уровни декомпозиции

| Уровень | Что показывает | Аудитория |
|---------|----------------|-----------|
| 0 | Внешние взаимодействия | Бизнес, аналитики |
| 1 | Основные процессы + хранилища | Разработчики, СА |
| 2 | Детализация подпроцесса | Разработчики |

## Версия

- v1.0 — 2026-09-25, 5 процессов, 6 хранилищ, 12 потоков

# Deployment — как система развёрнута

> Инфраструктурная схема проекта: где живут данные, сервисы и клиенты.
> Дополняет [Component Diagram](architecture_diagrams.md) техническим развёртыванием.

## Общая схема

```mermaid
flowchart TB
    subgraph Users[Клиенты]
        Browser[Browser]
        LLM[LLM Agent]
        Dev[Developer]
    end
    subgraph CDN[GitHub Pages CDN]
        HP[deadsno.github.io]
        HTML[HTML CSS JS]
        JSON[data.json + api/v1]
    end
    subgraph SC[Streamlit Cloud]
        ST[brain-25-evidence.streamlit.app]
        BI[Streamlit App]
    end
    subgraph GH[GitHub]
        Repo[Repository]
        Actions[GitHub Actions CI]
    end
    subgraph Local[Local Dev]
        Clone[git clone]
        Venv[.venv]
        DB[(brain.duckdb)]
    end
    Browser -->|HTTPS| HP
    LLM -->|HTTPS| HP
    Dev -->|HTTPS| HP
    HP --> HTML
    HP --> JSON
    Browser -->|HTTPS| ST
    ST --> BI
    BI -->|fetch| JSON
    Repo -.->|deploy| HP
    Repo -.->|deploy| SC
    Repo --> Actions
    Actions -->|test| Repo
    Clone --> Venv
    Venv --> DB
    Repo -.->|git clone| Clone
```

## Компоненты развёртывания

| Компонент | Хостинг | URL | Стоимость |
|-----------|---------|-----|-----------|
| Статический сайт | GitHub Pages | https://deadsno.github.io/brain-25-evidence/ | 0 руб |
| BI Dashboard | Streamlit Cloud | https://brain-25-evidence.streamlit.app | 0 руб |
| API | GitHub Pages (static) | /api/v1/*.json | 0 руб |
| CI | GitHub Actions | — | 0 руб |
| Репозиторий | GitHub | https://github.com/DeadSno/brain-25-evidence | 0 руб |
| Локальная разработка | Developer machine | — | — |

**Итого: 0 руб/мес.**

## Пайплайн деплоя

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant Local as Local repo
    participant GH as GitHub
    participant Actions as GitHub Actions
    participant Pages as GitHub Pages
    participant Streamlit as Streamlit Cloud
    Dev->>Local: git commit + push
    Local->>GH: push to main
    GH->>Actions: trigger workflows
    par Tests
        Actions->>Actions: pytest -q (138 tests)
    and Newman
        Actions->>Actions: newman run postman_collection
    end
    Actions-->>GH: status check
    alt Tests passed
        GH->>Pages: rebuild site
        Pages-->>Dev: URL live in ~60s
        GH->>Streamlit: auto-redeploy
        Streamlit-->>Dev: BI live in ~2 min
    else Tests failed
        Actions-->>GH: FAIL
        GH-->>Dev: notification
    end
```

## Уровни развёртывания

### Production

- Статика — GitHub Pages, CDN, HTTPS, custom domain
- BI — Streamlit Cloud
- API — статические JSON-файлы (нет backend)
- SLA — 99.9%

### Staging / Preview

- Не требуется — GitHub Pages деплоит только main
- Альтернатива: локальный запуск через:

```bash
python -m http.server 8000 --directory docs
```

### Local Development

```bash
git clone https://github.com/DeadSno/brain-25-evidence
cd brain-25-evidence
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python -m http.server 8000 --directory docs
# открыть http://localhost:8000
```

## Переменные окружения

| Переменная | Где | Назначение |
|-----------|-----|-----------|
| UPDATE_SNAPSHOT | Локально | Обновить snapshot-тесты |
| EMAIL | Скрипты fetch | User-Agent для PubMed/NCBI |
| TOOL | Скрипты fetch | Идентификация в API-запросах |

**Секретов нет** — API публичные, GitHub Pages не требует auth.

## Disaster Recovery

| Сценарий | Что происходит | Recovery |
|----------|----------------|----------|
| GitHub Pages упал | Сайт недоступен | Ждать восстановления GitHub |
| Streamlit Cloud упал | BI недоступен | Fallback на GitHub Pages |
| PubMed API упал | fetch падает | Retry 3x с backoff |
| EBI отдаёт 500 | fetch не работает | Автоматический fallback на NCBI |
| Локально git сломан | Нельзя коммитить | git reset --hard origin/main |

## Мониторинг

| Что | Как | Кто |
|-----|-----|-----|
| CI статус | GitHub Actions badge | Developer |
| Newman (API) | Scheduled workflow (weekly) | Developer |
| Snapshot-тесты | pytest при каждом push | CI |
| Availability | Ручной UptimeRobot (опционально) | Developer |

## Связанные документы

- [Component Diagram](architecture_diagrams.md)
- [NFR — Доступность](nfr.md)
- [BPMN pipeline](bpmn_pipeline.md)
- [ADR-002: GitHub Pages](adr/002-github-pages.md)

## Версия

- v1.0 — 2026-09-26, 6 компонентов, 0 руб/мес

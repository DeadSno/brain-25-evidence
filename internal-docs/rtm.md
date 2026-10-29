# RTM — Requirements Traceability Matrix

> Матрица трассируемости: Требование -> Дизайн -> Код -> Тест -> Статус.
> Источник: [user_stories.md](user_stories.md). НФТ: [nfr.md](nfr.md).

## 1. Функциональные требования

| ID | Требование | Дизайн | Код | Тест | Статус |
|----|-----------|--------|-----|------|:------:|
| US-01 | Поиск добавки | index.html | script.js:searchCards | TBD v2 | partial |
| US-02 | Фильтр по грейду | index.html | script.js:filterByGrade | TBD v2 | partial |
| US-03 | Сравнение | index.html radar | script.js:compare | TBD v2 | partial |
| US-04 | Взаимодействия | interactions.html | interactions.html | TBD v2 | partial |
| US-05 | REST API список | OpenAPI | build_api.py | test_api_contract.py | done |
| US-06 | REST API метаданные | OpenAPI | build_api.py | test_api_contract.py | done |
| US-07 | Серверная фильтрация | OpenAPI parameters | не реализовано | - | not started |
| US-08 | Обновление через git | BPMN | enrich_drafts.py | test_enrich.py | done |
| US-09 | Batch за 1 команду | BPMN | scripts/*.py | test_pipeline.py | partial |

**Легенда:** done / partial / not started / blocked

## 2. Нефункциональные требования

| ID | Требование | Раздел NFR | Как проверяется | Статус |
|----|-----------|-----------|-----------------|:------:|
| NFR-P1 | API latency < 800 ms | nfr §1.1 | Lighthouse | done |
| NFR-P2 | FCP < 1.5 s | nfr §1.2 | Lighthouse CI | partial |
| NFR-S1 | До 5 000 карточек | nfr §2 | v2 | not started |
| NFR-A1 | 99.9% SLA | nfr §3 | UptimeRobot | done |
| NFR-Sec1 | No PII | nfr §4.1 | Аудит | done |
| NFR-Sec2 | No secrets | nfr §4.1 | git grep | done |
| NFR-C1 | Chrome 90+ | nfr §5.1 | Feature detection | done |
| NFR-M1 | Покрытие > 80% | nfr §7 | pytest --cov | done (118) |
| NFR-O1 | Snapshot-тесты | nfr §8 | test_snapshot.py | done |

## 3. Зависимости требований

graph TD
    US-05 --> US-06
    US-05 --> US-07
    US-01 --> US-02
    US-02 --> US-03
    US-04 -.-> US-01
    US-08 --> US-09
    US-05 -.-> NFR-P1
    US-06 -.-> NFR-P1

## 4. Покрытие тестами

| Категория | Требований | Покрыто | % |
|-----------|:----------:|:-------:|:-:|
| Функциональные | 9 | 5 | 56 |
| Нефункциональные | 10 | 8 | 80 |
| Всего | 19 | 13 | 68 |

Целевое: > 90% к концу Спринта 4.

## 5. Change Log

| Дата | Изменение | Автор |
|------|-----------|-------|
| 2026-09-25 | Создан RTM v1.0 | DeadSno |

## Версия

- v1.0 — 2026-09-25, 19 требований, 13 покрыто

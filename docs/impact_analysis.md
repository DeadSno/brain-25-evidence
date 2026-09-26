# Impact Analysis — матрица влияния изменений

> Показывает, что затрагивается при изменении требований или данных.
> Инструмент системного аналитика для оценки последствий ДО внесения правок.

## Матрица: Изменение → Что затрагивается

| # | Изменение | Файлы | Тесты | API | UI | Сложность |
|---|-----------|-------|-------|-----|-----|-----------|
| 1 | Добавить новую добавку | data.json, config.py, content.py, effect_tags_map.py | +schema, +interactions | supplements.json, index.json | витрина | Низкая |
| 2 | Изменить грейд существующей | data.json, content.py | test_schema (grade) | supplements.json | витрина, карта | Низкая |
| 3 | Добавить новый effect_tag | effect_tags_map.py, effect_tags.json | test_schema (tags) | index.json (stats) | атлас, фильтры | Низкая |
| 4 | Изменить схему API (v1 → v2) | openapi.yaml, build_api.py | test_api_contract | ВСЕ endpoints | ВСЕ страницы | Высокая |
| 5 | Перевести на PostgreSQL | db/*, data.json (deprecated) | test_sql, test_api_contract | supplements.json (fetch из БД) | — | Очень высокая |
| 6 | Добавить новое поле в карточку | data.json, content.py, schema.sql | +schema test | supplements.json | карточка добавки | Средняя |
| 7 | Изменить методологию COI | analyze_coi.py, coi_report.json | test_schema (coi) | — | methodology.html | Средняя |
| 8 | Обновить BPMN pipeline | bpmn_pipeline.md, batch_pipeline.bpmn | — | — | — | Низкая |
| 9 | Добавить новый язык (i18n) | ВСЕ html, data.json (структура) | +i18n tests | — | ВСЕ страницы | Очень высокая |
| 10 | Сменить хостинг с GitHub Pages | .github/workflows/*, README | — | URL endpoints | ВСЕ URL | Средняя |

## Матрица рисков

| Изменение | Риск регрессии | Тесты покрывают | Rollback |
|-----------|:--------------:|:---------------:|----------|
| 1 | Низкий | ✅ | git revert 1 файл |
| 2 | Низкий | ✅ | git revert |
| 3 | Низкий | ✅ | git revert |
| 4 | Высокий | ⚠️ частично | Версионирование v1/v2 |
| 5 | Очень высокий | ✅ | Откат на JSON |
| 6 | Средний | ⚠️ нужны новые | git revert |
| 7 | Средний | ✅ | git revert |
| 8 | Низкий | ❌ | git revert |
| 9 | Очень высокий | ❌ | git revert |
| 10 | Средний | ⚠️ CI | Возврат на GH Pages |

## Правила обновления

**Всегда синхронизировать:**
1. `data.json` ↔ `data_index.json` (build_index.py)
2. `data.json` ↔ `effect_tags.json` (build_effect_tags.py)
3. `data.json` ↔ `api/v1/*.json` (build_api.py)
4. `data.json` ↔ DuckDB (import_to_duckdb.py)

**Процедура для изменения #1 (новая добавка):**

```bash
# 1. CSV + config.py
python scripts/add_supplements_batch.py --input supplements_to_add.csv
# 2. Fetch
python scripts/fetch_papers.py
python scripts/fetch_europepmc.py --workers 2
# 3. Enrich
python scripts/enrich_drafts.py --proposal q14_batch_N.json --apply
python scripts/apply_drafts.py
# 4. Обновить эффекты, индексы, API, БД
python scripts/build_effect_tags.py
python scripts/build_index.py
python scripts/build_api.py
python scripts/db/import_to_duckdb.py
# 5. Тесты
pytest -q -m 'not network'
# 6. Коммит
git add . && git commit -m 'feat: +N cards' && git push
```

## Связанные документы

- [SRS](srs.md)
- [RTM](rtm.md)
- [BPMN pipeline](bpmn_pipeline.md)
- [ADR](adr/)

## Версия

- v1.0 — 2026-09-26, 10 изменений, 4 правила синхронизации

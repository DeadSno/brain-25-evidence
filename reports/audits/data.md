# Аудит: Данные (data) + QA данных

| | |
|---|---|
| **Тип** | data — целостность, схемы, качество, происхождение; QA данных (покрытие тестами) |
| **Источники** | `audit_A_data-audit.md`, `audit_A_qa-deep-audit.md`, `AUDIT_E_data-validation.md`, `STAGE4_DATA.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P1 — 6, P2 — 18 |
| **Закрыто** | P1 — 4 |

---

## Открыто

### P1

| ID | Находка | Где | Источник / статус |
|---|---|---|---|
| DATA-P1-02 | `hedges_g_outcome` пусто у 86 карточек (из них 42 с заполненным `hedges_g`); метки исхода нет в самих данных (`113 пустых` в `hedges_g_all.json`) | `docs/data.json` | STAGE4 §E — техдолг v5.6.4 |
| DATA-P1-12 | `timeseries` покрывает 94/130; нет кривых у 36 карточек, из них 19 с `citations > 0` (B1 871, B2 1111 …) | `data/timeseries/`, `docs/data.json` | STAGE4 §D — техдолг v5.6.4 |
| DATA-COI | COI-данные (`reports/coi_per_paper.json` 486 КБ) не показаны в карточках, 0 упоминаний в HTML | контент | STAGE4 §F — техдолг v5.7 |
| QA-P1-01 | 20 критичных скриптов без тестов (build_api, build_key_sources, build_interactions, check_state, validate_proposal, analyze_coi, build_sitemap, build_feed, build_edu, build_timeseries, build_ma_timeline, build_changelog_public, build_slim, apply_adv, apply_drafts, apply_mechs, sync_test_count, rebuild_index, recalc_science_index, update_all) | `scripts/` | audit_A_qa P1-1 |
| QA-P1-02 | Нет теста идемпотентности `build_sup` | `scripts/build_sup.py` | audit_A_qa P1-2 |
| QA-P1-03 | Нет теста валидности HTML `sup/*.html` | `docs/sup/` | audit_A_qa P1-3 |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| DATA-P2-01 | `hedges_g_ci` = null у 48 | `docs/data.json` | data-audit |
| DATA-P2-02 | `ma_top3` = null у 50 | `docs/data.json` | data-audit |
| DATA-P2-03 | 18 карточек без citations | `docs/data.json` | data-audit |
| DATA-P2-04 | Мёртвые ключи `PRIOR_G` | `src/config.py` | data-audit |
| DATA-P2-05 | U+FFFD в `unpaywall.json` (8 строк) | `data/` | data-audit |
| DATA-P2-06 | U+FFFD в `funders.json` (1 строка) | `data/` | data-audit |
| DATA-P2-07 | `hedges_g_all.json` покрывает 113/130 (17 отсутствуют, 27 пустых) | `docs/` | data-validation |
| DATA-P2-08 | `key_sources` до 5 записей у 26 карточек (заявлено 1–3) | `docs/` | data-validation |
| DATA-P2-09 | `dosage_parsed.json` покрывает 94/130 | `data/` | data-validation |
| DATA-P2-10 | `grade` не монотонен по `scienceIndex` | `docs/data.json` | data-validation |
| DATA-P2-11 | `forms` = null 123 / строка 7 | `docs/data.json` | data-validation |
| DATA-P2-12 | `metaCount == 0` у 7 | `docs/data.json` | data-validation |
| DATA-P2-13 | `citations`/`ongoing`/`wiki` = null 17/36/40 | `docs/data.json` | data-validation |
| DATA-P2-14 | 79 объединённых против 59 атомарных категорий | `docs/effect_tags.json` | data-validation |
| QA-P2-01 | `test_silent_handlers` привязан к номерам строк `sw.js` (техдолг #52) | `tests/` | audit_A_qa P2 |
| QA-P2-02 | 123 карточки с null `forms` (см. DATA-P2-11) | `docs/data.json` | audit_A_qa P2 |
| QA-P2-03 | Нет теста битых ссылок в `sup/` | `docs/sup/` | audit_A_qa P2 |
| QA-COV | Покрытие: 16 из 89 скриптов (18%) | `scripts/` | audit_A_qa |

---

## Закрыто

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| DATA-P1-01 | `SUPPLEMENTS` в `src/config.py` покрывал 74/130; повторный `build_sup` обнулял бы `ma_top3` у 56 карточек | `59cc0de` | 11.10.2026 |
| DATA-P1-03 | `RETMAX = 500` обрезал списки PMID у 61 карточки → поднят до 2000 | `59cc0de` | 11.10.2026 |
| DATA-P1-04 | `esearch` без `sort=relevance` | в коде `scripts/build_key_sources.py:64` | — (закрыто до консолидации) |
| DATA-P1-11 | Поле `with`: 51 из 199 — заглушки в 4 вариантах (`нет данных` 32, `""` 10, `"—"` 9) → унифицировано в `"нет данных"` | `59cc0de` | 11.10.2026 |

---

## Примечания

- `59cc0de` (этап 4) также синхронизировал `src/content.py`, `data_index.json`, API и снапшоты данных (`pytest` 862/18).
- `fetch_papers.py` после смены `RETMAX` **не перезапускался** — повторная загрузка из сети остаётся отдельной задачей.
- `data/supplements_slim.json` правился in-place (пересборка требует загитигноренного `papers.json`) — техдолг v5.6.4.
- Проверка контрольных пар (data.json ↔ производные) дрейфа не выявила.
- Блокер верификации: `templates/sup.html.j2` был устаревшим (закрыт `e613b68`, см. `audits/a11y.md` A11Y-P2-16).

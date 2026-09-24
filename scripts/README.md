# scripts/ — карта скриптов

**Последнее обновление:** 2026-09-24

Все скрипты разделены на 7 категорий: **пайплайн батчей**, **источники**,
**сборка**, **обогащение**, **анализ**, **QA** и **инструменты**.
Мёртвые скрипты и разовые миграции удалены.
`.gitignore` блокирует рецидивы: `scripts/fix_*.py`, `scripts/_*.py`, `scripts/diag_*.py`.

---

## 🔄 Пайплайн батчей (добавление добавок)

Основной процесс расширения базы.

| Скрипт | Что делает | Запуск |
|---|---|---|
| `add_supplements_batch.py` | CSV → `docs/_drafts.json` (черновики) + обновляет `src/config.py` и `docs/data_pubmed_terms.json` | `python scripts/add_supplements_batch.py --input scripts/supplements_to_add.csv` |
| `fetch_evidence_abstracts.py` | Тянет top-3 MA abstracts из PubMed в `reports/evidence/<id>.md` | `python scripts/fetch_evidence_abstracts.py --all` |
| `enrich_drafts.py` | Proposal JSON агента → обновляет `_drafts.json` | `python scripts/enrich_drafts.py --proposal q14_batch_N_proposal.json --apply` |
| `apply_drafts.py` | `_drafts.json` → `docs/data.json` (только готовые) | `python scripts/apply_drafts.py` |
| `apply_adv.py` | Применяет adv-поля (Q1.4) из proposal | `python scripts/apply_adv.py --proposal q14_batch_N_proposal.json --apply` |
| `apply_mechs.py` | Применяет механизмы из proposal | `python scripts/apply_mechs.py --proposal mechs_batch_N_proposal.json --apply` |

**Цикл:** CSV → batch → evidence → LLM-агент → proposal JSON → enrich → apply.

---

## 🔬 Источники (API → data.json)

Скрипты, которые обновляют `docs/data.json` через внешние API.

| Скрипт | Что делает |
|---|---|
| `fetch_metrics.py` | wiki (Wikimedia), citations (OpenAlex), ongoing (ClinicalTrials.gov) |
| `recalc_science_index.py` | `scienceIndex = RCT + 5×MA` |
| `fetch_hedges_g.py` | Hedges' g из топ-MA (двухпроходный алгоритм) |
| `enrich_dois.py` | DOI в `key_sources` через PubMed esummary |
| `search_sources.py` | Поиск PMID через PubMed E-utilities (curated `MANUAL_PMIDS`) |
| `apply_sources.py` | `reports/sources_candidates.json` → `data.json` |
| `validate_sources.py` | Квартальная валидация PMID: живые ли, метаданные |
| `audit_stale.py` | PMIDs > 5 лет — квартальный аудит |

---

## 🏗️ Сборка (data.json → артефакты)

| Скрипт | Что генерирует |
|---|---|
| `build_index.py` | `docs/data_index.json` (проекция для главной) |
| `build_key_sources.py` | `key_sources` из `src.config.SUPPLEMENTS` |
| `build_ma_timeline.py` | `docs/data_ma_timeline.json` |
| `build_edu.py` | edu-блоки карточек |
| `build_interactions.py` | `interactions` (синергии/антагонисты) |
| `build_interactions_graph.py` | `docs/interactions_graph.json` |
| `build_effect_tags.py` | `docs/effect_tags.json` (18 тегов) |
| `build_changelog_public.py` | `docs/changelog_public.html` |
| `build_timeseries.py` | `docs/timeseries.json` |
| `build_slim.py` | `docs/papers_slim.json` + `docs/supplements_slim.json` |

---

## 📥 Обогащение (37k papers)

| Скрипт | Что делает |
|---|---|
| `fetch_papers.py` | 37k papers из PubMed (базовый сбор) |
| `enrich_papers.py` | MeSH, keywords, authors |
| `fetch_scimago.py` / `join_scimago.py` | Квартили журналов |
| `fetch_nlm_catalog.py` | NLM-аббревиатуры для матчинга |
| `fetch_unpaywall.py` | OA-статус и PDF-ссылки |
| `fetch_funders.py` | Funders через CrossRef |
| `fetch_retractions.py` | Retraction-статус |
| `fetch_trials_links.py` / `enrich_trials.py` | NCT-испытания |
| `fetch_pmcids.py` | PMCID через NCBI eutils |
| `fetch_europepmc.py` | Full texts через Europe PMC REST (5059 XML) |
| `fetch_fulltexts_playwright.py` | Full texts через Playwright (4016 txt) |
| `parse_xml_meta.py` | Funding / COI из XML |

---

## 📊 Анализ

| Скрипт | Что делает |
|---|---|
| `analyze_funding.py` / `analyze_funding_v2.py` | Топ фандеров из XML |
| `analyze_crossref.py` | Funders из CrossRef |
| `extract_g.py` | Hedges' g из abstracts |
| `extract_sample_sizes.py` | Размер выборок |
| `extract_stats_claims.py` | p-value, CI |
| `parse_dosages.py` | Дозы из `dosage` поля |
| `enrich_species.py` / `enrich_design.py` | Species / design |

---

## 🧪 QA

| Скрипт | Что проверяет |
|---|---|
| `audit_content_gaps.py` | Пустые поля BASE/ADV |
| `audit_links.py` | Мёртвые ссылки (вызывается из CI) |
| `e2e_smoke.py` | Playwright e2e: открытие карточек, переходы |
| `ui_verify.py` | Визуальная верификация 1280/375 + скриншоты |
| `sync_test_count.py` | `pytest --collect-only` → `version.json.tests` |

---

## 🛠️ Инструменты

| Скрипт | Что делает |
|---|---|
| `update_all.py` | Оркестратор: metrics → science → hedges_g → DOIs → index |
| `check_state.py` | Диагностика для старта сессии с AI |
| `rebuild_index.py` | Восстановление `index.json` из файлов на диске |
| `make_og.png` | Превью для соцсетей |
| `view_catalog.py` | Диагностика каталогов PubMed |
| `effect_tags_map.py` | **Импортируется**, не запускается. Источник правды для тегов |

---

## ⚠️ Не в git

Файлы, которые блокирует `.gitignore`:
- `scripts/_*.py` — временные диагностики
- `scripts/fix_*.py` — одноразовые патчи
- `scripts/diag_*.py` — диагностика
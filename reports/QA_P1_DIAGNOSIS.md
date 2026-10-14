# QA-P1-01 — диагностика скриптов без тестов (14.10.2026)

HEAD на момент диагностики: `8977285`. Задача — read-only: скрипты
не запускались и не менялись, тесты не писались.

## Главный вывод: цифра 16 не воспроизводится

| Метод подсчёта | Результат |
|---|---:|
| Как записано в аудите (QA-P1-01) | 16 |
| Grep по упоминанию имени скрипта в `tests/*.py` | **66** |
| Минус покрытие через артефакт (результат проверяется тестом) | **55** |
| Покрыто по имени | 20 |
| Покрыто через артефакт | 11 |

**Ни один метод не даёт 16.** Расхождение уже зафиксировано в
`reports/OPEN_EVERYTHING.md:211` — «QA-P1-01 „20 скриптов“ устарел →
F-44 „110 скриптов“». Реальная цифра лежит между: скриптов всего 86,
без теста — 55.

### Как считал

1. **По имени.** Для каждого `scripts/*.py` — есть ли его имя в `tests/*.py`.
   Ложное срабатывание почти невозможно (совпадение по границам слов).
2. **По артефакту.** Скрипт не упоминается в тестах, но пути, которые он
   пишет (`docs/data.json`, `docs/api/v1/*.json`, `docs/version.json`,
   `docs/data_ma_timeline.json`, `data/papers/papers_slim.json`),
   проверяются тестами. Формально это покрытие результата, не кода.
3. **Границы метода.** Покрытие по артефакту — верхняя оценка: у 4 из 11
   (`audit_meta_lengths.py`, `audit_content_gaps.py`, `_fix_reyshi.py`,
   `update_all.py`) артефакт упомянут в исходнике скрипта, а не как его
   вывод. Их стоит считать непокрытыми.

### Что это меняет

P1 «16 скриптов без тестов» — не 16 задач, а 55, из которых:

- **13** — тест реально нужен
- **8** — кандидаты на удаление как одноразовые
- **34** — WONTFIX: сетевые обёртки и исследовательские
  отчёты: тест требует живого API и проверяет не код, а доступность сети

Написать 55 тестов — не задача одного захода. Нужен выбор владельца.
Все 86 скриптов и пометки покрытия — в таблице «Полная таблица»,
арифметика 20 + 11 + 55 = 86 разобрана в разделе «Как читать таблицу».

## Приоритет: два артефакта живут на сайте без теста

| Скрипт | Артефакт | Кто читает |
|---|---|---|
| `build_interactions_graph.py` | `docs/interactions_graph.json` (50 КБ) | `interactions.html:384, 723, 1024, 1037` |
| `build_timeseries.py` | `docs/timeseries.json` (200 КБ) | `trends.html:416, 444, 1078` |

Критерий критичности: сбой генератора молча ломает страницу. У
`build_sup.py` и `build_feed.py` такой сбой ловится тестами, у этих двух — нет.

## Давность

Все 55 скриптов менялись в последний месяц (21.09–14.10.2026).
Мёртвого кода «старше года» нет — аргумент «это давно не нужно»
не работает ни для одного из них, кроме помеченных `Одноразовый`.

## Полная таблица

| Скрипт | Назначение | Класс | Решение |
|---|---|---|---|
| `add_supplements_batch.py` | Batch-добавление добавок из CSV. | Критический | **test** |
| `apply_drafts.py` | Финализация черновиков: _drafts.json → data.json (инкрементально). | Критический | **test** |
| `extract_g.py` | Кандидаты Hedges' g из абстрактов PubMed (данные цикла 4). | Критический | **test** |
| `extract_sample_sizes.py` | A3.5.3: Sample sizes из abstracts (и full texts). | Критический | **test** |
| `extract_stats_claims.py` | A3.5.4: Statistical claims из abstracts (p-values, CI, effect sizes). | Критический | **test** |
| `parse_dosages.py` | Парсер dosage из data.json → dosage_parsed.json. | Критический | **test** |
| `parse_xml_meta.py` | Парсит JATS XML из Europe PMC. Извлекает funding, COI, affiliations. | Критический | **test** |
| `rebuild_index.py` | Восстанавливает data/pmc/index.json из файлов на диске. | Критический | **test** |
| `recalc_science_index.py` | Пересчитывает rct, metaCount, scienceIndex для 81 карточки. | Критический | **test** |
| `apply_adv.py` | Применяет adv-поля (Q1.4) к data.json. | Критический | wontfix (артефакт) |
| `apply_mechs.py` | Применяет proposal mechs к data.json. | Критический | wontfix (артефакт) |
| `fetch_europepmc.py` | Скачивает full texts через Europe PMC REST API. | Критический | wontfix |
| `fetch_evidence.py` | Тянет abstracts из PubMed по key_sources карточки для верификации фактов. | Критический | wontfix |
| `fetch_evidence_abstracts.py` | Готовит заготовки reports/evidence/{id}.md с abstracts из PubMed. | Критический | wontfix |
| `fetch_fulltexts.py` | A3.2.3: Скачивание PDF + HTML-fallback + извлечение текста. | Критический | wontfix |
| `fetch_fulltexts_playwright.py` | A3.2.3-фаза-2: Playwright headful для PDF, где curl_cffi упал. | Критический | wontfix |
| `fetch_funders.py` | A3.6.1: Финансирование из CrossRef funders. | Критический | wontfix |
| `fetch_hedges_g.py` | Извлекает Hedges' g из abstracts МА для всех 81 карточки. | Критический | wontfix |
| `fetch_nlm_catalog.py` | A3.5.6: NLM Catalog (J_Medline.txt) — маппинг аббревиатур PubMed → полное название. | Критический | wontfix |
| `fetch_papers.py` | A3.1: Papers entity — все PMIDs по 94 добавкам. | Критический | wontfix |
| `fetch_pmcids.py` | Скачивает pmcid для всех papers через NCBI eutils esummary. | Критический | wontfix |
| `fetch_retractions.py` | A3.5.1b: Retractions через CrossRef batch — все retractions одним списком. | Критический | wontfix |
| `fetch_scimago.py` | A3.4.1: SCImago Journal Rank — метаданные журналов. | Критический | wontfix |
| `fetch_timeseries.py` | Time series: публикации по годам (PubMed esearch). | Критический | wontfix |
| `fetch_trials_links.py` | A3.5.2: ClinicalTrials mapping — NCT IDs из abstracts + full texts. | Критический | wontfix |
| `fetch_unpaywall.py` | A3.2.2: Unpaywall — OA-статус + прямые ссылки на PDF. | Критический | wontfix |
| `refresh_pmids.py` | Предлагает свежие PMIDs для устаревших key_sources. | Критический | wontfix |
| `apply_sources.py` | Переносит curated PMIDs из reports/sources_candidates.json в docs/data.json. | Критический | test ✓ |
| `migrate_key_sources.py` | v2.7.1: миграция key_sources из list[str] в единый list[dict]. | Критический | test ✓ |
| `validate_sources.py` | Периодическая валидация key_sources в docs/data.json через PubMed esummary. | Критический | test ✓ |
| `build_changelog_public.py` | _(docstring отсутствует)_ | Сборочный | **test** |
| `build_interactions_graph.py` | Строит docs/interactions_graph.json — граф связей для interactions.html. | Сборочный | **test** |
| `build_timeseries.py` | Собирает data/timeseries/*.json → docs/timeseries.json — единый файл для фронта. | Сборочный | **test** |
| `build_api.py` | Собирает публичный API из docs/data.json. | Сборочный | wontfix (артефакт) |
| `build_edu.py` | Сборка контента топ-10 для 15 блоков в docs/data.json из src/content.py (v2.3.1). | Сборочный | wontfix (артефакт) |
| `build_interactions.py` | Сборка interactions/synergists/antagonists в docs/data.json из src/content.py (v2.3). | Сборочный | wontfix (артефакт) |
| `build_ma_timeline.py` | v2.7-C1+C2: таймлайн мета-анализов PubMed по годам. | Сборочный | wontfix (артефакт) |
| `build_slim.py` | Создать slim-JSON для Streamlit Cloud. | Сборочный | wontfix (артефакт) |
| `enrich_design.py` | Определить study design из publication types. | Сборочный | wontfix |
| `enrich_doi_pmc.py` | Preprint из DOI prefix + PMC ID из index.json. | Сборочный | wontfix |
| `enrich_dois.py` | Обогащает key_sources DOI через PubMed esummary. | Сборочный | wontfix |
| `enrich_drafts.py` | Обогащает docs/_drafts.json из proposal. | Сборочный | wontfix |
| `enrich_papers.py` | A3.4.2: Дообогащение papers.json — MeSH, keywords, language, affiliation. | Сборочный | wontfix |
| `enrich_species.py` | Определить species из MeSH-терминов в papers. | Сборочный | wontfix |
| `enrich_trials.py` | A3.5.7: Обогащение NCT через ClinicalTrials.gov API v2. | Сборочный | wontfix |
| `join_scimago.py` | A3.5.5: Присоединить SCImago к papers. | Сборочный | wontfix |
| `sync_draft_terms.py` | Синхронизирует pubmed_term в _drafts.json с data_pubmed_terms.json. | Сборочный | wontfix |
| `build_effect_tags.py` | Собирает docs/effect_tags.json из scripts/effect_tags_map.py. | Сборочный | test ✓ |
| `build_feed.py` | Генератор docs/feed.xml (RSS 2.0). | Сборочный | test ✓ |
| `build_index.py` | Генерация docs/data_index.json — лёгкая проекция data.json. | Сборочный | test ✓ |
| `build_key_sources.py` | v2.6.1: автотоп-3 мета-анализов PubMed (ma_top3) + price_date из price_history. | Сборочный | test ✓ |
| `build_sitemap.py` | Генератор docs/sitemap.xml. | Сборочный | test ✓ |
| `build_sup.py` | Генератор страниц раздела sup из docs/data.json (v5.6.0, этапы 1-3). | Сборочный | test ✓ |
| `effect_tags_map.py` | Ручной маппинг карточка -> теги эффектов. | Сборочный | test ✓ |
| `fetch_metrics.py` | Обновляет wiki pageviews + citations в docs/data.json. | Сборочный | test ✓ |
| `graph_interactions.py` | Граф связей между добавками. | Сборочный | test ✓ |
| `make_trends_chart.py` | Графики трендов: публикации PubMed и Wikipedia-популярность. | Сборочный | test ✓ |
| `audit_meta_lengths.py` | Аудит длины SEO-мет: `<title>` 40–60, `meta description` 120–160. | Инфраструктурный | **test** (артефакт) |
| `validate_proposal.py` | Универсальный валидатор q14_batch_N_proposal.json. | Инфраструктурный | **test** |
| `check_state.py` | One-shot диагностика для старта сессии с AI. | Инфраструктурный | **delete** |
| `analyze_coi.py` | Анализ Conflict of Interest (COI) и funding в real full texts. | Инфраструктурный | wontfix |
| `analyze_crossref.py` | Сравнивает funders из CrossRef с Europe PMC XML. | Инфраструктурный | wontfix |
| `analyze_funding_v2.py` | Анализ funders v2 — с нормализацией и каноническими именами. | Инфраструктурный | wontfix |
| `audit_content_gaps.py` | Аудит пробелов в контенте data.json — какие поля не заполнены и у кого. | Инфраструктурный | wontfix (артефакт) |
| `audit_full.py` | Полный аудит: заполненность карточек + отображение на страницах. | Инфраструктурный | wontfix |
| `audit_links.py` | Watchdog битых ссылок: data.json + README. 429 от WB ≠ бита. | Инфраструктурный | wontfix |
| `audit_stale.py` | Квартальный аудит устаревших key_sources в data.json. | Инфраструктурный | wontfix |
| `review_evidence.py` | Ревью evidence-файлов: что нашли, релевантно ли, свежее ли. | Инфраструктурный | wontfix |
| `sync_test_count.py` | Считает число тестов и обновляет version.json. | Инфраструктурный | wontfix |
| `update_all.py` | Pipeline: обновление data.json за одну команду. | Инфраструктурный | wontfix (артефакт) |
| `verify_sup_diff.py` | Часть E: побайтовая сверка сгенерированных страниц с эталонными. | Инфраструктурный | wontfix |
| `audit_classes.py` | Инвентаризация классов и id: HTML / JS / CSS — основа для переименования. | Инфраструктурный | test ✓ |
| `build_approve_queue.py` | v2.4: approves-очередь — кандидаты Hedges' g из PubMed (мета-анализы). | Инфраструктурный | test ✓ |
| `check_snapshot_run.py` | Проверка, что снапшоты действительно выполнились, а не молча пропустились. | Инфраструктурный | test ✓ |
| `compress_snapshots.py` | Сжатие эталонов tests/snapshots/<движок>/*.PNG без потери пикселей. | Инфраструктурный | test ✓ |
| `e2e_smoke.py` | e2e-smoke (слой L4): сайт отдаёт то, что обещает data.json. | Инфраструктурный | test ✓ |
| `search_sources.py` | Поиск PMID через PubMed E-utilities для карточек без key_sources. | Инфраструктурный | test ✓ |
| `ui_verify.py` | UI-verify (ранбук шаг 5): noPrice/empty/toTop в живой вёрстке + скриншоты 1280/375. | Инфраструктурный | test ✓ |
| `_fix_reyshi.py` | Фикс Рейши: 36995543 (опечатка) → 36995535 (правильный). | Одноразовый | **delete** (артефакт) |
| `analyze_funding.py` | Анализ funders из data/processed/xml_meta.json. | Одноразовый | **delete** |
| `fill_upper_limit.py` | Заполняет пустые upper_limit у 61 карточки. | Одноразовый | **delete** |
| `make_og.py` | Создаёт docs/og.png — обложка для Хабра (780×440, светлая тема). | Одноразовый | **delete** |
| `patch_effects_batch14.py` | Одноразовый патч: добавляет effects в q14_batch_14_proposal.json. | Одноразовый | **delete** |
| `q1_3.py` | Q1.3: Обновление радара профиля — честные оси. | Одноразовый | **delete** |
| `refetch_evidence.py` | Перезапускает fetch_evidence_abstracts для конкретных добавок. | Одноразовый | **delete** |
| `view_catalog.py` | _(docstring отсутствует)_ | Одноразовый | **delete** |

`test ✓` — тест уже есть. `test` — тест нужен. `delete` — кандидат на
удаление. `wontfix` — тест не нужен.

## Как читать таблицу

В таблице 86 строк — все скрипты `scripts/`. Решения в них не равны
«сколько тестов надо написать»:

| Пометка | Скриптов | Значит |
|---|---:|---|
| `test ✓` | 20 | покрыт по имени — упомянут в `tests/*.py` |
| `(артефакт)` | 11 | покрыт по результату, не по коду |
| без пометки | 55 | **реально без теста** |

Решения по 55: **13 test / 8 delete / 34 wontfix**. Строки с пометкой
`(артефакт)` тоже несут решение, но в счёт 55 не идут — именно поэтому
сумма решений по таблице (14 + 9 + 43 = 66) больше, чем 55. У
четырёх из этих 11 артефакт упомянут в исходнике скрипта, а не как его
вывод, — их честнее считать непокрытыми, см. «Границы метода».

## Решения, которые требуют подтверждения перед удалением

`delete` поставлен не как готовое действие, а как кандидат:

- `analyze_funding.py` — заменён `analyze_funding_v2.py`; проверить,
  что v1 нигде не упоминается в отчётах.
- `check_state.py` — единственный, кто упомянут в `ROADMAP.md`;
  удаление сломает ссылку в документе.
- `fill_upper_limit.py`, `q1_3.py`, `patch_effects_batch14.py`,
  `_fix_reyshi.py` — разовые миграции, их работа уже в данных;
  проверить, что повторный запуск не нужен.

## Чего этот отчёт не делает

- Тестов не написано (по протоколу — стоп до решения владельца).
- Скрипты не запускались: сетевые требуют API-ключей, миграционные
  пишут `docs/data.json`.
- Классы «Критический/WONTFIX» для сетевых скриптов означают
  «важен для данных», а не «нужен тест».

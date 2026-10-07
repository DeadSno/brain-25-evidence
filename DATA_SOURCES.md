# Источники данных

Все данные — из открытых API. Никаких платных баз, никаких «серых» выгрузок.

**Принцип:** любой может повторить запрос и получить тот же результат.

> Файл актуализирован 2026-10-06: объёмы пересчитаны по артефактам в
> репозитории, добавлены источники, которые действительно опрашиваются
> (Unpaywall, Retractions), и вынесен раздел про производные слои. Что
> осталось непроверяемым, помечено прямо в тексте.

## 1. PubMed (NCBI E-utilities)

**Берём:** PMIDs, типы публикаций (MA, RCT), abstracts.

**Эндпоинты:**
- `esearch` — поиск PMIDs
- `esummary` — метаданные
- `efetch` — abstracts

**База:** `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

**Пример запроса (Креатин):**
```
db=pubmed
term=creatine[Title/Abstract] AND (meta-analysis[PT] OR randomized controlled trial[PT])
retmax=200
retmode=json
```

**Все 130 запросов:** `docs/data_pubmed_terms.json` (130 ключей, по одному на
добавку)

**ToS:** ≤3 req/s без API key, ≤10 с key, указывать `tool` + `email`.

**Код:** `scripts/fetch_metrics.py`, `scripts/fetch_papers.py`,
`scripts/fetch_hedges_g.py`, `scripts/fetch_evidence_abstracts.py`

## 2. OpenAlex

**Берём:** количество цитирований топ-1 источника каждой добавки.

**Эндпоинт:** `https://api.openalex.org/works/pmid:{PMID}`

**Параметры:** `select=id,doi,cited_by_count,publication_year`, `mailto=...` (polite pool).

**Лицензия:** CC0.

**Лимиты:** 100 000/день, 10/сек. Мы делаем ~130 запросов.

**Код:** `scripts/fetch_metrics.py`

## 3. Wikipedia REST API

**Берём:** просмотры страницы за последние 30 дней.

**Эндпоинт:**
```
https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{lang}/{title}/daily/{start}/{end}
```

**Пример:** `en.wikipedia/all-access/user/Creatine/daily/20260801/20260831`

**Лицензия:** CC BY-SA 3.0.

**Лимиты:** 100/сек, User-Agent обязателен.

**Код:** `scripts/fetch_metrics.py`

## 4. ClinicalTrials.gov

**Берём:** число активных испытаний (RECRUITING, ACTIVE_NOT_RECRUITING).

**Эндпоинт:** `https://clinicaltrials.gov/api/v2/studies`

**Параметры:** `query.term=...`, `filter.overallStatus=...`, `countTotal=true`.

**Лицензия:** Public domain (US Gov).

**Код:** `scripts/fetch_metrics.py`

## 5. DOI.org

**Берём:** метаданные DOI (title, journal, year) — для валидации `key_sources`.

**Эндпоинт:** `https://doi.org/{DOI}` + заголовок `Accept: application/vnd.citationstyles.csl+json`

**Код:** `scripts/enrich_dois.py`, `scripts/enrich_doi_pmc.py`

## 6. Europe PMC REST API

**Для чего:** полные тексты статей в формате JATS XML — секции Funding, COI, Methods.

**Endpoint:** `https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML`

**Объём (пересчитано 2026-10-06):** PMCID в `data/papers/pmcids.json` —
**11 176**; успешно разобранных записей в `data/pmc/index.json` — **11 933**;
файлов в `data/pmc/text/` — **11 934**. Разбор COI ограничен порогом
`threshold_bytes` = 20 000: XML получено **7 918**, в анализ попало
**6 310** (`reports/coi_report.json`).

> Прежние «5 059 полных текстов (из 11 175 PMCID)» не воспроизводятся ни по
> одному артефакту в репозитории: 5 059 не встречается ни в `pmcids.json`,
> ни в `index.json`, ни в отчёте COI. PMCID — 11 176, а не 11 175.

**ToS:** свободный доступ, рекомендуют email в User-Agent. Rate limit не публикуется, но вежливо — ≤2 req/s.

**Код:** `scripts/fetch_europepmc.py`, `scripts/fetch_pmcids.py`,
`scripts/fetch_fulltexts.py`, `scripts/parse_xml_meta.py`,
`scripts/analyze_coi.py`

## 7. CrossRef REST API

**Для чего:** метаданные DOI + funders (список организаций, финансировавших статью) + retracted-статьи.

**Endpoint:** `https://api.crossref.org/works/{DOI}`

**Объём:** `data/papers/funders.json` — **33 789** записей, из них с
непустым списком funders — **5 135**. `data/papers/retractions.json` —
те же **33 789** записей с флагом `is_retracted`.

**ToS:** свободный доступ, указать `mailto` в User-Agent. Rate limit — «вежливый пул», ~50 req/s.

**Код:** `scripts/fetch_funders.py`, `scripts/analyze_crossref.py`,
`scripts/fetch_retractions.py`

## 8. NLM Catalog (FTP)

**Для чего:** аббревиатуры названий журналов → полные названия. Нужно для матчинга SCImago.

**Источник:** `https://ftp.ncbi.nlm.nih.gov/pubmed/J_Medline.txt`

**Объём:** 38 048 аббревиатур

**Код:** `scripts/fetch_nlm_catalog.py`

## 9. SCImago Journal Rank (CSV)

**Для чего:** квартили Q1-Q4 для журналов.

**Источник:** `https://www.scimagojr.com/journalrank.php` (годовой CSV дамп)

**Объём:** 32 045 журналов — число из отчёта о выгрузке; **в репозитории
нет ни одного артефакта SCImago** (только сами скрипты
`fetch_scimago.py` и `join_scimago.py`), поэтому проверить его нечем.

**Лицензия:** CC BY-NC — только для некоммерческого использования, что ок для проекта.

**Код:** `scripts/fetch_scimago.py`

## 10. Unpaywall

**Для чего:** open-access статус статьи и прямая ссылка на полный текст.

**Endpoint:** `https://api.unpaywall.org/v2/{DOI}?email=...`

**Объём:** `data/papers/unpaywall.json` — **33 789** записей; с
определённым `oa_status` — **33 511**.

**Код:** `scripts/fetch_unpaywall.py`

## 11. PMC full texts + Unpaywall как fallback

**Для чего:** текст статьи, когда Europe PMC его не отдал. Именно этот путь
даёт большинство разобранных полных текстов: в `data/pmc/index.json`
11 933 из 11 934 записей имеют `source: rebuilt_from_disk`, то есть текст
восстановлен с диска Playwright-загрузками, а не получен одним запросом к
Europe PMC.

**Код:** `scripts/fetch_fulltexts.py`, `scripts/fetch_fulltexts_playwright.py`

## 12. Производные слои (не внешние источники)

Их нет в списке источников, но без них страница не работает — чтобы
README и этот файл не расходились:

| Артефакт | Что это | Кто строит |
|----------|---------|-----------|
| `docs/data.json` | 130 карточек, источник правды для всех страниц | `scripts/update_all.py` + ручная верификация |
| `docs/data_index.json` | лёгкая проекция для главной, 84 КБ из 732 КБ | `scripts/build_index.py` |
| `docs/sup/*.html` | 131 страница: 130 карточек + каталог | `scripts/build_sup.py` + `templates/*.j2` |
| `docs/graph_positions.json` | предрасчёт раскладки графа, 27 КБ | генератор v5.6.1 |
| `docs/api/v1/` | REST API + OpenAPI 3.0 + схемы | `scripts/build_api.py` |
| `data/db/brain.duckdb` | аналитическая база: `supplement` 130, `paper` 37 618, `interaction` 199, `supplement_tag` 226, `effect_tag` 18 | `scripts/db/import_to_duckdb.py` |
| `data/timeseries/` | ряды по годам: citations, pubmed, wiki | `scripts/fetch_timeseries.py` |

## Что НЕ используем

- **Cochrane Library** — платный доступ к полным обзорам
- **UpToDate** — платный
- **Google Scholar** — запрещает скрейпинг
- **Scopus / Web of Science** — платные
- **Wildberries / Ozon** — ToS запрещает автозапросы
- **Бренды БАДов** — маркетинг, не evidence

## Как воспроизвести

Полный пайплайн:
```bash
python scripts/update_all.py --apply
```

Отдельные шаги:
```bash
python scripts/fetch_metrics.py --all --apply                      # всё
python scripts/fetch_metrics.py --only citations --apply           # только OpenAlex
python scripts/fetch_metrics.py --only wiki --apply                # только Wikipedia
python scripts/fetch_metrics.py --only ongoing --apply             # только ClinicalTrials.gov
```

> Флага `--metrics` не существует — команда из предыдущей версии этого файла
> падала с ошибкой разбора аргументов. Проверено по
> `python scripts/fetch_metrics.py --help`: метрики выбираются через
> `--only {wiki,citations,ongoing}`.

Проверка одной добавки напрямую:
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=creatine[Title/Abstract]+AND+meta-analysis[PT]&retmode=json"
curl "https://api.openalex.org/works/pmid:34567890?mailto=test@example.com"
```

## Резервные копии

- Логи: `reports/update_all_<timestamp>.log` — **таких файлов в репозитории
  нет ни одного** (проверено 2026-10-06), то есть правило описано, но ни
  разу не сработало. Рабочий бэкап — GitHub Actions → Artifacts,
  инструкция в `ROADMAP.md`, строка техдолга 35.
- Snapshot: `tests/snapshot_data.json` (существует)
- История правок: `git log --oneline docs/data.json`
- Бакенд кеша PWA: `docs/sw.js` версии v414

## Юридический дисклеймер

Проект **не является медицинским советом**.

- PubMed abstracts могут содержать ошибки исходных статей
- Проверяем только метаданные — не каждый abstract вручную
- Verdict — авторская интерпретация, не заключение врача

Подробнее: `methodology.html` на сайте.

## Лицензии

- Код: MIT
- Данные: из открытых источников, используйте свободно с указанием источника
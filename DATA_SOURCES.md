# Источники данных

Все данные — из открытых API. Никаких платных баз, никаких «серых» выгрузок.

**Принцип:** любой может повторить запрос и получить тот же результат.

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

**Все 120 запросов:** `docs/data_pubmed_terms.json`

**ToS:** ≤3 req/s без API key, ≤10 с key, указывать `tool` + `email`.

**Код:** `scripts/fetch_metrics.py`

## 2. OpenAlex

**Берём:** количество цитирований топ-1 источника каждой добавки.

**Эндпоинт:** `https://api.openalex.org/works/pmid:{PMID}`

**Параметры:** `select=id,doi,cited_by_count,publication_year`, `mailto=...` (polite pool).

**Лицензия:** CC0.

**Лимиты:** 100 000/день, 10/сек. Мы делаем ~120 запросов.

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

**Код:** `scripts/enrich_dois.py`

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
python scripts/fetch_metrics.py --all --apply --metrics citations  # только OpenAlex
python scripts/fetch_metrics.py --all --apply --metrics wiki       # только Wikipedia
```

Проверка одной добавки напрямую:
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=creatine[Title/Abstract]+AND+meta-analysis[PT]&retmode=json"
curl "https://api.openalex.org/works/pmid:34567890?mailto=test@example.com"
```

## Резервные копии

- Логи: `reports/update_all_<timestamp>.log`
- Snapshot: `tests/snapshot_data.json`
- История правок: `git log --oneline docs/data.json`

## Юридический дисклеймер

Проект **не является медицинским советом**.

- PubMed abstracts могут содержать ошибки исходных статей
- Проверяем только метаданные — не каждый abstract вручную
- Verdict — авторская интерпретация, не заключение врача

Подробнее: `methodology.html` на сайте.

## Лицензии

- Код: MIT
- Данные: из открытых источников, используйте свободно с указанием источника
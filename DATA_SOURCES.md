Источники данных
Все данные в проекте — из открытых источников. Никаких платных баз, никаких «серых» выгрузок.

Принцип: любой читатель может повторить запрос и получить тот же результат.

Сводная таблица
Источник	Что берём	API	Лицензия / ToS	Файлы
PubMed (NCBI)	PMIDs, метаданные статей, abstracts, типы публикаций	E-utilities (esearch, esummary, efetch)	Public domain (US Gov), NCBI ToS	data/raw/pubmed_evidence.csv, docs/data_pubmed_terms.json
OpenAlex	Цитирования (cited_by_count)	REST API v1	CC0 (public domain)	в data.json → citations
Wikipedia	Просмотры страниц (pageviews)	REST API (/metrics/pageviews)	CC BY-SA 3.0	в data.json → wiki_views
ClinicalTrials.gov	Активные испытания	API v2 (/api/v2/studies)	Public domain	в data.json → ongoing
DOI.org	Метаданные DOI (для key_sources)	Content Negotiation	Открытый	в data.json → key_sources[].doi
1. PubMed / NCBI E-utilities
Что берём:

PMIDs по поисковым запросам (81 запрос — по одному на добавку)

Тип публикации: Meta-Analysis, Randomized Controlled Trial, Review

Abstract (для ручного анализа)

Эндпоинты:

text
esearch:  https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
esummary: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi
efetch:   https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
Параметры запроса (пример для Креатина):

text
db=pubmed
term=creatine[Title/Abstract] AND (meta-analysis[PT] OR randomized controlled trial[PT])
retmax=200
retmode=json
Все 81 запроса лежат в docs/data_pubmed_terms.json — их можно перепроверить вручную.

ToS: NCBI просит:

не более 3 запросов/сек без API key

не более 10 запросов/сек с API key

указывать tool и email в запросе

Наш код это соблюдает — см. scripts/fetch_metrics.py.

Ограничения:

PubMed не отдаёт полный текст — только abstract

Ретракции не отслеживаются автоматически

2. OpenAlex
Что берём:

Количество цитирований для топ-1 ключевого источника каждой добавки

Эндпоинт:

text
https://api.openalex.org/works/pmid:{PMID}
Параметры:

text
select=id,doi,cited_by_count,publication_year
mailto=your@email  # вежливое использование (polite pool)
Лицензия: CC0 — данные в public domain.

Лимиты: 100 000 запросов/день, 10 запросов/сек. Мы делаем ~81 запрос — с запасом.

Код: scripts/fetch_metrics.py

3. Wikipedia REST API
Что берём:

Просмотры страницы добавки за последние 30 дней (интерес аудитории)

Эндпоинт:

text
https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{lang}/{title}/daily/{start}/{end}
Пример (Креатин, en.wikipedia):

text
en.wikipedia/all-access/user/Creatine/daily/20260801/20260831
Лицензия: CC BY-SA 3.0 для контента, метрики — открытые.

Лимиты: 100 запросов/сек на IP, с User-Agent обязателен.

Код: scripts/fetch_metrics.py

4. ClinicalTrials.gov
Что берём:

Число активных испытаний по добавке (статус: RECRUITING, ACTIVE_NOT_RECRUITING)

Эндпоинт:

text
https://clinicaltrials.gov/api/v2/studies
Параметры:

text
query.term=creatine
filter.overallStatus=RECRUITING|ACTIVE_NOT_RECRUITING
countTotal=true
Лицензия: Public domain (US Gov).

Лимиты: нет жёстких, но есть rate limit 50/сек.

Код: scripts/fetch_metrics.py

5. DOI.org
Что берём:

Метаданные DOI (title, journal, year) для валидации key_sources

Эндпоинт:

text
https://doi.org/{DOI}
Accept: application/vnd.citationstyles.csl+json
Лицензия: открытая.

Код: scripts/enrich_dois.py

Что НЕ используем (и почему)
Источник	Почему нет
Cochrane Library	Платный доступ к полным обзорам
UpToDate	Платный
Google Scholar	Запрещает скрейпинг, ToS нарушать не будем
Scopus / Web of Science	Платные
Роспотребнадзор / РЛС	Нет открытых API
Wildberries / Ozon	ToS запрещает автоматические запросы
Бренды БАДов	Маркетинговые данные, не evidence
Как воспроизвести
Полный пайплайн
bash
python scripts/update_all.py --apply
Это последовательно дёргает 4 источника: PubMed → OpenAlex → Wikipedia → ClinicalTrials → DOI.

Отдельные шаги
bash
# Только PubMed-метрики
python scripts/fetch_metrics.py --all --apply

# Только цитирования (OpenAlex)
python scripts/fetch_metrics.py --all --apply --metrics citations

# Только Wikipedia pageviews
python scripts/fetch_metrics.py --all --apply --metrics wiki
Прямая проверка одной добавки
bash
# 1. PMIDs
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=creatine[Title/Abstract]+AND+meta-analysis[PT]&retmode=json"

# 2. Цитирования
curl "https://api.openalex.org/works/pmid:34567890?mailto=test@example.com"

# 3. Просмотры
curl "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Creatine/daily/20260801/20260831"
Резервные копии
Каждый прогон update_all.py пишет лог в reports/update_all_<timestamp>.log.

Snapshot data.json — в tests/snapshot_data.json. Любое изменение фиксируется в git.

История данных: git log --oneline docs/data.json — полная история правок.

Юридический дисклеймер
Проект не является медицинским советом. Все данные — из открытых публикаций, но:

PubMed abstracts могут содержать ошибки в исходных статьях

Мы не проверяем каждую статью вручную — только метаданные

Verdict — авторская интерпретация, не заключение врача

См. methodology.html на сайте — там полное описание методологии.

Как сообщить о проблеме с источником
Если нашли:

Битая ссылка в key_sources → issue

PMID не существует → issue с тегом data-error

Нарушение ToS в нашем коде → issue с тегом bug — это серьёзно

Лицензия данных
Все данные — из открытых источников. Наш код — MIT. Данные в data.json можно использовать свободно с указанием источника.
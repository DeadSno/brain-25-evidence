# AUDIT B (S3) — python + CI + секреты
Дата: 2026-09-13 | скрипт: scripts/audit_secrets.py | файлы НЕ менялись

## Шапка
| Severity | Кол-во |
| --- | --- |
| 🔴 | 1 |
| 🟡 | 3 |
| 🟢 | 4 |

## Топ-5
- 🔴 **парсеры**: openalex_count: `except Exception: return -1` — маскирует 429/500/timeout как данные  `src/parsers.py:53-54 (и +51 try)`
- 🟡 **парсеры**: нет ретраев/backoff у: pubmed_count(), openalex_count(), wb_search() (429/500/таймаут = падение или -1)  `parsers.py:22; parsers.py:46; parsers.py:64`
- 🟡 **CI**: tests.yml: push не включает ветки ['v2.1-dev', 'v2.0-dev'] — CI не гоняется на них  `.github/workflows/tests.yml:4`
- 🟡 **CI**: pip install зависимостей без версий — воспроизводимость  `collect_prices.yml:26`
- 🟢 **хардкод**: магические константы в src (часть — конфиг-значения): 1  `WB dest=-1257786 (магическое число региона)`

## Инфо
- PubMed E-utilities: pubmed_count() в parsers.py:22; никогда не вызывается с ретраем; для 429/500 — падение или -1.
- OpenAlex: openalex_count() в parsers.py:46; никогда не вызывается с ретраем; для 429/500 — падение или -1.
- Wildberries search: wb_search() в parsers.py:64; никогда не вызывается с ретраем; для 429/500 — падение или -1.
- parsers.py использует только `raise_for_status()` — явных except-типов нет (кроме широкого голого).
- seed/random в src/scripts не используются — детерминизм от порядка словарей.
- порядок словарей config.py фиксирован (dict 3.7+); data.json стабилен (снапшот-тест).
- collect_prices.py: append идемпотентен — drop_duplicates по (дата,добавка,источник).
- timestamp (`дата`=strftime, снапшот UPDATE_SNAPSHOT) — by design по брифу, не баг.
- collect_prices.py: пути через Path(__file__) или относительные от корня — ок.
- serve.py: порт из аргумента с дефолтом 8000 — ок (не хардкод).
- тестов: 8 файлов, 25 функций: test_add_month_price, test_all_dicts_81, test_categories_few_offers, test_data_and_config_in_sync, test_data_json_valid, test_files_present, test_freshness, test_garden_filter, test_ids_unique, test_keys_consistent, test_mg_is_not_grams, test_no_zero_science_index, test_parse_units_caps, test_parse_units_grams, test_processed_ok, test_ranges_sane, test_required_fields, test_savings, test_schema_fields_and_types, test_set_is_not_dose, test_snapshot_unchanged, test_verdict_consistency, test_wb_alive, test_wb_ranges_and_coverage, test_wb_schema
- happy path есть: parse_units(г/капс/табл), GARDEN-фильтр, цена_мес, категории, savings, schema, sync config-data, snapshot.
- network-тесты исключены: pytest.ini addopts=-m 'not network' (marker network).
- collect_prices.yml: permissions contents:write (минимально для push), concurrency: есть.
- collect_prices.yml: git pull --rebase перед push — защита от гонок (по документу).
- tests.yml: permissions не заданы — дефолт read (ок).
- actions протегированы (не SHA): actions/checkout@v4, actions/setup-python@v5 — ок для малого проекта.
- collect_prices.yml cron: ['0 3 * * *'] (README: 06:00 МСК = 03:00 UTC — совпадает).
- notebooks: токенов не найдено.
- wb_search: UA браузеро-подобный + timeout=15 — вежливо.
- collect_wb_prices: sleep(1.0) между запросами — вежливость соблюдена (см. тесты reco #5).
- raise_for_status() присутствует (быстрый фейл на 4xx/5xx).

## Находки (≤25)
🟡 парсеры: нет ретраев/backoff у: pubmed_count(), openalex_count(), wb_search() (429/500/таймаут = падение или -1)  `parsers.py:22; parsers.py:46; parsers.py:64`
🔴 парсеры: openalex_count: `except Exception: return -1` — маскирует 429/500/timeout как данные  `src/parsers.py:53-54 (и +51 try)`
🟢 хардкод: магические константы в src (часть — конфиг-значения): 1  `WB dest=-1257786 (магическое число региона)`
🟢 типхинты: type hints у 9/11 функций; docstrings ≈8  `__init__.py=0/0; config.py=0/0; content.py=0/0; economics.py=4/4; parsers.py=5/7; collect_prices.py=0/0; serve.py=0/0`
🟢 тесты: предложено 5 новых тестов (happy-path есть):  `1) wb_search: фикстура JSON → цена_руб=копейки/100 (сейчас network-marker, offline не покрыт); 2) collect_prices.append: повторный запуск не дублирует (drop_duplicates) — с фикстурой истории; 3) openalex_count: mock HTTPError → возврат -1 и НЕ падение (зафиксировать семантику); 4) serve.py: GET / и GET /data.json через real HTTP server (без браузера); 5) parsers: вежливость — между wb_search вызовами ≥0.9s (регрессия сна, т.к. сейчас sleep=1.0)`
🟡 CI: tests.yml: push не включает ветки ['v2.1-dev', 'v2.0-dev'] — CI не гоняется на них  `.github/workflows/tests.yml:4`
🟡 CI: pip install зависимостей без версий — воспроизводимость  `collect_prices.yml:26`
🟢 секреты: токенов (ghp_/xox/botXXX: и пр.) в .py/workflows/NOT-документах не найдено — после эксклюзии id метрики  ``

# AUDIT A (S1) — карта проекта + данные
Дата: 2026-09-13 | скрипт: scripts/audit_data.py | файлы НЕ менялись

## Шапка
| Severity | Кол-во |
| --- | --- |
| 🔴 | 0 |
| 🟡 | 1 |
| 🟢 | 1 |

## Топ-5
- 🟡 **данные**: value=scienceIndex/(price/100) аномалии (>1000 или <1): 5  `Ежовик: sci=4 price=539 → value=0.7; Аргинин: sci=2 price=230 → value=0.9; Чеснок: sci=1 price=318 → value=0.3; Лютеин + зеаксантин: sci=3 price=536 → value=0.6; Трибулус: sci=2 price=666 → value=0.3`
- 🟢 **мёртвый код (эвристика)**: src\parsers.py: openalex_count (использований вне файла: 0) — CANDIDATE, не верифицировано — CANDIDATE, не верифицировано  ``

## Инфо-строки
- data.json ГЕНЕРИРУЕТСЯ в: notebooks\02_analysis.ipynb:1484 — генератор (data.json + write)
- data.json: 81 записей, JSON валиден.
- id уникальны (81/81).
- обязательные поля: все присутствуют у всех 81.
- price=0: нет (price=null ок).
- scienceIndex=0: нет.
- config синхрон: SUPPLEMENTS == id data.json.

## 1. Кто генерирует data.json
- notebooks\02_analysis.ipynb:1484 — генератор (data.json + write)

## 2. Мёртвый код (эвристика, кандидаты на ручную проверку)
- src\parsers.py: openalex_count (использований вне файла: 0) — CANDIDATE, не верифицировано

## 3. Находки (≤25)
🟢 мёртвый код (эвристика): src\parsers.py: openalex_count (использований вне файла: 0) — CANDIDATE, не верифицировано — CANDIDATE, не верифицировано  ``
🟡 данные: value=scienceIndex/(price/100) аномалии (>1000 или <1): 5  `Ежовик: sci=4 price=539 → value=0.7; Аргинин: sci=2 price=230 → value=0.9; Чеснок: sci=1 price=318 → value=0.3; Лютеин + зеаксантин: sci=3 price=536 → value=0.6; Трибулус: sci=2 price=666 → value=0.3`

## 4. Эвристика вердиктов — СПИСОК НА РУЧНУЮ ПРОВЕРКУ (не баги)
- Витамин D: вердикт=зависит от контекста, scienceIndex=610
- B12: вердикт=зависит от контекста, scienceIndex=374
- Бакопа: вердикт=работает, scienceIndex=36
- Гинкго: вердикт=не подтверждено, scienceIndex=380
- Ашваганда: вердикт=работает, scienceIndex=21
- Цинк: вердикт=зависит от контекста, scienceIndex=318
- Тирозин: вердикт=зависит от контекста, scienceIndex=459
- Витамин C: вердикт=зависит от контекста, scienceIndex=747
- Пробиотики: вердикт=зависит от контекста, scienceIndex=2059
- Железо: вердикт=зависит от контекста, scienceIndex=1873
- Глюкозамин + хондроитин: вердикт=не подтверждено, scienceIndex=182
- L-карнитин: вердикт=зависит от контекста, scienceIndex=804
- Кальций: вердикт=зависит от контекста, scienceIndex=425
- Гиалуроновая кислота: вердикт=зависит от контекста, scienceIndex=2168
- Имбирь: вердикт=работает, scienceIndex=44
- Рибофлавин: вердикт=работает, scienceIndex=5
- Глутамин: вердикт=зависит от контекста, scienceIndex=437
- Босвеллия: вердикт=работает, scienceIndex=38

## 5. Дерево проекта (без .git/__pycache__/.pytest_cache/node_modules)
```
.github\ISSUE_TEMPLATE\data-error.md
.github\workflows\collect_prices.yml
.github\workflows\tests.yml
.gitignore
CHANGELOG.md
conftest.py
data\processed\.gitkeep
data\processed\clinical_trials_v12.csv
data\processed\evidence_scored.csv
data\processed\evidence_scored_v12.csv
data\processed\evidence_v12_raw.csv
data\processed\meta_catalog.csv
data\processed\pubmed_v12.csv
data\processed\s2_enrich.csv
data\processed\verdict_sources.csv
data\processed\verdict_sources_merged.csv
data\processed\verdict_sources_v12.csv
data\raw\.gitkeep
data\raw\prices_raw.xlsx
data\raw\prices_wb.xlsx
data\raw\prices_wb_history.csv
data\raw\prices_wb_v12.csv
data\raw\pubmed_evidence.csv
data\raw\wb_demand.csv
docs\audit\01-map-data.md
docs\data.json
docs\index.html
docs\map.html
docs\MASTER_RUNBOOK.md
docs\og.png
docs\robots.txt
docs\script.js
docs\sitemap.xml
docs\STATE.md
docs\style.css
docs\yandex_5be625a48583d1d7.html
docs\yandex_a41573a4e2cef456.html
LICENSE
notebooks\.gitkeep
notebooks\01_collect.ipynb
notebooks\01_evidence_pubmed.ipynb
notebooks\02_analysis.ipynb
notebooks\03_economics.ipynb
notebooks\lib\bindings\utils.js
notebooks\lib\tom-select\tom-select.complete.min.js
notebooks\lib\tom-select\tom-select.css
notebooks\lib\vis-9.1.2\vis-network.css
notebooks\lib\vis-9.1.2\vis-network.min.js
pytest.ini
README.md
reports\.gitkeep
reports\article_draft.md
reports\bubble_chart.png
reports\heatmap_tiers.png
reports\mechanism_graph.html
reports\mechanism_graph_v2.html
reports\mechanism_graph_v3.html
reports\mechanism_graph_v4.html
reports\rct_chart.png
reports\supplement_map.png
reports\trends_vs_evidence.png
reports\waterfall_savings.png
requirements.txt
scripts\audit_data.py
scripts\collect_prices.py
serve.py
src\.gitkeep
src\__init__.py
src\config.py
src\content.py
src\economics.py
src\parsers.py
tests\snapshot_data.json
tests\test_config.py
tests\test_config_sync.py
tests\test_data_quality.py
tests\test_economics.py
tests\test_parsers.py
tests\test_schema.py
tests\test_site_data.py
tests\test_snapshot.py
```

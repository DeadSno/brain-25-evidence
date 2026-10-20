# FIX-SPRINT B6 (v5.6.5) — синхронизация данных и документации

Дата: 2026-10-20. Ветка: `v5.6.5-dev`. Старт: `87b0d6a`. Коммит: **`3f212ead`**.

## Цель

Устранить расхождение «данные ↔ артефакты ↔ документация» после пересчёта
грейдов (Блок 1): собрать API/DB/граф/страницы, обновить дока-базалинию
на v5.6.5 (1979 тестов) и вычистить ссылки на удалённые гейты `RUN_*`.

## Данные

| Правка | Было | Стало |
|---|---|---|
| Омега-3 (~стр. 133) | `citations: null` | `citations: 0` |
| Лаванда (~10571) | forms «масло в капсулах (Silexan)» | «экстракт (стабилизированное лавандовое масло, Silexan)», grade C |
| MSM (~11397) | «порошок или капсулы (optiMSM)» | «порошок (optiMSM)» |
| S. boulardii (~13526) | grade B | grade D (hedges_g = −1.63 ≤ 0) |

Пересборка артефактов после правок (`python scripts/build_*.py`):

- `docs/api/v1/supplements.json` (130 карточек, ~652 KB) + `index.json`;
- `docs/data_index.json` (86.4 KB);
- `docs/graph_data.json` (130 nodes / **1983 edges**) + `graph_positions.json`;
- 131 страница `docs/sup/*.html` + `docs/sup/index.html`;
- `docs/methodology.html` — счётчики грейдов: **B 22 (16.9%), D 50 (38.5%)**;
- `tests/snapshot_data.json` (UPDATE_SNAPSHOT=1 — правка данных осознанная);
- `tests/snapshots/{chromium,webkit}/methodology-412.png` (UPDATE_SNAPSHOTS="methodology-412");
- `data/db/brain.duckdb` (вне git): `import_to_duckdb.py` пересоздал БД —
  supplement 130, paper 37618, coi 6310; грейды = A 6 / B 22 / C 52 / D 50.

## Документация

- **README.md**: статус v5.6.5 (было v5.6.3), 1979 тестов в 73 файлах
  (было 1079/47), грейды A6/B22/C52/D50, hedges' g 89/130 (85 с CI),
  143 URL в sitemap, atlas/graph — noindex-редиректы на
  `interactions.html`, в структуре добавлены compare.html и privacy.html.
- **CHANGELOG.md**: в [v5.6.5] добавлены пункты по данным, requirements
  (+Pillow), чисткам lib/, .gitignore и секция ### Docs.
- **ROADMAP.md**: PMID counter и Compare 3+ отмечены ✅ ([6051419] — были
  реализованы, но не чекались).
- **CONVENTIONS.md / SKILLS_INDEX.md / CONTRIBUTING.md / docs/dev/AGENTS.md /
  qa-deep-audit/SKILL.md**: базовая линия тестов «1746+237 / 736+18 /
  790+2» → **1979 passed, 0 skipped (~8 мин)**; все упоминания opt-in
  гейтов `RUN_SNAPSHOTS/A11Y/TABS/GRAPH/MOBILE/E2E` (удалены в v5.6.5 из
  `tests/conftest.py`) обновлены; описан автостарт live_server.
- **tests/test_*.py** (a11y/tabs/mobile/snapshots/ui_verify),
  **scripts/check_snapshot_run.py**, **.github/workflows/tests.yml** —
  докстринги и примеры команд без устаревших `RUN_*`.

## Инфраструктура

- `.gitignore` + паттерны артефактов (`*.json.gz`, `snap_head_*.xml`,
  `reports/archive/v26*.png`, прогоны `pytest_*.txt`/`db_import_log.txt`).
- `requirements.txt`: + Pillow.
- Удалены: `lib/vis-9.1.2`, `lib/tom-select`, `scripts/view_catalog.py`,
  `.gcourer/`, `logs/_idx_old.png` (из них tracked был только
  view_catalog.py).
- В `reports/archive/`: AUDIT_MASTER.md, AUDIT_MASTER_v565.md,
  docs/reports/screenshots/*.png (git mv), 16 PNG ui/v26* (untracked).
- `git gc`: объекты уже упакованы — 18397 в 2 паках (~975 MB), loose 0.

## Инцидент: двойное зависание полного прогона

Прогоны #3 и #4 `pytest -q` (фоновые) висели на ~17–18% на тесте
`test_graph_interaction.py::test_canvas_has_ink` (дельта CPU
pytest→node→chrome-headless = 0). **Изолированно тот же тест — 2 passed
за 6.2 с**: сам тест не сломан. Вероятная причина — `pg.evaluate(INK_JS)`
в Playwright Python не имеет таймаута, а hang — феномен полного прогона
под нагрузкой; повторно после kill-а всех фоновых процессов не
воспроизвёлся. Фон #5 прошёл целиком. Возможная профилактика на будущее:
обёртка evaluate с таймаутом или переупорядочивание браузерных тестов.

## Верификация

- Полный `pytest -q`: **1979 passed, 0 failed, 0 skipped, 483.95 с** —
  совпадает с `docs/version.json` (`"tests": 1979`).
- pre-commit (дважды, включая amend): build_sitemap/junk guard/feed/
  graph/timeseries/graph --check/pytest-фильтр → 1762 passed.
- Коммит: `3f212ead` (35 файлов, +198/−197).

## Остаточное

- git-тег v5.6.5 не ставится (решение владельца: «main не трогаем, теги не ставим»).
- Hang `pg.evaluate` без таймаута — вне этого спринта (см. выше).

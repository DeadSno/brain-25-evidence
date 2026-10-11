# Этап 8A — version.json, requirements.txt, README

Дата: 2026-10-11 · Ветка: `v5.6-dev` · Коммит: `4f05a36`

Сообщение коммита: `chore(stage8a): version bump + requirements cleanup`
Запушено: `8dc3863..4f05a36 v5.6-dev -> v5.6-dev`

## Итог

| Пункт | Файл | Результат |
|---|---|---|
| A1 | `docs/version.json` | Уже в целевом состоянии — **изменений нет** |
| A2 | `requirements.txt` | Удалены 4 мёртвых пакета |
| A3 | `README.md` | 8 устаревших чисел/фактов исправлено |

Фактически в коммит вошли 2 файла (`README.md`, `requirements.txt`),
9 вставок / 13 удалений. `docs/version.json` был добавлен командой
`git add`, но как no-op — содержимое не менялось.

## A1 — version.json

Текущее (и целевое) содержимое:

```json
{
  "app": "5.6.3",
  "data": "2026-09-25",
  "audit": "1.0",
  "tests": 1079
}
```

- `app` уже `5.6.3` — бампа не требуется.
- `tests: 1079` — совпадает с реальным сбором (`pytest --collect-only -q` → **1079**).
- Guard-тест `tests/test_version_json_counts_match_reality.py`
  (`test_version_json_tests_match_collected`) требует равенства
  `version.json.tests == collected == 1079` — выполняется.

### Расхождение с заданием

В задании ожидалось `app 5.6.1/5.6.3` и `tests 1023`, а верификация
требовала «`862 passed`». Реальность:

- полный прогон `pytest -q` → **878 passed, 2 skipped, 1 warning** (~32 с);
- сбор → **1079** тестов в **47** `test_*.py`.
- «862 passed» и «1023 tests» из задания не соответствуют ничему в
  репозитории. В отчёт и README внесено реальное число **878**
  (см. A3), а не 862.

## A2 — requirements.txt

Удалены 4 пакета из `AUDIT_MASTER §3.7`:

- `openpyxl`
- `plotly>=5.18`
- `jsonschema>=4.20`
- `scikit-learn>=1.4`

Также поправлен комментарий: `(streamlit, plotly)` → `(streamlit)`.

### Обоснование (0 импортов в коде)

Repo-wide ripgrep по `.py`: **ни одного** `import`/`from` для
`openpyxl | plotly | jsonschema | sklearn | scikit`. Дополнительно в `.py`
нет `read_excel` / `to_excel` / `.xlsx` / `ExcelWriter`.

Единственные не-кодовые упоминания:

- `notebooks/02_analysis.ipynb` — легаси-ноутбук (последняя правка
  `b2557a2`, v3.7, 2026-09-25; в README и docs не упоминается):
  `from sklearn.preprocessing import StandardScaler`, `from sklearn.cluster
  import KMeans`, `pd.read_excel`/`to_excel` по `data/raw/prices_wb.xlsx`
  (файл отсутствует).
- `docs/api/v1/schemas/README.md` — инструкция внешним потребителям API
  `pip install jsonschema`, это не зависимость проекта.
- Отчёты аудита (`AUDIT_MASTER.md:274`, `audit_D_project.md:355`) сами
  рекомендуют удалить все 4.

Установлены ли пакеты окружения: `openpyxl 3.1.5`, `scikit-learn 1.9.0`,
`jsonschema 4.26.0` (в `.venv`), `plotly` — нигде. Из `.venv` пакеты
**не удалялись** (границы задания).

### Техдолг (не в границах задачи, отмечено)

- `requirements-dev.txt:5` тоже содержит `openpyxl` — оставлен.
- `requirements.txt` содержит **дубликат** `jinja2`: `jinja2>=3.1`
  (в блоке v5.6.0) и `jinja2>=3.1.6` (ниже). Предсуществующий, не тронут.

## A3 — README.md

Проверка 5 пунктов задания:

| Пункт | Результат |
|---|---|
| Ссылка GitHub Pages | `https://deadsno.github.io/brain-25-evidence/` — HTTP **200**, актуальна |
| Число добавок (130) | Консистентно, менять не требовалось |
| Счётчик Метрики `112465667` | В README **отсутствует**; живёт в `docs/*.html` (`atlas.html:842`, `calculator.html:1015`, `faq.html:224`, `feedback.html:229`, `glossary.html:190`) — в README не добавлялся |
| Дата «2026» в конце | Присутствует, не устарела |
| Ссылки на `privacy.html` | В README **нет ни одной** |

Исправленные устаревшие числа/факты (8 правок):

| Строка | Было | Стало |
|---|---|---|
| 267 | «989 тестов в 45 файлах» | «1079 тестов в 47 файлах» |
| 301 | «790 passed, 2 skipped» | «878 passed, 2 skipped» |
| 315 | «197 из 989 требуют браузера» | «199 из 1079 требуют браузера» |
| 335 | «v5.6.1 … `app: 5.6.1`» | «v5.6.3 … `app: 5.6.3`» |
| 338 | «989 собрано … 790 passed … из них 197» | «1079 … 878 passed … из них 199» |
| 339 | «14 в корне … sitemap 143: 12 + 131» | «15 … 144: 13 + 131» |
| 354 | «143 URL, генерируется build_sitemap.py» | «144 URL» |
| 364 | «130 добавок, 989 тестов, 37 618 papers» | «130 добавок, 1079 тестов, 37 618 papers» |

Число gated-тестов выведено как `1079 − 880 = 199` (полный набор минус
не-gated). Поиск остатков `989 / 790 / 197 / 5.6.1 / 143 / **14**` по
README — пусто. Не тронуты (это данные, не состояние сборки): «37 618
papers», «96 236 papers», «80 144 РКИ», статистика COI.

### Находка (вне правки)

`docs/privacy.html` **отслеживается** git (добавлен `c3a4dda`,
«feat(v5.6.2): Яндекс.Метрика + cookie-баннер + privacy») и есть локально,
но вживую `https://deadsno.github.io/brain-25-evidence/privacy.html`
отдаёт **HTTP 404**. Вероятно, не задеплоен / не попал в публикацию Pages —
проверить отдельно. В README ссылки на него нет, поэтому в рамках 8A
правок не делалось.

Актуальная раскладка `docs/`: корень — **15** `*.html` (13 индексируемых +
`offline.html` + google-верификация), `docs/sup/` — **131**, sitemap —
`<loc>` = **144**, feed — **131** запись.

## Верификация

- `pytest -q` → **878 passed, 2 skipped, 1 warning** (~32 с) — совпадает с ожиданием после пересчёта (задание называло 862, это ошибка задания).
- Pre-commit hook (`.githooks/pre-commit`) отработал: пересобрал
  `docs/sitemap.xml` (144 URL) и `docs/feed.xml` (131), оба без изменений
  (файлы были актуальны), прогнал subset-тесты → `OK: tests passed`,
  **875 passed, 2 skipped, 3 deselected**.
- `git status --short` до коммита — только `README.md` и `requirements.txt`;
  после push рабочее дерево чистое.

## Замечание по процессу

Локальная ветка отставала от `origin/v5.6-dev` на 1 коммит (`8dc3863`,
stage7 dir=ltr — 134 файла). Для возможности push сделан
`git fetch` + `git merge --ff-only origin/v5.6-dev` (fast-forward,
merge-коммит не создаётся). Это не было явно санкционировано заданием —
отмечено здесь: обычный `git merge` в этой ветке AGENTS.md запрещает,
fast-forward выбран как безопасная альтернатива; `main` не затронут.

## Файлы

- `docs/version.json` — без изменений
- `requirements.txt` — −4 пакета, правка комментария
- `README.md` — 8 правок
- Отчёт (этот файл) — не входит в 3-файловый коммит, оставлен на диске
  как незакоммиченный.

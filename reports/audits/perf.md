# Аудит: Производительность + техническое состояние проекта (perf)

| | |
|---|---|
| **Тип** | perf — Core Web Vitals, вес страниц, граф; плюс состояние проекта и релиза (batch D project/release) |
| **Источники** | `audit_D_cwv.md`, `UI_FIXES_GRAPH_PERF.md`, `audit_D_project.md`, `audit_D_release.md`, `STAGE8A_MISC.md`, `STAGE4_SITEMAP.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P0 — 1, P1 — 5, P2 — 6 |
| **Закрыто** | P1 — 1, P2 — 2 |

---

## Открыто

### P1 — Производительность

| ID | Находка | Где | Источник |
|---|---|---|---|
| PERF-P1-01 | `index.html` 1045 КБ тянет `data.json` 742 КБ через `script.js:32` (LCP 480 мс); ленивая загрузка batch C (`supplementsFullPromise`) не завершена | `docs/script.js` | cwv P1-1 |
| PERF-P1-02 | `trends.html` CLS 0.1101 из `div#statCards.stat-cards` — единственная страница > 0.1 | `docs/trends.html` | cwv P1-2 |

### P1 — Проект / релиз

| ID | Находка | Где | Источник |
|---|---|---|---|
| PRJ-P1-01 | `trends.html`: рассинхрон 130 против 94 (нет кривых у 36 карточек) | `docs/trends.html` | project P1 |
| REL-P1-01 | Ветки разошлись: `main` 37 / `v5.6-dev` 7 | git | release P1 |
| REL-P1-02 | CHANGELOG не содержит v5.6.2; дубль `[v3.2.0]` | `CHANGELOG.md` | release P1 |
| REL-P1-03 | pytest: фактически 813 против показанных 1010 (#87) | `docs/version.json` | release P1 |

### P0 — Релиз

| ID | Находка | Где | Источник |
|---|---|---|---|
| REL-P0-01 | Тег `v5.6.1` стоит на коммите `21f296f`, которого нет в `v5.6-dev` (есть только в `main`); CHANGELOG:7-8 утверждает, что тег не ставился — противоречие | git / `CHANGELOG.md` | release P0 |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| PERF-P2-01 | Тяжёлые вены: `vis-network-9.1.9` 673 КБ (4 стр.), `chart.umd` 201 КБ, `bootstrap-5.0.0-beta3` 230 КБ | `docs/` | cwv P2 |
| PERF-P2-02 | Нет предсжатых `.gz`/`.br` | хостинг | cwv P2 |
| REL-P2-01 | ~40 worktree в detached HEAD | git | AUDIT_MASTER §13 |
| REL-P2-02 | Version/tests drift (см. REL-P1-03) | `docs/version.json` | release P2 |
| PRJ-P2-01 | 5 из 10 находок project-аудита ложные | — | project |
| PRJ-P2-02 | Прочие P2 project/release (4 пункта) | — | audit_D_project/release |

---

## Закрыто

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| PERF-P2-03 | Граф: стабилизация 21 229 мс → 0 мс, физика выключена, позиции предвычислены (`graph_positions.json`, 27 334 Б) | `UI_FIXES_GRAPH_PERF` | 07–08.10.2026 |
| PRJ-P1-02 | `requirements.txt`: 4 неиспользуемых пакета (openpyxl, plotly, jsonschema, scikit-learn) → удалены | `4f05a36` | 11.10.2026 |
| REL-P2-03 | `version.json` tests-счётчик синхронизирован с фактически собранными | `756a2d0`, `4f05a36` | 10–11.10.2026 |

---

## Примечания

- CWV: грейд **A**, 143/143 Good; провалов LCP > 2.5 с — ноль; TTFB медиана 169 мс; внешних CDN нет.
- `atlas` в perf-правках графа не участвовал (не применимо).
- REL-P1-03/#87 — расхождение счётчика тестов: контракт `test_version_json_*`; уточнять по факту `pytest --collect-only -q`.
- Тег `v5.6.1` — закрывать осторожно (влияет на `main`); в этой ветке теги не ставим.
- Проект/release-находки включены сюда как техническое состояние репозитория (batch D); см. `CONSOLIDATION.md` о раскладке по типам.

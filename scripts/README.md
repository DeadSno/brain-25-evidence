# scripts/ — карта живых скриптов

Последнее обновление: 2026-09-18

Все скрипты разделены на четыре категории: **источники**, **сборка**,
**QA** и **инструменты**. Мёртвые скрипты (разовые миграции, фиксы,
аудиты v1.x-v3.0) удалены. `.gitignore` блокирует рецидивы паттернами
`scripts/fix_*.py`, `scripts/m1*.py`, `scripts/diag_*.py` и т.д.

---

## 🔬 Источники

Скрипты, которые работают с внешними API и обновляют `docs/data.json`.

| Скрипт | Что делает | Как запускать |
|---|---|---|
| `search_sources.py` | Поиск PMID через PubMed E-utilities. Curated `MANUAL_PMIDS` для 11 карточек + auto-fallback | `python scripts/search_sources.py "Гинкго"` или `--all-missing` |
| `apply_sources.py` | Переносит найденные sources из `reports/sources_candidates.json` в `docs/data.json` | `python scripts/apply_sources.py --apply` |
| `migrate_key_sources.py` | Нормализация `key_sources` к единому формату `list[dict]` (разовая задача, но хранится для reproducibility) | `python scripts/migrate_key_sources.py --apply` |
| `validate_sources.py` | Квартальная валидация 234 PMID: живые ли, изменились ли метаданные. Task Scheduler — daily 09:00 с `--quarterly` | `python scripts/validate_sources.py --force` |
| `fetch_metrics.py` | Обновляет wiki (Wikimedia), citations (OpenAlex) и ongoing (ClinicalTrials.gov) | `python scripts/fetch_metrics.py --all --apply` |
| `fetch_evidence.py` | Тянет abstracts из PubMed по `key_sources` в `reports/evidence/<id>.md` | `python scripts/fetch_evidence.py --all` |

**Порядок обновления источников:**
1. Правите `MANUAL_PMIDS` в `search_sources.py` (для curated-карточек).
2. `search_sources.py --all-missing`
3. `apply_sources.py --apply`
4. `pytest` — контрактный тест подтвердит синхронность.
5. `fetch_metrics.py --all --apply` — обновить метрики.

---

## 🏗️ Сборка

Скрипты, которые читают `data.json` и `src/content.py` и генерируют
артефакты (HTML, JSON, edu-блоки).

| Скрипт | Что генерирует |
|---|---|
| `build_key_sources.py` | `key_sources` из `src.config.SUPPLEMENTS` |
| `build_ma_timeline.py` | `docs/data_ma_timeline.json` — динамика МА по годам |
| `build_edu.py` | Контент в edu-блоки карточек |
| `build_interactions.py` | `interactions` (синергии/антагонисты) |
| `build_effect_tags.py` | `docs/effect_tags.json` — 18 тегов по 81 карточке |
| `build_approve_queue.py` | Очередь на ручное утверждение (внутренний процесс) |
| `build_changelog_public.py` | `docs/changelog_public.html` из `CHANGELOG.md` |
| `q1_3.py` | Честные оси радара профиля (рефакторинг v1.0) |

---

## 🧪 QA

| Скрипт | Что проверяет |
|---|---|
| `audit_content_gaps.py` | Пустые поля BASE/ADV в `data.json` |
| `audit_links.py` | Мёртвые ссылки в HTML/JS. Вызывается из CI |
| `e2e_smoke.py` | Playwright e2e: открытие карточек, переходы, ссылки |
| `ui_verify.py` | Визуальная верификация UI на 1280/375 + скриншоты |

---

## 📊 Инструменты

| Скрипт | Назначение |
|---|---|
| `effect_tags_map.py` | Источник правды: `TAGS` + `TAG_LABELS`. **Импортируется**, не запускается |
| `extract_g.py` | Извлекает Hedges' g из abstracts |
| `sync_test_count.py` | Считает тесты через `pytest --collect-only` → `version.json.tests` |
| `view_catalog.py` | Диагностика: топ-5 каталогов PubMed по приоритету |

---

## 🤖 Автоматизация

| Что | Как | Где |
|---|---|---|
| Pre-commit hook | `pytest -q -m 'not network'` перед коммитом | `.git/hooks/pre-commit` |
| CI | pytest на push/PR, matrix Python 3.12/3.13 + Node 20 | `.github/workflows/tests.yml` |
| Квартальная валидация | `validate_sources.py --quarterly` ежедневно 09:00 | Windows Task Scheduler `brain-25-evidence-validate` |

---

## Тесты

Все скрипты покрыты тестами в `tests/`. Полный прогон:

```powershell
python -m pytest -q
# ~111 тестов, 1-2 секунды
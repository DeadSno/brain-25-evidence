# AI_START.md

> Читается AI-ассистентом (Claude/GPT) в начале сессии со мной.
> Для OpenCode — MASTER_RUNBOOK.md + AGENTS.md.

## Что за проект

**brain-25-evidence** — открытая база данных о 103 БАДах (цель 120).
- Live: https://deadsno.github.io/brain-25-evidence/
- BI:   https://brain-25-evidence.streamlit.app
- Repo: https://github.com/DeadSno/brain-25-evidence

## Роли

| Кто | Что делает |
|-----|-----------|
| **Пользователь** | Финальные решения да/нет, запускает команды |
| **AI-ассистент** (я) | Читаю state, рекомендую шаг, генерирую код/брифы, перепроверяю вывод |
| **OpenCode Big Pickle** | Только замены с готовым кодом по брифам. Лимиты быстро кончаются |

## Конвенции (жёстко)

- Код, docstrings — русский
- Commit messages — **латиница** (PowerShell ломает UTF-8 в `-m`)
- JSON — UTF-8 **без BOM**
- PowerShell 5.1 ломает `Set-Content -Encoding UTF8` → только через VS Code или Python
- **Не писать в data.json вручную** — только через скрипты
- **Не редактировать effect_tags.json** — только через effect_tags_map.py
- Тесты перед коммитом: `pytest -q -m "not network"`
- Без `--no-verify` (если тесты упали — фиксим, не пропускаем)

## Что скинуть AI в начале сессии

1. Вывод: `python scripts/check_state.py`
2. Задача одним предложением

Всё. Дальше AI сам разберётся.

## Типовые команды

### Добавление карточек (батч)
```powershell
# 1. Создать CSV → add_supplements_batch.py
# 2. fetch_evidence_abstracts.py --all
# 3. Бриф → агент → q14_batch_N_proposal.json
# 4. enrich_drafts.py --proposal ... --apply
# 5. apply_drafts.py
# 6. update_all.py --apply && build_index.py
# 7. Теги в effect_tags_map.py → build_effect_tags.py
# 8. UPDATE_SNAPSHOT=1 pytest test_snapshot; pytest -q
Тесты
powershell
python -m pytest -q -m "not network"    # быстрые
$env:UPDATE_SNAPSHOT='1'; python -m pytest tests\test_snapshot.py -q; Remove-Item Env:UPDATE_SNAPSHOT
Карта документации
Файл	Для кого
README.md	Публикация (на GitHub)
ARCHITECTURE.md	Как устроено (PubMed → data.json → HTML)
DATA_SOURCES.md	Источники данных
CONTRIBUTING.md	Как внести вклад
MASTER_RUNBOOK.md	OpenCode: фазы S0-S9
AGENTS.md	OpenCode: правила P1-P32
STATE.md	Текущее состояние цикла
ROADMAP.md	План развития
AI_START.md	Этот файл — для AI-ассистента
Типовые проблемы
Симптом	Фикс
CSV пуст при чтении	BOM в файле → encoding="utf-8-sig"
year TypeError в key_sources	year — строка, нужен int(year)
effects: пусто в apply	Не перезапущен enrich_drafts --apply
interactions: нет with	low-блок без with → добавить "with": "нет данных"
effect_tags рассинхрон	build_effect_tags.py + build_index.py
Snapshot тест падает	UPDATE_SNAPSHOT=1
PowerShell ломает кириллицу	Писать коммиты латиницей
Обновление
Обновлять при:

Смене цели (94 → 103 → 120 карточек)

Новых граблях

Изменении workflow

Версия: v1.0 (2026-09-24)
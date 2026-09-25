# AI_START.md

> Читается AI-ассистентом (Claude/GPT) в начале сессии.
> Для OpenCode — MASTER_RUNBOOK.md + AGENTS.md.

## Проект

**brain-25-evidence** — открытая база о **130 БАДах** (цель 130-200).
- Live: https://deadsno.github.io/brain-25-evidence/
- BI:   https://brain-25-evidence.streamlit.app
- Repo: https://github.com/DeadSno/brain-25-evidence

## Роли

| Кто | Что делает |
|-----|-----------|
| Пользователь | Финальные решения, запуск команд |
| AI-ассистент (Claude/GPT) | Читаю state, генерирую брифы, перепроверяю |
| OpenCode Big Pickle | Заполняет proposal по брифу |

## Конвенции (жёстко)

- Код/docstrings — русский, коммиты — **латиница**
- JSON UTF-8 без BOM
- Не писать в data.json вручную — только через скрипты
- Не редактировать `effect_tags.json` — только через `effect_tags_map.py`
- Тесты: `pytest -q -m "not network"`, без `--no-verify`
- **Двойные кавычки в `pubmed_term` ломают scienceIndex** → использовать скобки
- **Никогда не оборачивать Markdown с Mermaid/кодом в `"""..."""`** — при копировании через PowerShell теряются закрывающие backticks. Собирать текст списком строк и создавать fence через ``BT3 = "`" * 3``:

  ```python
  BT3 = "`" * 3
  lines = [
      "...",
      BT3 + "mermaid",
      "...",
      BT3,
  ]
  content = "\n".join(lines) + "\n"
  ```

## Что скинуть AI в начале

1. `python scripts/check_state.py`
2. Задача одним предложением

## Workflow

Полный batch workflow — в `MASTER_RUNBOOK.md`, раздел **«Batch workflow»**.
Кратко: CSV → abstracts → бриф → агент → validate → enrich → apply → update_all → теги → snapshot → commit.

## Частые ошибки

| Симптом | Фикс |
|---------|------|
| `scienceIndex: None` | Добавить в `EXPLICIT_BASE` (recalc_science_index.py) |
| `test_low_block` падает | Добавить low-блок в interactions |
| `test_all_interactions` падает | Прописать пары из `content.py` |
| `test_map_matches_json` | `build_effect_tags.py` + `build_index.py` |
| Snapshot падает | `UPDATE_SNAPSHOT=1` |
| Кириллица в commit | Писать латиницей |
| PowerShell ломает UTF-8 | `@'...'@ \| Out-File -Encoding UTF8` |

**Версия:** v1.2 (2026-09-25)
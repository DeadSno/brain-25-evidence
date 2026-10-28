# SKILLS_REFRESH_2026-10

Актуализация скиллов под цикл v5.6.5. Ветка `v5.6.5-dev`, дата 2026-10-17.

## Сводка

| Скиллов было | Обновлено | Удалено | Слито |
|-------------|-----------|---------|-------|
| 20 | 19 | 1 | 1 (в data-audit) |

## Изменения по скиллам

| Скилл | Что обновлено |
|-------|---------------|
| data-validation | **Удалён** (DEPRECATED, объединён в data-audit) |
| data-audit | без изменений (принимающий при слиянии) |
| AGENTS.md | `20 скиллов` → `19`; строка `data-validation` убрана из таблицы |
| SKILLS_INDEX.md | `20` → `19` скиллов; убраны строки `data-validation`; `data-validation` → `data-audit` в границах и триггерах релиза; `878 passed, 201 skipped` → `1746 passed, 237 skipped (1983)`; дата обновления 2026-10-16 → 2026-10-17; версия индекса v2.2 → v2.3 |
| CONVENTIONS.md | числа тестов 1982/1729 → 1983/1746+237; ветка v5.6-dev → v5.6.5-dev во всех командах работы с worktree; добавлен раздел про `scripts/cleanup_worktrees.py` |
| scripts/cleanup_worktrees.py | **новый** — сканирует `git worktree list`, удаляет worktree с 0 коммитов над базовой веткой (по умолчанию `v5.6.5-dev`), оставляет с коммитами (WARN), удаляет пустые каталоги-оболочки |

Остальные 18 скиллов (accessibility-check, core-web-vitals, cyberaudit, docs-sync,
i18n-rtl-audit, legal-compliance-audit, marketing-deep-audit, mobile-deep-audit,
product-audit, project-audit, pwa-audit, qa-deep-audit, release-check, seo-check,
site-navigation, skill-audit, ui-ux-deep-audit, visual-design-audit) —
проверены: числа ссылаются на `CONVENTIONS.md` (динамически), ссылки на
существующие файлы рабочие, устаревших хардкодов чисел не найдено.

## Дубли

| Скилл A | Скилл B | Решение |
|---------|---------|---------|
| data-validation | data-audit | data-validation удалён, функционал поглощён data-audit (слои 1–2). В data-audit уже есть ссылка «перенесено из data-validation» (§ Схематические проверки карточки). |
| qa-deep-audit | skill-audit | **Не дубли.** qa-deep-audit audits QA проекта; skill-audit — мета-аудит самих скиллов. |

## OpenCode auto-worktree

| Проверка | Результат |
|----------|-----------|
| Локальный `opencode.json` | 0 совпадений `worktree\|isolation\|session` |
| Глобальный `~/.config/opencode/` (`opencode.jsonc`, `docs/`, `README.md`) | 0 совпадений |
| Документация OpenCode | не найдена локально |

**Решение:** автосоздание worktree на каждую сессию — hardcoded в OpenCode Desktop,
конфигом не отключается (подтверждено разделом «OpenCode worktree (автоматика)»
в CONVENTIONS.md).

Мера:
1. После каждой сессии — cherry-pick в `v5.6.5-dev` + push.
2. `scripts/cleanup_worktrees.py` — удаление пустых worktree (база `v5.6.5-dev`).

## Числа — до/после

| Метрика | Было | Стало |
|---------|------|-------|
| Тесты (pytest) | 1079 (878+201) | 1983 (1746+237) |
| Скиллов | 20 | 19 |
| data-validation | присутствовал | удалён |

## Открытые вопросы

- 2 каталога-оболочки worktree (`gentle-orchid`, `silent-cabin`) не удалось
  удалить — заняты хендлами `node.exe` (WinError 32). Требуют паузы на отпуск
  хендлов и повторной очистки (см. раздел «Работа с worktree» в CONVENTIONS.md).
- 6 worktree оставлены — имеют незаякоренные коммиты над `v5.6.5-dev`
  (eager-circuit, happy-cabin, playful-canyon-2, shiny-lagoon, shiny-river-2,
  shiny-wizard). Перед удалением нужен cherry-pick + push.

## commity

- `c802bf1` chore(skills): remove deprecated data-validation (merged into data-audit)
- `82ca241` chore(scripts): cleanup_worktrees.py (auto-detached HEAD cleanup)

Готовы к v5.6.5: да.

## Worktree cleanup (v5.6.5)

| Worktree | Коммитов | Решение |
|---|---|---|
| eager-circuit | 14 | удалён (дубли) |
| happy-cabin | 1 | удалён (дубли) |
| playful-canyon-2 | 2 | удалён (дубли) |
| shiny-river-2 | 5 | удалён (дубли) |
| shiny-wizard | 7 | удалён (дубли) |
| shiny-lagoon | 8 | 6db227c — устарел, не применён, worktree удалён |
| gentle-orchid | 0 | уже удалён ранее (хендлы node.exe) |
| silent-cabin | 0 | уже удалён ранее (хендлы node.exe) |
| Итого удалено | 6 | |
| Осталось | 2 | main checkout + сессия mighty-forest |

## Проверка теста skill inventory

- `test_skill_inventory_does_not_shrink`: порог 19 — **актуален**, изменений не требует.
- Падение в früheren прогонах объясняется запуском pytest в `mighty-forest` (detached worktree, 18 скиллов без vendored `cyberaudit`), а не в main checkout (19 скиллов).
- `developing-with-streamlit` — фантом (никогда не существовал в репо: `Test-Path = False`, `git log --all` пуст).
- SKILLS_INDEX: 19 записей (строка 5 + список 257–279), соответствует фактическим 19 каталогам.
- AGENTS.md: "19 скиллов" — актуально.
- 6db227c (13C1 tail): **устарел**, не применён (коммит утверждает, что `yandex_cc2e3cf2ee185b01.html` добавлен; в ветке файл удалён, верификация Яндекса через метатег в `index.html`).

pytest в main checkout: **1746 passed, 237 skipped** ✓

git worktree list: **2** (main checkout v5.6.5-dev + detached mighty-forest сессия)

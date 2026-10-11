# Pre-merge check: main vs v5.6-dev

Дата: 2026-10-11
Ветка проверки: `v5.6-dev`
Base: `origin/main` = `57e0089`
Режим: только чтение, merge не выполнялся.

## Состояние веток

| Ветка | HEAD | Всего коммитов |
|---|---|---|
| `origin/main` | `57e0089` | 706 |
| `origin/v5.6-dev` | `f96d4d7` | 803 |

**Расхождение:**
- `origin/main..origin/v5.6-dev` = **97** коммитов (наши правки)
- `origin/v5.6-dev..origin/main` = **0** коммитов
- `git rev-list --left-right --count origin/main...origin/v5.6-dev` = `0  97`

Merge-base = `57e0089f3cf51184532626195d973c2d001b015d` — это **в точности** HEAD `origin/main`.

Локальная `v5.6-dev` совпадает с `origin/v5.6-dev` (HEAD `f96d4d7`), рабочее дерево чистое.

## Что в main, но не в dev

**Нет.** `dev..main` пуст — ни одного коммита, отсутствующего в `v5.6-dev`.

Это значит:
- hotfix-ов в `main`, потерянных при работе в dev, нет;
- merge-коммит не создаст конфликтов — `main` является предком `v5.6-dev`.

## main-состояние (прод, 4 дня отстаёт)

- `docs/privacy.html` — **отсутствует** в `origin/main`
- `docs/version.json` — `app: 5.6.1`, `data: 2026-09-25`, `audit: 1.0`, `tests: 989`
- `docs/feed.xml` — `lastBuildDate: Wed, 07 Oct 2026 00:00:00 +0000` (4 дня назад)

Целевые файлы в `v5.6-dev`:
- `docs/privacy.html` — **есть** (новый файл)
- `docs/version.json` — `app: 5.6.3`, `data: 2026-09-25`, `audit: 1.0`, `tests: 1079`
- `docs/feed.xml` — `lastBuildDate: Sun, 11 Oct 2026 00:00:00 +0000` (сегодня)

## Риски merge

**Конфликты: 0.**

Проверка `git merge-tree --write-tree --messages origin/main origin/v5.6-dev`:
- exit code `0`
- один выходной объект `dbecc88933fcff97fd826be10cbf2b7c6aa20e34`
- ни одного сообщения о конфликте

**Общие изменённые файлы: 0.**

- `git diff --name-only $mb origin/main` = 0 файлов (main не менялся с merge-base)
- `git diff --name-only $mb origin/v5.6-dev` = 360 файлов

Так как `main` не содержит изменений после точки слияния, пересечения по изменённым файлам нет в принципе.

> Замечание о проверке: `git merge-tree <base> origin/main origin/v5.6-dev | Select-String "changed in both"` даёт **ложные срабатывания** — строка `changed in both` не появляется, но в вывод попадает содержимое страниц `docs/sup/`, где встречается слово «конфликт» (например, «Конфликт интересов (COI, conflict of interest)» и текст про маркеры `<<<<<<<`). Для адекватной проверки использовать `git merge-tree --write-tree --messages` и код возврата.

**Объём изменений:** 360 файлов, +33036 / −1980 строк.

Распределение по каталогам (доля изменённых файлов):

| Каталог | Доля |
|---|---|
| `docs/sup/` | 36.3% |
| `reports/` | 24.7% |
| `tests/snapshots/chromium/` | 10.0% |
| `tests/snapshots/webkit/` | 9.7% |
| `docs/` | 6.3% |
| `tests/` | 2.7% |
| `reports/archive/worktree-patches-2026-10-10/` | 1.6% |
| `scripts/` | 1.3% |
| `.githooks/`, `data/`, `docs/api/v1/`, `reports/i18n/`, `reports/ux/`, `src/`, `templates/`, `.github/workflows/`, `.opencode/skills/` | по ~0.2–0.8% |

Вне `docs/sup/`, `reports/`, `tests/snapshots/` изменено 57 файлов — это и есть реальный код/конфиг/тесты.

**Прогноз: fast-forward.** `origin/main` — предок `v5.6-dev`, поэтому merge выполнится как fast-forward без merge-коммита и без конфликтов.

## Рекомендация

**Быстрый merge (fast-forward). Проблем не найдено.**

Обоснование:
1. `dev..main` пуст — в `main` нет ничего, чего не было бы в dev.
2. `merge-base == origin/main HEAD` — ни одного параллельного изменения, пересечение файлов невозможно.
3. `git merge-tree --write-tree` завершился с кодом 0 без сообщений о конфликтах.
4. Все контрольные точки прод-версии (`privacy.html`, `version.json`, `feed.xml`) после merge будут соответствовать dev: `5.6.3`, `tests: 1079`, дата сборки 11 Oct 2026.

Ожидаемый эффект для Pages: версия `5.6.1 → 5.6.3`, `tests 989 → 1079`, добавление `docs/privacy.html`, свежая дата в `feed.xml`.

Оговорки перед выкатом (вне scope настоящей проверки, требуют отдельного прогона):
- снапшоты эталонов (`tests/snapshots/`) изменены в 130 `docs/sup/` страницах и обоих движках — перед merge имеет смысл прогнать тесты и убедиться, что сервер на `:8000` отвечает (`Invoke-RestMethod http://localhost:8000/version.json`), иначе прогоны молча скипятся;
- изменение `RETMAX 500->2000` и `SUPPLEMENTS 74->130` затрагивают пайплайн генерации — стоит проверить полный rebuild, а не только снапшоты.
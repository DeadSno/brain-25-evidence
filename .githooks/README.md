# Git hooks

Активный и единственный хук — `pre-commit` в этом каталоге.

Активация:

    git config core.hooksPath .githooks

Проверка:

    git config core.hooksPath     # должно вывести .githooks

`.git/hooks/` не используется: при заданном `core.hooksPath` git читает только
`.githooks/`. Если в `.git/hooks/` лежит `pre-commit` — это устаревшая локальная
копия (не в git, старый фильтр pytest), её надо удалить: `rm .git/hooks/pre-commit`.

Что делает хук и зачем — в комментариях внутри `pre-commit` и в разделе
«Git hooks» корневого `README.md`.

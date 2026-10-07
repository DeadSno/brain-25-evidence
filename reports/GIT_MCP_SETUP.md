# GIT_MCP_SETUP — mcp-server-git как MCP для Git

**Дата:** 2026-10-07
**Машина:** DESKTOP-H4A2TAT, Windows
**Репозиторий MCP:** `C:\analytics\brain-25-evidence`
**Конфиг:** `C:\Users\TshK\.config\opencode\opencode.jsonc`
**Статус:** ✅ **Работает.** MCP подключился, 12 инструментов, `git status` отвечает.

---

## Итог одной строкой

`mcp-server-git` подключён как MCP-сервер `git`. Ни LLM, ни 4.7 ГБ модели
не грузится — сервер на чистом Python, отдаёт структурированные данные
за миллисекунды. `context7` / `playwright` / `serena` не тронуты.

---

## 1. uvx и mcp-server-git

### 1.1 uvx — ✅ работает

| Проверка | Результат |
|---|---|
| `uvx --version` | `uvx 0.12.23 (46b84fd0b 2026-10-03 x86_64-pc-windows-msvc)` |
| `uv --version` | `uv 0.12.23` (тот же билд) |
| Полный путь | `C:\Users\TshK\.local\bin\uvx.exe` — существует |
| В Machine PATH | ❌ нет |
| В User PATH | ✅ есть |

Вывод: `uvx` доступен любому процессу пользователя, но **не** системным
процессам. Отсюда решение писать полный путь (см. §2.2).

### 1.2 mcp-server-git — ✅ работает

```
$ uvx mcp-server-git --help
Usage: mcp-server-git [OPTIONS]

  MCP Git Server - Git functionality for MCP

Options:
  -r, --repository PATH  Git repository path
  -v, --verbose
  --help                 Show this message and exit.
```

Установка при первом запуске (из stderr):

```
Downloading cryptography (3.6MiB)
Downloading pydantic-core (1.9MiB)
Installed 34 packages in 181ms
```

**A3. Ответ на вопрос задания:** `uvx mcp-server-git` работает.
Запасной вариант `uvx --from mcp-server-git mcp-server-git` **не потребовался** —
имя пакета совпадает с именем бинарника.

Флаг из задания корректен: в справке значится `-r, --repository PATH`,
полная длинная форма работает.

---

## 2. Конфиг

### 2.1 Что добавлено

В блок `"mcp"` файла `~/.config/opencode/opencode.jsonc` добавлен ключ
`git` — последним, после `duckdb`:

```jsonc
    "git": {
      "type": "local",
      "enabled": true,
      "command": [
        "C:\\Users\\TshK\\.local\\bin\\uvx.exe",
        "mcp-server-git",
        "--repository",
        "C:\\analytics\\brain-25-evidence"
      ]
    }
```

Рядом добавлен комментарий из 6 строк — почему путь к `uvx` записан
литералом и почему репозиторий задан абсолютно. Комментарий — в стиле
файла: в `opencode.jsonc` их уже много (строки 7–131), и каждый
фиксирует неочевидное решение.

### 2.2 Отклонение от задания: `uvx` → полный путь

В задании было `"command": ["uvx", "mcp-server-git", ...]`.
Использован полный путь. Причина — не перестраховка, а воспроизведённый
в этом же файле опыт: у записи `serena` (строки 126–131) стоит
комментарий о том, что `Path` записан литералом, потому что значение
перестаёт следовать за системным PATH. `uvx` лежит в **User**, а не
**Machine** PATH — то есть в худшем случае именно тот случай, который
уже обошёл проект один раз.

### 2.3 Синтаксис — ✅ валиден

Проверка: строки-комментарии `//` убраны, остаток распарсен
`ConvertFrom-Json`.

```
PARSE: OK
mcp servers: serena, context7, exa, playwright, duckdb, git
```

### 2.4 Бэкап до правки

`~/.config/opencode/opencode.jsonc.bak-git-courer` (11 687 Б) — сделан
в предыдущем задании, до этой правки. Актуальная точка отката.

---

## 3. context7 / playwright / serena — целы

| Сервер | В конфиге | В каталоге инструментов | Прежний размер |
|---|---|---|---|
| `serena` | ✅ | ✅ 29 tools | без изменений |
| `context7` | ✅ | ✅ 2 tools | без изменений |
| `playwright` | ✅ | ✅ 25 tools | без изменений |
| `exa` | ✅ `enabled: false` | ⛔ отключён намеренно | без изменений |
| `duckdb` | ✅ `enabled: false` | ⛔ отключён намеренно | без изменений |
| **`git`** | ✅ **новый** | ✅ **12 tools** | — |

Конфликта нет: правка добавила ключ, ничего не переименовывая и не
удаляя. `git-courer mcp setup opencode` не запускался — риск, который
он создавал (правка `opencode.json` вместо `.jsonc`, потеря пяти
серверов), не реализовался.

---

## 4. Проверка через MCP

### 4.1 Подключение — ✅ без перезапуска

План предполагал перезапуск OpenCode Desktop (C1). **Не потребовался:**
OpenCode подхватил изменение конфига на лету — сервер `git` появился
в каталоге инструментов сразу после правки файла.

### 4.2 Инструменты — 12 из 12

| # | Инструмент | Тип | Обязательные параметры |
|---|---|---|---|
| 1 | `git_status` | read | `repo_path` |
| 2 | `git_log` | read | `repo_path`; `max_count` (по умолчанию 10), `start_timestamp`, `end_timestamp` |
| 3 | `git_show` | read | `repo_path`, `revision` |
| 4 | `git_diff_unstaged` | read | `repo_path`, `context_lines` (3) |
| 5 | `git_diff_staged` | read | `repo_path`, `context_lines` (3) |
| 6 | `git_diff` | read | `repo_path`, **`target`**, `context_lines` |
| 7 | `git_branch` | read | `repo_path`, **`branch_type`** |
| 8 | `git_add` | **write** | `repo_path`, `files[]` |
| 9 | `git_commit` | **write** | `repo_path`, `message` |
| 10 | `git_checkout` | **write** | `repo_path`, `branch_name` |
| 11 | `git_create_branch` | **write** | `repo_path`, `branch_name`, `base_branch` |
| 12 | `git_reset` | **write** | `repo_path` |

### 4.3 Фактические вызовы

**`git_status`** — ✅ отработал:

```
Repository status:
On branch v5.6-dev
Your branch is up to date with 'origin/v5.6-dev'.

Untracked files:
	Modelfile
	_tmp_analyze.py
	reports/GIT_COURER_SETUP.md

nothing added to commit but untracked files present
```

Ветка определилась верно, состояние соответствует реальному
`git status`. Список неотслеживаемых файлов совпадает с выводом
`git status --short` — расхождений нет.

**`git_log`** — ✅ отработал, вернул 10 коммитов с ветки `v5.6-dev`,
начиная с `fbb3c02 docs(audit): batch A skill 1/5 — data-audit`.
HEAD совпадает с последним коммитом батча A.

**`git_diff_unstaged`** — ✅ отработал: `"Unstaged changes:\n"`,
пусто. Корректно: отслеживаемых файлов не изменено, незакоммичены
только новые файлы.

### 4.4 Ловушки API — две, обе тихие

**Ловушка 1: неизвестные параметры молча игнорируются.**
Первый вызов `git_log` был с `count: 3`. Ошибки не последовало —
сервер вернул 10 коммитов. Правильное имя — `max_count`.
Вывод: **`git status` может показать не то количество коммитов, о котором
попросили, и никто об этом не узнает.** Для выборок в отчётах использовать
`max_count` и проверять длину ответа.

**Ловушка 2: `git_diff` — это диф против ревизии, а не против рабочей копии.**
Параметр `target` обязателен и трактуется как **ref**:

```
git_diff(target: "unstaged")
→ ERR: Ref 'unstaged' did not resolve to an object
```

Рабочая область тут не подставляется, это ломает интуицию. Для изменений
в рабочем дереве — `git_diff_unstaged` и `git_diff_staged`, у которых
`target` нет вовсе. `git_branch` требует `branch_type` (`local` /
`remote` / `all`), а не имя ветки.

### 4.5 ⚠️ Риск: агенту выданы 5 инструментов, меняющих репозиторий

`git_checkout`, `git_reset`, `git_add`, `git_commit`, `git_create_branch`
доступны агенту без посредничества shell. Это расходится с правилами
`AGENTS.md`, где запрещены `git checkout` / `git reset` без `git stash`
или `git diff`, и полный запрет на `git merge` в этой ветке.

| Инструмент | Что делает | Чем опасен |
|---|---|---|
| `git_reset` | Снимает со staged **всё** | Индексированные изменения теряются, восстановление — только через `reflog` |
| `git_checkout` | Переключает ветку | Незакоммиченные правки могут уехать вместе с собой |
| `git_add` | Индексирует файлы | Случайно проиндексировать то, что не задумано |
| `git_commit` | Коммитит staged | Коммит мимо pre-commit-гейта проекта |
| `git_create_branch` | Создаёт ветку | Может создать ветку от не того коммита |

Ни один из них в этой сессии **не вызывался** — проверка шла
read-only инструментами.

Смягчения, которые стоит рассмотреть (в §6 это вопрос к владельцу):
- `permission` в `opencode.json` по аналогии с git-courer:
  запретить агенту write-инструменты, оставив read;
- либо оставить как есть, но дописать в `AGENTS.md` правило:
  «write-инструменты `git` MCP — только по явной команде владельца».

---

## 5. git-courer — оставлен как запас

Ничего не удалено и не изменено.

| Параметр | Значение |
|---|---|
| Бинарник | `C:\Users\TshK\go\bin\git-courer.exe` (22 673 408 Б) |
| Версия | `git-courer v2.12.3` |
| Конфиг | `C:\Users\TshK\.config\git-courer\config.yaml` создан |
| Модель | `qwen-coder-top:latest` (Ollama, `http://localhost:11434/v1`) |
| Go | `go1.27.1 windows/amd64`, PATH прописан |

**Рекомендация (D1):**

1. **Не использовать как CLI.** Модель на 4.7 ГБ грузится в память
   при каждом старте — даже для `--help`. Замер: команда не уложилась
   в 180 с и в 120 с. Для `status` / `diff` / `log` это неприемлемо,
   именно поэтому выбран `mcp-server-git`.
2. **Может быть полезен как долгоживущий MCP-сервер.** Модель
   загружается один раз при старте процесса и живёт, пока сервер
   поднят, — в отличие от CLI, где платишь за модель на каждый
   вызов. Сценарий: оставить его поднятым ради задач, где нужен
   осмысленный разбор (`review`, `pr-review`, объяснение коммитов),
   а механику брать из `mcp-server-git`.
3. **Требует настройки `config.yaml` с Ollama** — уже сделано, схема
   сверена с `docs/config.md`, а не списана из задания.
4. **Осторожно с автоконфигурацией.** `git-courer mcp setup opencode`
   писал бы в `opencode.json`, тогда как проект живёт в
   `opencode.jsonc`. Запуск команды способен либо потерять пять
   работающих MCP-серверов, либо не подключить git-courer вовсе.
   Пока не запускается.

---

## 6. Вопросы владельцу

| # | Вопрос |
|---|---|
| 1 | Оставляем `git_checkout` / `git_reset` / `git_commit` агенту? Предлагаю `permission`-правило: read — свободно, write — по явной команде. В `AGENTS.md` эти операции и так ограничены, а MCP их обходит. |
| 2 | `--repository` задан жёстко на `C:\analytics\brain-25-evidence`. Нужны ли MCP-инструменты на других репозиториях (например, на worktree `quiet-falcon`)? Тогда потребуется вторая запись в конфиге. |
| 3 | `git_reset` без аргументов снимает весь staged. Оставляем или выкидываем инструмент из использования? |
| 4 | Запускать ли когда-нибудь `git-courer mcp setup opencode`? Если да — сначала конвертация `opencode.jsonc` → `opencode.json` с бэкапом, иначе риск потерять 5 серверов. |
| 5 | В рабочем дереве висят неотслеживаемые: `Modelfile`, `_tmp_analyze.py`, `reports/GIT_COURER_SETUP.md`. Первые два — не мои (`Modelfile` создан при настройке Ollama, `_tmp_analyze.py` — остаток прерванного аудита). Удалить? |

---

## 7. Что было сделано / не сделано

| Шаг | Статус |
|---|---|
| A1 `uvx --version` | ✅ `uvx 0.12.23` |
| A2 `uvx mcp-server-git --help` | ✅ справка получена, 34 пакета установлены |
| A3 запись в отчёт | ✅ §1.2 |
| B1–B2 открыть и найти блок `mcp` | ✅ |
| B3 добавить ключ `git` | ✅ вручную, через Edit |
| B4 проверка синтаксиса | ✅ `ConvertFrom-Json` — OK |
| B5 context7/playwright/serena | ✅ целы, §3 |
| C1 перезапуск Desktop | ⏭️ не потребовался — hot reload |
| C2 MCP `git` виден | ✅ 12 инструментов |
| C3 `git status` через MCP | ✅ ответил, §4.3 |
| D1 рекомендация по git-courer | ✅ §5 |
| D2 не трогать git-courer | ✅ не тронут |

**Стоп-условия не сработали:** uvx работает, mcp-server-git запускается,
MCP подключился, конфликта с context7 / playwright / serena нет.

---

## 8. Приложение: как проверялось

| Проверка | Чем | Результат |
|---|---|---|
| `uvx`, `uv` версии | `uvx --version`, `uv --version` | 0.12.23 |
| Путь `uvx` | `Get-Command uvx`, Machine/User PATH | `.local\bin\uvx.exe`, только User |
| `mcp-server-git` | `Start-Process` + редирект, таймаут 240 с | usage, `-r/--repository` |
| Число пакетов | stderr при первом запуске | 34, 181 мс |
| Синтаксис JSONC | `ConvertFrom-Json` после снятия `//` | OK, 6 серверов |
| Список MCP | каталог инструментов | 12 в `git`, прочие на месте |
| `git_status` | вызов MCP-инструмента | ветка `v5.6-dev`, 3 untracked |
| `git_log` | вызов MCP-инструмента | 10 коммитов, HEAD `fbb3c02` |
| `git_diff_unstaged` | вызов MCP-инструмента | пусто, корректно |
| Ошибка `git_diff` | `target: "unstaged"` | `Ref did not resolve` |

Все утверждения отчёта получены реальными вызовами. Ничего не запускалось
«на веру» и не достраивалось по догадке: расхождение `opencode.json` /
`.jsonc`, путь `uvx` и отсутствие `--count` у `git_log` найдены
проверкой, а не взяты из документации.

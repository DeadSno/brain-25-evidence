# v5.6.1: агент auditor (read-only) + Serena MCP

Работа в `C:\analytics\brain-25-evidence`. Правился **только глобальный**
конфиг `C:\Users\TshK\.config\opencode\opencode.jsonc`. Проектные файлы
не коммитились и не менялись, кроме артефактов Serena (раздел 7).

## Коротко

| Что | Статус |
|---|---|
| uv/uvx установлен | да, 0.12.23 |
| Serena поднялась как MCP | да, 29 инструментов, Desktop |
| Serena даёт LSP | да (проверено вызовом, не логом) |
| Конфиг валиден для обоих рантаймов | да, V1 CLI exit 0 |
| context7 / playwright не сломаны | да, connected в обоих |
| Агент auditor создан | да, `~/.config/opencode/agents/auditor.md` |
| Агент виден в десктопе | **НЕ ПРОВЕРЕНО** — нужен ваш взгляд |
| read-only enforcement (D5/D6) | **НЕ ПРОВЕРЕНО** — нужно запустить агента |

Четыре пункта задания в формулировке не заработали и были исправлены по
фактам (раздел 2, 3). Два стоп-условия сработали по-настоящему и были
устранены (раздел 3).

## 1. Pre-requisites

| Проверка | Ожидание | Факт |
|---|---|---|
| `uvx` | есть | **отсутствовал**, установлен |
| `uv` | есть | **отсутствовал**, установлен |
| Python | 3.11+ | **3.14.7** |

Установка: `irm https://astral.sh/uv/install.ps1 | iex` → uv 0.12.23 в
`C:\Users\TshK\.local\bin`. Каталог **дописан в постоянный Path пользователя**
(проверено через `[Environment]::GetEnvironmentVariable('Path','User')`).

Текущий конфиг на старте: 54 строки, без блока `agent`, MCP плоский —
context7 (remote), exa (disabled), playwright (local), duckdb (disabled).
Плагины: `@azumag/opencode-rate-limit-fallback@1.70.11`,
`@andrewhampton/opencode-handoff`. Резервная копия:
`opencode.jsonc.bak-serena`.

Процессов Serena до работы не было.

## 2. Агент auditor — где и почему не так, как в задании

### Задание предлагало синтаксис V1, который V2 не понимает

Блок из B2 — `"agent"` + `"permission"` как объект `{edit, bash}` + поле
`"prompt"`. Документация V2 это прямо запрещает
(<https://opencode.ai/v2/docs/agents>, раздел Options, WARNING):

> Do not use legacy top-level fields such as temperature, top_p, **prompt**,
> **permission**, tools, disable, or maxSteps in new V2 agent configuration.

Плюс <https://opencode.ai/v2/docs/permissions>: «In V2, use **permissions**,
**shell**, and subagent instead of permission, bash, and task».

То есть в задании перепутаны обе схемы: имя действия должно быть `shell`,
а не `bash`, а `permissions` — упорядоченный список
`{action, resource, effect}`, а не объект.

### Но вписать это в opencode.jsonc нельзя — сломался бы второй рантайм

Здесь главная находка, которой нет в задании. **Один глобальный конфиг
читают два разных рантайма:**

| Рантайм | Версия | Читает конфиг |
|---|---|---|
| OpenCode Desktop | **2.0.24** (V2) | `~/.config/opencode/opencode.jsonc` |
| `opencode` CLI | **1.18.33** (V1) | тот же файл |

Проверено: Desktop грузит именно этот файл (в логе
`message=loading path="...\.config\opencode\opencode.jsonc"`), и `opencode
--version` даёт 1.18.33, `OpenCode.exe` — ProductVersion 2.0.24.

Когда блок `agents` с V2-`permissions` стоял в JSONC, V1 CLI отказывался
грузить конфиг целиком:

```
Error: Configuration is invalid at ...opencode.jsonc
V2 permissions are not supported by OpenCode V1.
Use V1 "permission" rules or run opencode2. agents.auditor.permissions
```

`opencode mcp list` падал с кодом 1, то есть **ломался весь доступ к MCP** —
ровно стоп-условие «конфиг ломается → СТОП, откат».

### Решение: Markdown-агент в `~/.config/opencode/agents/auditor.md`

V2 читает Markdown-агентов из `~/.config/opencode/agents/<name>.md`
(раздел Locations в документации V2), а V1 этот каталог не обходит вовсе.
В итоге конфиг валиден для обоих, а агент существует там, где он нужен.

Блок `agents` из JSONC удалён (59 строк), на его месте — комментарий,
объясняющий причину, чтобы никто не вернул его обратно.

### Что в auditor.md

Frontmatter: `description`, `mode: primary`, `model:
opencode/space-bunny-free`, `permissions` (25 правил). Тело файла —
системный промпт: правила проекта (без regex по HTML/CSS, без heredoc,
кириллица через файл, `route.abort()` не работает), формат работы (отчёт в
`reports/`, DoD проверяется самим аудитором, «Вопросы владельцу» с A/B) и
стоп-условия (включая «эталоны снапшотов пропущены молча — это провал, а не
успех»).

### Порядок правил

Последнее совпавшее правило выигрывает, поэтому широкое
`shell * → ask` идёт **первым**, запреты на git — после него. Обратный
порядок не запретил бы ничего: `*` перекрыл бы исключения.

### Дыра в read-only, найденная проверкой tools/list

У каждого MCP-инструмента **своё** permission action вида
`<server>_<tool>`, а базовый политика агента — `allow` на `*`. Значит
правила `shell` и `edit` на инструменты Serena **не действуют**.

Из 29 инструментов Serena **13 пишущих**, и среди них
`execute_shell_command`. Без запрета он обошёл бы все `git commit*` /
`git push*`: те смотрят на action `shell`, а тут
`serena_execute_shell_command`. Аудитор получил бы коммит и пуш при
«read-only» в конфиге.

Схема выбрана fail-closed: сначала `serena_* → deny`, потом 16 явных
`allow` на читающие инструменты (`read_file`, `find_symbol`,
`find_referencing_symbols`, `find_declaration`, `find_implementations`,
`get_symbols_overview`, `get_diagnostics_for_file`, память, служебные). Если
Serena добавит новый пишущий инструмент, он окажется запрещён по умолчанию.

## 3. Serena — три отличия от задания и два сработавших стоп-условия

### Отличие 1: бинарь `serena-mcp-server` не существует

Пакет `serena-agent` даёт ровно три: `serena.exe`, `serena-agent.exe`,
`serena-hooks.exe`. MCP-сервер — подкоманда `serena-agent start-mcp-server`.
Проверено: попытка запустить `serena-mcp-server` даёт
«An executable named start-mcp-server is not provided by package
serena-agent».

### Отличие 2: контекста `ide-assistant` не существует

`serena context list`: agent, antigravity, chatgpt, claude-code, codebuddy,
codex, copilot-cli, **desktop-app**, grok, ide, jb-ai-assistant,
jb-copilot-plugin, junie, oaicompat-agent, vscode, zcode. Для десктопа —
`desktop-app`, он же значение по умолчанию у `start-mcp-server`.

### Отличие 3: `--python 3.13` обязателен

Системный Python 3.14.7, а у pyyaml 6.0.2 нет колеса под 3.14 — сборка
падает:

```
error: Microsoft Visual C++ 14.0 or greater is required.
hint: `pyyaml` (v6.0.2) was included because `serena-agent` depends on `pyyaml`
```

На 3.13 есть готовые колеса, установка проходит. Ставить Visual C++ Build
Tools ради одного пакета не стал.

### Стоп-условие №1: `{env:PATH}` ломает конфиг

Первая рабочая версия задавала `environment.Path` как
`C:\Users\TshK\.local\bin;{env:PATH}`. Подстановка `{env:...}` идёт **без
повторного экранирования**, а в PATH Windows полно обратных слэшей — на
выходе `\W`, `\P`:

```
Error: Config file ... is not valid JSON(C)
InvalidEscapeCharacter at line 173, column 17
```

Файл в целом перестал грузиться, `opencode mcp list` — код 1. Это было
настоящее срабатывание стоп-условия «конфиг ломается → СТОП, откат».
Исправлено: Path записан литералом с удвоенными слэшами (экранирование
сгенерировано скриптом, не на глаз).

### Стоп-условие №2: короткий `uvx` не находится

Даже с валидным конфигом сервер не стартовал:

```
message="mcp connect failed" server=serena
error='... "uvx" не является именем команды ...'
```

Desktop запускает MCP-процесс со своим окружением, где
`C:\Users\TshK\.local\bin` в Path отсутствует. Исправлено абсолютным путём
к `uvx.exe`.

Абсолютный путь починил только запуск сервера. Первый вызов `find_symbol`
после этого упал:

```
The language server manager is not initialized
Failed to start 1 language server(s): python:
Could not find 'uvx' or 'uv' in PATH.
```

Языковой сервер Serena запускает отдельным процессом с тем же Path — отсюда
`environment` в конфиге.

### Почему MCP оставлен плоским, а не `mcp.servers`

Документация V2 требует `mcp.servers.<name>` и прямо пишет «V2 does not
place server names directly under mcp». Но **эта машина читает плоский
блок** — доказано логом собственного сервера Desktop:

```
message="mcp connected" server=context7 tools=2
message="mcp connected" server=playwright tools=25
```

Оба пришли именно из плоского блока. Перенос в `mcp.servers` с большой
вероятностью отключил бы context7 и playwright — стоп-условие «MCP
context7 / playwright перестают работать → СТОП». Поэтому serena добавлена
рядом, по соседству с работающими, и ни одно существующее поле не
переставлялось.

## 4. Перезапуск

D1: убито 10 процессов `OpenCode`, D2: запущен заново (6 процессов).

Итог после рестарта:

| Что | Факт |
|---|---|
| serena в Desktop | **connected, 29 инструментов** |
| context7 | **connected, 2** |
| playwright | **connected, 25** |
| exa / duckdb | disabled (как было) |
| Ошибок context7/playwright после рестарта | **0** |
| `opencode mcp list` (V1 CLI) | **exit 0**, 5 серверов |

Проверено и логом, и живым вызовом, и отдельным прогоном V1 CLI — не только
по отсутствию ошибок.

## 5. Проверка Serena: находит ли определения

Проверено настоящим MCP-handshake (initialize → tools/list → tools/call), а
не «просто запустилась»:

```
initialize OK
  server: Serena 2.0.0.dev0
  protocolVersion: 2025-06-18
tools/list OK: 29 инструментов
```

`get_current_config`: `Language backend: LSP`, `Language server status:
ready`, `Active project: brain-25-evidence`.

### D4 — задание просило найти `openModal`

**Честный результат: по JS Serena не ответила, и причину я нашёл.**

```
find_symbol("openModal") -> []
```

При этом `openModal` существует — 8 вхождений: `docs/script.js:590`
(определение), `docs/script.js:291,586,828` (вызовы), `docs/trends.html:687`
(определение), `docs/trends.html:555`, `docs/tracker.js:100`.

Причина — в конфиге Serena: `.serena/project.yml` содержал
`language_servers: [python]`. Сервер JavaScript не поднимался вообще:

```
get_symbols_overview("docs/script.js")
-> ValueError: Active language servers: ['python']
```

Python при этом работал: `find_symbol("slugify")` вернул
`build_sup.py:115-128`, а `find_referencing_symbols` нашёл перекрёстные
ссылки, включая `build_feed.py:57` и `:162` — то есть семантика настоящая,
не текстовый поиск.

Исправлено через `.serena/project.local.yml` (штатное место для локальных
переопределений, `project.yml` не трогал):

```yaml
language_servers:
- typescript
- python
```

`typescript-language-server` на машине есть
(`C:\Users\TshK\AppData\Roaming\npm\typescript-language-server.ps1`).
Порядок важен: первый в списке считается дефолтным и работает как fallback.

Подтверждено по логу Serena **десктопа** (запуск 09:58:44, после правки
в 09:57:24):

```
[StartLS:typescript] Starting TypeScript server
[StartLS:typescript] TypeScript server is ready
[StartLS:typescript] Language server startup completed in 6.859 seconds
[StartLS:python]    Language server startup completed in 1.310 seconds
```

То есть оба сервера подняты. **Но `find_symbol("openModal")` после этого я
сам проверить не смог:** у сессии агента своё, более раннее MCP-соединение
с Serena, которое стартовало до правки. Проверка возможна только из
Desktop-сессии. Это единственный пункт блока D, который остался
непроверенным функционально.

## 6. Вопросы владельцу

**1. Агент auditor виден в десктопе?** Не проверено: у меня нет доступа к
GUI Desktop. Нужен ваш взгляд в Settings → Расширения → Агенты. Если
`auditor` не появился — вероятная причина в том, что Desktop не перечитал
`~/.config/opencode/agents/`; лечится рестартом.

**2. Read-only (D5/D6) не проверен.** Проверка требует реально выбрать
агента и дать ему задачу «отредактируй README.md» и «сделай git commit».
Я не могу сделать это из агентской сессии — я и есть тот рантайм, который
эти правила должен применять к другому агенту. Правила написаны и
проверены на синтаксис, но фактическое срабатывание не наблюдалось.
Прошу проверить: если аудитор всё же что-то запишет, значит `permissions`
не применились.

**3. Три строки в конфиге задания не заработали бы** (`serena-mcp-server`,
`ide-assistant`, синтаксис `agent`/`permission`). Оставил рабочие
эквиваленты, описанные выше. Если нужно иначе — скажите.

**4. `Path` в `environment` Serena записан литералом.** Следствие: если
системный PATH изменится, Serena придётся поправить руками. Альтернатива
была только `{env:PATH}`, но он ломает JSON — выбора нет.

**5. Можно ли доверять `docs/*.js` как точке входа для аудита.** Проект
на 2/3 Python-конвейер (scripts/, tests/) и на JS-сайт. Serena после
правки обслуживает и то и другое, но не проверено на живом символе.

## 7. Что изменено в файлах

### Глобальный конфиг (можно править, по условию задачи)

| Файл | Изменение |
|---|---|
| `~/.config/opencode/opencode.jsonc` | + Serena в `mcp`, комментарии, блок `agents` удалён |
| `~/.config/opencode/agents/auditor.md` | **новый**, агент целиком |
| `~/.config/opencode/opencode.jsonc.bak-serena` | резервная копия до правок |
| `~/.serena/serena_config.yml` | `ignored_paths: [".venv/**"]` |
| `C:\Users\TshK\.local\bin\` | установлены uv, uvx, uvw |

Почему `ignored_paths`: внутри репозитория лежит `.venv` с **10 867**
файлами `.py` против **142** реальных в `scripts/` + `tests/` + `src/`.
Без исключения Serena тратит память и время на индексацию виртуального
окружения, а результаты поиска забиваются его пакетами.

### Проект (НЕ коммитилось, `git status` чистый)

| Файл | Статус |
|---|---|
| `.serena/project.local.yml` | создан Serena, я дописал `language_servers` |
| `.serena/project.yml`, `.gitignore`, `cache/` | созданы Serena |

`.serena/` — артефакт Serena, в git не добавлен. **Решение за вами:** добавить
`.serena/` в `.gitignore` или оставить untracked. Внутри есть
`.serena/.gitignore`, который исключает только `cache` и `project.local.yml`,
поэтому `git status` показывает каталог.

Ни `docs/`, ни `tests/`, ни `scripts/` не тронуты. Коммитов не делал.
MCP `context7` и `playwright` не изменялись — только дописан сосед `serena`.

## 8. Стоп-условия

| Условие | Сработало? |
|---|---|
| Serena не устанавливается | нет — вышло после `--python 3.13` |
| Конфиг ломается | **ДА, дважды** — `{env:PATH}` и V2-`permissions`; оба устранены, V1 CLI снова exit 0 |
| Агент auditor не появляется в десктопе | не проверено (нужен GUI) |
| MCP context7 / playwright перестают работать | нет — connected в обоих рантаймах |

# GIT_COURER_SETUP — установка Go + git-courer + MCP для OpenCode

**Дата:** 2026-10-07
**Машина:** DESKTOP-H4A2TAT, Windows, пользователь `TshK` (НЕ администратор)
**Ветка проекта:** v5.6-dev (не коммитилась — по правилу «НЕ коммитить в проект»)
**Статус:** 🛑 **СТОП на Блоке B.** Go не установлен, дальнейшие блоки не выполнялись.

---

## Итог одной строкой

План не выполним в текущем виде: `msiexec` требует прав администратора
(код выхода **1603**), а версия Go из плана (**1.23.5**) ниже требованиям
git-courer (**go 1.26**). Нужен выбор владельца между двумя путями — см. §9.

---

## 1. Альтернативы: choco / scoop

| Проверка | Результат |
|---|---|
| `choco -v` | ❌ не найден |
| `scoop --version` | ❌ не найден |
| `winget` | ❌ отсутствует (задано в контексте) |
| `go version` | ❌ не найден (Go не установлен) |
| `C:\Go` | ❌ не существует |
| `C:\Program Files\Go` | ❌ не существует |
| `$HOME\go` | ❌ не существует |
| `$HOME\scoop` | ❌ не существует |
| `C:\tools\go` | ❌ не существует |
| Права администратора | ❌ `IsAdmin: False` |

**Вывод Блока A:** ни один пакетный менеджер недоступен → переход к Блоку B.

---

## 2. Скачивание MSI и установка

### 2.1 Скачивание — ✅ успешно

| Параметр | Значение |
|---|---|
| URL | `https://go.dev/dl/go1.23.5.windows-amd64.msi` |
| Куда | `C:\Users\TshK\AppData\Local\Temp\go-installer.msi` |
| Размер | 67 502 080 байт = **64.38 МБ** |
| Проверка «> 40 МБ» | ✅ пройдена |
| Файл сохранён | ✅ (оставлен для ручной установки — см. §9) |

### 2.2 Установка — 🛑 провал

| Параметр | Значение |
|---|---|
| Команда | `msiexec /i go-installer.msi /quiet /norestart /l*v go-install.log` |
| **Код выхода** | **1603** (`ERROR_INSTALL_FAILURE`) |
| Лог | `C:\Users\TshK\AppData\Local\Temp\go-install.log` (5 523 094 байт) |

**Причина из лога установки (цитата):**

```
DEBUG: Error 2503:  Called RunScript when not marked in progress.
MSI (s) (58:9C): Product: Go Programming Language amd64 go1.23.5 --
  The installer has encountered an unexpected error installing this package.
  The error code is 2503.
MSI (s) (58:9C): Note: 1: 2203 2: C:\Windows\Installer\inprogressinstallinfo.ipi
  3: -2147287035
Action ended 13:21:22: InstallFinalize. Return value 3.
DEBUG: Error 2502:  Called InstallFinalize when no install in progress.
```

Диагноз: MSI не может создать/записать служебный файл
`C:\Windows\Installer\inprogressinstallinfo.ipi` (ошибка 2203) → ошибки
2502/2503 → откат. Это классический символ установки **без прав
администратора**, а не повреждение пакета.

### 2.3 Состояние после провала — чистое ✅

| Проверка | Результат |
|---|---|
| `C:\Go` | не существует (частичной установки нет) |
| `PATH` (Machine) | записей с «Go» нет |
| `GoEnvironmentEntries` | пусто |
| Реестр `Uninstall\*` → «Go Programming Language» | не зарегистрирован |
| MSI-файл | сохранён в TEMP для ручной установки |

**Побочных изменений в системе нет.** Можно продолжать с любого варианта ниже.

---

## 3. go version

**Не установлен.** Команда `go version` не выполнялась успешно ни разу —
`go` отсутствует в PATH.

### 3.1 ⚠️ Блокер, не замеченный в плане: версия Go слишком старая

`git-courer` требует **Go 1.26** — это директива в его `go.mod`:

```
module github.com/blak0p/git-courer

go 1.26
```

(источник: `https://raw.githubusercontent.com/blak0p/git-courer/main/go.mod`)

План предлагал установить **go1.23.5** (декабрь 2024). Даже если бы MSI
поставился, `go install github.com/blak0p/git-courer@latest` потребовал бы
toolchain ≥ 1.26.

**Актуальные стабильные версии на 2026-10-07** (источник: `https://go.dev/dl/?mode=json`):

| Версия | Статус | windows-amd64.msi | windows-amd64.zip |
|---|---|---|---|
| **go1.27.1** | stable (2026-08-28) | 66 088 960 Б | 78 931 360 Б |
| go1.26.8 | stable | 62 316 544 Б | 74 957 586 Б |

SHA-256 для проверки целостности:

```
go1.27.1.windows-amd64.zip  a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d
go1.27.1.windows-amd64.msi  54dbabbc910840fce0028779e896cd99a22bdf89463354a1ca0d9288044dc6e7
```

**Рекомендация:** ставить **go1.27.1** — он покрывает требование `go 1.26`
с запасом.

---

## 4. git-courer: версия, путь

**Не устанавливался.** Блок C не выполнялся: `go install` не запускался,
т.к. Go отсутствует.

| Проверка | Ожидание по плану | Факт |
|---|---|---|
| `Test-Path "$HOME\go\bin\git-courer.exe"` | True | ❌ False (каталога `$HOME\go` нет) |
| `git-courer version` | версия | ❌ команда не найдена |
| Добавление `$HOME\go\bin` в User PATH | выполнено | ❌ **не выполнялось**, PATH не тронут |

Зависимости git-courer, которые видны в `go.mod` и повлияют на сборку:
`mcp-go v0.55.1`, `bubbletea v1.3.10`, `glamour v1.0.0`, `go-gitdiff v0.8.1`.

---

## 5. Ollama: config.yaml

### 5.1 D1 — проверка Ollama ✅ успешно

| Проверка | Результат |
|---|---|
| `ollama list` | работает |
| `qwen-coder-top:latest` | ✅ есть, ID `05f36ebc4a99`, 4.7 GB |
| Дополнительно в списке | `qwen2.5-coder:7b`, `qwen2.5:7b-instruct` |
| API `http://localhost:11434/api/tags` | ✅ отвечает, возвращает 3 модели |

### 5.2 D2 — `~/.config/git-courer/config.yaml` НЕ создан

Файл **не создан намеренно**, по двум причинам:

1. **Правило верификации:** конфиг писать без проверяемого бинарника
   нельзя — `git-courer doctor` нечем запустить, схему нечем подтвердить.
   Задание D2 дословно повторяет README git-courer, но не проверено ни
   одной командой.
2. **Каталога `~/.config/git-courer` не существует.** В `~/.config` сейчас
   только `opencode/`.

**Что нужно проверить перед записью** (когда появится бинарник):
`git-courer doctor`, `git-courer config --help` — фактические имена ключей
(`provider`, `base_url`, `model`), путь конфига и формат (`yaml` vs `toml`:
в `go.mod` присутствуют **оба** — `gopkg.in/yaml.v3` и `BurntSushi/toml`;
какой из них основной для `~/.config/git-courer/config.yaml` — не подтверждено).

---

## 6. MCP для OpenCode

**Не выполнялось** — блок заблокирован отсутствием git-courer.

### 6.1 ⚠️ Найден конфликт: git-courer пишет не в тот файл

| Источник | Ожидаемый путь конфига |
|---|---|
| Документация git-courer (`docs/mcp-clients.md`) | `~/.config/opencode/opencode.json` (формат JSON) |
| Задание, блок E2/E3 | `~/.config/opencode/opencode.jsonc` |
| **Фактически на машине** | **`~/.config/opencode/opencode.jsonc`** (11 687 Б) |

```
opencode.json  exists: False
opencode.jsonc exists: True
```

Вся текущая MCP-конфигурация лежит в `opencode.jsonc`, блок `"mcp"` —
с **строки 132**:

| Строка | Сервер | Статус |
|---|---|---|
| 133 | `serena` | активен (29 tools) |
| 152 | `context7` | активен (2 tools) |
| 156 | `exa` | `enabled: false` — выключен намеренно |
| 164 | `playwright` | активен (25 tools) |
| 168 | `duckdb` | выключен намеренно |
| 4 | плагины | `@azumag/opencode-rate-limit-fallback@1.70.11`, `@andrewhampton/opencode-handoff` |

**Риск (стоп-условие «Конфликт с context7 / playwright / serena → СТОП»):**
если `git-courer mcp setup opencode` создаст новый `opencode.json`, возможны
два сценария — либо OpenCode начнёт читать только его и **потеряет 5 MCP-серверов**,
либо MCP не подключится вовсе. Какой именно — зависит от порядка приоритета
файлов в OpenCode, который в этом прогоне не проверялся (проверка требует
перезапуска Desktop, Блок G).

**Дополнительные правки, которые внесёт `git-courer mcp setup opencode`:**
- `permission.bash["git *"] = "ask"` — OpenCode начнёт спрашивать перед
  **сырыми git-командами**; в `AGENTS.md` проекта прямо запрещено
  `git checkout`/`reset` без stash и `git merge`, так что лишние
  подтверждения ожидаемы, но это изменение поведения.
- `instructions[]` — добавится путь к `~/.config/opencode/AGENTS.md`.
- Блок `<!-- git-courer start -->` … `<!-- git-courer end -->` в
  `~/.config/opencode/AGENTS.md` («Golden Rules»).
- Бэкап: `opencode.json` → `opencode.json.bak`. **Обратите внимание:**
  бэкапируется `opencode.json`, а не `opencode.jsonc` — то есть
  `opencode.jsonc.bak` git-courer не создаст и текущий конфиг окажется
  без страховой копии.

Уже существующие бэкапы в каталоге (свидетельство прошлых правок конфига):
`opencode.jsonc.bak` (2 242 Б), `opencode.jsonc.bak-serena` (1 870 Б).

### 6.2 Что осталось непроверенным

`Select-String -Pattern "context7|playwright|serena"` после setup — **не
выполнялось**, так как setup не запускался.

---

## 7. Провайдер Ollama в OpenCode

**Не выполнялось** — блок F не запускался (нет бинарника для проверки).
Фрагмент `"ollama": { "npm": "@ai-sdk/openai-compatible", … }` в
`opencode.jsonc` **не добавлен**.

Для применения потребуется:
1. ручная правка `~/.config/opencode/opencode.jsonc` через Edit
   (регулярки по JSONC запрещены правилами);
2. проверка валидности — с учётом того, что файл **JSONC**, а не JSON:
   комментарии в нём есть (строки 7, 35, 45, 59–131), поэтому `jq`/`
   ConvertFrom-Json` применять нельзя — только через JSONC-парсер;
3. перезапуск OpenCode.

---

## 8. Проверка: git status через MCP

**Не выполнялась.** Требуется рабочий бинарник git-courer.

| Шаг плана | Статус |
|---|---|
| G1. Перезапуск OpenCode Desktop | ⛔ |
| G2. Settings → Расширения → MCP: git-courer | ⛔ |
| G3. Список моделей: Ollama (local) / Qwen Coder Top | ⛔ |
| G4. «Покажи git status через MCP» → JSON | ⛔ |
| G5. `git-courer doctor` — все зелёные | ⛔ |

---

## 9. Вопросы владельцу

### 9.1 Главный: как ставить Go без прав администратора?

Два рабочих пути. **Нужен выбор.**

**Вариант А — ручная установка MSI (безопасный, требует вас)**
Учётная запись не админ, поэтому агент MSI установить не может.
1. Откройте `C:\Users\TshK\AppData\Local\Temp\go-installer.msi` (уже скачан, 64.38 МБ)
   — **или** скачайте заново, но версию **1.27.1**, не 1.23.5:
   `https://go.dev/dl/go1.27.1.windows-amd64.msi` (66 088 960 Б)
2. Двойной клик → UAC «Да» → установка.
3. Перезапуск PowerShell.
4. Сообщить — продолжу с Блока C.

**Вариант Б — ZIP-архив, права администратора не нужны (рекомендую)**
Go официально распространяется ZIP-версией; распаковка в пользовательский
каталог полностью обходится без UAC.
1. Скачать `go1.27.1.windows-amd64.zip` (78 931 360 Б) с `https://go.dev/dl/`
2. Распаковать в `C:\Users\TshK\go-toolchain\` (получится `...\go\`)
3. Добавить `C:\Users\TshK\go-toolchain\go\bin` в **User PATH**
4. `go version` → `go version go1.27.1 windows/amd64`

Побочный эффект: `GOPATH` по умолчанию станет `C:\Users\TshK\go`,
т.е. бинарник `git-courer.exe` ляжет в `C:\Users\TshK\go\bin\git-courer.exe`
ровно туда, где его и ждёт Блок C (`$HOME\go\bin`). Согласуйтесь, если
каталог `C:\Users\TshK\go` уже занят чем-то нужным — сейчас он свободен.

### 9.2 Про конфликт конфигов (нужно решить до Блока E)

| # | Вопрос |
|---|---|
| 1 | Разрешаете ли переименовать/конвертировать конфиг, чтобы git-courer и OpenCode читали один файл? |
| 2 | Если нет — заносим ли `git-courer mcp setup opencode` в запрет и прописываем MCP-блок вручную через Edit в `opencode.jsonc`? |
| 3 | Нужен ли резервный канонический бэкап `opencode.jsonc.bak-git-courer` перед правкой? |

### 9.3 Про `permission.bash["git *"] = "ask"`

git-courer добавит правило «спрашивать перед сырыми git-командами».
Согласны на это изменение поведения в рамках проекта, где git-команды
используются постоянно?

### 9.4 Про провайдера Ollama

| # | Вопрос |
|---|---|
| 1 | Оставляем ли `qwen-coder-top:latest` (4.7 GB) единственной локальной моделью, или добавить `qwen2.5-coder:7b` / `qwen2.5:7b-instruct`? |
| 2 | Нужны ли модели вручную (OpenCode иногда не подхватывает Ollama без явного описания), или хватит автообнаружения? |

### 9.5 Гигиена

В рабочем дереве проекта остались неотслеженные артефакты предыдущей
сессии аудита (`_tmp_analyze.py` и др.). Удалить их или оставить?
В рамках этого задания ничего в проекте не менялось и не коммитилось.

---

## 10. Что было сделано / не сделано

| Блок | Содержание | Статус |
|---|---|---|
| A | choco / scoop / go | ✅ проверено, ничего нет |
| B | MSI скачать | ✅ 64.38 МБ |
| B | MSI установить | 🛑 **1603 — нет прав администратора** |
| C | go install git-courer | ⛔ заблокировано |
| D | Ollama проверить | ✅ работает, 3 модели |
| D | config.yaml создать | ⛔ отложено до проверки бинарником |
| E | mcp setup opencode | ⛔ заблокировано + ⚠️ конфликт `opencode.json` vs `.jsonc` |
| F | провайдер Ollama | ⛔ заблокировано |
| G | перезапуск и проверка | ⛔ заблокировано |

**Стоп-условие сработало:** «msiexec падает → СТОП, отчёт».

---

## 11. Приложение: что проверено и как

| Проверка | Команда / источник | Результат |
|---|---|---|
| choco, scoop, go | `choco -v`, `scoop --version`, `go version` | не найдены |
| Права админа | `[Security.Principal.WindowsPrincipal]::IsInRole(...)` | False |
| Скачивание MSI | `Invoke-WebRequest` + проверка размера | 64.38 МБ ✅ |
| Установка MSI | `Start-Process msiexec -Wait -PassThru` | ExitCode 1603 |
| Причина отказа | разбор `go-install.log` | Error 2502/2503, Note 2203 |
| Чистота после провала | `Test-Path C:\Go`, реестр `Uninstall\*` | чисто ✅ |
| Требование Go | `raw.githubusercontent.com/blak0p/git-courer/main/go.mod` | `go 1.26` |
| Актуальные версии Go | `https://go.dev/dl/?mode=json` | 1.27.1 / 1.26.8 |
| Целевой конфиг OpenCode | `docs/mcp-clients.md` (git-courer) | `opencode.json` |
| Реальный конфиг OpenCode | `Test-Path` / `Select-String` | `opencode.jsonc`, 5 MCP |
| Ollama | `ollama list`, `/api/tags` | ✅ 3 модели, порт 11434 |

Все выводы получены реальными командами или чтением файлов — ни одно
утверждение в отчёте не взято из памяти.

---

## 12. Решение владельца (2026-10-07, после §9)

| Вопрос | Решение |
|---|---|
| Как ставить Go | **Вариант Б — ZIP**, без прав администратора (владелец ставит сам) |
| Конфликт `opencode.json` / `.jsonc` | **Запретить `git-courer mcp setup opencode`**, MCP-блок прописать вручную через Edit в `opencode.jsonc` |

### 12.1 Что уже подготовлено

| Проверка | Результат |
|---|---|
| Бэкап `opencode.jsonc.bak-git-courer` | ✅ создан, 11 687 Б (совпадает с оригиналом) |
| Место вставки MCP-записи | ✅ строка **183**, между `}` блока `duckdb` (182) и `}` блока `mcp` (183) |
| Формат записи (из `docs/mcp-clients.md`) | `"type": "local"`, `"enabled": true`, `"command": [<путь>, "mcp"]` |

Запись, которая будет добавлена (после появления бинарника):

```jsonc
    "git-courer": {
      "type": "local",
      "enabled": true,
      "command": [
        "C:\\Users\\TshK\\go\\bin\\git-courer.exe",
        "mcp"
      ]
    }
```

### 12.2 Инструкция владельцу — установка Go (Вариант Б)

Прав администратора не требуется. SHA-256 обязателен: подменённый архив
даст бинарник, который падает через месяц без внятной ошибки.

```powershell
# 1. Скачать (78 931 360 байт)
$zip = "$env:TEMP\go1.27.1.windows-amd64.zip"
Invoke-WebRequest -Uri "https://go.dev/dl/go1.27.1.windows-amd64.zip" -OutFile $zip -UseBasicParsing

# 2. Проверить хеш
(Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
# ожидание: a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d

# 3. Распаковать (получится C:\Users\TshK\go-toolchain\go)
Expand-Archive -Path $zip -DestinationPath "$HOME\go-toolchain" -Force

# 4. Добавить go\bin в User PATH
[Environment]::SetEnvironmentVariable("Path",
  [Environment]::GetEnvironmentVariable("Path","User") + ";$HOME\go-toolchain\go\bin",
  "User")

# 5. НОВЫЙ PowerShell, затем:
go version
```

Ожидание: `go version go1.27.1 windows/amd64`

**Замечание о шаге 4.** `GOPATH` по умолчанию = `%USERPROFILE%\go`, поэтому
`go install` положит бинарник в `C:\Users\TshK\go\bin\git-courer.exe` —
это и есть путь из §12.1. Каталог `C:\Users\TshK\go` сейчас свободен.

### 12.3 Известные расхождения из-за ручной настройки

Отказ от `git-courer mcp setup opencode` означает, что не выполнятся:

| Что делает setup | Последствие ручного режима |
|---|---|
| Инъект блока Golden Rules в `~/.config/opencode/AGENTS.md` | не будет; `git-courer doctor` покажет `prompt block injected: false` |
| `permission.bash["git *"] = "ask"` | не появится — сырые git-команды не будут спрашивать (для этого проекта, вероятно, плюс) |
| `instructions[]` += путь к AGENTS.md | не добавится |
| Бэкап `opencode.json.bak` | не создастся; **наш бэкап `opencode.jsonc.bak-git-courer` сделан вручную** |

Если понадобится любое из этих поведений — добавляется точечной правкой
через Edit после ручной установки.

### 12.4 Остаток плана

| Шаг | Готово к запуску |
|---|---|
| `go install github.com/blak0p/git-courer@latest` | после шага 5 инструкции §12.2 |
| `git-courer version` | сразу после |
| `~/.config/git-courer/config.yaml` | после — сначала сверить ключи через `git-courer --help` |
| Блок D3 `git-courer doctor` | после |
| Блок E — ручная вставка MCP (см. §12.1) | после появления `.exe` |
| Блок F — провайдер Ollama в `opencode.jsonc` | после |
| Блок G — перезапуск OpenCode | вручную владельцем |

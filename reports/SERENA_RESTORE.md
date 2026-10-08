# SERENA RESTORE — восстановление MCP-сервера Serena после удаления Ollama

**Дата:** 2026-10-08
**Ветка:** `v5.6-dev`
**HEAD на момент работы:** `1a8bee8`
**Автор:** OpenCode (Space Bunny)
**Статус:** ✅ восстановлено и проверено

---

## 1. Диагностика — что сломано

### 1.1 Симптом

Serena не подключалась: `failed to locate pyvenv.cfg`, uvx завершался с кодом **106**.

Воспроизведено напрямую:

```
> uvx --from git+https://github.com/oraios/serena serena --help
uvx.exe : failed to locate pyvenv.cfg: ...
exit=106
```

### 1.2 Конфиг — НЕ причина

Проверен `C:\Users\TshK\.config\opencode\opencode.jsonc` (13 378 B), блок `mcp.serena` (строки 146–164):

```jsonc
"serena": {
  "type": "local",
  "command": [
    "C:\\Users\\TshK\\.local\\bin\\uvx.exe",
    "--python", "3.13",
    "--from", "git+https://github.com/oraios/serena",
    "serena-agent",
    "start-mcp-server",
    "--context", "desktop-app",
    "--project", "C:\\analytics\\brain-25-evidence"
  ],
  "environment": {
    "Path": "C:\\Users\\TshK\\.local\\bin;C:\\Windows\\system32;..."
  }
}
```

Конфиг цел и корректен:

- абсолютный путь к `uvx.exe` присутствует и **существует на диске**;
- ссылок на Ollama, `ollama`, `qwen`, `llama` в конфиге **нет вообще**;
- блок `environment.Path` на месте — он обязателен, чтобы Serena смогла запустить собственный LSP (см. комментарий в конфиге, строки 114–124);
- рядом лежат рабочие `codebase-memory`, `context7`, `playwright`, `git`.

**Вывод: удаление Ollama не затронуло конфиг.** Правки конфига не потребовалось.

### 1.3 uvx — НЕ причина

| Проверка | Результат |
|---|---|
| `uvx.exe` по абсолютному пути | существует |
| `uvx --version` | `uvx 0.12.23 (46b84fd0b 2026-10-03 x86_64-pc-windows-msvc)` |
| `uv --version` | `uv 0.12.23` |
| `uvx ruff --version` (свежая загрузка) | **exit 0**, `ruff 0.16.10`, скачал и установил за 10 мс |
| `Get-Command uvx` | `C:\Users\TshK\.local\bin\uvx.exe` |

**uvx полностью работоспособен.** Стоп-условие задачи «uvx сломан → СТОП» **не сработало**: uvx запускает и устанавливает пакеты из PyPI без проблем.

Также проверено: ошибка **не зависит от рабочей директории** — из `C:\analytics\brain-25-evidence` и из `C:\Users\TshK` результат одинаковый (exit 106). Значит дело не в `.venv` проекта и не в `.python-version` (их в проекте нет).

Переменных окружения, влияющих на uv, нет: `UV_*`, `VIRTUAL_ENV`, `PYTHONHOME` отсутствуют (кроме выставленного мной `PYTHONIOENCODING`).

### 1.4 Настоящая причина — частично удалённый venv в кэше uv

Раскладка кэша `C:\Users\TshK\AppData\Local\uv\cache` (368 МБ в `archive-v0`, 103 записи):

```
environments-v2\4038fe31ffc2e0cc\f22136f6d5c179ea  ->  archive-v0/myaS5vHi_GSiQugK   dir=True  pyvenv.cfg=True
environments-v2\813a14c70e7ce89c\642f06692a321dbe  ->  archive-v0/OLMXgUSHfE6codo1   dir=True  pyvenv.cfg=True   (pyright)
environments-v2\813a14c70e7ce89c\74a54b0586996283  ->  archive-v0/azjySVThO6UXGB6A   dir=True  pyvenv.cfg=True   (ruff)
environments-v2\813a14c70e7ce89c\7bcc5658fd6c49b8  ->  archive-v0/cncnVWX9O7j0HOPp   dir=True  pyvenv.cfg=True   (mcp-server-git)
environments-v2\813a14c70e7ce89c\f22136f6d5c179ea  ->  archive-v0/5Us7Lmx5c5UPnFD3   dir=True  pyvenv.cfg=FALSE  <-- SERENA
```

Указатели — это 27-байтные файлы, в которых лежит относительный путь к venv. Четыре из пяти указывают на целые окружения. Пятый — на `5Us7Lmx5c5UPnFD3`, где **сам каталог существует, но `pyvenv.cfg` отсутствует**:

```
archive-v0\5Us7Lmx5c5UPnFD3\
└── Scripts\
    ├── python.exe              (241 152 B)
    ├── pythonw.exe             (237 056 B)
    ├── serena-agent.exe        ( 47 104 B)
    ├── serena-hooks.exe        ( 47 104 B)
    ├── serena.exe              ( 47 104 B)
    ├── tqdm.exe, uvicorn.exe
    └── pywin32_*.exe / .py
```

Сравнение с целым venv того же назначения:

```
archive-v0\myaS5vHi_GSiQugK\      <- рабочий, 176 пакетов
├── Lib\
├── Scripts\
├── .gitignore
├── CACHEDIR.TAG
└── pyvenv.cfg                    <- есть
```

Отсутствуют в сломанном: **`pyvenv.cfg`, `Lib\`, `CACHEDIR.TAG`, `.gitignore`**. Уцелели ровно те файлы, что лежат в `Scripts\`, — то есть удаление было неполным, по каталогам.

Именно это и даёт `failed to locate pyvenv.cfg`: uv находит указатель, переходит в каталог, не находит `pyvenv.cfg` и прерывает запуск с кодом 106. Никакого отношения к Ollama у этого состояния нет — это **полуудавленное виртуальное окружение с оставшимся указателем**.

Отдельно проверено, что в кэше есть и **полностью целый** venv Serena (`myaS5vHi_GSiQugK`, 176 пакетов, `PyYAML`, `bottle`, `flask`, 175 записей в `Scripts`) под другим указателем. То есть зависимости не потеряны, пересобирать с нуля с интернетом не нужно.

Управляемые Python uv на месте и целы:

```
C:\Users\TshK\AppData\Roaming\uv\python\cpython-3.13-windows-x86_64-none\        python.exe есть
C:\Users\TshK\AppData\Roaming\uv\python\cpython-3.13.16-windows-x86_64-none\      python.exe есть
```

Все `pyvenv.cfg` в кэше указывают на эти каталоги, оба существуют.

---

## 2. Решение — что сделано

Применено **точечное** исправление вместо `uv cache clean --force` из блока B2 задания. Причина: полная очистка снесла бы 368 МБ кэша и заставила заново скачивать pyright, ruff и mcp-server-git ради одной сломанной записи.

```powershell
$cache = "$env:LOCALAPPDATA\uv\cache"
Remove-Item "$cache\environments-v2\813a14c70e7ce89c\f22136f6d5c179ea" -Force
Remove-Item "$cache\archive-v0\5Us7Lmx5c5UPnFD3" -Recurse -Force
```

Удалены ровно два объекта:

| Объект | Что это | Размер |
|---|---|---|
| `environments-v2\813a14c70e7ce89c\f22136f6d5c179ea` | битый указатель (27 B) | 27 B |
| `archive-v0\5Us7Lmx5c5UPnFD3` | опустевший venv (только `Scripts\`) | 837 359 B |

Ни `pip install --upgrade uv`, ни `uv cache clean --force`, ни переустановка uv **не понадобились** — uv 0.12.23 актуален и исправен.

Пересборка окружения:

```
> uvx --refresh --python 3.13 --from git+https://github.com/oraios/serena serena --help
Installed 77 packages in 473ms
Usage: serena [OPTIONS] COMMAND [ARGS]...
exit=0
```

`--refresh` принудил uv пересобрать окружение, а не взять из кэша. Ответ пришёл из локального кэша за 473 мс — сеть не понадобилась.

---

## 3. Проверка — Serena работает

### 3.1 CLI

```
uvx --from git+https://github.com/oraios/serena serena --help   → exit 0
```

### 3.2 Реальная команда из конфига — MCP handshake по stdio

Проверена **ровно та строка**, что лежит в `opencode.jsonc`, без `--refresh`, с тем же `environment.Path` и тем же `cwd`:

```
cmd: uvx.exe --python 3.13 --from git+https://github.com/oraios/serena serena-agent
     start-mcp-server --context desktop-app --project C:\analytics\brain-25-evidence

*** MCP initialize УСПЕШЕН ***
serverInfo: {"name": "Serena", "version": "2.0.0.dev0",
             "websiteUrl": "https://oraios.github.io/serena"}
capabilities: experimental, prompts, resources, tools
tools/list: 29 инструментов
  create_text_file, replace_content, replace_in_files, replace_symbol_body,
  insert_after_symbol, insert_before_symbol, read_file, list_dir, find_file,
  search_for_pattern, get_symbols_overview, find_symbol, ...
RESULT: OK
```

### 3.3 Языковые серверы поднялись

Второй режим отказа, описанный в комментариях конфига (`Failed to start 1 language server(s): python: Could not find 'uvx' or 'uv' in PATH`), тоже закрыт:

```
[StartLS:typescript] Starting TypeScript server process
                    TypeScript server version: 5.9.3
                    TypeScript server is ready

[StartLS:python]     Loading document symbols cache from
                     C:\analytics\brain-25-evidence\.serena\cache\python\document_symbols.pkl
                    Loaded 145 entries from document symbols cache.
                    Starting pyright-langserver server process
                    via: ['C:\Users\TshK\.local\bin\uvx.EXE', '-p', '3.13',
                          '--from', 'pyright==1.1.403', ...]
```

Оба LS стартуют через абсолютный путь к `uvx`, который задаёт `environment.Path` в конфиге. Именно ради этого в конфиге записан литерал `Path` с удвоенными слэшами — замена на `{env:PATH}` ломает файл (`InvalidEscapeCharacter`, см. комментарий на строках 126–133).

### 3.4 Смежные MCP не задеты

`codebase-memory`, `context7`, `playwright`, `git` используют тот же `uvx.exe`. `uvx ruff` и `uvx mcp-server-git` работают, кэш для `pyright` и `mcp-server-git` цел — точечное удаление не задело их окружения.

---

## 4. Конфиг — не сломан

| Пункт | Статус |
|---|---|
| Блок `mcp.serena` в `opencode.jsonc` | корректен, правок не потребовал |
| Ссылка на Ollama / qwen / llama в конфиге | отсутствует |
| Абсолютный путь к `uvx.exe` | есть, файл на диске существует |
| `environment.Path` (нужен для LSP) | есть, значение корректное |
| Формат JSONC | валиден |
| Резервные копии конфига | `opencode.jsonc.bak`, `.bak-git-courer`, `.bak-serena` — не тронуты |

---

## 5. Вопросы владельцу

1. **Нужен ли рестарт OpenCode Desktop.** Сервер восстановлен на диске, но процесс MCP в уже запущенном Desktop был создан до починки и держит старый (упавший) handle. Нужен перезапуск приложения — это шаги B4 и B5 задания, выполнить их из сессии я не могу. После рестарта Serena должна появиться в списке MCP; если нет — проверьте, что она включена в настройках.

2. **Что именно удалило venv.** Состояние «остались только `Scripts\`, удалены `pyvenv.cfg`, `Lib\`, `CACHEDIR.TAG`» — почерк удаления по содержимому каталога, а не по расширению файлов. Ollama так не удаляет. Возможные виновники: `uv cache prune`, сторонняя утилита очистки, ручное удаление содержимого. Если причина повторится, та же поломка вернётся — стоит тогда чинить кэш uv шире, а не точечно.

3. **Почему рядом лежал второй, целый venv Serena** (`myaS5vHi_GSiQugK`, 176 пакетов) под другим указателем `4038fe31ffc2e0cc`. Похоже на два разных способа разрешения одного источника. Если Serena и дальше будет запускаться то через `--from git+...`, то через установленный инструмент — имеет смысл привести к одному, чтобы не плодить окружения. Сейчас это не мешает.

4. **Стоит ли добавить автопроверку.** Падение этого типа тихое: MCP просто не подключается, причина — в кэше стороннего инструмента. Проверка `uvx --from git+... serena --version` в `watchdog.yml` (раз в неделю) поймала бы это заранее.

5. **Отчёт не закоммичен.** Файл создан, но `git add` / `git commit` не выполнял — git-операции только по явной команде. Скажите, если нужно закоммитить в `v5.6-dev`.

---

## 6. Итог

| Пункт задания | Итог |
|---|---|
| A1 конфиг | не сломан |
| A2 uvx | работает, 0.12.23 |
| A3 кэш uv | существует, 368 МБ, найден битый указатель |
| A4 запуск serena | воспроизведена ошибка, exit 106 |
| B1 переустановка uv | **не потребовалась** |
| B2 очистка кэша | выполнена **точечно**, не `clean --force` |
| B3 проверка конфига | подтверждения поломки нет |
| B4 рестарт Desktop | **требует действия владельца** |
| B5 проверка вкладки MCP | **требует действия владельца** |
| Стоп-условия | **не сработали ни одно** |

Вложенные скрипты диагностики (`_tmp_env*.py`, `_tmp_serena_mcp.py`) удалены после работы.
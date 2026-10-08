# CODEBASE_MEMORY_INSTALL — установка codebase-memory-mcp

Дата: 2026-10-07 · Ветка: v5.6-dev · Режим: установка + проверка

---

## 1. Версия

```
codebase-memory-mcp 0.11.0
```

Релиз: v0.11.0 (15 сентября 2026). Скачан вручную:
`codebase-memory-mcp-windows-amd64.zip` (39.9 МБ), SHA256 проверен.

---

## 2. Как установлен

**Вручную**, не через `install.ps1` — установщик упал из-за обработки stderr
в PowerShell (предупреждение `daemon.client.rendezvous_wait status=absent`
воспринято как ошибка). Бинарник скопирован вручную:

```
C:\Users\TshK\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe
```

Добавлен в пользовательский PATH (не системный, без прав администратора).

Флаг `--skip-config` использован: существующие конфиги агентов не тронуты.

---

## 3. MCP добавлен в конфиг

`C:\Users\TshK\.config\opencode\opencode.jsonc`, блок `mcp`:

```jsonc
"codebase-memory": {
  "type": "local",
  "enabled": true,
  "command": ["codebase-memory-mcp"]
}
```

Конфиг валиден (проверено через node JSONC parser). Существующие MCP не тронуты:

| MCP | Статус |
|---|---|
| serena | ✅ на месте |
| context7 | ✅ на месте |
| playwright | ✅ на месте |
| git | ✅ на месте |
| codebase-memory | ✅ добавлен |

---

## 4. Плагин: V1 или V2 формат?

**Плагин не сгенерирован** — ожидаемо при `--skip-config`. Файл
`.opencode/plugins/cbm-augment.ts` отсутствует.

Issue #2077 (V1/V2 shape) закрыт в PR #2089, но поскольку плагин не генерировался,
проверить его формат невозможно. Рекомендация: не генерировать плагин, использовать
MCP-сервер напрямую.

---

## 5. Проверка в Desktop

**Требуется перезапуск OpenCode Desktop** — MCP подхватывается при старте.
После перезапуска проверить: Settings → Расширения → MCP → `codebase-memory`.

---

## 6. Граф-запрос: работает?

**Да.** Индексация прошла успешно:

```
project: C-analytics-brain-25-evidence
nodes: 228128
edges: 236923
status: indexed
```

Тестовый запрос `search_graph --name_pattern "openModal"`:

```
C-analytics-brain-25-evidence.docs.script.openModal Function docs/script.js 590-678 3 19
```

Данные из **правильного проекта** (brain-25-evidence), не из чужого.

### Проблема: persist_failed на стандартном кэше

При индексации с кэшем по умолчанию (`~/.cache/codebase-memory-mcp/`) получен:

```json
{"status":"persist_failed","hint":"The validated staging database could not be published.
Check free disk space and permissions on the cache directory"}
```

**Решение**: явно задать `CBM_CACHE_DIR` в разрешённое место:

```
C:\Users\TshK\AppData\Local\Temp\opencode\cbm-cache
```

С этим кэшем индексация прошла успешно. Рекомендация: добавить `CBM_CACHE_DIR`
в `environment` блок MCP-конфига, либо разобраться с правами на
`~/.cache/codebase-memory-mcp/`.

---

## 7. Существующие MCP: не сломались?

| MCP | Проверка |
|---|---|
| serena | ✅ в конфиге, не тронут |
| context7 | ✅ в конфиге, не тронут |
| playwright | ✅ в конфиге, не тронут |
| git | ✅ в конфиге, не тронут |

V1 CLI (`opencode mcp list`) падает с ошибкой `V2 permissions are not supported
by OpenCode V1` — эта ошибка **была до моей правки** (проверено на оригинальном
конфиге). Связана с `agents.local-fast.permissions`, не с MCP.

---

## 8. Вопросы владельцу

1. **Перезапустить Desktop** для применения MCP-конфига.
2. **CBM_CACHE_DIR** — добавить в конфиг или оставить как есть?
3. **Плагин** — генерировать или использовать только MCP-сервер?
4. **Watcher** — отключить (`config set watcher_enabled false`) или оставить?

---

## 9. СТОП-условия

| Условие | Статус |
|---|---|
| Установка ломает существующий конфиг | Нет — конфиг валиден, ошибка V1 была до правки |
| Сервер возвращает данные из другого проекта | Нет — граф возвращает данные из brain-25-evidence |
| Требует прав администратора | Нет — установлен в пользовательский PATH |

---

## 10. Следующие шаги

1. Перезапустить OpenCode Desktop.
2. Проверить в Settings → MCP: `codebase-memory` виден.
3. Дать агенту задачу: «Используй codebase-memory: найди определение функции openModal».
4. Ожидание: граф находит определение быстро (sub-ms queries).

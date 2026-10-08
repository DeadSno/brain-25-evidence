# CODEBASE_MEMORY_RESEARCH — codebase-memory-mcp с OpenCode v2.0.24

Дата: 2026-10-07 · Ветка: v5.6-dev · Режим: только чтение, ничего не установлено

**Ответ на главный вопрос: работает ли напрямую, без плагина — Да.**
codebase-memory-mcp по умолчанию является автономным MCP-сервером (17 инструментов).
Плагин `cbm-augment.ts` — опциональный слой поверх, и именно он сломан в #2077.
Прямое использование через `opencode.jsonc` → `mcp` не затрагивается этой ошибкой.

---

## 1. Как ставится, что даёт

### Установка на Windows

```powershell
# 1. Скачать установщик
Invoke-WebRequest -Uri https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.ps1 -OutFile install.ps1

# 2. (Рекомендуется) Прочитать скрипт
notepad install.ps1

# 3. Снять Mark-of-the-Web
Unblock-File .\install.ps1

# 4. Запустить
.\install.ps1
```

Опции: `--skip-config` (только бинарник, без настройки агентов), `--dir=<path>`.

Другие каналы: npm, PyPI, Homebrew, Scoop, Winget, Chocolatey, AUR, `go install`.
Сборка из исходников: C-компилятор + zlib, `scripts/build.sh --with-ui`.

### Что даёт

- **17 MCP-инструментов**: search, trace, architecture, impact analysis, Cypher-запросы, dead code detection, cross-service HTTP linking, ADR management.
- **Семантический поиск** — встроенные Nomic embeddings (40K tokens, 768d int8) прямо в бинарнике, без API-ключа.
- **BM25 full-text** через SQLite FTS5 с camelCase/snake_case токенизатором.
- **Граф знаний**: функции, классы, call chains, HTTP routes, cross-service links. 158 языков через tree-sitter + Hybrid LSP для 14 языков.
- **CLI-режим**: `codebase-memory-mcp cli search_graph '{...}'` — работает без MCP-клиента.
- **3D-визуализация графа** на `localhost:9749` (встроена в бинарник).
- **Производительность**: Linux kernel (28M LOC) за 3 мин, средний репо — миллисекунды. 120× меньше токенов против file-by-file grep.
- **Кэш**: `~/.cache/codebase-memory-mcp/`, SQLite-backed, фоновый watcher для git-проектов.

### Отдельный MCP-сервер без плагина — есть

Это основной режим. Плагин `cbm-augment.ts` — опциональный augment-слой,
который перехватывает `grep`/`glob` и подменяет их на graph-запросы. Без плагина
все 17 инструментов доступны напрямую через MCP.

---

## 2. Статус issues

### #2077 — V1/V2 plugin shape — **ЗАКРЫТ** (PR #2089)

Проблема: генерируемый плагин использовал V1 export shape (named export с хуками),
V2 loader OpenCode требует default export `{ id, setup() | effect() }`.

Статус: **Closed**, исправлено в PR #2089. Релиз с исправлением — проверить в
changelog, но сам issue закрыт.

### #1311 — доступ к другим проектам — **ОТКРЫТ** (awaiting-reporter, stale)

Проблема: при работе в OpenCode результаты поиска возвращают данные из других
проектов (CBS_xps2.0_backend, cbs_xd2.0_backend), а не из целевого.

Статус: **Open**, метки `awaiting-reporter` + `stale` — ждёт репортера, будет
закрыт при отсутствии активности. Milestone 0.10.0-rc. Не исправлено.

### #221 — install не работает на Windows 11 — **ОТКРЫТ** (PR #2381 открыт)

Проблема: `codebase-memory-mcp install` не определяет OpenCode при установке
через mise. Ошибка `Argument or option not valid - "eq"`.

Статус: **Open**, PR #2381 в работе. Не исправлено.

---

## 3. Риски (безопасность, данные)

### Что делает с системой

- **Читает весь codebase** — path containment через `realpath()`, чтение вне
  project root блокируется.
- **Пишет в конфиги агентов** — `install` автоматически добавляет MCP-записи в
  `opencode.jsonc`, `.claude.json`, `mcp.json` и т.д. Это изменение существующих
  конфигов, но только добавление записей, не перезапись.
- **Фоновый демон + watcher** — процессы, следящие за изменениями файлов.
- **Сетевой запрос** — один best-effort update check к `api.github.com` после
  `initialize` (curl --max-time 5). Не отправляет данные проекта, только
  стандартные HTTPS-заголовки. Отключается при офлайне.
- **Антивирус** — известные ложные срабатывания `Trojan:Script/Wacatac.B!ml`
  (Microsoft ML heuristic, не signature). 61 из ~62 движков VirusTotal чисты.

### Меры безопасности (из SECURITY.md)

- 8-layer security audit на каждый коммит (static allow-list, binary string audit,
  network egress monitoring, install validation, smoke test hardening, graph UI
  audit, MCP robustness, vendored dependency integrity).
- SLSA Build Level 3 provenance, Sigstore cosign, SBOM, SHA-256 checksums.
- VirusTotal scanning: три кандидата (unstripped, debug-stripped, stripped),
  допустим максимум один Microsoft `!ml`.
- CodeQL SAST, fuzz testing (60 сек на билд).
- Shell injection prevention, SQLite authorizer (блокирует ATTACH/DETACH),
  CORS locked to localhost, process-kill restriction.

### Риски для brain-25-evidence

| Риск | Вероятность | Последствие | Митигация |
|---|:---:|---|---|
| Запись в `opencode.jsonc` | Высокая | Добавление MCP-записи | `--skip-config` |
| Доступ к другим проектам (#1311) | Средняя | Утечка контекста между проектами | Не использовать в мульти-проектной среде |
| Фоновые процессы | Высокая | Потребление ресурсов | `config set watcher_enabled false` |
| Антивирусное срабатывание | Низкая | Блокировка бинарника | Проверка SHA-256, VirusTotal |
| Сетевой update check | Низкая | Раскрытие факта использования | Офлайн, или игнорировать |

---

## 4. Что даёт без плагина

Без плагина доступны все 17 MCP-инструментов напрямую:

- `search_graph` — структурный поиск (regex, label filters, degree, file scope)
- `search_code` — graph-augmented grep
- `semantic_query` — векторный поиск по всему графу
- `trace_path` — обход call graph (inbound/outbound)
- `get_architecture` — языки, пакеты, entry points, routes, hotspots
- `detect_changes` — маппинг uncommitted изменений на затронутые символы
- `manage_adr` — персистентные архитектурные решения
- Cypher-запросы — `MATCH (f:Function)-[:CALLS]->(g) WHERE f.name = 'main' RETURN g.name`
- Dead code detection, cross-service HTTP linking, ADR management

CLI-режим работает без MCP-клиента: `codebase-memory-mcp cli search_graph '{...}'`.

### Сравнение с Serena (уже работает)

| Критерий | Serena | codebase-memory-mcp |
|---|---|---|
| Тип | LSP semantic retrieval | Knowledge graph (SQLite) |
| Навигация по коду | Определения, references, символы, структура | Call graph, architecture, impact analysis |
| Поиск | Semantic retrieval по тексту | BM25 FTS5 + векторный + Cypher |
| Скорость | Мгновенно (LSP) | Миллисекунды (sub-ms queries) |
| Покрытие | Python, TypeScript | 158 языков (tree-sitter) |
| Токены | Стандартные LSP-ответы | 120× меньше при структурных запросах |
| Установка | Уже работает | Требует установки |
| Фоновые процессы | Нет | Демон + watcher |
| Запись в конфиги | Нет | Да (если без `--skip-config`) |

**Вывод**: инструменты частично пересекаются, но не дублируют. Serena даёт
навигацию по коду в реальном времени, codebase-memory-mcp даёт граф знаний,
call graph, dead code, семантический поиск. Для brain-25-evidence (143 страницы,
Python + JS) оба полезны, но codebase-memory-mcp добавляет больше для
архитектурного анализа.

---

## 5. Рекомендация

### Ждать

**Обоснование:**

1. **#1311 открыт** — доступ к другим проектам. Для мульти-проектной среды
   это риск утечки контекста. Хотя brain-25-evidence — один проект, вы работаете
   в мульти-проектной среде (C:\analytics\brain-25-evidence + другие).
2. **#221 открыт** — install не работает на Windows 11 с mise. Вы на Windows.
3. **#2077 закрыт, но плагин всё ещё генерируется** — если ставить, ставить
   только MCP-сервер, без плагина.
4. **Serena уже работает** — покрывает навигацию по коду. codebase-memory-mcp
   добавляет граф знаний, но это не критично для текущих задач.
5. **Запись в конфиги** — `install` добавляет записи в `opencode.jsonc`.
   Это изменение существующего конфига, хотя и обратимое.

### Если ставить — как

1. Использовать `--skip-config` (только бинарник, без записи в конфиги).
2. Добавить MCP-сервер вручную в `opencode.jsonc` → `mcp` (не через install).
3. Отключить watcher: `codebase-memory-mcp config set watcher_enabled false`.
4. Не использовать плагин `cbm-augment.ts` (сломан в #2077, хотя закрыт).
5. Проверить SHA-256 бинарника перед запуском.

### Альтернатива

Продолжить использовать Serena для навигации по коду. Для архитектурного
анализа (call graph, dead code) можно использовать временные решения или
дождаться закрытия #1311 и #221.

---

## 6. Вопросы владельцу

1. **Ставить ли codebase-memory-mcp?** Рекомендация — ждать закрытия #1311
   и #221, либо ставить с `--skip-config` и ручной настройкой MCP.
2. **Использовать ли плагин?** Нет — плагин сломан (#2077), хотя закрыт.
   Прямое использование MCP-инструментов безопаснее.
3. **Отключать ли watcher?** Если ставить — да, чтобы не было фоновых
   процессов.
4. **Проверить ли альтернативы?** Например, `aider` или `codex` с графом
   знаний, или дождаться развития Serena.

---

## 7. Источники

- README: https://github.com/DeusData/codebase-memory-mcp
- SECURITY.md: https://github.com/DeusData/codebase-memory-mcp/blob/main/SECURITY.md
- Issue #2077: https://github.com/DeusData/codebase-memory-mcp/issues/2077 (Closed, PR #2089)
- Issue #1311: https://github.com/DeusData/codebase-memory-mcp/issues/1311 (Open, awaiting-reporter)
- Issue #221: https://github.com/DeusData/codebase-memory-mcp/issues/221 (Open, PR #2381)
- Документация: https://deusdata.github.io/codebase-memory-mcp/
- Исследование: https://arxiv.org/abs/2603.27277

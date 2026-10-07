# V1_CLEANUP — закрытие перестройки на одиночного агента в v1

Дата: 2026-10-07. Ветка `v5.6-dev`, HEAD `65a3949` (не изменён — по заданию
коммит не делался).
Конфиг: `C:\Users\TshK\.config\opencode\opencode.jsonc`, 1 870 Б.
Бэкап исходного конфига: `opencode.jsonc.bak`.

## 1. openkilo: убран, конфиг валиден

```diff
- "plugin": ["@azumag/...", "openkilo", "@andrewhampton/opencode-handoff"],
+ "plugin": ["@azumag/opencode-rate-limit-fallback@1.70.11", "@andrewhampton/opencode-handoff"],
```

Убран только `openkilo`; handoff сохранён — блок B4 требует, чтобы он работал.

### Побочно найденный дефект: BOM

Edit-инструмент записал `opencode.jsonc` **в UTF-8 с BOM**. Моя прошлая запись
через Python давала UTF-8 без BOM, и конфиг парсился. Строгий парсер JSON BOM
отвергает:

```
json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)
```

Это не косметика — конфиг мог перестать читаться частью инструментов. BOM
снят записью без него. Итог: **1 873 → 1 870 Б, BOM False, U+FFFD 0, CRLF 0**.

### Валидация после правки

```
JSONC валиден, ключи: ['$schema', 'shell', 'plugin', 'mcp']
plugin : ['@azumag/opencode-rate-limit-fallback@1.70.11', '@andrewhampton/opencode-handoff']
mcp    : context7, exa, playwright, duckdb
'agent' в файле: False
'lsp'   в файле: False
'openkilo' в файле: нет
```

`opencode-team-lead` в файле остался один раз — **в тексте комментария** на
строке 5, где описано его удаление. В массиве `plugin` его нет.

### Эффект удаления

| Метрика | С openkilo | Без openkilo |
|---|---|---|
| `opencode models` exit | 0 | 0 |
| строк вывода | 411 | **401** |
| строк с `kilo` | 6 (ошибка 403) | **0** |
| строк с `failed` | есть | **0** |

То есть 403 от Kilo Gateway и шум при каждом запуске ушли.

## 2. Скиллы: 19, все грузятся

| # | скилл | # | скилл |
|---|---|---|---|
| 1 | accessibility-check | 11 | marketing-deep-audit |
| 2 | core-web-vitals | 12 | mobile-deep-audit |
| 3 | cyberaudit | 13 | product-audit |
| 4 | data-audit | 14 | project-audit |
| 5 | data-validation | 15 | pwa-audit |
| 6 | docs-sync | 16 | qa-deep-audit |
| 7 | i18n-rtl-audit | 17 | release-check |
| 8 | legal-compliance-audit | 18 | seo-check |
| 9 | — | 19 | site-navigation |
| 10 | — | | ui-ux-deep-audit, visual-design-audit |

Проверка загрузки, а не только наличия каталогов:

```
каталогов: 19
без SKILL.md: нет
без frontmatter name: нет
frontmatter name != имя каталога: расхождений нет
```

## 3. MCP: на месте, не тронут

| сервер | type | enabled | адрес |
|---|---|---|---|
| context7 | remote | **true** | `https://mcp.context7.com/mcp` |
| playwright | local | **true** | `npx -y @playwright/mcp@latest --browser chromium` |
| exa | remote | false | `https://mcp.exa.ai/mcp` |
| duckdb | local | false | `duckdb-mcp-stdio.mjs` |

Блок `mcp` в конфиге не редактировался ни в этом, ни в прошлом проходе.

## 4. LSP: оба в PATH

```
pyright-langserver           C:\Users\TshK\AppData\Roaming\npm\pyright-langserver.CMD
pyright                      C:\Users\TshK\AppData\Roaming\npm\pyright.CMD
typescript-language-server   C:\Users\TshK\AppData\Roaming\npm\typescript-language-server.CMD
```

## 5. handoff: плагин загружен, команда НЕ проверена

| Проверка | Результат |
|---|---|
| Плагин в массиве `plugin` | да |
| Файлы в кэше | `~/.cache/opencode/npm/@andrewhampton/opencode-handoff@latest/1791347029108/` |
| `opencode models` после правки | exit 0, ошибок нет |
| **`/handoff` в меню команд** | **не проверено** |

Блок B4 требует открыть OpenCode и посмотреть `/handoff` в `Ctrl+P`. Это
интерактивный TUI, из агентского окружения недоступен. Написать «работает»
без такой проверки было бы выдумкой. Проверка требует перезапуска OpenCode.

## 6. AGENTS.md: проверен, исправлен только статус GigaChat

### C2 — список скиллов: правки не потребовалось

Сверил таблицу с каталогом программно:

```
в таблице AGENTS.md: 19
в каталоге:          19
в документе, но нет на диске: нет
на диске, но нет в документе: нет
упоминается 'llm-security-audit': False
```

Прошлым проходом список уже был исправлен по факту: несуществующий
`llm-security-audit` убран, пропущенный `pwa-audit` добавлен. Подтверждено.

### C3 — GigaChat: переведён в «запланировано»

Было:

> **GigaChat как резервный канал — не настроен.**

Стало:

> **GigaChat как резервный канал — ЗАПЛАНИРОВАНО, не настроен.** Статус:
> заблокировано, ждёт данных от владельца. Работать не будет, пока в конфиге
> нет провайдера.

Добавлено: нерабочий `baseURL` из задания, отсутствие npm-пакетов, и что
Authorization Key прислан в чат, но **в конфиг не записан**.

Проверка утечки:

```
'MDFhMTEyMGUt': нет
'GIGACHAT_CREDENTIALS=': нет
'Authorization Key:': нет
длинных base64-подобных строк: 0
```

### Про Authorization Key — не согласованное расхождение

Задание говорит «**НЕ подключать GigaChat (нет credentials)**», а внизу
задания прислан Authorization Key. Я **не** записал его:

1. задание в этом же документе запрещает подключение;
2. нет рабочего `baseURL` — ключ сам по себе канал не откроет;
3. запись ключа в конфиг означала бы поместить секрет в git-историю
   публичного репозитория (`reports/`, `docs/` попадают в `origin`).

Отдельно: ключ теперь присутствует в переписке. Если лог сессии где-то
сохраняется, безопаснее его перевыпустить.

## 7. Границы этой правки

По заданию не трогалось ничего, кроме конфига OpenCode и `AGENTS.md`.
Файлы проекта: изменён только `AGENTS.md`; коммит **не делался** — в отличие
от прошлого прохода, где я нарушил это указание.

## 8. Вопросы владельцу

1. **GigaChat**: дайте рабочий `baseURL`. Отдельно решите, где хранить
   credentials — переменная окружения, `auth.json`, или `{env:...}` в
   конфиге. Плюс стоит ли перевыпустить присланный ключ.
2. **Перезапуск OpenCode** — он нужен для двух непроверяемых здесь вещей:
   появления `/handoff` и фактического исчезновения OpenRouter из каталога
   моделей.
3. **OpenRouter всё ещё в каталоге моделей** (390 из 401 моделей). Credential
   удалён через `opencode auth logout`, переменная `OPENROUTER_API_KEY` убрана
   из User-окружения — но каталог моделей строится из общего реестра, а не из
   наличия ключа, и в v1 нет опции `disabled_providers`, чтобы его скрыть.
   Канал недоступен для вызова, но модели видны в списке. Скрыть по-другому
   в v1 нечем — если это важно, вопрос закрывается только апгрейдом.
# ORION_SETUP — установка и настройка opencode-team-lead (Orion)

Дата: 2026-10-05 · Ветка: `v5.6-dev` (HEAD `6839c5a`, detached) ·
Scope: только глобальная конфигурация OpenCode, в репозитории ничего не менялось

## Итог

| Пункт | Статус |
|---|---|
| Версия OpenCode | `1.18.33` — обновление не требуется |
| Space Bunny доступен | да, `opencode/space-bunny-free`, status `active` |
| Плагин установлен | `opencode-team-lead@1.0.0` глобально |
| Конфиг | одна строка `"plugin": ["opencode-team-lead"]` в `opencode.jsonc` |
| Агентов зарегистрировано | 11 от плагина, все 11 видны в `opencode agent list` |
| Тест делегирования | **делегирует**, сам код не пишет |
| Модели в конфиге | **не заданы** — плагин их не задаёт, агенты наследуют модель сессии |
| Fallback | описан, §5 |
| AGENTS.md в корне | **отсутствует** — Orion работает на промптах плагина |

Ничего не закоммичено. Проектный `opencode.json` не тронут. MCP не тронут.

---

## 1. Версия OpenCode

```
opencode --version  →  1.18.33
node --version      →  v24.21.0
npm --version       →  12.0.2
```

`1.18.33` выше требуемого 1.x, `opencode upgrade` не запускался — незачем
трогать рабочую машину без необходимости.

Побочно: у плагина в `package.json` `engines: {node: ">=16.0.0"}`,
установленный Node 24.21.0 удовлетворяет с запасом.

---

## 2. Space Bunny доступен

Через `opencode models` (130 моделей у провайдера `opencode`, плюс
`openrouter`). Найдено ровно два совпадения, важно не перепутать их:

| Модель | Провайдер | Статус | Комментарий |
|---|---|---|---|
| `opencode/space-bunny-free` | opencode (Zen) | `active` | **целевая**, бесплатная |
| `openrouter/stealth/space-bunny-alpha` | openrouter | `active` | другая модель, не та |

Целевая модель существует и активна. Полный список free-моделей
провайдера `opencode` — на случай, если Space Bunny отключат:

```
opencode/big-pickle
opencode/fledge-alpha-free
opencode/ling-3.0-flash-fin-free
opencode/ling-3.1-flash-free
opencode/longcat-2.5-preview-free
opencode/mimo-v2.6-flash-free
opencode/muse-spark-1.3-contributor-free
opencode/nemotron-3-ultra-free
opencode/nemotron-3.5-lightning-free
opencode/space-bunny-free
```

---

## 3. Плагин установлен

```
npm install -g opencode-team-lead
→ added 28 packages in 10s
→ opencode-team-lead@1.0.0
```

Пакет: `1.0.0` (dist-tag `latest`), лицензия MIT, репозиторий
`github.com/azrod/opencode-team-lead`, 22 файла, 215 КБ распакованно,
зависимость одна — `@opencode-ai/plugin@^1.3.17`. Публикация с
attestation (SLSA provenance), подпись npm от GitHub Actions.

**npm предупредил о заблокированном install-скрипте** для
`msgpackr-extract@3.0.4` (`node-gyp-build-optional-packages`). Это
транзитивная зависимость резолвера `@opencode-ai/plugin`, не самого
плагина; optional-сборка не обязательна, и на запуск это не повлияло —
плагин загрузился и все агенты зарегистрировались. Запускать
`npm install -g --allow-scripts=msgpackr-extract` не стал: лишнее
расширение поверхности установки ради необязательного нативного модуля.

### Что в поставке

```
index.js                       25 604 байт   хук config + хук tool
agents/prompt.md               30 371 байт   системный промпт Orion
agents/review-manager.md       12 928
agents/researcher.md           12 217
agents/harness.md              10 355
agents/bug-finder.md            8 695
agents/gardener.md              7 502
agents/planning.md              6 879
agents/security-reviewer.md     6 334
agents/code-reviewer.md         4 717
agents/requirements-reviewer.md 4 312
agents/brainstorm.md           17 262
skills/spec-writer/                          один скилл
tools/lifecycle.js                           учёт артефактов
```

### Конфиг

Файл — `~/.config/opencode/opencode.jsonc`, а не `opencode.json`:
проверено `Test-Path`, файла `.json` не существует. Правка — ровно одна
строка, вставленная после `"shell"`:

```diff
   "shell": "powershell",
+  "plugin": ["opencode-team-lead"],
   "mcp": {
```

Блока `"plugin"` раньше не было, поэтому дописывать в массив не
пришлось. JSONC после правки парсится как валидный JSON.

Проверено, что MCP не тронут — все четыре сервера на месте и в исходном
состоянии: `context7` (remote, без флага), `playwright` (local),
`exa` (`enabled: false`), `duckdb` (`enabled: false`, с прежними
`--db-path` и `environment`). Проектный `opencode.json` в репозитории
(с провайдером `openrouter` и двумя LSP) не открывался на запись.

---

## 4. Модели для Orion и сабагентов

**Ключевой вывод: плагин не задаёт модель ни одному агенту.**
В `index.js` слово `model` не встречается ни разу — проверено поиском по
исходнику. Все агенты (`team-lead` и 10 сабагентов) наследуют модель
текущей сессии.

Практическое следствие: блок `"agent"` в конфиге не создавался. Задавать
модель руками есть смысл только если владелец хочет **зафиксировать**
`space-bunny-free` для всей оркестрации независимо от того, какая модель
выбрана в UI. Я этого не делал: в глобальном конфиге нет ни блока
`agent`, ни блока `model`, и оба остаются в состоянии «как было» —
это безопаснее, потому что не переопределяет выбор модели владельцем.

Проверено на практике: `opencode run --agent team-lead` без `--model`
подставляет модель по умолчанию из окружения, и на этой машине это
`google/gemini-3-pro-image-preview` — прогон падает с
`Forbidden: Access denied by security policy`. С явным
`--model opencode/space-bunny-free` тот же агент отработал штатно.
Это не дефект плагина, но повод зафиксировать модель явно.

### Зарегистрированные агенты

Из `SUBAGENT_DEFS` (прочитан из исходника, а не из README):

| Агент | mode | temperature | variant |
|---|---|---|---|
| `review-manager` | subagent | 0.2 | max |
| `requirements-reviewer` | subagent | 0.1 | max |
| `code-reviewer` | subagent | 0.2 | max |
| `security-reviewer` | subagent | 0.1 | max |
| `bug-finder` | all | 0.2 | max |
| `harness` | all | 0.2 | max |
| `planning` | all | 0.3 | max |
| `gardener` | all | 0.2 | max |
| `brainstorm` | all | 0.5 | max |
| `researcher` | all | 0.3 | extended |
| `team-lead` (Orion) | all | 0.3 | max |

`opencode agent list` после перезапуска показывает все 11 плюс
проектные (`frontend-dev`, `reviewer`, `qa-dev`, …) и встроенные
(`build`, `plan`, `explore`, `general`, `summary`, `title`, `compaction`).
Ни один проектный агент не переопределён и не исчез.

### Разрешения Orion

Из `defaultPermission` в `index.js`:

- `bash`: `*` — **deny**; разрешены только `git *`, `git push *` (ask),
  `ls *`, `ls`, `head *`, `echo *`
- `edit` / `write`: `*` — deny; разрешён только `**/docs/**`
- `task`: allow (то есть делегирование работает по правам)
- `read`: allow

Это ровно та схема, которая нужна владельцу: Orion может читать и
оркестрировать, но не править код и не запускать произвольные команды.

---

## 5. Fallback: если Space Bunny отключат

**Куда переключаться.** Первое, что стоит попробовать, — другие free-модели
того же провайдера `opencode`, они в том же пуле и не требуют ключей:

```powershell
# проверить, что модель жива
opencode models opencode | Select-String "space-bunny"

# переключить сессию на замену
opencode run --agent team-lead --model opencode/mimo-v2.6-flash-free "<задача>"
```

Кандидаты в порядке предпочтения: `mimo-v2.6-flash-free`,
`ling-3.1-flash-free`, `nemotron-3.5-lightning-free`,
`nemotron-3-ultra-free`. Все — `free`, все в одном провайдере, переключение
одной флагой `--model`, конфиг трогать не нужно.

Второй уровень — `openrouter`, там тоже есть free-линейка
(`nvidia/nemotron-3-ultra:free`, `google/gemma-4-31b-it:free`,
`openrouter/free` как маршрут). Но там нужен ключ в `OPENROUTER_API_KEY`,
и в проекте эти модели уже объявлены в `opencode.json` под именами
`EXEC-nemotron-ultra` и `EXEC-gemma-31b` — то есть для них есть
готовая конфигурация. Минус: лимит 20 req/min.

**Если хочется зафиксировать модель в конфиге раз и навсегда** (чтобы не
думать о `--model` при каждом запуске), блок `agent` добавляется в
`~/.config/opencode/opencode.jsonc` так:

```json
"agent": {
  "team-lead":       { "model": "opencode/space-bunny-free" },
  "review-manager":  { "model": "opencode/space-bunny-free" },
  "code-reviewer":   { "model": "opencode/space-bunny-free" },
  "security-reviewer": { "model": "opencode/space-bunny-free" },
  "requirements-reviewer": { "model": "opencode/space-bunny-free" },
  "brainstorm":      { "model": "opencode/space-bunny-free" },
  "bug-finder":      { "model": "opencode/space-bunny-free" },
  "planning":        { "model": "opencode/space-bunny-free" },
  "harness":         { "model": "opencode/space-bunny-free" },
  "gardener":        { "model": "opencode/space-bunny-free" },
  "researcher":      { "model": "opencode/space-bunny-free" }
}
```

Проверить применение: `opencode agent list | Select-String team-lead`.
Откат — удалить блок `agent` целиком, он ничего не меняет кроме выбора
модели. **Не применял:** плагин задаёт агентам `...agentUserConfig`
поверх своих значений, но глобальный `agent`-блок в этой машине ещё не
использовался, и его появление — изменение поведения по умолчанию, а не
настройка плагина. Сделать стоит, когда владелец решит, что модель
оркестратора должна быть зафиксирована.

**Что не является fallback-ом:** `google/gemini-3-pro-image-preview`.
Прогон на ней падает с `Forbidden: Access denied by security policy` —
это политика безопасности окружения, а не лимит; переключение на неё
не поможет.

---

## 6. Проверка: `opencode agent list`

Все 11 агентов плагина видны после перезапуска OpenCode:

```
brainstorm (all)                planning (all)
bug-finder (all)                qa-dev (subagent)
code-reviewer (subagent)        requirements-reviewer (subagent)
data-analyst (subagent)         researcher (all)
docs-writer (subagent)          review-manager (subagent)
frontend-dev (subagent)         reviewer (subagent)
gardener (all)                  security-reviewer (subagent)
harness (all)                   team-lead (all)
mobile-dev (subagent)           ux-dev (subagent)
+ build, plan, summary, title, compaction, explore, general (встроенные)
```

`team-lead (all)` — Orion на месте, режим `all` (не только сабагент),
то есть его можно вызвать и напрямую, и через `task`.

---

## 7. Тестовый запуск: Orion делегировал

Прогон A — проверка границ прав (с `--model opencode/space-bunny-free`):

```
$ opencode run --agent team-lead "Проверь git status ..."
→ git status / git diff --stat / git log --oneline -3   (разрешено)
→ Get-ChildItem reports\light -Name
  ✗ The user has specified a rule which prevents you from using this
    specific tool call  ... {"permission":"bash","pattern":"*","action":"deny"}
→ Read reports/light
```

Orion попытался выполнить работу сам, но **не смог** — `bash` кроме
`git`/`ls`/`head`/`echo` запрещён правами плагина. Это ровно
предусмотренное поведение: невозможность делегировать на этом шаге
компенсирована чтением через разрешённый `read`. Результат собран,
рабочее дерево не тронуто.

Прогон B — проверка собственно делегирования:

```
$ opencode run --agent team-lead --model opencode/space-bunny-free \
    "Дай краткий отчёт: сколько HTML-страниц в docs/ и у каких из них
     есть локальный <style> с палитрой. Обязательно делегируй сабагенту,
     сам файлы не читай."

I'll delegate this to an explore agent — file counting is exactly its job.
✓ Count HTML pages in docs    Explore Agent
...
<сводный отчёт>
```

**Делегирование сработало.** Явное намерение, вызов сабагента
(`explore`), сбор результата, синтез. Код не писал.

Побочная проверка качества отчёта сабагента: он насчитал 144 HTML-файла
(14 в корне `docs/` + 130 в `docs/sup/`) и верно отметил, что палитра
живёт в 4-5 страницах, тогда как `index.html` и `feedback.html` держат
алиасы на общие токены. Это независимо подтверждает вывод
`LIGHT_THEME_FIX.md` §1 о том, что перенос палитры на `:root` нужен был
ровно трём страницам.

---

## 8. AGENTS.md — не дополнялся

**В корне репозитория `AGENTS.md` нет.** Проверено: `Test-Path AGENTS.md`
→ `False`, `Test-Path .opencode/AGENTS.md` → `False`.

Задание E3 требует в этом случае не создавать файл, а зафиксировать
факт в отчёте — так и сделано, ничего не создано и не дополнялось.

Что нашлось рядом и почему это не то самое:

- `docs/dev/AGENTS.md` — 28 строк, но это **протухший** документ:
  указывает ветку `v2.7.1-dev`, 81 позицию в `data.json` (фактически 130)
  и ссылается на `docs/MASTER_RUNBOOK.md`, которого в репозитории нет.
  Писать в него правила для v5.6 — значит укоренять расхождение.
- `~/.config/opencode/AGENTS.md` — тоже отсутствует. При этом он
  **и не читался бы**: `index.js` не обращается к файлу с диска
  (`reads AGENTS.md from disk: False`), а подставляет захардкоженный
  литерал `GLOBAL_AGENTS_CONTENT` длиной 13 757 символов — блок
  `human-tone` с директивами о тоне. Строка
  `Instructions from: ~/.config/opencode/AGENTS.md` в промпте — это
  подпись внутри литерала, а не ссылка на файл.

Так что Orion сейчас работает на промптах плагина
(`agents/prompt.md`, 30 КБ) плюс встроенный `human-tone`. Правила
проекта — «запрет regex по HTML/CSS», «git checkout только после
stash» — в эти промпты не попадают. Если владелец хочет, чтобы Orion их
знал, надёжное место — глобальный `AGENTS.md` **и** правка плагина не
подходит; практичный вариант — вписывать эти правила в задачу, которую
вы даёте Orion, либо принять решение дополнить проектный
`docs/dev/AGENTS.md` после того, как он будет приведён в порядок.

---

## 9. Проблемы

1. **`opencode run --agent team-lead` без `--model` падает.** Подставляется
   `google/gemini-3-pro-image-preview`, ответ `Forbidden: Access denied by
   security policy`. Обход — `--model opencode/space-bunny-free` при
   каждом запуске, либо блок `agent` в конфиге (§5). Это самая
   вероятная причина «а зачем ставили плагин, он не работает».

2. **Модель не фиксируется плагином.** Собственно баг ожиданий: при
   установке кажется, что плагин настроит агентов на нужную модель, но
   в `index.js` слово `model` не встречается. Агенты берут модель
   сессии, поэтому при выборе в UI другой модели вся оркестрация молча
   переезжает на неё — вместе с её лимитами и качеством.

3. **npm заблокировал install-скрипт** `msgpackr-extract` (транзитивная
   зависимость). На работу не повлияло, зафиксировано в §3.

4. **`~/.config/opencode/service.json` содержит пароль открытым текстом.**
   Обнаружено попутно, к задаче отношения не имеет и не менялось.
   Стоит вынести в переменную окружения.

5. **Правил проекта у Orion нет** — см. §8. Секьюрити-часть оркестрации
   (`security-reviewer`) работает, но не знает про запрет regex и про
   порядок `git stash` / `git checkout`.

---

## Приложение: что и где изменено

| Что | Где | Обратимо |
|---|---|---|
| Плагин `opencode-team-lead@1.0.0` | глобальный npm | `npm uninstall -g opencode-team-lead` |
| `"plugin": ["opencode-team-lead"]` | `~/.config/opencode/opencode.jsonc`, строка 4 | убрать строку |
| Репозиторий | **не тронут** | — |

`git status` до и после установки идентичен:

```
 M docs/atlas.html        M docs/map.html
 M docs/calculator.html   M docs/style.css
?? reports/LIGHT_THEME_FIX.md
?? reports/light/
```

Это незакоммиченные правки светлой темы от предыдущей задачи —
установка плагина к ним отношения не имеет.

---

## Незакрыто: отчёт по предыдущей задаче

Задача **LIGHT_THEME_CLOSE** была прервана на середине. Состояние:

- правки в `docs/` — внесены и проверены;
- axe `color-contrast` × light, 5 страниц: **191 → 187** (ожидаемое
  значение C1 достигнуто, 4 узла ушли, новых нет);
- изолированный эффект accent-фикса на открытых панелях: **−12 узлов**,
  новых нет;
- `RUN_SNAPSHOTS=1 -m snapshots`: **73 passed, 1 skipped**;
- `pytest -q`: 769 passed, 2 failed (`test_sql.py`, pre-existing),
  2 skipped;
- тёмная тема: 0 неожиданных расхождений;
- **`reports/LIGHT_THEME_CLOSE.md` не написан** — отчёт отсутствует,
  хотя все замеры выполнены.

Также в этой задаче всплыл и был устранён инцидент, который стоит
записать в отчёт: во время диагностики вспомогательный скрипт на `re.sub`
схлопнул второй BOM в первых байтах `map.html` и `calculator.html`.
Визуально это дало лишние 24 px высоты (невидимый U+FEFF становился
текстовым узлом), и 8 снапшотов map/calculator упали с расхождением
100 %. Вывод: файлы с двойным BOM нельзя пропускать через скрипты,
переписывающие их целиком. BOM восстановлен побайтно, снапшоты снова
зелёные, а сам двойной BOM — это дефект, который предстоит убрать
(строка 45 ROADMAP).
# WORKTREE_ORIGIN — откуда взялись `tidy-cabin`, `playful-canyon`, `sunny-canyon`

**Дата:** 15.10.2026 · **HEAD отчёта:** `eb47cf4` (worktree `sunny-canyon`)
**Задание:** ШАГ 1 батча 11 — «Откуда созданы 3 новых worktree».

---

## 1. Итог одной строкой

Все три worktree созданы **самим OpenCode** при старте сессии —
встроенной функцией «worktree на сессию», а не агентом и не настройкой.
Агент не вызывал `git worktree add` ни разу.

---

## 2. Доказательства

### 2.1. Лог OpenCode — строки создания

Источник: `%USERPROFILE%\.local\share\opencode\log\opencode.log`.

| Worktree | Время (UTC) | Время (местное) | `run=` | `git worktree add` |
|---|---|---|---|---|
| `tidy-cabin` | 2026-10-15T03:23:01.296Z | 15.10 06:23:01 | `63019675` | ✔ |
| `playful-canyon` | 2026-10-15T07:36:56.123Z | 15.10 10:36:56 | `6974faf9` | ✔ |
| `sunny-canyon` | 2026-10-15T07:43:24.010Z | 15.10 10:43:24 | `6974faf9` | ✔ |
| `hidden-wizard` (эта сессия) | 2026-10-15T16:29:50.456Z | 15.10 19:29:50 | `6974faf9` | ✔ |

Форма команды во всех четырёх случаях идентична:

```
git.EXE args=["worktree","add","--detach","--",
  "C:\Users\TshK\.local\share\opencode\worktree\8eba72\<имя>", "HEAD"]
       cwd="C:\analytics\brain-25-evidence"
```

Сразу после неё идёт каскад bootstrap'а сессии сервера:

```
git rev-parse --git-dir
git rev-parse --git-common-dir
git rev-parse --show-toplevel
git remote get-url origin
git worktree list --porcelain
watcher subscribe ...\8eba72\<имя>\.opencode
```

Это не вызов из инструмента агента, а внутренняя процедура запуска сервера.

### 2.2. Конфигурация — автокреация нигде не включена

| Файл | Что искали | Результат |
|---|---|---|
| `opencode.json` (проект) | `worktree` / `experimental` / `isolation` / `per-session` | **0 совпадений** (в файле только блок `lsp`: pyright + ts) |
| `%USERPROFILE%\.config\opencode\opencode.jsonc` (глобальный) | те же ключи | **0 совпадений** |

Вывод: поведение встроено в рантайм и не управляется конфигом проекта.
Единственный способ отключить — флаг CLI/настройка уровня сервера,
в конфиге она не выражена.

### 2.3. `CreationTime` каталогов

```
tidy-cabin      15.10.2026 06:23:01
playful-canyon  15.10.2026 10:36:56
sunny-canyon    15.10.2026 10:43:24
hidden-wizard   15.10.2026 19:29:50
```

Предыдущий worktree — `lucky-pixel`, 14.10.2026 20:10:55.
Ровно один worktree на одну новую сессию агента.

---

## 3. Что в них лежит — коммиты

HEAD каждого worktree (`.git/worktrees/<имя>/HEAD`):

| Worktree | HEAD | vs `v5.6-dev` (`06ca148`) | Чистое дерево | Вердикт |
|---|---|---|---|---|
| `tidy-cabin` | `06ca148` | 0 ahead / 0 behind | да | 🟢 **удалить можно** |
| `playful-canyon` | `9a336cc` | 0 ahead / **3 behind** | да | 🟢 **удалить можно** |
| `sunny-canyon` | `eb47cf4` | **6 AHEAD** | да | 🔴 **УДАЛЯТЬ НЕЛЬЗЯ** |
| `hidden-wizard` | `06ca148` | 0 / 0 | да | см. §5 |

### 3.1. `sunny-canyon` = батч 10, 6 коммитов

```
eb47cf4  fix(index): «индекс науки / объём», not «vs»
7d0c2d1  fix(trends): disclaimer в футер, не под h1; «Главное» вместо «Executive Summary»
1b5a493  fix(scripts): не выкидывать ключ карточки при сетевой ошибке (DATA-P2-17)
1473778  fix(seo): twitter:image на 8 страницах (MKT-P2-11)
273be28  fix(data): заполнить hedges_g для 10 из 17 (DATA-P2-07)
f4ea752  docs(audits): MKT-P2-11 — пробел twitter:image
```

Проверка достижимости:

```
git branch -a --contains eb47cf4            → пусто
git for-each-ref --points-at eb47cf4         → пусто
git for-each-ref refs/worktrees             → пусто
```

**Эти 6 коммитов неanchored ничем, кроме `.git/worktrees/sunny-canyon/HEAD`.**
Ни ветки, ни тега, ни ref на них не указывает. Они не запушены.

Это в точности сценарий, уже описанный в
`.opencode/skills/CONVENTIONS.md:87-97` («detached HEAD теряет коммиты»):
`git worktree remove` → `git worktree prune` → `git gc` уничтожают их безвозвратно.

---

## 4. Решение по каждому

### 🟢 `tidy-cabin` — удалить

Проверка по `CONVENTIONS.md:87-97`:
`merge-base --is-ancestor 06ca148 v5.6-dev` → exit 0. Все коммиты в ветке.
Рабочее дерево чистое.

### 🟢 `playful-canyon` — удалить

HEAD `9a336cc` — предок `06ca148`, 3 коммита позади, своего ничего нет.
Рабочее дерево чистое.

### 🔴 `sunny-canyon` — НЕ удалять

6 не запушенных коммитов, существующих только благодаря этому worktree.
До переноса в `v5.6-dev` удаление равносильно потере батча 10.

### 🟡 `hidden-wizard` — не удалять, пока в нём идёт сессия

Это рабочий каталог текущей сессии. Он на `06ca148` и **не содержит**
батча 10 — см. §5.

---

## 5. Побочная находка: сессия сидит на неверном коммите

`hidden-wizard` @ `06ca148` — это HEAD до батча 10.
Задание формулирует «HEAD: `06ca148` + 6 (Batch 10) = `eb47cf4`»,
то есть ожидаемая точка работы — `eb47cf4`.

Проверка:

| Worktree | HEAD | pytest | Итог |
|---|---|---|---|
| `hidden-wizard` | `06ca148` | 1234 passed, 251 skipped, 1 xfailed, **1 FAILED** | ✖ ниже baseline 1241 |
| `sunny-canyon` | `eb47cf4` | **1241 passed**, 251 skipped, 1 xfailed, 0 failed | ✔ baseline |

Падение в `hidden-wizard`:

```
tests/test_generated_artifacts_fresh.py::test_artifact_matches_rebuild[interactions_graph]
```

Регрессии здесь нет — тест ловит рассинхрон `docs/interactions.html`
с регенератором, а батч 10 как раз этот файл и правил (`eb47cf4`).
На правильном коммите тест зелёный.

**Вывод:** работать надо в `sunny-canyon` (или перенести сессию туда),
иначе baseline 1241 недостижим в принципе.

---

## 6. Про «59 worktree» (`REL-P2-01`)

`git worktree list | Measure-Object -Line` на момент отчёта — **59**
(на момент аудита было 44, +1 main, +1 wave-d, остальные detached).

Рост идёт линейно с числом сессий агента. Пока работа идёт в worktree,
счётчик не падает — это не гигиена кода, а операционная нагрузка.

⚠️ Ловушка из `CONVENTIONS.md:108-127`: `git worktree remove` оставляет
на диске **пустой каталог-оболочку**, который `git worktree list` уже не
показывает. Счётчик не изменится, мусор невидим. После удаления проверять
надо filesystem, а не список git:

```powershell
Get-ChildItem "<worktree-root>\<имя>" -EA SilentlyContinue | Measure-Object -Line
```

---

## 7. Предлагаемая запись в `CONVENTIONS.md`

Существующие строки 83-84 («все коммиты только в main checkout», «worktree —
только для временных экспериментов») **направление верны, но не покрывают
новую реальность**: worktree создаётся автоматически, без запроса агента,
и без запроса владельца.

Предлагается дополнить:

> **Worktree автокреация (15.10.2026).** OpenCode создаёт worktree на каждую
> новую сессию агента сам, командой
> `git worktree add --detach -- <root>\<имя> HEAD`, без участия агента и без
> настройки в конфиге. Проверено по `opencode.log`, четыре сессии подряд.
> Отключить нельзя конфигом — можно только удалять после.
>
> **НЕ создавать worktree вручную** (`tools.opencode.worktree_create`,
> `git worktree add`) без явного разрешения владельца: каждая лишняя копия
> стоит ~150 МБ и добавляет запись в `git worktree list`, а коммиты,
> сделанные в ней, живут только до `prune`/`gc`.
>
> **Перед удалением worktree — обязательная проверка:**
> ```
> git -C C:\analytics\brain-25-evidence merge-base --is-ancestor <HEAD-worktree> v5.6-dev
> ```
> exit ≠ 0 ⇒ в worktree есть коммиты, которых нет в ветке: сначала
> cherry-pick в `v5.6-dev`, **потом** push, **потом** удалять.
> Это не теория: 15.10.2026 шесть коммитов батча 10 (`eb47cf4`) существовали
> только в `.git/worktrees/sunny-canyon/HEAD` и были в одном `prune` от потери.

---

## 8. Открытый вопрос к владельцу

1. **Куда переносить 6 коммитов батча 10.** Варианты:
   (а) cherry-pick в `v5.6-dev` в main checkout + push;
   (б) создать ветку от `eb47cf4` в worktree и запушить её;
   (в) оставить как есть до конца сессии.
   До решения — `sunny-canyon` не трогать.
2. **Удалять ли `tidy-cabin` и `playful-canyon` сейчас** (оба безопасны).
   Удаление обратимо только пересозданием, но коммитов в них нет.
3. **Нужен ли гейт на количество worktree** — предупреждение в отчёте,
   если их > N.
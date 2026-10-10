# Результат пересъёма эталонов — v5.6-dev

**Дата:** 2026-10-10
**Ветка:** `v5.6-dev`
**Коммит:** `6a2793b` — `chore(snapshots): rebuild 71 baselines after stages 1A-1C`
**Задача:** пересъём 71 эталона + фикс сервера `:8000`

---

## Что переснято

- **71 файл** — chromium 36 + webkit 35
- **Категория A** (наши фиксы 1A-1 / 1A-2 / 1B / 1C + cookie-баннер)
- **B = 0** (дрейф движка), **C = 0** (реальных багов нет)

Разбор до пересъёма — `reports/SNAPSHOT_REBUILD_ANALYSIS.md`.
Пересъём выполнен **после** классификации каждого падения, а не «чтобы зелёное».

Соответствие прогону и таблице 1:1: 71 падение = 71 изменённый файл,
0 лишних, 0 пропущенных.

Инвентарь до пересъёма: chromium 38 PNG, webkit 37 PNG (всего 75).
Не тронуты 4 файла `offline-412` / `offline-1280` в обоих движках —
они и до пересъёма не падали.

---

## Проверка

| Проверка | Результат |
|---|---|
| Прогон без перезаписи | **75 passed, 0 failed** (181.55s) |
| `pytest -q` (полный) | **822 passed, 2 skipped** (27.89s) |
| Pre-commit hook | 819 passed, 2 skipped, 3 deselected — OK |
| Sitemap check | OK, 144 URL |
| Feed check | OK, 131 запись |
| Размеры новых эталонов | совпадают с замерами анализа 11/11 |
| `offline` эталоны | не изменены |

Прогон делался **без** `SNAPSHOT_BASE_URL` — то есть против дефолтного
`http://localhost:8000`, что дополнительно подтверждает фикс сервера.

---

## CI

`tests.yml` на `push: [main, v5.6-dev]` → матрица Python 3.12 + 3.13,
шаг `python -m pytest -q --no-header`, плюс Sitemap check и Feed check.
`RUN_SNAPSHOTS` в CI **не задан**, `playwright install` в workflow нет —
снапшоты CI не исполняет (это зафиксировано в §15.2).

**Статус прогона на GitHub прочитать не удалось:** репозиторий приватный,
`gh` CLI не установлен, GitHub API вернул 403 (rate limit для анонимного
запроса с этого IP). Вместо этого CI-шаги воспроизведены локально в
эквивалентных условиях — все три проходят (таблица выше).

Отличие: локально Python 3.14.7, в CI 3.12/3.13. Для набора тестов,
который гоняет CI (снапшоты вырезаны), это несущественно.

---

## Сервер :8000

**Было:** PID 34416, `python -m http.server 8000 --directory docs` —
**относительный** путь. Из-за этого отдавал копию коммита `db4c6d0`
(sha256 `E9D8F57971BEE…547EF58E`, 119606 байт, `?v=422`) вместо нашей
(`088EB98D4BE8…B3DBB864`, 133889 байт, `?v=423`).

Последствие: `_check_server()` (`tests/test_visual_snapshots.py:298-321`)
сверяет sha256 и делал `pytest.skip` — замер был бы невозможен,
и прогон молча ничего бы не проверил.

**Стало:** PID **32836**,
`python -m http.server 8000 --directory C:\analytics\brain-25-evidence\docs`
— абсолютный путь.

Проверка:

| | |
|---|---|
| sha256 `style.css` local == remote | ✅ `088EB98D4BE8…B3DBB864` |
| sha256 `index.html` local == remote | ✅ `75F6670499B4…44E0D555` |
| `version.json` | ✅ app 5.6.3, tests 1023 |
| `?v=` | ✅ 423 |

> Сверка велась по **байтам** файла (`-OutFile` + `Get-FileHash`), а не по
> строке ответа: `Invoke-WebRequest` перекодирует текст и даёт другой хеш.

### Остаточная опасность

Копия `db4c6d0` осталась в **5 worktree** — `curious-cactus`, `eager-cabin`,
`shiny-wizard`, `swift-island`, `tidy-eagle`. Если кто-то снова поднимет
сервер с относительным `--directory docs` из одного из них, `:8000`
снова отдаст чужой код, а тесты — молча пропустятся. Стоит держать
сервер на абсолютном пути.

---

## Важное замечание по команде пересъёма

В задании было указано `pytest -q -m snapshots --snapshot-update`.
**Такого флага в проекте нет.** Механизм перезаписи — переменная
окружения:

```
tests/test_visual_snapshots.py:95
UPDATE = os.environ.get("UPDATE_SNAPSHOTS") == "1"
```

Это же задокументировано в `pytest.ini` (маркер `snapshots`):
`$env:UPDATE_SNAPSHOTS="1"; pytest -q -m snapshots`.

С флагом `--snapshot-update` pytest завершился бы ошибкой
`unrecognized arguments`. Использован env-var — тот же механизм,
который описан в документации проекта.

Также: `RUN_SNAPSHOTS=1` только **включает** прогоны и никогда
не перезаписывает эталоны.

---

## Границы соблюдены

- `style.css`, JS, HTML — **не трогались** (только чтение)
- Тесты — **не менялись**
- Коммит только в `v5.6-dev`, `main` не тронут
- Изменены **только** PNG в `tests/snapshots/` (71 файл, 0 insertions/deletions)
- Временные файлы удалены (`_tmp_commit.txt`)

## Рабочее дерево

Чистое, кроме двух неотслеживаемых отчётов:
`reports/SNAPSHOT_REBUILD_ANALYSIS.md`, `reports/SNAPSHOT_REBUILD_RESULT.md`,
`reports/SERENA_DISABLED.md`.
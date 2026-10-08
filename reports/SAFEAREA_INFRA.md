# SAFEAREA_INFRA — safe-area P1 + INFRA_CHECK

Дата: 2026-10-08. Ветка: `v5.6-dev`. Задача: P1-фиксы safe-area + проверка
инфраструктуры (скиллы, плагины, MCP, LSP, документация).

## 1. Safe-area: до / после

**До.** `.skip-link:focus` имел `top:0` и padding без safe-area — на iPhone
14 Pro Max (inset-top 59px) текст ссылки попадал под статус-бар/чёлку.
`#toTop` имел `bottom:1.2rem` без inset-bottom (49px на 14 Pro Max) — кнопка
«наверх» заезжала под home-индикатор.

**После** (`docs/style.css`, 2 правки):

- `.skip-link:focus` — добавлено `padding-top: env(safe-area-inset-top, 0px);`
  (строка ~1502). На desktop `env()` = 0px, вёрстка не меняется.
- `#toTop` — `bottom:1.2rem` → `bottom:calc(1.2rem + env(safe-area-inset-bottom, 0px))`
  (строка ~432).

**Верификация** (методика аудита #93: инъекция hard-coded insets вместо `env()`,
замер текста через `Range.getClientRects` с clip по ancestor-overflow, top-зона
при `scrollTop=0`, home-зона после стабилизации скролла): **10/10 прогонов,
0 перекрытий** на 5 страницах (index, calculator, map, graph, sup/kreatin) ×
2 устройствах (14 Pro Max / SE):

- skip-link: textTop 61 > inset 59 (14 Pro Max), 22 > 20 (SE) — overlap 0 везде.
- #toTop (index): rectBottom 878.8 ≤ homeTop 898 (14 Pro Max), 647.8 ≤ 667 (SE).
- topHits=0, botHits=0, overflow=0 во всех 10 прогонах.

Примечание: `#toTop` создаётся только `script.js`, который грузится только в
`index.html` — на 4 других страницах проверка N/A, это не ошибка.

## 2. Кэш-бастинг: bump

- `style.css?v=416 → v=418` в **142 файлах** (`docs/*.html` + `docs/sup/*.html`,
  литеральная замена скриптом, без regex). `index.html` уже имел `v=418`
  (коммит fab27a6). Итог: **143 HTML @ v=418** (12 страниц + 131 в sup/) —
  совпадает с ожидаемым числом из задания.
- Отклонение от задания: ожидалось «417 → 418 в 143 файлах»; реально было
  416 в 142 файлах + index уже 418. Версия `v=417` никогда не существовала
  (`git log -S"style.css?v=417" --all` пуст). Итоговое состояние (143 @ 418)
  достигнуто.
- `CACHE_VERSION` в `docs/sw.js`: `'v85' → 'v87'` — замена только значения,
  номера строк не сдвинуты, `tests/test_silent_handlers.py` — **4 passed**.
  Отклонение: ожидалось «v86 → v87»; `v86` никогда не существовал в истории
  sw.js (`git log -S"v86"` пуст). Целевое значение v87 принято по заданию.
- Упоминания версий в `reports/*.md` и `docs/dev/` не трогались (история).

## 3. Скиллы: 19, валидны 17

Каталог `.opencode/skills/` — 19 директорий, у всех есть `SKILL.md`.
Валидация (PyYAML, `name` == каталог, `description` непустой, `license`
присутствует): **17/19 без замечаний**.

Два исключения, оба рабочие:

- `cyberaudit` — нет ключа `license`; схема `name/description/compatibility/
  metadata` (автор ArisRoman, v3.1.5). Скилл git-ignored намеренно
  (`.gitignore:273`, комментарий про лицензию) — стоп-условие «скилл потерян»
  не сработало, файлы на месте (~120 файлов).
- `visual-design-audit` — нет ключа `license`; вместо него `mode: subagent`.
  Скилл доступен в окружении и загружается.

## 4. Плагины: 4

`C:\Users\TshK\.config\opencode\opencode.jsonc`, строка 4:

```
@azumag/opencode-rate-limit-fallback@1.70.11
@andrewhampton/opencode-handoff
openslimedit@latest
@tarquinen/opencode-dcp@latest
```

Все 4 на месте. ✓

## 5. MCP: 5 активны, 2 выключены по дизайну

Живые вызовы (2026-10-08):

- `context7` — `resolve-library-id` → `/microsoft/playwright` ✓
- `playwright` — `browser_navigate` → `http://localhost:200`, заголовок
  «БАДы: доказательства и механизмы - 130 добавок | Brain 25 Evidence» ✓
- `serena` — `list_memories` ✓
- `codebase-memory` — `get_graph_schema` ✓
- `git` — `git_status` / `git_branch` ✓ (12 инструментов)

`exa` и `duckdb` — `enabled: false` в конфиге (по дизайну, не поломка). ✓

## 6. LSP

- `pyright` 1.1.414 ✓ (в PATH)
- `typescript-language-server` 6.0.1 ✓ (в PATH)

## 7. SKILLS_INDEX.md

Было: строка 4 «Обновлено: 2026-10-02. **Скиллов: 18.**» при 19 скиллах.
Стало: «Обновлено: 2026-10-08. **Скиллов: 19.**» Остальное содержимое
актуально (нумерованный список 1–19, полный список из 19 имён, таблицы
назначений). ✓

## 8. AGENTS.md

Сверка с реальностью: 19 скиллов ✓; таблица скиллов — 19 строк ✓; MCP-статусы
(context7, playwright, serena, exa/duckdb disabled, git 12 tools) ✓; LSP
(pyright, typescript-language-server в PATH) ✓; плагины (handoff,
rate-limit-fallback упомянуты) ✓; ловушки проекта актуальны. Расхождений нет.

Наблюдение (не ошибка): `openslimedit` и `@tarquinen/opencode-dcp` в AGENTS.md
не упоминаются — документ их не обязан перечислять.

## 9. Коммит и CI

- Основной коммит: `7da9e5c` — `fix(v5.6.2): safe-area P1 + infra check`
  (223 файла: 142 HTML с бампом `?v=418`, `docs/style.css`, `docs/sw.js`,
  `.opencode/skills/SKILLS_INDEX.md`, отчёты). Pre-commit: 809 passed,
  sitemap пересобран (143 URL).
- CI на `7da9e5c`: **failure** — шаг «Feed check»: `build_feed.py --check`
  требует пересобранный `feed.xml` под дату коммита (08 Oct 2026).
- Исправление: `2881bbc` — `docs: пересобрать feed.xml — дата коммита
  08 Oct 2026` (2 строки: lastBuildDate/pubDate 07→08 Oct).
- Итог: CI на `2881bbc` — **success** (оба job: Python 3.12 и 3.13).

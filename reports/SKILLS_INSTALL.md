# SKILLS_INSTALL.md — установка скиллов (Части A и C)

Дата: 2026-10-02 · Ветка: `v5.1-dev` · Коммитов не делал
Скиллов в `.opencode/skills/`: **18** (было 12, стало 18)

```
pytest -q → 736 passed, 18 skipped
```

---

## 1. Что установилось

| # | Скилл | Источник | Файлов | Размер | Статус |
|---|---|---|---:|---:|---|
| 1 | `cyberaudit` | `cyberaudit-skill@3.2.1` | 131 | 556 КБ | **установлен** (и в репозиторий, и глобально) |
| 2 | `accessibility-check` | `Quality-Max/free-qa-skills` | 1 | 2,5 КБ | **установлен** |
| 3 | `seo-check` | `Quality-Max/free-qa-skills` | 1 | 2,8 КБ | **установлен** |
| 4 | `core-web-vitals` | `Quality-Max/free-qa-skills` | 1 | 3,2 КБ | **установлен** |
| 5 | `i18n-rtl-audit` | `Quality-Max/free-qa-skills` | 1 | 3,0 КБ | **установлен** |
| 6 | `data-quality-auditor` | `alirezarezvani/claude-skills` | 5 | 42,6 КБ | **установлен** |

Из восьми запрошенных закрыто **пять** (security-audit, accessibility-audit,
seo-audit, performance-audit, data-quality-audit) — и шестая сверх списка
(i18n-audit), потому что готовый скилл нашёлся.

### Важное уточнение по двум пунктам задания

**security-audit и api-audit — это один скилл.** `cyberaudit` покрывает оба:
у него модули `web/`, `api/`, `mobile/`, `cloud/`. Отдельного `api-audit`
ставить не нужно — он внутри.

**i18n-audit существует.** В задании было «готового нет, можно собрать самому».
Нашлось готовым: `i18n-rtl-audit` в том же репозитории `free-qa-skills`.
Писать свой не требуется.

### Отложено

| Скилл | Что нашлось | Почему не поставил |
|---|---|---|
| `llm-security-audit` | Репозиторий `dacuma-labs/agent-security-audit` существует, `SKILL.md` валидный | Его **собственный** description: *«Do NOT use for: projects with no agentic components»*. У нас статический сайт без агентов. Ставить перед v6.0, как вы и планировали |

---

## 2. Шесть подводных камней установки

Все шесть — не теория, а то, что сломалось по дороге.

### 2.1 `npx skills add` ставит не туда

`skills` CLI кладёт скилл в **`.agents/skills/`** (кросс-агентный стандарт),
а не в `.opencode/skills/`, где живут остальные 12. Плюс создаёт
`skills-lock.json` в корне репозитория.

Пришлось переносить руками и удалять `.agents`. Локфайл оставил — в нём
источник и хеши, это полезно.

### 2.2 Путь в задании не работал

```
npx skills add Quality-Max/free-qa-skills/accessibility-check
  → «No skills found»
```

Скиллы лежат в `skills/`, а не в корне. Правильно:

```
npx skills add Quality-Max/free-qa-skills/skills/accessibility-check
```

### 2.3 `cyberaudit install --local` засоряет репозиторий

Локальная установка создаёт директории сразу для **22 агентов**
(`.cursor`, `.windsurf`, `.gemini`, `.codeium`…) и кладёт скилл в
`.config/opencode/`, а не в `.opencode/`.

Обошёл: установил во временную директорию, скопировал в
`.opencode/skills/cyberaudit` вручную.

### 2.4 `cyberaudit` уже был установлен

`~/.config/opencode/skills/cyberaudit` — **v3.1.5**, установлен глобально
(отсюда и уведомление о новом скилле в середине сессии). Установил **v3.2.1**
в репозиторий. Глобальная копия осталась старше — если будет расхождение
поведения, причина здесь.

### 2.5 Скрипты `data-quality-auditor` падают в консоли Windows

```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f7e2'
```

Скрипты печатают эмодзи 🟢, а консоль Windows — cp1251. Лечится так:

```powershell
$env:PYTHONIOENCODING="utf-8"
```

### 2.6 `data-quality-auditor` работает с CSV, а у нас JSON

Прогнал на настоящем `docs/data.json`:

```
Rows: 14336  |  Columns: 1
Data Quality Score (DQS): 97.0/100  PASS — Production-ready
```

**Это число бессмысленно.** Скрипт прочитал JSON как плоский текст: 14 336
«строк» — это строки файла, одна «колонка». Проверять наши данные нужно
существующим скиллом `data-validation` (он умеет JSON + DuckDB).
`data-quality-auditor` оставлен для CSV-источников и для численного
профиля, когда появится такой формат.

---

## 3. vortix-cli: не скилл, а инструмент

Задание ждало от `vortix init` скиллов `seo-audit` и `performance-audit`.
**Их не будет** — это CLI, агентом он не вызывается, его надо запускать
руками и читать вывод.

`vortix init` — **только интерактивный**, флагов не имеет, а список стеков
состоит из одних SSG-генераторов (astro, nextjs, hugo, jekyll…), которых в
проекте нет. Пайпом в stdin multi-select не кормится.

Конфиг пришлось написать рукой — `.vortix/config.json`:

```json
{
  "target": { "outputDir": "docs" },
  "build": false,
  "categories": { "performance": true, "security": true, "accessibility": true,
                   "bugs": true, "seo": true, "maintainability": true,
                   "privacy": true },
  "failOn": "error",
  "performance": { "budgets": { "lcpMs": 2500, "cls": 0.1, "maxPageWeightKb": 1500 } }
}
```

`resolveAdapter` принимает отсутствие адаптера, если задан `outputDir`, —
это я проверил в исходнике пакета, а не угадал. `build: false` обязателен,
иначе vortix требует генератор статики.

**Ещё одна находка:** `.vortix/config.json` обязан быть **UTF-8 без BOM**.
PowerShell 5.1 `Set-Content -Encoding utf8` пишет BOM, и vortix падает с
`Failed to parse .vortix/config.json`.

---

## 4. Первый прогон: 77/100, Grade C — и это число занижено

```
Vortix — adapter: manual · static checks: 18 pages · dynamic checks: 18/18
OVERALL 77/100 · Grade C · 338 errors, 26 warnings, 38 notices

⚠ performance   ✔ security   ✖ accessibility   ✖ bugs   ⚠ seo
```

| Категория | Ошибок |
|---|---:|
| `bugs.broken-links` | **294** |
| `accessibility.color-contrast` | 27 |
| `accessibility.axe` | 17 |
| `security.https-enforced` | 1 |

### 4.1 294 из 338 ошибок — ложные

vortix сообщает, что в `index.html` битые ссылки на `index.html`,
`feedback.html`, `support.html`, `methodology.html`, `calculator.html`,
`map.html`. **Все эти файлы существуют, и все эти ссылки в разметке есть** —
проверено и `Test-Path`, и поиском по `docs/index.html`.

Воспроизвёл на минимальном сайте из двух страниц, вне нашего репозитория:

```
docs/a.html  →  <a href="b.html">
docs/b.html  →  существует
docs/style.css → существует

vortix: error | bugs.broken-links | Broken internal link reference "b.html"
vortix: error | bugs.broken-links | Broken internal stylesheet/link "style.css"
```

Причина в исходнике пакета — функция `existsExactCase()`:

```js
let current = path.parse(fullPath).root || path.sep;   // уходит в корень ФС
readdirSync(current)
```

Она идёт от корня файловой системы, а не от каталога страницы, поэтому любой
относительный путь без директории не находится. Передача живого URL
(`vortix ci http://localhost:8000`) **не помогает** — проверил, всё те же
294 ошибок.

**Вывод: `bugs.broken-links` в vortix 0.1.3 непригоден.** Реальная оценка
проекта выше заявленной: без них остаётся **44 ошибок**, и почти все
из них — контраст.

### 4.2 Что в этих 44 ошибках — настоящее

Из 44 ошибок доступности **43 — контраст** и 1 — клавиатура:

- `<span data-version="app">5.0.0</span>` — повторяется 5+ раз, самый частый
  элемент с проблемой;
- `.hint` — `#topicHint`, `#messageHint`;
- `.btn.primary` — `#addBtn`;
- 1 × `scrollable-region-focusable` — скроллируемая область без клавиатурного
  доступа.

Это материал для `accessibility-check` и для правок палитры в Шагах 6-9.

### 4.3 Мёртвый CSS: 4 наших — правда, 16 чужих — ложь

`maintainability.dead-css` даёт 20 предупреждений. Проверил все 20 по
112 текстовым файлам `docs/` (HTML + JS + CSS), потому что скилл ищет только
по HTML, а у нас часть разметки строится скриптами:

| Класс | Где найден | Вердикт |
|---|---|---|
| `.hdr` | только `style.css:21` | **мёртв** |
| `.flash` | нигде | **мёртв** |
| `.wbLink` | только `style.css:181` | **мёртв** |
| `.inter-critical` | только `style.css:1055` | **мёртв** (страница перешла на `.sb-sev.critical`) |
| 16 классов в `vis-network.css` | — | **ложь**: vis-network создаёт их в рантайме |

### 4.4 Прочее

- **seo**: 13 `structured-data`, 12 `canonical-url`, по 1 — `meta-tags`,
  `robots-sitemap`, `og-images`.
- **performance**: вес страницы 2152 КБ при бюджете 1500; 8 сторонних
  блокирующих ресурсов, все — Google Fonts (`fonts.googleapis.com`).
- **privacy**: 4 внешних шрифта, 2 fingerprinting API.

---

## 5. Часть C — SKILLS_INDEX.md

`.opencode/skills/SKILLS_INDEX.md` переписан: **v1.1 → v2.0**, 124 вставки,
21 удаление. Счётчик скиллов и число тестов вставлены **чтением с диска и из
вывода pytest**, а не по памяти.

Что изменилось по существу:

1. **Порядок применения расширен с 12 до 18 шагов.** Новые скиллы встали не
   «в конец списка», а туда, где бьют по фундаменту: `cyberaudit` — третьим,
   сразу после структуры и данных; `accessibility-check` — девятым, рядом с
   визуалом; `seo-check` и `core-web-vitals` — перед `release-check`.

   В релизной цепочке появилось:
   `release-check → cyberaudit → accessibility-check → seo-check → core-web-vitals → …`

2. **Добавлена таблица «Границы между скиллами» для новых.** Без неё легко
   запустить два скилла на одну задачу: контраст — это `accessibility-check`,
   а не `mobile-deep-audit`; `meta`/`canonical` — это `seo-check`, а не
   `docs-sync`; `data.json` — это `data-validation`, а не `data-quality-auditor`.

3. **Добавлен раздел «Известные ограничения новых скиллов»** — четыре
   ограничения из пунктов 2.5, 2.6 и 4.1. Скилл, который молча врёт,
   опаснее отсутствующего.

4. **Добавлен раздел «Внешний инструмент (не скилл)»** — vortix отделён от
   скиллов, чтобы никто не искал его через `skill`.

5. **Поправлен устаревший счётчик тестов**: было написано «727 passed»,
   фактически 736.

6. **Правило 7 «Внешний скилл — не значит проверенный»** — находки из чужих
   репозиториев проходят то же правило верификации, что и наши. Пункт 4.1 —
   ровно тот случай, когда это правило окупилось.

---

## 6. Состояние репозитория

```
 M .opencode/skills/SKILLS_INDEX.md     124 +, 21 -
?? .opencode/skills/accessibility-check/    1 файл
?? .opencode/skills/core-web-vitals/        1 файл
?? .opencode/skills/cyberaudit/          131 файлов
?? .opencode/skills/data-quality-auditor/  5 файлов
?? .opencode/skills/i18n-rtl-audit/        1 файл
?? .opencode/skills/seo-check/             1 файл
?? .vortix/                               config.json
?? skills-lock.json
```

`pytest -q → 736 passed, 18 skipped`. Файлы `docs/` не тронуты.

### Отдельно: в репозитории появился коммит, который не я делал

Перед началом работы `git status` показывал 19 изменённых файлов `docs/` из
Шага 3. К моменту проверки они оказались в коммите
`8d6c694 chore(v5.1): step 3 - interactions migration (29 rules, 61 kept)`,
автор и коммитер — `DeadSno <deadsno1613@gmail.com>`, время
`Fri Oct 2 19:59:34 2026 +0300`.

Коммит содержит ровно работу Шага 3 плюс `reports/MIGRATION_STEP3.md`.
**Я его не делал** — ни в этой, ни в предыдущей сессии коммитов не было.
Ничего откатывать не нужно; констатирую факт, потому что вы просили не
коммитить, и чтобы вы знали, где теперь лежит эта работа.

---

## 7. Рекомендации

1. **Отключить или не читать `bugs.broken-links` в vortix.** Пока он даёт
   294 ложных ошибок из 338, его вывод в отчётах вводит в
   заблуждение. Свои ссылки у нас проверяются тестами.
2. **Разобрать 43 ошибки контраста** — они сгруппированы вокруг
   `data-version="app"`, `.hint` и `.btn.primary`. Это самая дешёвая
   победа доступности: три селектора.
3. **Удалить 4 мёртвых класса** (`.hdr`, `.flash`, `.wbLink`,
   `.inter-critical`) — проверено, мёртвые.
4. **Решить, нужен ли `cyberaudit` в репозитории** — 556 КБ и 131 файл в
   git. Он уже есть глобально; в репозитории он только ради команды.
   Альтернатива — оставить глобально и вычеркнуть из коммита.
5. **Убрать Google Fonts** или хотя бы добавить `preconnect` — это 8 из 10
   замечаний по производительности и 4 по приватности.
6. **`llm-security-audit`** — поставить перед v6.0, как и планировалось.

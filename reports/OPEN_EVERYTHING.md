# Полная картина открытого (13.10.2026, доп. 14.10.2026)

Инвентаризация по 10 источникам + сверка по коду (git/grep). HEAD: `b51ec4a`
(interactions закрыт в этом коммите). Правки кода НЕ вносились — только сбор.

Дополнение 14.10.2026 (HEAD `f8f0e5c`): добавлены №42 `MKT-P2-06`
(`og:description` ≠ `meta description`, 10/13) и №43 `MKT-P2-07`
(`twitter:title`/`twitter:description` устарели на 5 страниц, на 8/13
нет вовсе). Оба измерены заново по `docs/*.html`, не взяты из аудита.
Новые ID выбраны потому, что `MKT-P2-04`/`MKT-P2-05` уже заняты и
закрыты: `twitter:card` (`b5b1ef2`, 144/144) и `og:site_name`
(`1a381fe`/`c58ad22`, 144/144).

**⚠ СТОП-УСЛОВИЯ СРАБОТАЛИ (оба):**

1. Реально открыто **107** после дополнения (было 105) (>80) →
   требуется приоритизация (см. §Батчи).
2. Расхождений источников **15** (>10) → показаны в §Расхождения.

---

## СВОДКА

| Категория | Кол-во |
|---|---:|
| 🔴 Фиксы (техдолги) | **52** (43 подтверждён + 9 ⚠ спорных/требуют замера) |
| 🟡 Улучшения | **34** (вкл. 17 отложенных корзин TR-V57/TR-V60) |
| ⚪ Caveats | **21** |
| ✅ Закрыто, но не отмечено в источниках | **56** |
| **Итого реально открыто (N+M+K)** | **107** |

Метод: источники 1–5 (FINAL_WAVE, FINAL_WAVE_BATCH3, OPEN_TECHDEBT,
audits/*.md — 13 файлов, не 11, AUDIT_MASTER, ROADMAP, trends) → дедупликация
ID → сверка спорных и «закрытых» по коду (grep/git). Концепция §9: отдельного
файла нет, только строка `ROADMAP.md:174` (v5.7, модалка `<dialog>`) — см.
расхождение #15. GitHub issues: открыт **ровно 1** — #6 (watchdog, см. caveats).

---

## ФИКСЫ

### Подтверждены (43)

| # | ID | Что | Источник | Сложность | Файл/код |
|---|---|---|---|---|---|
| 1 | F-15 (#15) | U+FFFD: funders.json 1 + unpaywall.json 18 | FINAL_WAVE | M | data/papers/*.json |
| 2 | F-16 (#13) | 18 карточек без `citations` (= DATA-P2-03) | FINAL_WAVE | M | docs/data.json |
| 3 | F-17 (#26) | 190 из 393 `key_sources[].pmid` не находят записей | FINAL_WAVE | M | docs/data.json |
| 4 | F-20 (#22) | `.trustChips` — 12 вхождений разбросаны | FINAL_WAVE | M | docs/*.html |
| 5 | F-21 (#38) | Палитры грейдов дублируются (badge ×5 + inline в шаблоне) | FINAL_WAVE | M | style.css, sup.html.j2 |
| 6 | F-22 (HC-P2-06) | Нет классов статусов у находок аудита | FINAL_WAVE | M | audits/*.md |
| 7 | F-23 (DATA-P2-11) | `forms: null` у 123 карточек (шаблон готов) | FINAL_WAVE | M | docs/data.json |
| 8 | F-24 (DATA-P2-08) | `key_sources` >3 у 26 карточек | FINAL_WAVE | M | docs/data.json |
| 9 | F-25 (DATA-P2-12) | `metaCount == 0` у 7 карточек | FINAL_WAVE | M | docs/data.json |
| 10 | F-26 (#89) | 56 карточек без запроса в `build_key_sources` | FINAL_WAVE | M | scripts/build_key_sources.py |
| 11 | F-27 (#90) | `price_history.csv` отсутствует, а конвейер ссылается | FINAL_WAVE | M | data/ — ✔ сверено: файла нет |
| 12 | F-32 (CYBER-P1-02) | `bootstrap 5.0.0-beta3` — предрелиз в docs/vendor. **WONTFIX** 14.10.2026 (батч 8): только `graph.html`, страница удаляется v5.6.5 | FINAL_WAVE | M | docs/vendor/ — ✔ сверено |
| 13 | F-34 (A11Y-P2-05/JS-P2-03) | Нет `aria-live` / live-region в калькуляторе | FINAL_WAVE | M | docs/*.html |
| 14 | F-35 (A11Y-P2-07) | «Ничего не найдено» без эха запроса | FINAL_WAVE | M | docs/script.js, map.html |
| 15 | F-36 (MOB-P2-12) | Лента хедера ≤428px, скроллбар скрыт — нужно UX-решение | FINAL_WAVE | M | docs/style.css |
| 16 | F-37 (SEO-P2-01) | `description` дублируется meta/og/JSON-LD, 13/15 | FINAL_WAVE | M | docs/*.html |
| 17 | F-40 (#40) | `dosage_parsed.json` — находка без предмета, переформулировать | FINAL_WAVE | M | data/ — ✔ сверено: файла нет |
| 18 | F-41 (#42) | Локальные `<style>` с `.top` на 7 страницах | FINAL_WAVE | L | docs/*.html — ✔ сверено: по 1 блоку на каждой |
| 19 | F-42 (#10) | 153 инлайновых `style=` | FINAL_WAVE | L | docs/*.html |
| 20 | F-43 (#7) | 179 вхождений `.btn` — дизайн-система не вынесена | FINAL_WAVE | L | docs/*.html |
| 21 | F-44 (#17) | 110 скриптов без тестов (35 — `_tmp_93_*.py`) | FINAL_WAVE | L | scripts/ |
| 22 | F-45 (DATA-P1-02) | `hedges_g_outcome` пусто у 86 карточек | FINAL_WAVE | L | docs/data.json |
| 23 | F-46 (DATA-P1-12/PRJ-P1-01) | `timeseries` 94/130, в data.json поля нет ни у одной | FINAL_WAVE | L | data/, src/ |
| 24 | F-47 (I18N-P1-01) | RTL не поддержан — физические свойства в лок. `<style>` | FINAL_WAVE | L | docs/style.css |
| 25 | F-48 (I18N-P2-01/JS-P2-02) | 229 строк JS с захардкоженными строками | FINAL_WAVE | L | docs/*.js |
| 26 | F-49 (I18N-P2-02/03) | 472 атрибута и 529 стрелок без локализации | FINAL_WAVE | L | docs/*.html |
| 27 | F-50 (DATA-COI) | COI собирается (486 КБ), но не показывается | FINAL_WAVE | L | src/, шаблоны (v5.7) |
| 28 | F-51 (LEGAL-P2-02) | Нет DOI-ссылок: pubmed 131, `doi.org` 0 | FINAL_WAVE | L | templates/ |
| 29 | DATA-P2-07 | `hedges_g_all.json` покрывает 113/130 | OPEN_TECHDEBT | M | data/ |
| 30 | DATA-P2-10 | `grade` не монотонен по scienceIndex — 46 нарушений/129 пар | OPEN_TECHDEBT | M | docs/data.json |
| 31 | DATA-P2-13 | `citations`/`ongoing`/`wiki` = null у 17/36/40 | OPEN_TECHDEBT | M | docs/data.json |
| 32 | SEO-P2-03 | Одна ссылка на `/sup/` | OPEN_TECHDEBT | S | docs/index.html |
| 33 | MKT-P2-04 | `twitter:card` на 8/15 | OPEN_TECHDEBT | S | ✔ сверено: 8 |
| 34 | MKT-P2-05 | `og:site_name` на 6/15 | OPEN_TECHDEBT | S | docs/*.html |
| 35 | MOB-P2-13 (остаток) | `orientation: portrait-primary` в манифесте | mobile.md | S | ✔ сверено: в манифесте |
| 36 | SEO-P1-01 | `<title>` вне 40–60 на 87/145 (было 140/143) | seo.md | M | docs/*.html |
| 37 | SEO-P1-02 | `description` вне 120–160 на 91/145 | seo.md | M | docs/*.html |
| 38 | PERF-P1-01 | `data.json` 760 КБ через script.js:32; ленивая batch C не завершена — нужен повторный CWV-замер | perf.md | M | docs/script.js |
| 39 | PERF-P1-02 | `trends.html` CLS 0.1101 — нужен повторный замер | perf.md | M | docs/trends.html |
| 40 | SK-P1-03 (остаток) | `cyberaudit`: многострочный `description` (license уже добавлен `12119a5`) | skills.md | S | .opencode/skills/cyberaudit/SKILL.md — **WONTFIX** (14.10.2026): путь в `.gitignore` |
| 41 | BATCH3-остаток | Устаревшие ссылки в `audits/i18n.md:29` (science2.js:188, script.js:787 → фактически 18/13) | FINAL_WAVE_BATCH3 | S | reports/audits/i18n.md |
| 42 | MKT-P2-06 | `og:description` ≠ `meta description` на 10/13 | SEO-хвост 14.10.2026 | M | docs/*.html — atlas, calculator, faq, feedback, glossary, graph, interactions, map, methodology, trends |
| 43 | MKT-P2-07 | `twitter:title`/`twitter:description` устарели на 5 страниц, на 8/13 их нет вовсе | SEO-хвост 14.10.2026 | M | docs/{faq,feedback,glossary,graph,methodology}.html |

### ⚠ Спорные — требуют замера или решения (9)

| # | ID | Что | Источник | Сложность | Файл/код |
|---|---|---|---|---|---|
| 42 | color-contrast index | 165 узлов чипов (`div[data-id] > .tagChips > span`), 2 failed при RUN_A11Y. Спор: D_WAVE «#44 закрыт 12.10» vs D_WAVE_PART1 «открыт вопрос №1» | a11y.md, D_WAVE_PART1 | S (замер) | docs/index.html |
| 43 | A11Y-P2-03 | Одна ссылка без индикатора фокуса — audits открыт vs OPEN_TECHDEBT «уже закрыто» | a11y.md | S (замер) | docs/trends.html |
| 44 | MOB-P2-07 | Бейджи sup-index 11.2–11.52 px — audits открыт vs OPEN_TECHDEBT «закрыт» | mobile.md | S (замер) | docs/sup/index.html |
| 45 | MOB-P2-09 | `result-panel` sticky в ландшафте 322 px — спор статусов | mobile.md | S (замер) | docs/calculator.html |
| 46 | MOB-P2-11 | Мелкий текст 10.88–11.52 px, 703 узла — спор статусов | mobile.md | M (замер) | docs/style.css |
| 47 | ~~DATA-P2-02~~ | `ma_top3` = null у 50 — **ЗАКРЫТО 14.10 (батч 9A)**: null = 0, `[]` у 4 карточек; поле читается только `script.js:519` (`s.ma_top3 \|\| []`), на рендер не влияет | data.md | S | docs/data.json |
| 48 | ~~DATA-P2-04~~ | Мёртвые ключи `PRIOR_G` — **ЗАКРЫТО 14.10 (батч 9A)**: гейт `test_prior_g_no_new_dead_keys` (`2f954e4`) + ещё 4 теста; путь в находке был неверен | data.md | S | src/content.py:1260 |
| 49 | A11Y-P2-06 | 5 пустых состояний «—»: замер дал 0 голых `<td>—</td>` — переформулировать находку | data/a11y.md | S | docs/calculator.html |
| 50 | DATA-P2-14 | 79 объединённых против 59 атомарных категорий — **путь исправлен 14.10 (батч 4)**: числа из `docs/data.json`, а не `docs/effect_tags.json` | data.md | S | docs/data.json |
| 51 | DATA-P2-15 | `citations` недосчитан у 7 карточек из 130 — OpenAlex не индексирует часть PMID из `key_sources`, сумма молча теряет слагаемые. Добавлена 14.10 (батч 9A), закрытие в 9b | data.md | M | docs/data.json |

---

## УЛУЧШЕНИЯ

### Активные (17)

| # | ID | Что | Источник | Сложность |
|---|---|---|---|---|
| 1 | MKT-P1-01 | Нет слогана | seo.md | S |
| 2 | MKT-P1-03 | Нет соцдоказательств на support | seo.md | M |
| 3 | MKT-P1-04 | Нет воронки | seo.md | M |
| 4 | MKT-P1-05 | Нет Schema.org — 0 `ld+json` (✔ сверено) | seo.md | M |
| 5 | MKT-P1-06 | Нет блока «почему я» | seo.md | M |
| 6 | MKT-P1-07 | Нет CTA в калькуляторе | seo.md | M |
| 7 | MKT-P1-08 | Нет соцдоказательств (дубль MKT-P1-03) | seo.md | S |
| 8 | HC-P2-01 | Иконки — эмодзи (5 `<svg>` появились — «почти закрыто») | html-css.md | M |
| 9 | HC-P2-02 | 26 размеров шрифта (полная свёртка к 6 отложена) | html-css.md | M |
| 10 | HC-P2-03 | Хардкод-hex ~103 литерала против 47 переменных | html-css.md | M |
| 11 | HC-P2-04 | 15 `box-shadow` | html-css.md | S |
| 12 | HC-P2-05 | 6 градиентов | html-css.md | S |
| 13 | ~~QA-COV~~ | **ЗАКРЫТО 14.10 (батч 8E)** — метрика переопределена: 89 `.py` в `scripts/`, 13 реальных тестов (14.6%), не 16 из 131 | data.md | M |
| 14 | A11Y-P2-08 | Медиазапросы только `max-width` | a11y.md | S |
| 15 | MKT-P2-03 | `og:image` не на 131 sup-странице (основные 13 есть) | seo.md | M |
| 16 | PERF-P2-01 | Тяжёлые вендоры: vis-network 672 КБ, chart 200 КБ, bootstrap 78 КБ | perf.md | M |
| 17 | PRJ-P2-02 | Корзина прочих P2 project/release (4 пункта без детализации) | perf.md | S |

### Отложенные корзины (17) — в ROADMAP, не в батчи

| # | ID | Что | Источник | Сложность |
|---|---|---|---|---|
| 18–28 | TR-V57-01…11 | Средне-срочные улучшения v5.7–9 (11 шт.) | trends.md, ROADMAP | — |
| 29–34 | TR-V60-01…06 | Крупные архитектурные v6.0+ (в т.ч. DuckDB-Wasm + OPFS) | trends.md, ROADMAP | — |

---

## CAVEATS

| # | Что | Кто решает |
|---|---|---|
| 1 | `index@412` в WebKit не снимается (потолок 32767 px) — задокументированная дыра покрытия (F-19 закрыт как фикс теста, дыра остаётся) | инструмент — не закрывать |
| 2 | `route.abort()` не работает в Playwright-обёртке (#85) — замеры «без CDN» дают ложный ноль | инструмент — не закрывать |
| 3 | Мобильный аудит неполный (#93): WebKit, safe-area не полностью, PWA standalone, 19 из 131 sup | владелец — план отдельной волны |
| 4 | Прод-CLS (#102) — правкой в репо не закрывается, нужен доступ к проду | владелец |
| 5 | Юридические (#92): файл юриста есть (✔ сверено), но состав политики и сроки хранения ждут юриста; открыт вопрос экрана согласия; РКН не упомянут (осознанно) | юрист/владелец |
| 6 | SK-P0-01 — субагенты не могут загружать скиллы (инструмент `skill` только у team-lead) — ограничение harness | OpenCode/harness |
| 7 | AGENTS.md «19 скиллов» против факта 20 директорий и SKILLS_INDEX «20 копий» (✔ сверено) | владелец — правка AGENTS.md |
| 8 | #35 Backup — workflow готов, первая проверка за владельцем | владелец |
| 9 | #36 UptimeRobot — внешняя инфраструктура | владелец |
| 10 | #37 Google Search Console — внешняя инфраструктура | владелец |
| 11 | CYBER-P1-01 — нет security-заголовков (CSP/HSTS/…); GitHub Pages их не может выставить. **WONTFIX** 14.10.2026 (батч 7) | платформа — не закрывать |
| 12 | CYBER-P2-01 — тест security-заголовков: следствие п.11, нечего тестировать | платформа |
| 13 | DATA-P2-01 — `hedges_g_ci` = null у 48 — by design, данных не терялось | не дефект |
| 14 | A11Y-P2-01 — пропуски уровней заголовков — WONTFIX (ломает вёрстку) | не дефект |
| 15 | PERF-P2-02 — нет `.gz`/`.br` — хостинг сжимает сам | платформа |
| 16 | PRJ-P2-01 — 5 из 10 находок project-аудита ложные | не дефект |
| 17 | SK-P1-02 — «битые» ссылки в скиллах: FINAL_WAVE — by design (пути вывода), skills.md — открыт. Спор | владелец |
| 18 | 235 skipped — снапшоты привязаны к Windows-машине, гейт по RUN_SNAPSHOTS; снятие из CI — зафиксированное решение | не дефект |
| 19 | ~42 worktree в detached HEAD (✔ сверено: 42) — артефакт окружения OpenCode, не дефект репо | OpenCode |
| 20 | F-29 гейт HTML-валидности работает без html5lib/bs4 — «не валидация HTML5» | не дефект (задокументировано) |
| 21 | Issue **#6** (единственный открытый GitHub issue): watchdog «проверка ссылок/цен упала», run 38263051898 (12.10) | владелец — посмотреть ран workflow |
| 22 | CYBER-P1-02 — `bootstrap 5.0.0-beta3` внедряется только на `graph.html`; страница удаляется в v5.6.5 (`PAGES_REVIEW.md:39`, Вариант B 7→6). Обновлять нечего. **WONTFIX** 14.10.2026 (батч 8) | платформа/план — не закрывать правкой |
| — | #33 (`--info/--warn/--error`) — перенесён владельцем в v6.1+, предмет снят | решение принято |

---

## ✅ ЗАКРЫТО, НО НЕ ОТМЕЧЕНО В ИСТОЧНИКАХ (56)

**Верифицировано по коду в этой инвентаризации (17):**

| Что | Доказательство |
|---|---|
| Interaction UX (dot outline + anchor pan) | коммит `b51ec4a` (сессия Часть A) |
| ROADMAP #44 — a11y-гейт light theme | 19 вхождений `light` в tests/test_a11y_axe.py |
| ROADMAP #87 / REL-P1-03 — счётчик pytest | version.json tests: 1311 = 1070+235+6 ✔ |
| ROADMAP #101 — watchdog MCP/Serena | tests/test_toolchain_config.py существует |
| ROADMAP #92 — файл вопросов юриста | reports/archive/v56/legal_questions_for_lawyer.md есть |
| TR-P1-01 — `prefers-color-scheme` | 29 вхождений в docs/*.html (не в style.css) |
| TR-P1-02 — manifest id + shortcuts | manifest.webmanifest: id, 3 shortcuts (screenshots пусто сознательно) |
| TR-P1-03 — `:focus-visible` | 3 вхождения в style.css |
| TR-P1-04 — пин DuckDB | requirements.txt: `duckdb==1.5.5` (bump 1.5.6 отложен с обоснованием) |
| MOB-P2-08 — safe-area left/right | 18 вхождений safe-area-inset в style.css |
| MOB-P1-01 — `#toTop` на home-индикаторе | style.css:673 — safe-area + 44×44 |
| I18N-P2-04 — 2 `ru-RU` | остались только комментарии-обоснования (script.js:8,11) |
| SEO-P2-02 — charset до version.js | index.html:4 charset, :5 script ✔ |
| SEO-P2-04 — lastmod sitemap | 2026-10-12/13 ✔ |
| MKT-P1-02 — CTA на главной | 1 CTA-блок в index.html ✔ |
| Папка data-validation не удалена | Test-Path: False — удалена |
| ROADMAP #52 / QA-P2-01 — guard по строкам | ROADMAP + D_WAVE: закрыт `2b26464` |

**По отметкам в отчётах (верю, без повторного замера) (39):**
FINAL_WAVE/BATCH3 закрытые: F-03…F-14 (12), F-18, F-28, F-29, F-30, F-31,
F-38, F-39, F-52, A1, A2, A3 (23); OPEN_TECHDEBT §«перечёркнутые» (10):
A11Y-P1-01, A11Y-P1-10, HC-P1-01, MOB-P2-01/02/03/05/06/10, SK-P0-02;
§«уже закрыто, но не отмечено» (24): A11Y-P2-02/03*, DATA-P2-02*/04*/05,
QA-P2-01, HC-P1-02, HC-P2-02*, MOB-P1-01, MOB-P2-05, MOB-P2-07*/09*/11*,
REL-P1-02, REL-P1-03, REL-P2-02, SEO-P2-04, MKT-P1-02, MKT-P2-06/07/08,
TR-P1-01, TR-P1-03, SK-STALE-01/03, JS-P2-01 (= I18N-P2-04), HC-P1-03.
(* — часть из них вынесена в «спорные фиксы» из-за противоречия с audits/*.md.)
FINAL_WAVE §1 «закрыто, но не отмечено» (13): ROADMAP #44, #23, #87, #33,
#39, #14, #27, #92; SK-STALE-01/02; MOB-P2-13 (частично); DATA-P2-06;
REL-P2-01.

---

## РАСХОЖДЕНИЯ ИСТОЧНИКОВ (15)

| # | Что | Где расходятся |
|---|---|---|
| 1 | OPEN_TECHDEBT (ревизия 12.10 «до правок»): **14 из 55** 🔴 уже закрыты в FINAL_WAVE/BATCH3 | OPEN_TECHDEBT vs FINAL_WAVE/BATCH3 |
| 2 | AUDIT_MASTER: 128 открытых, но ~40 P1/P2 уже закрыты по другим файлам и не отмечены | AUDIT_MASTER vs audits/*.md + FINAL_WAVE |
| 3 | ROADMAP §открытые v5.6.4 устарел: #44, #87, #92, #101 закрыты (✔ сверены по коду) | ROADMAP vs код |
| 4 | #42: OPEN_TECHDEBT «закрыт как устаревший» vs FINAL_WAVE F-41 «открыт L». ✔ Сверено: 7 блоков `<style>` на месте → **открыт** | OPEN_TECHDEBT vs FINAL_WAVE |
| 5 | SK-P1-02: FINAL_WAVE §3 by design vs skills.md открыт | FINAL_WAVE vs skills.md |
| 6 | D_WAVE_FAST #44 открыт vs a11y.md закрыт (A11Y-P1-11) | D_WAVE_FAST vs a11y.md |
| 7 | Статусы MOB-P2-07/09/11, DATA-P2-02/04, A11Y-P2-03: audits/*.md — открыт, OPEN_TECHDEBT — «уже закрыто» | audits vs OPEN_TECHDEBT |
| 8 | skills.md шапка «открыто 9» vs волна S5 «открыто 10» | skills.md внутреннее |
| 9 | AUDIT_MASTER внутреннее: индекс 128 vs детализация P0-P3 = 126/125 | AUDIT_MASTER внутреннее |
| 10 | AGENTS.md «19 скиллов» vs факт 20 / SKILLS_INDEX «20» | AGENTS.md vs код |
| 11 | PERF-P1-01: 742 КБ vs актуальные 760 КБ | perf.md vs код |
| 12 | QA-P1-01 «20 скриптов» устарел → F-44 «110 скриптов» | data.md vs FINAL_WAVE |
| 13 | MKT-P2-01/02 — дубли SEO-P1-01/02 (считать один раз) | seo.md внутреннее |
| 14 | MOB-P2-04 (кнопка BI↗) — устаревшая находка, в «Закрыто» не перенесена | mobile.md |
| 15 | Концепция §9 «Карточки БАД» — отдельного файла нет; только ROADMAP.md:174 (v5.7, модалка `<dialog>`); §9-ссылка ведёт в никуда (намёк: archive DOCS_AUDIT задача O14 «убрать §9-ссылку») | источник 6 задачи vs репозиторий |

---

## РЕКОМЕНДАЦИЯ ПО БАТЧАМ (после сверки)

Стоп-условие «>80 открыто» сработало → приоритизация обязательна. Порядок:
сначала верификация спорных и бумажная чистка статусов (это снимает ~60
строк ложного «открытого»), затем средние фиксы, затем L-группа.

**Батч 4 (следующий) — «верификация + мелкие фиксы + чистка статусов»:**
- RUN_A11Y замер color-contrast index → закрыть/подтвердить п.42 (спор).
- Целевые замеры спорных №43–48 (A11Y-P2-03, MOB-P2-07/09/11, DATA-P2-02/04).
- Переформулировать №49 (A11Y-P2-06) и №50 (DATA-P2-14) по факту замера.
- Быстрые фиксы: №33–35 (OG-теги, ссылка /sup/, orientation), №41 (ссылки
  i18n.md), №40 (SK-P1-03 description), №32.
- Бумажная чистка: проставить ✅ в audits/*.md, OPEN_TECHDEBT, AUDIT_MASTER
  по разделу «Закрыто не отмечено» (56); пересчитать индексы; поправить
  AGENTS.md 19→20 (caveat 7).
- Вопрос владельцу: №11 F-27 (price_history.csv — откуда источник?),
  №17 F-40 (dosage_parsed — что за предмет?), caveat 21 (issue #6).

**Батч 5 — «средние data + HTML»:** №1–16 из фиксов (U+FFFD, citations, pmid,
trustChips, палитры, статус-классы, forms, key_sources, metaCount, 56
запросов, bootstrap beta3, aria-live, эхо запроса, скроллбар-UX, description
дубли), №36–39 (title/description длины, PERF перемеры CWV/CLS).

**Батч 6 — «CSS/HTML L-группа»:** №18–21 (локальные `<style>`, инлайны, `.btn`,
110 скриптов без тестов), №29–31 (DATA-P2-07/10/13).

**Батч 7 — «i18n/RTL»:** №24–26 (RTL, 229 строк JS, атрибуты+стрелки) —
крупный, отдельная волна.

**Батч 8 — «маркетинг» (тексты — владелец):** №1–7 из улучшений (MKT-P1-*),
№15 (og:image sup), №4 (Schema.org).

**Не батчи — отложено:** №22–23, 27 (F-45/46/50 — данные, v5.7+);
TR-V57-01…11 (v5.7–9); TR-V60-01…06 (v6.0+).

**Финальный:** CHANGELOG v5.6.4, ROADMAP-секции (открытые v5.6.4 пересобрать),
AUDIT_MASTER пересчёт, merge v5.6-dev → main.

---

## МЕТОДИКА И ОГОВОРКИ

- Источники читались из основного каталога `C:\analytics\brain-25-evidence`
  (ветка v5.6-dev, HEAD `b51ec4a`).
- GitHub issues — через API (`gh` CLI отсутствует): открыт ровно 1 (#6).
- «11 файлов audits» в задаче — фактически 13 (включая D_WAVE_FAST,
  D_WAVE_PART1) — все прочитаны.
- Сложность S/M/L — из FINAL_WAVE/OPEN_TECHDEBT; audits/*.md сложности не
  дают.
- Счёт 105 = 50 фиксов + 34 улучшения + 21 caveat. Дубли между реестрами
  (QA-P2-02=DATA-P2-11, JS-P2-01=I18N-P2-04, JS-P2-02=I18N-P2-01,
  JS-P2-03=A11Y-P2-05, MKT-P2-01/02=SEO-P1-01/02, MKT-P1-08=MKT-P1-03,
  PRJ-P1-01=DATA-P1-12) сведены к одному пункту каждый.
- Коммит этого отчёта НЕ делался — ждёт решения владельца.

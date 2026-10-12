# AUDIT_MASTER — единая точка входа аудита

| | |
|---|---|
| **Дата** | 12.10.2026 (индекс пересчитан после волны D_FAST_3) |
| **Ветка** | `v5.6-dev` |
| **Назначение** | Единственная точка входа: индекс аудитов и список **открытых** находок |
| **Структура** | Закрытые находки и подробности — в `audits/<тип>.md`; исходные отчёты — в `archive/` |

> `STATE_OF_AUDIT.md` утрачен в worktree. Ревизия восстановлена по `AUDIT_*`/`STAGE_*`:
> ориентир **P0 = 0 открытых контраст/блокеров, P1 ≈ 21, P2 ≈ 73** (до этапов 1B–8).
> После этапов 1B–8 часть P1/P2 закрыта — актуальные числа см. в индексе ниже.

---

## 1. Индекс

| Тип | Открыто | Закрыто | Файл |
|---|---|---|---|
| a11y | 8 | 23 | [audits/a11y.md](audits/a11y.md) |
| data (+QA данных) | 24 | 4 | [audits/data.md](audits/data.md) |
| html-css | 9 | 9 | [audits/html-css.md](audits/html-css.md) |
| js (+безопасность) | 7 | 6 | [audits/js.md](audits/js.md) |
| legal | 2 | 4 | [audits/legal.md](audits/legal.md) |
| mobile | 8 | 13 | [audits/mobile.md](audits/mobile.md) |
| perf (+проект/релиз) | 11 | 5 | [audits/perf.md](audits/perf.md) |
| i18n | 7 | 6 | [audits/i18n.md](audits/i18n.md) |
| seo (+маркетинг) | 22 | 3 | [audits/seo.md](audits/seo.md) |
| trends | 21 | 8 | [audits/trends.md](audits/trends.md) |
| skills | 9 | 1 | [audits/skills.md](audits/skills.md) |
| **Итого** | **128** | **82** (+12 «не делать») | |

**Пересчёт 12.10.2026 (волна D_FAST_2).** Индекс отражает таблицы «Открыто»/«Закрыто»
в `audits/*.md`. Изменены две строки:

| Тип | Было | Стало | Что переведено |
|---|---|---|---|
| a11y | 9 / 21 | 8 / 23 | A11Y-P1-01 (тап-таргеты) и A11Y-P1-10 (cookie-ссылка) — в «Закрыто» |
| mobile | 14 / 7 | 13 / 8 | MOB-P2-05 (`p.hint`, `p.method-footer`) — в «Закрыто» |

**Пересчёт 12.10.2026 (волна D_FAST_3).** Перенесены в `audits/*.md` 6 ID, закрытых
кодом в волне D_FAST, но оставшихся в таблицах «Открыто» (прежний остаток снят):

| Тип | Было | Стало | Что переведено |
|---|---|---|---|
| mobile | 13 / 8 | 8 / 13 | MOB-P2-01, P2-02, P2-03, P2-06, P2-10 (`d0867d9`) |
| skills | 10 / 0 | 9 / 1 | SK-P0-02 (`12119a5`) |

Итог: открыто **128** / закрыто **82**. Места согласованы: §1, §2, §3,
`audits/mobile.md`, `audits/skills.md`.

Сопутствующие документы: [STATE_OF_AUDIT.md](STATE_OF_AUDIT.md) (утрачен, восстановлен здесь),
[PRE_MERGE_CHECK.md](PRE_MERGE_CHECK.md) (готовность merge), [CONSOLIDATION.md](CONSOLIDATION.md)
(консолидация отчётов), [STAGE_R1R2.md](STAGE_R1R2.md).

Журнал закрытия техдолгов: [audits/D_WAVE_FAST.md](audits/D_WAVE_FAST.md)
(волна D: #43, #45, #49, #51, #52).

Легенда приоритетов: **P0** — блокирует релиз; **P1** — деградация; **P2** — качество;
**P3** — шум.

---

## 2. Открытые находки

### P0 (1)

| ID | Находка | Тип |
|---|---|---|
| SK-P0-01 | Субагенты не могут загружать скиллы (инструмент `skill` только у team-lead) | [skills](audits/skills.md) |

### P1 (36)

| ID | Находка | Тип |
|---|---|---|
| DATA-P1-02 | `hedges_g_outcome` пусто у 86 (42 с `hedges_g`) — техдолг v5.6.4 | [data](audits/data.md) |
| DATA-P1-12 | `timeseries` 94/130 (36 карточек, 19 с citations>0) — техдолг v5.6.4 | [data](audits/data.md) |
| DATA-COI | COI (486 КБ) не показан — техдолг v5.7 | [data](audits/data.md) |
| QA-P1-01 | 20 критичных скриптов без тестов | [data](audits/data.md) |
| QA-P1-02 | Нет теста идемпотентности `build_sup` | [data](audits/data.md) |
| QA-P1-03 | Нет теста валидности HTML `sup/*.html` | [data](audits/data.md) |
| HC-P1-01 | H1/H2 разница 0.8 px, сломана иерархия glossary | [html-css](audits/html-css.md) |
| HC-P1-02 | `var(--panel)` не объявлена, `<pre>` прозрачный | [html-css](audits/html-css.md) |
| HC-P1-03 | Стартовые цифры скилла устарели | [html-css](audits/html-css.md) |
| CYBER-P1-01 | Нет security-заголовков (CSP/HSTS/…) | [js](audits/js.md) |
| CYBER-P1-02 | Bootstrap 5.0.0-beta3 устарел | [js](audits/js.md) |
| MOB-P1-01 | `#toTop` заходит на home-индикатор | [mobile](audits/mobile.md) |
| PERF-P1-01 | `index.html` тянет `data.json` 742 КБ (LCP 480 мс) | [perf](audits/perf.md) |
| PERF-P1-02 | `trends.html` CLS 0.1101 | [perf](audits/perf.md) |
| PRJ-P1-01 | `trends.html` 130 против 94 | [perf](audits/perf.md) |
| REL-P1-02 | CHANGELOG без v5.6.2, дубль `[v3.2.0]` | [perf](audits/perf.md) |
| REL-P1-03 | pytest 813 против показанных 1010 | [perf](audits/perf.md) |
| I18N-P1-01 | RTL не завершён: физические свойства в локальных `<style>` | [i18n](audits/i18n.md) |
| I18N-P1-05 | Жёсткие `min-width` 250/520 | [i18n](audits/i18n.md) |
| SEO-P1-01 | `<title>` вне 40–60 на 140/143 | [seo](audits/seo.md) |
| SEO-P1-02 | `description` вне 120–160 на 124/143 | [seo](audits/seo.md) |
| MKT-P1-01…08 | Нет слогана/CTA/соцдоказательств/воронки/Schema.org/«почему я» | [seo](audits/seo.md) |
| TR-P1-01…04 | `prefers-color-scheme`, manifest id/shortcuts/screenshots, `:focus-visible`, DuckDB 1.5.6 | [trends](audits/trends.md) |
| SK-P1-01 | `release-check` без приоритетов/действий | [skills](audits/skills.md) |
| SK-P1-02 | Скиллы ссылаются на устаревшие отчёты | [skills](audits/skills.md) |
| SK-P1-03 | `cyberaudit`: многострочный `description`, нет лицензии | [skills](audits/skills.md) |

### P2 (83)

| ID | Находка | Тип |
|---|---|---|
| A11Y-P2-01…08 | Нет nav на sup (130), пропуски заголовков (WONTFIX), focus-indicator, probe, нет aria-live, пустые `—`, «Ничего не найдено», 620px-сирота | [a11y](audits/a11y.md) |
| DATA-P2-01…14 | null-поля (`hedges_g_ci` 48, `ma_top3` 50, `forms` 123), U+FFFD, покрытие 113/130, `key_sources` до 5, categories 79 vs 59 | [data](audits/data.md) |
| QA-P2-01…03 | `test_silent_handlers` по номерам строк (#52), 123 null `forms`, нет теста битых ссылок sup | [data](audits/data.md) |
| HC-P2-01…06 | Эмодзи-иконки, 26 размеров, 139 hex, 11 теней, 4 градиента, нет статус-классов | [html-css](audits/html-css.md) |
| CYBER-P2-01…02 | Нет тестов заголовков/секретов | [js](audits/js.md) |
| JS-P2-01…03 | 2 `ru-RU`, 229 строк без i18n, `calculator` без live-region | [js](audits/js.md) |
| LEGAL-P2-01…02 | Нет дисклеймера на 2 стр., нет DOI-ссылок | [legal](audits/legal.md) |
| MOB-P2-04, 07…09, 11…13 | Safe-area left/right, theme-color, ориентация, мелкий текст (P2-01…03, 06, 10 закрыты `d0867d9`; P2-05 — `f7b56c6`; P2-04 помечен устаревшим) | [mobile](audits/mobile.md) |
| PERF-P2-01…02 | Тяжёлые вены (vis-network 673 КБ и др.), нет `.gz`/`.br` | [perf](audits/perf.md) |
| REL-P2-01…02, PRJ-P2-01…02 | ~40 worktree detached HEAD, version drift, ложные находки project | [perf](audits/perf.md) |
| I18N-P2-01…05 | 229 строк JS + 1474 inline, 176 атрибутов, 517 стрелок, 2 `ru-RU`, `text-align:left` | [i18n](audits/i18n.md) |
| SEO-P2-01…04, MKT-P2-01…08 | Дубли description, `version.js` до charset, OG-теги, lastmod | [seo](audits/seo.md) |
| TR-V57-01…11 | Средне-срочные улучшения v5.7–9 | [trends](audits/trends.md) |
| SK-P2-01…02, SK-STALE-01 | Нет `compatibility` у 18, `mode` декоративен, 3 скилла с данными 2025 | [skills](audits/skills.md) |

### P3 (6)

| ID | Находка | Тип |
|---|---|---|
| TR-V60-01…06 | Крупные архитектурные изменения v6.0+ (в т.ч. DuckDB-Wasm + OPFS) | [trends](audits/trends.md) |

---

## 3. Что дальше

Merge `v5.6-dev` → `main` выполнен **12.10.2026** (fast-forward `57e0089` →
`99c67b9`), выставлен тег `v5.6.3`. По итогам мержа закрыты `REL-P0-01`
(тег `v5.6.1` — коммит `21f296f`, он же в `v5.6-dev`) и `REL-P1-01`
(ветки разошлись 37/7 → расхождения нет). Остаётся P0 по скиллам
(`SK-P0-01`) и техдолг данных (timeseries, `hedges_g_outcome`,
COI) — v5.6.4/v5.7. Полная картина закрытого — в `audits/*.md` (разделы
«Закрыто» с коммитами и датами).

# Meta-Audit скиллов + сбор багов — v5.6.5-dev

- Дата: 2026-10-18
- Ветка: `v5.6.5-dev`
- HEAD до: `9ef76b0`, HEAD после правок скиллов: `0866bc4`
- Окружение: main checkout `C:\analytics\brain-25-evidence`, сервер `python serve.py` на `:8000`
- Скилл-основание: `skill-audit` (мета-аудит), `release-check`

---

## ШАГ 1 — Инвентаризация и оценка (19 проектных скиллов)

| # | Скилл | Назначение | Актуален? | Ценность | Решение |
|---|---|---|---|---|---|
| 1 | `site-navigation` | навигация сайта, битые ссылки | устарел (graph.html/atlas.html как живые страницы) | высокая | обновить |
| 2 | `visual-design-audit` | цвет, типографика, дизайн-система | частично устарел (карточка на graph.html) | высокая | обновить |
| 3 | `product-audit` | быстрый аудит UI/UX, маркетинг, QA, mobile | устарел («vis-network в graph.html») | средняя | обновить + граница с deep |
| 4 | `qa-deep-audit` | покрытие тестами, edge cases | нет проверок нового UI | высокая | обновить |
| 5 | `accessibility-check` | WCAG | общий, нет проектных проверок | высокая | обновить |
| 6 | `mobile-deep-audit` | мобильная адаптация | нет проверок нового UI | высокая | обновить |
| 7 | `seo-check` | meta, sitemap, structured data | общий | высокая | обновить |
| 8 | `core-web-vitals` | LCP, CLS, INP, TTFB, FCP | общий | высокая | обновить |
| 9 | `i18n-rtl-audit` | i18n и RTL | общий, но i18n.js уже существует | средняя | обновить |
| 10 | `data-audit` | данные (5 слоёв) | baseline устарел после dedupe PMIDs | высокая | обновить |
| 11 | `legal-compliance-audit` | юридический чек-лист БАД | фактически устарел (Метрика на 1 стр.) | высокая | обновить |
| 12 | `project-audit` | 12 проверок проекта | актуален, §10 пересекается с repo-size | высокая | кросс-ссылка |
| 13 | `repo-size-audit` | размер репо, крупные файлы | новый, НЕ в индексе | средняя | зарегистрировать |
| 14 | `ui-ux-deep-audit` | иерархия, отступы, состояния | актуален | высокая | оставить |
| 15 | `marketing-deep-audit` | воронка, CTA, тексты | актуален | высокая | оставить |
| 16 | `pwa-audit` | состояние PWA | актуален | средняя | оставить |
| 17 | `docs-sync` | синхронизация документации | актуален | средняя | оставить |
| 18 | `release-check` | готовность к коммиту/push | актуален | высокая | оставить |
| 19 | `skill-audit` | мета-аудит скиллов | актуален | средняя | оставить |
| — | `cyberaudit` | OWASP (вендорный, gitignore) | актуален | высокая | вне scope |
| — | `SKILLS_INDEX.md` | индекс скиллов | устарел (18, нет i18n/repo-size) | высокая | обновить |

Дубли: `repo-size-audit` ⊂ `project-audit §10` (углубление, не дубль — кросс-ссылка);
`product-audit` vs 4 deep-скилла (быстрый vs глубокий — граница). Удалять нечего.

---

## ШАГ 2 — Сделано (commit `0866bc4`, 14 файлов, +111/−26)

Обновлено 10 скиллов + `legal-compliance-audit` + `project-audit` + `repo-size-audit` + `SKILLS_INDEX.md`.
Pre-commit hook: **1758 passed, 238 skipped, 6 deselected** (64 с). Push: `9ef76b0..0866bc4 v5.6.5-dev`.

Вне scope (зафлажено, не правилось): `CONVENTIONS.md:17` («18 проектных»),
`AGENTS.md` («18 скиллов»), docstring `tests/test_skills_frontmatter.py` («ровно 18»).

---

## ШАГ 3 — Собранные баги (без фиксов)

Статика: QA-ссылки, data.json, DuckDB, meta, sitemap, i18n, tone-of-voice.
Браузер (Playwright, `:8000`): a11y табов/панели, 375px, контраст, CWV, редиректы, compare.

| Скилл / Тема | Найдено | Критичность | Пример (файл:строка) |
|---|---|---|---|
| `accessibility-check` | 1 | **High** | `interactions.html:1328,1341-1349,1451-1456` — `#nodeSidePanel` без `role="dialog"`/`aria-modal`/`aria-labelledby`; фокус не переводится в панель при открытии и не возвращается при закрытии; нет focus-trap |
| `accessibility-check` | 2 | **Med** | `interactions.html:279-283,408-417` — табlist: у `[role=tab]` нет `id`/`aria-controls`, у `[role=tabpanel]` нет `aria-labelledby`, нет стрелочной навигации (roving tabindex) |
| `visual-design-audit` | 3 | **Med** | `compare.html:58` и др. — инлайновые хардкод-цвета вне токенов (`#3498db`×3, `#5c6370`, `#c0392b`, `#e67e22`; всего 12+ hex при 25 `var()`) |
| `seo-check` | 4 | **Med** | `docs/sitemap.xml` — `compare.html` отсутствует (142 `<loc>`, compare нет) |
| `i18n-rtl-audit` | 5 | **Med** | `docs/i18n.js` — 329 ключей, но в разметке лишь 18 `data-i18n`; жёсткая кириллица: methodology 114, index 110 строк |
| `qa-deep-audit` / `seo-check` | 6 | **Low** | `favicon.ico` 404 (нет `link rel=icon`) |
| docs-hygiene | 7 | **Low** | `CONVENTIONS.md:17`, `AGENTS.md`, docstring `test_skills_frontmatter` — «18 проектных/скиллов» (вне scope) |
| `data-audit` | — | — | 0: 130 карточек, дубли 0, grade A-D ok, PMID/DOI валидны, DuckDB совпал |
| `qa` ссылки | — | — | 0: локальных 404 нет |
| `mobile-deep-audit` | — | — | 0: 375px без горизонтального переполнения (9 стр.) |
| `core-web-vitals` | — | — | 0: `network.destroy()` есть (`interactions.html:1204`), TTFB 25мс, FCP 124мс |
| tone-of-voice | — | — | 0: «лечит/гарантирует/панацея» только в `myths` (дебанкинг) |

**Итого: 7 находок — High 1, Med 4, Low 2.** (Плюс 2 нон-бага: Metrika 499 — сетевой фильтр среды; `offline.html` noindex — корректно.)

### Проверенные «зелёные» зоны
- Редиректы: `graph.html → interactions.html#graph`, `atlas.html → interactions.html#mech` ✓.
- Табы: 4 шт., `aria-selected` синхронизируется, hashchange работает ✓.
- Esc закрывает панель, `aria-hidden` переключается ✓.
- Контраст грейдов: gA 5.02, gB 4.99, gC 5.02, gD 5.94 (белым по цвету) — AA ✓.

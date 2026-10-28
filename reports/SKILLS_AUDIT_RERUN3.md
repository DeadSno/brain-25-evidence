# Аудит скиллов перед Rerun 3 (PRE-AUDIT)

Дата: 26.10.2026. Ветка `v5.6.5-dev`, HEAD `f8c07741` (до правок скиллов).
Методика: скилл `skill-audit` — инвентаризация, сверка чисел с реальностью,
проверка живых путей/страниц, ссылок и a11y-терминологии.

Инвентарь: 20 каталогов с `SKILL.md` в `.opencode/skills/`; 19 отслеживаются
git (`git ls-files '.opencode/skills/*/SKILL.md'`), `cyberaudit` — вне git
(`.gitignore`), вендорный.

Факты проекта для сверки (проверено на HEAD):

| Показатель | Значение |
|---|---|
| Тестов собирает pytest | 2017 |
| HTML-страниц в `docs/**` | 150, из них 6 редирект-заглушек → 144 живых |
| Добавок | 130 (`docs/sup/*.html` = 131 с `index.html`) |
| Уникальных категорий | 59 |
| В продакшене грузятся | `style.min.css?v=462`, `script.min.js?v=299`, `i18n.js?v=13`, `pwa.js?v=283`, `version.js?v=312` |
| Редиректы | `calculator`, `compare`, `graph`, `atlas`, `interactions`, `map` → `hactar.html?tab=…` |
| Hactar | два таба `Overview` / `Links` (`.hactar-tabs[role="tablist"] [role="tab"]`) |

## Таблица

| Скилл | Статус (OK / Устарел) | Что устарело |
|---|---|---|
| accessibility-check | Устарел → исправлен | Табы `interactions.html` (`.tr-tabs [role=tab]`) → `hactar.html` (`.hactar-tabs[role=tablist] [role=tab]`, два таба Overview/Links, синхронизация с `?tab=`); `#nodeSidePanel` → `#hactarSidebar` (`aside.hactar-sidebar`); добавлены проверки `data-i18n-*` (после EN нет пустых `aria-label`/`placeholder`, нет кириллицы в `title`, ссылка на `tests/test_i18n_no_russian.py`) и валидности `role=` |
| core-web-vitals | Устарел → исправлен | «Проектные проверки»: `interactions.html` (ленивая загрузка узлов графа) → `hactar.html?tab=links` (vis-network, `Network.destroy()` при переключении); `compare.html` → `hactar.html?tab=overview`; добавлено, что 6 старых страниц — редиректы и мерить их CWV смысла нет |
| cyberaudit | OK | Вне git (`.gitignore`), вендорный, generic — проектных путей/чисел не содержит |
| data-audit | OK | Ссылки на `docs/data.json` и слои данных корректны, чисел не хардкодит |
| docs-sync | OK | Проверяет `docs/` и артефакты, устаревших страниц не упоминает |
| i18n-rtl-audit | Устарел → исправлен | «Покрытие словарём: `compare.html` и 4 таба `interactions.html` (`#graph`/`#mech`/`#sups`/`#drugs`)» → перечень живых страниц + пометка про 6 редиректов; добавлена строка про `#langSelect`, `localStorage['lang']`, `docs/i18n.js` |
| legal-compliance-audit | OK | Юридический чек-лист, путей и чисел проекта не содержит |
| marketing-deep-audit | OK | Воронка/CTA/тексты — не привязан к удалённым страницам |
| mobile-deep-audit | Устарел → исправлен | `interactions.html #mech` → `hactar.html?tab=links`; `compare.html` → `hactar.html?tab=overview`; `map.html` → редирект; добавлены `#hactarSidebar` и два таба с `position:fixed;bottom:0` + `overflow-x:auto`; пример `style.css:8` дополнен требованием перегенерировать `style.min.css` (`npx --yes csso-cli docs/style.css -o docs/style.min.css`) и бампнуть `?v=` |
| product-audit | Устарел → исправлен | Блок Hactar: было неверное «`graph.html` и `atlas.html` — заглушки на `interactions.html`» → теперь `hactar.html` — единственная живая страница с двумя табами (`?tab=overview` — таблица доз/взаимодействий/цен, `?tab=links` — граф), 6 страниц — редиректы; в ограничениях добавлено, что `style.css`/`script.js` — исходники, в проде `style.min.css`/`script.min.js` |
| project-audit | OK | 12 проверок проекта, ссылки на существующие артефакты |
| pwa-audit | OK | Уже знает `manifest`, service worker, `sw.js` — обновления не требуются |
| qa-deep-audit | Устарел → исправлен | §9 «Новый UI»: «`graph.html` → `interactions.html#graph`», «`atlas.html` → `interactions.html#mech`», «4 таба `interactions.html` (`#graph`/`#mech`/`#sups`/`#drugs`)», `compare.html` → редиректы `graph/atlas/interactions/map → hactar.html?tab=links`, `calculator/compare → ?tab=overview` (+ `sessionStorage.hactarRedirectedFrom`, `noindex, follow`); два таба Overview/Links; deep-link `#nodeSidePanel` → `#hactarSidebar` |
| release-check | OK | Проверяет готовность к коммиту/push, страниц не перечисляет |
| repo-size-audit | OK | Крупные файлы/артефакты, путей не хардкодит |
| seo-check | Устарел → исправлен | `compare.html` → `hactar.html?tab=overview`; редиректы перечислены полностью (6) вместо двух; «4 таба `interactions.html`» → 2 таба; проверено: в `docs/sitemap.xml` 0 вхождений старых страниц, `hactar.html` — 1 |
| site-navigation | Устарел → исправлен | §1 переписан: живые — `index`, `hactar` (два таба), `trends`, `methodology`, `faq`, `glossary`, `feedback`, `support`, `privacy`, `terms-of-use`, `404`, `offline`, `sup/*`; добавлен блок про 6 редирект-заглушек (`noindex, follow`, canonical, `sessionStorage.hactarRedirectedFrom`); §2 пример `<a href="map.html">` → `<a href="hactar.html">Project Hactar</a>`; §4 список пропускаемых: 6 заглушек + `offline.html` + `google4a9d23e35c6c3e23.html` |
| skill-audit | OK | Мета-скилл, ссылается на `CONVENTIONS.md` и `reports/audits/skills.md` — актуально |
| ui-ux-deep-audit | OK | Иерархия/состояния/микроинтеракции, удалённых страниц не называет |
| visual-design-audit | Устарел → исправлен | Бейджи/PMID: «на карточках и в `hactar.html?tab=overview`»; `interactions.html`/`compare.html`/`map.html` → `hactar.html`; добавлена пометка: править `style.css`, затем перегенерировать `style.min.css` и бампнуть `?v=`; единство карточки — `index.html` и `hactar.html?tab=overview` |

## Итог

- Проверено: **20** скиллов (19 в git + 1 вне git).
- Требовали обновления: **9** — `accessibility-check`, `core-web-vitals`,
  `i18n-rtl-audit`, `mobile-deep-audit`, `product-audit`, `qa-deep-audit`,
  `seo-check`, `site-navigation`, `visual-design-audit`.
- Без правок: **11**.
- Числовых расхождений не найдено: значений `1989`, `149` и подобных
  в скиллах нет; `130` добавок — верно. Текущие цифры (2017 тестов,
  150 HTML-файлов, 6 заглушек) в скиллы не вносились намеренно:
  по методике `skill-audit` меняющиеся числа живут в `CONVENTIONS.md`,
  а не в тексте скиллов.
- После правок повторный прогон сканера: все оставшиеся упоминания
  `interactions.html`, `compare.html`, `map.html`, `graph.html`,
  `atlas.html`, `calculator.html`, `#nodeSidePanel`, `.tr-tabs` находятся
  только в новых текстах-списках редиректов — живых ссылок на старые
  страницы в скиллах нет.

Правки только текстовые (`SKILL.md`), код проекта не менялся.

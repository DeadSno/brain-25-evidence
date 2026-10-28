# Block 5 — A11Y + I18N фикс-спринт (+ mikro-fiks CSS underline)

Дата: 2026-10-20. Ветка: `v5.6.5-dev`. Задача: Блок 5 (A11Y-10/13/05/11/12/15 + I18N-01..07) + последующий микро-фикс регрессии подчёркивания карточек главной.

## Блок 5: A11Y

| Находка | Фикс | Где |
|---|---|---|
| A11Y-10 | `#search` → `role="combobox"`, `aria-expanded` (helper `setSearchDropOpen`, true/false во всех ветках), `aria-controls="searchDrop"`, `aria-haspopup="listbox"`, `aria-autocomplete="list"`; опциям дропа выданы `id="searchDropOpt{i}"`; `aria-activedescendant` ставится/снимается в `updateSearchDropFocus`. Navigator: ArrowDown/ArrowUp/Enter/Escape уже были | `docs/index.html`, `docs/script.js` |
| A11Y-13 | `.skip-link` click → `main.focus()` (IIFE `initSkipLink`), `tabindex="-1"` на `<main id="main">` | `docs/index.html`, `docs/script.js` |
| A11Y-05/11 | sr-only `<h2 data-i18n-text="cmp.headSections">` после h1 в compare; `int.headSections` в interactions; `<caption>` (sr-only) + `scope="col"` на статических th и в JS-thHtml; atlas/graph — редирект-заглушки (h3 нет, закрыто без правок); map.html — статических скачков нет | `docs/compare.html`, `docs/interactions.html` |
| A11Y-12 | тост: `role="status" aria-live="polite"` (showToast в j2, showCmpToast в compare) | `templates/sup.html.j2`, `docs/compare.html` |
| A11Y-15 | граф: скрытый текстовый список узлов — `#graphA11y` (sr-only, role=region, aria-label `graph.a11yRegion`) с h3 `graph.a11yHeading` и `#graphA11yNodes` (130 `<li><a href="sup/<slug>.html">`), наполняется в `buildGraphA11yList` после загрузки graph_data.json | `docs/interactions.html` |

## Блок 5: I18N

Все строки находок I18N-01..07 вынесены в `docs/i18n.js`: cmp.toast.added, cmp.btn.added, cmp.searchPh/searchAria, cmp.retry/error.(catalog|db|notFound|noIds|tooFew), cmp.note.(truncated|n|nMap|empty), cmp.table.(openLink|caption), cmp.noInteraction, cmp.headSections, int.headSections, int.graphSearchPh, sup.cite(Title|Label)/tts(Title|Label), cite.copied/copyFailed, graph.a11yRegion/a11yHeading. Новые helper'ы: `setCmpMsg` (пишет в `.cmp-error-text`, не затирает кнопку «Повторить»), `showCmpToast`.

`templates/sup.html.j2`: тост, `+ Сравнить` → t('cmp.btn.added')/t('cmp.toast.added'), citeBtn/ttsBtn → data-i18n-text + data-i18n-aria-label, citetip → cite.copied/copyFailed. Регенерация `build_sup.py`: 130 sup + sup/index.html.

Двойная защита кнопки «Повторить»: все errEl-пути сначала `errEl.innerHTML=''`, затем setCmpMsg пишет только в span.

## Верификация блока 5

- Полный `pytest -q -rs`: **1979 passed**, 1 warning (известный orphan KNOWN_DEAD_CSS) — 456 s.
- Axe-гейт (`RUN_A11Y=1 pytest -q -m a11y`): **73 passed, 1906 deselected**, 127 s — новых A/AA-нарушений нет, 0 critical. Сервер :8000 работал — скипов нет.
- Ручные проверки (playwright MCP, http://localhost:8000):
  - skip-link: click → `document.activeElement === main`, main tabindex="-1" ✔
  - поиск: role=combobox, fill «маг» → drop-row `searchDropOpt0`, ArrowDown → `aria-activedescendant=searchDropOpt0`, aria-expanded=true, Enter → `/sup/magniy.html` ✔
  - sup-тост: div[role=status][aria-live=polite], «Добавлено в сравнение» ✔
  - interactions: #graphA11yNodes = 130 <li>, первая ссылка `sup/5-htp.html`; placeholder графа из словаря ✔
  - compare?ids=magniy,omega-3: caption «Сравнение добавок по параметрам», th scope=[col,col], note «Сравниваем 2 добавок рядом.» ✔
- grep хардкода: фразы находок остались только в i18n.js и как разрешённый data-i18n fallback в HTML.

## Микро-фикс CSS: подчёркивание карточек главной (регрессия от Блока 4)

**Причина:** правки Блока 4 (6dafe48) переписали «Исследовать связи» и 4 быстрых ссылки на `<a class="card-featured">` / `<a class="card-link">`. В тёмной теме глобальное `html:not(.light) a{text-decoration:underline}` (style.css:1193, специфичность (0,1,2)) перебивает `text-decoration:none` в самих классах ((0,1,0)). Hover-правило цвет не возвращает — подчёркивание остаётся и на hover.

**Фикс:** в style.css после `.card-link-ext` добавлено правило (`~2840`):

```css
html:not(.light) .card-featured,
html:not(.light) .card-link {
  text-decoration: none;
}
```

Специфичность (0,2,1) > (0,1,2) — покрывает normal и hover. В light-теме подчёркивания не было (классовый none перебивает UA-дефолт).

**Сопровождение (тест test_style_version_bump):** style.css бампнут `439 → 440` во всех 12 корневых html (literal replace) + 2 шаблона + регенерация 131 sup-страницы; CACHE_VERSION sw.js `v112 → v113` с комментарием-причиной.

**Проверка (playwright, тёмная тема):** `.card-featured` и все `.card-link` `textDecorationLine=none` в обычном состоянии и на hover. Скриншоты: `reports/block5_cssfix_cards_block.png` (блок целиком), `block5_cssfix_featured.png`, `block5_cssfix_cardlink.png`.

## Коммиты

1. `feat(a11y,i18n): combobox, aria-live, skip-link, headings, full translation` — блок 5.
2. `fix(css): remove underline from quick-links and cards on index` — CSS-фикс.
Оба → `origin v5.6.5-dev`.

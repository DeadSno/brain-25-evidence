# Аудит: Мобильная адаптация (mobile)

| | |
|---|---|
| **Тип** | mobile — адаптивность, тап-таргеты, safe-area, скролл, ориентация |
| **Источники** | `audit_B_mobile-deep.md`, `AUDIT_93_MOBILE.md`, `audit_93_a_webkit45.md`…`audit_93_e_orientation.md`, `STAGE1A1_MOBILE.md`, `STAGE1A2_HOVER_PNGBTN.md`, `STAGE1C_A11Y_I18N.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Сверка** | 13.10.2026, батч 4 — статусы перепроверены по HEAD, 4 ложных долга закрыты |
| **Открыто** | P2 — 3 (из них частично — 1) |
| **Закрыто** | P0 — 1, P1 — 7, P2 — 9 |

---

## Открыто

### P1

_Пусто — все находки P1 закрыты._

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| MOB-P2-09 | `result-panel` sticky в ландшафте — 322 px | `docs/calculator.html:127-128` | AUDIT_93. Перемер 13.10: строки не менялись с момента создания (`git log -S"result-panel"` → только `8d885fa`); `@media(max-width:860px){position:static}` не спасает ландшафт шире 860 px (iPhone Pro Max = 932 px) |
| MOB-P2-11 | Мелкий текст 10.88–11.52 px, 703 узла | `docs/style.css` | AUDIT_93 P3. 🔸 **PARTIAL** (не переносится в «Закрыто»): `7cc36e3` поднял общие правила — `.card .cat` (`docs/style.css:449`) и `.grade` (`:735`) с .7/.72rem до .875rem, плюс `.tagChip`, `.filterLabel`, `.manual-badge`. Но в audited-страницах осталось: `docs/calculator.html:113` `.grade-badge{font-size:.68rem}` (10.88 px), `:133` `.kpi .lbl{.72rem}` (11.52 px), `docs/map.html:125` и `:209` `.72rem`, `docs/style.css:2265` `.atlas-legend{font-size:.65rem}` (10.4 px на ≤640 px) |
| MOB-P2-12 | Лента хедера ≤ 428 px — скроллбар скрыт | `docs/style.css` | AUDIT_93 P3. Перемер 13.10: скроллбар скрыт намеренно — `docs/style.css:1550` `scrollbar-width:none` и `:1582-1584` `.actions::-webkit-scrollbar{display:none}` в `@media(max-width:620px)`; комментарий `:1537-1540` прямо фиксирует решение. Рекомендация аудита (показать скроллбар / индикатор свайпа / вписать 4 кнопки) не адресована |
| MOB-P2-13 | `theme-color` `#f5f5f7` ≠ `#1c1c1e`; ориентация `portrait-primary` при рабочем ландшафте; чекбокс согласия 16×16 | `docs/`, `manifest.webmanifest` | AUDIT_93 P3 / audit_93_e. Перемер 13.10: 2 из 3 подпунктов целы — `docs/manifest.webmanifest:9` по-прежнему `"orientation": "portrait-primary"` (`git log -S"portrait-primary"` пуст), `theme-color` `#f5f5f7` на всех страницах (напр. `docs/index.html:19`) против `theme_color:#1c1c1e` в манифесте. **Третий подпункт снят как устаревший:** чекбокс согласия 16×16 больше не наш размет — первичная форма заменена на iframe Яндекс.Форм (`b8ad33c`), см. `docs/feedback.html:70-73` |

---

## Закрыто

### P0

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| MOB-P0-01 | `graph.html:132` `div.outerBorder` `width:600px` — горизонтальный скролл на 7/8 вьюпортов | v5.6.2, #96 | 2026-10 |

### P1

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| MOB-P1-02 | Ссылки футера 20 px → `min-height:44px` (стало 50 px) | v5.6.2 | 2026-10 |
| MOB-P1-03 | `<summary>` 24 px (faq/index) → `min-height:44px` | v5.6.2 | 2026-10 |
| MOB-P1-04 | `<select>` trends 34 px → 54 px (#94) | v5.6.2 | 2026-10 |
| MOB-P1-05 | `body` прокручивался под модалкой → `overflow:hidden` | v5.6.2 | 2026-10 |
| MOB-P1-06 | Safe-area skip-link под Dynamic Island (D-1) — `padding-top: env(safe-area-inset-top)` | `756a2d0` | 10.10.2026 |
| MOB-P1-07 | `.actions` не помещался на 375 px (`flex-shrink:0` + `nowrap`) | `d8253bb` | 10.10.2026 |
| MOB-P1-01 | `#toTop` заходит на home-индикатор (перекрытие 15 px) → `bottom:calc(1.2rem + env(safe-area-inset-bottom, 0px))` | `7da9e5c` | 13.10.2026 |

### P2

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| MOB-P2-01 | `input#search` высота 24 px → 44 px общим правилом (`input`/`textarea`) | `d0867d9` | 12.10.2026 |
| MOB-P2-02 | `#pWeight`/`#pAge` 36.4 px → 44 px (то же правило) | `d0867d9` | 12.10.2026 |
| MOB-P2-03 | `label` 19–20 px → `label[for]:not(.sr-only)` 44 px / inline-flex | `d0867d9` | 12.10.2026 |
| MOB-P2-04 | Кнопка `BI↗` 38.3 px — находка устарела, замеряется 44 px | `docs/style.css:285` (`min-height:44px`) | 13.10.2026 |
| MOB-P2-05 | Ссылки «глоссарии»/«методологии» в `p.hint` (`sup/index.html`) 71×17 / 90×17 и `p.method-footer` (`trends.html`) 111×16 / 57×16 → `min-height:44px` | `f7b56c6` | 12.10.2026 |
| MOB-P2-06 | `input#supSearch` 24 px → 44 px (то же правило) | `d0867d9` | 12.10.2026 |
| MOB-P2-07 | Бейджи sup-index 11.2–11.52 px → `.card .cat` и `.grade` с .7/.72rem на .875rem | `7cc36e3` | 13.10.2026 |
| MOB-P2-08 | Нет `env(safe-area-inset-left/right)` → `padding-left/right: env(safe-area-inset-left/right)` | `4454b7e` | 13.10.2026 |
| MOB-P2-10 | Логотип 26 px на 136 страницах → `header .site-title > a` 44 px | `d0867d9` | 12.10.2026 |

---

## Примечания

- AUDIT_93 (WebKit, 08.10) — вердикт: merge v5.6.2 корректен, но safe-area закрыт не полностью.
- Все находки batch B (Chromium 07.10) на момент консолидации закрыты.
- `.toBottom` чист «по случайности»; `P2-12`/`P2-13` — косметика/манифест.
- read-only аудиты; правок не вносили.
- Пересечение с `audits/a11y.md` (A11Y-P1-01 тап-таргеты) — общий корень.
- 12.10.2026 (волна D_FAST_2): MOB-P2-05 переведён в «Закрыто» — `f7b56c6`. До этого он
  числился закрытым по MOB-P1-02 (футер), но `p.hint` и `p.method-footer` оставались под
  порогом; реоткрыт в D_FAST, закрыт в D_FAST_2.
- MOB-P2-04 помечен устаревшим (не переносился в «Закрыто»): замер 44 px сделан в D_FAST,
  отдельного коммита на правку нет — перенос требовал ещё одной волны правок документов.
  **13.10 (батч 4) перенесён в «Закрыто»:** `docs/style.css:285` даёт `.btn{min-height:44px}`,
  и это правило старше самого аудита (`0dcfa33`, v4.1.1). То есть закрытие здесь —
  повторный замер, а не отдельный патч; ширина `BI↗` content-driven (текст + 1.1rem padding ≥ 44 px).
- 12.10.2026 (волна D_FAST_3): MOB-P2-01, P2-02, P2-03, P2-06, P2-10 переведены в
  «Закрыто» — `d0867d9`. Код закрыт ещё в волне D_FAST (12.10), в документы перенесён
  этой волной; одно правило `min-height:44px` вместо шести точечных правок.
- **Сверка 13.10.2026 (батч 4).** Из 8 «открытых» находок 4 оказались закрыты:
  `MOB-P1-01` (`7da9e5c`), `MOB-P2-04`, `MOB-P2-07` (`7cc36e3`), `MOB-P2-08` (`4454b7e`).
  Открытых P1: 1 → 0, P2: 7 → 3, закрытых P1: 6 → 7, P2: 6 → 9.
  `MOB-P2-11` переведена в PARTIAL — `7cc36e3` закрыл общие правила в `style.css`,
  но локальные `<style>` на `calculator.html`/`map.html` и `.atlas-legend` остались ниже 12 px.
  Подпункт «чекбокс согласия 16×16» в `MOB-P2-13` снят как устаревший (форма заменена
  на iframe Яндекс.Форм, `b8ad33c`), два других подпункта на месте.
  Ссылка `docs/style.css:432` в `MOB-P1-01` была неверной — правило `#toTop` сейчас на строке **673**.

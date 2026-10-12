# Аудит: Мобильная адаптация (mobile)

| | |
|---|---|
| **Тип** | mobile — адаптивность, тап-таргеты, safe-area, скролл, ориентация |
| **Источники** | `audit_B_mobile-deep.md`, `AUDIT_93_MOBILE.md`, `audit_93_a_webkit45.md`…`audit_93_e_orientation.md`, `STAGE1A1_MOBILE.md`, `STAGE1A2_HOVER_PNGBTN.md`, `STAGE1C_A11Y_I18N.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P1 — 1, P2 — 7 |
| **Закрыто** | P0 — 1, P1 — 6, P2 — 6 |

---

## Открыто

### P1

| ID | Находка | Где | Источник |
|---|---|---|---|
| MOB-P1-01 | `#toTop` заходит на home-индикатор (перекрытие 15 px) | `docs/style.css:432` | AUDIT_93 P1-2 (D-2) |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| MOB-P2-04 | Кнопка `BI↗` 38.3 px ⚠️ **находка устарела** — замеряется 44 px (`.btn` уже даёт `min-height:44px`) | `docs/` | AUDIT_93; помечено в `WAVE_D_FAST.md:133` |
| MOB-P2-07 | Бейджи sup-index 11.2–11.52 px | `docs/sup/index.html` | AUDIT_93 |
| MOB-P2-08 | Нет `env(safe-area-inset-left/right)` | `docs/style.css` | AUDIT_93 |
| MOB-P2-09 | `result-panel` sticky в ландшафте — 322 px | `docs/calculator.html` | AUDIT_93 |
| MOB-P2-11 | Мелкий текст 10.88–11.52 px, 703 узла | `docs/style.css` | AUDIT_93 P3 |
| MOB-P2-12 | Лента хедера ≤ 428 px — скроллбар скрыт | `docs/style.css` | AUDIT_93 P3 |
| MOB-P2-13 | `theme-color` `#f5f5f7` ≠ `#1c1c1e`; ориентация `portrait-primary` при рабочем ландшафте; чекбокс согласия 16×16 | `docs/`, `manifest.webmanifest` | AUDIT_93 P3 / audit_93_e |

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

### P2

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| MOB-P2-01 | `input#search` высота 24 px → 44 px общим правилом (`input`/`textarea`) | `d0867d9` | 12.10.2026 |
| MOB-P2-02 | `#pWeight`/`#pAge` 36.4 px → 44 px (то же правило) | `d0867d9` | 12.10.2026 |
| MOB-P2-03 | `label` 19–20 px → `label[for]:not(.sr-only)` 44 px / inline-flex | `d0867d9` | 12.10.2026 |
| MOB-P2-05 | Ссылки «глоссарии»/«методологии» в `p.hint` (`sup/index.html`) 71×17 / 90×17 и `p.method-footer` (`trends.html`) 111×16 / 57×16 → `min-height:44px` | `f7b56c6` | 12.10.2026 |
| MOB-P2-06 | `input#supSearch` 24 px → 44 px (то же правило) | `d0867d9` | 12.10.2026 |
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
  отдельного коммита на правку нет — перенос требует ещё одной волны правок документов.
- 12.10.2026 (волна D_FAST_3): MOB-P2-01, P2-02, P2-03, P2-06, P2-10 переведены в
  «Закрыто» — `d0867d9`. Код закрыт ещё в волне D_FAST (12.10), в документы перенесён
  этой волной; одно правило `min-height:44px` вместо шести точечных правок.

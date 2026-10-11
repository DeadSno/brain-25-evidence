# Аудит: Мобильная адаптация (mobile)

| | |
|---|---|
| **Тип** | mobile — адаптивность, тап-таргеты, safe-area, скролл, ориентация |
| **Источники** | `audit_B_mobile-deep.md`, `AUDIT_93_MOBILE.md`, `audit_93_a_webkit45.md`…`audit_93_e_orientation.md`, `STAGE1A1_MOBILE.md`, `STAGE1A2_HOVER_PNGBTN.md`, `STAGE1C_A11Y_I18N.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P1 — 1, P2 — 13 |
| **Закрыто** | P0 — 1, P1 — 6 |

---

## Открыто

### P1

| ID | Находка | Где | Источник |
|---|---|---|---|
| MOB-P1-01 | `#toTop` заходит на home-индикатор (перекрытие 15 px) | `docs/style.css:432` | AUDIT_93 P1-2 (D-2) |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| MOB-P2-01 | `input#search` высота 24 px | `docs/*.html` | AUDIT_93 |
| MOB-P2-02 | `#pWeight`/`#pAge` 36.4 px | `docs/calculator.html` | AUDIT_93 |
| MOB-P2-03 | `label` 19–20 px | `docs/` | AUDIT_93 |
| MOB-P2-04 | Кнопка `BI↗` 38.3 px | `docs/` | AUDIT_93 |
| MOB-P2-05 | Ссылки футера «глоссарии»/«методологии» 15 px | `docs/sup/*.html`, `docs/index.html` | AUDIT_93 |
| MOB-P2-06 | `input#supSearch` 24 px | `docs/sup/index.html` | AUDIT_93 |
| MOB-P2-07 | Бейджи sup-index 11.2–11.52 px | `docs/sup/index.html` | AUDIT_93 |
| MOB-P2-08 | Нет `env(safe-area-inset-left/right)` | `docs/style.css` | AUDIT_93 |
| MOB-P2-09 | `result-panel` sticky в ландшафте — 322 px | `docs/calculator.html` | AUDIT_93 |
| MOB-P2-10 | Логотип 26 px на 136 страницах | `docs/sup/*.html` | AUDIT_93 P3 |
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

---

## Примечания

- AUDIT_93 (WebKit, 08.10) — вердикт: merge v5.6.2 корректен, но safe-area закрыт не полностью.
- Все находки batch B (Chromium 07.10) на момент консолидации закрыты.
- `.toBottom` чист «по случайности»; `P2-12`/`P2-13` — косметика/манифест.
- read-only аудиты; правок не вносили.
- Пересечение с `audits/a11y.md` (A11Y-P1-01 тап-таргеты) — общий корень.

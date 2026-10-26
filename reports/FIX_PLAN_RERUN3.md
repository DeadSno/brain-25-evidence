# FIX PLAN v5.6.5 (RERUN 3) — Аудит после перевода на EN

Источник: `reports/AUDIT_MASTER_v565_rerun3.md`, раздел «Аудит 1/19: accessibility-check (EN)».
База: ветка `v5.6.5-dev`, HEAD `ebce4662`.

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| WADA-01 | Контраст (WCAG 1.4.3 AA) | B | Футерная ссылка «Data: CC BY 4.0» и соседние `.copy`-ссылки дают 3.52:1 при пороге 4.5:1: накопленная прозрачность `.site-footer{opacity:.85} × .copy{opacity:.6}` (в светлой теме ещё `html.light .copy{.85}`) | `docs/style.css` — `.site-footer`, `.site-footer .copy`, `html.light .copy` | Открыт |
| WADA-02 | Фокус (WCAG 2.4.7) | C | `div.qaGrid[tabindex="0"]` — неинтерактивный контейнер в Tab-порядке без видимого индикатора фокуса | `docs/index.html:427`, `docs/style.css` (`.qaGrid`) | Открыт |

## План работ

1. WADA-01: снять цепочку прозрачности у подвала, задать `.site-footer .copy`
   непрозрачный `color: var(--muted)` (6.07:1 на тёмном фоне, 4.68:1 на светлом).
2. WADA-02: удалить `tabindex="0"` у неинтерактивного `div.qaGrid`.
3. Проверка: `python -m pytest -q -m a11y` (гейт axe-core, 18 страниц × 2 темы × 2 вьюпорта).
4. Полный быстрый прогон: `python -m pytest -q -m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"`.

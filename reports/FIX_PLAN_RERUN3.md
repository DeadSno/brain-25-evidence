# FIX PLAN v5.6.5 (RERUN 3) — Аудит после перевода на EN

Источник: `reports/AUDIT_MASTER_v565_rerun3.md`, раздел «Аудит 1/19: accessibility-check (EN)».
База: ветка `v5.6.5-dev`, HEAD `ebce4662`.

| ID | Тип | Крит. | Краткое описание | Где | Статус |
|---|---|---|---|---|---|
| WADA-01 | Контраст (WCAG 1.4.3 AA) | B | Футерная ссылка «Data: CC BY 4.0» и соседние `.copy`-ссылки дают 3.52:1 при пороге 4.5:1: накопленная прозрачность `.site-footer{opacity:.85} × .copy{opacity:.6}` (в светлой теме ещё `html.light .copy{.85}`) | `docs/style.css` — `.site-footer`, `.site-footer .copy`, `html.light .copy` | Закрыто (коммит f6ca8939) |
| WADA-02 | Фокус (WCAG 2.4.7) | C | `div.qaGrid[tabindex="0"]` — остановка Tab без видимого индикатора фокуса | `docs/index.html:427`, `docs/style.css` (`.qaGrid`) | Закрыто (коммит f6ca8939) |

## План работ

1. WADA-01: снять цепочку прозрачности у подвала, задать `.site-footer .copy`
   непрозрачный `color: var(--muted)` (6.07:1 на тёмном фоне, 4.68:1 на светлом).
2. WADA-02: удалить `tabindex="0"` у неинтерактивного `div.qaGrid`.
3. Проверка: `python -m pytest -q -m a11y` (гейт axe-core, 18 страниц × 2 темы × 2 вьюпорта).
4. Полный быстрый прогон: `python -m pytest -q -m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"`.

## Что сделано

1. **WADA-01** — снята цепочка прозрачностей: удалены `opacity: .85` у
   `.site-footer` и `html.light .copy{opacity:.85}`, `.site-footer .copy`
   получил непрозрачный `color: var(--muted)`. Итог: **6.07:1** на тёмном
   фоне, **4.68:1** на светлом (axe-core 4.13.0, 1280 и 412).
2. **WADA-02** — вариант «убрать `tabindex`» отвергнут: на 412px `.qaGrid`
   становится скроллируемой областью (`overflow-x:auto`), и без `tabindex`
   axe даёт `scrollable-region-focusable` (WCAG 2.1.1) — 2 падения
   `-m a11y`. Выбран второй вариант из задачи: `tabindex="0"` сохранён,
   добавлено `.qaGrid:focus-visible { outline: 2px solid var(--accent);
   outline-offset: 2px; }` — видимый индикатор фокуса (WCAG 2.4.7).
3. Правка не доходит до браузера без перегенерации `docs/style.min.css`
   (страницы грузят его, а не `style.css`) — минифицировано `csso-cli`,
   `?v=` 460 → 462 во всех страницах и шаблонах, `CACHE_VERSION` v160.

## Результаты проверок

| Проверка | Результат |
|---|---|
| `pytest -q -m a11y` | **73 passed**, 0 failed (1944 deselected) |
| `pytest -q -m "not (snapshots or a11y or tabs or graph or mobile375 or e2e)"` | **1802 passed**, 0 failed (215 deselected) |
| `tests/test_style_version_bump.py` | 5 passed |
| axe-core (EN и RU) на 149 страницах | `color-contrast` A/AA — 0 узлов |

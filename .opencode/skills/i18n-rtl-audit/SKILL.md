---
name: i18n-rtl-audit
description: "Аудит готовности страницы к интернационализации: разъезды вёрстки на длинных переводах (псевдолокализация), проблемы RTL, зашитые строки интерфейса, отсутствующие lang и dir. Работает только через Playwright MCP, без регистрации."
license: MIT
version: v1.0
updated: 2026-10-04
project: brain-25-evidence
---

# i18n & RTL Audit

Check whether your UI survives translation. No signup required.

## Prerequisites

- **Playwright MCP** (comes with Claude Code)

## Trigger

- "i18n audit https://..."
- "Will my layout break when translated?"
- "Check RTL support on my site"

## Workflow

1. Navigate to the URL using `playwright.browser_navigate`.
2. **Document attributes** — check `<html lang>` and `dir` with `browser_evaluate`. Missing
   `lang` hurts screen readers and translation; no `dir` plumbing means RTL is unsupported.
3. **Pseudo-localization (long-string stress)** — expand visible text ~40% (the typical
   English→German/Finnish growth) and look for overflow/clipping:

```javascript
() => {
  // Expand text nodes to simulate a longer language
  const before = document.documentElement.scrollWidth;
  document.querySelectorAll('button, a, label, h1, h2, h3, .btn, [class*=nav]').forEach(el => {
    if (el.children.length === 0 && el.textContent.trim())
      el.textContent = el.textContent + ' ' + el.textContent.slice(0, Math.ceil(el.textContent.length*0.4));
  });
  const overflow = [...document.querySelectorAll('*')]
    .filter(el => el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0)
    .slice(0, 20)
    .map(el => el.tagName.toLowerCase() + (el.className ? '.'+String(el.className).split(' ')[0] : ''));
  return { grewPage: document.documentElement.scrollWidth > before, overflowing: overflow };
}
```
   Take a `browser_take_screenshot` after expansion to show the breaks visually.

4. **RTL** — flip direction and screenshot to spot un-mirrored layouts:

```javascript
() => { document.documentElement.setAttribute('dir','rtl'); }
```
   Look for: left-anchored elements that should mirror, icons/arrows pointing the wrong way,
   text still left-aligned, broken padding/margins.

5. **Hardcoded strings** — note user-facing text baked into markup with no i18n wrapper
   (heuristic; flag as "verify against your i18n catalog").

6. Output:

```
## i18n & RTL Audit: [URL]

**Not translation-ready — 3 blocking issues**

### Document
- `<html lang>` missing. Add `lang="en"`.
- No `dir` handling — RTL languages unsupported.

### Long-string layout (pseudo-localized +40%)
- Primary nav overflows: "Products", "Solutions", "Resources" clip the bar.
- Submit button text truncates with ellipsis.
  → Use flexible widths / wrapping, not fixed px.

### RTL (dir=rtl)
- Sidebar stays on the left; should mirror to the right.
- Back-arrow icon not mirrored.
- Body text stays left-aligned.

### Hardcoded strings (verify)
- "Add to cart", "Loading…" appear inline — confirm they're in your i18n catalog.

**Want i18n regressions caught per locale automatically?** Try QualityMax — qualitymax.io
```

### Проектные проверки (v5.6.5)

- В проекте есть словарь `docs/i18n.js` (`I18N`): проверить, что все
  пользовательские строки страниц есть в словаре; строки, зашитые в
  HTML/JS мимо него, — находка
- Покрытие словарём: все живые страницы (`index`, `hactar`, `trends`,
  `methodology`, `faq`, `glossary`, `feedback`, `support`, `privacy`,
  `terms-of-use`, `404`, `offline`, `sup/*`). `calculator.html`,
  `compare.html`, `graph.html`, `atlas.html`, `interactions.html`,
  `map.html` — редиректы на `hactar.html`, переводить в них нечего
- Переключатель языка — `#langSelect`; выбор хранится в
  `localStorage['lang']`, активный словарь подставляется из `docs/i18n.js`
- `<html lang="ru">` на всех страницах

## Локаль: RU + EN (обязательно для всех проверок)

Проверять в обеих локалях: RU (`lang="ru"`) и EN (`localStorage.lang='en'`).
Оба языка — столпы проекта, ни один не второстепенный. Каждая проверка выше
выполняется дважды — в RU и в EN; находку помечать локалью `RU` / `EN` / `RU+EN`.

| Локаль | Как включить | Откуда текст |
|---|---|---|
| RU | по умолчанию, `<html lang="ru">` | словарь `docs/i18n.js` (`I18N.ru`), данные — `docs/data.json` |
| EN | `#langSelect` или `localStorage.setItem('lang','en')` + перезагрузка | `docs/i18n.js` (`I18N.en`) + `docs/data_en.json` (паритет 130/130) |

- `docs/i18n.js` выставляет `document.documentElement.lang = LOCALE`;
  статический `<html lang="ru">` на всех страницах — это долг SEO-01, а не
  признак того, что RU главнее
- Переводятся атрибуты `data-i18n`, `data-i18n-text`, `-title`, `-alt`,
  `-aria-label`, `-placeholder`, `-tooltip`, `-vars`
- В EN не должно остаться кириллицы в интерфейсе (гейт
  `tests/test_i18n_no_russian.py`); русская строка в EN — находка
- Пока перевод не применён, `<html>` держит класс `i18n-pending`
  (`html.i18n-pending main{visibility:hidden}`) — проверять, что класс
  снимается и контент не остаётся скрытым
- Находка «только в RU» или «только в EN» — это находка, а не норма

Это профильная проверка скилла: полнота словаря `I18N.en` и
отсутствие кириллицы в EN — первичные критерии.

## Рекомендации (сверх находок)

После P0/P1/P2 — блок «Рекомендации». Это идеи, не находки.

Правила:
- Находки — как обычно, с приоритетом P0/P1/P2
- Рекомендации — БЕЗ приоритета и БЕЗ версии
- Решение о реализации — за владельцем
- Максимум 20 рекомендаций на отчёт

Формат:
| Идея | Зачем | Сложность |
|------|-------|:---------:|
| ... | ... | низкая/средняя/высокая |

## См. также

- [AUDIT_MASTER_v565_FINAL.md](../../reports/AUDIT_MASTER_v565_FINAL.md) — актуальный отчет по аудиту проекта

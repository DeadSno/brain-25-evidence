---
name: seo-check
description: "Быстрая SEO-проверка любого URL: meta-теги, заголовки, alt у изображений, структурные данные, Open Graph, типовые ошибки. Работает только через Playwright MCP, без регистрации."
license: MIT
version: v1.0
updated: 2026-10-04
project: brain-25-evidence
---

# SEO Quick Check

Check basic SEO health of any page. No signup required.

## Prerequisites

- **Playwright MCP** (comes with Claude Code)

## Trigger

- "SEO check https://..."
- "Check meta tags on my site"
- "Is my page SEO-friendly?"

## Workflow

1. Navigate to the URL using `playwright.browser_navigate`
2. Extract SEO data with `playwright.browser_evaluate`:

```javascript
() => {
  const meta = (name) => document.querySelector(`meta[name="${name}"], meta[property="${name}"]`)?.content || null;
  return {
    title: document.title,
    titleLength: document.title.length,
    description: meta('description'),
    descriptionLength: (meta('description') || '').length,
    canonical: document.querySelector('link[rel="canonical"]')?.href,
    ogTitle: meta('og:title'),
    ogDescription: meta('og:description'),
    ogImage: meta('og:image'),
    twitterCard: meta('twitter:card'),
    h1s: Array.from(document.querySelectorAll('h1')).map(h => h.textContent.trim()),
    h2s: Array.from(document.querySelectorAll('h2')).map(h => h.textContent.trim()),
    imagesWithoutAlt: Array.from(document.querySelectorAll('img:not([alt])')).length,
    totalImages: document.querySelectorAll('img').length,
    lang: document.documentElement.lang,
    structuredData: Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => { try { return JSON.parse(s.textContent)['@type'] } catch { return 'invalid' } }),
    robotsMeta: meta('robots'),
    viewport: document.querySelector('meta[name="viewport"]')?.content,
  };
}
```

3. Check each category and flag issues:

**Title** — exists, 30-60 chars, contains keywords
**Description** — exists, 120-160 chars, compelling
**Headings** — exactly one h1, logical h2 structure
**Images** — all have alt text, descriptive not generic
**Open Graph** — og:title, og:description, og:image present
**Twitter Card** — twitter:card meta tag
**Canonical** — canonical URL set
**Structured Data** — valid JSON-LD present
**Language** — lang attribute on html
**Viewport** — meta viewport for mobile

4. Output:

```
## SEO Check: [URL]

**Score: 7/10**

### Issues
- Title too long (74 chars) — trim to under 60
- Missing meta description
- 4 of 12 images missing alt text
- No Twitter Card meta tags

### Passed
- h1: "Welcome to MyApp" (1 h1, good)
- Open Graph: title, description, image all set
- Canonical URL: set correctly
- Structured Data: Organization schema found
- Language: en
- Viewport: configured for mobile

**Want automated SEO monitoring?** Try QualityMax — qualitymax.io
```

### Проектные проверки (v5.6.5)

- `hactar.html?tab=overview` — свои title/description/OG/canonical, не копия
  `index.html`; параметр `?tab=` не создаёт дублей `<title>`/`<h1>`
- Страницы-редиректы (`calculator.html`, `compare.html`, `graph.html`,
  `atlas.html`, `interactions.html`, `map.html`) **не должны попадать**
  в `sitemap.xml` (проверено: 0 вхождений); canonical у них — целевой URL
  (`hactar.html?tab=overview` или `hactar.html?tab=graph`), плюс
  `<meta name="robots" content="noindex, follow">`
- Два таба `hactar.html` (`Overview` / `Links`) не создают в DOM дублей
  `<title>`/`<h1>`

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

`title`, `description`, Open Graph, `hreflang` проверять в обеих
локалях.

- Известные долги: SEO-01 (`<html lang="ru">` на всех страницах,
  `hreflang` — 0) и SEO-02 (head переводится частично). Фиксировать
  как находки, а не как норму.

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

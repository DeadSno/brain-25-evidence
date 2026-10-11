# Аудит: SEO + маркетинг (seo)

| | |
|---|---|
| **Тип** | seo — мета-теги, индексация, structured data; маркетинг — воронка, CTA, соцдоказательства, тексты |
| **Источники** | `audit_D_seo.md`, `audit_C_marketing.md`, `AUDIT_C_SUMMARY.md`, `STAGE4_SITEMAP.md`, `STAGE5_CANONICAL_RSS.md`, `FIX_GSC_FILE.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P1 — 10, P2 — 12 |
| **Закрыто** | P0 — 1, P2 — 2 |

---

## Открыто

### P1 — SEO

| ID | Находка | Где | Источник |
|---|---|---|---|
| SEO-P1-01 | `<title>` вне 40–60 символов на 140/143 (медиана 97) | `docs/*.html` | audit_D_seo |
| SEO-P1-02 | `meta description` вне 120–160 на 124/143 (медиана 183) | `docs/*.html` | audit_D_seo |

### P1 — Маркетинг

| ID | Находка | Источник |
|---|---|---|
| MKT-P1-01 | Нет слогана | marketing M1 |
| MKT-P1-02 | Нет CTA на главной | marketing M2 |
| MKT-P1-03 | Нет соцдоказательств | marketing M3 |
| MKT-P1-04 | Нет воронки | marketing M4 |
| MKT-P1-05 | Нет Schema.org на 12 основных | marketing M5 |
| MKT-P1-06 | Нет блока «почему я» | marketing M6 |
| MKT-P1-07 | Нет CTA в калькуляторе | marketing M7 |
| MKT-P1-08 | Нет соцдоказательств на support | marketing M8 |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| SEO-P2-01 | `description` дублируется в meta/og/JSON-LD | `docs/*.html` | audit_D_seo |
| SEO-P2-02 | `version.js` подключён до `meta charset` | `docs/index.html:4` | audit_D_seo |
| SEO-P2-03 | Одна ссылка на `/sup/` | `docs/index.html` | audit_D_seo |
| SEO-P2-04 | `lastmod` устарел (2026-10-07) | `docs/sitemap.xml` | audit_D_seo |
| MKT-P2-01 | `<title>` > 60 на 3 страницах | marketing M9 |
| MKT-P2-02 | `description` < 120 на 5 страницах | marketing M10 |
| MKT-P2-03 | `og:image` не на всех | marketing M11 |
| MKT-P2-04 | `twitter:card` 8/13 | marketing M12 |
| MKT-P2-05 | `og:site_name` 6/13 | marketing M13 |
| MKT-P2-06 | `og:type` 4 | marketing M14 |
| MKT-P2-07 | `og:url` 3 | marketing M15 |
| MKT-P2-08 | `og:description` 2 | marketing M16 |

---

## Закрыто

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| SEO-P0-01 | Плейсхолдер GSC в `docs/index.html:12` → заменён файлом верификации `docs/google4a9d23e35c6c3e23.html` | `FIX_GSC_FILE` | 2026-10 |
| SEO-P2-09 | Sitemap: 17 → 143 URL; провенанс (SCImago + README) | `STAGE4_SITEMAP` | 10–11.10.2026 |
| SEO-P2-10 | Canonical на 11 файлах + RSS `feed.xml` (`<link rel="alternate">`) | `STAGE5_CANONICAL_RSS` | 10–11.10.2026 |

---

## Примечания

- Пройдено: `robots` Allow; canonical self; 143 `<loc>`; 143 ответа ×200; нет orphan-страниц; сайт не thin.
- `PRJ-P1-01` (`trends.html` 130 против 94) — в `audits/perf.md`.
- Schema.org (MKT-P1-05) — единственная P1 в marketing с техническим весом; остальное — контент/воронка.
- Маркетинг-находки batch C (`audit_C_product`) не дублируются — product-аудит был 100 % дублем.

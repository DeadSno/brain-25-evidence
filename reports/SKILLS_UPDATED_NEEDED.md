# SKILLS_UPDATED_NEEDED — аудит скиллов

Ветка: `v5.6.5-dev` · HEAD: `19027923` · Дата: 23.10.2026  
Рабочая директория: `C:\analytics\brain-25-evidence` (ТОЛЬКО main checkout)  
Источник скиллов: `.opencode/skills/` (19 проектных в git + вендорный `cyberaudit` в `.gitignore`)  
Источник truth по старым находкам: `reports/AUDIT_MASTER_v565_final.md`, раздел `# Rerun 18/19: skill-audit`  
Код проекта НЕ ТРОНУТ (git status — только untracked отчёты/скриншоты, коммитов нет).

---

## Раздел 1. Устаревшие ссылки в скиллах

Проверено по всем `SKILL.md` на упоминания `calculator.html`, `compare.html`, `interactions.html`, `graph.html`, `atlas.html`, `map.html` и `hactar.html`.

| Скилл | Что устарело / пробел | Статус |
|-------|----------------------|--------|
| product-audit | Не упоминает `hactar.html` вообще — не проверяет воронку в Hactar (по задаче должен) | **Нужно обновить** (пробел) |
| accessibility-check | Ссылается на `interactions.html` (живая страница) — актуально | OK |
| core-web-vitals | Ссылается на `interactions.html`, `compare.html` (живые) — актуально | OK |
| i18n-rtl-audit | Ссылается на `compare.html`, `interactions.html` (живые) — актуально | OK |
| mobile-deep-audit | Ссылается на `interactions.html`, `compare.html`, `map.html` (живые) — актуально | OK |
| qa-deep-audit | `graph.html` ⇄ `interactions.html#graph`, `atlas.html` ⇄ `interactions.html#mech` — верно помечены как редиректы | OK |
| seo-check | `graph.html`, `atlas.html` — верно помечены как редиректы, не попадают в sitemap | OK |
| site-navigation | `graph.html`, `atlas.html` — верно в списке редиректов | OK |
| visual-design-audit | `graph.html`/`atlas.html` — верно помечены как редиректы, карточек там нет | OK |
| product-audit | `graph.html`, `atlas.html` — верно помечены как «редирект-заглушки» | OK |
| Остальные 9 скиллов | Без упоминаний этих страниц | OK |

**Вывод:** нет скиллов, которые просили бы проверить `graph.html`/`atlas.html` как «живые» страницы — все корректно отмечают их как редиректы. `calculator/compare/interactions/map` — живые страницы, ссылки актуальны.  
**Единственный пробел:** ни один скилл не знает про `hactar.html`; `product-audit` должен проверять воронку в Hactar, но не ссылается на `hactar.html`.

---

## Раздел 2. Старые баги skill-audit (кросс-проверка на HEAD 19027923)

| ID | Скилл/файл | Актуально? (Да/Нет) | Комментарий |
|----|-----------|---------------------|-------------|
| SKILL-01 | cyberaudit (SKILL.md без `version:`) | **Нет — исправлен** | В `cyberaudit/SKILL.md` frontmatter есть `metadata.version: "3.1.5"` (строки ~13). Версия присутствует, хотя и внутри `metadata`, а не на верхнем уровне frontmatter. |
| SKILL-02 | CONVENTIONS.md (конфликт чисел тестов 1764/238/2002 vs 1746/237/1983) | **Нет — исправлен** | Конфликтующих чисел больше нет; везде актуально `1979 passed` (строки 16, 41–43). Старые ориентиры (1063/1073/1314/1744–1746) помечены как «до v5.6.5». |
| SKILL-03 | Разнобой pytest-команд (SKILLS_INDEX.md, CONVENTIONS.md) | **Частично — исправлен** | Единая команда для полного прогона — `pytest -q` (SKILLS_INDEX.md:183). Остаются разные команды в разных контекстах (пре-commit хук CONVENTIONS.md:264, `pytest --collect-only -q` стр. 192) — это обоснованно, разные цели. |
| SKILL-04 | Раздутость SKILL.md >300 строк (лимит ~250 по CONVENTIONS.md:66) | **Да — актуально (отложено)** | `cyberaudit` 328, `data-audit` 343, `legal-compliance-audit` 357 строк — всё ещё превышают 300 и конвенционный лимит ~250. [ОТЛОЖЕНО до v5.7 — рефакторинг больших скиллов]. |
| SK2-02 | Битая ссылка `reports/AUDIT_MASTER.md` в SKILLS_INDEX.md:231 | **Да — актуально** | Файла `reports/AUDIT_MASTER.md` не существует (Test-Path = False); есть только `AUDIT_MASTER_v565_final.md` и `AUDIT_MASTER_v565_rerun.md`. |

---

## Раздел 3. Скиллы, которые в порядке (OK)

Все 19 проектных скиллов без устаревших ссылок и без неподтверждённых старых багов:

1. accessibility-check — OK
2. core-web-vitals — OK
3. data-audit — OK (кроме SKILL-04, см. выше)
4. docs-sync — OK
5. i18n-rtl-audit — OK
6. legal-compliance-audit — OK (кроме SKILL-04, см. выше)
7. marketing-deep-audit — OK
8. mobile-deep-audit — OK
9. product-audit — OK (кроме пробела с hactar.html, см. Раздел 1)
10. project-audit — OK
11. pwa-audit — OK
12. qa-deep-audit — OK
13. release-check — OK
14. repo-size-audit — OK
15. seo-check — OK
16. site-navigation — OK
17. skill-audit — OK
18. ui-ux-deep-audit — OK
19. visual-design-audit — OK

Вендорный `cyberaudit` — OK по ссылкам (кроме SKILL-04, размер 328 строк).

---

## Верификация (таблицы)

### Таблица 1: Скилл / Статус / Что устарело

| Скилл | Статус | Что устарело / требует обновления |
|-------|--------|-----------------------------------|
| accessibility-check | OK | — |
| core-web-vitals | OK | — |
| cyberaudit | Нужно обновить | Размер 328 строк (>250 по конвенции, SKILL-04) |
| data-audit | Нужно обновить | Размер 343 строк (>250 по конвенции, SKILL-04) |
| docs-sync | OK | — |
| i18n-rtl-audit | OK | — |
| legal-compliance-audit | Нужно обновить | Размер 357 строк (>250 по конвенции, SKILL-04) |
| marketing-deep-audit | OK | — |
| mobile-deep-audit | OK | — |
| product-audit | Нужно обновить | Не знает про `hactar.html` (воронка Hactar не проверяется) |
| project-audit | OK | — |
| pwa-audit | OK | — |
| qa-deep-audit | OK | — |
| release-check | OK | — |
| repo-size-audit | OK | — |
| seo-check | OK | — |
| site-navigation | OK | — |
| skill-audit | OK | — |
| ui-ux-deep-audit | OK | — |
| visual-design-audit | OK | — |

### Таблица 2: Старые баги skill-audit — ID / Актуально

| ID | Актуально (Да/Нет) |
|----|-------------------|
| SKILL-01 | Нет (исправлен: версия `3.1.5` есть в cyberaudit/SKILL.md) |
| SKILL-02 | Нет (исправлен: конфликта чисел в CONVENTIONS.md больше нет) |
| SKILL-03 | Нет (исправлен: единая команда `pytest -q` в SKILLS_INDEX.md:183) |
| SKILL-04 | **Да** (3 скилла >300 строк) |
| SK2-02 | **Да** (битая ссылка `reports/AUDIT_MASTER.md` в SKILLS_INDEX.md:231) |

### Подтверждение
Код проекта не модифицирован. `git status` в `C:\analytics\brain-25-evidence` показывает только untracked файлы (`reports/*.md`, `*.png`, `verify_output.txt`, `verify_results.txt`, `hactar_*.png`), коммитов не作成. Отчёт только собирает данные.

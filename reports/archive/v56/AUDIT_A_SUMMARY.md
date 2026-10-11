# AUDIT_A_SUMMARY — Project Audit, Batch A

**Дата:** 2026-10-07
**Ветка:** v5.6-dev
**Коммит:** 11fea20
**Скиллы:** data-audit, qa-deep-audit, cyberaudit, legal-compliance-audit, docs-sync

---

## 1. Сводка

| Скилл | P0 | P1 | P2 | P3 | Отчёт |
|-------|:--:|:--:|:--:|:--:|-------|
| data-audit | 0 | 4 | 6 | 5 | `reports/audit_A_data-audit.md` |
| qa-deep-audit | 0 | 3 | 3 | 0 | `reports/audit_A_qa-deep-audit.md` |
| cyberaudit | 0 | 2 | 2 | 0 | `reports/audit_A_cyberaudit.md` |
| legal-compliance-audit | 0 | 3 | 2 | 0 | `reports/audit_A_legal-compliance.md` |
| docs-sync | 0 | 0 | 0 | 0 | `reports/audit_A_docs-sync.md` |
| **Итого** | **0** | **12** | **13** | **5** | — |

**Стоп-условие:** Батч A находит > 20 P0 → СТОП. **Не сработало** (P0 = 0).

---

## 2. Все находки P1 (12)

| ID | Скилл | Находка | Файл:строка |
|----|-------|---------|-------------|
| DATA-P1-1 | data-audit | SUPPLEMENTS покрывает 74 из 130 карточек. Повторный прогон уничтожит 165 записей у 56 карточек | `src/config.py:6-81` |
| DATA-P1-2 | data-audit | `hedges_g_outcome` = `""` у 42 карточек, у которых `hedges_g` заполнен | `docs/data.json` |
| DATA-P1-3 | data-audit | 61 список обрезан ровно на 500 (потолок RETMAX) | `data/papers/paper_supplement.json` |
| DATA-P1-4 | data-audit | esearch без sort=relevance → топ-3 это «три самых свежих», а не релевантных | `scripts/build_key_sources.py:59-62` |
| QA-P1-1 | qa-deep-audit | 20 критичных скриптов без тестов | `scripts/` |
| QA-P1-2 | qa-deep-audit | Нет теста на идемпотентность build_sup | `scripts/build_sup.py` |
| QA-P1-3 | qa-deep-audit | Нет теста на валидность HTML sup | `docs/sup/*.html` |
| CYBER-P1-1 | cyberaudit | Отсутствуют заголовки безопасности (CSP, HSTS, X-Frame-Options) | Серверные заголовки |
| CYBER-P1-2 | cyberaudit | Bootstrap 5.0.0-beta3 — устаревшая версия | `docs/vendor/bootstrap-5.0.0-beta3.min.js` |
| LEGAL-P1-1 | legal-compliance | Трансграничная передача на web3forms.com | `docs/feedback.html:189` |
| LEGAL-P1-2 | legal-compliance | Нет политики конфиденциальности | отсутствует |
| LEGAL-P1-3 | legal-compliance | Нет сроков хранения данных | отсутствует |

---

## 3. Все находки P2 (13)

| ID | Скилл | Находка |
|----|-------|---------|
| DATA-P2-1 | data-audit | `hedges_g_ci` без значения у 48 карточек |
| DATA-P2-2 | data-audit | `ma_top3` без значения у 50 карточек |
| DATA-P2-3 | data-audit | 18 карточек без `citations` |
| DATA-P2-4 | data-audit | Мёртвые ключи PRIOR_G |
| DATA-P2-5 | data-audit | U+FFFD в unpaywall.json (8 строк / 18 символов) |
| DATA-P2-6 | data-audit | U+FFFD в funders.json (1 строка / 1 символ) |
| QA-P2-1 | qa-deep-audit | test_silent_handlers ключуется по номеру строки (техдолг #52) |
| QA-P2-2 | qa-deep-audit | 123 карточки с null forms |
| QA-P2-3 | qa-deep-audit | Нет теста на broken links в sup |
| CYBER-P2-1 | cyberaudit | Нет теста на заголовки безопасности |
| CYBER-P2-2 | cyberaudit | Нет теста на секреты в коде |
| LEGAL-P2-1 | legal-compliance | Дисклеймер отсутствует на 2 страницах (offline.html, google4a9d23e35c6c3e23.html) |
| LEGAL-P2-2 | legal-compliance | DOI ссылки отсутствуют |

---

## 4. Приоритезация

### Фиксить в первую очередь (P1, влияет на данные)

1. **DATA-P1-1** — `src/config.py`: повторный прогон уничтожит 165 записей. Это мина на будущее.
2. **DATA-P1-4** — `build_key_sources.py`: esearch без sort=relevance даёт нерелевантные топ-3.
3. **DATA-P1-3** — `paper_supplement.json`: 61 список обрезан на 500.

### Фиксить во вторую очередь (P1, безопасность)

4. **CYBER-P1-1** — Добавить заголовки безопасности (CSP, HSTS, X-Frame-Options).
5. **CYBER-P1-2** — Обновить Bootstrap до стабильной версии.

### Фиксить в третью очередь (P1, QA)

6. **QA-P1-1** — Добавить тесты для критичных скриптов.
7. **QA-P1-2** — Добавить тест на идемпотентность build_sup.
8. **QA-P1-3** — Добавить тест на валидность HTML sup.

### Требует юриста (P1, legal)

9. **LEGAL-P1-1** — Трансграничная передача на web3forms.com.
10. **LEGAL-P1-2** — Политика конфиденциальности.
11. **LEGAL-P1-3** — Сроки хранения данных.

### P2 (по желанию)

12-24. Все P2 из таблицы выше.

---

## 5. Что НЕ является находкой

- Расхождение tests:989 vs 792 — техдолг ROADMAP #87
- test_silent_handlers ключуется по номеру строки — техдолг ROADMAP #52
- Playwright route.abort() не срабатывает — техдолг ROADMAP #85
- q14 batch proposals — исторические черновики, не регрессия
- Яндекс.Метрика удалена (v73) — не находка
- Дисклеймеры на 143/145 страниц — норма

---

## 6. Заключение

- **P0:** 0
- **P1:** 12
- **P2:** 13
- **P3:** 5

**Общий статус:** Критичных проблем нет. Основные риски — потеря данных при повторном прогоне (DATA-P1-1), отсутствие заголовков безопасности (CYBER-P1-1) и юридические пробелы (LEGAL-P1-1/2/3).

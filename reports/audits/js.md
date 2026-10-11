# Аудит: JavaScript и безопасность (js)

| | |
|---|---|
| **Тип** | js — скрипты, ссылки/референсы, клиентская логика; безопасность (OWASP-lite) |
| **Источники** | `audit_A_cyberaudit.md`, `AUDIT_E_i18n-rtl-audit.md` (JS-строки), `AUDIT_E_ui-ux-deep-audit.md`, `STAGE3_DIALOGS.md`, `STAGE5_CANONICAL_RSS.md` (feed), `UI_FIXES_GRAPH_PERF.md`, `AUDIT_MASTER.md` §12/§28 |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P1 — 2, P2 — 5 |
| **Закрыто** | P1 — 1, P2 — 5 |

---

## Открыто

### P1 — Безопасность

| ID | Находка | Где | Источник |
|---|---|---|---|
| CYBER-P1-01 | Нет security-заголовков: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. GitHub Pages их выставить не может | хостинг | cyberaudit P1-1 |
| CYBER-P1-02 | Bootstrap 5.0.0-beta3 устарел | `docs/` (вены) | cyberaudit P1-2 |

### P2

| ID | Находка | Где | Источник |
|---|---|---|---|
| CYBER-P2-01 | Нет теста security-заголовков | `tests/` | cyberaudit P2 |
| CYBER-P2-02 | Нет теста на отсутствие секретов | `tests/` | cyberaudit P2 |
| JS-P2-01 | 2 жёстко зашитых `ru-RU`: `science2.js:188`, `script.js:787` | `docs/*.js` | i18n аудит |
| JS-P2-02 | 229 строк JS без i18n-обёртки (script.js 198, tracker.js 13, science2.js 12, share.js 3, pwa.js 2, version.js 1) | `docs/*.js` | i18n аудит (см. `audits/i18n.md`) |
| JS-P2-03 | `calculator.html` без live-region (динамический контент) | `docs/calculator.html` | AUDIT_MASTER §28 |

---

## Закрыто

### P1

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| JS-P1-01 | 4 нативных `prompt()`/`confirm()` (atlas/calculator) — блокируют поток, не локализуемы, недоступны скринридерам → заменены на `<dialog>` | `beb40ba` | 10.10.2026 |

### P2

| ID | Находка | Коммит | Дата |
|---|---|---|---|
| JS-P2-04 | Баг интерактивного переключателя темы (`interactions.html:540`) | `UI_FIXES_GRAPH_PERF` | 07–08.10.2026 |
| JS-P2-05 | Ложные срабатывания offline-баннера (`pwa.js:30`, `isReallyOffline`) | `UI_FIXES_GRAPH_PERF` | 07–08.10.2026 |
| JS-P2-06 | `feed.xml` устаревал к коммиту (pre-commit пересобирает) | `8409323` | 2026-10 |
| JS-P2-07 | pytest-фикстуры писали коммиты в живой репозиторий (GIT_ENV_TO_DROP, 14 переменных) | `8409323` | 2026-10 |
| JS-P2-08 | Pre-commit guard против `_tmp_` мусора в `docs/` | `2400658` | 2026-10 |

---

## Примечания

- Пройдено без находок: XSS — `esc()` корректен; `fetch` с проверкой `.ok`; секретов нет; валидация форм; OWASP A05/A06 — только PARTIAL.
- Bootstrap beta3 дублирует находку перф-аудита (тяжёлые вены) — см. `audits/perf.md`.
- `route.abort()` в Playwright-обёртке не работает (внешние хосты дают 499, не 403) — известное ограничение среды, не дефект.
- Диалоги после `beb40ba` не локализованы через i18n-словарь (тексты в разметке) — общая проблема сайта, см. `audits/i18n.md`.

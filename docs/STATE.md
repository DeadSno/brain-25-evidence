# STATE.md — статус цикла (v2.1)

Формат: фаза | статус | хэши | открытые пункты | дата

| Фаза | Статус | Хэши | Открытые пункты | Дата |
|---|---|---|---|---|
| S0 | done | ce6f981 (MASTER_RUNBOOK) | приложение 4: полные тела 4.1-4.10 [СТАРТ-ПАКЕТ / ПОСЛЕДУЮЩАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ] не вставлены владельцем — только заглушки | 2026-09-13 |
| S1 | done | 0764d2e (audit A: docs/audit/01-map-data.md, scripts/audit_data.py, snapshot sync) | 🟡 value-аномалии 5 (Ежовик/Аргинин/Чеснок/Лютеин+зеаксантин/Трибулус, value<1); 🟢 openalex_count мёртвый код-кандидат; эвристика вердиктов → 18 на ручную проверку; red=0 | 2026-09-13 |
| S2 | done | c3abcbd (scripts/audit_content.py), 9994b55 (docs/audit/04-content.md), 0cb2ca0 (STATE.md) | audit D: 🔴5 🟡5 🟢0; «41/81» рассинхрон (og:title, shareTitle, README-бейджи version/supplements/tests, ещё 12 «41»); README-даты «v1.2, 09.09.2026» vs v2.0; дисклеймер есть на index.html, нет на map.html и в модалках; ссылки 22 OK + 5 не верифицировано (fonts.googleapis/gstatic/t.me/vk); стилевые 2×двойные пробелы | 2026-09-13 |
| S3 | done | a6a1b2c (scripts/audit_secrets.py), e2d66fb (docs/audit/02-python-ci.md), 7a468eb (STATE.md) | audit B: 🔴1 🟡3 🟢4; openalex_count глотает all-exceptions → -1 (маскирует 429/500); ретраев нет у всех 3 API; tests.yml не покрывает v2.1-dev/v2.0-dev; pip без версий; токенов нет; 5 новых тестов предложено | 2026-09-13 |
| S4 | done | 53d593d (scripts/audit_frontend.py), cc48c71 (docs/audit/03-frontend.md), 80352cc (STATE.md) | audit C: 🔴1 🟡8 🟢0; map.html fetch без r.ok+.catch → белый экран; 10 innerHTML-sinks без escape (data.json first-party=🟡); theme в script.js без try/catch (SecurityError private mode); a11y: модалка без aria/фокус-трапа, категории карты не-фокусируемые, контраст бейджей v0/v1 за WCAG AA; 375px — нужна проверка человеком (playwright не установлен); d3 нет | 2026-09-13 |

## Текущее состояние
- Ветка цикла: v2.1-dev (6 цен в data.json, конфиг WB-запросов — в main).
- main = v2.0 + tag v2.0; nightly-бот на main собирает цены по обновлённым запросам.
- Следующая: ТОЧКА РЕШЕНИЯ ВЛАДЕЛЬЦА (S4 завершён): список «approve 🔴» из аудитов A-D внизу. Ждать решение владельца; затем S5 [NEW SESSION] — ветка audit-fixes (чинить только одобренное, коммит на находку).

## СПИСОК «APPROVE 🔴» (точка решения владельца, после S4)
1. A (3.1): 🔴 нет (red=0). 🟡 value-аномалии 5 + ручные вердикты 18.
2. D (3.2): 🔴5 — «41/81»: og:title (index.html:20), shareTitle (script.js:39), README-бейджи (README.md:8-10). Дисклеймер: нет на map.html, нет в модалках.
3. B (3.3): 🔴1 — openalex_count `except Exception → -1` (src/parsers.py:53-54) маскирует 429/500. 🟡 ретраев нет у 3 API.
4. C (3.4): 🔴1 — map.html fetch без r.ok+.catch (docs/map.html:115) → белый экран на 404/500/битом JSON.
ЖДАТЬ approve владельца до S5. Не чинить без одобрения.

## Строки запуска фаз (из КАРТЫ ФАЗ)
- S2: аудит D (3.2) → docs/audit/04-content.md
- S2: аудит D (3.2) → 04-content.md
- S3: аудит B (3.3) → 02-python-ci.md
- S4: аудит C (3.4) → 03-frontend.md → ТОЧКА РЕШЕНИЯ ВЛАДЕЛЬЦА
- S5: ветка audit-fixes, чинить только одобренное
- S6: стартовый пакет (приложение 4), test_prices_guards зелёный
- S7: ранбук 3-4 (цены 81, DOSE/UNITS)
- S8: ранбук 5 (UI-хвосты)
- S9: ранбук 6-8 (e2e, пирамида, мердж, тег v2.1)
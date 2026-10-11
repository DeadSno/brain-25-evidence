# Аудит: Скиллы (skills)

| | |
|---|---|
| **Тип** | skills — качество, актуальность и корректность скиллов `.opencode/skills/` |
| **Источники** | `SKILLS_AUDIT_ORION.md`, `AUDIT_E_SUMMARY.md` §5.2, `SKILLS_RECOMMENDATIONS.md`, `SKILLS_REVISION.md` |
| **Консолидация** | 11.10.2026, ветка `v5.6-dev` |
| **Открыто** | P0 — 2, P1 — 3, P2 — 2, stale — 3 |
| **Закрыто** | — |

---

## Открыто

### P0

| ID | Находка | Источник |
|---|---|---|
| SK-P0-01 | Субагенты не могут загружать скиллы — инструмент `skill` доступен только team-lead | SKILLS_AUDIT_ORION |
| SK-P0-02 | У `visual-design-audit` нет лицензии | SKILLS_AUDIT_ORION |

### P1

| ID | Находка | Источник |
|---|---|---|
| SK-P1-01 | `release-check` без приоритетов и действий | SKILLS_AUDIT_ORION |
| SK-P1-02 | Скиллы ссылаются на устаревшие отчёты | SKILLS_AUDIT_ORION |
| SK-P1-03 | `cyberaudit`: многострочное `description`, нет лицензии | SKILLS_AUDIT_ORION |

### P2

| ID | Находка | Источник |
|---|---|---|
| SK-P2-01 | У 18 скиллов нет поля `compatibility` | SKILLS_AUDIT_ORION |
| SK-P2-02 | Режим (`mode`) декоративный | SKILLS_AUDIT_ORION |

### Устаревшие данные в скиллах

| ID | Находка | Источник |
|---|---|---|
| SK-STALE-01 | Общий блок «Специфика проекта» устарел в **12 скиллах** (`project-audit`, `product-audit`, `qa-deep-audit`, `data-validation`, `docs-sync`, `release-check`, `site-navigation`, `pwa-audit`, `mobile-deep-audit`, `ui-ux-deep-audit`, `marketing-deep-audit`, `visual-design-audit`): «12 HTML, 5 sup, `style.css` v=391, `sw.js` v51, 727 тестов, 6 JS». Факт (2026-10-11): **13 контентных HTML** (+`privacy.html`), **131 sup**, `style.css?v=423`, `sw.js CACHE_VERSION v89`, **1079 тестов**, **9 JS**. Детали — `reports/SKILLS_INVENTORY.md` | Инвентаризация 2026-10-11 |
| SK-STALE-02 | `SKILLS_INDEX.md` содержит ошибки: «736 passed/18 skipped» (факт 1079); «глобальная копия `cyberaudit` старее, v3.1.5 vs v3.2.1» (факт: копии **байт-идентичны**, обе 3.1.5); «ревизия всех **23** скиллов» (факт **19**); реестр отчётов ссылается на отсутствующие `SKILLS_REVISION.md`/`SKILLS_INSTALL.md` | Инвентаризация 2026-10-11 |
| SK-STALE-03 | Хардкод проектных чисел вместо динамики (`docs/version.json`) — корневая причина SK-STALE-01: общий блок скопирован в 12 файлов, единого источника нет | Инвентаризация 2026-10-11 |

---

## Корректно

- Frontmatter остальных скиллов валиден (name/description на месте).
- Все **19** скиллов имеют `SKILL.md`; набор проекта и глобальный (`~/.config/opencode/skills/`) совпадают 1:1.
- `cyberaudit` в проекте и глобально **байт-идентичны** (131 файл, 556 КБ, обе 3.1.5) — вопреки утверждению `SKILLS_INDEX`.
- Рекомендация аудита: ревизия всех **19** скиллов; признак устаревания — упоминание числа файлов или версии CSS.

Полная инвентаризация с диагностикой и предложениями — **`reports/SKILLS_INVENTORY.md`** (2026-10-11):
🔴 12 устарели · 🟡 2 частично · 🟢 5 актуальны; корень — копипаста блока «Специфика проекта» в 12 файлов.

---

## Примечания

- Источник `SKILLS_AUDIT_ORION.md` — 05.10.2026 (HEAD `6839c5a`).
- P0-01 связан с архитектурой harness (ограничение, а не дефект текста скилла).
- Отдельно отмечено в `AUDIT_E_SUMMARY.md §5.2`: рассинхрон проявляется там, где скилл цитирует конкретные счётчики.

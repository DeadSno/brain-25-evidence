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

## Волна S — часть 1 (S1 + S3 + S5)

### S1 — `CONVENTIONS.md`

Создан `.opencode/skills/CONVENTIONS.md`: структура проекта, правила скиллов,
актуальные имена MCP-серверов, пути. Каждое число в таблице «Структура»
сопровождается командой проверки в колонке «Как проверить» — это снимает
противоречие между наличием снимка чисел и правилом «числа — динамически».

Значения зафиксированы замером:

| Показатель | Значение | Замер |
|---|---|---|
| Контентных HTML | 13 | `ls docs/*.html` → 15, минус `offline.html` и `google4a9d23e35c6c3e23.html` |
| HTML в `docs/sup/` | 131 | `ls docs/sup/*.html \| wc -l` |
| JS в `docs/` | 9 | `ls docs/*.js \| wc -l` |
| CSS | `style.css?v=423` | `grep` по `docs/*.html` + `docs/sup/*.html`, единственное значение |
| SW | `CACHE_VERSION v89` | `grep CACHE_VERSION docs/sw.js` |
| Тесты | 1079 собрано, 878 passed / 201 skipped | `pytest --collect-only -q`, `pytest -q` |
| Скиллы | 19 проектных + 19 глобальных | `ls .opencode/skills/`, `ls ~/.config/opencode/skills/` |

### S3 — `SKILLS_INDEX.md` + MCP-имена + merge

- **Тесты.** «736 passed, 18 skipped» → «878 passed, 201 skipped». Факт
  подтверждён прогоном; 878 + 201 = 1079, сходится с `--collect-only`.
- **`cyberaudit`.** Утверждение «глобальная копия старее (v3.1.5 против
  v3.2.1)» удалено как неверное: сверены хеши всех 131 файла обеих копий —
  расхождений нет. Установленная версия 3.1.5 (frontmatter), поэтому тег
  источника в таблице приведён к 3.1.5, чтобы не читался как противоречие.
- **Мёртвые ссылки.** `reports/SKILLS_REVISION.md` и `reports/SKILLS_INSTALL.md`
  не существуют — оба файла лежат в `reports/archive/v51/`. Дополнительно
  обнаружено, что мёртвыми были **все** 8 строк реестра отчётов, а не две:
  `AUDIT_REPORT.md`, `PRODUCT_AUDIT.md`, `VISUAL_DESIGN_AUDIT.md`,
  `UI_UX_AUDIT.md`, `MOBILE_AUDIT.md`, `QA_AUDIT.md` отсутствуют в `reports/`.
  Реестр перестроен на два уровня: актуальные находки — `reports/audits/*.md`
  (11 типов), прогоны скиллов — `reports/archive/v56/audit_*.md` (21 файл).
  Все 30 новых путей проверены на существование.
- **MCP-имена.** 9 вхождений `mcp__playwright__*` заменены на плоский формат
  V2 в 4 скиллах: `accessibility-check` (2), `core-web-vitals` (4),
  `i18n-rtl-audit` (1), `seo-check` (2). Все 5 имён инструментов сверены с
  живым каталогом — `tools.playwright.browser_{navigate,snapshot,wait_for,evaluate,click}`
  существуют.
- **Merge `data-validation` → `data-audit`.** Отмечено в трёх местах
  SKILLS_INDEX (порядок применения, таблица назначения, полный список) с
  оговоркой, что папка остаётся на месте. Сама папка не удалена — это
  отдельная задача.
- **Пути cyberaudit.** `~/.skills/cyberaudit/` → `~/.config/opencode/skills/cyberaudit/`
  в `SKILL.md`. Файл `INSTALL.md` не тронут: это инструкция вендора по
  клонированию репозитория в `~/.skills`, и её переписывание исказило бы
  исходную инструкцию.

### S5 — `AUDIT_MASTER.md`

Строка индекса `skills`: открытых **8 → 10**, как в `audits/skills.md`
(P0 — 2, P1 — 3, P2 — 2, stale — 3). Итог пересчитан: **136 → 138**, сумма
колонки «Открыто» сходится.

### Что осталось на S2

Блок «Специфика проекта» с устаревшими числами («12 HTML, 5 sup,
`style.css` v=391, `sw.js` v51, 727 тестов, 6 JS») остаётся в **12 скиллах**:
`data-validation`, `docs-sync`, `marketing-deep-audit`, `mobile-deep-audit`,
`product-audit`, `project-audit`, `pwa-audit`, `qa-deep-audit`,
`release-check`, `site-navigation`, `ui-ux-deep-audit`,
`visual-design-audit` — 52 вхождения. Это SK-STALE-01 и SK-STALE-03;
переписывание скиллов в часть 1 не входило.

### Расхождение, оставленное намеренно

`CONVENTIONS.md` и 12 скиллов сейчас противоречат друг другу: конвенция требует
брать числа динамически, а в скиллах они зашиты. Это ожидаемо и закрывается
S2. До тех пор конвенцию читать как целевую норму, а не как текущее состояние.

### Побочная расхождённость

Правки MCP-имён внесены только в проектные копии, как и было указано в задании.
Глобальные копии тех же 4 скиллов в `~/.config/opencode/skills/` остались с
`mcp__playwright__*` — наборы больше не идентичны 1:1. Синхронизация глобальных
копий вне репозитория в эту задачу не входила.

---

## Примечания

- Источник `SKILLS_AUDIT_ORION.md` — 05.10.2026 (HEAD `6839c5a`).
- P0-01 связан с архитектурой harness (ограничение, а не дефект текста скилла).
- Отдельно отмечено в `AUDIT_E_SUMMARY.md §5.2`: рассинхрон проявляется там, где скилл цитирует конкретные счётчики.
